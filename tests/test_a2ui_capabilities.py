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
V10_BASIC = BASIC_CATALOG_IDS["v1.0"]

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
    caps = _caps(DEFAULT_CATALOG_ID, key="a2uiRendererCapabilities", version="v1.0")
    assert caps.version == "v1.0" and caps.supports(DEFAULT_CATALOG_ID)


def test_v091_emits_as_v09_and_v10_preferred_when_both_offered():
    assert _caps(V09_BASIC, version="v0.9.1").version == "v0.9"
    both = parse_client_capabilities({"a2uiRendererCapabilities": {
        "v0.9": {"supportedCatalogIds": [V09_BASIC]},
        "v1.0": {"supportedCatalogIds": [V10_BASIC]}}})
    assert both.version == "v1.0"


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


@pytest.mark.parametrize("basic_id,version", [(V09_BASIC, "v0.9"), (V10_BASIC, "v1.0")])
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
    msgs = emit_messages(copy.deepcopy(PAYLOAD), _caps(DEFAULT_CATALOG_ID, key="a2uiRendererCapabilities", version="v1.0"))
    assert len(msgs) == 1 and msgs[0]["version"] == "v1.0"


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
    msg = emit_surface(copy.deepcopy(PAYLOAD), capabilities=_caps(V10_BASIC, version="v1.0"))
    assert_conforms(msg, AGENT_TO_RENDERER)
