"""v1.0 catalog resolution (evolution_guide 2.7) for emitter output, wired payloads, and surfaceId uniqueness.

A component resolves via its own `catalogId`, else the surface default, else it is not rendered. The default
output therefore names the Basic v1.0 catalog on the surface and our catalogue on each extension component."""
import copy
import glob
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from renderers.a2ui_v1 import emit_surface, emit_messages, BASIC_V1_CATALOG_ID, DEFAULT_CATALOG_ID  # noqa: E402
from renderers.a2ui_v1_wired import emit_wired_surface, DEFAULT_STATE_CATALOG_ID  # noqa: E402
from renderers.a2ui_capabilities import ClientCapabilities, BASIC_CATALOG_IDS  # noqa: E402
from tests.a2ui_v1_conformance import AGENT_TO_RENDERER  # noqa: E402

SAVED_BASIC = json.load(open(os.path.join(ROOT, "tests/fixtures/a2ui_v1_0_spec/catalogs/basic/catalog.json")))
BASIC_NAMES = set(SAVED_BASIC["components"])
EXT_CATALOGS = {DEFAULT_CATALOG_ID, DEFAULT_STATE_CATALOG_ID}


def _resolve_all(cs):
    """Apply the spec's rule to every component; return (component, catalogId) pairs, raising on no catalog."""
    out = []
    for c in cs["components"]:
        cid = c.get("catalogId") or cs.get("catalogId")
        assert cid, f"{c['id']}: neither a component nor a surface catalogId"
        out.append((c, cid))
    return out


def _assert_resolves(cs):
    for c, cid in _resolve_all(cs):
        if cid == BASIC_V1_CATALOG_ID:
            assert c["component"] in BASIC_NAMES, f"{c['id']}: {c['component']} is not in the saved Basic catalog"
        else:
            assert cid in EXT_CATALOGS, (c["id"], cid)
            assert c["component"] not in BASIC_NAMES, f"{c['id']}: Basic component pinned to {cid}"


def _sample():
    import build_web_preview as b
    return [(k, {"title": k, "blocks": [dict(b.DEMO[k], type=k)]}) for k in sorted(b.DEMO)]


def test_basic_catalog_id_matches_the_saved_catalog():
    assert SAVED_BASIC["catalogId"] == BASIC_V1_CATALOG_ID == BASIC_CATALOG_IDS["1.0"]


def test_default_emit_resolves_against_the_saved_basic_catalog_for_every_demo_atom():
    seen_ext = seen_basic = 0
    for k, payload in _sample():
        cs = emit_surface(copy.deepcopy(payload))["createSurface"]
        assert cs["catalogId"] == BASIC_V1_CATALOG_ID, k
        _assert_resolves(cs)
        seen_ext += sum(1 for c in cs["components"] if c.get("catalogId"))
        seen_basic += sum(1 for c in cs["components"] if not c.get("catalogId"))
    assert seen_ext > 100 and seen_basic > 100          # both kinds are exercised


def test_explicit_catalog_id_names_the_extension_components():
    cs = emit_surface({"blocks": [{"type": "glowing_stat", "value": "1"}]}, catalog_id="https://x.test/c.json")["createSurface"]
    assert cs["catalogId"] == BASIC_V1_CATALOG_ID
    assert [c["catalogId"] for c in cs["components"] if c["component"] == "glowing_stat"] == ["https://x.test/c.json"]


def test_extension_component_with_catalogid_still_validates():
    m = emit_surface({"blocks": [{"type": "glowing_stat", "value": "1"}, {"type": "body", "text": "t"}]})
    assert not list(AGENT_TO_RENDERER.iter_errors(m))


def test_basic_only_client_gets_a_pure_basic_surface_without_per_component_ids():
    caps = ClientCapabilities("1.0", (BASIC_V1_CATALOG_ID,))
    cs = emit_surface({"blocks": [{"type": "glowing_stat", "value": "1", "label": "L"}]}, capabilities=caps)["createSurface"]
    assert cs["catalogId"] == BASIC_V1_CATALOG_ID and not any("catalogId" in c for c in cs["components"])


def test_v09_path_is_unchanged_by_the_catalog_split():
    caps = ClientCapabilities("v0.9", (DEFAULT_CATALOG_ID,))
    msgs = emit_messages({"blocks": [{"type": "glowing_stat", "value": "1"}, {"type": "body", "text": "t"}]}, caps)
    assert msgs[0]["createSurface"]["catalogId"] == DEFAULT_CATALOG_ID
    comps = msgs[-1]["updateComponents"]["components"]
    assert comps and not any("catalogId" in c for c in comps)


# ── wired emitter: all repo wired payloads ───────────────────────────────────────
WIRED = []
for _f in sorted(glob.glob(os.path.join(ROOT, "payloads", "**", "*.json"), recursive=True)):
    try:
        _d = json.load(open(_f))
    except Exception:
        continue
    if isinstance(_d, dict) and _d.get("type") == "a2ui_wired_surface":
        WIRED.append((os.path.basename(_f), _d))


def test_there_are_13_wired_payloads():
    assert len(WIRED) == 13


@pytest.mark.parametrize("name,payload", WIRED, ids=[n for n, _ in WIRED])
def test_wired_payload_validates_and_resolves(name, payload):
    m = emit_wired_surface(copy.deepcopy(payload))
    assert not list(AGENT_TO_RENDERER.iter_errors(m)), name
    cs = m["createSurface"]
    assert cs["catalogId"] == BASIC_V1_CATALOG_ID
    _assert_resolves(cs)
    for c in cs["components"]:
        if c["component"] in BASIC_NAMES:
            assert "wire" not in c and "inputType" not in c and "type" not in c, (name, c)


def test_wired_textfield_input_type_becomes_variant_and_wires_move_to_metadata():
    p = {"type": "a2ui_wired_surface", "title": "w", "layout": [
        {"atom": "text_input", "id": "pw", "props": {"label": "PIN", "inputType": "password", "accent": "x"}, "wire": {"onFoo": "#nope.bar"}},
        {"atom": "textarea", "id": "ta", "props": {"label": "Notes"}}]}
    cs = emit_wired_surface(p)["createSurface"]
    by = {c["id"]: c for c in cs["components"]}
    assert by["pw"]["variant"] == "obscured" and by["ta"]["variant"] == "longText"
    meta = cs["metadata"]["extensions"]["a2uicatalog_wired"]
    assert meta["componentWires"]["pw"] == {"onFoo": "#nope.bar"} and meta["componentProps"]["pw"] == {"accent": "x"}


# ── surfaceId ────────────────────────────────────────────────────────────────────
def test_two_surfaces_with_the_same_title_get_distinct_ids_and_the_same_payload_the_same_id():
    a = {"title": "Report", "blocks": [{"type": "body", "text": "a"}]}
    b = {"title": "Report", "blocks": [{"type": "body", "text": "b"}]}
    ida, idb = (emit_surface(x)["createSurface"]["surfaceId"] for x in (a, b))
    assert ida != idb and ida.startswith("report-") and idb.startswith("report-")
    assert emit_surface(copy.deepcopy(a))["createSurface"]["surfaceId"] == ida
    w1 = emit_wired_surface({"type": "a2ui_wired_surface", "layout": [{"atom": "heading", "props": {"text": "1"}}]})
    w2 = emit_wired_surface({"type": "a2ui_wired_surface", "layout": [{"atom": "heading", "props": {"text": "2"}}]})
    assert w1["createSurface"]["surfaceId"] != w2["createSurface"]["surfaceId"]


def test_explicit_surface_id_wins():
    assert emit_surface({"blocks": []}, surface_id="mine")["createSurface"]["surfaceId"] == "mine"


def test_no_unprefixed_binding_is_emitted_anywhere_in_the_demo_sweep():
    """Review: a leftover {"path": ...} in a context validates (it is a literal in 1.0), so only a walk catches it."""
    def walk(o):
        if isinstance(o, dict):
            yield o
            for v in o.values():
                yield from walk(v)
        elif isinstance(o, list):
            for v in o:
                yield from walk(v)
    for k, payload in _sample():
        cs = emit_surface(copy.deepcopy(payload))["createSurface"]
        assert not [o for o in walk(cs["components"]) if set(o) == {"path"}], k
