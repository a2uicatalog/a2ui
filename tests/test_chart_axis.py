"""Shared chart-axis helper (plotly core-bar): d3-format 3.1.0 subset and d3-scale 4.0.2 scaleLog / linear ticks, ported by hand into
BOTH renderers.

GOLDEN (tests/fixtures/chart_axis_d3_golden.json) was produced by the REAL d3-format / d3-scale (chart_axis_d3_golden_gen.mjs). Both
twins must reproduce every string and every tick EXACTLY (== on the doubles, not within a tolerance).
Specifiers d3 itself rejects, and the types b c o p r x X that are outside the ported subset, are rejected (None) and never answered.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from test_motion_atoms import _node, core_js, wa  # noqa: F401

ROOT = Path(__file__).resolve().parent.parent
D = json.loads((ROOT / "tests/fixtures/chart_axis_d3_golden.json").read_text())
VALS = [-0.0 if v == "-0" else v for v in D["vals"]]
SUPPORTED = {s: o for s, o in D["formats"].items() if o[0] is not None and s not in ("x",)}
REJECTED = [s for s, o in D["formats"].items() if o[0] is None] + ["x", "b", "p", "r", "c", "o", "X"]


def test_the_golden_has_the_cases_that_make_a_hand_port_drift():
    f = D["formats"]
    assert f["s"][VALS.index(0.5)] == "500.000m" and f["~s"][VALS.index(1e6)] == "1M"        # SI prefixes, trimmed
    assert f["$,.2f"][VALS.index(-1)] == "−$1.00"                                      # d3 3.x minus sign
    assert f[",.0f"][VALS.index(1234.5678)] == "1,235" and f[".1f"][VALS.index(0.05 if 0.05 in VALS else 0.5)]
    assert f["010,.1f"][VALS.index(1234.5678)] == "0,001,234.6"                             # comma + zero fill groups the padding
    assert f[".0%"][VALS.index(0.5)] == "50%" and f["(.1f"][VALS.index(-1)] == "(1.0)"
    assert any(o[0] is None for o in f.values())                                            # a specifier d3 throws on


@pytest.mark.parametrize("spec", list(SUPPORTED))
def test_python_format_matches_d3_exactly(spec):
    got = [wa._ax_format(spec, v) for v in VALS]
    assert got == SUPPORTED[spec], [(v, g, w) for v, g, w in zip(VALS, got, SUPPORTED[spec]) if g != w]


def test_gas_format_matches_d3_exactly(core_js):
    specs = list(SUPPORTED)
    res = _node(core_js, "var S = " + json.dumps(specs) + ", V = " + json.dumps(VALS) + ".map(function(v){ return v === '-0' ? -0 : v; });"
                " console.log(JSON.stringify(S.map(function(s){ return V.map(function(v){ return _axFormat(s, v); }); })));")
    for s, got in zip(specs, res):
        assert got == SUPPORTED[s], (s, [(v, g, w) for v, g, w in zip(VALS, got, SUPPORTED[s]) if g != w])


@pytest.mark.parametrize("spec", REJECTED + ["", ".2f%", "\n.2f", "x" * 40, 5, None])
def test_unsupported_or_hostile_specifiers_are_rejected_not_answered(spec, core_js):
    if spec in ("",):
        assert wa._ax_parse(spec) is not None        # the empty specifier is valid d3: the default format
        return
    assert wa._ax_parse(spec) is None


def test_gas_rejects_the_same_specifiers(core_js):
    specs = REJECTED + ["", ".2f%", "\n.2f", "x" * 40, 5, None]
    res = _node(core_js, "console.log(JSON.stringify(" + json.dumps(specs) + ".map(function(s){ return _axParse(s) === null; })));")
    assert res == [wa._ax_parse(s) is None for s in specs]


def test_log_ticks_and_nice_match_d3_exactly_in_both_twins(core_js):
    cases = D["logTicks"]
    for c in cases:
        a, b = c["domain"]
        assert wa._ax_log_ticks(a, b, c["count"]) == c["ticks"], c
        assert list(wa._ax_log_nice(a, b)) == c["nice"], c
    res = _node(core_js, "var C = " + json.dumps([[c["domain"], c["count"]] for c in cases]) +
                "; console.log(JSON.stringify(C.map(function(c){ return [_axLogTicks(c[0][0], c[0][1], c[1]), _axLogNice(c[0][0], c[0][1])]; })));")
    for c, (t, n) in zip(cases, res):
        assert t == c["ticks"] and n == c["nice"], c


def test_linear_nice_and_ticks_match_d3_in_both_twins(core_js):
    cases = D["linear"]
    for c in cases:
        a, b = c["domain"]
        assert wa._hg_ticks(a, b, c["count"]) == c["ticks"], c
        n0, n1 = wa._hg_nice(a, b, c["count"])
        assert [n0, n1] == c["nice"] and wa._hg_ticks(n0, n1, c["count"]) == c["niceTicks"], c
    res = _node(core_js, "var C = " + json.dumps([[c["domain"], c["count"]] for c in cases]) +
                "; console.log(JSON.stringify(C.map(function(c){ var n = _hgNice(c[0][0], c[0][1], c[1]); return [_hgTicks(c[0][0], c[0][1], c[1]), n, _hgTicks(n[0], n[1], c[1])]; })));")
    for c, (t, n, nt) in zip(cases, res):
        assert t == c["ticks"] and n == c["nice"] and nt == c["niceTicks"], c


def test_the_golden_covers_the_hard_log_cases():
    by = {(tuple(c["domain"]), c["count"]): c for c in D["logTicks"]}
    assert by[((1, 1000), 10)]["ticks"][:4] == [1, 2, 3, 4]       # fewer decades than ticks asked: 1..9 of each decade
    assert by[((1, 1000), 2)]["ticks"] == [1, 100]                # too few ticks: the linear ticks of the exponents
    assert by[((1000, 1), 5)]["ticks"] == by[((1, 1000), 5)]["ticks"][::-1]       # a reversed domain reverses the ticks
    assert by[((1, 1e15), 5)]["ticks"][0] == 1 and by[((1, 1e15), 5)]["ticks"][-1] <= 1e15
    assert by[((0.001, 0.1), 10)]["ticks"][0] == 0.001            # negative exponents
