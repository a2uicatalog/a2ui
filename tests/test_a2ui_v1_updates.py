"""A2UI v1.0 incremental-update conformance — renderers/a2ui_v1_updates.py (C2).

Locks the server->client message shapes, the reference apply semantics (RFC 6901
JSON-pointer patch, component upsert, surface teardown), poll->protocol
compliance, and the channel abstraction (poll + injected-writer push).
"""
import pytest

from renderers.a2ui_v1_updates import (
    update_components, update_data_model, delete_surface,
    poll_result_to_update, apply_update, surface_state_from_create,
    PollChannel, FirestorePushChannel, Channel,
)
from renderers.a2ui_v1 import A2UI_VERSION


def _one_key(msg, key):
    assert msg["version"] == A2UI_VERSION
    envelope_keys = [k for k in msg if k != "version"]
    assert envelope_keys == [key], f"message must carry exactly one of the message keys, got {envelope_keys}"


def test_emit_shapes():
    _one_key(update_components("s1", [{"id": "a", "component": "Text", "text": "hi"}]), "updateComponents")
    _one_key(update_data_model("s1", value=5, path="/count"), "updateDataModel")
    _one_key(delete_surface("s1"), "deleteSurface")
    # updateDataModel: value present -> included; omitted -> absent (means remove)
    assert update_data_model("s1", value=5, path="/x")["updateDataModel"] == {"surfaceId": "s1", "path": "/x", "value": 5}
    assert "value" not in update_data_model("s1", path="/x")["updateDataModel"]
    assert update_data_model("s1")["updateDataModel"]["path"] == "/"     # default whole-model


BASE = {
    "version": A2UI_VERSION,
    "createSurface": {
        "surfaceId": "s1", "catalogId": "a2ui-atoms-v1",
        "components": [{"id": "root", "component": "Column", "children": ["t"]},
                       {"id": "t", "component": "Text", "text": "old"}],
        "dataModel": {"user": {"name": "A"}, "count": 1},
    },
}


def test_update_components_upserts_by_id():
    st = surface_state_from_create(BASE)
    apply_update(st, update_components("s1", [
        {"id": "t", "component": "Text", "text": "new"},     # update existing
        {"id": "t2", "component": "Text", "text": "added"},  # add new
    ]))
    assert st["components"]["t"]["text"] == "new"
    assert st["components"]["t2"]["text"] == "added"
    assert st["components"]["root"]["component"] == "Column"  # untouched


def test_update_data_model_pointer_patch():
    st = surface_state_from_create(BASE)
    apply_update(st, update_data_model("s1", value="B", path="/user/name"))
    assert st["dataModel"]["user"]["name"] == "B"
    assert st["dataModel"]["count"] == 1                      # sibling untouched
    # deep path auto-vivifies intermediate objects
    apply_update(st, update_data_model("s1", value=9, path="/a/b/c"))
    assert st["dataModel"]["a"]["b"]["c"] == 9


def test_update_data_model_whole_replace_and_remove():
    st = surface_state_from_create(BASE)
    apply_update(st, update_data_model("s1", value={"fresh": True}, path="/"))
    assert st["dataModel"] == {"fresh": True}                # path '/' replaces all
    st2 = surface_state_from_create(BASE)
    apply_update(st2, update_data_model("s1", path="/count"))  # value omitted -> remove
    assert "count" not in st2["dataModel"]
    assert "user" in st2["dataModel"]


def test_delete_surface_tears_down():
    st = surface_state_from_create(BASE)
    apply_update(st, delete_surface("s1"))
    assert st["deleted"] is True and st["components"] == {} and st["dataModel"] == {}


def test_surfaceid_guard():
    st = surface_state_from_create(BASE)
    with pytest.raises(ValueError):
        apply_update(st, update_data_model("WRONG", value=1, path="/count"))


def test_poll_result_to_update_compliance():
    ok = poll_result_to_update("s1", {"ok": True, "data": [1, 2], "total": 2}, "/rows")
    _one_key(ok, "updateDataModel")
    assert ok["updateDataModel"]["value"] == {"items": [1, 2], "total": 2}
    assert ok["updateDataModel"]["path"] == "/rows"
    bad = poll_result_to_update("s1", {"ok": False, "error": "boom"}, "/rows")
    assert bad["updateDataModel"]["value"] == {"error": "boom"}


def test_poll_channel_roundtrip():
    """Existing pull-on-a-timer, made compliant: each poll -> updateDataModel that
    applies cleanly onto the surface state."""
    ch = PollChannel("s1", path="/rows")
    st = surface_state_from_create(BASE)
    msg = ch.from_poll({"ok": True, "data": [{"id": 1}], "total": 1})
    apply_update(st, msg)
    assert st["dataModel"]["rows"] == {"items": [{"id": 1}], "total": 1}
    assert len(ch.buffer) == 1


def test_firestore_push_channel_injected_writer():
    """True-push server half: emit() persists the message via an injected writer
    (so it's testable without live Firestore; real writer = trade bot Firestore)."""
    written = []
    ch = FirestorePushChannel("s1", writer=lambda path, m: written.append((path, m)))
    ch.emit(update_data_model("s1", value=42, path="/count"))
    ch.emit(delete_surface("s1"))
    assert written[0][0] == "surface_updates/s1"
    assert written[0][1]["updateDataModel"]["value"] == 42
    assert "deleteSurface" in written[1][1]
    assert isinstance(ch, Channel)


def test_full_incremental_session():
    """createSurface -> a stream of pushes -> the reference client state tracks it."""
    st = surface_state_from_create(BASE)
    for msg in [
        update_data_model("s1", value=2, path="/count"),
        update_components("s1", [{"id": "t", "component": "Text", "text": "live"}]),
        update_data_model("s1", value={"name": "Z"}, path="/user"),
    ]:
        apply_update(st, msg)
    assert st["dataModel"]["count"] == 2
    assert st["components"]["t"]["text"] == "live"
    assert st["dataModel"]["user"] == {"name": "Z"}
    assert st["deleted"] is False
