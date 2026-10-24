"""polar_chart (Plotly scatterpolar / scatterpolargl): points and lines by angle and radius, or a radar.

GOLDEN (tests/fixtures/polar_chart_d3_golden.json, from polar_chart_d3_golden_gen.mjs) holds the radial axis (d3 nice/ticks), each radius
(d3 scaleLinear), each angle (clockwise from the top, d3 lineRadial's convention) and the open and closed lineRadial() path strings (d3-path's
3 digits, defined() gaps) from the REAL d3-array 3.2.4, d3-scale 4.0.2 and d3-shape 3.2.0. Both twins must reproduce it exactly (==).
Also held here: Python/GAS HTML parity, the hidden table, the aria label, series told apart without colour, categories, the point cap and
its note, malformed input, the `version` field, escaping and registration.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

from test_histogram import ATTACK, _table
from test_motion_atoms import _gas_batch, _node, _py, core_js  # noqa: F401  (core_js is a fixture)
from test_motion_atoms import wa  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
D = json.loads((ROOT / "tests/fixtures/polar_chart_d3_golden.json").read_text())
CASES = {**D["golden"], **{f"fuzz{i}": c for i, c in enumerate(D["fuzz"])}}


def _args(c):
    return c["r"], c["theta"], c["rotation"], c["direction"], (tuple(c["range"]) if "range" in c else None), 4


# ─── the maths against real d3 ────────────────────────────────────────────────
@pytest.mark.parametrize("name", list(CASES))
def test_python_layout_and_paths_match_d3_exactly(name):
    c = CASES[name]
    lo, hi, tk, ang, rad, ok = wa._pl_layout(*_args(c))
    assert (lo, hi, tk, ang, rad) == (c["lo"], c["hi"], c["ticks"], c["angles"], c["radii"])
    assert wa._pl_path(ang, rad, ok, False) == c["open"] and wa._pl_path(ang, rad, ok, True) == c["closed"]


def test_gas_layout_and_paths_match_d3_exactly(core_js):
    names = list(CASES)
    res = _node(core_js, "var G = " + json.dumps([_args(CASES[n]) for n in names]) + ";" +
                "console.log(JSON.stringify(G.map(function(g){ var L = _plLayout(g[0], g[1], g[2], g[3], g[4], g[5]);"
                " return [L[0], L[1], L[2], L[3], L[4], _plPath(L[3], L[4], L[5], false), _plPath(L[3], L[4], L[5], true)]; })));")
    for n, (lo, hi, tk, ang, rad, op, cl) in zip(names, res):
        c = CASES[n]
        assert (lo, hi, tk, ang, rad, op, cl) == (c["lo"], c["hi"], c["ticks"], c["angles"], c["radii"], c["open"], c["closed"]), n


def test_the_golden_set_covers_the_hard_cases():
    g = D["golden"]
    assert g["negative_r"]["lo"] < 0 < g["negative_r"]["hi"]
    assert g["gaps"]["open"].count("M") == 3 and "M8,0Z" in g["gaps"]["open"]          # a lone point is a Z, a break starts a new M
    assert g["single"]["open"].endswith("Z") and g["rotated"]["angles"][0] != g["radar6"]["angles"][0]
    assert any("range" in c for c in D["fuzz"])


# ─── rendering ────────────────────────────────────────────────────────────────
def _ser(c, label="Series", **kw):
    s = {"label": label, "r": c["r"], "theta": c["theta"]}
    s.update(kw)
    return s


RADAR_CATS = ["Speed", "Power", "Range", "Comfort", "Safety", "Cost"]
PAYLOADS = {
    "radar": {"type": "polar_chart", "title": "Two models", "unit": "pts", "series": [
        {"label": "Model A", "theta": RADAR_CATS, "r": [4, 3, 5, 2, 4.5, 3.5], "fill": "toself"},
        {"label": "Model B", "theta": RADAR_CATS, "r": [3, 4, 2, 5, 3, 4]}]},
    "wind": {"type": "polar_chart", "title": "Wind", "unit": "m/s", "series": [_ser(CASES["numeric_ccw"], "Gusts")]},
    "negative": {"type": "polar_chart", "series": [_ser(CASES["negative_r"], "Delta")]},
    "range": {"type": "polar_chart", "r_range": [0, 1], "series": [_ser(CASES["explicit_range"], "Share", fill="toself")]},
    "gaps": {"type": "polar_chart", "r_range": [0, 5], "rotation": 45, "direction": "clockwise", "series": [_ser(CASES["gaps"], "Gappy")]},
    "single": {"type": "polar_chart", "series": [_ser(CASES["single"], "One")]},
    "big": {"type": "polar_chart", "series": [_ser(CASES["big"], "Large", mode="markers")], "theta_step": 90, "r_ticks": 3},
    "six": {"type": "polar_chart", "series": [{"label": "S%d" % k, "theta": [0, 90, 180, 270], "r": [1 + k, 2, 3, 2 + k]} for k in range(6)]},
    "long_labels": {"type": "polar_chart", "categories": ["A very long category name that goes on", "Second", "Third one here", "Fourth"],
                    "series": [{"label": "L", "theta": ["Second", "Fourth", "Third one here"], "r": [2, 4, 3]}]},
    "twelve": {"type": "polar_chart", "series": [{"label": "Months", "theta": ["M%d" % k for k in range(12)], "r": [k % 5 + 1 for k in range(12)]}]},
    "malformed": {"type": "polar_chart", "r_range": "x", "series": [None, 7, {"label": "Good", "theta": [0, 90, "x", True, None, 1e30, 45], "r": [1, 2, 3, 4, 5, 6, "7", 8]},
                                                                  {"theta": [1], "r": []}, {"label": 5, "r": "no", "theta": 3}]},
    "no_series": {"type": "polar_chart", "title": "T"},
    "series_not_a_list": {"type": "polar_chart", "series": {"r": [1], "theta": [1]}},
    "none_usable": {"type": "polar_chart", "series": [{"r": [None], "theta": [1]}]},
    "zeros": {"type": "polar_chart", "series": [{"label": "Z", "r": [0, 0], "theta": [0, 90]}]},
}


@pytest.mark.parametrize("name", list(PAYLOADS))
def test_python_and_gas_emit_identical_html(name, core_js):
    assert _py(PAYLOADS[name]) == _gas_batch(core_js, [PAYLOADS[name]])[0]


def test_nothing_prints_nan_undefined_or_an_object(core_js):
    for n, b in PAYLOADS.items():
        h = _py(b)
        assert not re.search(r"NaN|undefined|Infinity|\[object|None\b", re.sub(r"<style.*?</style>", "", h)), n


def test_hidden_table_gives_every_drawn_point(core_js):
    for h in (_py(PAYLOADS["radar"]), _gas_batch(core_js, [PAYLOADS["radar"]])[0]):
        head, rows = _table(h)
        assert head == ["Series", "Category", "Radius", "Status"] and len(rows) == 12
        assert rows[0] == ["Model A", "Speed", "4 pts", "drawn"] and rows[11] == ["Model B", "Cost", "4 pts", "drawn"]
    head, rows = _table(_py(dict(PAYLOADS["wind"], unit="m/s")))
    assert head == ["Series", "Angle (degrees)", "Radius", "Status"] and rows[2] == ["Gusts", "90", "3 m/s", "drawn"]


def test_aria_label_gives_the_range_and_each_series(core_js):
    for h in (_py(PAYLOADS["radar"]), _gas_batch(core_js, [PAYLOADS["radar"]])[0]):
        a = re.search(r'role="img" aria-label="([^"]*)"', h).group(1)
        assert "2 series" in a and "radius from 0 to 5 pts" in a and "6 categories: Speed, Power" in a and "Model B: 6 points, radius from 2 to 5 pts" in a
    assert "angles in degrees" in _py(PAYLOADS["wind"])


def test_series_differ_by_dash_and_marker_not_only_colour():
    h = _py(PAYLOADS["six"])
    assert len(set(re.findall(r'stroke-dasharray="([^"]*)"', h))) >= 5
    assert all(s in h for s in ("<circle", "<rect", "L", "Z"))
    legend = h[h.index('class="pcl"'):]
    assert legend.count('class="pcl"') == 6 and "stroke-dasharray" in legend


def test_categories_start_at_the_top_and_run_clockwise_numbers_run_counterclockwise():
    assert D["golden"]["radar6"]["rotation"] == 90 and D["golden"]["radar6"]["direction"] == -1
    h = _py(PAYLOADS["radar"])
    assert 'class="pca" style="position:absolute;left:50%;top:' in h              # the first category sits at twelve o'clock
    h2 = _py(PAYLOADS["wind"])
    assert 'class="pca" style="position:absolute;left:' in h2 and ">0°<" in h2 and ">90°<" in h2


def test_fill_toself_adds_a_closed_shaded_path():
    h = _py(PAYLOADS["radar"])
    assert h.count('fill-opacity="0.16"') == 1 and 'stroke="none"' in h


def test_points_outside_the_range_are_not_drawn_and_counted():
    h = _py(PAYLOADS["range"])
    assert "1 point is outside the radial range and not drawn." in h
    assert len(_table(h)[1]) == 5                                       # the table lists every point and says which are not drawn
    assert [r[-1] for r in _table(h)[1]].count("outside the radial range, not drawn") == 1


def test_points_beyond_the_cap_are_thinned_deterministically_with_a_note(core_js):
    big = {"type": "polar_chart", "series": [{"label": "Dense", "theta": [i * 0.36 for i in range(5000)], "r": [1 + (i % 7) for i in range(5000)]}]}
    h = _py(big)
    assert "5000 points were thinned to 2000 evenly spaced points" in h and len(_table(h)[1]) == 2000
    assert _table(h)[1][0][1] == "0" and _table(h)[1][-1][1] == "1,799.64"                                  # first and last are kept
    assert h == _py(big) == _gas_batch(core_js, [big])[0]
    many = {"type": "polar_chart", "series": [{"label": "S%d" % k, "theta": list(range(1000)), "r": [1] * 1000} for k in range(4)]}
    assert "limit is 2000 points in all" in _py(many) and len(_table(_py(many))[1]) == 4 * 500


def test_only_the_first_six_series_and_twelve_categories_are_read():
    b = {"type": "polar_chart", "series": [{"label": "S%d" % k, "theta": [0], "r": [1]} for k in range(8)]}
    h = _py(b)
    assert "2 series beyond the first 6 were not drawn." in h and len(_table(h)[1]) == 6
    b = {"type": "polar_chart", "series": [{"theta": ["c%d" % k for k in range(14)], "r": [1] * 14}]}
    assert "2 points were in a category beyond the first 12" in _py(b)


def test_malformed_input_is_skipped_and_explained(core_js):
    h = _py(PAYLOADS["malformed"])
    assert "2 series were not a series and were left out." in h and "r_range needs two numbers" in h and "skipped." in h
    assert len(_table(h)[1]) >= 2
    for n in ("no_series", "series_not_a_list", "none_usable"):
        assert "needs at least one series" in _py(PAYLOADS[n]) and "<svg" not in _py(PAYLOADS[n])


def test_a_chart_of_zeros_still_draws_a_scale():
    h = _py(PAYLOADS["zeros"])
    assert "radius from 0 to 1" in h


def test_version_above_one_is_noted_and_otherwise_silent(core_js):
    b = dict(PAYLOADS["wind"], version=2)
    for h in (_py(b), _gas_batch(core_js, [b])[0]):
        assert "Written for polar_chart version 2; drawn as version 1." in h
    assert "Written for" not in _py(dict(PAYLOADS["wind"], version=1)) and _py(dict(PAYLOADS["wind"], version=1)) == _py(PAYLOADS["wind"])


def test_motion_index_per_series_stays_inside_its_clamp():
    h = _py(PAYLOADS["radar"])
    assert "--k:clamp(0,calc(var(--p,1)*3 - 0),1);" in h and "--k:clamp(0,calc(var(--p,1)*3 - 1),1);" in h


def test_hostile_text_is_escaped_in_both_twins(core_js):
    b = {"type": "polar_chart", "title": ATTACK, "unit": ATTACK, "categories": [ATTACK], "series": [{"label": ATTACK, "theta": [ATTACK, "b"], "r": [1, 2]}]}
    for h in (_py(b), _gas_batch(core_js, [b])[0]):
        assert "<img" not in h and "<script" not in h.replace("<style", "") and 'onerror=alert(1)>' not in h.replace("&gt;", "")


# ─── registration ─────────────────────────────────────────────────────────────
def test_registered_as_a_preview_charts_atom_with_an_example_and_every_field_documented():
    blocks = {a["type"]: a for a in yaml.safe_load((ROOT / "atoms/schema.yaml").read_text())["blocks"]}
    a = blocks["polar_chart"]
    assert a["stage"] == "preview" and set(a["fields"]) == {"title", "series", "categories", "r_range", "r_ticks", "theta_step", "direction", "rotation", "unit", "version"}
    assert a["surfaces"] == blocks["treemap"]["surfaces"] and a["source"] == blocks["treemap"]["source"]
    assert re.search(r"^a2ui-charts-v1:\n(?:- .*\n)*- polar_chart$", (ROOT / "atoms/atom-packs.yaml").read_text(), re.M)
    assert '"polar_chart":"a2ui-charts-v1"' in (ROOT / "apps-script-surface/gas-wired-renderer/PackMap.gs").read_text()
    import generate_atom_pages as g
    ex = g._EXAMPLE_BLOCKS["polar_chart"]
    assert ex["type"] == "polar_chart" and "<table" in _py(ex)


def test_d3_credit_names_the_polar_chart():
    assert "tests/test_polar_chart.py" in (ROOT / "THIRD-PARTY-NOTICES.md").read_text()


def test_points_past_the_read_cap_are_counted_in_a_note_never_dropped_silently(core_js):
    b = {"type": "polar_chart", "series": [{"label": "Huge", "theta": [i % 360 for i in range(6200)], "r": [1 + i % 3 for i in range(6200)]}]}
    h = _py(b)
    assert 'Series &quot;Huge&quot;: 6200 points were given; only the first 5000 were read and the rest were not drawn.' in h
    assert "5000 points were thinned to 2000" in h                      # the thinning note counts what was read
    assert h == _gas_batch(core_js, [b])[0]


def test_explicit_clockwise_starts_due_north_like_plotly_and_counterclockwise_due_east(core_js):
    cw = {"type": "polar_chart", "direction": "clockwise", "r_range": [0, 1], "series": [{"label": "w", "theta": [0, 90], "r": [1, 1]}]}
    ccw = dict(cw, direction="counterclockwise")
    for b in (cw, ccw):
        assert _py(b) == _gas_batch(core_js, [b])[0]
    # theta 0 with clockwise is at the top (x 0, y -40); with counterclockwise it is at the right (x 40, y 0)
    assert "M0,-40" in _py(cw) and "M40,0" in _py(ccw)


def test_series_groups_carry_unique_keys(core_js):
    b = {"type": "polar_chart", "series": [{"label": "A", "theta": [0], "r": [1]}, {"label": "A", "theta": [0], "r": [2]}, {"theta": [0], "r": [3]}]}
    h = wa._RENDERERS["polar_chart"](b)
    assert re.findall(r'<g data-cb="node" data-key="([^"]*)"', h) == ["A", "A~2", "Series 3"]
