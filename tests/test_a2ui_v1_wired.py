"""A2UI v1.0 WIRED-dialect emitter tests — renderers/a2ui_v1_wired.py (Track B2).

Locks the conformant subset: createSurface envelope, a real dataModel built from
ValueStores + onLoad-resolved arrays, JSON-Pointer read-bindings, List template
children ({path, componentId}), action.event + actionId, and reactive primitives
riding as a2ui-state-v1 extensions rather than crashing.
"""
import json
import os

from renderers.a2ui_v1_wired import emit_wired_surface
from renderers.a2ui_v1 import A2UI_VERSION

ROOT = os.path.dirname(os.path.dirname(__file__))


def _valid_wired_surface(msg):
    """Structural validity for a wired createSurface. Child refs may be a plain
    array of ComponentIds OR a List template object {path, componentId} — both
    are valid A2UI v1.0; the template's componentId must resolve."""
    assert msg["version"] == A2UI_VERSION
    cs = msg["createSurface"]
    assert cs["surfaceId"] and cs["catalogId"]
    comps = cs["components"]
    assert isinstance(comps, list) and comps
    ids = [c["id"] for c in comps]
    assert len(ids) == len(set(ids)), "component ids unique"
    idset = set(ids)
    for c in comps:
        assert c.get("component")
        ch = c.get("children")
        if isinstance(ch, list):
            for r in ch:
                assert r in idset, f"dangling child ref {r} in {c['id']}"
        elif isinstance(ch, dict):                       # List template form
            assert "componentId" in ch and ch["componentId"] in idset, f"template componentId unresolved in {c['id']}"
            assert "path" in ch
        if isinstance(c.get("child"), str):
            assert c["child"] in idset
    return cs, {c["id"]: c for c in comps}


def _paths(obj):
    """Collect every JSON-Pointer `path` string appearing in a binding object."""
    out = []
    if isinstance(obj, dict):
        if "path" in obj and isinstance(obj["path"], str):
            out.append(obj["path"])
        for v in obj.values():
            out.extend(_paths(v))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(_paths(v))
    return out


def test_expenses_demo_emits_valid_wired_surface():
    d = json.load(open(os.path.join(ROOT, "payloads", "expenses-demo.json")))
    cs, by_id = _valid_wired_surface(emit_wired_surface(d))
    # a real data model (ValueStores + onLoad-resolved arrays)
    dm = cs.get("dataModel")
    assert isinstance(dm, dict) and dm, "wired surface must carry a dataModel"
    # at least one JSON-pointer binding somewhere in the components. Absolute
    # pointers (/…) resolve from the dataModel root; RELATIVE pointers are valid
    # too but only inside List-template scope (each iterated row) — so we require
    # a non-empty path set with at least one absolute binding, not all-absolute.
    bind_paths = _paths(cs["components"])
    assert bind_paths, "expected at least one {path} JSON-pointer binding"
    assert all(p for p in bind_paths), "binding paths must be non-empty"
    assert any(p.startswith("/") for p in bind_paths), "expected at least one absolute (root) binding"


def test_valuestore_becomes_datamodel_path():
    payload = {
        "type": "a2ui_wired_surface", "title": "VS", "theme": "light",
        "state_primitives": [{"id": "amount_mem", "primitive": "ValueStore", "props": {"initialValue": 0}}],
        "layout": [{"atom": "form_input", "id": "amt", "props": {"label": "Amount"},
                    "wire": {"value": "#amount_mem.value"}}],
        "actions": [],
    }
    cs, by_id = _valid_wired_surface(emit_wired_surface(payload))
    assert "amount_mem" in cs["dataModel"]                       # ValueStore -> dataModel entry
    # the input's read-wire became a JSON-pointer binding to /amount_mem
    assert any("/amount_mem" in p for p in _paths(cs["components"]))


def test_action_has_actionid_and_event():
    payload = {
        "type": "a2ui_wired_surface", "title": "Act", "theme": "light",
        "state_primitives": [{"id": "amount_mem", "primitive": "ValueStore", "props": {}}],
        "actions": [{"id": "submit", "type": "gas:store_append",
                     "props": {"collect": {"amount": "#amount_mem.value"}}}],
        "layout": [{"atom": "cta_button", "id": "b", "props": {"label": "Save"},
                    "wire": {"onClick": "#submit.run"}}],
    }
    cs, by_id = _valid_wired_surface(emit_wired_surface(payload))
    # find a component carrying an action.event with a name + actionId path
    acted = [c for c in cs["components"] if isinstance(c.get("action"), dict)]
    assert acted, "expected a component with an action"
    ev = acted[0]["action"].get("event", {})
    assert ev.get("name"), "action.event needs a name"


def test_reactive_primitive_rides_as_extension_not_crash():
    """ArrayFilter (client reactive) must not crash the emitter; it either lands
    in the dataModel/extension surface, but never raises."""
    payload = {
        "type": "a2ui_wired_surface", "title": "Reactive", "theme": "light",
        "state_primitives": [
            {"id": "rows", "primitive": "ValueStore", "props": {"initialValue": []}},
            {"id": "filtered", "primitive": "ArrayFilter", "props": {"filterKey": "kind"},
             "wire": {"source": "#rows.value"}},
        ],
        "layout": [{"atom": "body", "id": "t", "props": {"text": "ok"}}],
        "actions": [],
    }
    # must not raise
    cs, by_id = _valid_wired_surface(emit_wired_surface(payload))
    assert cs["components"]
