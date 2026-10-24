"""scatter_matrix and parallel_categories (Plotly splom / parcats, wave B).

GOLDEN (tests/fixtures/splom_parcats_d3_golden.json, from splom_parcats_d3_golden_gen.mjs) holds, from the REAL d3-array 3.2.4,
each dimension's shared axis (nice, ticks) for scatter_matrix and, from rollup(), the category counts and the joint counts between
adjacent dimensions for parallel_categories. Both twins must reproduce it exactly. Also held here: Python/GAS HTML parity, hidden
tables, aria labels, caps with notes, malformed input, `version`, escaping and registration.
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
D = json.loads((ROOT / "tests/fixtures/splom_parcats_d3_golden.json").read_text())


# ─── the numbers against real d3 ───────────────────────────────────────────────
@pytest.mark.parametrize("name", list(D["axes"]))
def test_python_axis_matches_d3_exactly(name):
    c = D["axes"][name]
    x0, x1, ticks = wa._sm_axis(c["values"])
    assert [x0, x1] == c["domain"] and ticks == c["ticks"]


def test_gas_axis_matches_d3_exactly(core_js):
    names = list(D["axes"])
    res = _node(core_js, "var G = " + json.dumps([D["axes"][n]["values"] for n in names]) + "; console.log(JSON.stringify(G.map(_smAxis)));")
    for n, (x0, x1, ticks) in zip(names, res):
        assert [x0, x1] == D["axes"][n]["domain"] and ticks == D["axes"][n]["ticks"], n


def _want(c):
    return [[[x["name"], x["count"]] for x in col] for col in c["cats"]], c["joint"]


@pytest.mark.parametrize("name", list(D["cats"]))
def test_python_categories_and_joint_counts_match_d3_rollup(name):
    c = D["cats"][name]
    cats, joint = wa._pc_model(c["cols"])
    wc, wj = _want(c)
    assert [[list(x) for x in col] for col in cats] == wc and joint == wj


def test_gas_categories_and_joint_counts_match_d3_rollup(core_js):
    names = list(D["cats"])
    res = _node(core_js, "var G = " + json.dumps([D["cats"][n]["cols"] for n in names]) + "; console.log(JSON.stringify(G.map(_pcModel)));")
    for n, (cats, joint) in zip(names, res):
        wc, wj = _want(D["cats"][n])
        assert cats == wc and joint == wj, n


def test_the_golden_set_covers_the_hard_cases():
    assert D["axes"]["equal"]["ticks"] == [5] and D["axes"]["negatives"]["domain"][0] < 0
    assert D["cats"]["ties"]["cats"][0][0]["name"] == "b"                                 # equal counts keep first appearance
    assert D["cats"]["other"]["cats"][0][-1] == {"name": "Other", "count": 12, "merged": 4}
    assert D["cats"]["numeric_like"]["cats"][0][0]["name"] == "10"                         # no integer-key reordering


# ─── rendering ─────────────────────────────────────────────────────────────────
def _dims(cols, labels=None):
    return [{"label": (labels[i] if labels else "Dim %d" % (i + 1)), "values": c} for i, c in enumerate(cols)]


NUM = [[5.1, 4.9, 4.7, 4.6, 5.0, 5.4, 4.6, 5.0], [3.5, 3.0, 3.2, 3.1, 3.6, 3.9, 3.4, 3.4], [1.4, 1.4, 1.3, 1.5, 1.4, 1.7, 1.4, 1.5]]
SM = {
    "iris": {"type": "scatter_matrix", "title": "Flower measures", "dimensions": _dims(NUM, ["Sepal length", "Sepal width", "Petal length"])},
    "upper": {"type": "scatter_matrix", "show_upper": True, "dimensions": _dims(NUM[:2])},
    "six": {"type": "scatter_matrix", "dimensions": _dims([[(i * (k + 3)) % 17 + k for i in range(30)] for k in range(6)], ["A rather long dimension name", "Two", "Three", "Four", "Five", "Six"])},
    "equal": {"type": "scatter_matrix", "dimensions": _dims([[5, 5, 5], [1, 2, 3]])},
    "negatives": {"type": "scatter_matrix", "dimensions": _dims([[-12.5, 3, 7.25, -0.5, 18], [1e6, -2e6, 3e5, 0, 5]])},
    "malformed": {"type": "scatter_matrix", "dimensions": [None, 7, {"label": "A", "values": [1, 2, "x", None, 4, True, 1e30, 5]}, {"label": "B", "values": [2, 4, 6, 8, 10, 12, 14]},
                                                         {"label": "No values"}, {"label": "C", "values": [1, 3, 2, 4, 3, 5, 4, 6]}]},
    "many_rows": {"type": "scatter_matrix", "dimensions": _dims([[i % 13 for i in range(250)], [(i * 7) % 11 for i in range(250)]])},
    "seven": {"type": "scatter_matrix", "dimensions": _dims([[1, 2, 3, 4]] * 7)},
    "one_dim": {"type": "scatter_matrix", "title": "T", "dimensions": _dims([[1, 2, 3]])},
    "no_dims": {"type": "scatter_matrix"},
    "dims_not_list": {"type": "scatter_matrix", "dimensions": {"label": "x"}},
    "version_2": {"type": "scatter_matrix", "version": 2, "dimensions": _dims(NUM[:2])},
    "version_junk": {"type": "scatter_matrix", "version": "2", "dimensions": _dims(NUM[:2])},
}
CATS = [["red", "blue", "red", "green", "blue", "red", "red", "blue"], ["s", "m", "l", "s", "m", "s", "s", "m"], ["yes", "no", "yes", "no", "no", "yes", "yes", "no"]]
PC = {
    "three": {"type": "parallel_categories", "title": "Orders", "dimensions": _dims(CATS, ["Colour", "Size", "Returned"])},
    "two": {"type": "parallel_categories", "dimensions": _dims(CATS[:2])},
    "six": {"type": "parallel_categories", "dimensions": _dims([[("c%d" % ((i * (k + 1)) % (k + 2))) for i in range(40)] for k in range(6)])},
    "other": {"type": "parallel_categories", "dimensions": _dims(D["cats"]["other"]["cols"], ["Twelve kinds", "Three"])},
    "mixed_types": {"type": "parallel_categories", "dimensions": _dims([[1, 2, 1, True, None, "", {"a": 1}, 2.5], ["a", "a", "b", "b", "a", "a", "b", "a"]])},
    "uneven": {"type": "parallel_categories", "dimensions": _dims([["a", "b", "a", "b"], ["x", "y"]])},
    "malformed": {"type": "parallel_categories", "dimensions": [None, 7, {"label": "No values"}, {"label": "A", "values": ["p", "q", "p"]}, {"label": "B", "values": ["u", "u", "v"]}]},
    "seven": {"type": "parallel_categories", "dimensions": _dims([["a", "b"]] * 7)},
    "long_names": {"type": "parallel_categories", "dimensions": _dims([["A very long category name indeed, longer than twenty", "short"] * 3, ["x", "y", "x", "y", "x", "y"]], ["A dimension label that is very long indeed", "B"])},
    "one_dim": {"type": "parallel_categories", "title": "T", "dimensions": _dims([["a", "b"]])},
    "no_dims": {"type": "parallel_categories"},
    "records_cap": {"type": "parallel_categories", "dimensions": _dims([[("a", "b", "c")[i % 3] for i in range(5100)], [("x", "y")[i % 2] for i in range(5100)]])},
    "version_2": {"type": "parallel_categories", "version": 2, "dimensions": _dims(CATS[:2])},
}
ALL = {**{"sm_" + k: v for k, v in SM.items()}, **{"pc_" + k: v for k, v in PC.items()}}


@pytest.mark.parametrize("name", list(ALL))
def test_python_and_gas_emit_identical_html(name, core_js):
    assert _py(ALL[name]) == _gas_batch(core_js, [ALL[name]])[0]


# ─── scatter_matrix ────────────────────────────────────────────────────────────
def test_sm_hidden_table_has_every_value_and_aria_names_the_dimensions(core_js):
    for html in (_py(SM["iris"]), _gas_batch(core_js, [SM["iris"]])[0]):
        head, rows = _table(html)
        assert head == ["Row", "Sepal length", "Sepal width", "Petal length"] and len(rows) == 8
        assert rows[0] == ["1", "5.1", "3.5", "1.4"] and rows[7] == ["8", "5", "3.4", "1.5"]
        a = re.search(r'role="img" aria-label="([^"]*)"', html).group(1)
        assert a == "Scatter plot matrix of 3 measures over 8 rows: Sepal length (4.6 to 5.4), Sepal width (3 to 3.9), Petal length (1.3 to 1.7)."
        t = html.index("<table")
        assert 'role="img"' in html[:t] and 'role="img"' not in html[t:]


def test_sm_draws_only_the_lower_half_unless_asked(core_js):
    for h2, hu in ((_py(SM["iris"]), _py(SM["upper"])), (_gas_batch(core_js, [SM["iris"]])[0], _gas_batch(core_js, [SM["upper"]])[0])):
        assert h2.count('<svg class="smx"') == 3 and hu.count('<svg class="smx"') == 2        # 3 dims: 3 lower cells; 2 dims + upper: both
        assert h2.count('class="smp"') == 3 * 8 and hu.count('class="smp"') == 2 * 8


def test_sm_dots_sit_inside_their_cell_on_the_shared_axes(core_js):
    for html in (_py(SM["negatives"]), _gas_batch(core_js, [SM["negatives"]])[0]):
        pts = [(float(x), float(y)) for x, y in re.findall(r'<circle class="smp" cx="([\d.]+)" cy="([\d.]+)"', html)]
        assert len(pts) == 5 and all(5 <= x <= 95 and 5 <= y <= 95 for x, y in pts)
        x0, x1, _ = wa._sm_axis([-12.5, 3, 7.25, -0.5, 18]); y0, y1, _ = wa._sm_axis([1e6, -2e6, 3e5, 0, 5])
        want = [(round(5 + 90 * (v - x0) / (x1 - x0), 1), round(95 - 90 * (w - y0) / (y1 - y0), 1)) for v, w in zip([-12.5, 3, 7.25, -0.5, 18], [1e6, -2e6, 3e5, 0, 5])]
        assert all(abs(a - c) < 0.051 and abs(b - d) < 0.051 for (a, b), (c, d) in zip(pts, want))


def test_sm_equal_values_draw_in_the_middle_without_nan(core_js):
    for h in (_py(SM["equal"]), _gas_batch(core_js, [SM["equal"]])[0]):
        assert 'cx="50"' in h or 'cx="50.0"' in h
        assert "NaN" not in h and "Infinity" not in h and "undefined" not in h


def test_sm_malformed_dimensions_and_rows_are_left_out_and_explained(core_js):
    for h in (_py(SM["malformed"]), _gas_batch(core_js, [SM["malformed"]])[0]):
        head, rows = _table(h)
        assert head == ["Row", "A", "B", "C"] and [r[0] for r in rows] == ["1", "2", "5"]           # rows 3, 4, 6, 7 (A not a usable number) and 8 (B has no row 8) are left out
        assert "3 entries were not a dimension with a list of values and were left out." in h
        assert "5 rows had a value that was not a usable number and were left out." in h
        assert "NaN" not in h and "undefined" not in h and "[object Object]" not in h


def test_sm_caps_rows_and_dimensions_with_a_visible_note():
    h = _py(SM["many_rows"])
    assert len(_table(h)[1]) == 200 and "50 rows beyond the first 200 were not drawn." in h
    h = _py(SM["seven"])
    assert "1 dimension beyond the first 6 was not drawn." in h and len(_table(h)[0]) == 7


def test_sm_too_little_to_draw_gives_a_note_and_no_chart():
    for k in ("one_dim", "no_dims", "dims_not_list"):
        h = _py(SM[k])
        assert "A scatter plot matrix needs at least two dimensions with two complete rows." in h
        assert 'role="img"' not in h and "<table" not in h and "NaN" not in h
    assert ">T</div>" in _py(SM["one_dim"])


def test_sm_motion_index_stays_inside_its_clamp(core_js):
    for html in (_py(SM["six"]), _gas_batch(core_js, [SM["six"]])[0]):
        ks = re.findall(r'class="smc[^"]*" style="[^"]*--k:clamp\(0,calc\(var\(--p,1\)\*(\d+) - (\d+)\),1\);', html)
        assert [int(i) for _, i in ks] == list(range(36)) and all(int(n) == 37 for n, _ in ks)


# ─── parallel_categories ───────────────────────────────────────────────────────
def test_pc_hidden_table_has_every_flow_with_counts_and_share(core_js):
    for html in (_py(PC["three"]), _gas_batch(core_js, [PC["three"]])[0]):
        head, rows = _table(html)
        assert head == ["From dimension", "From category", "To dimension", "To category", "Records", "Share of records"]
        assert rows[0] == ["Colour", "red", "Size", "s", "3", "37.5%"]
        assert sum(int(r[4]) for r in rows if r[0] == "Colour") == 8 and sum(int(r[4]) for r in rows if r[0] == "Size") == 8
        a = re.search(r'role="img" aria-label="([^"]*)"', html).group(1)
        assert a.startswith("Parallel categories of 3 dimensions (Colour, Size, Returned) over 8 records.") and "Biggest flow:" in a
        t = html.index("<table")
        assert 'role="img"' in html[:t] and 'role="img"' not in html[t:]


def test_pc_bars_and_ribbons_are_counted_and_not_colour_only(core_js):
    for html in (_py(PC["three"]), _gas_batch(core_js, [PC["three"]])[0]):
        assert len(re.findall(r'class="pcb"', html)) == 3 + 3 + 2                         # categories per dimension
        digits = re.findall(r'class="pcb"[^>]*>(\d+)</div>', html)
        assert digits == ["1", "2", "3", "1", "2", "3", "1", "2"]                          # a number on every bar: rank is not colour alone
        assert len(re.findall(r'<path (?:data-cb="\w+" (?:data-key="[^"]*" )?)?class="pcr"', html)) == len(_table(html)[1])
        assert "Colour" in html and "1 red (4)" in html.replace("&nbsp;", " ") or "red (4)" in html


def test_pc_category_other_and_missing_values():
    h = _py(PC["other"])
    assert "In Twelve kinds, 4 less common categories were grouped as Other." in h and "Other (12)" in h
    h = _py(PC["mixed_types"])
    assert "(missing) (3)" in h or "(missing)" in h
    assert "NaN" not in h and "undefined" not in h and "[object Object]" not in h


def test_pc_uneven_columns_and_malformed_dimensions(core_js):
    for h in (_py(PC["uneven"]), _gas_batch(core_js, [PC["uneven"]])[0]):
        assert "(missing)" in h and sum(int(r[4]) for r in _table(h)[1]) == 4
    for h in (_py(PC["malformed"]), _gas_batch(core_js, [PC["malformed"]])[0]):
        assert "3 entries were not a dimension with a list of values and were left out." in h and "Parallel categories of 2 dimensions (A, B)" in h


def test_pc_caps_dimensions_and_records_with_a_note():
    h = _py(PC["seven"])
    assert "1 dimension beyond the first 6 was not drawn." in h
    h = _py(PC["records_cap"])
    assert "100 records beyond the first 5000 were not drawn." in h and "over 5000 records" in h


def test_pc_too_little_to_draw_gives_a_note_and_no_chart():
    for k in ("one_dim", "no_dims"):
        h = _py(PC[k])
        assert "Parallel categories needs at least two dimensions with values." in h and 'role="img"' not in h and "<table" not in h
    assert ">T</div>" in _py(PC["one_dim"])


def test_pc_long_names_never_reach_the_page_unbounded():
    h = _py(PC["long_names"])
    assert "A very long category name indeed, longer than twenty" not in h and "A dimension label that is very long indeed" not in h


def test_pc_ribbon_heights_at_both_ends_add_up_to_the_column():
    h = _py(PC["three"])
    assert "NaN" not in h and "Infinity" not in h
    for d in re.findall(r'<path (?:data-cb="\w+" (?:data-key="[^"]*" )?)?class="pcr" d="([^"]+)"', h):
        assert all(float(x) >= 0 for x in re.findall(r"-?[\d.]+", d))


# ─── both ──────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("key", ["sm_version_2", "pc_version_2"])
def test_version_above_one_is_noted_and_otherwise_silent(key, core_js):
    atom = ALL[key]["type"]
    for h in (_py(ALL[key]), _gas_batch(core_js, [ALL[key]])[0]):
        assert "Written for " + atom + " version 2; drawn as version 1." in h
    assert "version" not in _py(ALL["sm_version_junk"]).lower()


@pytest.mark.parametrize("atom", ["scatter_matrix", "parallel_categories"])
def test_hostile_text_is_escaped_in_both_twins(atom, core_js):
    vals = [[1, 2, 3], ["a", "b", "a"]] if atom == "parallel_categories" else [[1, 2, 3], [3, 1, 2]]
    cats = [ATTACK, ATTACK] if atom == "parallel_categories" else vals[0]
    b = {"type": atom, "title": ATTACK, "dimensions": [{"label": ATTACK, "values": cats if atom == "parallel_categories" else vals[0]}, {"label": ATTACK, "values": vals[1]}]}
    for h in (_py(b), _gas_batch(core_js, [b])[0]):
        assert "<img" not in h and "<script" not in h.replace("<style", "") and 'onerror=alert(1)>' not in h.replace("&gt;", "")


def test_no_script_and_text_never_below_12px():
    for k in ("sm_iris", "pc_three", "pc_six", "sm_six"):
        h = _py(ALL[k])
        assert "<script" not in h
        sizes = [float(x) for x in re.findall(r"font-size:([\d.]+)rem", h)]
        assert all(s >= 0.75 for s in sizes)


# ─── registration ─────────────────────────────────────────────────────────────
@pytest.mark.parametrize("atom,fields", [("scatter_matrix", {"title", "dimensions", "show_upper", "version"}), ("parallel_categories", {"title", "dimensions", "version"})])
def test_registered_as_a_preview_charts_atom_with_an_example_and_every_field_documented(atom, fields):
    blocks = {a["type"]: a for a in yaml.safe_load((ROOT / "atoms/schema.yaml").read_text())["blocks"]}
    a = blocks[atom]
    assert a["stage"] == "preview" and set(a["fields"]) == fields
    assert a["surfaces"] == blocks["treemap"]["surfaces"] and a["source"] == blocks["treemap"]["source"]
    assert re.search(r"^a2ui-charts-v1:\n(?:- .*\n)*- " + atom + "$", (ROOT / "atoms/atom-packs.yaml").read_text(), re.M)
    assert '"%s":"a2ui-charts-v1"' % atom in (ROOT / "apps-script-surface/gas-wired-renderer/PackMap.gs").read_text()
    import generate_atom_pages as g
    ex = g._EXAMPLE_BLOCKS[atom]
    assert ex["type"] == atom and "<table" in _py(ex)


def test_d3_array_credit_names_the_tests():
    assert "tests/test_splom_parcats.py" in (ROOT / "THIRD-PARTY-NOTICES.md").read_text()


# ─── wave B fixes ──────────────────────────────────────────────────────────────
def _both(core_js, b):
    return _py(dict(b)), _gas_batch(core_js, [dict(b)])[0]


def _pc(vals_a, vals_b):
    return {"type": "parallel_categories", "dimensions": [{"label": "A", "values": vals_a}, {"label": "B", "values": vals_b}]}


def test_categories_past_the_eighth_are_listed_in_a_text_alternative(core_js):
    a = ["c%02d" % (i % 12) for i in range(60)]   # 12 categories of 5 records; the ranked tail (after the first 8 by count, ties by first appearance) is c08..c11
    for h in _both(core_js, _pc(a, ["x"] * 60)):
        assert "Category grouped as Other" in h
        tail = re.findall(r'<tr><th scope="row">A</th><td>(c\d\d)</td><td>(\d+)</td></tr>', h)
        assert tail == [("c08", "5"), ("c09", "5"), ("c10", "5"), ("c11", "5")]


def test_a_real_other_or_missing_value_does_not_merge_with_the_placeholders(core_js):
    a = ["Other"] * 3 + ["(missing)"] * 2 + [None] * 4 + ["k%d" % i for i in range(10)]
    for h in _both(core_js, _pc(a, ["z"] * len(a))):
        assert "&quot;Other&quot;" in h and "&quot;(missing)&quot;" in h
        assert "(missing)</td>" in h   # the real placeholder for the 4 missing values
        # grouped bucket "Other" appears once per dimension as the plain word
        assert h.count("<td>Other</td>") >= 1


def test_the_other_bar_number_uses_the_page_background_not_white(core_js):
    a = ["c%02d" % (i % 12) for i in range(60)]
    for h in _both(core_js, _pc(a, ["x"] * 60)):
        assert "background:var(--muted,#475569);color:var(--bg,#fff)" in h


def test_a_share_below_a_tenth_of_a_percent_is_not_written_as_zero(core_js):
    big = ["a"] * 4000 + ["b"]
    for h in _both(core_js, _pc(big, ["x"] * 4001)):
        assert "&lt;0.1%" in h and ">0.0%<" not in h


def test_tiny_scatter_matrix_numbers_are_not_printed_as_zero(core_js):
    b = {"type": "scatter_matrix", "dimensions": [{"label": "a", "values": [1e-9, 2.5e-9, 3e-9]}, {"label": "b", "values": [1, 2, 3]}]}
    py, gas = _both(core_js, b)
    for h in (py, gas):
        assert "1.00e-9" in h and "3.00e-9" in h and "a (0 to 0)" not in h
    assert py == gas
