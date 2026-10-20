"""decision_tree `layout: "tree"` (I44): the nested {text, children} payload drawn as a static top-down tidy tree (d3-hierarchy 3.1.2 tree()), reusing
org_chart's layout port and node boxes. Absent / unknown `layout` is today's collapsible outline, byte for byte.

GOLDEN (tests/fixtures/decision_tree_d3_golden.json): what the REAL d3.tree().nodeSize([1, 1]) produced for decision-tree-shaped payloads (see the generator).
Both twins must reproduce the x positions to 1e-9 (org_chart's own tolerance: the shared _oc_layout keeps d3's operation order) and the depths exactly.

BASELINE (tests/fixtures/decision_tree_baseline.json): the output of the UNMODIFIED renderers (Python and the wired Apps Script one) for the payloads in OUTLINE.
Only the wired Apps Script renderer has org_chart's tree port; the older gas-schema-renderer / fakes / starter copies render the outline for every layout.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from test_motion_atoms import _gas_batch, _node, _py, core_js  # noqa: F401
from test_motion_atoms import wa  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
D = json.loads((ROOT / "tests/fixtures/decision_tree_d3_golden.json").read_text())
CASES = {**D["golden"], **{f"fuzz{i}": c for i, c in enumerate(D["fuzz"])}}
ATTACK = '"><img src=x onerror=alert(1)>\'"><svg onload=alert(1)></script><script>alert(4)</script> onmouseover=alert(2)'


def T(text, *kids):
    return {"text": text, "children": list(kids)} if kids else {"text": text}


def chain(n):
    node = T(str(n))
    for i in range(n - 1, 0, -1):
        node = T(str(i), node)
    return node


NESTED = {"type": "decision_tree", "title": "Should we ship?",
          "nodes": [T("Tests pass?", T("Yes: ship"), T("No: fix first", T("Re-run <b>CI</b>")))]}
OUTLINE = {
    "nested": NESTED,
    "graph": {"type": "decision_tree", "title": "Graph form", "nodes": [{"id": "a", "label": "Start", "type": "question", "children": [{"label": "go", "next": "b"}]}, {"id": "b", "label": "End", "type": "leaf"}]},
    "no_title": {"type": "decision_tree", "nodes": [T("Q", T("A"), T("B"))]},
    "empty": {"type": "decision_tree", "nodes": []},
    "no_nodes": {"type": "decision_tree", "title": "T"},
    "forest": {"type": "decision_tree", "nodes": [T("One", T("a")), T("Two", T("b", T("c")))]},
    "aliases": {"type": "decision_tree", "nodes": [{"question": "Q?", "branches": [{"label": "L1"}, {"text": "T1"}]}]},
    "deep_ten": {"type": "decision_tree", "nodes": [chain(10)]},
    "wide": {"type": "decision_tree", "nodes": [T("root", *[T("child %d" % i) for i in range(40)])]},
    "hostile": {"type": "decision_tree", "title": ATTACK, "nodes": [T(ATTACK, T(ATTACK))]},
    "junk_children": {"type": "decision_tree", "nodes": [{"text": "x", "children": "ab"}, {"text": "y", "children": [1, None, {"text": "z"}]}]},
}
BASELINE = json.loads((ROOT / "tests/fixtures/decision_tree_baseline.json").read_text())
JUNK = [None, "outline", "Tree", "TREE", "tree ", "radial", "cluster", "", 0, 1, True, [], ["tree"], {}, {"layout": "tree"}]


def _pyx(b):
    try:
        return _py(b)
    except Exception as e:  # noqa: BLE001
        return "!" + type(e).__name__


def test_baseline_covers_every_payload():
    assert set(BASELINE["python"]) == set(OUTLINE) == set(BASELINE["gas"])


@pytest.mark.parametrize("name", list(OUTLINE))
def test_absent_layout_is_todays_outline_in_python(name):
    assert _pyx(OUTLINE[name]) == BASELINE["python"][name]


def test_absent_layout_is_todays_outline_in_gas(core_js):
    assert dict(zip(OUTLINE, _gas_batch(core_js, list(OUTLINE.values())))) == BASELINE["gas"]


@pytest.mark.parametrize("junk", JUNK, ids=lambda j: json.dumps(j))
def test_unknown_layouts_render_todays_outline_in_both_twins(junk, core_js):
    blocks = [{**b, "layout": junk} for b in OUTLINE.values()]
    assert [_pyx(b) for b in blocks] == [BASELINE["python"][n] for n in OUTLINE]
    assert _gas_batch(core_js, blocks) == [BASELINE["gas"][n] for n in OUTLINE]


def test_version_one_and_junk_versions_change_nothing(core_js):
    for v in (1, 0, "2", 2.5, None, [2]):
        blocks = [{**b, "version": v} for b in OUTLINE.values()]
        assert [_pyx(b) for b in blocks] == [BASELINE["python"][n] for n in OUTLINE], v
        assert _gas_batch(core_js, blocks) == [BASELINE["gas"][n] for n in OUTLINE], v


# ─── the layout against real d3 ────────────────────────────────────────────────
def _flat_py(nodes):
    r = wa._dt_flatten(nodes)
    assert r[0] is not None
    return r


@pytest.mark.parametrize("name", list(CASES))
def test_python_layout_matches_d3(name):
    g = CASES[name]
    flat, top = _flat_py(g["nodes"])
    kids = [f["kids"] for f in flat]
    ws = [wa._oc_width(f["t"], f["depth"] == 0) for f in flat]
    if g["virt"]:
        kids.append(top)
        ws.append(0)
    assert kids == g["kids"] and ws == g["w"] and [f["l"] for f in flat] == g["labels"]
    x, depth = wa._oc_layout(kids, len(flat) if g["virt"] else top[0], ws)
    assert len(x) == len(g["x"]) and all(abs(a - b) <= 1e-9 for a, b in zip(x, g["x"])), (x, g["x"])
    assert list(depth) == g["depth"]


def test_gas_layout_matches_d3(core_js):
    names = list(CASES)
    body = ("var G = " + json.dumps([CASES[n]["nodes"] for n in names]) +
            "; console.log(JSON.stringify(G.map(function(nodes){ var r = _dtFlatten(nodes); var kids = r.flat.map(function(f){return f.kids;}), "
            "ws = r.flat.map(function(f){return _ocWidth(f.t, f.depth === 0);}); var virt = r.top.length !== 1; "
            "if (virt) { kids.push(r.top); ws.push(0); } var lay = _ocLayout(kids, virt ? r.flat.length : r.top[0], ws); "
            "return [kids, ws, lay[0], lay[1], r.flat.map(function(f){return f.l;})]; })));")
    res = _node(core_js, body)
    for n, (kids, ws, x, depth, labels) in zip(names, res):
        g = CASES[n]
        assert kids == g["kids"] and ws == g["w"] and labels == g["labels"], n
        assert all(abs(a - b) <= 1e-9 for a, b in zip(x, g["x"])) and depth == g["depth"], n


def test_the_golden_covers_the_hard_cases():
    g = D["golden"]
    assert g["forest"]["virt"] and not g["ship"]["virt"] and len(g["deep_six_levels"]["x"]) == 10 and max(g["deep_six_levels"]["depth"]) == 5
    assert any(c["virt"] for c in D["fuzz"]) and any(not c["virt"] for c in D["fuzz"]) and max(len(c["labels"]) for c in D["fuzz"]) > 15


# ─── the drawn tree ───────────────────────────────────────────────────────────
def _tree(nodes, **kw):
    return {"type": "decision_tree", "layout": "tree", "title": "T", "nodes": nodes, **kw}


PAYLOADS = {
    "ship": _tree(NESTED["nodes"]),
    "single": _tree([T("Only node")]),
    "wide_root": _tree(CASES["wide_root"]["nodes"]),
    "forest": _tree(CASES["forest"]["nodes"]),
    "six_levels": _tree(CASES["deep_six_levels"]["nodes"]),
    "long_labels": _tree(CASES["long_labels"]["nodes"]),
    "thirty_one": _tree([T("root", *[T("c%d" % i, *[T("g%d.%d" % (i, j)) for j in range(2)]) for i in range(10)])]),
    "aliases": _tree([{"question": "Q?", "branches": [{"label": "L1"}, {"text": "T1"}]}]),
    "junk_children": _tree([{"text": "x", "children": "ab"}, {"text": "y", "children": [1, None, {"text": "z"}]}]),
    "hostile": _tree([T(ATTACK[:30], T(ATTACK[:30]))], title=ATTACK),
    "version2": _tree(NESTED["nodes"], version=2),
    "no_title": {"type": "decision_tree", "layout": "tree", "nodes": [T("Q", T("A"), T("B"))]},
    # fall back to the outline, with a note
    "too_many_nodes": _tree([T("root", *[T("child %d" % i) for i in range(31)])]),
    "too_deep": _tree([chain(7)]),
    "long_label": _tree([T("Q", T("x" * 33))]),
    "graph_form": {"type": "decision_tree", "layout": "tree", "nodes": OUTLINE["graph"]["nodes"]},
}
FALLBACK = ("too_many_nodes", "too_deep", "long_label", "graph_form")
DRAWN = [n for n in PAYLOADS if n not in FALLBACK]


@pytest.mark.parametrize("name", DRAWN)
def test_python_and_gas_emit_identical_html(name, core_js):
    assert _py(PAYLOADS[name]) == _gas_batch(core_js, [PAYLOADS[name]])[0]


@pytest.mark.parametrize("name", list(PAYLOADS))
def test_never_prints_junk(name):
    h = re.sub(r"<style>.*?</style>", "", _py(PAYLOADS[name]), flags=re.S)
    for bad in ("NaN", "undefined", "Infinity", "[object Object]", "None", "True", "False"):
        assert bad not in h, (name, bad)


def _first(h):
    """A tree wider than 640 px is drawn twice (top-down and left-to-right, CSS shows one, as org_chart does); look at the first."""
    return h.split('<div class="ocl"')[0]


def _boxes(h):
    h = _first(h)
    return re.findall(r'<div style="position:absolute;left:([\d.]+)%;top:([\d.]+)%;width:([\d.]+)%;height:(\d+)px;[^"]*">([^<]*)</div>', h)


@pytest.mark.parametrize("name", DRAWN)
def test_every_node_is_drawn_once_and_the_hierarchy_is_a_nested_list(name):
    h = _py(PAYLOADS[name])
    flat, top = wa._dt_flatten(PAYLOADS[name]["nodes"])
    labels = [wa._cv_esc(f["l"]) for f in flat]
    assert [b[4] for b in _boxes(h)] == labels                                         # every node, in pre-order
    assert "<details" not in h and "<canvas" not in h and "<script" not in h
    h1 = _first(h)
    assert h1.count("<li") == len(flat) and h1.count("<ul") == 1 + sum(1 for f in flat if f["kids"])      # <ul><li> nesting carries the hierarchy for a screen reader
    assert h1.count("<svg") == 1 and 'aria-hidden="true"' in h and 'data-oc=' in h


def test_boxes_follow_the_d3_layout():
    h = _py(PAYLOADS["ship"])
    flat, top = wa._dt_flatten(PAYLOADS["ship"]["nodes"])
    kids = [f["kids"] for f in flat]
    ws = [wa._oc_width(f["t"], f["depth"] == 0) for f in flat]
    x, depth = wa._oc_layout(kids, top[0], ws)
    lo = min(x[i] - ws[i] / 2 for i in range(len(flat)))
    wid = max(x[i] + ws[i] / 2 for i in range(len(flat))) - lo
    for i, (l, t, w, hh, txt) in enumerate(_boxes(h)):
        assert abs(float(l) - (x[i] - ws[i] / 2 - lo) / wid * 100) < 0.0011, i
        assert abs(float(w) - ws[i] / wid * 100) < 0.0011


def test_a_forest_gets_an_undrawn_root_and_no_extra_box():
    h = _py(PAYLOADS["forest"])
    assert len(_boxes(h)) == 7 and _first(h).count("<li") == 7


def test_text_is_escaped_and_whole():
    h = _py(PAYLOADS["hostile"])
    assert "<img" not in h and "<script>" not in h and "&lt;img" in h
    assert "<b>CI</b>" not in _py(_tree(NESTED["nodes"])) and "Re-run &lt;b&gt;CI&lt;/b&gt;" in _py(_tree(NESTED["nodes"]))


def test_aliases_children_and_junk_entries():
    assert [b[4] for b in _boxes(_py(PAYLOADS["aliases"]))] == ["Q?", "L1", "T1"]
    assert [b[4] for b in _boxes(_py(PAYLOADS["junk_children"]))] == ["x", "y", "z"]


def test_the_limits_are_exactly_31_nodes_and_6_levels_and_32_characters():
    assert len(_boxes(_py(PAYLOADS["thirty_one"]))) == 31 and "<details" not in _py(PAYLOADS["thirty_one"])
    assert len(_boxes(_py(PAYLOADS["six_levels"]))) == 10
    assert _boxes(_py(_tree([T("Q", T("x" * 32))])))[1][4] == "x" * 32


@pytest.mark.parametrize("name,why", [("too_many_nodes", "31 nodes"), ("too_deep", "6 levels"), ("long_label", "32 characters"), ("graph_form", "nested")])
def test_beyond_the_limits_the_outline_is_shown_with_a_note(name, why, core_js):
    b = PAYLOADS[name]
    plain = {k: v for k, v in b.items() if k != "layout"}
    gas_plain = _gas_batch(core_js, [plain])[0]
    for out, base in ((_py(b), _py(plain)), (_gas_batch(core_js, [b])[0], gas_plain)):
        assert ("<details" in out or name == "graph_form") and "position:absolute;left:" not in out
        assert why in out and "shown as the outline" in out
        assert out.startswith(base) and out[len(base):].startswith('<div style="font-size:0.75rem;color:var(--muted,#475569);margin-top:4px;">')   # the outline itself is untouched; the note follows
    assert _py(b)[len(_py(plain)):] == _gas_batch(core_js, [b])[0][len(gas_plain):]                                                                 # and the note is the same in both twins


def test_no_nodes_at_all_keeps_the_outline():
    for b in ({"type": "decision_tree", "layout": "tree", "nodes": []}, {"type": "decision_tree", "layout": "tree"}):
        plain = {k: v for k, v in b.items() if k != "layout"}
        assert _pyx(b) == _pyx(plain)


def test_version_note():
    assert "Written for decision_tree version 2; drawn as version 1." in _py(PAYLOADS["version2"])
    assert "Written for decision_tree version 3; drawn as version 1." in _py({**NESTED, "version": 3})
    assert "Written for" not in _py({**PAYLOADS["ship"], "version": 1})


def test_schema_declares_layout_and_version():
    import yaml
    s = yaml.safe_load((ROOT / "atoms/schema.yaml").read_text())
    a = next(x for x in s["blocks"] if x.get("type") == "decision_tree")
    assert "layout" in a["fields"] and "tree" in a["fields"]["layout"] and "version" in a["fields"]
