"""d3-variants (plotly wave B): optional fields on histogram, box_plot and treemap, in both twins.

Every existing payload must render byte for byte as before (tests/fixtures/d3_variants_base_sha.json holds the sha256 of the
base commit's output for tests/fixtures/d3_variants_payloads.py), and Python and GAS must emit identical HTML.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent / "fixtures"))
from d3_variants_payloads import payloads  # noqa: E402
from test_motion_atoms import _gas_batch, _node, _py, core_js  # noqa: F401,E402
from test_motion_atoms import wa  # noqa: E402

FIX = Path(__file__).parent / "fixtures"
BASE = json.loads((FIX / "d3_variants_base_sha.json").read_text())
PAY = payloads()
ATTACK = '"><script>alert(1)</script><img src=x onerror=alert(1)>'
BAD = ("NaN", "undefined", "Infinity", "[object Object]")


def _sha(h):
    return hashlib.sha256(h.encode()).hexdigest()


def _both(core_js, blocks):
    return [_py(dict(b)) for b in blocks], _gas_batch(core_js, blocks)


def _clean(h):
    assert "<script" not in h.lower() and not any(t in h for t in BAD), [t for t in BAD if t in h]


# ── existing payloads are unchanged ─────────────────────────────────────────────
@pytest.mark.parametrize("name", list(BASE))
def test_existing_payload_is_byte_for_byte_unchanged_in_python(name):
    assert _sha(_py(dict(PAY[name]))) == BASE[name]


def test_existing_payloads_are_byte_for_byte_unchanged_in_gas(core_js):
    names = list(BASE)
    out = _gas_batch(core_js, [PAY[n] for n in names])
    assert [_sha(h) for h in out] == [BASE[n] for n in names]


# ── treemap max_items ─────────────────────────────────────────────────────────────
def _tm(n, **kw):
    return {"type": "treemap", "items": [{"category": "A", "name": "n%d" % i, "value": 100 - i} for i in range(n)], **kw}


def _rows(h):
    return len(re.findall(r"<tr>", h.split("<table")[1])) - 1 if "<table" in h else 0


def test_treemap_default_cap_is_twelve_and_max_items_lifts_it(core_js):
    blocks = [_tm(30), _tm(30, max_items=30), _tm(30, max_items=20), _tm(30, max_items=99), _tm(30, max_items=5), _tm(30, max_items="x"), _tm(30, max_items=15.5)]
    py, gas = _both(core_js, blocks)
    assert py == gas
    assert [_rows(h) for h in py] == [12, 30, 20, 12, 12, 12, 12]
    assert "10 items beyond the first 20 were not drawn." in py[2]
    assert "beyond the first" not in py[0] and "beyond the first" not in py[1]
    assert "18 items beyond the first 12" in py[5] or "beyond the first" in py[4]


def test_treemap_max_items_in_nested_mode(core_js):
    b = {"type": "treemap", "max_items": 40, "items": [{"path": ["G%d" % (i % 3), "S%d" % (i % 2)], "name": "n%d" % i, "value": 5 + i} for i in range(40)]}
    py, gas = _both(core_js, [b])
    assert py == gas and _rows(py[0]) == 40
    _clean(py[0])


def test_treemap_hostile_names_stay_escaped_with_max_items(core_js):
    b = _tm(20, max_items=20)
    b["items"][3]["name"] = ATTACK
    py, gas = _both(core_js, [b])
    assert py == gas
    assert "<script" not in py[0] and "<img" not in py[0]


# ── histogram options ───────────────────────────────────────────────────────────────
HG = json.loads((FIX / "histogram_opts_d3_golden.json").read_text())


def _hgs(c):
    return float(c["start"]), float(c["size"]), float(c["end"])


@pytest.mark.parametrize("name", list(HG))
def test_python_explicit_bins_match_d3_exactly(name):
    c = HG[name]
    edges, idx = wa._hg_fixed([float(v) for v in c["values"]], *_hgs(c))
    assert [list(e) for e in edges] == c["edges"]
    cnt = [sum(1 for k in idx if k == j) for j in range(len(edges))]
    assert cnt == c["counts"]
    for fn, key in (("sum", "sum"), ("min", "min"), ("max", "max")):
        got = []
        for j in range(len(edges)):
            a = [w for w, k in zip(c["weights"], idx) if k == j]
            got.append(None if not a else (sum(a) if fn == "sum" else min(a) if fn == "min" else max(a)))
        if fn == "sum":      # d3.sum adds left to right, so does sum() on the same doubles
            assert got == c["sum"]
        else:
            assert got == c[key]


def test_gas_explicit_bins_match_d3_exactly(core_js):
    names = list(HG)
    res = _node(core_js, "var G = " + json.dumps([[HG[n]["values"], HG[n]["start"], HG[n]["size"], HG[n]["end"]] for n in names]) +
                "; console.log(JSON.stringify(G.map(function(g){ var r = _hgFixed(g[0], g[1], g[2], g[3]); return [r[0], r[1]]; })));")
    for n, (edges, idx) in zip(names, res):
        assert edges == HG[n]["edges"], n
        assert [sum(1 for k in idx if k == j) for j in range(len(edges))] == HG[n]["counts"], n


V = [3, 4, 4, 5, 6, 7, 7, 7, 8, 9, 12, 15, 21, 22, 40]
W = [1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6, 6.5, 7, 7.5, 8, 9]
HOPTS = [dict(bin_size=5), dict(bin_size=5, bin_start=0, bin_end=30), dict(bin_start=2), dict(bin_end=50), dict(bin_start=0, bin_end=40),
         dict(norm="percent"), dict(norm="probability"), dict(norm="density", bin_size=4), dict(norm="probability density", bin_size=4),
         dict(cumulative=True), dict(cumulative=True, norm="percent"), dict(func="sum", weights=W), dict(func="avg", weights=W, bin_size=10),
         dict(func="min", weights=W, bin_size=10, cumulative=True), dict(func="max", weights=[-w for w in W], bin_size=10), dict(func="sum", weights=[w - 5 for w in W], bin_size=5, norm="percent"),
         dict(func="sum"), dict(bin_size=0.001), dict(bin_size=-2, norm="bogus", func="nope"), dict(norm=[], func={}, bin_size="x", weights="y"), dict(bin_start=50, bin_end=10),
         dict(bin_size=5, unit="ms", x_label="Latency", version=2), dict(weights=[1] * 10), dict(weights=[None, "a"] + W[2:], func="sum", bin_size=7)]


def test_histogram_options_python_and_gas_emit_identical_html(core_js):
    blocks = [{"type": "histogram", "values": V, **o} for o in HOPTS]
    py, gas = _both(core_js, blocks)
    for o, p, g in zip(HOPTS, py, gas):
        assert p == g, o
        _clean(p)


def _tab(h):
    return [re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r) for r in re.findall(r"<tr>(.*?)</tr>", h.split("<table")[1], re.S)]


def test_histogram_explicit_bins_and_count_table():
    h = _py({"type": "histogram", "values": V, "bin_size": 10, "bin_start": 0, "bin_end": 50})
    t = _tab(h)
    assert t[0][:3] == ["Bin from", "Bin to", "Count"] and [r[2] for r in t[1:]] == ["10", "2", "2", "0", "1"]
    assert "Count per bin" in h


def test_histogram_norm_cumulative_and_func():
    t = _tab(_py({"type": "histogram", "values": V, "bin_size": 10, "bin_start": 0, "bin_end": 50, "norm": "percent", "cumulative": True}))
    assert [r[3] for r in t[1:]] == ["66.667", "80", "93.333", "93.333", "100"]
    t = _tab(_py({"type": "histogram", "values": V, "bin_size": 10, "bin_start": 0, "bin_end": 50, "func": "sum", "weights": W}))
    assert t[1][3] == "37.5" and t[4][3] == "0"              # 1.5+2+2.5+3+3.5+4+4.5+5+5.5+6; the empty bin sums to 0


def test_histogram_options_hostile_input_never_throws_or_becomes_markup(core_js):
    odd = [None, True, "x", [], {}, ATTACK, 1e308, -1e308, 0]
    blocks = [{"type": "histogram", "values": V, "unit": ATTACK, "x_label": ATTACK, "title": ATTACK, "bin_size": 5, "norm": ATTACK, "func": ATTACK, "weights": [ATTACK] * 3 + W[3:]}]
    blocks += [{"type": "histogram", "values": V, k: o} for k in ("bin_size", "bin_start", "bin_end", "norm", "cumulative", "func", "weights") for o in odd]
    blocks += [{"type": "histogram", "values": V + odd, "bin_size": 0.5, "bin_start": -1e12, "bin_end": 1e12}, {"type": "histogram", "values": [1e12] * 6, "bin_size": 1e-9}]
    py, gas = _both(core_js, blocks)
    for b, p, g in zip(blocks, py, gas):
        assert p == g, b
        assert "<script" not in p and "<img" not in p, b
        assert not any(t in p for t in BAD), b


# ── box_plot options ──────────────────────────────────────────────────────────────
BX = json.loads((FIX / "box_opts_d3_golden.json").read_text())


@pytest.mark.parametrize("name", list(BX))
@pytest.mark.parametrize("method", ["linear", "exclusive", "inclusive"])
def test_python_quartile_methods_match_d3(name, method):
    a = sorted(float(v) for v in BX[name]["values"])
    assert list(wa._bp_quartiles(a, method)) == BX[name][method]


def test_gas_quartile_methods_match_d3(core_js):
    names = list(BX)
    res = _node(core_js, "var G = " + json.dumps([BX[n]["values"] for n in names]) +
                "; console.log(JSON.stringify(G.map(function(v){ v = v.slice().sort(function(a,b){return a-b;}); return ['linear','exclusive','inclusive'].map(function(m){ return _bpQuartiles(v, m); }); })));")
    for n, r in zip(names, res):
        assert r == [BX[n]["linear"], BX[n]["exclusive"], BX[n]["inclusive"]], n


@pytest.mark.parametrize("name", list(BX))
def test_python_kde_matches_d3_example_to_1e9(name):
    a = sorted(float(v) for v in BX[name]["values"])
    q1, _, q3 = wa._bp_quartiles(a, "linear")
    dens, bw, _ = wa._bp_kde(a, q1, q3, None)
    assert wa._bp_sd(a) == BX[name]["sd"] and bw == BX[name]["bw"]
    # exp() may differ from V8's in the last ulp, so the density is compared to 1e-9 (relative), not bit for bit
    assert all(abs(d - g) <= 1e-9 * max(1.0, abs(g)) for (_, d), g in zip(dens, BX[name]["density"]))


def test_gas_kde_matches_d3_example_to_1e9(core_js):
    names = list(BX)
    res = _node(core_js, "var G = " + json.dumps([BX[n]["values"] for n in names]) +
                "; console.log(JSON.stringify(G.map(function(v){ v = v.slice().sort(function(a,b){return a-b;}); var q = _bpQuartiles(v, 'linear'), r = _bpKde(v, q[0], q[2], null); return [_bpSd(v), r[1], r[0].map(function(p){return p[1];})]; })));")
    for n, (sd, bw, dens) in zip(names, res):
        assert sd == BX[n]["sd"] and bw == BX[n]["bw"], n
        assert all(abs(d - g) <= 1e-9 * max(1.0, abs(g)) for d, g in zip(dens, BX[n]["density"])), n


G3 = [{"label": "A", "values": V}, {"label": "B", "values": [1, 2, 3, 4, 5, 6, 7, 40]}, {"label": ATTACK, "stats": {"q1": 2, "median": 3, "q3": 5, "n": 20, "mean": 3.4, "min": 0, "max": 9}}]
BOPTS = [dict(quartile_method="exclusive"), dict(quartile_method="inclusive", show_mean=True), dict(orientation="v"), dict(orientation="v", shape="violin", notches=True, show_mean=True),
         dict(shape="violin"), dict(shape="violin", bandwidth=2), dict(shape="violin", bandwidth=-1), dict(notches=True), dict(show_mean=True, unit="ms", x_label="Latency", version=2),
         dict(orientation="sideways", shape="cube", quartile_method="bogus"), dict(show_points=True, notches=True), dict(quartile_method=[], show_mean="yes", notches=1, bandwidth="x")]


def test_box_plot_options_python_and_gas_emit_identical_html(core_js):
    blocks = [{"type": "box_plot", "groups": G3, **o} for o in BOPTS] + [{"type": "box_plot", "groups": G3[2:], "violin": 1}, {"type": "box_plot", "groups": [G3[2]], "shape": "violin", "orientation": "v"}]
    py, gas = _both(core_js, blocks)
    for o, p, g in zip(BOPTS, py, gas):
        assert p == g, o
        assert "<script" not in p and "<img" not in p and not any(t in p for t in BAD), o


def test_box_plot_stats_form_alone_triggers_the_new_path_and_needs_no_values():
    h = _py({"type": "box_plot", "groups": [{"label": "S", "stats": {"q1": 2, "median": 3, "q3": 5, "lo": 0, "hi": 9, "n": 12}}]})
    t = _tab(h)
    assert t[1][:2] == ["S", "12"] and t[1][3:6] == ["2", "3", "5"] and t[1][2] == "n/a"


def test_box_plot_quartile_method_changes_the_table_and_is_named_in_the_label():
    lin = _tab(_py({"type": "box_plot", "groups": [{"label": "G", "values": [2, 4, 4, 5, 7, 9, 12]}], "quartile_method": "linear"}))
    exc = _tab(_py({"type": "box_plot", "groups": [{"label": "G", "values": [2, 4, 4, 5, 7, 9, 12]}], "quartile_method": "exclusive"}))
    assert lin[1][3] == "4" and lin[1][5] == "8" and exc[1][5] == "9"
    assert "Quartiles by the exclusive method" in _py({"type": "box_plot", "groups": [{"label": "G", "values": [2, 4, 4, 5, 7, 9, 12]}], "quartile_method": "exclusive"})


def test_box_plot_mean_notch_violin_and_orientation_marks():
    base = {"type": "box_plot", "groups": G3[:2]}
    h = _py({**base, "show_mean": True, "notches": True, "shape": "violin", "orientation": "v"})
    assert h.count('class="bpa"') == 2 and h.count('class="bpv"') == 2 and "vertical axis" in h and "Mean" in _tab(h)[0]
    assert len(re.findall(r'class="bpq bpt" points="([^"]+)"', h)[0].split()) == 10          # a notched box has 10 vertices
    assert 'class="bpv"' not in _py({**base, "orientation": "v"}) and "horizontal axis" in _py({**base, "notches": True})


def test_box_plot_options_hostile_input_never_throws_or_becomes_markup(core_js):
    odd = [None, True, "x", [], {}, ATTACK, 1e308, 0]
    blocks = [{"type": "box_plot", "groups": [{"label": ATTACK, "values": V}], "unit": ATTACK, "x_label": ATTACK, "title": ATTACK, "quartile_method": ATTACK, "shape": ATTACK, "orientation": ATTACK, "notches": True, "show_mean": True}]
    blocks += [{"type": "box_plot", "groups": [{"values": V}], k: o} for k in ("quartile_method", "show_mean", "orientation", "notches", "shape", "bandwidth") for o in odd]
    blocks += [{"type": "box_plot", "groups": [{"stats": o}, {"stats": {"q1": 1, "median": 2, "q3": 3, "n": o}}, {"values": V, "stats": o}], "notches": True} for o in odd]
    py, gas = _both(core_js, blocks)
    for b, p, g in zip(blocks, py, gas):
        assert p == g, b
        assert "<script" not in p and "<img" not in p and not any(t in p for t in BAD), b


# ─── wave B fix round: hostile numbers, build-contract keys, defaults, empty bins ─────────────────────────────────
def _raw(core_js, blocks):
    """Both twins with the data-key attributes kept (_py and _gas_batch strip them)."""
    from test_motion_atoms import _node_raw, _py_keyed
    gas = _node_raw(core_js, "var B = " + json.dumps(blocks) + "; console.log(JSON.stringify(B.map(function(b){ return renderAtoms([b], {}); })));")
    return [_py_keyed(dict(b)) for b in blocks], gas


NUMS = [10 ** 400, -10 ** 400, 1e308, -1e308, 1.7976931348623157e308, 5e-324, 1e-320, 1e-300, 1e-9, 0, -1, -1e-9, float("nan"), float("inf"), float("-inf"), "1e999", "NaN", 1e12, -1e12]


def test_histogram_hostile_bin_numbers_never_raise_and_never_print_nan(core_js):
    blocks = []
    for bad in NUMS:
        for k in ("bin_size", "bin_start", "bin_end"):
            blocks.append({"type": "histogram", "values": V, k: bad})
            blocks.append({"type": "histogram", "values": V, "bin_size": 1, k: bad} if k != "bin_size" else {"type": "histogram", "values": V, "bin_size": bad, "bin_start": 0, "bin_end": 50})
        blocks.append({"type": "histogram", "values": V + [bad], "bin_size": 2, "weights": [bad] * 5 + W, "func": "sum", "norm": "percent", "cumulative": True})
        blocks.append({"type": "histogram", "values": [bad if isinstance(bad, (int, float)) else 1] * 6 + V, "bin_size": bad})
    # a denormal spread makes the automatic bin size 0
    blocks += [{"type": "histogram", "values": [0, 0, 5e-324, 5e-324, 5e-324, 5e-324], "bin_start": 0}, {"type": "histogram", "values": [1e12, -1e12, 1e12, 0, 0], "bin_size": 1e-300}]
    py = [_py(dict(b)) for b in blocks]          # a raise here fails the test
    gas = _gas_batch(core_js, blocks)
    for b, p, g in zip(blocks, py, gas):
        assert p == g, json.dumps(b, default=str)[:240]
        _clean(p)
        assert "<script" not in p


def test_a_tiny_bin_size_is_capped_at_200_bins_with_a_note_in_both_twins(core_js):
    blocks = [{"type": "histogram", "values": V, "bin_size": s} for s in (1e-9, 1e-300, 1e-320, 5e-324, 0.01, 0.1)] + [{"type": "histogram", "values": V, "bin_size": 1e-300, "bin_start": 0, "bin_end": 50}]
    py, gas = _both(core_js, blocks)
    assert py == gas
    for p in py:
        assert "bins; the first 200 are drawn" in p, p[:200]
    # sizes that were fine before are untouched by the cap: same edges, same table
    ok = _py({"type": "histogram", "values": V, "bin_size": 0.1})
    assert _rows(ok) == 200 and "No value falls" not in ok


def test_histogram_option_paths_carry_keys_and_empty_bins_count_zero(core_js):
    blocks = [{"type": "histogram", "values": V, "bin_size": 10, "bin_start": 0, "bin_end": 50, "norm": "percent"}, {"type": "histogram", "values": V, "bin_size": 10, "bin_start": 0, "bin_end": 50, "cumulative": True, "unit": "ms"},
              {"type": "histogram", "values": V, "bin_size": 10, "bin_start": 0, "bin_end": 50, "func": "sum", "weights": W}, {"type": "histogram", "values": V, "bin_size": 10, "bin_start": 0, "bin_end": 50, "func": "avg", "weights": W}]
    py, gas = _raw(core_js, blocks)
    from test_motion_atoms import _norm
    for p, g in zip(py, gas):
        assert _norm(p) == _norm(g)
        keys = re.findall(r'<rect class="hgb[^"]*" data-cb="bar" data-key="([^"]*)"', p)
        assert len(keys) >= 4 and len(set(keys)) == len(keys) and all(keys), keys
    assert re.findall(r'data-key="([^"]*)"', py[0])[:3] == ["0 to 10", "10 to 20", "20 to 30"]
    assert re.findall(r'data-key="([^"]*)"', py[1])[:2] == ["0 to 10 ms", "10 to 20 ms"]
    t = [_tab(h) for h in _both(core_js, blocks)[0]]
    assert [r[3] for r in t[0][1:]] == ["66.667", "13.333", "13.333", "0", "6.667"]       # the empty bin is 0, not "none"
    assert [r[3] for r in t[1][1:]] == ["10", "12", "14", "14", "15"]
    assert t[2][4][3] == "0" and t[3][4][3] == "none"                                       # sum of nothing is 0; the average of nothing is not a number
    # keys are additive: the same markup without them
    strip = lambda h: re.sub(r' data-(?:cb|key)="[^"]*"', "", h)
    assert strip(py[0]) == strip(_py(dict(blocks[0])))


def test_box_plot_option_paths_carry_keys_and_the_notch_is_in_the_table(core_js):
    base = {"type": "box_plot", "groups": [{"label": "A", "values": V}, {"label": "A", "values": [1, 2, 3, 4, 5, 6, 7, 40]}, {"label": "S", "stats": {"q1": 2, "median": 3, "q3": 5}}]}
    blocks = [dict(base, notches=True), dict(base, orientation="v", shape="violin"), dict(base, quartile_method="exclusive", show_mean=True)]
    py, gas = _raw(core_js, blocks)
    from test_motion_atoms import _norm
    for p, g in zip(py, gas):
        assert _norm(p) == _norm(g)
        assert re.findall(r'<g data-cb="node" data-key="([^"]*)">', p) == ["A", "A (2)", "S"]
    t = _tab(_both(core_js, blocks)[0][0])
    assert t[0][-2:] == ["Notch from", "Notch to"] and t[3][-2:] == ["n/a", "n/a"] and float(t[1][-2]) < float(t[1][4]) < float(t[1][-1])


def test_a_tiny_bandwidth_is_raised_not_nan(core_js):
    blocks = [{"type": "box_plot", "shape": "violin", "bandwidth": bw, "groups": [{"label": "A", "values": V}, {"label": "B", "values": [5] * 6}]} for bw in (1e-320, 5e-324, 1e-300, 1e-12, 1e-9, 1e12, 0, -3, float("nan"), "x")]
    py, gas = _both(core_js, blocks)
    assert py == gas
    for bw, p in zip((1e-320, 5e-324, 1e-300, 1e-12, 1e-9, 1e12, 0, -3, float("nan"), "x"), py):
        _clean(p)
        assert 'class="bpv"' in p
        assert ("The bandwidth was too small" in p) == (bw in (1e-320, 5e-324, 1e-300, 1e-12, 1e-9)), bw


def test_box_plot_hostile_numbers_never_raise(core_js):
    blocks = []
    for bad in NUMS:
        blocks += [{"type": "box_plot", "groups": [{"label": "A", "values": V + [bad]}], "shape": "violin", "notches": True, "show_mean": True, "bandwidth": bad},
                   {"type": "box_plot", "groups": [{"label": "S", "stats": {"q1": bad, "median": 3, "q3": 5, "n": bad, "mean": bad, "min": bad, "max": bad, "lo": bad, "hi": bad}}], "notches": True},
                   {"type": "box_plot", "groups": [{"label": "S", "stats": {"q1": 1, "median": 3, "q3": 5, "n": bad, "mean": bad, "min": bad, "max": bad}}], "notches": True, "show_mean": True}]
    py = [_py(dict(b)) for b in blocks]
    gas = _gas_batch(core_js, blocks)
    for b, p, g in zip(blocks, py, gas):
        assert p == g, json.dumps(b, default=str)[:240]
        _clean(p)


def test_options_written_at_their_default_draw_exactly_what_leaving_them_out_draws(core_js):
    hist = [{}, {"norm": ""}, {"norm": "count"}, {"cumulative": False}, {"func": "count"}, {"bin_size": None}, {"weights": None}, {"cumulative": None, "norm": None, "func": None}, {"weights": "x"}]
    box = [{}, {"quartile_method": "linear"}, {"show_mean": False}, {"notches": False}, {"orientation": "h"}, {"orientation": "horizontal"}, {"shape": "box"}, {"bandwidth": 3}, {"shape": None, "orientation": None},
           {"quartile_method": "linear", "show_mean": False, "notches": False, "orientation": "h", "shape": "box"}]
    blocks = [{"type": "histogram", "values": V, **o} for o in hist] + [{"type": "box_plot", "groups": [{"label": "A", "values": V}], **o} for o in box]
    py, gas = _both(core_js, blocks)
    nh = len(hist)
    assert py == gas
    assert all(p == py[0] for p in py[:nh]) and all(p == py[nh] for p in py[nh:])
    assert "Count of values per bin" in py[0] and "Not understood" not in py[0]
    # a real option still switches the path
    assert "Count per bin" in _py({"type": "histogram", "values": V, "bin_size": 5}) and "bpq" in _py({"type": "box_plot", "groups": [{"label": "A", "values": V}], "notches": True})


def test_the_old_paths_keep_their_stagger_count_and_keys(core_js):
    # the treemap cell lines are main's (stagger over the real item count); max_items only lifts the cap
    py, gas = _both(core_js, [_tm(2), _tm(30, max_items=30)])
    assert py == gas and "var(--p,1)*3 -" in py[0]
