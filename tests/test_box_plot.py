"""box_plot (I37, owner decision D5): one horizontal box per group on a shared axis, ported by hand into BOTH renderers.

GOLDEN (tests/fixtures/box_plot_d3_golden.json, from box_plot_d3_golden_gen.mjs) holds what the REAL d3-array 3.2.4
gives: quartiles from quantileSorted (R-7), Tukey whiskers as in d3's box plot example, and the shared axis from
nice(min, max, 5) and ticks. Both twins must reproduce it exactly.
Also held here: Python/GAS HTML parity, the hidden table, the aria label, the motion index, malformed groups, the
`version` field, escaping and registration.
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
D = json.loads((ROOT / "tests/fixtures/box_plot_d3_golden.json").read_text())
CASES = {**D["golden"], **{f"fuzz{i}": c for i, c in enumerate(D["fuzz"])}}
KEYS = ("n", "min", "q1", "median", "q3", "max", "lo", "hi", "outliers")


def _bp(c, labels=None, **kw):
    b = {"type": "box_plot", "groups": [{"label": labels[k] if labels and k < len(labels) else "G%d" % (k + 1), "values": v} for k, v in enumerate(c["groups"])]}
    b.update(kw)
    return b


# ─── the layout against real d3 ────────────────────────────────────────────────
@pytest.mark.parametrize("name", list(CASES))
def test_python_stats_and_axis_match_d3_exactly(name):
    c = CASES[name]
    stats, domain, ticks = wa._bp_layout([[float(v) for v in g] for g in c["groups"]])
    assert [{k: s[k] for k in KEYS} for s in stats] == c["stats"]
    assert list(domain) == c["domain"] and ticks == c["ticks"]


def test_gas_stats_and_axis_match_d3_exactly(core_js):
    names = list(CASES)
    res = _node(core_js, "var G = " + json.dumps([CASES[n]["groups"] for n in names]) +
                "; console.log(JSON.stringify(G.map(function(g){ return _bpLayout(g); })));")
    for n, (stats, domain, ticks) in zip(names, res):
        assert [{k: s[k] for k in KEYS} for s in stats] == CASES[n]["stats"], n
        assert domain == CASES[n]["domain"] and ticks == CASES[n]["ticks"], n


def test_the_golden_set_covers_the_hard_cases():
    g = D["golden"]
    assert g["six_values"]["stats"][0]["q1"] == 2.25 and g["six_values"]["stats"][0]["outliers"] == [100]       # interpolated quartile, one outlier
    assert g["zero_iqr"]["stats"][0]["q1"] == g["zero_iqr"]["stats"][0]["q3"] == 5 and g["zero_iqr"]["stats"][0]["outliers"] == [1, 9]
    assert g["outliers_both_sides"]["stats"][0]["outliers"] == [-50, 60, 61]
    assert g["all_equal"]["domain"] == [7, 7] and g["all_equal"]["ticks"] == [7]
    assert len(g["twelve"]["groups"]) == 12


# ─── rendering ─────────────────────────────────────────────────────────────────
PAYLOADS = {
    "three": _bp(CASES["three"], ["Before", "During", "After"], title="Wait times by phase", x_label="Wait", unit="min"),
    "five": _bp(CASES["five_values"]),
    "six": _bp(CASES["six_values"], ["With one outlier"]),
    "all_equal": _bp(CASES["all_equal"]),
    "both_sides": _bp(CASES["outliers_both_sides"], unit="C"),
    "negatives": _bp(CASES["negatives"], ["North", "South"]),
    "tiny": _bp(CASES["tiny"], unit="V"),
    "big": _bp(CASES["big"], ["Population"]),
    "skewed": _bp(CASES["skewed"], ["Order value"], unit="EUR"),
    "twelve": _bp(CASES["twelve"], ["A rather long group label here"] + list("BCDEFGHIJKL")),
    "zero_iqr": _bp(CASES["zero_iqr"]),
    "malformed": {"type": "box_plot", "groups": [None, 7, "x", {"label": "Good", "values": [1, 2, 3, 4, 5, "6", None, 1e30]},
                                                 {"values": [2, 3, 4, 5, 6, 7]}, {"label": "Short", "values": [1, 2, 3]}, {"label": ["a"], "values": "1,2"}]},
    "no_groups": {"type": "box_plot", "title": "T"},
    "groups_not_a_list": {"type": "box_plot", "groups": {"label": "x", "values": [1, 2, 3, 4, 5]}},
    "all_short": {"type": "box_plot", "groups": [{"label": "a", "values": [1, 2]}]},
    "thirteen": {"type": "box_plot", "groups": [{"label": "G%d" % k, "values": [k, k + 1, k + 2, k + 3, k + 4]} for k in range(13)]},
    "many_outliers": {"type": "box_plot", "groups": [{"label": "Spiky", "values": [50] * 600 + list(range(1000, 1160))}]},
    "version_2": dict(_bp(CASES["five_values"]), version=2),
    "version_junk": dict(_bp(CASES["five_values"]), version=True),
}


@pytest.mark.parametrize("name", list(PAYLOADS))
def test_python_and_gas_emit_identical_html(name, core_js):
    assert _py(PAYLOADS[name]) == _gas_batch(core_js, [PAYLOADS[name]])[0]


def test_hidden_table_gives_the_five_numbers_per_group(core_js):
    for name in ("three", "six", "both_sides", "twelve"):
        b = PAYLOADS[name]
        stats, _, _ = wa._bp_layout([[float(v) for v in g["values"]] for g in b["groups"]])
        for html in (_py(b), _gas_batch(core_js, [b])[0]):
            head, rows = _table(html)
            assert head == ["Group", "Count", "Minimum", "Lower quartile", "Median", "Upper quartile", "Maximum", "Outliers"]
            assert [r[0] for r in rows] == [g["label"][:30] for g in b["groups"]]
            assert [int(r[1]) for r in rows] == [s["n"] for s in stats] and [int(r[7]) for r in rows] == [len(s["outliers"]) for s in stats]
            t = html.index("<table")
            assert 'role="img"' in html[:t] and 'role="img"' not in html[t:]
    head, rows = _table(_py(PAYLOADS["six"]))
    assert rows[0][2:7] == ["1", "2.25", "3.5", "4.75", "100"]
    assert all(c.endswith(" min") for r in _table(_py(PAYLOADS["three"]))[1] for c in r[2:7])


def test_stats_print_only_the_decimals_they_need_and_tiny_numbers_stay_readable():
    _, rows = _table(_py(PAYLOADS["tiny"]))
    assert all(len(c.split(" ")[0].split(".")[-1]) <= 7 for r in rows for c in r[2:7])
    _, rows = _table(_py(PAYLOADS["big"]))
    assert "," in rows[0][4] and "." not in rows[0][2]


def test_aria_label_names_every_group(core_js):
    for html in (_py(PAYLOADS["three"]), _gas_batch(core_js, [PAYLOADS["three"]])[0]):
        a = re.search(r'role="img" aria-label="([^"]*)"', html).group(1)
        assert re.match(r"Box plot of 3 groups on a shared axis from \S+ to \S+ min\. Before: median \S+ min, middle half \S+ to \S+ min, whiskers \S+ to \S+ min, \d+ outliers?; During: ", a), a


def test_boxes_whiskers_median_and_outliers_sit_where_the_stats_say(core_js):
    b = PAYLOADS["both_sides"]
    (s,), (x0, x1), _ = wa._bp_layout([[float(v) for v in g["values"]] for g in b["groups"]])
    pct = lambda v: round((v - x0) / (x1 - x0) * 100, 3)
    for html in (_py(b), _gas_batch(core_js, [b])[0]):
        assert "<script" not in html
        box = re.search(r'<div class="bpb" style="position:absolute;left:([\d.]+)%;width:([\d.]+)%;', html)
        assert abs(float(box.group(1)) - pct(s["q1"])) < 0.001 and abs(float(box.group(1)) + float(box.group(2)) - pct(s["q3"])) < 0.002
        assert abs(float(re.search(r'<div class="bpm" style="position:absolute;left:([\d.]+)%;', html).group(1)) - pct(s["median"])) < 0.001
        wh = re.search(r'<div class="bpw" style="position:absolute;left:([\d.]+)%;width:([\d.]+)%;', html)
        assert abs(float(wh.group(1)) - pct(s["lo"])) < 0.001 and abs(float(wh.group(1)) + float(wh.group(2)) - pct(s["hi"])) < 0.002
        dots = [float(x) for x in re.findall(r'<div class="bpo" style="position:absolute;left:([\d.]+)%;', html)]
        assert sorted(dots) == sorted(pct(o) for o in s["outliers"])


def test_zero_width_axis_draws_in_the_middle_without_nan(core_js):
    for h in (_py(PAYLOADS["all_equal"]), _gas_batch(core_js, [PAYLOADS["all_equal"]])[0]):
        assert "NaN" not in h and "Infinity" not in h and "undefined" not in h
        assert '<div class="bpm" style="position:absolute;left:50%;' in h


def test_motion_index_per_group_stays_inside_its_clamp(core_js):
    for html in (_py(PAYLOADS["twelve"]), _gas_batch(core_js, [PAYLOADS["twelve"]])[0]):
        ks = re.findall(r'<div class="bpg" style="position:absolute;inset:0;--k:clamp\(0,calc\(var\(--p,1\)\*(\d+) - (\d+)\),1\);', html)
        assert [int(i) for _, i in ks] == list(range(12)) and all(int(n) == 13 for n, _ in ks)


def test_malformed_groups_are_skipped_and_explained(core_js):
    for h in (_py(PAYLOADS["malformed"]), _gas_batch(core_js, [PAYLOADS["malformed"]])[0]):
        head, rows = _table(h)
        assert [r[0] for r in rows] == ["Good", "Group 5"] and [r[1] for r in rows] == ["5", "6"]
        assert "3 entries were not a usable number and were skipped." in h
        assert "5 groups had fewer than 5 usable numbers or were not a group and were left out." in h
        assert "NaN" not in h and "undefined" not in h and "[object Object]" not in h


def test_no_usable_group_gives_a_clear_note_and_no_chart():
    for k in ("no_groups", "groups_not_a_list", "all_short"):
        h = _py(PAYLOADS[k])
        assert "A box plot needs at least one group with 5 numbers." in h
        assert 'role="img"' not in h and "<table" not in h and "NaN" not in h
    assert ">T</div>" in _py(PAYLOADS["no_groups"])


def test_only_the_first_twelve_groups_are_read():
    h = _py(PAYLOADS["thirteen"])
    assert [r[0] for r in _table(h)[1]] == ["G%d" % k for k in range(12)]
    assert "1 group beyond the first 12 was not drawn." in h


def test_outliers_are_drawn_once_per_distinct_value_and_capped_with_a_note(core_js):
    for h in (_py(PAYLOADS["many_outliers"]), _gas_batch(core_js, [PAYLOADS["many_outliers"]])[0]):
        n = len(re.findall(r'<div class="bpo"', h))
        assert n == 100
        assert "Spiky has 160 distinct outliers; the 100 furthest from the median are drawn. The table counts them all." in h
    assert len(re.findall(r'<div class="bpo"', _py({"type": "box_plot", "groups": [{"values": [2] * 20 + [1, 9, 9, 9]}]}))) == 2


def test_version_above_one_is_noted_and_otherwise_silent(core_js):
    for h in (_py(PAYLOADS["version_2"]), _gas_batch(core_js, [PAYLOADS["version_2"]])[0]):
        assert "Written for box_plot version 2; drawn as version 1." in h
    assert "version" not in _py(PAYLOADS["version_junk"]).lower()
    assert _py(dict(PAYLOADS["five"], version=1)) == _py(PAYLOADS["five"])


def test_hostile_text_is_escaped_in_both_twins(core_js):
    b = {"type": "box_plot", "title": ATTACK, "x_label": ATTACK, "unit": ATTACK, "groups": [{"label": ATTACK, "values": [1, 2, 3, 4, 5]}]}
    for h in (_py(b), _gas_batch(core_js, [b])[0]):
        assert "<img" not in h and "<script" not in h.replace("<style", "") and 'onerror=alert(1)>' not in h.replace("&gt;", "")


# ─── registration ─────────────────────────────────────────────────────────────
def test_registered_as_a_stable_charts_atom_with_an_example_and_every_field_documented():
    blocks = {a["type"]: a for a in yaml.safe_load((ROOT / "atoms/schema.yaml").read_text())["blocks"]}
    a = blocks["box_plot"]
    assert a["stage"] == "stable" and set(a["fields"]) == {"title", "groups", "x_label", "unit", "version", "show_points"}
    assert a["surfaces"] == blocks["treemap"]["surfaces"] and a["source"] == blocks["treemap"]["source"]
    assert re.search(r"^a2ui-charts-v1:\n(?:- .*\n)*- box_plot$", (ROOT / "atoms/atom-packs.yaml").read_text(), re.M)
    assert '"box_plot":"a2ui-charts-v1"' in (ROOT / "apps-script-surface/gas-wired-renderer/PackMap.gs").read_text()
    import generate_atom_pages as g
    ex = g._EXAMPLE_BLOCKS["box_plot"]
    assert ex["type"] == "box_plot" and "<table" in _py(ex)


def test_d3_array_credit_names_the_box_plot():
    t = (ROOT / "THIRD-PARTY-NOTICES.md").read_text()
    assert "quantileSorted" in t and "tests/test_box_plot.py" in t
