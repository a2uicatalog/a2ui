"""sunburst (I40) with the optional `layout` icicle (I54): d3-hierarchy partition() and d3-shape arc(), ported by hand into BOTH renderers.

GOLDEN (tests/fixtures/sunburst_d3_golden.json, from sunburst_d3_golden_gen.mjs) holds what the REAL d3-hierarchy 3.1.2
(hierarchy().sum().sort(by value descending), partition().size(...)) and the REAL d3-shape 3.2.0 arc() (with padAngle and padRadius,
as in d3's "sunburst" example) give.
 * The partition rectangles are compared with ==: both twins run d3's float operations in d3's order.
 * The arc strings printed with arc()'s default 3 digits are compared with == as text; the full-precision numbers (digits(null)) to 1e-9.
   Python's libm and V8 can differ by an ulp in sin / cos / asin, which only matters at a rounding edge of the 3-digit text or for the
   1e-9 numbers; neither shows up in this set. The GAS twin runs in V8 itself.
Also held here: Python/GAS HTML parity, the hidden table, the aria label, the motion index, malformed input, caps with notes, the `version`
field, escaping, the label rule and registration.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

import pytest
import yaml

from test_histogram import ATTACK, _table
from test_motion_atoms import _gas_batch, _node, _py, core_js  # noqa: F401  (core_js is a fixture)
from test_motion_atoms import wa  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
D = json.loads((ROOT / "tests/fixtures/sunburst_d3_golden.json").read_text())
CASES = D["cases"]
NUM = r"-?\d+(?:\.\d+)?(?:e[-+]?\d+)?"


# ─── the partition and the arcs against real d3 ───────────────────────────────────────────────────────────────
@pytest.mark.parametrize("name", list(CASES))
def test_python_partition_matches_d3_exactly(name):
    c = CASES[name]
    assert [list(r) for r in wa._sb_rows(c["spec"], *D["radial_size"])] == c["radial"]
    assert [list(r) for r in wa._sb_rows(c["spec"], *D["icicle_size"])] == c["icicle"]


def test_gas_partition_matches_d3_exactly(core_js):
    names = list(CASES)
    res = _node(core_js, "var G = " + json.dumps([CASES[n]["spec"] for n in names]) + ", RS = " + json.dumps(D["radial_size"]) + ", IS = " + json.dumps(D["icicle_size"])
                + "; console.log(JSON.stringify(G.map(function(s){ return [_sbRows(s, RS[0], RS[1]), _sbRows(s, IS[0], IS[1])]; })));")
    for n, (rad, ici) in zip(names, res):
        assert rad == CASES[n]["radial"] and ici == CASES[n]["icicle"], n


def _params(rows):
    """The arc() arguments of every node below the root, as the renderer builds them (d3's sunburst example)."""
    return [(r[1], r[3], r[2], max(r[2], r[4] - 1), min((r[3] - r[1]) / 2, D["pad_angle"]), D["pad_radius"]) for r in rows if r[0]]


def _same_numbers(got, want):
    assert re.sub(NUM, "#", got) == re.sub(NUM, "#", want)
    a, b = [float(x) for x in re.findall(NUM, got)], [float(x) for x in re.findall(NUM, want)]
    assert len(a) == len(b) and all(abs(x - y) <= 1e-9 for x, y in zip(a, b)), (got, want)


@pytest.mark.parametrize("name", list(CASES))
def test_python_arcs_match_d3(name):
    c = CASES[name]
    for p, (text, full) in zip(_params(c["radial"]), c["arcs"]):
        assert wa._sb_arc(*p) == text
        _same_numbers(wa._sb_arc(*p, None), full)


@pytest.mark.parametrize("k", range(len(D["arcs"]["own"])))
def test_python_arc_edge_cases_match_d3(k):
    c = D["arcs"]["own"][k]
    a0, a1, r0, r1, pa, pr = c["p"]
    assert wa._sb_arc(a0, a1, r0, r1, pa, pr) == c["d"]
    _same_numbers(wa._sb_arc(a0, a1, r0, r1, pa, pr, None), c["full"])


def test_gas_arcs_match_d3(core_js):
    own = [c["p"] for c in D["arcs"]["own"]]
    names = list(CASES)
    params = [_params(CASES[n]["radial"]) for n in names]
    res = _node(core_js, "var O = " + json.dumps(own) + ", P = " + json.dumps(params) + "; console.log(JSON.stringify({"
                "own: O.map(function(p){ return [_sbArc(p[0],p[1],p[2],p[3],p[4],p[5],3), _sbArc(p[0],p[1],p[2],p[3],p[4],p[5],null)]; }),"
                "nodes: P.map(function(ps){ return ps.map(function(p){ return [_sbArc(p[0],p[1],p[2],p[3],p[4],p[5],3), _sbArc(p[0],p[1],p[2],p[3],p[4],p[5],null)]; }); })}));")
    for c, (text, full) in zip(D["arcs"]["own"], res["own"]):
        assert text == c["d"]
        _same_numbers(full, c["full"])
    for n, got in zip(names, res["nodes"]):
        for (text, full), (wt, wf) in zip(got, CASES[n]["arcs"]):
            assert text == wt
            _same_numbers(full, wf)


def test_the_golden_set_covers_the_hard_cases():
    own = D["arcs"]["own"]
    assert any(c["d"].count("A") == 4 for c in own)                       # a full ring (annulus)
    assert any(c["d"].startswith("M0,0") for c in own)                    # a point
    assert any("L" in c["d"] and c["p"][2] == 0 for c in own)             # a circular sector with no inner ring
    assert len(D["cases"]) == 40 and CASES["forty"]["radial"][0][5] > 0 and len(CASES["forty"]["radial"]) == 49
    assert [r[0] for r in CASES["depth4"]["radial"]][:3] == [0, 1, 2]


def test_icicle_partition_uses_the_whole_height_for_the_roots_children():
    for c in CASES.values():
        kids = [r for r in c["icicle"] if r[0] == 1]
        assert abs(sum(r[3] - r[1] for r in kids) - D["icicle_size"][0]) < 1e-9


# ─── rendering ─────────────────────────────────────────────────────────────────────────────────────────────────
def _it(path, name, value):
    return ({"path": path} if path else {}) | {"name": name, "value": value}


BUDGET = [
    _it(["Operations", "Cloud"], "Compute", 420), _it(["Operations", "Cloud"], "Storage", 180), _it(["Operations", "Cloud"], "Network", 95),
    _it(["Operations", "Offices"], "Rent", 300), _it(["Operations", "Offices"], "Utilities", 60), _it(["Operations"], "Insurance", 70),
    _it(["People", "Engineering"], "Salaries", 900), _it(["People", "Engineering"], "Training", 40), _it(["People", "Sales"], "Salaries", 520),
    _it(["People", "Sales"], "Commission", 130), _it(["People"], "Recruiting", 85),
    _it(["Marketing", "Paid"], "Search", 160), _it(["Marketing", "Paid"], "Social", 110), _it(["Marketing", "Events"], "Conference", 75), _it(["Marketing"], "Content", 55),
    _it([], "Legal", 90),
]
FLAT = [_it([], "Rent", 300), _it([], "Salaries", 900), _it([], "Tools", 80), _it([], "Travel", 40)]
PAYLOADS = {
    "budget": {"type": "sunburst", "title": "Where the money goes", "unit": "k EUR", "items": BUDGET},
    "budget_icicle": {"type": "sunburst", "title": "Where the money goes", "unit": "k EUR", "layout": "icicle", "items": BUDGET},
    "flat": {"type": "sunburst", "items": FLAT},
    "flat_icicle": {"type": "sunburst", "layout": "icicle", "items": FLAT},
    "two": {"type": "sunburst", "items": [_it(["A"], "x", 3), _it(["B"], "y", 1)]},
    "one_group": {"type": "sunburst", "items": [_it(["Only"], "a", 7), _it(["Only"], "b", 3)]},
    "one_group_icicle": {"type": "sunburst", "layout": "icicle", "items": [_it(["Only"], "a", 7), _it(["Only"], "b", 3)]},
    "deep": {"type": "sunburst", "items": [_it(["A", "B", "C"], "one", 50), _it(["A", "B", "C"], "two", 30), _it(["A", "B"], "three", 20), _it(["A"], "four", 10),
                                           _it(["D", "E", "F"], "five", 40), _it(["D", "E", "F"], "six", 25), _it(["D", "E", "F"], "seven", 5), _it(["D", "E"], "eight", 15), _it(["D"], "nine", 12), _it([], "ten", 8)]},
    "deep_icicle": {"type": "sunburst", "layout": "icicle", "items": [_it(["A", "B", "C"], "one", 50), _it(["A", "B", "C"], "two", 30), _it(["A", "B"], "three", 20), _it(["A"], "four", 10),
                                                                      _it(["D", "E", "F"], "five", 40), _it(["D", "E", "F"], "six", 25), _it(["D", "E", "F"], "seven", 5), _it(["D", "E"], "eight", 15), _it(["D"], "nine", 12), _it([], "ten", 8)]},
    "forty": {"type": "sunburst", "unit": "GB", "items": [_it(["Group %d" % (k % 10), "Sub %d" % (k % 3)] if k % 4 else ["Group %d" % (k % 10)], "Item %d" % k, 1 + (k * 7) % 13 + k / 8) for k in range(40)]},
    "forty_icicle": {"type": "sunburst", "layout": "icicle", "items": [_it(["Group %d" % (k % 10), "Sub %d" % (k % 3)] if k % 4 else ["Group %d" % (k % 10)], "Item %d" % k, 1 + (k * 7) % 13 + k / 8) for k in range(40)]},
    "forty_one": {"type": "sunburst", "items": [_it(["G%d" % (k % 5)], "Item %d" % k, k + 1) for k in range(41)]},
    "tiny_share": {"type": "sunburst", "items": [_it(["Big"], "huge", 1e9), _it(["Big"], "tiny", 1e-9), _it(["Small"], "ok", 5)]},
    "long_names": {"type": "sunburst", "items": [_it(["A very long group name!!"], "An item with a name of twenty-four chars", 40), _it(["A very long group name!!"], "Short", 5), _it(["Other"], "Another quite long item name", 30)]},
    "twelve_groups": {"type": "sunburst", "items": [_it(["G%d" % k], "item %d" % k, 12 - k) for k in range(12)]},
    "bad_values": {"type": "sunburst", "items": [_it(["A"], "zero", 0), _it(["A"], "neg", -3), _it(["A"], "str", "12"), _it(["A"], "junk", "x"), _it(["A"], "none", None), _it(["A"], "inf", float("inf")),
                                                  "text", None, 7, {"path": ["B"], "name": "good", "value": 5}, {"name": "ok", "value": 3.5}, {"name": 12, "value": 2}, {"path": ["B"], "value": 4}]},
    "path_junk": {"type": "sunburst", "items": [{"path": ["a", "", "  ", 5, None, "b", "c", "d", "e"], "name": "x", "value": 3}, {"path": "notalist", "name": "y", "value": 2}, {"path": [], "name": "z", "value": 1},
                                                 {"path": ["a" * 40], "name": "w", "value": 1}]},
    "too_few": {"type": "sunburst", "title": "T", "items": [_it(["A"], "only", 5)]},
    "no_items": {"type": "sunburst"},
    "items_not_list": {"type": "sunburst", "items": {"name": "x", "value": 3}},
    "all_bad": {"type": "sunburst", "items": [_it([], "a", 0), _it([], "b", -1)]},
    "bad_layout": {"type": "sunburst", "layout": "spiral", "items": BUDGET},
    "layout_junk": {"type": "sunburst", "layout": ["icicle"], "items": FLAT},
    "version_2": {"type": "sunburst", "version": 2, "items": FLAT},
    "version_junk": {"type": "sunburst", "version": True, "items": FLAT},
}


@pytest.mark.parametrize("name", list(PAYLOADS))
def test_python_and_gas_emit_identical_html(name, core_js):
    assert _py(PAYLOADS[name]) == _gas_batch(core_js, [PAYLOADS[name]])[0]


def test_hostile_text_python_and_gas_agree_and_are_escaped(core_js):
    b = {"type": "sunburst", "title": ATTACK, "unit": ATTACK, "items": [_it([ATTACK], ATTACK, 5), _it([ATTACK, "x"], ATTACK, 3), _it([], ATTACK, 2)]}
    outs = [_py(b), _gas_batch(core_js, [b])[0], _py(dict(b, layout="icicle")), _gas_batch(core_js, [dict(b, layout="icicle")])[0]]
    assert outs[0] == outs[1] and outs[2] == outs[3]
    for h in outs:
        assert "<img" not in h and "<svg onload" not in h and "<script" not in h.replace("<style", "") and 'onerror=alert(1)>' not in h.replace("&gt;", "")
        assert "&lt;img" in h


def _arcs(html):
    return re.findall(r'<path d="([^"]*)" fill="(#[0-9A-F]{6})"><title>(.*?)</title></path>', html)


def test_radial_draws_one_arc_per_node_with_a_title_and_a_hidden_table(core_js):
    for html in (_py(PAYLOADS["budget"]), _gas_batch(core_js, [PAYLOADS["budget"]])[0]):
        assert "<script" not in html and "<svg " in html and "NaN" not in html and "undefined" not in html
        arcs = _arcs(html)
        assert len(arcs) == 16 + 9                                            # 16 items and 9 groups: Operations, Cloud, Offices, People, Engineering, Sales, Marketing, Paid, Events
        head, rows = _table(html)
        assert head == ["Item", "Path", "Value", "Share of total"] and len(rows) == 16
        t = html.index("<table")
        assert 'role="img"' in html[:t] and 'role="img"' not in html[t:]
        assert rows[0] == ["Compute", "Operations / Cloud", "420 k EUR", "%.1f%%" % (420 / 3290 * 100)]
        assert rows[-1][1] == "Top level"
        assert abs(sum(float(r[3][:-1]) for r in rows) - 100) < 1
        titles = [a[2] for a in arcs]
        assert "Operations / Cloud / Compute: 420 k EUR (12.8%)" in titles and "Operations: 1,125 k EUR (34.2%)" in titles
        assert "Legal: 90 k EUR (2.7%)" in titles


def test_icicle_draws_one_rectangle_per_node(core_js):
    for html in (_py(PAYLOADS["budget_icicle"]), _gas_batch(core_js, [PAYLOADS["budget_icicle"]])[0]):
        assert "<svg" not in html and "<script" not in html
        cells = re.findall(r'<div title="([^"]*)" style="position:absolute;left:([\d.]+)%;top:([\d.]+)%;width:([\d.]+)%;height:([\d.]+)%;', html)
        assert len(cells) == 25
        assert len(_table(html)[1]) == 16
        # the first column (the top-level groups) sits at the left edge, the deepest at the right
        assert min(float(c[1]) for c in cells) == 0
        assert max(float(c[1]) + float(c[3]) for c in cells) <= 100.001


def test_aria_label_gives_total_group_count_and_largest_group(core_js):
    for html in (_py(PAYLOADS["budget"]), _gas_batch(core_js, [PAYLOADS["budget"]])[0]):
        a = re.search(r'role="img" aria-label="([^"]*)"', html).group(1)
        assert a == "Sunburst of 16 items in 4 top-level groups, total 3,290 k EUR. Largest top-level group: People, 1,675 k EUR, 50.9% of the total."
    for html in (_py(PAYLOADS["budget_icicle"]), _gas_batch(core_js, [PAYLOADS["budget_icicle"]])[0]):
        assert re.search(r'role="img" aria-label="Icicle chart of 16 items in 4 top-level groups, total 3,290 k EUR\. Largest top-level group: People, ', html)
    a = re.search(r'aria-label="([^"]*)"', _py(PAYLOADS["one_group"])).group(1)
    assert a == "Sunburst of 2 items in 1 top-level group, total 10. Largest top-level group: Only, 10, 100.0% of the total."


def test_group_colour_follows_the_top_level_group_and_deeper_rings_are_lighter():
    arcs = _arcs(_py(PAYLOADS["budget"]))
    by = {t.split(":")[0]: c for _, c, t in arcs}
    lum = lambda c: sum(int(c[i:i + 2], 16) for i in (1, 3, 5))
    assert by["Operations / Cloud / Compute"] != by["People / Engineering / Salaries"]
    assert lum(by["Operations"]) < lum(by["Operations / Cloud"]) < lum(by["Operations / Cloud / Compute"])
    assert by["Operations / Offices"] == by["Operations / Cloud"] and by["People"] != by["Operations"]
    assert len({c for _, c, _ in arcs}) > 4


def test_every_palette_colour_and_shade_has_readable_label_text():
    def lin(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    L = lambda h: 0.2126 * lin(int(h[1:3], 16)) + 0.7152 * lin(int(h[3:5], 16)) + 0.0722 * lin(int(h[5:7], 16))
    for base in wa._SB_PALETTE:
        for depth in range(1, 5):
            fill = wa._sb_fill(base, depth)
            text = wa._sb_ink(fill)
            hi, lo = sorted((L(fill), L(text)), reverse=True)
            assert (hi + 0.05) / (lo + 0.05) >= 4.5, (base, depth, fill, text)


def test_label_ink_python_and_gas_agree_for_every_colour(core_js):
    fills = [wa._sb_fill(c, d) for c in wa._SB_PALETTE for d in range(0, 7)]
    got = _node(core_js, "var P = " + json.dumps(wa._SB_PALETTE) + "; var o = []; P.forEach(function(c){ for (var d = 0; d < 7; d++) { var f = _sbFill(c, d); o.push([f, _sbInk(f)]); } }); console.log(JSON.stringify(o));")
    assert got == [[f, wa._sb_ink(f)] for f in fills]


def test_text_is_never_below_12px_and_nothing_has_a_script():
    for n, b in PAYLOADS.items():
        h = _py(b)
        assert all(int(x) >= 12 for x in re.findall(r"font-size:(\d+)px", h)), n
        assert "<script" not in h and "NaN" not in h and "Infinity" not in h and "undefined" not in h and "[object Object]" not in h, n


def test_motion_index_per_ring_stays_inside_its_clamp(core_js):
    for name, rings in (("budget", 3), ("deep", 4), ("flat", 1)):
        for html in (_py(PAYLOADS[name]), _gas_batch(core_js, [PAYLOADS[name]])[0]):
            ks = re.findall(r'<g class="sbr" style="--k:clamp\(0,calc\(var\(--p,1\)\*(\d+) - (\d+)\),1\);', html)
            assert [int(i) for _, i in ks] == list(range(rings)) and all(int(n) == rings + 1 for n, _ in ks), name
    for html in (_py(PAYLOADS["budget_icicle"]), _gas_batch(core_js, [PAYLOADS["budget_icicle"]])[0]):
        idx = {int(i) for _, i in re.findall(r'--k:clamp\(0,calc\(var\(--p,1\)\*(\d+) - (\d+)\),1\);', html)}
        assert idx == {0, 1, 2}


def test_malformed_items_are_dropped_and_explained(core_js):
    for h in (_py(PAYLOADS["bad_values"]), _gas_batch(core_js, [PAYLOADS["bad_values"]])[0]):
        head, rows = _table(h)
        assert [r[0] for r in rows] == ["str", "good", "ok", "12", "Item 13"] and [r[1] for r in rows] == ["A", "B", "Top level", "Top level", "B"]
        assert "8 entries had no value above 0 or were not an item and were left out." in h
        assert "NaN" not in h and "undefined" not in h and "[object Object]" not in h


def test_path_keeps_three_usable_names_of_twenty_characters():
    _, rows = _table(_py(PAYLOADS["path_junk"]))
    assert rows[0][1] == "a / b / c" and rows[1][1] == "Top level" and rows[2][1] == "Top level" and rows[3][1] == "a" * 20


def test_too_few_or_no_items_gives_a_note_and_no_chart():
    for k in ("too_few", "no_items", "items_not_list", "all_bad"):
        h = _py(PAYLOADS[k])
        assert "A sunburst needs at least 2 items with a value above 0." in h
        assert 'role="img"' not in h and "<table" not in h and "NaN" not in h
    assert ">T</div>" in _py(PAYLOADS["too_few"])


def test_only_the_first_forty_items_are_read():
    h = _py(PAYLOADS["forty_one"])
    assert len(_table(h)[1]) == 40 and "1 item beyond the first 40 was not drawn." in h
    assert "Item 40" not in h


def test_the_largest_group_and_ring_order_follow_d3s_descending_sort():
    arcs = _arcs(_py(PAYLOADS["budget"]))
    firsts = [t.split(":")[0] for _, _, t in arcs if "/" not in t.split(":")[0]]
    assert firsts[:4] == ["People", "Operations", "Marketing", "Legal"]


def test_unknown_or_malformed_layout_is_radial_and_absent_is_radial(core_js):
    assert _py(PAYLOADS["bad_layout"]) == _py(dict(PAYLOADS["bad_layout"], layout="radial")) == _py({k: v for k, v in PAYLOADS["bad_layout"].items() if k != "layout"})
    assert _py(PAYLOADS["layout_junk"]) == _py(PAYLOADS["flat"])


def test_tiny_share_arc_has_no_label_and_no_nan():
    h = _py(PAYLOADS["tiny_share"])
    assert "NaN" not in h and "Infinity" not in h
    assert len(_arcs(h)) == 5


def test_version_above_one_is_noted_and_otherwise_silent(core_js):
    for h in (_py(PAYLOADS["version_2"]), _gas_batch(core_js, [PAYLOADS["version_2"]])[0]):
        assert "Written for sunburst version 2; drawn as version 1." in h
    assert "version" not in _py(PAYLOADS["version_junk"]).lower()
    assert _py(dict(PAYLOADS["flat"], version=1)) == _py(PAYLOADS["flat"])


# ─── the label rule ────────────────────────────────────────────────────────────────────────────────────────────
def _labels(html):
    return re.findall(r'<div class="sbl(?: tmw(\d+))?" style="position:absolute;left:([\d.]+)%;top:([\d.]+)%;transform:translate\(-50%,-50%\) rotate\((-?[\d.]+)deg\);', html)


def test_labels_are_rotated_to_read_outward_and_never_upside_down(core_js):
    for name in ("budget", "deep", "forty"):
        for html in (_py(PAYLOADS[name]), _gas_batch(core_js, [PAYLOADS[name]])[0]):
            ls = _labels(html)
            assert ls, name
            assert all(-90 <= float(deg) <= 90 for _, _, _, deg in ls)
            assert any(float(deg) > 0 for *_, deg in ls) and any(float(deg) < 0 for *_, deg in ls)


def test_a_label_is_drawn_only_where_it_fits_and_gated_by_container_width():
    h = _py(PAYLOADS["deep"])
    ws = sorted({int(w) for w, *_ in _labels(h) if w})
    assert ws and all(w % 10 == 0 and w <= 640 for w in ws)
    css = re.search(r"<style>(.*?)</style>", h).group(1)
    assert all("@container (width<%dpx){.tmw%d{display:none}}" % (w, w) in css for w in ws)
    assert h.count('class="sbl') < len(_arcs(h)) + 1                         # the tiny arcs have none


def test_registered_as_a_preview_charts_atom_with_an_example_and_every_field_documented():
    blocks = {a["type"]: a for a in yaml.safe_load((ROOT / "atoms/schema.yaml").read_text())["blocks"]}
    a = blocks["sunburst"]
    assert a["stage"] == "preview" and set(a["fields"]) == {"title", "items", "layout", "unit", "version"}
    assert a["surfaces"] == blocks["treemap"]["surfaces"] and a["source"] == blocks["treemap"]["source"]
    assert "treemap" in a["routing_text"] and "bar chart" in a["routing_text"] and len(a["intent_phrases"]) == 3
    assert re.search(r"^a2ui-charts-v1:\n(?:- .*\n)*- sunburst$", (ROOT / "atoms/atom-packs.yaml").read_text(), re.M)
    assert '"sunburst":"a2ui-charts-v1"' in (ROOT / "apps-script-surface/gas-wired-renderer/PackMap.gs").read_text()
    import generate_atom_pages as g
    ex = g._EXAMPLE_BLOCKS["sunburst"]
    assert ex["type"] == "sunburst" and "<table" in _py(ex) and "<path" in _py(ex)
    txt = (ROOT / "atoms/schema.yaml").read_text()
    assert txt.index("- type: sunburst") < txt.index("# ── Motion candidates (2026-10-10, preview) ──")


def test_d3_credit_names_partition_and_arc():
    t = (ROOT / "THIRD-PARTY-NOTICES.md").read_text()
    assert "partition" in t and "tests/test_sunburst.py" in t and "d3-shape" in t and "`arc`" in t
