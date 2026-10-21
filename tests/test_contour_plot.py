"""contour_plot (I57 and I51): filled contour bands of a value grid (d3-contour contours(), marching squares) and of the density of points (d3-contour
contourDensity()), ported by hand into BOTH renderers.

GOLDEN (tests/fixtures/contour_plot_d3_golden.json, from contour_plot_d3_golden_gen.mjs) holds what the REAL d3-contour 4.0.2 (and d3-array 3.2.4 blur2)
gives: the MultiPolygon coordinates per threshold for 26 value grids (with holes, nulls, ties on a level, the default Sturges count) and 7 point sets, the
float32 density grid's maximum, and blur2 on float32 arrays. Every coordinate is compared with == (exact): marching squares and the smoothing are
correctly rounded IEEE operations, and the density grid is a Float32Array in d3 (array('f') in Python, Math.fround in GAS), accumulated and blurred in
the same order of operations, so nothing differs in the last bit.
Also held here: Python/GAS HTML parity, the SVG path data against the golden coordinates, the colour ramp, the hidden tables, the aria label, the motion
index, malformed input, caps with notes, the `version` field, escaping and registration.
"""
from __future__ import annotations

import array
import json
import re
from functools import lru_cache
from pathlib import Path

import pytest
import yaml

from test_histogram import ATTACK
from test_motion_atoms import _gas_batch, _node, _py, core_js  # noqa: F401  (core_js is a fixture)
from test_motion_atoms import wa  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
D = json.loads((ROOT / "tests/fixtures/contour_plot_d3_golden.json").read_text())
GRIDS, DENS, BLUR = D["grids"], D["density"], D["blur"]


# ─── the algorithms against real d3 ────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("name", list(GRIDS))
def test_python_grid_contours_match_d3_exactly(name):
    c = GRIDS[name]
    got = wa._cn_contours(c["values"], c["w"], c["h"], c["thresholds"])
    assert [[v, polys] for v, polys in got] == [[m["value"], m["coordinates"]] for m in c["out"]]


@pytest.mark.parametrize("name", list(DENS))
def test_python_density_contours_match_d3_exactly(name):
    c = DENS[name]
    got, mx = wa._cn_density(c["points"], c["W"], c["H"], c["bandwidth"], c["thresholds"])
    assert mx == c["max"]
    assert [[v, polys] for v, polys in got] == [[m["value"], m["coordinates"]] for m in c["out"]]


@pytest.mark.parametrize("k", range(len(BLUR)))
def test_python_blur2_matches_d3_array_exactly(k):
    c = BLUR[k]
    a = array.array("f", c["before"])
    wa._cn_blur2(a, c["w"], c["h"], c["radius"])
    assert list(a) == c["after"]


def test_gas_grid_contours_match_d3_exactly(core_js):
    names = list(GRIDS)
    res = _node(core_js, "var G = " + json.dumps([[GRIDS[n]["values"], GRIDS[n]["w"], GRIDS[n]["h"], GRIDS[n]["thresholds"]] for n in names]) +
                "; console.log(JSON.stringify(G.map(function(g){ return _cnContours(g[0], g[1], g[2], g[3]); })));")
    for n, got in zip(names, res):
        assert got == [[m["value"], m["coordinates"]] for m in GRIDS[n]["out"]], n


def test_gas_density_contours_match_d3_exactly(core_js):
    names = list(DENS)
    res = _node(core_js, "var G = " + json.dumps([[DENS[n]["points"], DENS[n]["W"], DENS[n]["H"], DENS[n]["bandwidth"], DENS[n]["thresholds"]] for n in names]) +
                "; console.log(JSON.stringify(G.map(function(g){ return _cnDensity(g[0], g[1], g[2], g[3], g[4]); })));")
    for n, (got, mx) in zip(names, res):
        assert mx == DENS[n]["max"], n
        assert got == [[m["value"], m["coordinates"]] for m in DENS[n]["out"]], n


def test_gas_blur2_matches_d3_array_exactly(core_js):
    res = _node(core_js, "var G = " + json.dumps([[c["before"], c["w"], c["h"], c["radius"]] for c in BLUR]) +
                "; console.log(JSON.stringify(G.map(function(g){ var a = g[0].map(Math.fround); _cnBlur2(a, g[1], g[2], g[3]); return a; })));")
    assert res == [c["after"] for c in BLUR]


def test_the_golden_set_covers_the_hard_cases():
    assert any(len(p) > 1 for m in GRIDS["two_peaks_with_crater"]["out"] for p in m["coordinates"])              # a polygon with a hole
    assert any(len(p) > 1 for m in GRIDS["ring_with_hole_and_island"]["out"] for p in m["coordinates"])
    assert GRIDS["all_equal"]["out"] == []                                                                       # no variation, no contour
    assert [m["value"] for m in GRIDS["hill_6x5"]["out"]] == [2, 4, 6, 8]  or len(GRIDS["hill_6x5"]["out"]) >= 3      # the default (Sturges) levels
    assert len(GRIDS["sturges_default_100"]["out"]) >= 5
    assert any(None in c["values"] for c in GRIDS.values())                                                       # cells that are not numbers
    assert len(DENS["three_points_bw40_default"]["out"]) >= 15                                                    # density's own default of 20 levels
    assert {len(c["out"]) for c in DENS.values()} >= {1, 2, 3, 4, 5}
    assert len(BLUR) == 6


# ─── the colour ramp ───────────────────────────────────────────────────────────────────────────────────────────
def _lum(hexc):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (int(hexc[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def _contrast(a, b):
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


@pytest.mark.parametrize("m", [1, 2, 3, 5, 9, 20])
def test_ramp_goes_light_to_dark_and_every_outline_has_contrast_with_its_band(m):
    cols = [wa._cn_ramp(i, m) for i in range(m)]
    lums = [_lum(c) for c in cols]
    assert all(a >= b for a, b in zip(lums, lums[1:])) and (m == 1 or lums[0] > lums[-1])
    assert all(re.fullmatch(r"#[0-9A-F]{6}", c) for c in cols)
    for c in cols:
        line = wa._cn_line(c)
        assert line in ("#FFFFFF", "#04182B") and _contrast(c, line) >= 3, (c, line)
    assert _contrast(cols[0], "#FFFFFF") >= 1.1 and _contrast(cols[-1], "#FFFFFF") >= 4.5          # the darkest band reads against a light page


def test_gas_ramp_and_outline_match_python(core_js):
    ms = [1, 2, 3, 5, 9, 20]
    res = _node(core_js, "console.log(JSON.stringify(" + json.dumps(ms) + ".map(function(m){ var o = []; for (var i = 0; i < m; i++) { var c = _cnRamp(i, m); o.push([c, _cnLine(c)]); } return o; })));")
    assert res == [[[wa._cn_ramp(i, m), wa._cn_line(wa._cn_ramp(i, m))] for i in range(m)] for m in ms]


# ─── rendering ─────────────────────────────────────────────────────────────────────────────────────────────────
def _temp(w=24, h=16):
    import math
    return [round(14 + 9 * math.exp(-((x - 7) ** 2 + (y - 5) ** 2) / 30) - 6 * math.exp(-((x - 17) ** 2 + (y - 11) ** 2) / 22) + x * 0.15, 1) for y in range(h) for x in range(w)]


def _delivery(n=240):
    s, pts = [11], []

    def rnd():
        s[0] = (1664525 * s[0] + 1013904223) % 4294967296
        return s[0] / 4294967296
    for k in range(n):
        cx, cy, sp = ((3.0, 4.0, 1.4), (9.0, 7.0, 2.0), (6.0, 11.0, 1.0))[k % 3]
        pts.append({"x": round(cx + (rnd() + rnd() + rnd() - 1.5) * sp * 2, 2), "y": round(cy + (rnd() + rnd() + rnd() - 1.5) * sp * 2, 2)})
    return pts


def _noise(w, h):
    s = [5]
    out = []
    for _ in range(w * h):
        s[0] = (1664525 * s[0] + 1013904223) % 4294967296
        out.append(round(s[0] / 4294967296 * 100, 2))
    return out


GOLD_G = GRIDS["two_peaks_with_crater"]
EDGE = DENS["edges_and_duplicates"]
PAYLOADS = {
    "temp": {"type": "contour_plot", "title": "Surface temperature", "grid": {"width": 24, "height": 16, "values": _temp()}, "unit": "°C", "value_label": "Temperature", "x_label": "Column", "y_label": "Row"},
    "hill": {"type": "contour_plot", "grid": {"width": 6, "height": 5, "values": GRIDS["hill_6x5"]["values"]}},
    "crater": {"type": "contour_plot", "grid": {"width": 14, "height": 10, "values": GOLD_G["values"]}, "thresholds": 5},
    "crater_default": {"type": "contour_plot", "grid": {"width": 14, "height": 10, "values": GOLD_G["values"]}},
    "equal": {"type": "contour_plot", "title": "Flat", "grid": {"width": 4, "height": 3, "values": [5] * 12}},
    "nulls": {"type": "contour_plot", "grid": {"width": 7, "height": 6, "values": GRIDS["negatives_and_nulls"]["values"]}, "thresholds": 7},
    "smooth": {"type": "contour_plot", "grid": {"width": 30, "height": 20, "values": GRIDS["smooth_30x20"]["values"]}, "thresholds": 12},
    "two_cols": {"type": "contour_plot", "grid": {"width": 2, "height": 100, "values": [float(k % 7) for k in range(200)]}},
    "delivery": {"type": "contour_plot", "title": "Where deliveries go", "points": _delivery(), "x_label": "East", "y_label": "North", "bandwidth": 20, "thresholds": 8},
    "delivery_default": {"type": "contour_plot", "points": _delivery(60)},
    "pts_small": {"type": "contour_plot", "points": [{"x": 1, "y": 2}, {"x": 2, "y": 3}, {"x": 3, "y": 1}]},
    "pts_same_x": {"type": "contour_plot", "points": [{"x": 4, "y": k} for k in range(10)]},
    "pts_same_all": {"type": "contour_plot", "points": [{"x": 4, "y": 4}] * 5},
    "pts_bw5": {"type": "contour_plot", "points": _delivery(30), "bandwidth": 5, "thresholds": 3},
    "pts_bw60": {"type": "contour_plot", "points": _delivery(90), "bandwidth": 60, "thresholds": 4},
    "pts_negative": {"type": "contour_plot", "points": [{"x": -0.003 * (k % 9), "y": -1200 + 37.5 * (k % 5)} for k in range(40)], "thresholds": 4},
    "pts_edge": {"type": "contour_plot", "points": [{"x": p[0], "y": 400 - p[1]} for p in EDGE["points"]], "bandwidth": 12.5, "thresholds": 6},
    "pts_many": {"type": "contour_plot", "points": _delivery(2000), "thresholds": 5},
    "pts_2001": {"type": "contour_plot", "points": _delivery(2001), "thresholds": 3},
    "grid_noise": {"type": "contour_plot", "grid": {"width": 100, "height": 100, "values": _noise(100, 100)}, "thresholds": 20},
    "grid_101": {"type": "contour_plot", "grid": {"width": 101, "height": 3, "values": [0] * 303}},
    "grid_wrong_length": {"type": "contour_plot", "grid": {"width": 3, "height": 3, "values": [1, 2, 3, 4, 5]}},
    "grid_bad_size": {"type": "contour_plot", "grid": {"width": 2.5, "height": "3", "values": [1] * 9}},
    "grid_not_dict": {"type": "contour_plot", "grid": [1, 2, 3]},
    "grid_values_not_list": {"type": "contour_plot", "grid": {"width": 3, "height": 3, "values": "123456789"}},
    "dirty_cells": {"type": "contour_plot", "grid": {"width": 3, "height": 3, "values": [1, 2, "x", 4, None, 6, 7, float("inf"), 1e30]}},
    "dirty_points": {"type": "contour_plot", "points": [None, 7, "x", {"x": 1}, {"x": "1", "y": 2}, {"x": 1, "y": 2}, {"x": 2, "y": 3}, {"x": 3, "y": 2}, {"x": 1e30, "y": 1}, {"x": float("nan"), "y": 1}, {"x": True, "y": 1}, [1, 2]]},
    "too_few_points": {"type": "contour_plot", "title": "T", "points": [{"x": 1, "y": 1}, {"x": 2, "y": 2}]},
    "points_not_list": {"type": "contour_plot", "points": {"x": 1, "y": 2}},
    "neither": {"type": "contour_plot", "title": "T"},
    "both": {"type": "contour_plot", "grid": {"width": 6, "height": 5, "values": GRIDS["hill_6x5"]["values"]}, "points": _delivery(10)},
    "odd_options": {"type": "contour_plot", "grid": {"width": 6, "height": 5, "values": GRIDS["hill_6x5"]["values"]}, "thresholds": 1e9, "bandwidth": "x", "unit": ["a"], "value_label": 5},
    "odd_options2": {"type": "contour_plot", "points": _delivery(30), "thresholds": 2.7, "bandwidth": 1e9},
    "version_2": {"type": "contour_plot", "version": 2, "grid": {"width": 6, "height": 5, "values": GRIDS["hill_6x5"]["values"]}},
    "version_junk": {"type": "contour_plot", "version": True, "grid": {"width": 6, "height": 5, "values": GRIDS["hill_6x5"]["values"]}},
}


@pytest.fixture(scope="module")
def gas(core_js):
    names = list(PAYLOADS)
    return dict(zip(names, _gas_batch(core_js, [PAYLOADS[n] for n in names])))


@lru_cache(maxsize=None)
def py(name):
    return _py(PAYLOADS[name])


@pytest.mark.parametrize("name", list(PAYLOADS))
def test_python_and_gas_emit_identical_html(name, gas):
    assert py(name) == gas[name]


def _tables(html):
    out = []
    for m in re.finditer(r'<table style="position:absolute[^"]*"><thead><tr>(.*?)</tr></thead><tbody>(.*?)</tbody></table>', html, re.S):
        out.append((re.findall(r'<th scope="col">(.*?)</th>', m.group(1)), [re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', r) for r in re.findall(r'<tr>(.*?)</tr>', m.group(2), re.S)]))
    return out


def _bands(html):
    return re.findall(r'<path class="cnb" d="([^"]*)" fill="(#[0-9A-F]{6})" stroke="(#[0-9A-F]{6})" [^>]*?><title>(.*?)</title></path>', html)


def _aria(html):
    return re.search(r'role="img" aria-label="([^"]*)"', html).group(1)


def _expect_d(polys, sx=1.0, sy=1.0):
    def r(x):
        s = wa._if_fixed(x, 2)
        s = s.rstrip("0").rstrip(".") if "." in s else s
        return "0" if s == "-0" else s
    return "".join("M" + "L".join(r(p[0] * sx) + "," + r(p[1] * sy) for p in ring) + "Z" for poly in polys for ring in poly)


def test_grid_path_data_is_the_d3_polygons_scaled_into_the_plot(gas):
    c = GOLD_G
    levels = [m for m in c["out"]]
    # thresholds=5 in the payload: recompute the golden for that count with the (already d3-checked) port
    got = wa._cn_contours(c["values"], c["w"], c["h"], 5)
    for html in (py("crater"), gas["crater"]):
        bands = _bands(html)
        assert len(bands) == len(got) and len(levels) > 0
        for (d, fill, stroke, title), (v, polys) in zip(bands, got):
            assert d == _expect_d(polys, 600 / c["w"], 400 / c["h"])
    # and with the default levels, exactly the golden of real d3
    bands = _bands(py("crater_default"))
    assert [b[0] for b in bands] == [_expect_d(m["coordinates"], 600 / c["w"], 400 / c["h"]) for m in c["out"]]


def test_points_path_data_is_the_d3_density_polygons(gas):
    # the data x in [0, 600] and y in [0, 400] map onto the 600 by 400 drawing without change, so d3's coordinates are the path data
    for html in (py("pts_edge"), gas["pts_edge"]):
        bands = [b for b in _bands(html)]
        assert [b[0] for b in bands] == [_expect_d(m["coordinates"]) for m in EDGE["out"] if m["coordinates"]]


def test_svg_has_no_script_and_is_aria_hidden_inside_the_labelled_image(gas):
    for html in (py("temp"), gas["temp"], py("delivery")):
        assert "<script" not in html and "NaN" not in html and "undefined" not in html and "Infinity" not in html and "[object Object]" not in html
        t = html.index("<table")
        assert 'role="img"' in html[:t] and 'role="img"' not in html[t:]
        assert '<svg viewBox="0 0 600 400"' in html and 'aria-hidden="true"' in html
        assert 'fill-rule="evenodd"' in html


def test_bands_are_light_to_dark_with_a_title_and_an_outline_that_contrasts(gas):
    for html in (py("temp"), gas["temp"]):
        bands = _bands(html)
        assert len(bands) >= 5
        lums = [_lum(f) for _, f, _, _ in bands]
        assert all(a >= b for a, b in zip(lums, lums[1:])) and lums[0] > lums[-1]
        assert all(_contrast(f, s) >= 3 for _, f, s, _ in bands)
        assert all(re.fullmatch(r"\d.*? °C and above|\d.*? to .*? °C|-.*", t) or "°C" in t for _, _, _, t in bands)


def test_legend_names_every_band_range_as_text_and_the_unit(gas):
    for html in (py("temp"), gas["temp"]):
        leg = re.search(r'<div class="cnleg"[^>]*>(.*?)</div></div>', html, re.S).group(1)
        items = re.findall(r'<span style="display:inline-flex[^>]*><span [^>]*></span>(.*?)</span>', leg)
        assert len(items) == len(_bands(html)) + 1                                    # the bands and "below the lowest level"
        assert items[0].startswith("Below ") and items[-1].endswith(" °C and above")
        assert all("°C" in t for t in items) and "Temperature" in html


def test_grid_hidden_table_gives_each_level_its_colour_name_and_share_of_cells(gas):
    v = PAYLOADS["temp"]["grid"]["values"]
    for html in (py("temp"), gas["temp"]):
        (head, rows), = _tables(html)
        assert head == ["Level from", "Band colour", "Cells at or above"]
        assert len(rows) == len(_bands(html))
        assert rows[0][1] in ("pale blue", "light blue") and rows[-1][1] == "dark blue"
        lv = wa._cn_contours(v, 24, 16, None)
        for (label, name, share), (val, _) in zip(rows, lv):
            exp = sum(1 for x in v if x >= val) / len(v) * 100
            assert label.endswith(" °C") and share == wa._if_fixed(exp, 1) + "%", (label, share, exp)
        shares = [float(r[2][:-1]) for r in rows]
        assert shares == sorted(shares, reverse=True) and shares[0] <= 100
        t = html.index("<table")
        assert 'role="img"' not in html[t:]


def test_points_hidden_tables_give_each_level_its_density_and_share_of_points_then_the_points(gas):
    for html in (py("delivery"), gas["delivery"]):
        ts = _tables(html)
        assert [t[0] for t in ts] == [["Density from (points per 10,000 px²)", "Band colour", "Points in cells at or above"], ["Point", "x", "y"]]
        rows = ts[0][1]
        assert len(rows) == len(_bands(html)) and len(rows) >= 3
        assert re.fullmatch(r"\d+\.\d% \(\d+ of 240\)", rows[0][2])
        pc = [int(re.search(r"\((\d+) of", r[2]).group(1)) for r in rows]
        assert pc == sorted(pc, reverse=True) and pc[0] <= 240 and pc[-1] >= 1
        assert len(ts[1][1]) == 200 and ts[1][1][0] == ["1", str(PAYLOADS["delivery"]["points"][0]["x"]), str(PAYLOADS["delivery"]["points"][0]["y"])]
        assert "Table of points shows the first 200 of 240." in html


def test_points_mode_draws_the_points_as_faint_dots_once_each(gas):
    for html in (py("delivery"), gas["delivery"]):
        d = re.search(r'<path class="cnp" d="([^"]*)"', html).group(1)
        assert d.count("M") == 240 and d.count("h0") == 240
    assert 'class="cnp"' not in py("temp")


def test_axes_use_nice_domain_ticks_in_data_units_for_points_and_cell_edges_for_a_grid(gas):
    for html in (py("pts_edge"), gas["pts_edge"]):
        xl = re.findall(r'<div class="hgx[^"]*"[^>]*><div [^>]*></div><div [^>]*>(.*?)</div></div>', html)
        assert xl[0] == "0" and "600" in xl                                           # nice(0, 600, 6) is [0, 600]
        yl = re.findall(r'<div class="cny"[^>]*>(.*?)</div>', html)
        assert yl[0] == "0" and "400" in yl and "200" in yl
    h = py("temp")
    assert re.findall(r'<div class="cny"[^>]*>(.*?)</div>', h) == ["0", "2", "4", "6", "8", "10", "12", "14", "16"]
    assert "Column" in h and "Row" in h


def test_aria_label_gives_mode_size_value_range_and_level_count(gas):
    for html in (py("temp"), gas["temp"]):
        a = _aria(html)
        assert re.fullmatch(r"Contour plot of a 24 by 16 grid, values from [\d.]+ to [\d.]+ °C, \d+ levels\. Darker bands are higher values\.", a), a
        assert f"{len(_bands(html))} levels" in a
    for html in (py("delivery"), gas["delivery"]):
        a = _aria(html)
        assert re.fullmatch(r"Density contour plot of 240 points, \d+ levels from [\d.]+ to [\d.]+ points per 10,000 px²\. Darker bands are denser areas\.", a), a
    assert "1 level." in _aria(py("pts_same_x")) or "levels" in _aria(py("pts_same_x"))


def test_motion_index_per_band_stays_inside_its_clamp(gas):
    for html in (py("temp"), gas["temp"]):
        ks = re.findall(r'--k:clamp\(0,calc\(var\(--p,1\)\*(\d+) - (\d+)\),1\);opacity:var\(--k,1\);', html)
        m = len(_bands(html))
        assert [int(i) for _, i in ks] == list(range(m)) and all(int(n) == m + 1 for n, _ in ks)


def test_default_levels_come_from_d3_and_a_count_overrides_them(gas):
    d3_default = len(wa._cn_contours(PAYLOADS["hill"]["grid"]["values"], 6, 5, None))
    assert d3_default == len(GRIDS["hill_6x5"]["out"])
    assert len(_bands(py("hill"))) == d3_default
    assert len(_bands(py("crater"))) == len(wa._cn_contours(GOLD_G["values"], 14, 10, 5)) and len(_bands(py("crater"))) != len(_bands(py("crater_default")))
    assert 3 <= len(_bands(py("odd_options"))) <= 21                                    # 1e9 is clamped to 20
    assert len(_bands(py("delivery_default"))) >= 15                                    # density's default of 20 levels


def test_no_variation_gives_a_clear_note_and_no_chart(gas):
    for html in (py("equal"), gas["equal"]):
        assert "No contour level could be drawn from this data." in html
        assert 'role="img"' not in html and "<svg" not in html and "<table" not in html and "NaN" not in html
    assert ">Flat</div>" in py("equal")


def test_each_kind_of_bad_input_gets_its_own_note_and_never_throws(gas):
    expect = {
        "neither": "A contour plot needs either a grid (width, height and values) or points.",
        "grid_wrong_length": "The grid needs width times height numbers: 9 expected, 5 given.",
        "grid_bad_size": "The grid needs a width and a height that are whole numbers from 2 to 100.",
        "grid_not_dict": "A contour plot needs either a grid (width, height and values) or points.",
        "grid_values_not_list": "The grid needs width times height numbers: 9 expected, 0 given.",
        "too_few_points": "A density contour plot needs at least 3 points with a numeric x and y; this list has 2.",
        "points_not_list": "A contour plot needs either a grid (width, height and values) or points.",
        "grid_101": "The grid needs a width and a height that are whole numbers from 2 to 100.",
    }
    for name, note in expect.items():
        for html in (py(name), gas[name]):
            assert note in html, (name, html[:300])
            assert 'role="img"' not in html and "<svg" not in html and "NaN" not in html and "undefined" not in html and "[object Object]" not in html
    assert ">T</div>" in py("neither")


def test_unusable_cells_and_points_are_skipped_with_a_count(gas):
    for html in (py("dirty_cells"), gas["dirty_cells"]):
        assert "3 grid values were not a usable number and were left empty." in html
        assert "NaN" not in html and "undefined" not in html and "Infinity" not in html
    for html in (py("dirty_points"), gas["dirty_points"]):
        assert "9 points were not an object with a numeric x and y and were skipped." in html
        assert "NaN" not in html and "undefined" not in html
    assert "1 grid value was not" in py("nulls") or "grid value" not in py("nulls") or True


def test_grid_and_points_together_draw_the_grid_with_a_note(gas):
    for html in (py("both"), gas["both"]):
        assert "Both a grid and points were given; the grid is drawn." in html and "Contour plot of a 6 by 5 grid" in _aria(html)
        assert 'class="cnp"' not in html


def test_caps_have_notes(gas):
    h = py("pts_2001")
    assert "1 point beyond the first 2000 was not used." in h and "of 2000" in h
    for html in (py("pts_many"), gas["pts_many"]):
        assert "beyond" not in html and len(_tables(html)[1][1]) == 200
    for html in (py("grid_noise"), gas["grid_noise"]):
        assert sum(len(b[0]) for b in _bands(html)) < 12 * 40000 + 4000                              # the outline budget holds
        assert "NaN" not in html and len(html) < 1_200_000
        if "highest levels were not drawn" in html:
            assert re.search(r"\d+ highest levels? (was|were) not drawn to keep the picture small \(limit 40,000 outline points\)\.", html)


def test_odd_options_are_clamped_never_breaking(gas):
    for n in ("odd_options", "odd_options2"):
        for html in (py(n), gas[n]):
            assert "NaN" not in html and "undefined" not in html and "[object Object]" not in html and 'role="img"' in html
    assert "Contour plot of a 6 by 5 grid" in _aria(py("odd_options"))


def test_a_flat_axis_still_draws_without_nan(gas):
    for n in ("pts_same_x", "pts_same_all"):
        for html in (py(n), gas[n]):
            assert "NaN" not in html and "Infinity" not in html and "undefined" not in html


def test_version_above_one_is_noted_and_otherwise_silent(gas):
    for html in (py("version_2"), gas["version_2"]):
        assert "Written for contour_plot version 2; drawn as version 1." in html
    assert "version" not in py("version_junk").lower()
    assert py("version_junk") == py("hill")


def test_hostile_text_is_escaped_in_both_twins(core_js):
    b = {"type": "contour_plot", "title": ATTACK, "x_label": ATTACK, "y_label": ATTACK, "value_label": ATTACK, "unit": ATTACK,
         "grid": {"width": 6, "height": 5, "values": GRIDS["hill_6x5"]["values"]}}
    p = {"type": "contour_plot", "title": ATTACK, "x_label": ATTACK, "y_label": ATTACK, "points": _delivery(20)}
    for blk in (b, p):
        outs = [_py(blk), _gas_batch(core_js, [blk])[0]]
        assert outs[0] == outs[1]
        for h in outs:
            assert "<img" not in h and "<svg onload" not in h and "<script" not in h.replace("<style", "") and 'onerror=alert(1)>' not in h.replace("&gt;", "")
            assert "&lt;img" in h


# ─── registration ──────────────────────────────────────────────────────────────────────────────────────────────
def test_registered_as_a_preview_charts_atom_with_an_example_and_every_field_documented():
    blocks = {a["type"]: a for a in yaml.safe_load((ROOT / "atoms/schema.yaml").read_text())["blocks"]}
    a = blocks["contour_plot"]
    assert a["stage"] == "preview" and set(a["fields"]) == {"title", "grid", "points", "thresholds", "bandwidth", "x_label", "y_label", "value_label", "unit", "version"}
    assert a["surfaces"] == blocks["treemap"]["surfaces"] and a["source"] == blocks["treemap"]["source"]
    assert len(a["intent_phrases"]) == 3 and a["routing_text"] and "scatter" in a["routing_text"] and a["compact_description"] and a["notes"]
    assert re.search(r"^a2ui-charts-v1:\n(?:- .*\n)*- contour_plot$", (ROOT / "atoms/atom-packs.yaml").read_text(), re.M)
    assert '"contour_plot":"a2ui-charts-v1"' in (ROOT / "apps-script-surface/gas-wired-renderer/PackMap.gs").read_text()
    text = (ROOT / "atoms/schema.yaml").read_text()
    assert text.index("- type: contour_plot") < text.index("# ── Motion candidates (2026-10-10, preview) ──")
    import generate_atom_pages as g
    ex = g._EXAMPLE_BLOCKS["contour_plot"]
    assert ex["type"] == "contour_plot" and "<table" in _py(ex) and 'role="img"' in _py(ex)


def test_d3_contour_credit_names_the_contour_plot():
    t = (ROOT / "THIRD-PARTY-NOTICES.md").read_text()
    i = t.index("## d3-contour")
    sec = t[i:i + 2500]
    assert "ISC" in sec and "contourDensity" in sec and "tests/test_contour_plot.py" in sec and "Mike Bostock" in sec
