"""Capability-aware emitting: a renderer only ever receives component types it
declared. androidx.a2ui (Google's Android renderer, 1.0.0-alpha01) throws on any
unregistered type, so a stock Android app sent one of our atoms loses the whole
surface. Found while testing a Pixel 7 Pro, 2026-10-04."""
import copy

import pytest

from renderers.a2ui_capabilities import (
    BASIC_CATALOG_IDS, BASIC_COMPONENTS, ClientCapabilities, parse_client_capabilities,
)
from renderers.a2ui_v1 import DEFAULT_CATALOG_ID, emit_messages, emit_surface
from tests.a2ui_v1_conformance import AGENT_TO_RENDERER, assert_conforms

V09_BASIC = BASIC_CATALOG_IDS["v0.9"]
V10_BASIC = BASIC_CATALOG_IDS["1.0"]

PAYLOAD = {"title": "Caps", "blocks": [
    {"type": "heading", "text": "Hello"},
    {"type": "callout", "kind": "info", "text": "A callout"},
    {"type": "brick_build_3d", "model": "house"},          # no readable text
    {"type": "info_card", "blocks": [{"type": "brick_build_3d", "model": "car"}]},
    {"type": "cta_button", "label": "Open", "url": "https://a2uicatalog.ai"},
    {"type": "motion_timeline", "title": "A film", "duration": 4,
     "blocks": [{"type": "motion_layer", "id": "s1", "blocks": [{"type": "motion_text", "text": "Hi"}]}]},
]}


def _components(msgs):
    out = []
    for m in msgs:
        body = m.get("createSurface") or m.get("updateComponents") or {}
        out += body.get("components") or []
    return out


def _caps(*ids, key="a2uiClientCapabilities", version="v0.9"):
    return parse_client_capabilities({key: {version: {"supportedCatalogIds": list(ids)}}})


# ── parsing ───────────────────────────────────────────────────────────────────
def test_parses_googles_v09_client_form():
    caps = _caps(V09_BASIC)
    assert caps == ClientCapabilities(version="v0.9", supported_catalog_ids=(V09_BASIC,))
    assert caps.basic_catalog_id == V09_BASIC


def test_parses_v10_spec_renderer_form():
    caps = _caps(DEFAULT_CATALOG_ID, key="a2uiRendererCapabilities", version="1.0")
    assert caps.version == "1.0" and caps.supports(DEFAULT_CATALOG_ID)


def test_v091_emits_as_v09_and_v10_preferred_when_both_offered():
    assert _caps(V09_BASIC, version="v0.9.1").version == "v0.9"
    both = parse_client_capabilities({"a2uiRendererCapabilities": {
        "v0.9": {"supportedCatalogIds": [V09_BASIC]},
        "1.0": {"supportedCatalogIds": [V10_BASIC]}}})
    assert both.version == "1.0"


@pytest.mark.parametrize("meta", [None, {}, {"other": 1}, {"a2uiClientCapabilities": {"v2.0": {}}}, "x"])
def test_no_usable_capabilities_is_none(meta):
    assert parse_client_capabilities(meta) is None


# ── behaviour by client ───────────────────────────────────────────────────────
def test_no_capabilities_is_byte_for_byte_unchanged():
    assert emit_messages(copy.deepcopy(PAYLOAD)) == [emit_surface(copy.deepcopy(PAYLOAD))]


def test_client_with_our_catalogue_gets_the_full_surface():
    full = emit_surface(copy.deepcopy(PAYLOAD))
    ours = emit_surface(copy.deepcopy(PAYLOAD), capabilities=_caps(V09_BASIC, DEFAULT_CATALOG_ID))
    assert ours == full


@pytest.mark.parametrize("basic_id,version", [(V09_BASIC, "v0.9"), (V10_BASIC, "1.0")])
def test_basic_only_client_never_receives_an_undeclared_type(basic_id, version):
    msgs = emit_messages(copy.deepcopy(PAYLOAD), _caps(basic_id, version=version))
    comps = _components(msgs)
    assert comps and all(c["component"] in BASIC_COMPONENTS for c in comps)
    assert msgs[0]["createSurface"]["catalogId"] == basic_id
    ids = {c["id"] for c in comps}
    for c in comps:                                        # every reference resolves
        for ref in (c.get("children") or []) + ([c["child"]] if "child" in c else []):
            assert ref in ids


def test_degradation_keeps_text_reports_everything_and_prunes():
    cs = emit_surface(copy.deepcopy(PAYLOAD), capabilities=_caps(V09_BASIC))["createSurface"]
    by_id = {c["id"]: c for c in cs["components"]}
    report = cs["metadata"]["extensions"]["a2uicatalog_surface"]["degraded"]
    as_of = {(r["type"], r["as"]) for r in report}

    assert ("callout", "Text") in as_of
    assert any(c.get("text") == "A callout" for c in by_id.values())
    assert ("motion_timeline", "Text") in as_of                 # a film degrades to its title
    assert any(c.get("text") == "A film" for c in by_id.values())
    assert not any(c.get("text") == "Hi" for c in by_id.values()), "a composite's inner parts must not leak"
    assert ("brick_build_3d", "dropped") in as_of               # no readable text: dropped...
    for c in by_id.values():                                    # ...and no parent still points at it
        assert all(ref in by_id for ref in c.get("children") or [])
    assert by_id["root"]["component"] == "Column"


def test_required_single_child_becomes_empty_text_not_a_dangling_ref():
    p = {"blocks": [{"type": "info_card", "blocks": [{"type": "brick_build_3d", "model": "car"}]}]}
    comps = emit_surface(p, capabilities=_caps(V09_BASIC))["createSurface"]["components"]
    by_id = {c["id"]: c for c in comps}
    card = next(c for c in comps if c["component"] == "Card")
    assert by_id[card["child"]] == {"id": card["child"], "component": "Text", "text": ""}


def test_renderer_with_no_catalogue_we_can_target_is_an_error():
    with pytest.raises(ValueError, match="no catalogue this emitter can target"):
        emit_surface(copy.deepcopy(PAYLOAD), capabilities=_caps("https://example.com/other.json"))


# ── version target ────────────────────────────────────────────────────────────
def test_v09_splits_components_into_update_components():
    msgs = emit_messages(copy.deepcopy(PAYLOAD), _caps(V09_BASIC, DEFAULT_CATALOG_ID))
    assert [m["version"] for m in msgs] == ["v0.9", "v0.9"]
    assert "components" not in msgs[0]["createSurface"]
    assert msgs[1]["updateComponents"]["surfaceId"] == msgs[0]["createSurface"]["surfaceId"]
    v10 = emit_surface(copy.deepcopy(PAYLOAD))["createSurface"]["components"]
    assert [(c["id"], c["component"]) for c in _components(msgs)] == [(c["id"], c["component"]) for c in v10]


def test_v10_client_gets_one_message():
    msgs = emit_messages(copy.deepcopy(PAYLOAD), _caps(DEFAULT_CATALOG_ID, key="a2uiRendererCapabilities", version="1.0"))
    assert len(msgs) == 1 and msgs[0]["version"] == "1.0"


# ── portable standard components ──────────────────────────────────────────────
def test_v10_headings_stay_markdown_v09_headings_get_the_variant():
    """The v1.0 spec dropped h1-h5 from Text.variant (caption|body only), so a
    v1.0 heading is markdown. v0.9 kept h1-h5 and its hosts need not parse
    markdown, so the v0.9 stream converts."""
    p = {"blocks": [{"type": "heading", "text": "H"}, {"type": "subheading", "text": "S"}]}
    v10 = [c for c in emit_surface(copy.deepcopy(p))["createSurface"]["components"] if c["component"] == "Text"]
    assert [c["text"] for c in v10] == ["# H", "## S"] and not any("variant" in c for c in v10)
    v09 = [c for c in _components(emit_messages(copy.deepcopy(p), _caps(V09_BASIC))) if c["component"] == "Text"]
    assert [(c["text"], c["variant"]) for c in v09] == [("H", "h1"), ("S", "h2")]


def test_degraded_v10_surface_conforms_to_the_real_schema():
    msg = emit_surface(copy.deepcopy(PAYLOAD), capabilities=_caps(V10_BASIC, version="1.0"))
    assert_conforms(msg, AGENT_TO_RENDERER)


# ── key_value keeps its values in the degraded form (Flutter finding 3: two contracts) ──
KV_ITEMS = {"type": "key_value", "title": "Env", "items": [{"key": "API_KEY", "description": "set"}, {"key": "BASE_URL", "description": "https://x.test"}]}
KV_PAIRS = {"type": "key_value", "pairs": [{"key": "A", "value": "1"}, {"key": "B", "value": "2"}]}


@pytest.mark.parametrize("block,expected", [
    (KV_ITEMS, "Env\nAPI_KEY: set\nBASE_URL: https://x.test"),
    (KV_PAIRS, "A: 1\nB: 2"),
])
@pytest.mark.parametrize("version,basic_id", [("v0.9", V09_BASIC), ("1.0", V10_BASIC)])
def test_degraded_key_value_carries_keys_and_values(block, expected, version, basic_id):
    msgs = emit_messages({"blocks": [copy.deepcopy(block)]}, _caps(basic_id, version=version))
    texts = [c["text"] for c in _components(msgs) if c["component"] == "Text"]
    assert texts == [expected]


def test_degraded_key_value_with_no_pairs_falls_back_to_the_title():
    comps = _components(emit_messages({"blocks": [{"type": "key_value", "title": "Only a title"}]}, _caps(V10_BASIC, version="1.0")))
    assert [c["text"] for c in comps if c["component"] == "Text"] == ["Only a title"]


def test_v10_basic_fallback_is_one_v10_create_surface_a_v10_basic_host_accepts():
    """Flutter's v1.0 basicCatalog() has id V10_BASIC and rejects v0.9 wire (CATALOG_NOT_FOUND): a renderer that
    offers the v1.0 Basic Catalog under "1.0" gets one version-"1.0" createSurface on that id, Basic components only."""
    msgs = emit_messages({"blocks": [copy.deepcopy(KV_PAIRS), {"type": "callout", "kind": "info", "text": "hi"}]},
                         _caps(V10_BASIC, key="a2uiRendererCapabilities", version="1.0"))
    assert len(msgs) == 1 and msgs[0]["version"] == "1.0"
    cs = msgs[0]["createSurface"]
    assert cs["catalogId"] == V10_BASIC
    assert all(c["component"] in BASIC_COMPONENTS and "@catalogId" not in c for c in cs["components"])
    assert_conforms(msgs[0], AGENT_TO_RENDERER)


# ── legacy early-draft "v1.0" key is never negotiated (review F4) ─────────────
def _legacy_meta(*versions):
    return {"a2uiClientCapabilities": {v: {"supportedCatalogIds": [V10_BASIC if v == "v1.0" else V09_BASIC]} for v in versions}}


def test_legacy_v1_0_key_never_outranks_v09():
    caps = parse_client_capabilities(_legacy_meta("v1.0", "v0.9"))
    assert caps.version == "v0.9"
    msgs = emit_messages(copy.deepcopy(PAYLOAD), caps)
    assert all(m["version"] == "v0.9" for m in msgs)


def test_legacy_v1_0_key_alone_is_not_negotiated():
    assert parse_client_capabilities(_legacy_meta("v1.0")) is None


def test_final_1_0_key_still_wins_over_v09():
    both = parse_client_capabilities({"a2uiRendererCapabilities": {"v1.0": {"supportedCatalogIds": [V10_BASIC]},
                                                                  "1.0": {"supportedCatalogIds": [V10_BASIC]},
                                                                  "v0.9": {"supportedCatalogIds": [V09_BASIC]}}})
    assert both.version == "1.0"
