"""candlestick_chart (Plotly candlestick + ohlc): open/high/low/close bars on a date axis, optional volume panel.

GOLDEN (tests/fixtures/candlestick_d3_golden.json, from candlestick_d3_golden_gen.mjs) holds the date-axis ticks and labels from the
REAL d3-scale 4.0.2 scaleUtc().ticks()/tickFormat() (d3-time 3.1.0 utcTicks, d3-time-format 4.1.0 utcFormat). Both twins must
reproduce it exactly (integer milliseconds and label strings, so == is exact). The price and volume axes reuse the histogram's d3-array
nice()/ticks() port, which has its own golden (test_histogram).
Also held: Python/GAS HTML parity, the hidden table, the aria label, direction not shown by colour alone (hollow vs filled body, thin vs
thick bar), the motion index, malformed input, caps with notes, the `version` note, escaping and registration.
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
D = json.loads((ROOT / "tests/fixtures/candlestick_d3_golden.json").read_text())
CASES = {**D["golden"], **{f"fuzz{i}": c for i, c in enumerate(D["fuzz"])}}


# ─── the date axis against real d3 ─────────────────────────────────────────────
@pytest.mark.parametrize("name", list(CASES))
def test_python_date_axis_matches_d3_exactly(name):
    c = CASES[name]
    ticks, labels = wa._cs_axis(c["start"], c["stop"], c["count"])
    assert ticks == c["ticks"] and labels == c["labels"]


def test_gas_date_axis_matches_d3_exactly(core_js):
    names = list(CASES)
    res = _node(core_js, "var G = " + json.dumps([[CASES[n]["start"], CASES[n]["stop"], CASES[n]["count"]] for n in names]) +
                "; console.log(JSON.stringify(G.map(function(g){ return _csAxis(g[0], g[1], g[2]); })));")
    for n, (ticks, labels) in zip(names, res):
        assert ticks == CASES[n]["ticks"] and labels == CASES[n]["labels"], n


def test_the_golden_set_covers_every_tick_interval():
    g = D["golden"]
    assert g["ms"]["labels"][1] == ".001" and g["seconds"]["labels"][1] == ":05" and g["minutes"]["labels"][1] == "10:15"
    assert g["hours"]["labels"][2] == "12 PM" and g["days_two_weeks"]["labels"][0] == "Tue 27" and g["weekly_span"]["labels"][0] == "Jan 07"
    assert g["months_one_year"]["labels"][0] == "April" and g["years_decade"]["labels"][0] == "2012" and g["leap_day"]["labels"][3] == "March"
    assert g["pre_epoch"]["ticks"][0] < 0 and g["same_instant"]["ticks"] == [CASES["same_instant"]["start"]]


PARSE = {
    "2024-03-05": 1709596800000, "2024-03-05T10:30": 1709634600000, "2024-03-05 10:30:15": 1709634615000,
    "2024-03-05T10:30:15.250Z": 1709634615250, "  2024-03-05  ": 1709596800000, "1969-12-31": -86400000, "2024-02-29": 1709164800000,
}


@pytest.mark.parametrize("s,ms", list(PARSE.items()))
def test_dates_parse_as_utc(s, ms, core_js):
    assert wa._cs_parse(s) == ms
    assert _node(core_js, "console.log(JSON.stringify(_csParse(%s)));" % json.dumps(s)) == ms


@pytest.mark.parametrize("s", ["", "2024-13-01", "2024-02-30", "2023-02-29", "24-03-05", "2024-03-05T25:00", "2024-3-5", "yesterday", "2024-03-05T10:30+02:00", "0999-01-01", None, 5, True, [], {}])
def test_bad_dates_are_none(s, core_js):
    assert wa._cs_parse(s) is None
    assert _node(core_js, "console.log(JSON.stringify(_csParse(%s)));" % json.dumps(s)) is None


# ─── rendering ─────────────────────────────────────────────────────────────────
def _series(n, start_day=0, step=1, seed=7, base=100.0):
    """n daily bars, deterministic: dates, open, high, low, close, volume."""
    import datetime as dt
    s, price = seed, base
    out = {"dates": [], "open": [], "high": [], "low": [], "close": [], "volume": []}
    for k in range(n):
        s = (s * 1103515245 + 12345) % 2147483648
        r1 = s / 2147483648
        s = (s * 1103515245 + 12345) % 2147483648
        r2 = s / 2147483648
        o = round(price, 2)
        c = round(price + (r1 - 0.5) * 4, 2)
        out["dates"].append((dt.date(2024, 1, 1) + dt.timedelta(days=start_day + k * step)).isoformat())
        out["open"].append(o)
        out["close"].append(c)
        out["high"].append(round(max(o, c) + r2 * 1.5, 2))
        out["low"].append(round(min(o, c) - r1 * 1.5, 2))
        out["volume"].append(int(1000 + r2 * 9000))
        price = c
    return out


def _cs(n=30, **kw):
    b = {"type": "candlestick_chart", **_series(n)}
    b.update(kw)
    return b


SMALL = {"type": "candlestick_chart", "title": "Share price", "unit": "USD", "y_label": "Price",
         "dates": ["2024-03-04", "2024-03-05", "2024-03-06"], "open": [10, 12, 11.5], "high": [13, 12.75, 12], "low": [9.5, 10.5, 10],
         "close": [12, 11, 11.75], "volume": [1500, 2200, 900]}
PAYLOADS = {
    "small": SMALL,
    "small_ohlc": dict(SMALL, style="ohlc"),
    "thirty": _cs(30),
    "thirty_ohlc": _cs(30, style="ohlc"),
    "no_volume": {k: v for k, v in _cs(40).items() if k != "volume"},
    "hundred": _cs(100, title="Hundred days", unit="EUR"),
    "full_cap": _cs(250),
    "weekly": dict(_cs(52), **{k: v for k, v in _series(52, step=7).items()}),
    "intraday": {"type": "candlestick_chart", "dates": ["2024-03-05T%02d:%02d" % (9 + m // 60, m % 60) for m in range(30, 330, 30)],
                 "open": [5, 5.1, 5.2, 5.1, 5, 5.2, 5.3, 5.2, 5.1, 5.15], "high": [5.2] * 10, "low": [4.9] * 10, "close": [5.1, 5.2, 5.1, 5, 5.2, 5.3, 5.2, 5.1, 5.15, 5.2]},
    "one_bar": {"type": "candlestick_chart", "dates": ["2024-03-04"], "open": [10], "high": [12], "low": [9], "close": [11], "volume": [100]},
    "flat": {"type": "candlestick_chart", "dates": ["2024-03-04", "2024-03-05"], "open": [10, 10], "high": [10, 10], "low": [10, 10], "close": [10, 10]},
    "doji": {"type": "candlestick_chart", "dates": ["2024-03-04", "2024-03-05", "2024-03-06"], "open": [10, 11, 10], "high": [12, 12, 11], "low": [9, 10, 9], "close": [10, 11, 10]},
    "big": {"type": "candlestick_chart", "dates": ["2024-03-04", "2024-03-05"], "open": [1.2e9, 1.3e9], "high": [1.4e9, 1.4e9], "low": [1e9, 1.2e9], "close": [1.3e9, 1.25e9], "volume": [3e12, 4e12]},
    "tiny": {"type": "candlestick_chart", "dates": ["2024-03-04", "2024-03-05"], "open": [0.0012, 0.0013], "high": [0.0015, 0.0014], "low": [0.001, 0.0012], "close": [0.0013, 0.00125]},
    "negative": {"type": "candlestick_chart", "dates": ["2024-03-04", "2024-03-05", "2024-03-08"], "open": [-2, -1, 1], "high": [0, 1, 3], "low": [-4, -2, 0], "close": [-1, 1, 2]},
    "unsorted": {"type": "candlestick_chart", "dates": ["2024-03-06", "2024-03-04", "2024-03-05"], "open": [3, 1, 2], "high": [4, 2, 3], "low": [2, 0, 1], "close": [3.5, 1.5, 2.5]},
    "years": {"type": "candlestick_chart", "dates": ["2015-01-02", "2017-06-01", "2020-01-02", "2024-01-02"], "open": [1, 2, 3, 4], "high": [3, 4, 5, 6], "low": [0, 1, 2, 3], "close": [2, 3, 4, 5]},
    "malformed": {"type": "candlestick_chart", "dates": ["2024-03-04", "bad", "2024-03-06", None, "2024-03-08", "2024-03-09", "2024-03-10", "2024-03-11"],
                  "open": [1, 2, "3", 4, 5, 6, 7, 8], "high": [2, 3, 4, 5, 3, 7, 8, 9], "low": [0, 1, 2, 3, 4, 5, 6, 7], "close": [1.5, 2.5, 3.5, 4.5, 5, 6.5, 7, 1e30],
                  "volume": [10, 20, 30, 40, 50, "x", -5, 80]},
    "inconsistent": {"type": "candlestick_chart", "dates": ["2024-03-04", "2024-03-05"], "open": [1, 2], "high": [0.5, 1], "low": [0, 0], "close": [1.5, 3]},
    "no_dates": {"type": "candlestick_chart", "title": "T", "open": [1], "high": [2], "low": [0], "close": [1]},
    "not_lists": {"type": "candlestick_chart", "dates": "2024-03-04", "open": 1, "high": {"a": 1}, "low": None, "close": True},
    "none_usable": {"type": "candlestick_chart", "dates": ["x", "y"], "open": [1, 2], "high": [1, 2], "low": [1, 2], "close": [1, 2]},
    "short_arrays": {"type": "candlestick_chart", "dates": ["2024-03-04", "2024-03-05", "2024-03-06"], "open": [1, 2], "high": [2, 3], "low": [0, 1], "close": [1, 2]},
    "volume_gaps": {"type": "candlestick_chart", "dates": ["2024-03-04", "2024-03-05", "2024-03-06"], "open": [1, 2, 3], "high": [2, 3, 4], "low": [0, 1, 2], "close": [1.5, 2.5, 2.5], "volume": [10, None, 30]},
    "bad_style": dict(SMALL, style="spiral"),
    "version_2": dict(SMALL, version=2),
    "version_junk": dict(SMALL, version="2"),
}


@pytest.mark.parametrize("name", list(PAYLOADS))
def test_python_and_gas_emit_identical_html(name, core_js):
    assert _py(PAYLOADS[name]) == _gas_batch(core_js, [PAYLOADS[name]])[0]


def test_hidden_table_gives_every_value(core_js):
    for html in (_py(SMALL), _gas_batch(core_js, [SMALL])[0]):
        head, rows = _table(html)
        assert head == ["Date", "Open", "High", "Low", "Close", "Direction", "Volume"]
        assert rows == [["2024-03-04", "10 USD", "13 USD", "9.5 USD", "12 USD", "Up", "1,500"],
                        ["2024-03-05", "12 USD", "12.75 USD", "10.5 USD", "11 USD", "Down", "2,200"],
                        ["2024-03-06", "11.5 USD", "12 USD", "10 USD", "11.75 USD", "Up", "900"]]
        t = html.index("<table")
        assert 'role="img"' in html[:t] and 'role="img"' not in html[t:]
    head, rows = _table(_py(PAYLOADS["no_volume"]))
    assert head == ["Date", "Open", "High", "Low", "Close", "Direction"] and len(rows) == 40
    assert _table(_py(PAYLOADS["volume_gaps"]))[1][1][-1] == "none"


def test_aria_label_states_the_gist(core_js):
    for html in (_py(SMALL), _gas_batch(core_js, [SMALL])[0]):
        a = re.search(r'role="img" aria-label="([^"]*)"', html).group(1)
        assert a == ("Candlestick chart of 3 bars from 2024-03-04 to 2024-03-06 in USD. First open 10, last close 11.75, change +1.75 (+17.5%). "
                     "Highest high 13 on 2024-03-04, lowest low 9.5 on 2024-03-04. 2 up, 1 down.")
    a = re.search(r'role="img" aria-label="([^"]*)"', _py(PAYLOADS["small_ohlc"])).group(1)
    assert a.startswith("OHLC bar chart of 3 bars")


def test_direction_is_never_colour_only(core_js):
    for html in (_py(SMALL), _gas_batch(core_js, [SMALL])[0]):
        kinds = re.findall(r'<div class="csc (cs[ud])"', html)
        assert kinds == ["csu", "csd", "csu"]
        # hollow up body (page surface) and filled down body, plus the words in the legend and the table
        assert re.search(r'class="csb csu" style="[^"]*background:var\(--surface,#FFFFFF\)', html)
        assert re.search(r'class="csb csd" style="[^"]*background:var\(--negative,#B91C1C\)', html)
        assert "Up: close at or above open (hollow)" in html and "Down: close below open (filled)" in html
    h = _py(PAYLOADS["small_ohlc"])
    assert "Up: close at or above open (thin bar)" in h and "Down: close below open (thick bar)" in h
    assert h.count('class="cso csu"') == 2 and h.count('class="cso csd"') == 1


def test_candles_sit_where_the_scales_say(core_js):
    b = SMALL
    Y0, Y1 = wa._hg_nice(9.5, 13, 5)
    for html in (_py(b), _gas_batch(core_js, [b])[0]):
        tops = [(float(t), float(h)) for t, h in re.findall(r'class="cs[ko][^"]*" style="position:absolute;left:[^;]*;width:[^;]*;top:([\d.]+)%;height:([\d.]+)%;', html)]
        assert len(tops) == 3
        for (t, h), (hi, lo) in zip(tops, [(13, 9.5), (12.75, 10.5), (12, 10)]):
            assert abs(t - (Y1 - hi) / (Y1 - Y0) * 100) < 0.001 and abs(t + h - (Y1 - lo) / (Y1 - Y0) * 100) < 0.002


def test_a_doji_still_has_a_visible_body():
    h = _py(PAYLOADS["doji"])
    assert h.count("min-height:2px") >= 3 and "NaN" not in h


def test_bars_are_drawn_in_date_order():
    a = _table(_py(PAYLOADS["unsorted"]))[1]
    assert [r[0] for r in a] == ["2024-03-04", "2024-03-05", "2024-03-06"] and [r[1] for r in a] == ["1", "2", "3"]


def test_date_axis_labels_come_from_the_d3_ticks(core_js):
    for html in (_py(PAYLOADS["thirty"]), _gas_batch(core_js, [PAYLOADS["thirty"]])[0]):
        labs = re.findall(r'<div style="position:absolute;left:0;top:10px;transform:translateX\(-50%\);[^"]*">([^<]*)</div>', html)
        assert labs and all(re.fullmatch(r"[A-Z][a-z]{2} \d\d|[A-Z][a-z]+|\d{4}", s) for s in labs), labs
    for name, first in (("years", "2016"), ("intraday", "10 AM")):
        h = _py(PAYLOADS[name])
        assert (">" + first + "<") in h


def test_zero_height_and_one_bar_axes_draw_without_nan(core_js):
    for name in ("one_bar", "flat", "doji"):
        for h in (_py(PAYLOADS[name]), _gas_batch(core_js, [PAYLOADS[name]])[0]):
            assert "NaN" not in h and "Infinity" not in h and "undefined" not in h and "[object Object]" not in h
            assert h.count('class="csc cs') == len(_table(h)[1])


def test_volume_panel_only_when_volume_is_given(core_js):
    assert 'class="csv ' in _py(SMALL) and 'class="csv ' not in _py(PAYLOADS["no_volume"])
    assert _py(PAYLOADS["volume_gaps"]).count('class="csv ') == 2
    h = _py(PAYLOADS["malformed"])
    assert "NaN" not in h


def test_motion_index_per_bar_stays_inside_its_clamp(core_js):
    for html in (_py(PAYLOADS["thirty"]), _gas_batch(core_js, [PAYLOADS["thirty"]])[0]):
        ks = re.findall(r'class="csc cs[ud]" style="[^"]*--k:clamp\(0,calc\(var\(--p,1\)\*(\d+) - (\d+)\),1\);', html)
        assert [int(i) for _, i in ks] == list(range(30)) and all(int(n) == 31 for n, _ in ks)


def test_caps_are_noted_not_silent(core_js):
    h = _py(_cs(251))
    assert len(_table(h)[1]) == 250 and "1 bar beyond the first 250 was not drawn." in h
    h = _py(_cs(260))
    assert "10 bars beyond the first 250 were not drawn." in h
    assert "beyond" not in _py(PAYLOADS["full_cap"])
    # the first 250 by date are kept
    assert _table(h)[1][-1][0] == _series(250)["dates"][-1]


def test_malformed_bars_are_left_out_and_explained(core_js):
    for h in (_py(PAYLOADS["malformed"]), _gas_batch(core_js, [PAYLOADS["malformed"]])[0]):
        _, rows = _table(h)
        assert [r[0] for r in rows] == ["2024-03-04", "2024-03-09", "2024-03-10"]
        assert "5 bars had a missing date, a missing number or prices that do not fit together and were left out." in h
        assert "2 volumes were missing, negative or not a number and were left out." in h
        assert "NaN" not in h and "undefined" not in h and "[object Object]" not in h
    h = _py(PAYLOADS["inconsistent"])
    assert "2 bars had a missing date" in h and 'role="img"' not in h


def test_no_usable_bar_gives_a_clear_note_and_no_chart():
    for k in ("no_dates", "not_lists", "none_usable", "inconsistent"):
        h = _py(PAYLOADS[k])
        assert "A candlestick chart needs at least one bar with a date and open, high, low and close numbers." in h
        assert 'role="img"' not in h and "<table" not in h and "NaN" not in h
    assert ">T</div>" in _py(PAYLOADS["no_dates"])


def test_arrays_of_different_length_use_the_shortest_complete_bars():
    _, rows = _table(_py(PAYLOADS["short_arrays"]))
    assert len(rows) == 2 and "1 bar had a missing date" in _py(PAYLOADS["short_arrays"])


def test_unknown_style_is_a_candle_chart():
    assert _py(PAYLOADS["bad_style"]) == _py(SMALL)


def test_version_above_one_is_noted_and_otherwise_silent(core_js):
    for h in (_py(PAYLOADS["version_2"]), _gas_batch(core_js, [PAYLOADS["version_2"]])[0]):
        assert "Written for candlestick_chart version 2; drawn as version 1." in h
    assert "version" not in _py(PAYLOADS["version_junk"]).lower()


def test_hostile_text_is_escaped_in_both_twins(core_js):
    b = dict(SMALL, title=ATTACK, unit=ATTACK, y_label=ATTACK)
    b["dates"] = ["2024-03-04", ATTACK, "2024-03-06"]
    for h in (_py(b), _gas_batch(core_js, [b])[0]):
        assert "<img" not in h and "<script" not in h.replace("<style", "") and 'onerror=alert(1)>' not in h.replace("&gt;", "")


def test_extremes_are_caught_by_the_number_guard():
    h = _py(PAYLOADS["big"])
    assert "NaN" not in h and "e+" not in h and "Infinity" not in h
    assert _table(_py(PAYLOADS["tiny"]))[1][0][1] == "0.0012"


# ─── registration ─────────────────────────────────────────────────────────────
def test_registered_as_a_preview_atom_in_the_charts_pack():
    s = yaml.safe_load((ROOT / "atoms/schema.yaml").read_text())
    atom = [a for a in s["blocks"] if a.get("type") == "candlestick_chart"]
    assert len(atom) == 1 and atom[0]["stage"] == "preview"
    for k in ("description", "compact_description", "routing_text", "intent_phrases", "fields", "notes", "surfaces", "source"):
        assert atom[0].get(k), k
    assert len(atom[0]["intent_phrases"]) == 3 and "version" in atom[0]["fields"]
    packs = yaml.safe_load((ROOT / "atoms/atom-packs.yaml").read_text())
    assert "candlestick_chart" in json.dumps(packs.get("a2ui-charts-v1", packs))
    assert '"candlestick_chart":"a2ui-charts-v1"' in (ROOT / "apps-script-surface/gas-wired-renderer/PackMap.gs").read_text()
    import generate_atom_pages as g
    assert "candlestick_chart" in g._EXAMPLE_BLOCKS and "<table" in _py(g._EXAMPLE_BLOCKS["candlestick_chart"])
    assert "d3-time-format" in (ROOT / "THIRD-PARTY-NOTICES.md").read_text()


# ─── review round 2 (C1 Unicode digits, C2 narrow axis, C3 volume wording) ─────
@pytest.mark.parametrize("s", ["２０２４-０１-０１", "٢٠٢٤-٠١-٠١", "2024-０１-01", "2024-01-01T１０:30"])
def test_non_ascii_digits_are_not_dates_in_either_twin(s, core_js):
    assert wa._cs_parse(s) is None
    assert _node(core_js, "console.log(JSON.stringify(_csParse(%s)));" % json.dumps(s)) is None


def test_non_ascii_digit_dates_render_identically(core_js):
    b = {**SMALL, "dates": ["２０２４-０１-０１", "2024-01-02", "2024-01-03"]}
    py, gas = _py(b), _gas_batch(core_js, [b])[0]
    assert py == gas
    assert "２０２４" not in re.sub(r"<table.*", "", py, flags=re.S) and "of 2 bars" in py


def _narrow_labels(html):
    """The x labels left visible by the narrow-container rule (every .hgx without .hgc is hidden at <= 560px)."""
    return [re.sub(r"<[^>]+>", "", m) for m in re.findall(r'<div class="hgx hgc"[^>]*>.*?top:10px;[^>]*>([^<]*)</div>', html)]


def test_narrow_axis_keeps_a_date_label_for_midnight_bars(core_js):
    b = {**SMALL, "volume": None}
    for html in (_py(b), _gas_batch(core_js, [b])[0]):
        labs = _narrow_labels(html)
        assert labs and not any(re.fullmatch(r"\d\d? [AP]M", s) for s in labs), labs


def test_volume_note_names_negative_volumes(core_js):
    b = {**SMALL, "volume": [1500, -1, 900]}
    for html in (_py(b), _gas_batch(core_js, [b])[0]):
        assert "missing, negative or not a number" in html
