"""waterfall (I38, owner decision D5): steps that add to or take from a running total, as horizontal bars on a shared axis.

GOLDEN (tests/fixtures/waterfall_d3_golden.json, from waterfall_d3_golden_gen.mjs) holds each bar's start and end (a delta
runs from the running total to the running total plus its value, a total from 0 to the running total) and the shared axis
from the REAL d3-array 3.2.4 nice() and ticks(). Both twins must reproduce it exactly.
Also held here: Python/GAS HTML parity, the hidden table, the aria label, direction not shown by colour alone, the motion
index, malformed steps, the checkpoint-total note, the `version` field, escaping and registration.
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
D = json.loads((ROOT / "tests/fixtures/waterfall_d3_golden.json").read_text())
CASES = {**D["golden"], **{f"fuzz{i}": c for i, c in enumerate(D["fuzz"])}}


def _wf(c, labels=None, **kw):
    steps = []
    for k, st in enumerate(c["steps"]):
        s = dict(st)
        s["label"] = labels[k] if labels and k < len(labels) else "Step %d" % (k + 1)
        steps.append(s)
    b = {"type": "waterfall", "steps": steps}
    b.update(kw)
    return b


# ─── the layout against real d3 ────────────────────────────────────────────────
@pytest.mark.parametrize("name", list(CASES))
def test_python_bars_and_axis_match_d3_exactly(name):
    c = CASES[name]
    bars, domain, ticks, _ = wa._wf_layout(c["steps"])
    assert [list(x) for x in bars] == c["bars"] and list(domain) == c["domain"] and ticks == c["ticks"]


def test_gas_bars_and_axis_match_d3_exactly(core_js):
    names = list(CASES)
    res = _node(core_js, "var G = " + json.dumps([CASES[n]["steps"] for n in names]) +
                "; console.log(JSON.stringify(G.map(function(g){ return _wfLayout(g).slice(0, 3); })));")
    for n, (bars, domain, ticks) in zip(names, res):
        assert bars == CASES[n]["bars"] and domain == CASES[n]["domain"] and ticks == CASES[n]["ticks"], n


def test_the_golden_set_covers_the_hard_cases():
    g = D["golden"]
    assert g["crosses_zero"]["domain"][0] < 0 < g["crosses_zero"]["domain"][1]
    assert g["decimals_noise"]["bars"][1][1] == 0.30000000000000004                       # left-to-right double sums, noise and all
    assert g["zeros"]["domain"] == [0, 0] and g["zeros"]["ticks"] == [0]
    assert g["checkpoint_mismatch"]["bars"][2] == [0, 120] and g["checkpoint_mismatch"]["bars"][3] == [120, 115]
    assert len(g["twenty_four"]["steps"]) == 24


# ─── rendering ─────────────────────────────────────────────────────────────────
PAYLOADS = {
    "pnl": _wf(CASES["pnl"], ["Revenue 2025", "New customers", "Churn", "Price rise", "Discounts", "Revenue 2026"], title="Revenue bridge", x_label="Revenue", unit="kEUR"),
    "all_down": _wf(CASES["all_down"]),
    "crosses_zero": _wf(CASES["crosses_zero"], unit="C"),
    "only_deltas": _wf(CASES["only_deltas"]),
    "noise": _wf(CASES["decimals_noise"]),
    "zeros": _wf(CASES["zeros"]),
    "big": _wf(CASES["big"], unit="people"),
    "tiny": _wf(CASES["tiny"], unit="V"),
    "mismatch": _wf(CASES["checkpoint_mismatch"], ["Start", "Growth", "Reported Q2", "Refunds", "End"]),
    "twenty_four": _wf(CASES["twenty_four"], ["A rather long step label here"]),
    "malformed": {"type": "waterfall", "steps": [None, 7, "x", {"label": "Good", "value": 5}, {"label": "Text value", "value": "6"}, {"label": "Huge", "value": 1e30},
                                                 {"value": 2}, {"label": "Bool", "value": True}, {"label": "Sum", "kind": "total", "value": "9"}]},
    "no_steps": {"type": "waterfall", "title": "T"},
    "steps_not_a_list": {"type": "waterfall", "steps": {"label": "x", "value": 1}},
    "none_usable": {"type": "waterfall", "steps": [{"label": "a"}, {"label": "b", "value": None}]},
    "twenty_five": {"type": "waterfall", "steps": [{"label": "S%d" % k, "value": k} for k in range(25)]},
    "unknown_kind": {"type": "waterfall", "steps": [{"label": "a", "value": 3, "kind": "subtotal"}, {"label": "b", "value": 2}]},
    "version_2": dict(_wf(CASES["only_deltas"]), version=2),
    "version_junk": dict(_wf(CASES["only_deltas"]), version="2"),
}


@pytest.mark.parametrize("name", list(PAYLOADS))
def test_python_and_gas_emit_identical_html(name, core_js):
    assert _py(PAYLOADS[name]) == _gas_batch(core_js, [PAYLOADS[name]])[0]


def test_hidden_table_gives_each_change_and_the_running_total(core_js):
    for html in (_py(PAYLOADS["pnl"]), _gas_batch(core_js, [PAYLOADS["pnl"]])[0]):
        head, rows = _table(html)
        assert head == ["Step", "Change", "Running total"]
        assert rows == [["Revenue 2025", "Total", "120 kEUR"], ["New customers", "+40 kEUR", "160 kEUR"], ["Churn", "-25 kEUR", "135 kEUR"],
                        ["Price rise", "+12.5 kEUR", "147.5 kEUR"], ["Discounts", "-7.25 kEUR", "140.25 kEUR"], ["Revenue 2026", "Total", "140.25 kEUR"]]
        t = html.index("<table")
        assert 'role="img"' in html[:t] and 'role="img"' not in html[t:]


def test_float_noise_never_reaches_the_reader():
    h = _py(PAYLOADS["noise"])
    _, rows = _table(h)
    assert [r[2] for r in rows] == ["0.1", "0.3", "0.3", "0", "0"]
    assert "0000000" not in h.replace("1000.00", "") and "e-17" not in h
    assert "add up to" not in h                                                          # 0.1 + 0.2 is 0.3 here: no false checkpoint note


def test_aria_label_gives_the_end_and_the_biggest_moves(core_js):
    for html in (_py(PAYLOADS["pnl"]), _gas_batch(core_js, [PAYLOADS["pnl"]])[0]):
        a = re.search(r'role="img" aria-label="([^"]*)"', html).group(1)
        assert a == "Waterfall of 6 steps ending at 140.25 kEUR. Biggest increase: New customers, +40 kEUR. Biggest decrease: Churn, -25 kEUR."
    a = re.search(r'role="img" aria-label="([^"]*)"', _py(PAYLOADS["only_deltas"])).group(1)
    assert a == "Waterfall of 3 steps ending at 6. Biggest increase: Step 3, +3."


def test_direction_is_not_shown_by_colour_alone(core_js):
    for html in (_py(PAYLOADS["pnl"]), _gas_batch(core_js, [PAYLOADS["pnl"]])[0]):
        kinds = re.findall(r'<div class="wfb (wf[tud])"', html)
        assert kinds == ["wft", "wfu", "wfd", "wfu", "wfd", "wft"]
        vals = re.findall(r'<div class="wfv"[^>]*>([^<]*)</div>', html)
        assert vals == ["120", "+40", "-25", "+12.5", "-7.25", "140.25"]


def test_bars_and_connectors_sit_where_the_layout_says(core_js):
    b = PAYLOADS["crosses_zero"]
    bars, (x0, x1), _, _ = wa._wf_layout(b["steps"])
    pct = lambda v: round((v - x0) / (x1 - x0) * 100, 3)
    for html in (_py(b), _gas_batch(core_js, [b])[0]):
        got = [(float(l), float(w)) for l, w in re.findall(r'<div class="wfb wf[tud]" style="position:absolute;left:([\d.]+)%;width:([\d.]+)%;', html)]
        for (l, w), (a, e) in zip(got, bars):
            assert abs(l - pct(min(a, e))) < 0.001 and abs(l + w - pct(max(a, e))) < 0.002
        cons = [float(x) for x in re.findall(r'<div class="wfc" style="position:absolute;left:([\d.]+)%;', html)]
        assert cons == [pct(e) for _, e in bars[:-1]]


def test_zero_width_axis_draws_without_nan(core_js):
    for h in (_py(PAYLOADS["zeros"]), _gas_batch(core_js, [PAYLOADS["zeros"]])[0]):
        assert "NaN" not in h and "Infinity" not in h and "undefined" not in h
        assert h.count('<div class="wfb wf') == 3 and 'left:50%' in h


def test_motion_index_per_step_stays_inside_its_clamp(core_js):
    for html in (_py(PAYLOADS["twenty_four"]), _gas_batch(core_js, [PAYLOADS["twenty_four"]])[0]):
        ks = re.findall(r'<div class="wfg" style="position:absolute;inset:0;--k:clamp\(0,calc\(var\(--p,1\)\*(\d+) - (\d+)\),1\);', html)
        assert [int(i) for _, i in ks] == list(range(24)) and all(int(n) == 25 for n, _ in ks)


def test_a_checkpoint_total_that_disagrees_is_drawn_and_called_out(core_js):
    for h in (_py(PAYLOADS["mismatch"]), _gas_batch(core_js, [PAYLOADS["mismatch"]])[0]):
        assert "The total &quot;Reported Q2&quot; is 120 but the steps before it add up to 110; the bar shows 120 and later steps start there." in h
        assert [r[2] for r in _table(h)[1]] == ["100", "110", "120", "115", "115"]
        # the opening total sets the start: nothing comes before it, so there is nothing to disagree with
        assert h.count("add up to") == 1
    for name in ("pnl",):
        assert "add up to" not in _py(PAYLOADS[name])
    import generate_atom_pages as g
    assert "add up to" not in _py(g._EXAMPLE_BLOCKS["waterfall"])


def test_malformed_steps_are_skipped_and_explained(core_js):
    for h in (_py(PAYLOADS["malformed"]), _gas_batch(core_js, [PAYLOADS["malformed"]])[0]):
        _, rows = _table(h)
        # a total whose value is not a number is still a total: it shows the running total
        assert [r[0] for r in rows] == ["Good", "Step 7", "Sum"] and [r[2] for r in rows] == ["5", "7", "7"]
        assert "6 steps had no usable number or were not a step and were left out." in h
        assert "NaN" not in h and "undefined" not in h and "[object Object]" not in h


def test_no_usable_step_gives_a_clear_note_and_no_chart():
    for k in ("no_steps", "steps_not_a_list", "none_usable"):
        h = _py(PAYLOADS[k])
        assert "A waterfall needs at least one step with a number." in h
        assert 'role="img"' not in h and "<table" not in h and "NaN" not in h
    assert ">T</div>" in _py(PAYLOADS["no_steps"])


def test_only_the_first_twenty_four_steps_are_read():
    h = _py(PAYLOADS["twenty_five"])
    assert len(_table(h)[1]) == 24 and "1 step beyond the first 24 was not drawn." in h


def test_an_unknown_kind_is_a_delta():
    assert _py(PAYLOADS["unknown_kind"]) == _py({"type": "waterfall", "steps": [{"label": "a", "value": 3}, {"label": "b", "value": 2}]})


def test_version_above_one_is_noted_and_otherwise_silent(core_js):
    for h in (_py(PAYLOADS["version_2"]), _gas_batch(core_js, [PAYLOADS["version_2"]])[0]):
        assert "Written for waterfall version 2; drawn as version 1." in h
    assert "version" not in _py(PAYLOADS["version_junk"]).lower()


def test_hostile_text_is_escaped_in_both_twins(core_js):
    b = {"type": "waterfall", "title": ATTACK, "x_label": ATTACK, "unit": ATTACK, "steps": [{"label": ATTACK, "value": 1}, {"label": ATTACK, "kind": "total", "value": 3}]}
    for h in (_py(b), _gas_batch(core_js, [b])[0]):
        assert "<img" not in h and "<script" not in h.replace("<style", "") and 'onerror=alert(1)>' not in h.replace("&gt;", "")


# ─── registration ─────────────────────────────────────────────────────────────
def test_registered_as_a_preview_charts_atom_with_an_example_and_every_field_documented():
    blocks = {a["type"]: a for a in yaml.safe_load((ROOT / "atoms/schema.yaml").read_text())["blocks"]}
    a = blocks["waterfall"]
    assert a["stage"] == "preview" and set(a["fields"]) == {"title", "steps", "x_label", "unit", "version"}
    assert a["surfaces"] == blocks["treemap"]["surfaces"] and a["source"] == blocks["treemap"]["source"]
    assert re.search(r"^a2ui-charts-v1:\n(?:- .*\n)*- waterfall$", (ROOT / "atoms/atom-packs.yaml").read_text(), re.M)
    assert '"waterfall":"a2ui-charts-v1"' in (ROOT / "apps-script-surface/gas-wired-renderer/PackMap.gs").read_text()
    import generate_atom_pages as g
    ex = g._EXAMPLE_BLOCKS["waterfall"]
    assert ex["type"] == "waterfall" and "<table" in _py(ex)


def test_d3_array_credit_names_the_waterfall():
    t = (ROOT / "THIRD-PARTY-NOTICES.md").read_text()
    assert "tests/test_waterfall.py" in t
