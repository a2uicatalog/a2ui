"""parallel_coords (Plotly parcoords): N numeric dimensions (2 to 8) as vertical axes, each row a polyline across them.

GOLDEN (tests/fixtures/parallel_coords_d3_golden.json, from parallel_coords_d3_golden_gen.mjs) holds, from the REAL d3-scale 4.0.2 /
d3-shape 3.2.0 / d3-array 3.2.4: each axis's nice domain and ticks (scaleLinear), the tick and row y positions, the axis x positions
(scalePoint, padding 0.5) and each row's path (line().digits(2)). Both twins must reproduce it exactly (== on doubles; paths as strings).
Also held here: Python/GAS HTML parity, the hidden table, the aria label, colour never the only cue, malformed input, caps with notes,
the `version` field, escaping and registration. Static settled picture only: brushing (filtering by dragging on an axis) is not drawn.
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
D = json.loads((ROOT / "tests/fixtures/parallel_coords_d3_golden.json").read_text())
CASES = {**D["golden"], **{f"fuzz{i}": c for i, c in enumerate(D["fuzz"])}}


def _dims(c, labels=None):
    out = []
    for k, d in enumerate(c["dims"]):
        o = dict(d)
        o["label"] = labels[k] if labels and k < len(labels) else "Dim %d" % (k + 1)
        out.append(o)
    return out


def _pc(c, labels=None, **kw):
    b = {"type": "parallel_coords", "dimensions": _dims(c, labels)}
    b.update(kw)
    return b


KEYS = ("xs", "domains", "ticks", "tickY", "ys", "paths")


# ─── the layout against real d3 ────────────────────────────────────────────────
@pytest.mark.parametrize("name", list(CASES))
def test_python_layout_matches_d3_exactly(name):
    c = CASES[name]
    got = wa._pc_layout(c["dims"])
    for k in KEYS:
        assert got[k] == c[k], k


def test_gas_layout_matches_d3_exactly(core_js):
    names = list(CASES)
    res = _node(core_js, "var G = " + json.dumps([CASES[n]["dims"] for n in names]) + "; console.log(JSON.stringify(G.map(function(g){ return _pcLayout(g); })));")
    for n, got in zip(names, res):
        for k in KEYS:
            assert got[k] == CASES[n][k], (n, k)


def test_the_golden_set_covers_the_hard_cases():
    g = D["golden"]
    assert g["constant_axis"]["domains"][0] == [4, 4] and g["constant_axis"]["ticks"][0] == [4]
    assert g["reversed"]["ys"][0][0] < g["reversed"]["ys"][2][0]                          # reversed: bigger value sits lower
    assert g["explicit_range"]["domains"] == [[0, 10], [0, 1]]
    assert len(g["eight_dims"]["xs"]) == 8 and len(D["fuzz"]) == 24


# ─── rendering ─────────────────────────────────────────────────────────────────
CARS = {"type": "parallel_coords", "title": "Cars", "color_by": "Weight", "row_labels": ["Alpha", "Beta", "Gamma", "Delta"],
        "dimensions": [{"label": "Power", "values": [90, 120, 150, 200]}, {"label": "Weight", "values": [1100, 1300, 1500, 1900]},
                       {"label": "Range", "values": [620.5, 540, 480.25, 400], "reverse": True}, {"label": "Price", "values": [18, 22, 31, 48]}]}
PAYLOADS = {
    "cars": CARS,
    "plain": {k: v for k, v in CARS.items() if k != "color_by"},
    "iris": _pc(CASES["iris_like"], ["Sepal length", "Sepal width", "Petal length", "Petal width"], title="Measurements"),
    "two": _pc(CASES["two_dims"]),
    "eight": _pc(CASES["eight_dims"], ["Horsepower", "Displacement", "Cylinders", "Weight", "Acceleration", "Mileage", "Year", "Origin"]),
    "negatives": _pc(CASES["negatives"]),
    "constant": _pc(CASES["constant_axis"]),
    "one_row": _pc(CASES["one_row"]),
    "explicit": _pc(CASES["explicit_range"]),
    "huge": _pc(CASES["huge"]),
    "outside": {"type": "parallel_coords", "dimensions": [{"label": "A", "values": [-5, 5, 15], "min": 0, "max": 10}, {"label": "B", "values": [1, 2, 3]}]},
    "malformed": {"type": "parallel_coords", "row_labels": [7, None, "ok"], "color_by": "Nope",
                  "dimensions": [None, 5, {"label": "no values"}, {"label": "A", "values": [1, "2", 3, None, True, 1e30, 6]}, {"label": "B", "values": [2, 3, 4, 5, 6, 7]},
                                 {"values": [9, 8, 7, 6, 5, 4, 3], "min": "x", "max": []}]},
    "one_dim": {"type": "parallel_coords", "dimensions": [{"label": "Only", "values": [1, 2, 3]}]},
    "no_dims": {"type": "parallel_coords", "title": "T"},
    "dims_not_a_list": {"type": "parallel_coords", "dimensions": {"label": "x", "values": [1]}},
    "no_rows": {"type": "parallel_coords", "dimensions": [{"label": "A", "values": []}, {"label": "B", "values": []}]},
    "nine_dims": {"type": "parallel_coords", "dimensions": [{"label": "D%d" % k, "values": [k, k + 1, 3]} for k in range(9)]},
    "many_rows": {"type": "parallel_coords", "color_by": 1, "dimensions": [{"label": "X", "values": [k % 17 for k in range(230)]}, {"label": "Y", "values": [(k * 7) % 23 for k in range(230)]}]},
    "version_2": dict(_pc(CASES["two_dims"]), version=2),
    "version_junk": dict(_pc(CASES["two_dims"]), version="2"),
}


@pytest.mark.parametrize("name", list(PAYLOADS))
def test_python_and_gas_emit_identical_html(name, core_js):
    assert _py(PAYLOADS[name]) == _gas_batch(core_js, [PAYLOADS[name]])[0]


def test_hidden_table_has_every_value_and_sits_outside_the_image(core_js):
    for html in (_py(CARS), _gas_batch(core_js, [CARS])[0]):
        head, rows = _table(html)
        assert head == ["Row", "Power", "Weight", "Range", "Price"]
        assert rows == [["Alpha", "90", "1,100", "620.5", "18"], ["Beta", "120", "1,300", "540", "22"],
                        ["Gamma", "150", "1,500", "480.25", "31"], ["Delta", "200", "1,900", "400", "48"]]
        t = html.index("<table")
        assert 'role="img"' in html[:t] and 'role="img"' not in html[t:]


def test_aria_label_gives_the_shape_and_each_axis_range(core_js):
    for html in (_py(CARS), _gas_batch(core_js, [CARS])[0]):
        a = re.search(r'role="img" aria-label="([^"]*)"', html).group(1)
        assert a == ("Parallel coordinates of 4 rows across 4 dimensions. Power from 90 to 200. Weight from 1,100 to 1,900. "
                     "Range from 400 to 620.5, drawn upside down. Price from 18 to 48. Lines are coloured by Weight, light for low and dark for high.")


def test_one_path_per_row_each_with_the_golden_path(core_js):
    c = CASES["iris_like"]
    for html in (_py(PAYLOADS["iris"]), _gas_batch(core_js, [PAYLOADS["iris"]])[0]):
        assert re.findall(r'<path class="pcr"(?: data-cb="link")? d="([^"]*)"', html) == c["paths"]
        assert len(re.findall(r'<line class="pca"', html)) == 4


def test_colour_is_never_the_only_cue(core_js):
    for html in (_py(CARS), _gas_batch(core_js, [CARS])[0]):
        assert "color-mix(in srgb,var(--accent,#0369A1)" in html
        assert "Weight" in re.search(r'<div class="pcl"[^>]*>(.*?)</div>', html, re.S).group(0) and ">1,100<" in html and ">1,900<" in html     # legend with the range
        assert html.count('class="pcr"') == 4                                                                                              # and the row's own position on every axis
    h = _py(PAYLOADS["plain"])
    assert "color-mix" not in h and 'class="pcl"' not in h and "stroke:var(--accent,#0369A1)" in h


def test_unmatched_colour_by_is_noted_and_lines_are_one_colour():
    h = _py(PAYLOADS["malformed"])
    assert "color_by " in h and "matches no dimension" in h and "color-mix" not in h


def test_color_by_accepts_a_dimension_number():
    h = _py(PAYLOADS["many_rows"])
    assert "color-mix" in h and "coloured by Y" in h


def test_values_outside_an_explicit_range_sit_on_the_edge_with_a_note(core_js):
    for h in (_py(PAYLOADS["outside"]), _gas_batch(core_js, [PAYLOADS["outside"]])[0]):
        assert "2 values were outside their axis range and are drawn on its edge." in h
        assert [r[1] for r in _table(h)[1]] == ["-5", "5", "15"]                        # the table keeps the real numbers


def test_constant_axis_draws_in_the_middle_without_nan(core_js):
    for h in (_py(PAYLOADS["constant"]), _gas_batch(core_js, [PAYLOADS["constant"]])[0]):
        assert "NaN" not in h and "Infinity" not in h and "undefined" not in h


def test_malformed_input_is_left_out_and_explained(core_js):
    for h in (_py(PAYLOADS["malformed"]), _gas_batch(core_js, [PAYLOADS["malformed"]])[0]):
        head, rows = _table(h)
        assert head == ["Row", "A", "B", "Dimension 6"]
        assert [r[0] for r in rows] == ["7", "ok"]                                      # only rows 1 and 3 are complete: "2" is text, None, True, 1e30, and row 7 lacks B
        assert "3 dimensions were not a usable dimension and were left out." in h
        assert "5 rows had a missing or non-numeric value and were left out." in h
        for bad in ("NaN", "undefined", "[object Object]", "Infinity"):
            assert bad not in h


def test_fewer_than_two_usable_dimensions_gives_a_note_and_no_chart():
    for k in ("one_dim", "no_dims", "dims_not_a_list", "no_rows"):
        h = _py(PAYLOADS[k])
        assert "Parallel coordinates need at least 2 dimensions with numbers, and at least 1 complete row." in h
        assert 'role="img"' not in h and "<table" not in h and "NaN" not in h


def test_only_eight_dimensions_and_two_hundred_rows_are_drawn(core_js):
    for h in (_py(PAYLOADS["nine_dims"]), _gas_batch(core_js, [PAYLOADS["nine_dims"]])[0]):
        assert len(_table(h)[0]) == 9 and "1 dimension beyond the first 8 was not drawn." in h
    h = _py(PAYLOADS["many_rows"])
    assert len(_table(h)[1]) == 200 and h.count('class="pcr"') == 200 and "30 rows beyond the first 200 were not drawn." in h


def test_version_above_one_is_noted_and_otherwise_silent(core_js):
    for h in (_py(PAYLOADS["version_2"]), _gas_batch(core_js, [PAYLOADS["version_2"]])[0]):
        assert "Written for parallel_coords version 2; drawn as version 1." in h
    assert "version" not in _py(PAYLOADS["version_junk"]).lower()


def test_brushing_is_not_claimed():
    assert "Drag" not in _py(CARS) and "brush" not in _py(CARS).lower()


def test_hostile_text_is_escaped_in_both_twins(core_js):
    b = {"type": "parallel_coords", "title": ATTACK, "row_labels": [ATTACK, ATTACK], "color_by": ATTACK,
         "dimensions": [{"label": ATTACK, "values": [1, 2]}, {"label": ATTACK, "values": [3, 4]}]}
    for h in (_py(b), _gas_batch(core_js, [b])[0]):
        assert "<img" not in h and "<script" not in h.replace("<style", "") and 'onerror=alert(1)>' not in h.replace("&gt;", "")


def test_output_is_deterministic():
    assert _py(CARS) == _py(CARS)


# ─── registration ─────────────────────────────────────────────────────────────
def test_registered_as_a_preview_charts_atom_with_an_example_and_every_field_documented():
    blocks = {a["type"]: a for a in yaml.safe_load((ROOT / "atoms/schema.yaml").read_text())["blocks"]}
    a = blocks["parallel_coords"]
    assert a["stage"] == "stable" and set(a["fields"]) == {"title", "dimensions", "row_labels", "color_by", "version"}
    assert a["surfaces"] == blocks["treemap"]["surfaces"] and a["source"] == blocks["treemap"]["source"]
    assert len(a["intent_phrases"]) == 3 and "NOT" in a["routing_text"].upper() or "not for" in a["routing_text"].lower()
    assert re.search(r"^a2ui-charts-v1:\n(?:- .*\n)*- parallel_coords$", (ROOT / "atoms/atom-packs.yaml").read_text(), re.M)
    assert '"parallel_coords":"a2ui-charts-v1"' in (ROOT / "apps-script-surface/gas-wired-renderer/PackMap.gs").read_text()
    import generate_atom_pages as g
    ex = g._EXAMPLE_BLOCKS["parallel_coords"]
    assert ex["type"] == "parallel_coords" and "<table" in _py(ex)


def test_d3_credit_names_parallel_coords():
    t = (ROOT / "THIRD-PARTY-NOTICES.md").read_text()
    assert "tests/test_parallel_coords.py" in t


# ─── round 2 (review P1, P3) ───────────────────────────────────────────────────
def test_object_labels_never_print_object_object(core_js):
    """P1: a dimension or row label that is not text or a number falls back to the default name, in both twins."""
    b = {"type": "parallel_coords", "row_labels": [{"x": 1}, ["a"]],
         "dimensions": [{"label": {"o": 1}, "values": [1, 2]}, {"label": ["l"], "values": [3, 4]}, {"label": True, "values": [5, 6]}]}
    py, gas = _py(b), _gas_batch(core_js, [b])[0]
    assert py == gas
    assert "[object" not in py
    for want in ("Dimension 1", "Dimension 2", "Dimension 3", "Row 1", "Row 2"):
        assert want in py
    n = {"type": "parallel_coords", "row_labels": [7, 8],
         "dimensions": [{"label": 12, "values": [1, 2]}, {"label": "B", "values": [3, 4]}]}
    assert _py(n) == _gas_batch(core_js, [n])[0] and "12" in _py(n) and "<th" in _py(n)


def test_color_by_matches_a_label_longer_than_24_characters(core_js):
    """P3: color_by given the full label still finds the dimension whose heading is cut to 24 characters."""
    long = "Average fuel consumption per hundred km"
    b = {"type": "parallel_coords", "color_by": long,
         "dimensions": [{"label": long, "values": [1, 2, 3]}, {"label": "B", "values": [3, 4, 5]}]}
    for h in (_py(b), _gas_batch(core_js, [b])[0]):
        assert "matches no dimension" not in h
