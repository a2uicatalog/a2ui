"""histogram (proposal, preview): d3-array 3.2.4 bin() with thresholdSturges, ported by hand into BOTH renderers.

GOLDEN (tests/fixtures/histogram_d3_golden.json) holds the bin edges and counts that the REAL d3-array produced
(see histogram_d3_golden_gen.mjs). Both twins must reproduce them exactly (== on the doubles, not within a tolerance).
Also held here: Python/GAS HTML parity, the hidden table, the aria label, the motion index inside its clamp at the
largest bin counts, malformed input, escaping, and registration.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

from test_motion_atoms import _gas_batch, _node, _py, core_js  # noqa: F401  (core_js is a fixture)
from test_motion_atoms import wa  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
D = json.loads((ROOT / "tests/fixtures/histogram_d3_golden.json").read_text())
CASES = {**D["golden"], **{f"fuzz{i}": c for i, c in enumerate(D["fuzz"])}}
ATTACK = '"><img src=x onerror=alert(1)>\'"><svg onload=alert(1)></script><script>alert(4)</script> onmouseover=alert(2)'


def _block(c, **kw):
    b = {"type": "histogram", "values": c["values"]}
    if c["bins"] is not None:
        b["bins"] = c["bins"]
    b.update(kw)
    return b


def _ramp(n, f=lambda i: (i * 37) % 101 + (i % 7) * 0.5):
    return [f(i) for i in range(n)]


# ─── the layout against real d3 ────────────────────────────────────────────────
@pytest.mark.parametrize("name", list(CASES))
def test_python_bins_match_d3_exactly(name):
    c = CASES[name]
    edges, counts = wa._hg_bin([float(v) for v in c["values"]], c["bins"])
    assert [list(e) for e in edges] == c["edges"]
    assert counts == c["counts"]


def test_gas_bins_match_d3_exactly(core_js):
    names = list(CASES)
    res = _node(core_js, "var G = " + json.dumps([[CASES[n]["values"], CASES[n]["bins"]] for n in names]) +
                "; console.log(JSON.stringify(G.map(function(g){ return _hgBin(g[0], g[1]); })));")
    for n, (edges, counts) in zip(names, res):
        assert edges == CASES[n]["edges"], n
        assert counts == CASES[n]["counts"], n


def test_the_golden_set_covers_the_hard_cases():
    # the cases that make a hand port drift: zero-width domain, bins that the tick rule rounds away from the request, more bins than asked for, negatives, tiny and huge scales
    g = D["golden"]
    assert g["all_equal@auto"]["counts"] == [6] and g["all_equal@auto"]["edges"] == [[7, 7]]
    assert len(g["two_values@40"]["counts"]) == 51 and len(g["small_ints@3"]["counts"]) == 2
    assert g["max_on_tick@auto"]["edges"][-1][1] == 120          # a value on a tick extends the last bin by one step
    assert min(e[0] for e in g["negatives@auto"]["edges"]) < 0
    assert any("e-" in repr(e[0]) or abs(e[0]) < 1e-3 for e in g["tiny_numbers@auto"]["edges"]) and g["big_numbers@auto"]["edges"][0][0] >= 4e5


def test_powers_of_ten_are_the_same_exact_literals_in_both_twins(core_js):
    ps = list(range(-330, 312))
    res = _node(core_js, "var P = " + json.dumps(ps) + "; console.log(JSON.stringify(P.map(function(p){ return _hgP10(p); }).map(function(v){ return v === Infinity ? 'inf' : v; })));")
    assert [wa._hg_pow10(p) for p in ps] == [float("inf") if v == "inf" else v for v in res]


def test_python_bins_agree_with_gas_on_400_fuzzed_datasets(core_js):
    # the golden fixture keeps 30 fuzz cases; here the same generator's other fuzz is replaced by a fresh seeded set run through both twins
    import random
    rnd = random.Random(7)
    cases = []
    for _ in range(300):
        n = rnd.randint(5, 600)
        scale, off = 10.0 ** rnd.randint(-8, 9), rnd.choice([0, 0, rnd.uniform(-1, 1) * 10.0 ** rnd.randint(-3, 9)])
        kind = rnd.randint(0, 3)
        v = [off + rnd.random() * scale if kind == 0 else off + rnd.gauss(0, scale) if kind == 1 else float(round(off + rnd.random() * scale)) if kind == 2 else round(rnd.gauss(off, scale), 2) for _ in range(n)]
        cases.append([[x for x in v if abs(x) <= 1e12] or [1.0] * 5, rnd.choice([None, rnd.randint(3, 40)])])
    res = _node(core_js, "var G = " + json.dumps(cases) + "; console.log(JSON.stringify(G.map(function(g){ return _hgBin(g[0], g[1]); })));")
    for (vals, bins), (edges, counts) in zip(cases, res):
        if len(vals) < 1:
            continue
        pe, pc = wa._hg_bin([float(x) for x in vals], bins)
        assert [list(e) for e in pe] == edges and pc == counts


# ─── rendering: parity, table, aria, motion ───────────────────────────────────
PAYLOADS = {
    "normalish": {"type": "histogram", "title": "Response times", "x_label": "Latency", "unit": "ms", "values": CASES["normalish_120@auto"]["values"]},
    "skewed": _block(CASES["skewed_300@auto"], title="Order value", unit="EUR"),
    "bimodal": _block(CASES["bimodal_400@auto"], x_label="Score"),
    "max_bins": _block(CASES["uniform_2000@40"]),
    "all_equal": _block(CASES["all_equal@auto"]),
    "negatives": _block(CASES["negatives@7"], unit="C"),
    "decimals": _block(CASES["decimals_small@auto"]),
    "tiny": _block(CASES["tiny_numbers@40"]),
    "big": _block(CASES["big_numbers@auto"], unit="people"),
    "three_bins": _block(CASES["small_ints@3"]),
    "malformed": {"type": "histogram", "values": [1, "2", None, True, 3, 4.5, [5], {"a": 1}, 6, 7, 8, 1e30, 9]},
    "too_few": {"type": "histogram", "title": "T", "values": [1, 2, "x", 4]},
    "empty": {"type": "histogram", "values": []},
    "no_values": {"type": "histogram", "title": "T"},
    "values_not_a_list": {"type": "histogram", "values": "1,2,3,4,5,6"},
    "odd_options": {"type": "histogram", "values": [1, 2, 3, 4, 5, 6, 7, 8], "bins": 1e9, "x_label": 0, "unit": ["a", "b"]},
    "bins_nan_string": {"type": "histogram", "values": [1, 2, 3, 4, 5, 6, 7, 8], "bins": "12"},
}


@pytest.mark.parametrize("name", list(PAYLOADS))
def test_python_and_gas_emit_identical_html(name, core_js):
    assert _py(PAYLOADS[name]) == _gas_batch(core_js, [PAYLOADS[name]])[0]


def test_infinite_and_huge_numbers_are_skipped_identically(core_js):
    b = {"type": "histogram", "values": [1, 2, 3, 4, 5, 6, float("inf"), float("-inf"), 10 ** 30, -(10 ** 13)]}
    py, gas = _py(b), _gas_batch(core_js, [b])[0]
    assert py == gas and "4 entries were not a usable number and were skipped." in py
    assert "Infinity" not in py and "NaN" not in py


def _table(html):
    m = re.search(r'<table style="position:absolute[^"]*"><thead><tr>(.*?)</tr></thead><tbody>(.*?)</tbody></table>', html, re.S)
    assert m
    head = re.findall(r'<th scope="col">(.*?)</th>', m.group(1))
    rows = [re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', r) for r in re.findall(r'<tr>(.*?)</tr>', m.group(2), re.S)]
    return head, rows


@pytest.mark.parametrize("name", ["normalish", "skewed", "bimodal", "max_bins", "negatives", "all_equal"])
def test_hidden_table_lists_every_bin_in_both_twins(name, core_js):
    b = PAYLOADS[name]
    edges, counts = wa._hg_bin([float(v) for v in b["values"]], b.get("bins"))
    for html in (_py(b), _gas_batch(core_js, [b])[0]):
        head, rows = _table(html)
        assert head == ["Bin from", "Bin to", "Count"]
        assert [int(r[2]) for r in rows] == counts and len(rows) == len(edges)
        assert sum(int(r[2]) for r in rows) == len(b["values"])
        if b.get("unit"):
            assert all(r[0].endswith(" " + b["unit"]) and r[1].endswith(" " + b["unit"]) for r in rows)
        t = html.index("<table")
        assert 'role="img"' in html[:t] and 'role="img"' not in html[t:]        # the table is a sibling of the img, so a screen reader still reaches it


def test_img_role_and_aria_label_describe_the_data(core_js):
    for html in (_py(PAYLOADS["normalish"]), _gas_batch(core_js, [PAYLOADS["normalish"]])[0]):
        m = re.search(r'role="img" aria-label="([^"]*)"', html)
        assert m
        a = m.group(1)
        assert a.startswith("Histogram of 120 values in 10 bins from 60 to 160 ms. Tallest bin: ") and a.endswith(" values.")
        assert '<svg viewBox="0 0 1000 1000" preserveAspectRatio="none" aria-hidden="true"' in html


def test_no_script_and_bars_match_the_counts(core_js):
    for name in ("normalish", "max_bins", "all_equal"):
        b = PAYLOADS[name]
        _, counts = wa._hg_bin([float(v) for v in b["values"]], b.get("bins"))
        for html in (_py(b), _gas_batch(core_js, [b])[0]):
            assert "<script" not in html and "onload" not in html.replace("\\", "") and "javascript:" not in html
            hs = [float(x) for x in re.findall(r'<rect class="hgb"[^>]* height="([\d.]+)"', html)]
            assert len(hs) == len(counts)
            # bar heights are proportional to the counts (the y axis starts at 0): h = count / top * 1000 for one common top, to two decimals
            tops = {round(c / h * 1000, 0) for h, c in zip(hs, counts) if c >= max(counts) / 2 and h}
            assert len(tops) <= 2 and max(counts) / max(tops) <= 1.0
            # the tallest bar never exceeds the plot, and a zero count draws a zero-height bar
            assert all(h <= 1000 for h in hs) and all((h == 0) == (c == 0) for h, c in zip(hs, counts))


@pytest.mark.parametrize("name,expect_bins", [("max_bins", 50), ("three_bins", 2), ("two40", 51)])
def test_motion_index_stays_inside_its_clamp_at_the_largest_bin_counts(name, expect_bins, core_js):
    # an earlier infographic bug: the index ran past the clamp, so late items rendered at opacity 0 in a static render.
    b = PAYLOADS[name] if name in PAYLOADS else _block(CASES["two_values@40"])
    for html in (_py(b), _gas_batch(core_js, [b])[0]):
        ks = re.findall(r'<rect class="hgb"[^>]*style="--k:clamp\(0,calc\(var\(--p,1\)\*(\d+) - (\d+)\),1\);transform:scaleY\(var\(--k,1\)\);"', html)
        assert len(ks) == expect_bins
        assert [int(i) for _, i in ks] == list(range(expect_bins))
        assert all(int(n) - int(i) >= 1 for n, i in ks), "a bar would still be at k < 1 when p is 1"
        assert all(int(n) == expect_bins + 1 for n, _ in ks)


def test_forty_requested_bins_can_draw_more_than_forty_and_still_fit():
    # d3 rounds the edges to 1, 2 or 5 times a power of ten; the contract says so
    assert len(CASES["uniform_2000@40"]["counts"]) == 50 and len(CASES["two_values@40"]["counts"]) == 51


def test_never_widens_its_container_by_construction():
    h = _py(PAYLOADS["normalish"])
    assert "container-type:inline-size;max-width:100%;overflow:hidden;" in h and "width:100%;height:100%" in h


def test_label_strides_keep_the_edge_labels_few_and_the_coarse_set_is_a_subset(core_js):
    for name in ("normalish", "max_bins", "big", "tiny"):
        html = _py(PAYLOADS[name])
        marks = re.findall(r'<div class="hgx( hgc)?" style="position:absolute;top:100%;left:([\d.]+)%;', html)
        assert 2 <= len(marks) <= 8, (name, len(marks))
        assert any(m[0] for m in marks), name
        assert len([m for m in marks if m[0]]) <= (len(marks) + 1) // 2 + 1


# ─── malformed input ──────────────────────────────────────────────────────────
def test_non_numbers_are_skipped_and_counted():
    h = _py(PAYLOADS["malformed"])
    # "2", null, true, [5], {"a":1} and 1e30 are not usable numbers; 1, 3, 4.5, 6, 7, 8, 9 are
    assert "6 entries were not a usable number and were skipped." in h
    head, rows = _table(h)
    assert sum(int(r[2]) for r in rows) == 7
    assert 'aria-label="Histogram of 7 values' in h


def test_too_few_values_gives_a_clear_note_and_no_chart():
    for k, n in (("too_few", 3), ("empty", 0), ("no_values", 0), ("values_not_a_list", 0)):
        h = _py(PAYLOADS[k])
        assert f"A histogram needs at least 5 numbers; this list has {n}." in h
        assert "<svg" not in h and "<table" not in h and "NaN" not in h and "undefined" not in h
    assert "1 entry was not a usable number and was skipped." in _py(PAYLOADS["too_few"])
    assert ">T</div>" in _py(PAYLOADS["too_few"])


def test_exactly_five_numbers_is_enough_and_four_is_not():
    assert "<svg" in _py({"type": "histogram", "values": [1, 2, 3, 4, 5]})
    assert "<svg" not in _py({"type": "histogram", "values": [1, 2, 3, 4]})


def test_only_the_first_2000_entries_are_read():
    h = _py({"type": "histogram", "values": list(range(2500))})
    head, rows = _table(h)
    assert sum(int(r[2]) for r in rows) == 2000


def test_bins_option_is_clamped_and_rounded():
    assert _py({"type": "histogram", "values": _ramp(60), "bins": 1}) == _py({"type": "histogram", "values": _ramp(60), "bins": 3})
    assert _py({"type": "histogram", "values": _ramp(60), "bins": 999}) == _py({"type": "histogram", "values": _ramp(60), "bins": 40})
    assert _py({"type": "histogram", "values": _ramp(60), "bins": 7.4}) == _py({"type": "histogram", "values": _ramp(60), "bins": 7})
    assert _py({"type": "histogram", "values": _ramp(60), "bins": "9"}) == _py({"type": "histogram", "values": _ramp(60)})


def test_zero_width_domain_draws_one_full_bar_without_nan(core_js):
    for h in (_py(PAYLOADS["all_equal"]), _gas_batch(core_js, [PAYLOADS["all_equal"]])[0]):
        assert 'x="0.00" y="0.00" width="1000.00" height="1000.00"' in h
        assert "NaN" not in h and "Infinity" not in h and "undefined" not in h and "left:50%" in h
        assert 'in 1 bin from 7 to 7' in h


def test_x_axis_labels_use_the_decimals_the_edges_need_and_group_thousands():
    assert _table(_py(PAYLOADS["decimals"]))[1][0][:2] == ["0.38", "0.40"] and "1,000,000 people" in [r[0] for r in _table(_py(PAYLOADS["big"]))[1]]
    assert _table(_py(PAYLOADS["tiny"]))[1][0][:2] == ["-0.00024", "-0.00023"]
    assert "-0.0" not in re.sub(r"-0\.0\d", "", _py(PAYLOADS["negatives"]))


def test_hostile_text_is_escaped_in_both_twins(core_js):
    b = {"type": "histogram", "title": ATTACK, "x_label": ATTACK, "unit": ATTACK, "values": [1, 2, 3, 4, 5, 6, 7]}
    for h in (_py(b), _gas_batch(core_js, [b])[0]):
        assert "<img" not in h and "<script" not in h.replace("<style", "") and 'onerror=alert(1)>' not in h.replace("&gt;", "")
        assert "&lt;img" in h or "&lt;" in h


# ─── registration ─────────────────────────────────────────────────────────────
def test_registered_as_a_preview_charts_atom_with_an_example_and_every_field_documented():
    blocks = {a["type"]: a for a in yaml.safe_load((ROOT / "atoms/schema.yaml").read_text())["blocks"]}
    a = blocks["histogram"]
    assert a["stage"] == "preview" and set(a["fields"]) == {"title", "values", "bins", "x_label", "unit"}
    assert a["surfaces"] == blocks["treemap"]["surfaces"] and a["source"] == blocks["treemap"]["source"]
    assert re.search(r"^a2ui-charts-v1:\n(?:- .*\n)*- histogram$", (ROOT / "atoms/atom-packs.yaml").read_text(), re.M)
    assert '"histogram":"a2ui-charts-v1"' in (ROOT / "apps-script-surface/gas-wired-renderer/PackMap.gs").read_text()
    import generate_atom_pages as g
    ex = g._EXAMPLE_BLOCKS["histogram"]
    assert ex["type"] == "histogram" and 5 <= len(ex["values"]) <= 2000
    assert "API response times" in _py(ex) and "<svg" in _py(ex)


def test_d3_array_is_credited():
    t = (ROOT / "THIRD-PARTY-NOTICES.md").read_text()
    assert "d3-array 3.2.4" in t and "ISC License" in t and "tests/test_histogram.py" in t
