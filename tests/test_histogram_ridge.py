"""histogram `layout: ridge` (I59, owner decision D5): several series on shared bins, one ridge per series.

GOLDEN (tests/fixtures/histogram_ridge_d3_golden.json, from histogram_ridge_d3_golden_gen.mjs) holds what the REAL
d3-array 3.2.4 gives: the shared edges are bin() of all the series pooled, and each series is counted by
bin().domain([x0, x1]).thresholds(the inner edges). Both twins must reproduce it exactly.
Also held here: Python/GAS HTML parity, the hidden table, the aria label, the motion index, malformed series, the
`version` field, and that a payload without `layout` renders exactly as before.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from test_histogram import ATTACK, PAYLOADS as BAR_PAYLOADS, _table
from test_motion_atoms import _gas_batch, _node, _py, core_js  # noqa: F401  (core_js is a fixture)
from test_motion_atoms import wa  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
D = json.loads((ROOT / "tests/fixtures/histogram_ridge_d3_golden.json").read_text())
CASES = {**D["golden"], **{f"fuzz{i}": c for i, c in enumerate(D["fuzz"])}}


def _ridge(c, labels=None, **kw):
    b = {"type": "histogram", "layout": "ridge", "series": [{"label": (labels or [])[k] if labels and k < len(labels) else "S%d" % (k + 1), "values": v} for k, v in enumerate(c["series"])]}
    if c["bins"] is not None:
        b["bins"] = c["bins"]
    b.update(kw)
    return b


# ─── the layout against real d3 ────────────────────────────────────────────────
@pytest.mark.parametrize("name", list(CASES))
def test_python_ridge_bins_match_d3_exactly(name):
    c = CASES[name]
    edges, counts = wa._hg_ridge([[float(v) for v in s] for s in c["series"]], c["bins"])
    assert [list(e) for e in edges] == c["edges"]
    assert counts == c["counts"]


def test_gas_ridge_bins_match_d3_exactly(core_js):
    names = list(CASES)
    res = _node(core_js, "var G = " + json.dumps([[CASES[n]["series"], CASES[n]["bins"]] for n in names]) +
                "; console.log(JSON.stringify(G.map(function(g){ return _hgRidge(g[0], g[1]); })));")
    for n, (edges, counts) in zip(names, res):
        assert edges == CASES[n]["edges"], n
        assert counts == CASES[n]["counts"], n


def test_the_ridge_golden_set_covers_the_hard_cases():
    g = D["golden"]
    assert g["all_equal@auto"]["edges"] == [[7, 7]] and g["all_equal@auto"]["counts"] == [[5], [6]]
    assert g["disjoint@auto"]["counts"][0][-1] == 0 and g["disjoint@auto"]["counts"][1][0] == 0       # a series can be empty in a bin
    assert g["value_on_max_tick@auto"]["edges"][-1][1] > 100                                         # the pooled max on a tick extends the last bin
    assert len(g["eight_series@auto"]["series"]) == 8 and len(g["one_series@auto"]["series"]) == 1
    assert all(sum(cs) == len(s) for c in CASES.values() for s, cs in zip(c["series"], c["counts"]))


# ─── rendering ─────────────────────────────────────────────────────────────────
PAYLOADS = {
    "three": _ridge(CASES["three_shifted@auto"], ["Before", "During", "After"], title="Wait times by phase", x_label="Wait", unit="min"),
    "one": _ridge(CASES["one_series@auto"], ["Only"]),
    "unequal": _ridge(CASES["unequal_sizes@12"], ["Pilot", "Rollout"]),
    "disjoint": _ridge(CASES["disjoint@auto"]),
    "all_equal": _ridge(CASES["all_equal@auto"]),
    "eight": _ridge(CASES["eight_series@40"], ["A rather long series label here", "B", "C", "D", "E", "F", "G", "H"]),
    "tiny": _ridge(CASES["negatives_and_tiny@auto"], unit="V"),
    "max_bins": _ridge(CASES["unequal_sizes@40"]),
    "malformed": {"type": "histogram", "layout": "ridge", "series": [None, 7, "x", {"label": "Good", "values": [1, 2, 3, 4, 5, "6", None, 1e30]},
                                                                      {"values": [2, 3, 4, 5, 6, 7]}, {"label": "Short", "values": [1, 2, 3]}, {"label": ["a", "b"], "values": "1,2,3"}]},
    "no_series": {"type": "histogram", "layout": "ridge", "title": "T"},
    "series_not_a_list": {"type": "histogram", "layout": "ridge", "series": {"label": "x", "values": [1, 2, 3, 4, 5]}},
    "all_short": {"type": "histogram", "layout": "ridge", "series": [{"label": "a", "values": [1, 2]}, {"label": "b", "values": []}]},
    "nine_series": {"type": "histogram", "layout": "ridge", "series": [{"label": "S%d" % k, "values": [k, k + 1, k + 2, k + 3, k + 4]} for k in range(9)]},
    "version_2": dict(_ridge(CASES["one_series@auto"]), version=2),
    "bars_version_3": {"type": "histogram", "version": 3, "values": [1, 2, 3, 4, 5, 6, 7]},
    "bars_version_junk": {"type": "histogram", "version": "two", "values": [1, 2, 3, 4, 5, 6, 7]},
    "unknown_layout": {"type": "histogram", "layout": "violin", "values": [1, 2, 3, 4, 5, 6, 7], "series": [{"values": [1, 2, 3, 4, 5]}]},
}


@pytest.mark.parametrize("name", list(PAYLOADS))
def test_python_and_gas_emit_identical_html(name, core_js):
    assert _py(PAYLOADS[name]) == _gas_batch(core_js, [PAYLOADS[name]])[0]


def test_a_payload_without_layout_renders_byte_for_byte_as_before():
    # the bars layout is the default; a ridge-only field on a bars payload is ignored, and so is an unknown layout
    for b in BAR_PAYLOADS.values():
        assert _py(b) == _py(dict(b, series=[{"label": "x", "values": [1, 2, 3, 4, 5]}]))
        assert _py(b) == _py(dict(b, layout="bars"))
    assert _py(PAYLOADS["unknown_layout"]) == _py({"type": "histogram", "values": [1, 2, 3, 4, 5, 6, 7]})


def test_hidden_table_has_one_count_column_per_series(core_js):
    for name in ("three", "eight", "unequal", "disjoint"):
        b = PAYLOADS[name]
        edges, counts = wa._hg_ridge([[float(v) for v in s["values"]] for s in b["series"]], b.get("bins"))
        for html in (_py(b), _gas_batch(core_js, [b])[0]):
            head, rows = _table(html)
            assert head == ["Bin from", "Bin to"] + [s["label"][:30] for s in b["series"]]
            assert len(rows) == len(edges)
            for k, s in enumerate(b["series"]):
                assert [int(r[2 + k]) for r in rows] == counts[k]
            t = html.index("<table")
            assert 'role="img"' in html[:t] and 'role="img"' not in html[t:]
    head, rows = _table(_py(PAYLOADS["three"]))
    assert all(r[0].endswith(" min") and r[1].endswith(" min") for r in rows)


def test_aria_label_names_every_series_and_its_peak(core_js):
    for html in (_py(PAYLOADS["three"]), _gas_batch(core_js, [PAYLOADS["three"]])[0]):
        a = re.search(r'role="img" aria-label="([^"]*)"', html).group(1)
        assert a.startswith("Ridgeline histogram of 3 series in 12 shared bins from 25 to 85 min. ")
        assert "Before: 120 values, most from " in a and "During: 200 values, most from " in a and "After: 80 values, most from " in a


def test_one_ridge_per_series_drawn_top_to_bottom_with_heights_as_shares(core_js):
    b = PAYLOADS["unequal"]
    edges, counts = wa._hg_ridge([[float(v) for v in s["values"]] for s in b["series"]], b.get("bins"))
    for html in (_py(b), _gas_batch(core_js, [b])[0]):
        assert "<script" not in html
        paths = re.findall(r'<path class="hgr" d="([^"]+)"', html)
        assert len(paths) == 2
        shares = [[c / sum(cs) for c in cs] for cs in counts]
        top = max(max(s) for s in shares)
        for d, sh in zip(paths, shares):
            ys = [float(y) for y in re.findall(r"H[\d.]+V([\d.]+)", d)]
            # one step per bin: the tallest share across all series reaches the top, a zero share sits on the baseline
            assert len(ys) == len(sh)
            assert all(abs((1000 - y) / 1000 - s / top) < 0.006 for y, s in zip(ys, sh))
        # a series of 12 and one of 600 are comparable: neither is flattened by the other's size
        assert max(shares[0]) / top > 0.3


def test_motion_index_per_ridge_stays_inside_its_clamp(core_js):
    for html in (_py(PAYLOADS["eight"]), _gas_batch(core_js, [PAYLOADS["eight"]])[0]):
        ks = re.findall(r'<g class="hgrg" style="--k:clamp\(0,calc\(var\(--p,1\)\*(\d+) - (\d+)\),1\);', html)
        assert [int(i) for _, i in ks] == list(range(8)) and all(int(n) == 9 for n, _ in ks)


def test_malformed_series_are_skipped_and_explained(core_js):
    for h in (_py(PAYLOADS["malformed"]), _gas_batch(core_js, [PAYLOADS["malformed"]])[0]):
        head, rows = _table(h)
        # null, 7 and "x" are not series; "Short" (3 numbers) and the one whose values are a string are left out
        assert head == ["Bin from", "Bin to", "Good", "Series 5"]
        assert sum(int(r[2]) for r in rows) == 5 and sum(int(r[3]) for r in rows) == 6
        assert "3 entries were not a usable number and were skipped." in h
        assert "5 series had fewer than 5 usable numbers or were not a series and were left out." in h
        assert "NaN" not in h and "undefined" not in h and "[object Object]" not in h


def test_no_usable_series_gives_a_clear_note_and_no_chart():
    for k in ("no_series", "series_not_a_list", "all_short"):
        h = _py(PAYLOADS[k])
        assert "A ridge histogram needs at least one series with 5 numbers." in h
        assert "<svg" not in h and "<table" not in h and "NaN" not in h
    assert ">T</div>" in _py(PAYLOADS["no_series"])


def test_only_the_first_eight_series_are_read():
    head, _ = _table(_py(PAYLOADS["nine_series"]))
    assert head[2:] == ["S%d" % k for k in range(8)]
    assert "1 series beyond the first 8 was not drawn." in _py(PAYLOADS["nine_series"])


def test_version_above_one_is_noted_and_otherwise_silent(core_js):
    for name in ("version_2", "bars_version_3"):
        for h in (_py(PAYLOADS[name]), _gas_batch(core_js, [PAYLOADS[name]])[0]):
            n = PAYLOADS[name]["version"]
            assert "Written for histogram version %d; drawn as version 1." % n in h
    for name in ("bars_version_junk",):
        assert "version" not in _py(PAYLOADS[name]).lower()
    assert _py(dict(BAR_PAYLOADS["normalish"], version=1)) == _py(BAR_PAYLOADS["normalish"])


def test_hostile_series_labels_are_escaped_in_both_twins(core_js):
    b = {"type": "histogram", "layout": "ridge", "title": ATTACK, "unit": ATTACK, "series": [{"label": ATTACK, "values": [1, 2, 3, 4, 5]}]}
    for h in (_py(b), _gas_batch(core_js, [b])[0]):
        assert "<img" not in h and "<script" not in h.replace("<style", "") and 'onerror=alert(1)>' not in h.replace("&gt;", "")
