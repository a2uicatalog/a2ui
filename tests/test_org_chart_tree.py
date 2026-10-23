"""org_chart layout: Python and GAS ports against REAL d3-hierarchy 3.1.2 tree() (Reingold-Tilford, Buchheim et al.).

GOLDEN holds what d3 produced (generated outside the repo by a node script running
`tree().nodeSize([1, 1]).separation((a, b) => (w[a] + w[b]) / 2 + (siblings ? 8 : 16))`, so x is the box centre in px;
the widths come from the label by the documented rule: ceil(chars * 8.4) + 22, or chars * 9.6 for the bold root row,
as _width_rule below: the one-line width, at most 112 px unless the longest word needs more (up to 140)). kids[i] lists the child indices of node i (node 0 is the root); labels, w (box widths), x and depth follow d3.
A tree whose top-down width (wid_td) exceeds 640 px also carries the left-to-right layout (ltr_x): the same d3 call with the separation taken from box
heights (hs). The layout functions must match to 1e-9; the rendered boxes (percentages, 3 decimals) must follow the layout, and every node must be
fully visible in a static render.
"""
from __future__ import annotations

import json
import re

import pytest

from test_motion_atoms import _gas_batch, _node, _py, core_js  # noqa: F401  (core_js is a fixture)
from test_motion_atoms import wa  # noqa: E402

GOLDEN = {
    'single': {"kids": [[]], "labels": ["L0xxxxxxxxxxxxx"], "w": [140], "nh": 46, "x": [0], "depth": [0], "wid_td": 140},
    'chain3': {"kids": [[1], [2], []], "labels": ["L0xxxxxx", "L1xxx lead of yyyyyyyy", "L2xxxx"], "w": [99, 112, 73], "nh": 60, "x": [0, 0, 0], "depth": [0, 1, 2], "wid_td": 112},
    'full_cap_10': {"kids": [[1, 2, 3, 4], [5, 6], [], [7, 8, 9], [], [], [], [], [], []], "labels": ["L0xxxxxxxxxxxxx", "L1x lead of yyyyyyyy", "L2xxxx", "L3xxxxxxxxxxxxxxxx", "L4xxxx", "L5xx lead of yyyyyyy", "L6xxx", "L7xxx", "L8x", "L9xxxx lead of yyyyyyy"], "w": [140, 112, 73, 140, 73, 112, 64, 64, 64, 112], "nh": 60, "x": [0, -164.75, -64.25, 50.25, 164.75, -212.75, -116.75, -33.75, 38.25, 134.25], "depth": [0, 1, 1, 1, 1, 2, 2, 2, 2, 2], "wid_td": 470},
    'unbalanced': {"kids": [[1, 2], [3], [4, 5, 6], [7], [], [], [], []], "labels": ["L0xxxxxxxxxxxxxxxxx", "L1xxxxx lead of y", "L2xx", "L3xxxxxxxxxxxxxx", "L4xx", "L5x lead of yyy", "L6xxxxxxxxxxxxxxxxxx", "L7xxxxx"], "w": [140, 112, 64, 140, 64, 112, 140, 81], "nh": 46, "x": [0, -116.5, 116.5, -116.5, 1.5, 97.5, 231.5, -116.5], "depth": [0, 1, 1, 2, 2, 2, 2, 3], "wid_td": 488},
    'four_children': {"kids": [[1, 2, 3, 4], [], [], [], []], "labels": ["L0xxxxxxxx", "L1xx lead of yyyyyyy", "L2x", "L3xxx", "L4x"], "w": [118, 112, 64, 64, 64], "nh": 60, "x": [0, -120, -24, 48, 120], "depth": [0, 1, 1, 1, 1], "wid_td": 328},
    'six_children': {"kids": [[1, 2, 3, 4, 5, 6], [], [], [], [], [], []], "labels": ["L0xxxxxxx", "L1xxx lead of yyyyyyyy", "L2xx", "L3xxxxxxxxxxxxxxx", "L4x", "L5xx lead of yyyyyyy", "L6xxxxxxxxxxxxxxxx"], "w": [109, 112, 64, 140, 64, 112, 140], "nh": 60, "x": [0, -273, -177, -67, 43, 139, 273], "depth": [0, 1, 1, 1, 1, 1, 1], "wid_td": 672, "hs": [60, 60, 60, 60, 60, 60, 60], "ltr_x": [0, -170, -102, -34, 34, 102, 170]},
    'interleave': {"kids": [[1, 2], [3, 4, 5], [6], [7], [], [], [8, 9], [], [], []], "labels": ["L0xxxxxx", "L1xxx lead of yyyyyyy", "L2xxxx", "L3xx", "L4xxx", "L5 lead of yyyyyy", "L6xxxxxxx", "L7xxxx", "L8x", "L9xxxxxxx lead of yyyy"], "w": [99, 112, 73, 64, 64, 112, 98, 73, 64, 112], "nh": 60, "x": [0, -102.5, 102.5, -186.5, -114.5, -18.5, 102.5, -186.5, 54.5, 150.5], "depth": [0, 1, 1, 2, 2, 2, 2, 3, 3, 3], "wid_td": 429.5},
    'four_tiers': {"kids": [[1, 2], [3], [], [4], []], "labels": ["L0xxxxxxxx", "L1xxxxx lead of yyyy", "L2", "L3xxxxx", "L4"], "w": [118, 112, 64, 81, 64], "nh": 60, "x": [0, -48, 48, -48, -48], "depth": [0, 1, 1, 2, 3], "wid_td": 184},
    'forest_virtual_root': {"kids": [[1, 2, 3], [4, 5], [6], [7], [], [], [], []], "labels": ["L0xxxxxxxxxxxxx", "L1 lead of yyy", "L2x", "L3xxxxxxxx", "L4x", "L5xxxx lead of yyyy", "L6xxxxxxxxxx", "L7xxxxx"], "w": [0, 112, 64, 118, 64, 112, 123, 81], "nh": 46, "x": [0, -149.75, 31.75, 149.75, -197.75, -101.75, 31.75, 149.75], "depth": [0, 1, 1, 1, 2, 2, 2, 2], "wid_td": 438.5},
    'tree20': {"kids": [[1, 2, 3, 4, 5, 6], [7, 8, 9], [10, 11, 12, 13], [14, 15], [], [16, 17, 18], [], [19], [], [], [], [], [], [], [], [], [], [], [], []], "labels": ["L0xxxxxxxxxxxx", "L1xxxx lead of y", "L2xxx", "L3xxxxxxxx", "L4xxx", "L5xxx lead of yyy", "L6xxxxxxxxx", "L7xxxxx", "L8x", "L9xxxxxxxxxx lead of yyyyyyyy", "L10xxx", "L11", "L12xxxxxxxxxxxx", "L13xxx lead of yyyy", "L14xxxx", "L15xxxxxxxxxxxxx", "L16x", "L17xxxx lead of yyyyyyyy", "L18xxxxxxxxx", "L19x"], "w": [140, 112, 64, 106, 64, 112, 115, 81, 64, 123, 73, 64, 140, 112, 81, 140, 64, 112, 123, 64], "nh": 60, "x": [0, -553.375, -188.125, 143.875, 286.375, 431.875, 553.375, -644.375, -563.875, -462.375, -348.375, -271.875, -161.875, -27.875, 84.625, 203.125, 321.125, 417.125, 542.625, -644.375], "depth": [0, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3], "wid_td": 1295.75, "hs": [60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60], "ltr_x": [0, -352, -106, 106, 195, 284, 352, -420, -352, -284, -208, -140, -72, -4, 72, 140, 216, 284, 352, -420]},
    'tree30_max': {"kids": [[1, 2, 3, 4, 5, 6], [7, 8, 9, 10, 11, 12], [13, 14, 15, 16], [17, 18, 19], [20, 21], [], [22, 23, 24], [25, 26, 27], [28, 29], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []], "labels": ["L0xxxxxxxxxxx", "L1xxxx lead of yyyyyyy", "L2xxx", "L3xxxxxxxxxxxxx", "L4", "L5xxxxx lead of y", "L6xxxx", "L7xx", "L8xxxx", "L9xxxxxx lead of yyyyyyy", "L10x", "L11xxxx", "L12xxxxxxxx", "L13xx lead of y", "L14x", "L15xxxxxxxxxxxxxx", "L16xxxx", "L17xxxx lead of yyyyyyyy", "L18xxxxxxxxxxx", "L19xxxxx", "L20x", "L21 lead of yyy", "L22xxx", "L23xxx", "L24xxxxxxxxxxxxx", "L25xxxx lead of yyyy", "L26xxx", "L27xxxxxxxxxxxxxxxxxx", "L28xxxx", "L29 lead of yyyyy"], "w": [140, 112, 64, 140, 64, 112, 73, 64, 73, 112, 64, 81, 115, 112, 64, 140, 81, 112, 140, 90, 64, 112, 73, 73, 140, 112, 73, 140, 81, 112], "nh": 60, "x": [0, -776.6875, -150.3125, 252.9375, 522.4375, 647.3125, 776.6875, -1111.3125, -825.0625, -724.5625, -628.5625, -548.0625, -442.0625, -312.5625, -216.5625, -106.5625, 11.9375, 124.4375, 258.4375, 381.4375, 474.4375, 570.4375, 678.9375, 759.9375, 874.4375, -1218.8125, -1118.3125, -1003.8125, -877.3125, -772.8125], "depth": [0, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3], "wid_td": 2219.25, "hs": [60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60], "ltr_x": [0, -502.5, -99.5, 146.5, 324.5, 413.5, 502.5, -727.5, -549.5, -481.5, -413.5, -345.5, -277.5, -201.5, -133.5, -65.5, 2.5, 78.5, 146.5, 214.5, 290.5, 358.5, 434.5, 502.5, 570.5, -795.5, -727.5, -659.5, -583.5, -515.5]},
}
# This case is rendered as three separate top-level roots (no node 0): the renderer adds an undrawn virtual root.
FOREST = "forest_virtual_root"

TOL = 1e-9
BOX = re.compile(r'<div (?:data-cb="node" )?style="position:absolute;left:([\d.]+)%;top:([\d.]+)%;width:([\d.]+)%;height:(\d+)px;')
KEY = re.compile(r'var\(--p,1\)\*(\d+)\s*-\s*(\d+)\)')
LABEL = re.compile(r'>(L\d+x*[^<]*)</div>')


def _payload(g, forest):
    kids = g["kids"]
    parent = {c: i for i, ks in enumerate(kids) for c in ks}
    nodes = []
    for i in range(0 if not forest else 1, len(kids)):
        p = parent.get(i)
        nodes.append({"id": "n%d" % i, "label": g["labels"][i], "parent_id": "" if (p is None or (forest and p == 0)) else "n%d" % p})
    return {"type": "org_chart", "title": "T", "nodes": nodes}


@pytest.mark.parametrize("name", list(GOLDEN))
def test_python_layout_matches_d3(name):
    g = GOLDEN[name]
    x, depth = wa._oc_layout(g["kids"], 0, g["w"])
    assert len(x) == len(g["x"])
    for a, b in zip(x, g["x"]):
        assert abs(a - b) <= TOL, (x, g["x"])
    assert list(depth) == g["depth"]
    if "ltr_x" in g:
        y, _ = wa._oc_layout(g["kids"], 0, g["hs"])
        for a, b in zip(y, g["ltr_x"]):
            assert abs(a - b) <= TOL, (y, g["ltr_x"])


def test_gas_layout_matches_d3(core_js):
    names = list(GOLDEN)
    calls = []
    for n in names:
        g = GOLDEN[n]
        calls.append([g["kids"], g["w"]])
        calls.append([g["kids"], g.get("hs", g["w"])])
    res = _node(core_js, "var G = " + json.dumps(calls) + "; console.log(JSON.stringify(G.map(function(k){ return _ocLayout(k[0], 0, k[1]); })));")
    for j, n in enumerate(names):
        g = GOLDEN[n]
        x, depth = res[2 * j]
        assert len(x) == len(g["x"])
        for a, b in zip(x, g["x"]):
            assert abs(a - b) <= TOL, (n, x, g["x"])
        assert depth == g["depth"], n
        if "ltr_x" in g:
            for a, b in zip(res[2 * j + 1][0], g["ltr_x"]):
                assert abs(a - b) <= TOL, (n, "ltr")


def _width_rule(t, bold):
    import math
    c = 9.6 if bold else 8.4
    full = math.ceil(len(t) * c) + 22
    word = math.ceil(max(len(x) for x in t.split(" ")) * c) + 22
    return max(64, min(full, max(112, min(140, word))))


def test_box_width_rule_is_the_same_in_both_twins(core_js):
    for t, bold in (("", False), ("a", False), ("Head of design", False), ("CEO", True), ("x" * 28, False), ("x" * 28, True), ("Infrastructure team", False), ("a b c d e f g h i j k l m", False), ("Workstream A", False)):
        exp = _width_rule(t, bold)
        assert wa._oc_width(t, bold) == exp, (t, bold)
        assert _node(core_js, "console.log(JSON.stringify(_ocWidth(%s, %s)));" % (json.dumps(t), "true" if bold else "false")) == exp, (t, bold)


def _expected(name):
    """Expected (left %, top %, width %, depth-less) per shown node for the top-down layout and, for a wide tree, the left-to-right one."""
    g = GOLDEN[name]
    forest = name == FOREST
    first = 1 if forest else 0
    idx = list(range(first, len(g["x"])))
    sh = 1 if forest else 0
    n = len(g["x"])
    nh = g["nh"]
    lo = min(g["x"][i] - g["w"][i] / 2 for i in idx)
    hi = max(g["x"][i] + g["w"][i] / 2 for i in idx)
    tiers = max(g["depth"][i] - sh for i in idx) + 1
    row = nh + 28
    ht = tiers * row - 28
    td = [((g["x"][i] - g["w"][i] / 2 - lo) / (hi - lo) * 100, (g["depth"][i] - sh) * row / ht * 100, g["w"][i] / (hi - lo) * 100) for i in idx]
    ltr = None
    if "ltr_x" in g:
        y = g["ltr_x"]
        top0 = min(y[i] - nh / 2 for i in idx)
        lht = max(y[i] + nh / 2 for i in idx) - top0
        colw = [0] * tiers
        for i in idx:
            colw[g["depth"][i] - sh] = max(colw[g["depth"][i] - sh], g["w"][i])
        gap = 28 if tiers < 2 else min(28, max(12, (640 - sum(colw)) // (tiers - 1)))
        col = [0]
        for t in range(1, tiers):
            col.append(col[-1] + colw[t - 1] + gap)
        lw = sum(colw) + gap * (tiers - 1)
        ltr = [(col[g["depth"][i] - sh] / lw * 100, (y[i] - nh / 2 - top0) / lht * 100, g["w"][i] / lw * 100) for i in idx]
    return idx, td, ltr, (hi - lo) > 640


@pytest.mark.parametrize("name", list(GOLDEN))
def test_rendered_nodes_follow_the_d3_layout_and_are_all_visible_in_both_renderers(name, core_js):
    g = GOLDEN[name]
    block = _payload(g, name == FOREST)
    idx, td, ltr, wide = _expected(name)
    for html in (_py(block), _gas_batch(core_js, [block])[0]):
        boxes = BOX.findall(html)
        assert len(boxes) == len(idx) * (2 if wide else 1), (len(boxes), len(idx))
        assert ('data-oc="both"' in html) == wide and ('data-oc="td"' in html) == (not wide)
        labels = LABEL.findall(html)
        assert int(boxes[0][3]) == g["nh"]
        for part, exp in ((0, td), (1, ltr)):
            if exp is None:
                continue
            sl = slice(part * len(idx), (part + 1) * len(idx))
            by_idx = {int(re.match(r"L(\d+)", l).group(1)): b for l, b in zip(labels[sl], boxes[sl])}
            for i, (left, top, width) in zip(idx, exp):
                l, t, w, _ = by_idx[i]
                assert abs(float(l) - left) <= 2e-3, (name, part, i, l, left)
                assert abs(float(t) - top) <= 2e-3, (name, part, i, t, top)
                assert abs(float(w) - width) <= 2e-3, (name, part, i, w, width)
        # every node reaches --k = 1 when --p is 1 (a static render, PDF): steps = n + 1 must exceed the index
        ks = KEY.findall(html)
        assert len(ks) >= len(idx)
        assert all(int(m) - int(i) >= 1 for m, i in ks), ks
        assert "<script" not in html and "<li" in html and "<ul" in html


def test_python_and_gas_emit_identical_html_for_every_golden_tree(core_js):
    names = list(GOLDEN)
    blocks = [_payload(GOLDEN[n], n == FOREST) for n in names]
    gas = _gas_batch(core_js, blocks)
    for n, b, gh in zip(names, blocks, gas):
        assert re.sub(r"\s+", " ", _py(b)) == re.sub(r"\s+", " ", gh), n


def test_wide_trees_carry_both_layouts_and_css_picks_one():
    html = _py(_payload(GOLDEN["tree20"], False))
    w = str(int(-(-GOLDEN["tree20"]["wid_td"] // 1)))
    assert "@container (min-width:%spx)" % w in html and "@media print" in html and "container-type:inline-size" in html
    assert ".oc-w%s .oct{display:none}" % w in html and ".oc-w%s .ocl{display:none}" % w in html
    narrow = _py(_payload(GOLDEN["full_cap_10"], False))
    assert "@container" not in narrow and "<style" not in narrow.replace(wa._CB_RULES, "") and 'class="ocl"' not in narrow


def test_nesting_is_still_a_real_list_in_document_order():
    html = _py(_payload(GOLDEN["full_cap_10"], False))
    assert html.count("<ul") == html.count("</ul>") and html.count("<li ") == html.count("</li>") == 10
    assert [int(re.match(r"L(\d+)", l).group(1)) for l in LABEL.findall(html)] == [0, 1, 5, 6, 2, 3, 7, 8, 9, 4]


def test_caps_are_thirty_nodes_four_tiers_six_children(core_js):
    nodes = [{"id": "r", "label": "R", "parent_id": ""}]
    nodes += [{"id": "c%d" % i, "label": "C%d" % i, "parent_id": "r"} for i in range(8)]      # eight children: only six shown
    nodes += [{"id": "g1", "label": "G1", "parent_id": "c0"}, {"id": "g2", "label": "G2", "parent_id": "g1"}, {"id": "g3", "label": "G3", "parent_id": "g2"}, {"id": "g4", "label": "G4", "parent_id": "g3"}]  # the fifth tier (G3, G4) is dropped
    nodes += [{"id": "x%d" % i, "label": "X%d" % i, "parent_id": "c1"} for i in range(30)]     # past thirty: cut
    block = {"type": "org_chart", "nodes": nodes}
    for html in (_py(block), _gas_batch(core_js, [block])[0]):
        m = 2 if 'data-oc="both"' in html else 1          # a wide tree carries both layouts
        got = re.findall(r'>([A-Z]\d*)</div>', html)
        assert m == 1 or got[:len(got) // 2] == got[len(got) // 2:]
        got = got[:len(got) // m]
        assert "C5" in got and "C6" not in got and "C7" not in got
        assert "G2" in got and "G3" not in got
        assert len(got) <= 30 and len(BOX.findall(html)) == len(got) * m


def test_thirty_nodes_all_reach_full_opacity_in_a_static_render(core_js):
    block = _payload(GOLDEN["tree30_max"], False)
    for html in (_py(block), _gas_batch(core_js, [block])[0]):
        assert 'data-oc="both"' in html and len(BOX.findall(html)) == 60          # both layouts, 30 boxes each
        ks = KEY.findall(html)
        assert len(ks) == 2 * (30 + 29) and all(int(m) - int(i) >= 1 for m, i in ks)


def test_duplicate_ids_cannot_push_a_node_past_the_motion_steps(core_js):
    # a duplicated id renders its subtree under both; the motion step count must cover everything rendered
    nodes = [{"id": "a", "label": "A", "parent_id": ""}, {"id": "b", "label": "B1", "parent_id": "a"}, {"id": "b", "label": "B2", "parent_id": "a"},
             {"id": "c", "label": "C", "parent_id": "b"}]
    block = {"type": "org_chart", "nodes": nodes}
    for html in (_py(block), _gas_batch(core_js, [block])[0]):
        ks = KEY.findall(html)
        assert ks and all(int(m) - int(i) >= 1 for m, i in ks), ks
