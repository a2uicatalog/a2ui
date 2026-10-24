"""treemap `path` (deep treemap, I36) and the width-aware label rule (I31), Python and GAS against REAL d3-hierarchy 3.1.2.

tests/fixtures/treemap_d3_golden.json is written by tests/fixtures/treemap_d3_golden_gen.mjs (real d3-hierarchy:
hierarchy().sum().sort(by value descending), treemap().tile(treemapSquarify).size([900, 300]), paddingInner 2, and below the root
paddingOuter 3 plus a 20 high header). Both twins must reproduce every rectangle EXACTLY (== on doubles), because they run the same
float operations in the same order as d3.
"""
from __future__ import annotations

import copy
import json
import math
import re
from pathlib import Path

import pytest

from test_motion_atoms import _gas_batch, _node, _py, core_js  # noqa: F401  (core_js is a fixture)
from test_motion_atoms import wa  # noqa: E402

GOLDEN = json.loads((Path(__file__).parent / "fixtures" / "treemap_d3_golden.json").read_text())
CELL = r'<div(?: data-cb="tile")?(?: title="[^"]*")? style="position:absolute;left:([\d.]+)%;top:([\d.]+)%;width:([\d.]+)%;height:([\d.]+)%;box-sizing:border-box;border:1px solid transparent;'


def _items(rows):
    """[(path, name, value)] -> a treemap block."""
    return {"type": "treemap", "items": [({"path": p} if p else {}) | {"name": n, "value": v} | ({} if p else {"category": "Other"}) for p, n, v in rows]}


# ── the layout, against real d3 ─────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("name", list(GOLDEN))
def test_python_nested_layout_matches_d3_exactly(name):
    g = GOLDEN[name]
    got = wa._tm_nest_layout(g["spec"])
    assert [list(r) for r in got] == g["rows"], name


def test_gas_nested_layout_matches_d3_exactly(core_js):
    names = list(GOLDEN)
    res = _node(core_js, "var G = " + json.dumps([GOLDEN[n]["spec"] for n in names]) + "; console.log(JSON.stringify(G.map(function(s){ return _tmNestLayout(s); })));")
    for n, rows in zip(names, res):
        assert rows == GOLDEN[n]["rows"], n


# ── payloads ───────────────────────────────────────────────────────────────────────────────────────────────────
DEPTH2 = _items([(["Home"], "2024", 120), (["Home"], "2023", 70), (["Home"], "docs", 30), (["Work"], "code", 90), (["Work"], "notes", 60)])
DEPTH3 = _items([(["Home", "Photos"], "2024", 120), (["Home", "Photos"], "2023", 70), (["Home"], "docs", 30),
                 (["Work", "Code"], "app", 90), (["Work", "Code"], "lib", 45), (["Work", "Code"], "tests", 5), (["Work"], "notes", 20)])
DEPTH4 = _items([(["A", "B", "C"], "one", 50), (["A", "B", "C"], "two", 30), (["A", "B"], "three", 20), (["A"], "four", 10),
                 (["D", "E", "F"], "five", 40), (["D", "E", "F"], "six", 25), (["D", "E", "F"], "seven", 5), (["D", "E"], "eight", 15), (["D"], "nine", 12), ([], "ten", 8)])
MIXED = {"type": "treemap", "items": [{"path": ["Home", "Photos"], "name": "2024", "value": 120, "category": "ignored"},
                                     {"name": "loose", "value": 40, "category": "Misc"}, {"name": "bare", "value": 20},
                                     {"path": ["Misc"], "name": "joins", "value": 10}]}


def _rows(html):
    return re.findall(r'<tr><th scope="row">(.*?)</th>(.*?)</tr>', html)


def test_path_chart_nests_by_path_and_the_table_gains_the_path(core_js):
    for html in (_py(DEPTH3), _gas_batch(core_js, [DEPTH3])[0]):
        assert "<th scope=\"col\">Path</th>" in html
        assert "<td>Home / Photos</td>" in html and "<td>Work / Code</td>" in html and "<td>Work</td>" in html
        assert html.count('<th scope="row">') == 7
        assert 'role="img"' in html and "aria-label=" in html and "<script" not in html
        # group headers show the name and the total
        assert "Home 220" in html and "Photos 190" in html and "Code 140" in html


def test_category_is_ignored_when_a_path_exists_and_loose_items_group_by_category_or_other(core_js):
    for html in (_py(MIXED), _gas_batch(core_js, [MIXED])[0]):
        assert "ignored" not in html
        rows = dict((n, c) for n, c in _rows(html))
        assert "<td>Home / Photos</td>" in rows["2024"]
        assert "<td>Misc</td>" in rows["loose"] and "<td>Misc</td>" in rows["joins"]   # the category group and the path group merge
        assert "<td>Other</td>" in rows["bare"]


def test_python_and_gas_agree_byte_for_byte_on_path_charts(core_js):
    blocks = [DEPTH2, DEPTH3, DEPTH4, MIXED, dict(DEPTH3, version=2)]
    assert [_py(b) for b in blocks] == _gas_batch(core_js, blocks)


def test_depth_is_at_most_three_groups_and_each_group_name_at_most_twenty_chars(core_js):
    b = {"type": "treemap", "items": [{"path": ["A" * 30, "B", "C", "D", "E"], "name": "n", "value": 5}, {"path": ["A" * 30, "B"], "name": "m", "value": 3}]}
    for html in (_py(b), _gas_batch(core_js, [b])[0]):
        assert "A" * 21 not in html and "<td>" + "A" * 20 + " / B / C</td>" in html and "<td>" + "A" * 20 + " / B</td>" in html
        table = html.split("<table")[1]
        assert " D" not in table and "E<" not in table


def test_unusable_paths_do_not_switch_the_chart_to_path_mode(core_js):
    base = {"type": "treemap", "items": [{"category": "A", "name": "a", "value": 5}, {"category": "A", "name": "b", "value": 3}, {"category": "B", "name": "c", "value": 2}]}
    want = _py(base)
    for junk in ([], "x", 5, None, [""], ["  "], [1, None, {}], {"a": 1}, True):
        b = copy.deepcopy(base)
        b["items"][0]["path"] = junk
        b["items"][2]["path"] = junk
        assert _py(b) == want, junk
        assert _gas_batch(core_js, [b])[0] == want, junk


def test_twelve_item_cap_still_holds_with_paths(core_js):
    b = {"type": "treemap", "items": [{"path": ["G%d" % (i % 4)], "name": "n%d" % i, "value": i + 1} for i in range(20)]}
    for html in (_py(b), _gas_batch(core_js, [b])[0]):
        assert html.count('<th scope="row">') == 12


def test_version_note_and_malformed_input(core_js):
    for h in (_py(dict(DEPTH2, version=2)), _gas_batch(core_js, [dict(DEPTH2, version=2)])[0]):
        assert "Written for treemap version 2; drawn as version 1." in h
    assert "version" not in _py(dict(DEPTH2, version="2")).lower() and "version" not in _py(dict(DEPTH2, version=1)).lower()
    bad = [{"type": "treemap", "items": [{"path": ["a", 1, None], "name": 5, "value": "7"}, {"path": [["x"]], "name": None, "value": -1}, 3, None, {"path": ["<b>&"], "name": "<i>", "value": 1e400}]},
           {"type": "treemap", "items": [{"path": ["a"], "name": "x", "value": 0}]}, {"type": "treemap", "items": [{"path": ["a"] * 9, "name": "x", "value": 1e-300}]}]
    for h in _gas_batch(core_js, bad) + [_py(b) for b in bad]:
        assert not any(w in h for w in ("NaN", "undefined", "Infinity", "[object", "<script", "<b>"))
    assert [_py(b) for b in bad] == _gas_batch(core_js, bad)


# ── I31: a label is shown only where it fits, at the width the chart is actually drawn at ───────────────────────────
I31 = _items([]) | {"items": [{"category": c, "name": n, "value": v} for c, n, v in
                              [("Platform", "Compute", 4200), ("Platform", "Storage", 1800), ("Data", "Warehouse", 3100), ("Data", "Pipelines", 1200), ("Data", "BI", 700),
                               ("Product", "Design", 950), ("Product", "Research", 400), ("Product", "Analytics", 380), ("Ops", "Support", 820), ("Ops", "On-call", 300)]]}
K = 0.6 * 12.48


def _check_labels(html, items):
    """every cell label is either always visible or gated by a container rule at exactly the width it needs"""
    rules = {int(n): int(n) for n in re.findall(r"@container \(width<(\d+)px\)\{\.tmw\d+\{display:none\}\}", html)}
    cells = re.findall(CELL + r'[^"]*"(?: class="cb-fade")?>(.*?)</div>', html)
    assert len(cells) == len(items)
    seen = set()
    for (x, y, w, h, text), (n, v) in zip(cells, items):
        wu, hu = float(w) * 9, float(h) * 3
        label = "%s %s" % (n, v)
        need = (len(label) * K + 18) * 900 / wu if wu else 1e9
        if hu < 30 - 0.5:
            assert text == "", (label, hu)
            seen.add("short")
            continue
        m = re.fullmatch(r'<span class="tmw(\d+)">(.*)</span>', text)
        if m:
            assert label == m.group(2) and int(m.group(1)) in rules and abs(int(m.group(1)) - need) <= 1.01, (label, need, m.group(1))
            seen.add("gated")
        elif text:
            assert label in text and need <= 320.5, (label, need)
            seen.add("always")
        else:
            assert need > 1600 - 1, (label, need)           # a cell tall enough but too narrow for its label at any container up to 1600px
            seen.add("hidden")
    return seen


def test_i31_labels_follow_the_width_the_chart_is_drawn_at(core_js):
    items = [(i["name"], i["value"]) for i in I31["items"]]
    for html in (_py(I31), _gas_batch(core_js, [I31])[0]):
        assert "container-type:inline-size" in html
        seen = _check_labels(html, items)
        assert {"gated", "hidden"} <= seen, seen
        for n, v in items:                                     # a gated or hidden label still names itself on hover and in the table
            assert '<th scope="row">%s</th>' % n in html
        assert 'title="BI 700"' in html and 'title="On-call 300"' in html


def test_i31_pill_never_sits_over_the_first_items_label(core_js):
    for html in (_py(I31), _gas_batch(core_js, [I31])[0]):
        pills = re.findall(r'<div(?: class="tmw\d+")? style="position:absolute;left:([\d.]+)%;top:([\d.]+)%;max-width', html)
        assert pills
        cells = re.findall(CELL + r'[^"]*padding:(\d+)px 8px 6px[^"]*"(?: class="cb-fade")?>', html)
        for px, py_ in pills:
            below = [c for c in cells if abs(float(c[0]) - float(px)) < 1e-6 and abs(float(c[1]) - float(py_)) < 1e-6]
            assert below and all(int(c[4]) >= 24 for c in below), (px, py_, below)       # the lead cell's text starts below the 24px pill band


def test_payloads_without_a_usable_path_render_exactly_as_without_the_field(core_js):
    # every payload of tests/test_treemap_squarify.py, with the new optional fields at their defaults
    from test_treemap_squarify import GOLDEN as FLAT
    blocks = [{"type": "treemap", "items": g["items"]} for g in FLAT.values()] + [I31]
    withdef = [dict(b, version=1, items=[dict(i, path=[]) for i in b["items"]]) for b in blocks]
    assert [_py(b) for b in withdef] == [_py(b) for b in blocks]
    assert _gas_batch(core_js, withdef) == _gas_batch(core_js, blocks)
    assert [_py(b) for b in blocks] == _gas_batch(core_js, blocks)


def test_a_chart_whose_labels_all_fit_at_320px_carries_no_gating_markup(core_js):
    b = {"type": "treemap", "items": [{"category": "A", "name": "Alpha", "value": 50}, {"category": "A", "name": "Beta", "value": 50}]}
    for html in (_py(b), _gas_batch(core_js, [b])[0]):
        assert "tmw" not in html and "<style" not in html.replace(wa._CB_RULES, "") and "container-type" not in html and 'height:300px;">' in html


def test_schema_describes_the_squarified_chart_and_the_new_fields():
    import yaml
    d = {a["type"]: a for a in yaml.safe_load((Path(__file__).parent.parent / "atoms/schema.yaml").read_text())["blocks"]}["treemap"]
    assert set(d["fields"]) == {"title", "items", "version", "max_items"}
    assert "Columns" not in d["description"] and "squarif" in d["description"].lower()
    assert "path" in d["fields"]["items"] and "version" in d["fields"]["version"]
