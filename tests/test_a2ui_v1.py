"""A2UI v1.0 emitter conformance tests — renderers/a2ui_v1.py.

Locks: envelope/metadata, deterministic flat component list with resolvable
child refs, standard-component mapping, container inversion, action-contract
adapter, and no-crash + structural validity over a real catalogue payload.
"""
import json
import glob
import os
import pytest

from renderers.a2ui_v1 import (
    emit_surface, call_renderer_function, agent_function_response, A2UI_VERSION,
)
from tests.a2ui_v1_conformance import AGENT_TO_RENDERER, assert_conforms

ROOT = os.path.dirname(os.path.dirname(__file__))


def _assert_valid_surface(msg):
    # Real jsonschema validation against the live spec (tests/
    # a2ui_v1_conformance.py, PR 1, 2026-08-24) -- added here so every
    # existing test using this helper gets it, not only the ones touched
    # directly while fixing emit_surface(). Complementary to the checks
    # below, not a replacement: jsonschema can't catch a dangling child
    # ref (a cross-reference semantic, not a structural schema rule).
    assert_conforms(msg, AGENT_TO_RENDERER)
    assert msg["version"] == A2UI_VERSION
    cs = msg["createSurface"]
    assert cs["surfaceId"] and isinstance(cs["surfaceId"], str)
    assert cs["catalogId"]                                   # required in v1.0
    comps = cs["components"]
    assert isinstance(comps, list) and comps
    ids = [c["id"] for c in comps]
    assert len(ids) == len(set(ids)), "component ids must be unique"
    idset = set(ids)
    # every child ref must resolve to a real component (flat list integrity),
    # across all three ref shapes this emitter produces: `children` (Row/
    # Column/Card/Modal-list), singular `child` (real A2UI Card/Modal), and
    # `tabs[].child` (real A2UI Tabs — see hub -> nested-Tabs mapping).
    for c in comps:
        assert c.get("component"), f"component missing type: {c}"
        for ref in c.get("children", []) or []:
            assert ref in idset, f"dangling child ref {ref} in {c['id']}"
        if isinstance(c.get("child"), str):
            assert c["child"] in idset, f"dangling child ref {c['child']} in {c['id']}"
        for tab in c.get("tabs", []) or []:
            assert tab.get("child") in idset, f"dangling tab child ref in {c['id']}"
    assert any(c["id"] == "root" and c["component"] == "Column" for c in comps)
    return cs, {c["id"]: c for c in comps}


SAMPLE = {
    "title": "Demo Surface",
    "theme": "dark",
    "blocks": [
        {"type": "heading", "text": "Hello"},
        {"type": "body", "text": "world"},
        {"type": "image", "url": "http://x/y.png", "alt": "pic", "caption": "cap"},
        {"type": "divider"},
        {"type": "quote", "text": "be honest", "attribution": "C"},
        {"type": "bullet_list", "items": ["a", "b"]},
        {"type": "columns", "items": [
            {"blocks": [{"type": "body", "text": "left"}]},
            {"blocks": [{"type": "body", "text": "right"}]},
        ]},
        {"type": "info_card", "title": "Card", "text": "sub", "blocks": [
            {"type": "body", "text": "inside"},
        ]},
        {"type": "glowing_stat", "value": "42", "label": "answer"},   # extension → pass-through
    ],
}


def test_envelope_and_metadata():
    """2026-08-24: surfaceProperties was removed (not a real v1.0 field) --
    title/theme/catalogs now ride in metadata.extensions.a2uicatalog_surface,
    the real spec's own sanctioned extension point."""
    msg = emit_surface(SAMPLE, catalog_id="a2ui-atoms-v1")
    cs, by_id = _assert_valid_surface(msg)
    props = cs["metadata"]["extensions"]["a2uicatalog_surface"]
    assert props["title"] == "Demo Surface" and props["theme"] == "dark"
    assert cs["catalogId"] == "a2ui-atoms-v1"
    # catalogs is auto-declared, DETERMINISTIC from the payload's atoms:
    # base always present; the glowing_stat extension pulls in a2ui-effects-v1.
    cats = props["catalogs"]
    assert cats[0].endswith("a2ui-atoms-v1.json")                    # base first, always
    assert any(c.endswith("a2ui-effects-v1.json") for c in cats)     # glowing_stat -> effects
    assert cats == sorted(cats[:1]) + sorted(cats[1:])               # base, then sorted extensions


def test_catalog_discovery_reaches_atoms_nested_via_declared_children():
    """Regression guard: before Phase 0 (spec/childlist-migration-v0.1.md), catalog_map's
    collect_types() walked a flat, hand-maintained key-name list that never included
    chat_thread's `messages[].block` — so an atom needing a non-base catalog, buried inside
    a chat_thread message, was silently missing from the declared catalogs list. A host
    that only resolved the declared catalogs would then fail to render it. Now driven by
    schema.yaml's `children:` declarations, so this can't go invisible by field-name
    coincidence again."""
    payload = {
        "title": "Chat with a chart", "blocks": [
            {"type": "chat_thread", "messages": [
                {"role": "assistant", "kind": "atom", "block": {"type": "chartjs_bar", "data": []}},
            ]},
        ],
    }
    msg = emit_surface(payload)
    cats = msg["createSurface"]["metadata"]["extensions"]["a2uicatalog_surface"]["catalogs"]
    assert any(c.endswith("a2ui-charts-v1.json") for c in cats), \
        f"chartjs_bar nested in chat_thread.messages[].block did not surface its catalog: {cats}"


def test_standard_component_mapping():
    _, by_id = _assert_valid_surface(emit_surface(SAMPLE))
    texts = [c for c in by_id.values() if c["component"] == "Text"]
    joined = "\n".join(c.get("text", "") for c in texts)
    assert "# Hello" in joined          # heading -> Text with md prefix
    assert "world" in joined            # body -> Text
    assert "> be honest" in joined      # quote -> Text blockquote
    assert "- a" in joined and "- b" in joined   # bullet_list -> Text bullets
    assert any(c["component"] == "Image" and c["url"] == "http://x/y.png" for c in by_id.values())
    assert any(c["component"] == "Divider" for c in by_id.values())


def test_container_inversion():
    _, by_id = _assert_valid_surface(emit_surface(SAMPLE))
    rows = [c for c in by_id.values() if c["component"] == "Row"]        # columns -> Row
    assert rows and len(rows[0]["children"]) == 2
    cards = [c for c in by_id.values() if c["component"] == "Card"]      # info_card -> Card
    assert cards
    # Real basic-catalog Card takes ONE `child` id (2026-08-24 fix) --
    # multiple items (title/text/nested block) get wrapped in a synthetic
    # Column, resolve through it to find the real leaf content.
    card_child = by_id[cards[0]["child"]]
    assert card_child["component"] == "Column"
    card_kids = [by_id[k] for k in card_child["children"]]
    assert any(k["component"] == "Text" and "Card" in k.get("text", "") for k in card_kids)
    assert any(k.get("text") == "inside" for k in card_kids)


def test_extension_passthrough():
    _, by_id = _assert_valid_surface(emit_surface(SAMPLE))
    ext = [c for c in by_id.values() if c["component"] == "glowing_stat"]
    assert ext, "extension atom must pass through as a catalog-scoped component"
    assert ext[0]["value"] == "42" and ext[0]["label"] == "answer"     # props preserved inline


def test_action_response_was_removed_not_just_broken():
    """2026-08-24: the real spec has no 'actionResponse' message type at
    all -- confirmed by reading renderer_to_agent.json directly. This isn't
    a regression test for behavior that should still exist; it's a lock
    against the function quietly coming back."""
    import renderers.a2ui_v1 as a2ui_v1
    assert not hasattr(a2ui_v1, "action_response")


def test_split_pane_to_row_of_columns():
    """B1: split_pane -> Row with two Columns, one per side, blocks preserved."""
    payload = {
        "title": "Split", "blocks": [
            {"type": "split_pane",
             "left": {"bg": "#f8fafc", "blocks": [{"type": "body", "text": "left side"}]},
             "right": {"bg": "#fff", "blocks": [{"type": "body", "text": "right side"}]}},
        ],
    }
    _, by_id = _assert_valid_surface(emit_surface(payload))
    rows = [c for c in by_id.values() if c["component"] == "Row"]
    assert len(rows) == 1 and len(rows[0]["children"]) == 2
    cols = [by_id[k] for k in rows[0]["children"]]
    assert all(c["component"] == "Column" for c in cols)
    # 2026-08-24: per-side `background` is real, confirmed loss -- Column
    # has no such field in the real basic catalog at all (checked
    # directly). No basic-catalog equivalent exists, same class as hub's
    # own documented color/background drops.
    assert "background" not in cols[0] and "background" not in cols[1]
    texts = [by_id[cid] for c in cols for cid in c["children"]]
    joined = "\n".join(t.get("text", "") for t in texts)
    assert "left side" in joined and "right side" in joined


def test_row_open_close_brackets_to_row():
    """B1: a row_open/row_close bracketed run in a flat block list -> a Row
    wrapping just the bracketed blocks; blocks outside the bracket stay
    top-level siblings, and align flourish is carried onto the Row.
    2026-08-24: `gap` is a confirmed, real drop -- no such field exists on
    the real basic-catalog Row at all (checked directly); `align` IS real
    and is still carried through."""
    payload = {
        "title": "Bracketed", "blocks": [
            {"type": "heading", "text": "Before"},
            {"type": "row_open", "gap": "12px", "align": "center"},
            {"type": "body", "text": "in-row-1"},
            {"type": "body", "text": "in-row-2"},
            {"type": "row_close"},
            {"type": "heading", "text": "After"},
        ],
    }
    _, by_id = _assert_valid_surface(emit_surface(payload))
    rows = [c for c in by_id.values() if c["component"] == "Row"]
    assert len(rows) == 1
    row = rows[0]
    assert row["align"] == "center" and "gap" not in row
    kids = [by_id[k] for k in row["children"]]
    assert len(kids) == 2
    joined = "\n".join(k.get("text", "") for k in kids)
    assert "in-row-1" in joined and "in-row-2" in joined
    # root column has 3 top-level children: heading, the Row, heading — not the
    # bracket markers themselves, and Before/After are siblings of the Row.
    root = by_id["root"]
    assert len(root["children"]) == 3
    root_texts = [by_id[k].get("text", "") for k in root["children"] if by_id[k]["component"] == "Text"]
    assert any("Before" in t for t in root_texts) and any("After" in t for t in root_texts)


def test_hub_to_nested_tabs():
    """B1: hub (subjects[].slides[]) -> nested Tabs, outer = subjects, inner =
    slides, each slide a Column of its blocks. Labels preserved at both
    levels; every tabs[].child ref resolves (checked by _assert_valid_surface)."""
    payload = {
        "title": "Deck", "blocks": [
            {"type": "hub", "background": "#0f172a", "subjects": [
                {"id": "s1", "label": "Subject One", "color": "#6366f1", "slides": [
                    {"id": "sl1", "label": "Slide A", "blocks": [{"type": "body", "text": "slide a body"}]},
                    {"id": "sl2", "label": "Slide B", "blocks": [{"type": "body", "text": "slide b body"}]},
                ]},
                {"id": "s2", "label": "Subject Two", "color": "#10b981", "slides": [
                    {"id": "sl3", "label": "Slide C", "blocks": [{"type": "body", "text": "slide c body"}]},
                ]},
            ]},
        ],
    }
    _, by_id = _assert_valid_surface(emit_surface(payload))
    all_tabs = [c for c in by_id.values() if c["component"] == "Tabs"]
    # outer (1) + one inner Tabs per subject (2) = 3
    assert len(all_tabs) == 3

    # 2026-08-24: real Tabs entries key on `title`, not `label` (confirmed
    # against catalogs/basic/catalog.json directly) -- the SOURCE payload
    # above still uses `label` (this dialect's own input field name); only
    # the emitted wire-format key changed.
    outer = [t for t in all_tabs if {e["title"] for e in t["tabs"]} == {"Subject One", "Subject Two"}]
    assert len(outer) == 1
    outer = outer[0]
    assert len(outer["tabs"]) == 2

    subj_one_inner = by_id[[e["child"] for e in outer["tabs"] if e["title"] == "Subject One"][0]]
    assert subj_one_inner["component"] == "Tabs"
    slide_titles = {e["title"] for e in subj_one_inner["tabs"]}
    assert slide_titles == {"Slide A", "Slide B"}

    slide_a_col = by_id[[e["child"] for e in subj_one_inner["tabs"] if e["title"] == "Slide A"][0]]
    assert slide_a_col["component"] == "Column"
    slide_a_texts = [by_id[k].get("text", "") for k in slide_a_col["children"]]
    assert any("slide a body" in t for t in slide_a_texts)

    subj_two_inner = by_id[[e["child"] for e in outer["tabs"] if e["title"] == "Subject Two"][0]]
    assert {e["title"] for e in subj_two_inner["tabs"]} == {"Slide C"}


def test_call_renderer_function_and_agent_function_response():
    """2026-08-24: replaces the old call_function()/function_response() —
    confirmed via the real schema that v1.0 has two direction-specific
    pairs, not one bidirectional callFunction/functionResponse (which
    never existed in the real protocol at all). Both messages here are
    validated against the REAL schema (assert_conforms), not just checked
    for the shape this test expects -- that's what would have caught the
    original drift in the first place."""
    # openUrl: a real basic-catalog function (confirmed against
    # catalogs/basic/catalog.json's own anyFunction list) -- an invented
    # name fails validation for a DIFFERENT reason than what's under test.
    call_msg = call_renderer_function(
        "https://a2ui.org/specification/v1_0/catalog.json",
        "openUrl", args={"url": "https://example.com"}, function_call_id="fc-1")
    assert call_msg["version"] == A2UI_VERSION
    assert call_msg["callRendererFunction"]["functionCallId"] == "fc-1"
    assert call_msg["callRendererFunction"]["callFunction"] == {
        "catalogId": "https://a2ui.org/specification/v1_0/catalog.json",
        "call": "openUrl", "args": {"url": "https://example.com"}}
    assert "wantResponse" not in call_msg   # not a real field, confirmed 2026-08-24
    assert_conforms(call_msg, AGENT_TO_RENDERER)

    # auto-minted functionCallId when omitted
    auto = call_renderer_function("https://a2uicatalog.ai/catalogue/a2ui-atoms-v1.json", "ping")
    assert auto["callRendererFunction"]["functionCallId"].startswith("ping-")

    ok = agent_function_response({"ok": True, "data": [1920, 1080]}, "fc-1")
    assert ok["version"] == A2UI_VERSION
    assert ok["agentFunctionResponse"] == {"functionCallId": "fc-1", "value": [1920, 1080]}
    assert_conforms(ok, AGENT_TO_RENDERER)

    bad = agent_function_response({"ok": False, "error": "denied"}, "fc-2")
    assert bad["agentFunctionResponse"] == {
        "functionCallId": "fc-2", "error": {"code": "function_call_failed", "message": "denied"}}
    assert_conforms(bad, AGENT_TO_RENDERER)


def test_all_declared_children_atoms_are_flattened():
    """Regression guard for the 2026-07-08 silent-gap class: module_map, chat_thread,
    playbook, quiz_set, atom_anatomy, blur_fade_in previously fell through to raw
    pass-through with nested atoms still embedded — non-conformant with v1.0's
    ChildList rule, and nothing caught it (same shape as the original module_map MCP
    incident, different codepath). Every atom that declares a `children:` block in
    schema.yaml and isn't already explicitly handled by a hand-written container case
    (_EXPLICITLY_HANDLED_TYPES) must, when emitted, replace EVERY declared child field
    with ID ref(s) — never leave a raw dict. Synthesizes a minimal payload per
    declared shape rather than hand-writing one per atom, so a NEW atom that later
    declares `children:` is covered automatically, with no test to remember to add."""
    from renderers.a2ui_v1 import _atom_children_schema, _EXPLICITLY_HANDLED_TYPES
    decl_by_type = _atom_children_schema()
    checked = 0
    for atom_type, decl in decl_by_type.items():
        if atom_type in _EXPLICITLY_HANDLED_TYPES:
            continue
        block = {"type": atom_type}
        for field, spec in decl.items():
            shape = spec["shape"]
            leaf = {"type": "body", "text": "x"}
            if shape == "simple":
                block[field] = [dict(leaf)]
            elif shape == "single":
                block[field] = dict(leaf)
            elif shape == "wrapper_list":
                inner = spec["inner_path"].split(".")[0]
                block[field] = [{"id": "w1", inner: [dict(leaf)]}]
            elif shape == "wrapper_single":
                inner = spec["inner_path"].split(".")[0]
                block[field] = {inner: [dict(leaf)]}
        _, by_id = _assert_valid_surface(emit_surface({"title": "t", "blocks": [block]}))
        emitted = by_id.get(f"{atom_type}-0")
        assert emitted is not None, f"{atom_type}: expected component id '{atom_type}-0' not found"
        for field in decl:
            val = emitted.get(field)
            assert val is not None, f"{atom_type}.{field}: declared child field missing from emitted component"
            if isinstance(val, list):
                assert all(isinstance(v, str) for v in val), \
                    f"{atom_type}.{field}: expected a list of ID refs, found raw embedded content"
            else:
                assert isinstance(val, str), \
                    f"{atom_type}.{field}: expected an ID ref (string), found raw embedded content"
        checked += 1
    assert checked >= 6, f"expected to cover at least the 6 originally-uncovered atoms, covered {checked}"


def test_real_payload_smoke():
    """Any real blocks-dialect payload must emit a structurally valid surface."""
    checked = 0
    for path in sorted(glob.glob(os.path.join(ROOT, "payloads", "*.json"))):
        try:
            d = json.load(open(path))
        except Exception:
            continue
        if not (isinstance(d, dict) and isinstance(d.get("blocks"), list) and d["blocks"]):
            continue
        _assert_valid_surface(emit_surface(d))
        checked += 1
        if checked >= 5:
            break
    assert checked >= 1, "expected at least one blocks-dialect payload to validate"


def test_childlist_v1_course_fixture():
    """Locks the exact scenario empirically verified against the LIVE GAS renderer
    (spec/childlist-migration-v0.1.md Phase 1, a2ui-private, 2026-07-09) — a course
    payload mixing standard-mapped atoms (heading/body -> Text), a container
    (columns -> Row of Columns), and an extension atom with inline data
    (brevet_timeline, its `events` array untouched, not resolved as child refs).
    This test locks the EMIT shape; the render-side proof is manual (curl against
    the deployed demo renderer — no automated GAS render-output harness exists yet,
    confirmed absent by this session's own investigation) and is not re-run here.
    A regression in this test means the GAS decode shim's assumptions about this
    shape (Code.gs:_rehydrateV1Surface, atoms_v1_standard.gs) may now be stale."""
    payload = json.load(open(os.path.join(ROOT, "tests", "fixtures", "childlist_v1_course_2026-07-09.json")))
    msg = emit_surface(payload)
    cs, by_id = _assert_valid_surface(msg)

    # standard-mapped atoms became Text
    texts = [c for c in by_id.values() if c.get("component") == "Text"]
    assert any("Web Dev 101" in c.get("text", "") for c in texts)
    assert any("Lesson 1: HTML" in c.get("text", "") for c in texts)
    assert any("Lesson 2: CSS" in c.get("text", "") for c in texts)

    # columns -> a Row containing two Columns, each with 2 Text children
    rows = [c for c in by_id.values() if c.get("component") == "Row"]
    assert len(rows) == 1
    cols = [by_id[cid] for cid in rows[0]["children"]]
    assert all(c["component"] == "Column" for c in cols)
    assert all(len(c["children"]) == 2 for c in cols)

    # brevet_timeline is an extension atom with no declared children — passes
    # through with its OWN type as `component`, `events` untouched as inline data
    # (NOT resolved as child refs — it's a data array, not nested atoms)
    timelines = [c for c in by_id.values() if c.get("component") == "brevet_timeline"]
    assert len(timelines) == 1
    assert timelines[0]["title"] == "Course milestones"
    assert timelines[0]["events"] == payload["blocks"][-1]["events"], \
        "events must pass through as literal data, not get resolved as ChildList refs"
