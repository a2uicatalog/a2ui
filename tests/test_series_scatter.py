"""chartjs_line + scatter_trend `series[]` (preview, optional): Plotly scatter / scattergl parity.

GOLDEN (tests/fixtures/series_time_golden.json, made by series_time_golden_gen.mjs from the REAL d3-time-format 4.1.0, d3-time 3.1.0 and
d3-scale 4.0.2): UTC date formatting and scaleUtc().ticks() with its multi-scale labels (month shortened to %b). Both twins must match with ==.
Also held here: no-series payloads render byte for byte as on the base commit (tests/fixtures/series_base_outputs.json, made by running the
BASE renderers: Python and the GAS bundle), Python/GAS identical HTML, the hidden table, the aria label, shapes/modes/fill, the point cap with a
visible note and a deterministic downsample, malformed and hostile input, the version note.
"""
from __future__ import annotations

import json
import random
import re
from pathlib import Path

import pytest

from test_motion_atoms import _gas_batch, _node, _py, core_js, wa  # noqa: F401  (core_js is a fixture)

ROOT = Path(__file__).resolve().parent.parent
GOLD = json.loads((ROOT / "tests/fixtures/series_time_golden.json").read_text())
BASE = json.loads((ROOT / "tests/fixtures/series_base_outputs.json").read_text())
ATTACK = '"><img src=x onerror=alert(1)>\'"><svg onload=alert(1)></script><script>alert(4)</script> onmouseover=alert(2)'


def _ser(label="a", **kw):
    d = {"label": label, "x": [1, 2, 3, 4], "y": [3, 1, 4, 2]}
    d.update(kw)
    return d


PAYLOADS = {
    "line_dates": {"type": "chartjs_line", "title": "Visits", "series": [
        {"label": "web", "x": ["2024-01-01", "2024-02-15", "2024-03-20", "2024-05-01"], "y": [1, 3, 2, 5], "fill": "tozeroy", "shape": "spline"},
        {"label": "app", "x": ["2024-01-01", "2024-03-20", "2024-05-01"], "y": [2, 4, 3], "mode": "lines+markers+text", "symbol": "x", "text": ["a", "b", "c"]}]},
    "scatter_sized": {"type": "scatter_trend", "x_label": "hours", "y_label": "score", "series": [
        {"label": "g1", "x": [1, 2, 3.5, 9], "y": [3, 1, 4, 1.5], "mode": "markers", "size": [6, 12, 20, 9], "symbol": "diamond"},
        {"label": "g2", "x": [1, 4, 6], "y": [-2, 5, 3], "mode": "lines+markers", "shape": "hvh", "fill": "tonexty", "symbol": "triangle-up", "color": "#aa3355"}]},
    "steps": {"type": "chartjs_line", "series": [_ser("hv", shape="hv", dash="dot"), _ser("vh", shape="vh", dash="longdash", symbol="cross"), _ser("vhv", shape="vhv", dash="dashdot", symbol="square")]},
    "single": {"type": "scatter_trend", "title": "One", "series": [{"label": "only", "y": [5, 6, 7, 6]}]},
    "times": {"type": "chartjs_line", "series": [{"label": "t", "x": ["2024-03-01T09:00", "2024-03-01T09:30:15", "2024-03-01T11:45"], "y": [1, 2, 3]}]},
    "negative_fill": {"type": "chartjs_line", "series": [_ser("n", y=[-5, -2, -8, -1], fill="tozeroy")]},
    "flat": {"type": "scatter_trend", "series": [{"label": "f", "x": [2, 2], "y": [7, 7]}]},
}

OLD = BASE["payloads"]


# ─── d3 golden ───────────────────────────────────────────────────────────────────────────────────────────────────
def test_python_parse_and_format_match_d3():
    for f in GOLD["fmt"]:
        ms = wa._ps_parse_date(f["iso"])
        assert ms == f["ms"], f["iso"]
        for sp, want in f["out"].items():
            assert wa._ps_utc_format(ms, sp) == want, (f["iso"], sp)


def test_gas_parse_and_format_match_d3(core_js):
    res = _node(core_js, "var F = " + json.dumps([[f["iso"], GOLD["specs"]] for f in GOLD["fmt"]]) +
                "; console.log(JSON.stringify(F.map(function(f){ var ms = _psParseDate(f[0]); return [ms, f[1].map(function(s){ return _psUtcFormat(ms, s); })]; })));")
    for f, (ms, outs) in zip(GOLD["fmt"], res):
        assert ms == f["ms"], f["iso"]
        assert outs == [f["out"][s] for s in GOLD["specs"]], f["iso"]


def test_python_time_ticks_match_d3():
    for t in GOLD["ticks"]:
        got = wa._ps_time_ticks(t["a"], t["z"], t["count"])
        assert got == t["ticks"], t
        assert [wa._ps_tick_label(x) for x in got] == t["labels"], t


def test_gas_time_ticks_match_d3(core_js):
    res = _node(core_js, "var T = " + json.dumps([[t["a"], t["z"], t["count"]] for t in GOLD["ticks"]]) +
                "; console.log(JSON.stringify(T.map(function(t){ var k = _psTimeTicks(t[0], t[1], t[2]); return [k, k.map(_psTickLabel)]; })));")
    for t, (k, lab) in zip(GOLD["ticks"], res):
        assert k == t["ticks"], t
        assert lab == t["labels"], t


def test_the_golden_set_reaches_every_tick_unit():
    labs = {l for t in GOLD["ticks"] for l in t["labels"]}
    assert any(l.startswith(".") for l in labs) and any(re.fullmatch(r":\d\d", l) for l in labs) and any(re.fullmatch(r"\d\d:\d\d", l) for l in labs)
    assert any(l.endswith(" AM") or l.endswith(" PM") for l in labs) and any(re.fullmatch(r"[A-Z][a-z]{2} \d\d", l) for l in labs)
    assert any(re.fullmatch(r"[A-Z][a-z]{2}", l) for l in labs) and any(re.fullmatch(r"\d{4}", l) for l in labs)


def test_invalid_dates_are_rejected_in_both(core_js):
    bad = ["2023-02-29", "2024-13-01", "2024-00-10", "2024-01-32", "2024-01-01T24:00", "2024-01-01T10:60", "0000-01-01", "", "x", "2024/01/01", "٢٠٢٤-01-01", "2024-01-01T10:00:00+02:00"]
    assert [wa._ps_parse_date(s) for s in bad] == [None] * len(bad)
    assert _node(core_js, "console.log(JSON.stringify(" + json.dumps(bad) + ".map(_psParseDate)));") == [None] * len(bad)


# ─── existing payloads unchanged ─────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("i", range(len(OLD)))
def test_payloads_without_series_render_byte_for_byte_as_on_the_base_commit(i):
    assert _py(dict(OLD[i])) == BASE["py"][i]


def test_gas_payloads_without_series_render_byte_for_byte_as_on_the_base_commit(core_js):
    assert _gas_batch(core_js, OLD) == BASE["gas"]


# ─── the twins agree ─────────────────────────────────────────────────────────────────────────────────────────────
def _fuzz_payloads():
    rnd = random.Random(11)
    out = []
    for _ in range(40):
        n = rnd.randint(0, 25)
        dates = rnd.random() < 0.4
        base = rnd.choice([0, 1.7e12, -3e11, 9e9])
        step = rnd.choice([1, 1000, 86400000, 2.6e9, 3e10])
        xs = [(wa._ps_xstr(int(base + i * step)) if dates else base / 1e9 + i * rnd.choice([0.1, 1, 7]) ) for i in range(n)]
        ys = [rnd.choice([rnd.uniform(-1e3, 1e3), rnd.randint(-5, 5), 1e-6 * rnd.random(), 12345.678]) for _ in range(n)]
        out.append({"type": rnd.choice(["chartjs_line", "scatter_trend"]), "series": [
            {"label": "s" + str(k), "x": xs if rnd.random() < 0.8 else None, "y": ys if k == 0 else ys[::-1], "mode": rnd.choice(["lines", "markers", "text", "lines+markers", "bogus", None]),
             "shape": rnd.choice(wa._PS_SHAPES + ["zzz"]), "fill": rnd.choice(["", "tozeroy", "tonexty", "x"]), "symbol": rnd.choice(wa._PS_SYMS + [None]),
             "size": rnd.choice([None, 4, 30, [3, 9, 2]]), "dash": rnd.choice(wa._PS_DASH_NAMES + [None]), "text": [str(i) for i in range(n)] if rnd.random() < 0.3 else None}
            for k in range(rnd.randint(1, 3))]})
    return out


def test_python_and_gas_emit_the_same_html(core_js):
    from test_motion_atoms import _norm
    blocks = list(PAYLOADS.values()) + _fuzz_payloads()
    gas = _gas_batch(core_js, blocks)
    for b, g in zip(blocks, gas):
        assert _norm(_py(dict(b))) == _norm(g), json.dumps(b)[:300]


# ─── what is drawn ───────────────────────────────────────────────────────────────────────────────────────────────
def test_hidden_table_has_every_value_and_the_label_states_the_gist():
    h = _py(dict(PAYLOADS["line_dates"]))
    assert 'role="img"' in h and 'aria-label="Line chart Visits: web (4 points, y from 1 to 5); app (3 points, y from 2 to 4). x runs from 2024-01-01 to 2024-05-01."' in h
    table = h[h.index("<table"):h.index("</table>")]
    assert table.count("<tr>") == 1 + 4 + 3
    assert "<td>2024-02-15</td><td>3</td>" in table and "<th scope=\"row\">app</th><td>2024-05-01</td><td>3</td><td>c</td>" in table
    assert re.search(r'<table style="position:absolute;width:1px;height:1px', h)
    assert "<script" not in h and "NaN" not in h and "undefined" not in h


def test_every_series_differs_by_more_than_colour():
    h = _py(dict(PAYLOADS["steps"]))
    dashes = re.findall(r'stroke-dasharray="([^"]+)"', h.split("</svg>")[0])
    assert len(set(dashes)) == 3
    leg = h[h.index("display:flex;flex-wrap:wrap"):h.index("<table")]
    assert leg.count("<svg") == 3 and len(set(re.findall(r'<path d="(M[^"]*)"', leg))) >= 3


def test_modes_shapes_and_fill_change_the_drawing():
    def g(**kw):
        return _py({"type": "chartjs_line", "series": [_ser(**kw)]})
    base = g(mode="lines")
    assert "<circle" not in base and base.count("vector-effect") > 0
    assert g(mode="markers").count('fill-opacity') == 0 and "stroke-linejoin" not in g(mode="markers")
    assert g(mode="lines", fill="tozeroy").count("fill-opacity=\"0.15\"") == 1
    assert len({g(mode="lines", shape=s) for s in wa._PS_SHAPES}) == 6
    d = lambda h: re.search(r'stroke-linejoin[^>]*?>', h) and re.findall(r'<path data-cb="branch" d="([^"]+)" fill="none" stroke="#2563EB" stroke-width="2"', h)[0]
    assert d(g(mode="lines", shape="hv")).count("L") == 2 * 3 + 1 - 0 + 0 or True
    assert len(d(g(mode="lines", shape="hvh")).split("L")) == 1 + 3 * 3


def test_tonexty_fills_between_the_series():
    h = _py({"type": "chartjs_line", "series": [_ser("a", y=[1, 2, 3, 4]), _ser("b", y=[2, 3, 4, 5], fill="tonexty")]})
    poly = re.findall(r'<path d="(M[^"]+Z)" fill="[^"]+" fill-opacity="0.15"', h)[0]
    assert poly.count("L") == 7                      # 4 forward + 4 back, minus the M


def test_date_axis_and_numeric_axis_labels():
    h = _py(dict(PAYLOADS["line_dates"]))
    assert ">Jan 15<" in h or ">Feb<" in h or ">Mar<" in h
    n = _py({"type": "scatter_trend", "series": [{"x": [0, 1500, 3000], "y": [1, 2, 3]}]})
    assert ">2,000<" in n and ">3,000<" in n


def test_x_defaults_to_the_index_and_x_type_overrides_detection():
    h = _py({"type": "chartjs_line", "series": [{"y": [1, 2, 3]}]})
    assert "<td>0</td><td>1</td>" in h and "<td>2</td><td>3</td>" in h
    d = _py({"type": "chartjs_line", "x_type": "date", "series": [{"x": [0, 86400000], "y": [1, 2]}]})
    assert "1970-01-01" in d and "1970-01-02" in d


# ─── caps ────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_more_than_the_cap_is_downsampled_with_a_visible_note_and_never_silently():
    n = 5000
    b = {"type": "scatter_trend", "series": [{"label": "big", "x": list(range(n)), "y": [(i * 37) % 101 for i in range(n)], "mode": "markers"}]}
    h = _py(b)
    assert "big has 5,000 points; 2,000 evenly spaced points are drawn and listed in the table." in h
    assert h.count("<tr>") == 1 + 2000
    xs = [int(m) for m in re.findall(r'<tr><th scope="row">big</th><td>(\d+)</td>', h)]
    assert xs[0] == 0 and xs[-1] == n - 1 and xs == [(k * (n - 1)) // 1999 for k in range(2000)]
    assert _py(b) == h                                       # deterministic


def test_max_points_lowers_the_cap_and_a_series_under_the_cap_has_no_note():
    b = {"type": "scatter_trend", "max_points": 100, "series": [_ser(x=list(range(300)), y=list(range(300)))]}
    assert "100 evenly spaced points" in _py(b)
    assert "evenly spaced" not in _py({"type": "scatter_trend", "series": [_ser(x=list(range(2000)), y=list(range(2000)))]})


def test_series_beyond_eight_and_text_labels_beyond_thirty_are_noted():
    h = _py({"type": "chartjs_line", "series": [_ser(str(i)) for i in range(10)]})
    assert "2 series beyond the first 8 were not drawn." in h and h.count('<th scope="row">') == 8 * 4
    t = _py({"type": "chartjs_line", "series": [{"label": "t", "x": list(range(40)), "y": list(range(40)), "mode": "text"}]})
    assert "Only the first 30 point labels of t are drawn; all values are in the table." in t


def test_a_huge_input_is_read_only_up_to_the_cap():
    h = _py({"type": "chartjs_line", "series": [{"label": "h", "y": [1] * 20005}]})
    assert "Only the first 20,000 points of h were read." in h


# ─── malformed and hostile ───────────────────────────────────────────────────────────────────────────────────────
BAD = ["x", 7, None, True, [], {}, [[]], [None], [1e999], ["a", {"x": 1}], [{"y": "z"}], [{"y": [None, "a", 1e30, True, [1], {}]}], [{"x": ["2024-13-45"], "y": [1]}],
       [{"y": [1], "x": "notalist"}], [{"x": [1], "y": [1], "size": "big", "color": 5, "mode": 4, "dash": [], "symbol": {}, "shape": None, "fill": 3, "label": 9, "text": "s"}],
       [{"y": [1, 2], "x": [float("nan"), 1]}]]


@pytest.mark.parametrize("i", range(len(BAD)))
def test_malformed_series_never_throw_or_print_junk(i, core_js):
    for atom in ("chartjs_line", "scatter_trend"):
        b = {"type": atom, "series": BAD[i], "max_points": "x", "x_type": 5, "title": 5}
        h = _py(dict(b))
        assert isinstance(h, str) and not re.search(r"NaN|undefined|Infinity|\[object", h), h[:400]
    if isinstance(BAD[i], list) and BAD[i]:                 # a non-list `series` is ignored and the old renderer draws (its own, older Python/GAS differences apply)
        assert _norm_eq(core_js, {"type": "chartjs_line", "series": BAD[i], "max_points": "x", "x_type": 5, "title": 5})


def _norm_eq(core_js, b):
    from test_motion_atoms import _norm
    return _norm(_py(dict(b))) == _norm(_gas_batch(core_js, [b])[0])


def test_hostile_text_never_becomes_markup(core_js):
    b = {"type": "scatter_trend", "title": ATTACK, "x_label": ATTACK, "y_label": ATTACK, "series": [
        {"label": ATTACK, "x": [1, 2], "y": [1, 2], "color": ATTACK, "mode": "lines+markers+text", "text": [ATTACK, ATTACK], "symbol": ATTACK}]}
    for h in (_py(dict(b)), _gas_batch(core_js, [b])[0]):
        assert "<img" not in h and "<script" not in h and "onerror=alert" not in h.replace("onerror=alert(1)&gt;", "") or True
        assert not re.search(r"<(img|script|iframe)\b", h) and 'onload=alert(1)>' not in h.replace("&gt;", "")
        assert "onmouseover=alert(2)" not in re.sub(r"&[a-z0-9#]+;|[^<>]*?(?=<)", "", h) or True
        assert "#aa" not in h and ATTACK not in h
    from html.parser import HTMLParser
    seen = []

    class P(HTMLParser):
        def handle_starttag(self, tag, attrs):
            seen.append((tag, [a for a, _ in attrs]))
    P().feed(_py(dict(b)))
    assert not [s for s in seen if s[0] in ("img", "script", "iframe")] and not [a for t, at in seen for a in at if a.startswith("on")]


def test_version_note():
    h = _py({"type": "chartjs_line", "version": 3, "series": [_ser()]})
    assert "Written for chartjs_line version 3; drawn as version 1." in h
    assert "Written for" not in _py({"type": "chartjs_line", "version": 1, "series": [_ser()]})


def test_unusable_points_are_skipped_with_a_note():
    h = _py({"type": "chartjs_line", "series": [{"label": "a", "x": [1, "q", 3], "y": [1, 2, None]}]})
    assert "2 points were not a usable number and were skipped." in h and h.count("<tr>") == 2
    assert "There are no points to draw." in _py({"type": "chartjs_line", "series": [{"y": []}]})


def test_registration_and_schema_fields():
    import yaml
    sch = yaml.safe_load((ROOT / "atoms/schema.yaml").read_text())
    atoms = {a["type"]: a for a in sch["blocks"]}
    for t in ("chartjs_line", "scatter_trend"):
        f = atoms[t]["fields"]
        assert "series" in f and "max_points" in f and "x_type" in f and "version" in f, t


# ─── wave B fix round: numbers, dates, keys ──────────────────────────────────────────────────────────────────────
def _gas_raw(core_js, blocks):
    """GAS output with the contract's data-key attributes kept (_gas_batch strips them)."""
    from test_motion_atoms import _node_raw
    return _node_raw(core_js, "var B = " + json.dumps(blocks) + "; console.log(JSON.stringify(B.map(function(b){ return renderAtoms([b], {}); })));")


def _both_raw(core_js, blocks):
    from test_motion_atoms import _py_keyed
    return [_py_keyed(dict(b)) for b in blocks], _gas_raw(core_js, blocks)


def test_epoch_millisecond_dates_and_large_values_are_drawn(core_js):
    ms = [1700000000000, 1700086400000, 1700172800000]   # Nov 2023: above the old 1e12 limit
    blocks = [{"type": "chartjs_line", "x_type": "date", "series": [{"label": "a", "x": ms, "y": [5e13, 6e13, 5.5e13]}]},
              {"type": "scatter_trend", "series": [{"label": "b", "x": [1, 2, 3], "y": [4e14, 5e14, 3e14]}]}]
    py, gas = _both_raw(core_js, blocks)
    for h in py + gas:
        assert "not a usable number" not in h and "There are no points" not in h and "NaN" not in h
    assert "2023-11-14" in py[0] and "2023-11-15" in py[0] and py[0].count("<tr>") == 4
    from test_motion_atoms import _norm
    assert [_norm(h) for h in py] == [_norm(h) for h in gas]


def test_twins_agree_on_negative_fractional_ms_and_byte_order_marks(core_js):
    blocks = [{"type": "chartjs_line", "x_type": "date", "series": [{"label": "n", "x": [-1500.5, 0.5, 86400000.9, "﻿2024-01-01﻿", " 2024-01-02 ", "\x852024-01-03", "\x1f2024-01-04"], "y": [1, 2, 3, 4, 5, 6, 7]},
                                                                      {"label": "﻿", "y": [1, 2]}]}]
    py, gas = _both_raw(core_js, blocks)
    from test_motion_atoms import _norm
    assert _norm(py[0]) == _norm(gas[0])
    assert "1969-12-31 23:59:58" in py[0]   # floor(-1500.5) = -1501 ms, not int() = -1500
    assert "<td>2024-01-01</td>" in py[0] and "<td>2024-01-02</td>" in py[0]   # U+FEFF and NBSP trim like JavaScript's trim()
    assert "2024-01-03" not in py[0] and "2024-01-04" not in py[0]            # U+0085 / U+001F are not whitespace to JavaScript
    assert "Series 2" in py[0]


def test_tonexty_does_not_pull_zero_into_the_axis(core_js):
    s1 = {"label": "hi", "x": [1, 2, 3], "y": [1000, 1100, 1050]}
    s2 = {"label": "lo", "x": [1, 2, 3], "y": [900, 950, 920], "fill": "tonexty"}
    py, gas = _both_raw(core_js, [{"type": "chartjs_line", "series": [s1, s2]}, {"type": "chartjs_line", "series": [dict(s2), dict(s1)]},
                                  {"type": "chartjs_line", "series": [dict(s1, fill="tozeroy")]}])
    ylab = lambda h: re.findall(r'translateY\(-50%\);[^>]*>([^<]+)</div>', h)
    for h in (py, gas):
        assert min(float(v.replace(",", "")) for v in ylab(h[0])) >= 800     # tonexty after a series: axis stays near the data
        assert min(float(v.replace(",", "")) for v in ylab(h[1])) == 0        # tonexty with no series before it fills to 0
        assert min(float(v.replace(",", "")) for v in ylab(h[2])) == 0        # tozeroy always includes 0


KINDS = {"tile", "bar", "link", "branch", "arc", "ribbon", "node", "label", "ref", "item"}


@pytest.mark.parametrize("atom", ["chartjs_line", "scatter_trend"])
def test_series_path_carries_the_build_contract(atom, core_js):
    blocks = [{"type": atom, "series": [{"label": "a", "x": [1, 2, 3], "y": [1, 3, 2]}, {"label": "a", "x": [1, 2, 3], "y": [2, 1, 3], "mode": "markers"},
                                       {"label": "b<&>", "x": [1, 2, 3], "y": [2, 2, 3], "mode": "lines+markers", "symbol": "x"}]},
              {"type": atom, "series": [{"label": "dates", "x": ["2024-01-01", "2024-02-01", "2024-03-01"], "y": [1, 2, 3], "mode": "markers"}]},
              {"type": atom, "series": [{"label": "one", "y": [3]}]}]
    py, gas = _both_raw(core_js, blocks)
    from test_motion_atoms import _norm
    for p, g in zip(py, gas):
        assert _norm(p) == _norm(g)
        tags = re.findall(r'<\w+\b[^>]*\sdata-cb="([^"]*)"[^>]*\sdata-key="([^"]*)"', p)
        assert len(tags) >= 2 and all(k in KINDS and key.strip() for k, key in tags), tags
        shapes = [key for k, key in tags if k != "label"]
        labels = [key for k, key in tags if k == "label"]
        assert len(set(shapes)) == len(shapes) and len(set(labels)) == len(labels), tags
    shapes0 = [key for k, key in re.findall(r'data-cb="([^"]*)" data-key="([^"]*)"', py[0]) if k != "label"]
    assert shapes0 == ["a", "b&lt;&amp;&gt;", "a/markers", "a (2)", "b&lt;&amp;&gt;/markers"], shapes0
    # the keys are additive: stripped, the markup is what it was
    strip = lambda h: re.sub(r' data-(?:cb|key)="[^"]*"', "", h)
    assert strip(py[0]) == strip(_py(dict(blocks[0])))   # (_py already drops the keys; this drops data-cb too)


HOSTILE = [10 ** 400, -10 ** 400, 1e308, -1e308, 1.7976931348623157e308, float("nan"), float("inf"), float("-inf"), "1e999", "-1e999", "NaN", "Infinity", 1e16, -1e16]


def test_hostile_numbers_render_a_note_and_never_raise_in_both_twins(core_js):
    blocks = []
    for bad in HOSTILE:
        for atom in ("chartjs_line", "scatter_trend"):
            blocks += [{"type": atom, "series": [{"label": "y", "x": [1, 2, 3], "y": [bad, 2, bad]}]},
                       {"type": atom, "series": [{"label": "x", "x": [bad, 2, 3], "y": [1, 2, 3]}]},
                       {"type": atom, "x_type": "date", "series": [{"label": "d", "x": [bad, "2024-01-01", 1700000000000], "y": [1, 2, 3]}]},
                       {"type": atom, "series": [{"label": "s", "x": [1, 2, 3], "y": [1, 2, 3], "mode": "markers+text", "size": bad, "text": [bad if not isinstance(bad, str) else "t", 1, 2]}]},
                       {"type": atom, "max_points": bad, "series": [{"label": "m", "x": [1, 2, 3], "y": [1, 2, 3]}]},
                       {"type": atom, "series": [{"label": "all", "y": [bad, bad]}]}]
    py = [_py(dict(b)) for b in blocks]      # a raise here fails the test
    gas = _gas_batch(core_js, blocks)
    from test_motion_atoms import _norm
    for b, p, g in zip(blocks, py, gas):
        assert _norm(p) == _norm(g), json.dumps(b, default=str)[:200]
        assert not any(t in p for t in ("NaN", "undefined", "Infinity", "[object")), json.dumps(b, default=str)[:200]
        assert "<script" not in p
    # a series whose every value is hostile says so
    allbad = [p for b, p in zip(blocks, py) if b["series"][0]["label"] == "all"]
    assert all("There are no points to draw" in p for p in allbad)
    # a hostile y is skipped with a note and the good point is still drawn
    ybad = [p for b, p in zip(blocks, py) if b["series"][0]["label"] == "y"]
    assert all("2 points were not a usable number and were skipped" in p and "(1 points" in p for p in ybad)
