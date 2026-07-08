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
    emit_surface, action_response, call_function, function_response, A2UI_VERSION,
)

ROOT = os.path.dirname(os.path.dirname(__file__))


def _assert_valid_surface(msg):
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
    msg = emit_surface(SAMPLE, catalog_id="a2ui-atoms-v1")
    cs, by_id = _assert_valid_surface(msg)
    props = cs["surfaceProperties"]
    assert props["title"] == "Demo Surface" and props["theme"] == "dark"
    assert cs["catalogId"] == "a2ui-atoms-v1"
    # surfaceProperties.catalogs is auto-declared, DETERMINISTIC from the payload's atoms:
    # base always present; the glowing_stat extension pulls in a2ui-effects-v1.
    cats = props["catalogs"]
    assert cats[0].endswith("a2ui-atoms-v1.json")                    # base first, always
    assert any(c.endswith("a2ui-effects-v1.json") for c in cats)     # glowing_stat -> effects
    assert cats == sorted(cats[:1]) + sorted(cats[1:])               # base, then sorted extensions


def test_catalog_discovery_reaches_atoms_nested_via_declared_children():
    """Regression guard: before Phase 0 (spec/childlist-migration-v0.1.md), catalog_map's
    collect_types() walked a flat, hand-maintained key-name list that never included
    chat_thread's `messages[].block` — so an atom needing a non-base catalog, buried inside
    a chat_thread message, was silently missing from surfaceProperties.catalogs. A host
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
    cats = msg["createSurface"]["surfaceProperties"]["catalogs"]
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
    # card's title/text became leading Text children + the nested block
    card_kids = [by_id[k] for k in cards[0]["children"]]
    assert any(k["component"] == "Text" and "Card" in k.get("text", "") for k in card_kids)
    assert any(k.get("text") == "inside" for k in card_kids)


def test_extension_passthrough():
    _, by_id = _assert_valid_surface(emit_surface(SAMPLE))
    ext = [c for c in by_id.values() if c["component"] == "glowing_stat"]
    assert ext, "extension atom must pass through as a catalog-scoped component"
    assert ext[0]["value"] == "42" and ext[0]["label"] == "answer"     # props preserved inline


def test_action_contract_adapter():
    ok = action_response({"ok": True, "data": [1, 2], "total": 2}, "a1")
    assert ok["actionResponse"]["value"] == {"items": [1, 2], "total": 2}
    assert "error" not in ok["actionResponse"]
    bad = action_response({"ok": False, "error": "nope"}, "a2")
    assert bad["actionResponse"]["error"]["message"] == "nope"
    assert "value" not in bad["actionResponse"]
    assert ok["actionId"] == "a1" and bad["version"] == A2UI_VERSION


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
    assert cols[0]["background"] == "#f8fafc" and cols[1]["background"] == "#fff"
    texts = [by_id[cid] for c in cols for cid in c["children"]]
    joined = "\n".join(t.get("text", "") for t in texts)
    assert "left side" in joined and "right side" in joined


def test_row_open_close_brackets_to_row():
    """B1: a row_open/row_close bracketed run in a flat block list -> a Row
    wrapping just the bracketed blocks; blocks outside the bracket stay
    top-level siblings, and gap/align flourish is carried onto the Row."""
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
    assert row["gap"] == "12px" and row["align"] == "center"
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

    outer = [t for t in all_tabs if {e["label"] for e in t["tabs"]} == {"Subject One", "Subject Two"}]
    assert len(outer) == 1
    outer = outer[0]
    assert len(outer["tabs"]) == 2

    subj_one_inner = by_id[[e["child"] for e in outer["tabs"] if e["label"] == "Subject One"][0]]
    assert subj_one_inner["component"] == "Tabs"
    slide_labels = {e["label"] for e in subj_one_inner["tabs"]}
    assert slide_labels == {"Slide A", "Slide B"}

    slide_a_col = by_id[[e["child"] for e in subj_one_inner["tabs"] if e["label"] == "Slide A"][0]]
    assert slide_a_col["component"] == "Column"
    slide_a_texts = [by_id[k].get("text", "") for k in slide_a_col["children"]]
    assert any("slide a body" in t for t in slide_a_texts)

    subj_two_inner = by_id[[e["child"] for e in outer["tabs"] if e["label"] == "Subject Two"][0]]
    assert {e["label"] for e in subj_two_inner["tabs"]} == {"Slide C"}


def test_call_function_and_function_response():
    call_msg = call_function("getScreenResolution", args={"screenIndex": 0}, function_call_id="fc-1")
    assert call_msg["version"] == A2UI_VERSION
    assert call_msg["functionCallId"] == "fc-1"
    assert call_msg["wantResponse"] is True
    assert call_msg["callFunction"] == {"call": "getScreenResolution", "args": {"screenIndex": 0}}

    # auto-minted functionCallId when omitted
    auto = call_function("ping")
    assert auto["functionCallId"].startswith("ping-")

    ok = function_response({"ok": True, "data": [1920, 1080]}, "fc-1", "getScreenResolution")
    assert ok["version"] == A2UI_VERSION
    assert ok["functionResponse"] == {
        "functionCallId": "fc-1", "call": "getScreenResolution", "value": [1920, 1080],
    }
    assert "error" not in ok

    bad = function_response({"ok": False, "error": "denied"}, "fc-2", "getScreenResolution")
    assert "functionResponse" not in bad
    assert bad["error"] == {"code": "function_call_failed", "message": "denied", "functionCallId": "fc-2"}


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
