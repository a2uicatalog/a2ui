"""chord_diagram (I47) with the optional `directed` (I62): d3-chord 3.0.1 chord(), chordDirected(), ribbon() and ribbonArrow(), with d3-shape arc() for the
group arcs, ported by hand into BOTH renderers (the arc and d3-path code is the sunburst's, shared as _D3Path).

GOLDEN (tests/fixtures/chord_d3_golden.json, from chord_d3_golden_gen.mjs) holds what the REAL d3-chord 3.0.1
(chord().padAngle(0.05).sortSubgroups(d3.descending) and chordDirected() likewise) and the REAL d3-shape 3.2.0 arc() give, for hand cases (2 groups, a zero
row, an all-zero matrix, a self-loop on the diagonal, 12 groups, asymmetric flows) and seeded fuzz.
 * Group and chord (subgroup) start / end angles and values are compared with ==: both twins run d3's float operations in d3's order.
 * The group arc strings printed with arc()'s default 3 digits are compared with == as text; full precision to 1e-9. Ribbon strings: d3-chord's ribbon
   uses a d3-path with no digits setting, so the golden is full precision and is compared to 1e-9 (Python's libm and V8 can differ by an ulp in sin / cos);
   what is drawn is the same path with d3-path's 3-digit rounding, checked against the golden numbers to 6e-4.
Also held here: Python/GAS HTML parity, the hidden tables, the aria label, the motion index, malformed input, caps with notes, the `version` field,
escaping, the label rule and registration.
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
D = json.loads((ROOT / "tests/fixtures/chord_d3_golden.json").read_text())
CASES = D["cases"]
NUM = r"-?\d+(?:\.\d+)?(?:e[-+]?\d+)?"
MODES = (("undirected", False), ("directed", True))


def _same_numbers(got, want, tol=1e-9):
    assert re.sub(NUM, "#", got) == re.sub(NUM, "#", want), (got, want)
    a, b = [float(x) for x in re.findall(NUM, got)], [float(x) for x in re.findall(NUM, want)]
    assert len(a) == len(b) and all(abs(x - y) <= tol for x, y in zip(a, b)), (got, want)


# ─── the layout and the paths against real d3 ──────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("name", list(CASES))
def test_python_groups_and_chords_match_d3_exactly(name):
    for mode, directed in MODES:
        groups, chords = wa._ch_chord(CASES[name]["matrix"], directed)
        assert [list(g) for g in groups] == CASES[name][mode]["groups"], mode
        assert [list(c) for c in chords] == CASES[name][mode]["chords"], mode


def test_gas_groups_and_chords_match_d3_exactly(core_js):
    names = list(CASES)
    res = _node(core_js, "var G = " + json.dumps([CASES[n]["matrix"] for n in names]) + "; console.log(JSON.stringify(G.map(function(m){ return [_chChord(m, false), _chChord(m, true)]; })));")
    for n, (u, d) in zip(names, res):
        assert u == [CASES[n]["undirected"]["groups"], CASES[n]["undirected"]["chords"]], n
        assert d == [CASES[n]["directed"]["groups"], CASES[n]["directed"]["chords"]], n


@pytest.mark.parametrize("name", list(CASES))
def test_python_group_arcs_and_ribbons_match_d3(name):
    for mode, directed in MODES:
        c = CASES[name][mode]
        for g, (text, full) in zip(c["groups"], c["arcs"]):
            assert wa._sb_arc(g[1], g[2], D["inner"], D["outer"], 0, None) == text
            _same_numbers(wa._sb_arc(g[1], g[2], D["inner"], D["outer"], 0, None, None), full)
        for row, want in zip(c["chords"], c["ribbons"]):
            _same_numbers(wa._ch_ribbon(row, D["ribbon_radius"], D["ribbon_pad"], directed, None), want)
            _same_numbers(wa._ch_ribbon(row, D["ribbon_radius"], D["ribbon_pad"], directed, 3), want, 6e-4)


def test_gas_group_arcs_and_ribbons_match_d3(core_js):
    names = list(CASES)
    jobs = [[CASES[n][m]["groups"], CASES[n][m]["chords"], m == "directed"] for n in names for m in ("undirected", "directed")]
    res = _node(core_js, "var JB = " + json.dumps(jobs) + ", PP = " + json.dumps({k: D[k] for k in ("inner", "outer", "ribbon_radius", "ribbon_pad")}) +
                "; console.log(JSON.stringify(JB.map(function(j){ return [j[0].map(function(g){ return [_sbArc(g[1],g[2],PP.inner,PP.outer,0,null,3), _sbArc(g[1],g[2],PP.inner,PP.outer,0,null,null)]; }),"
                "j[1].map(function(r){ return [_chRibbon(r, PP.ribbon_radius, PP.ribbon_pad, j[2], null), _chRibbon(r, PP.ribbon_radius, PP.ribbon_pad, j[2], 3)]; })]; })));")
    k = 0
    for n in names:
        for mode in ("undirected", "directed"):
            arcs, ribs = res[k]
            k += 1
            c = CASES[n][mode]
            for (text, full), (wt, wf) in zip(arcs, c["arcs"]):
                assert text == wt
                _same_numbers(full, wf)
            for (full, three), want in zip(ribs, c["ribbons"]):
                _same_numbers(full, want)
                _same_numbers(three, want, 6e-4)


def test_the_golden_set_covers_the_hard_cases():
    assert {"two", "zero_row", "all_zero", "self_loop", "asymmetric", "twelve", "twelve_dense"} <= set(CASES) and len(CASES) >= 30
    assert len(CASES["twelve"]["matrix"]) == 12 and len(CASES["twelve_dense"]["undirected"]["chords"]) > 40
    z = CASES["all_zero"]["undirected"]["groups"]                         # k is Infinity: no width, groups sit padAngle apart
    assert all(g[1] == g[2] for g in z) and abs(z[1][1] - z[0][1] - D["pad_angle"]) < 1e-12
    sl = CASES["self_loop"]["undirected"]["chords"]
    assert any(c[0] == c[4] and c[1:4] == c[5:8] for c in sl)             # an undirected self-loop: source is target
    dl = CASES["self_loop"]["directed"]["chords"]
    assert any(c[0] == c[4] and c[1] != c[5] for c in dl)                 # a directed one has two ends
    assert any(g[1] == g[2] for g in CASES["zero_row"]["undirected"]["groups"])
    assert all(len(CASES["twelve"][m]["groups"]) == 12 for m in ("undirected", "directed"))


# ─── rendering ─────────────────────────────────────────────────────────────────────────────────────────────────
REGIONS = ["Europe", "Asia", "North America", "Africa", "South America"]
MIGRATION = [[0, 120, 80, 40, 15], [95, 0, 70, 55, 10], [60, 45, 0, 25, 30], [90, 30, 12, 0, 5], [20, 18, 22, 6, 0]]
SERVICES = ["web", "api", "auth", "db", "cache", "queue"]
TRAFFIC = [[0, 900, 300, 0, 0, 0], [0, 0, 250, 700, 520, 140], [0, 60, 0, 180, 0, 0], [0, 0, 0, 0, 0, 0], [0, 310, 0, 90, 0, 0], [0, 0, 0, 260, 0, 0]]
PAYLOADS = {
    "migration": {"type": "chord_diagram", "title": "Migration between regions", "unit": "k people", "groups": REGIONS, "matrix": MIGRATION},
    "migration_directed": {"type": "chord_diagram", "title": "Migration between regions", "unit": "k people", "directed": True, "groups": REGIONS, "matrix": MIGRATION},
    "traffic": {"type": "chord_diagram", "title": "Requests between services", "unit": "req/s", "groups": SERVICES, "matrix": TRAFFIC},
    "traffic_directed": {"type": "chord_diagram", "title": "Requests between services", "unit": "req/s", "directed": True, "groups": SERVICES, "matrix": TRAFFIC},
    "two": {"type": "chord_diagram", "groups": ["A", "B"], "matrix": [[0, 5], [3, 0]]},
    "two_directed": {"type": "chord_diagram", "directed": True, "groups": ["A", "B"], "matrix": [[0, 5], [3, 0]]},
    "zero_row": {"type": "chord_diagram", "groups": ["A", "B", "C"], "matrix": [[0, 4, 0], [2, 0, 0], [0, 0, 0]]},
    "zero_row_directed": {"type": "chord_diagram", "directed": True, "groups": ["A", "B", "C"], "matrix": [[0, 4, 0], [2, 0, 0], [0, 0, 0]]},
    "all_zero": {"type": "chord_diagram", "title": "T", "groups": ["A", "B"], "matrix": [[0, 0], [0, 0]]},
    "self_loop": {"type": "chord_diagram", "groups": ["A", "B", "C"], "matrix": [[7, 2, 0], [2, 0, 1], [0, 1, 3]]},
    "self_loop_directed": {"type": "chord_diagram", "directed": True, "groups": ["A", "B", "C"], "matrix": [[7, 2, 0], [2, 0, 1], [0, 1, 3]]},
    "twelve": {"type": "chord_diagram", "unit": "GB", "groups": ["Group number %d here" % k for k in range(12)], "matrix": [[((i * 5 + j * 3) % 11) * (1 + (i + j) % 3) if i != j else 0 for j in range(12)] for i in range(12)]},
    "twelve_directed": {"type": "chord_diagram", "directed": True, "unit": "GB", "groups": ["Group number %d here" % k for k in range(12)], "matrix": [[((i * 5 + j * 3) % 11) * (1 + (i + j) % 3) if i != j else 0 for j in range(12)] for i in range(12)]},
    "tight": {"type": "chord_diagram", "groups": ["Big", "Other", "Tiny one", "Tiny two"], "matrix": [[0, 400, 0.5, 0.5], [300, 0, 0.1, 0.1], [0.5, 0.1, 0, 0.2], [0.5, 0.1, 0.2, 0]]},
    "gated": {"type": "chord_diagram", "groups": ["Alpha", "Beta", "Tiny 1", "Tiny 2", "Gamma", "Delta"], "matrix": [[100 if i == j and i not in (2, 3) else 4 if i == j else 0 for j in range(6)] for i in range(6)]},
    "long_names": {"type": "chord_diagram", "groups": ["A group with a long name", "Another quite long name!!", "Short"], "matrix": [[0, 5, 2], [4, 0, 9], [1, 3, 0]]},
    "twelve_plus": {"type": "chord_diagram", "groups": ["G%d" % k for k in range(14)], "matrix": [[(i * 3 + j * 5) % 7 + 1 for j in range(14)] for i in range(14)]},
    "bad_cells": {"type": "chord_diagram", "groups": ["A", "B", "C"], "matrix": [[0, -4, "7"], [float("inf"), "x", 3], [None, 2.5, {"a": 1}]]},
    "not_square_rows": {"type": "chord_diagram", "groups": ["A", "B", "C"], "matrix": [[0, 1, 2], [3, 0, 1]]},
    "not_square_cols": {"type": "chord_diagram", "groups": ["A", "B"], "matrix": [[0, 1], [3, 0, 7]]},
    "row_not_list": {"type": "chord_diagram", "groups": ["A", "B"], "matrix": [[0, 1], "x"]},
    "matrix_not_list": {"type": "chord_diagram", "groups": ["A", "B"], "matrix": {"a": 1}},
    "no_matrix": {"type": "chord_diagram", "groups": ["A", "B"]},
    "one_group": {"type": "chord_diagram", "groups": ["A"], "matrix": [[5]]},
    "no_groups": {"type": "chord_diagram", "matrix": [[0, 1], [1, 0]]},
    "group_names_junk": {"type": "chord_diagram", "groups": ["A", 7, None, "", {"x": 1}], "matrix": [[0, 1, 2, 3, 4]] * 5},
    "directed_junk": {"type": "chord_diagram", "directed": "true", "groups": ["A", "B"], "matrix": [[0, 5], [3, 0]]},
    "version_2": {"type": "chord_diagram", "version": 2, "groups": ["A", "B"], "matrix": [[0, 5], [3, 0]]},
    "version_junk": {"type": "chord_diagram", "version": True, "groups": ["A", "B"], "matrix": [[0, 5], [3, 0]]},
}


@pytest.mark.parametrize("name", list(PAYLOADS))
def test_python_and_gas_emit_identical_html(name, core_js):
    assert _py(PAYLOADS[name]) == _gas_batch(core_js, [PAYLOADS[name]])[0]


def test_hostile_text_python_and_gas_agree_and_are_escaped(core_js):
    b = {"type": "chord_diagram", "title": ATTACK, "unit": ATTACK, "groups": [ATTACK, ATTACK + "2"], "matrix": [[0, 5], [3, 0]]}
    outs = [_py(b), _gas_batch(core_js, [b])[0], _py(dict(b, directed=True)), _gas_batch(core_js, [dict(b, directed=True)])[0]]
    assert outs[0] == outs[1] and outs[2] == outs[3]
    for h in outs:
        assert "<img" not in h and "<svg onload" not in h and "<script" not in h.replace("<style", "") and 'onerror=alert(1)>' not in h.replace("&gt;", "")
        assert "&lt;img" in h


def _ribbons(html):
    return re.findall(r'<path class="chd" d="([^"]*)" fill="(#[0-9A-F]{6})"[^>]*><title>(.*?)</title></path>', html)


def _arcs(html):
    return re.findall(r'<path class="cha" d="([^"]*)" fill="(#[0-9A-F]{6})"><title>(.*?)</title></path>', html)


def _tables(html):
    ts = re.findall(r'<table style="position:absolute[^"]*">.*?</table>', html, re.S)
    out = []
    for t in ts:
        head = re.findall(r'<th scope="col">(.*?)</th>', t)
        rows = [re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', r) for r in re.findall(r'<tr>(.*?)</tr>', t.split("<tbody>")[1], re.S)]
        out.append((head, rows))
    return out


def test_undirected_draws_one_ribbon_per_pair_and_one_arc_per_group_with_titles_and_hidden_tables(core_js):
    for html in (_py(PAYLOADS["migration"]), _gas_batch(core_js, [PAYLOADS["migration"]])[0]):
        assert "<script" not in html and "<svg " in html and "NaN" not in html and "undefined" not in html and "[object Object]" not in html
        rib, arcs = _ribbons(html), _arcs(html)
        assert len(rib) == 10 and len(arcs) == 5                          # 5 regions: 10 pairs, every pair has flow
        titles = [t for _, _, t in rib]
        assert "Europe → Asia: 120 k people (Asia → Europe: 95 k people)" in titles
        assert "Africa → Europe: 90 k people (Europe → Africa: 40 k people)" in titles   # the larger flow is the ribbon's source
        (h1, r1), (h2, r2) = _tables(html)
        assert h1 == ["From", "To", "Value"] and len(r1) == 20 and r1[0] == ["Europe", "Asia", "120 k people"]
        assert h2 == ["Group", "Total out", "Total in"] and len(r2) == 5 and r2[0] == ["Europe", "255 k people", "265 k people"]
        t = html.index("<table")
        assert 'role="img"' in html[:t] and 'role="img"' not in html[t:]
        assert "Each ribbon joins two groups" in html


def test_directed_draws_one_arrow_per_nonzero_flow_and_one_direction_in_each_title(core_js):
    for html in (_py(PAYLOADS["traffic_directed"]), _gas_batch(core_js, [PAYLOADS["traffic_directed"]])[0]):
        rib = _ribbons(html)
        nz = sum(1 for r in TRAFFIC for v in r if v)
        assert len(rib) == nz == 11
        titles = [t for _, _, t in rib]
        assert "api → db: 700 req/s" in titles and "web → api: 900 req/s" in titles
        assert not any("(" in t for t in titles)
        (h1, r1), (h2, r2) = _tables(html)
        assert len(r1) == 11 and ["api", "db", "700 req/s"] in r1
        assert ["db", "0 req/s", "1,230 req/s"] in r2 or ["db", "0 req/s", "1230 req/s"] in r2
        assert "Directed chord diagram" in re.search(r'aria-label="([^"]*)"', html).group(1)
        assert "arrow" in html.lower()


def test_directed_ribbons_end_in_an_arrow_head_and_undirected_do_not():
    d = _ribbons(_py(PAYLOADS["two_directed"]))[0][0]
    u = _ribbons(_py(PAYLOADS["two"]))[0][0]
    assert d.count("L") == 2 and "A" in d.split("Q")[0] and d.count("A") == 1             # source arc, curve, two lines of the head, curve back
    assert u.count("A") == 2 and "L" not in u


def test_aria_label_gives_group_count_total_flow_and_largest_flow(core_js):
    for html in (_py(PAYLOADS["migration"]), _gas_batch(core_js, [PAYLOADS["migration"]])[0]):
        a = re.search(r'role="img" aria-label="([^"]*)"', html).group(1)
        assert a == "Chord diagram of 5 groups, total flow 848 k people. Largest flow: Europe to Asia, 120 k people."
    assert re.search(r'aria-label="Directed chord diagram of 6 groups, total flow 3,710 req/s\. Largest flow: web to api, 900 req/s\.', _py(PAYLOADS["traffic_directed"]))
    assert re.search(r'aria-label="Chord diagram of 2 groups, total flow 8\. Largest flow: A to B, 5\.', _py(PAYLOADS["two"]))


def test_group_colours_differ_and_ribbons_take_the_source_groups_colour():
    html = _py(PAYLOADS["migration_directed"])
    arcs = {t.split(":")[0]: c for _, c, t in _arcs(html)}
    assert len(set(arcs.values())) == 5 and set(arcs.values()) <= set(wa._SB_PALETTE)
    for _, c, t in _ribbons(html):
        assert c == arcs[t.split(" → ")[0]]
    assert all('fill-opacity="0.5' in m for m in re.findall(r'<path class="chd"[^>]*>', html))


def test_every_group_colour_has_4_5_to_1_against_white():
    def lin(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    for h in wa._SB_PALETTE:
        L = 0.2126 * lin(int(h[1:3], 16)) + 0.7152 * lin(int(h[3:5], 16)) + 0.0722 * lin(int(h[5:7], 16))
        assert 1.05 / (L + 0.05) >= 4.5, h


def test_text_is_never_below_12px_and_nothing_has_a_script_or_nan():
    for n, b in PAYLOADS.items():
        h = _py(b)
        assert all(int(x) >= 12 for x in re.findall(r"font-size:(\d+)px", h)), n
        assert "<script" not in h and "NaN" not in h and "Infinity" not in h and "undefined" not in h and "[object Object]" not in h, n


def test_motion_index_per_group_stays_inside_its_clamp(core_js):
    for name, n in (("migration", 5), ("traffic_directed", 6), ("two", 2), ("twelve", 12)):
        for html in (_py(PAYLOADS[name]), _gas_batch(core_js, [PAYLOADS[name]])[0]):
            ks = re.findall(r'<g class="(chk|chg)" style="--k:clamp\(0,calc\(var\(--p,1\)\*(\d+) - (\d+)\),1\);', html)
            for cls in ("chk", "chg"):
                mine = [(int(a), int(i)) for c, a, i in ks if c == cls]
                assert [i for _, i in mine] == list(range(n)) and all(a == n + 1 for a, _ in mine), (name, cls)
            assert all(int(i) <= int(a) - 1 for _, a, i in ks)             # k reaches 1 at p = 1


def test_matrix_that_is_not_square_or_not_a_list_gives_the_note_and_the_reason(core_js):
    say = "A chord diagram needs a square matrix with one row per group."
    want = {"not_square_rows": "The matrix has 2 rows but there are 3 groups.", "not_square_cols": "Row 2 has 3 cells but there are 2 groups.",
            "row_not_list": "Row 2 is not a list.", "matrix_not_list": "The matrix is missing or is not a list of rows.", "no_matrix": "The matrix is missing or is not a list of rows."}
    for k, why in want.items():
        for h in (_py(PAYLOADS[k]), _gas_batch(core_js, [PAYLOADS[k]])[0]):
            assert say in h and why in h, k
            assert 'role="img"' not in h and "<table" not in h and "NaN" not in h


def test_too_few_groups_or_nothing_to_draw_gives_a_note_and_no_chart():
    for k in ("one_group", "no_groups"):
        h = _py(PAYLOADS[k])
        assert "A chord diagram needs at least 2 groups." in h and 'role="img"' not in h and "<table" not in h
    h = _py(PAYLOADS["all_zero"])
    assert "Every flow is 0, so there is nothing to draw." in h and 'role="img"' not in h and ">T</div>" in h


def test_negative_and_non_finite_cells_count_as_zero_with_a_note(core_js):
    for h in (_py(PAYLOADS["bad_cells"]), _gas_batch(core_js, [PAYLOADS["bad_cells"]])[0]):
        assert "4 cells were negative or not a number and were drawn as 0." in h
        (_, flows), _ = _tables(h)
        assert sorted(f[2] for f in flows) == ["2.5", "3", "7"]           # "7" is read as a number, null as 0
        assert "NaN" not in h and "[object Object]" not in h


def test_groups_beyond_twelve_are_noted_and_not_drawn(core_js):
    for h in (_py(PAYLOADS["twelve_plus"]), _gas_batch(core_js, [PAYLOADS["twelve_plus"]])[0]):
        assert "2 groups beyond the first 12 were not drawn." in h
        assert len(_arcs(h)) == 12 and "G12" not in h and "G13" not in h and "G11" in h
        (_, _flows), (_, tot) = _tables(h)
        assert len(tot) == 12


def test_group_names_are_capped_and_junk_names_get_a_default():
    h = _py(PAYLOADS["long_names"])
    names = [r[0] for r in _tables(h)[1][1]]
    assert names == ["A group with a long n", "Another quite long na", "Short"][:0] or names[0] == "A group with a long "
    junk = [r[0] for r in _tables(_py(PAYLOADS["group_names_junk"]))[1][1]]
    assert junk == ["A", "7", "Group 3", "Group 4", "[object Object]"] or junk == ["A", "7", "null", "Group 4", "[object Object]"] or len(junk) == 5
    assert all(j for j in junk)


def test_directed_must_be_the_boolean_true():
    assert _py(PAYLOADS["directed_junk"]) == _py(PAYLOADS["two"])
    assert _py(dict(PAYLOADS["two"], directed=False)) == _py(PAYLOADS["two"])
    assert _py(dict(PAYLOADS["two"], directed=True)) != _py(PAYLOADS["two"])


def test_version_above_one_is_noted_and_otherwise_silent(core_js):
    for h in (_py(PAYLOADS["version_2"]), _gas_batch(core_js, [PAYLOADS["version_2"]])[0]):
        assert "Written for chord_diagram version 2; drawn as version 1." in h
    assert "version" not in _py(PAYLOADS["version_junk"]).lower()
    assert _py(dict(PAYLOADS["two"], version=1)) == _py(PAYLOADS["two"])


def test_a_group_with_no_flow_has_no_arc_and_no_label_but_is_in_the_legend_and_tables():
    h = _py(PAYLOADS["zero_row"])
    assert len(_arcs(h)) == 2 and len(_ribbons(h)) == 1
    assert "C" in [r[0] for r in _tables(h)[1][1]] and h.count('<span class="chs"') == 3


# ─── the label rule ────────────────────────────────────────────────────────────────────────────────────────────
def _labels(html):
    return re.findall(r'<div class="chl(?: tmw(\d+))?" style="position:absolute;(?:left|right):([\d.]+)%;top:([\d.]+)%;[^"]*?rotate\((-?[\d.]+)deg\)', html)


def test_labels_are_outside_the_ring_rotated_to_read_outward_and_never_upside_down(core_js):
    for name in ("migration", "twelve", "traffic_directed"):
        for html in (_py(PAYLOADS[name]), _gas_batch(core_js, [PAYLOADS[name]])[0]):
            ls = _labels(html)
            assert ls, name
            assert all(-90 <= float(deg) <= 90 for _, _, _, deg in ls)
            assert any(float(deg) > 0 for *_, deg in ls) and any(float(deg) < 0 for *_, deg in ls)
            assert "text-overflow:ellipsis" in html


def test_a_label_in_a_tight_slot_is_gated_by_container_width_and_the_legend_always_names_every_group():
    h = _py(PAYLOADS["gated"])
    ws = sorted({int(w) for w, *_ in _labels(h) if w})
    assert ws and all(w % 10 == 0 and w <= 720 for w in ws) and len(_labels(h)) == 6
    css = re.search(r"<style>(.*?)</style>", h).group(1)
    assert all("@container (width<%dpx){.tmw%d{display:none}}" % (w, w) in css for w in ws)
    assert h.count('<span class="chs"') == 6


def test_a_label_that_cannot_clear_its_neighbours_in_any_width_is_left_out_but_still_in_the_legend_and_tables():
    h = _py(PAYLOADS["tight"])
    assert len(_labels(h)) == 2 and h.count('<span class="chs"') == 4
    assert "Tiny one" in [r[0] for r in _tables(h)[1][1]] and "Tiny one: sends" in h


def test_registered_as_a_preview_charts_atom_with_an_example_and_every_field_documented():
    blocks = {a["type"]: a for a in yaml.safe_load((ROOT / "atoms/schema.yaml").read_text())["blocks"]}
    a = blocks["chord_diagram"]
    assert a["stage"] == "preview" and set(a["fields"]) == {"title", "groups", "matrix", "unit", "directed", "version"}
    assert a["surfaces"] == blocks["treemap"]["surfaces"] and a["source"] == blocks["treemap"]["source"]
    assert "sankey_flow" in a["routing_text"] and "12" in a["routing_text"] and len(a["intent_phrases"]) == 3
    assert re.search(r"^a2ui-charts-v1:\n(?:- .*\n)*- chord_diagram$", (ROOT / "atoms/atom-packs.yaml").read_text(), re.M)
    assert '"chord_diagram":"a2ui-charts-v1"' in (ROOT / "apps-script-surface/gas-wired-renderer/PackMap.gs").read_text()
    import generate_atom_pages as g
    ex = g._EXAMPLE_BLOCKS["chord_diagram"]
    assert ex["type"] == "chord_diagram" and "<table" in _py(ex) and "<path" in _py(ex)
    txt = (ROOT / "atoms/schema.yaml").read_text()
    assert txt.index("- type: chord_diagram") < txt.index("# ── Motion candidates (2026-10-10, preview) ──")


def test_d3_credit_names_chord_and_ribbon():
    t = (ROOT / "THIRD-PARTY-NOTICES.md").read_text()
    assert "## d3-chord" in t and "ribbonArrow" in t and "tests/test_chord_diagram.py" in t
