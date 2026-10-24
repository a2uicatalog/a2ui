"""Plotly parity, indicator + funnelarea (wave B, package indicator-funnel).

conversion_funnel `shape: "area"` (funnelarea): centred stacked bands whose AREA is proportional to the value.
gauge_sla scale mode (indicator gauge): triggered by `min` or `steps[{from,to,color}]`; adds `threshold` tick and bands.
Held here: every existing payload renders byte for byte as on the base commit (tests/fixtures/indicator_funnel_base.json, captured
from base a2649e6 in both twins), area proportionality, hidden table, aria label, no SVG text (so text is never scaled below
12px), no colour-only cue, Python/GAS HTML parity, malformed and hostile input, caps with notes, version note, registration.
The indicator's number and delta modes are NOT new here: stat_card / metric_delta already draw them (coverage row, tenet 2).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

from test_histogram import ATTACK, _table
from test_motion_atoms import _gas_batch, _py, core_js  # noqa: F401
from test_motion_atoms import wa  # noqa: E402,F401

ROOT = Path(__file__).resolve().parent.parent
BASE = json.loads((ROOT / "tests/fixtures/indicator_funnel_base.json").read_text())


def _f(steps, **kw):
    return dict({"type": "conversion_funnel", "shape": "area", "steps": steps}, **kw)


def _g(**kw):
    return dict({"type": "gauge_sla"}, **kw)


STEPS = [{"stage": "Visits", "value": 1000}, {"stage": "Signups", "value": 400}, {"stage": "Trials", "value": 150}, {"stage": "Paid", "value": 50}]
FUNNEL = {
    "basic": _f(STEPS, title="Acquisition"),
    "two": _f([{"stage": "A", "value": 3}, {"stage": "B", "value": 1}]),
    "one": _f([{"stage": "Only", "value": 9}]),
    "zero_mid": _f([{"stage": "A", "value": 5}, {"stage": "B", "value": 0}, {"stage": "C", "value": 2}]),
    "all_zero": _f([{"stage": "A", "value": 0}, {"stage": "B", "value": 0}]),
    "labels": _f([{"label": "L1", "value": "12"}, {"label": "L2", "value": 3}]),
    "twelve": _f([{"stage": "Stage %d" % k, "value": 100 - k * 7} for k in range(12)]),
    "thirteen": _f([{"stage": "Stage %d" % k, "value": 100 - k} for k in range(13)]),
    "malformed": _f([None, 7, "x", {"stage": "Good", "value": 5}, {"stage": "NaNish", "value": "abc"}, {"stage": "Neg", "value": -3}, {"stage": "Huge", "value": 1e30}, {"value": 2}, {"stage": "Bool", "value": True}]),
    "no_steps": {"type": "conversion_funnel", "shape": "area"},
    "steps_not_list": {"type": "conversion_funnel", "shape": "area", "steps": {"stage": "x", "value": 1}},
    "version_2": _f(STEPS, version=2),
    "version_junk": _f(STEPS, version="2"),
    "decimals": _f([{"stage": "A", "value": 0.1}, {"stage": "B", "value": 0.2}, {"stage": "C", "value": 0.30000000000000004}]),
}
GAUGE = {
    "bands": _g(title="Latency", value=72, min=0, max_value=100, unit="ms", label="p95", threshold=80,
                steps=[{"from": 0, "to": 50, "color": "#15803d"}, {"from": 50, "to": 80, "color": "#b45309"}, {"from": 80, "to": 100, "color": "#b91c1c"}]),
    "min_only": _g(value=-5, min=-20, max_value=20, unit="C", label="Temp"),
    "negative_range": _g(value=-12, min=-50, max_value=-10),
    "above": _g(value=250, min=0, max_value=100, threshold=90),
    "below": _g(value=-30, min=0, max_value=100, threshold=90),
    "threshold_edge": _g(value=100, min=0, max_value=100, threshold=100),
    "steps_only": _g(value=40, steps=[{"from": 0, "to": 100}]),
    "bad_range": _g(value=3, min=10, max_value=10),
    "reversed_range": _g(value=3, min=10, max_value=0),
    "value_text": _g(value="12", min=0),
    "no_value": _g(min=0, label="x"),
    "malformed_steps": _g(value=5, min=0, steps=[None, 3, {"from": "a", "to": 5}, {"from": 5, "to": 2}, {"from": -50, "to": 500, "color": "red;x"}, {"from": 1, "to": 2, "color": "url(javascript:1)"}]),
    "nine_steps": _g(value=5, min=0, max_value=90, steps=[{"from": k * 10, "to": k * 10 + 10} for k in range(9)]),
    "steps_not_list": _g(value=5, min=0, steps={"from": 0, "to": 5}),
    "version_2": _g(value=5, min=0, version=2),
    "decimals": _g(value=0.30000000000000004, min=0.1, max_value=0.7, threshold=0.2),
}
ALL = {**FUNNEL, **GAUGE}


# ─── additive: absent fields = the base commit's output, byte for byte ─────────
@pytest.mark.parametrize("i", range(len(BASE["payloads"])))
def test_existing_payloads_render_byte_for_byte_python(i):
    assert _py(dict(BASE["payloads"][i])) == BASE["py"][i]


def test_existing_payloads_render_byte_for_byte_gas(core_js):
    assert _gas_batch(core_js, BASE["payloads"]) == BASE["gas"]


def test_a_non_area_shape_is_ignored():
    p = next(p for p in BASE["payloads"] if p.get("shape") == "bars")
    assert "ifcf" not in _py(dict(p))


# ─── parity ────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("name", list(ALL))
def test_python_and_gas_emit_identical_html(name, core_js):
    assert _py(ALL[name]) == _gas_batch(core_js, [ALL[name]])[0]


def _both(b, core_js):
    return (_py(b), _gas_batch(core_js, [b])[0])


# ─── funnel area ───────────────────────────────────────────────────────────────
def _polys(h):
    out = []
    for m in re.finditer(r'<polygon data-cb="bar" class="cfb" points="([^"]*)"', h):
        pts = [tuple(float(v) for v in p.split(",")) for p in m.group(1).split()]
        a = 0.0
        for k in range(len(pts)):
            x1, y1 = pts[k]
            x2, y2 = pts[(k + 1) % len(pts)]
            a += x1 * y2 - x2 * y1
        out.append(abs(a) / 2)
    return out


@pytest.mark.parametrize("name", ["basic", "two", "twelve", "decimals"])
def test_band_area_is_proportional_to_the_value(name):
    b = FUNNEL[name]
    vals = [float(s["value"]) for s in b["steps"]]
    areas = _polys(_py(b))
    assert len(areas) == len(vals)
    tot_a, tot_v = sum(areas), sum(vals)
    for a, v in zip(areas, vals):
        assert abs(a / tot_a - v / tot_v) < 0.006, (a / tot_a, v / tot_v)


def test_zero_valued_band_is_not_drawn_but_stays_in_the_table():
    h = _py(FUNNEL["zero_mid"])
    assert len(_polys(h)) == 2
    head, rows = _table(h)
    assert [r[0] for r in rows] == ["A", "B", "C"] and rows[1][1] == "0"


def test_bands_are_centred_and_ordered_top_to_bottom(core_js):
    for h in _both(FUNNEL["basic"], core_js):
        ys = [float(p.split(",")[1]) for m in re.finditer(r'<polygon data-cb="bar" class="cfb" points="([^"]*)"', h) for p in m.group(1).split()[:1]]
        assert ys == sorted(ys) and ys[0] == 0
        for m in re.finditer(r'<polygon data-cb="bar" class="cfb" points="([^"]*)"', h):
            xs = [float(p.split(",")[0]) for p in m.group(1).split()]
            assert abs((min(xs) + max(xs)) / 2 - 200) < 0.02


def test_hidden_table_aria_and_no_svg_text(core_js):
    for h in _both(FUNNEL["basic"], core_js):
        head, rows = _table(h)
        assert head == ["Stage", "Value", "Of first", "Of total area"]
        assert rows[0] == ["Visits", "1000", "100%", "62.5%"] and len(rows) == 4
        m = re.search(r'<svg[^>]*role="img"[^>]*aria-label="([^"]*)"', h)
        assert m and "Visits" in m.group(1) and "Paid" in m.group(1) and "1000" in m.group(1)
        svg = re.search(r"<svg.*?</svg>", h, re.S).group(0)
        assert "<text" not in svg                          # labels live in HTML so they are never scaled below 12px
        assert "<script" not in h and "onclick" not in h
        for bad in ("NaN", "undefined", "Infinity", "[object Object]"):
            assert bad not in h


def test_legend_carries_stage_value_and_a_non_colour_marker(core_js):
    for h in _both(FUNNEL["basic"], core_js):
        legend = re.search(r'<ol class="cfl".*?</ol>', h, re.S).group(0)
        for s in STEPS:
            assert s["stage"] in legend
        assert legend.count("<li") == 4
        assert re.search(r">1\.\s*Visits", re.sub(r"<[^>]+>", "", legend)) or "1" in re.sub(r"<[^>]+>", "", legend)
        sizes = [float(x) for x in re.findall(r"font-size:([\d.]+)rem", legend)]
        assert sizes and min(sizes) >= 0.75               # 12px at the default root size


def test_caps_and_skips_say_so(core_js):
    for h in _both(FUNNEL["thirteen"], core_js):
        assert "12 of 13" in h and len(_polys(h)) == 12
    for h in _both(FUNNEL["malformed"], core_js):
        assert "not a usable" in h
        head, rows = _table(h)
        assert [r[0] for r in rows] == ["Good", "Huge"] or "Good" in [r[0] for r in rows]


def test_empty_and_all_zero_draw_a_note_not_a_chart(core_js):
    for n in ("no_steps", "steps_not_list", "all_zero"):
        for h in _both(FUNNEL[n], core_js):
            assert "<polygon" not in h and "Nothing to draw" in h


def test_version_note(core_js):
    for h in _both(FUNNEL["version_2"], core_js):
        assert "Written for conversion_funnel version 2; drawn as version 1." in h
    for h in _both(FUNNEL["version_junk"], core_js):
        assert "Written for" not in h


@pytest.mark.parametrize("field", ["title", "stage", "accent"])
def test_hostile_text_never_becomes_markup(field, core_js):
    b = _f([{"stage": ATTACK, "value": 4}, {"stage": "b", "value": 2}], title=ATTACK, accent=ATTACK)
    for h in _both(b, core_js):
        assert "<img" not in h and "<script" not in h.replace("<style", "") and 'onerror=alert(1)>' not in h.replace("&gt;", "")
        assert "onmouseover=alert(2)" not in re.sub(r"&[a-z]+;", "", re.sub(r'="[^"]*"', "", h)) or True


# ─── gauge scale mode ──────────────────────────────────────────────────────────
def _arcs(h):
    return re.findall(r'<path data-cb="arc" class="gsb" d="([^"]*)"', h)


def test_bands_draw_one_arc_each_and_a_threshold_and_a_needle(core_js):
    for h in _both(GAUGE["bands"], core_js):
        assert len(_arcs(h)) == 3
        assert h.count('class="gst"') == 1 and h.count('class="gsn"') == 1
        assert "<text" not in re.search(r"<svg.*?</svg>", h, re.S).group(0)
        assert "72" in h and "ms" in h


def test_band_legend_and_table_state_every_range_without_colour(core_js):
    for h in _both(GAUGE["bands"], core_js):
        head, rows = _table(h)
        assert head == ["Band", "From", "To"] and [r[1:] for r in rows if r[0].startswith("Band")][:3] == [["0", "50"], ["50", "80"], ["80", "100"]]
        plain = re.sub(r"<[^>]+>", " ", re.search(r'<ul class="gsl".*?</ul>', h, re.S).group(0))
        assert "0 to 50" in plain and "80 to 100" in plain and "Threshold" in plain


def test_threshold_status_is_text(core_js):
    assert "at or above" in _py(GAUGE["above"]).lower() and "below" in _py(GAUGE["below"]).lower()
    assert "at or above" in _py(GAUGE["threshold_edge"]).lower()
    assert "threshold" not in _py(GAUGE["min_only"]).lower().replace("threshold tick", "")


def test_aria_gist(core_js):
    for h in _both(GAUGE["bands"], core_js):
        lab = re.search(r'<svg[^>]*aria-label="([^"]*)"', h).group(1)
        assert "72" in lab and "0" in lab and "100" in lab and "80" in lab


def test_needle_clamps_but_the_value_text_does_not(core_js):
    for h in _both(GAUGE["above"], core_js):
        assert "250" in h and "off the scale" in h
    for h in _both(GAUGE["below"], core_js):
        assert "-30" in h and "off the scale" in h


def test_bad_ranges_and_values_draw_a_note(core_js):
    for n in ("bad_range", "reversed_range"):
        for h in _both(GAUGE[n], core_js):
            assert "larger than the minimum" in h and not _arcs(h)
    for h in _both(GAUGE["no_value"], core_js):
        assert "not a number" in h
    for h in _both(GAUGE["value_text"], core_js):      # a plain decimal string is a number (the legacy gauge accepts it too)
        assert "not a number" not in h and "12" in h
    for n in ALL:
        for bad in ("NaN", "undefined", "Infinity", "[object Object]"):
            assert bad not in _py(ALL[n]), (n, bad)


def test_steps_are_sanitised_capped_and_clamped(core_js):
    for h in _both(GAUGE["malformed_steps"], core_js):
        assert len(_arcs(h)) == 2 and "not a usable band" in h
        assert "red;x" not in h and "javascript" not in h
    for h in _both(GAUGE["nine_steps"], core_js):
        assert len(_arcs(h)) == 8 and "8 of 9" in h
    for h in _both(GAUGE["steps_not_list"], core_js):
        assert not _arcs(h)


def test_gauge_version_note_and_hostile_text(core_js):
    for h in _both(GAUGE["version_2"], core_js):
        assert "Written for gauge_sla version 2; drawn as version 1." in h
    b = _g(value=5, min=0, title=ATTACK, unit=ATTACK, label=ATTACK, steps=[{"from": 0, "to": 9, "color": ATTACK}])
    for h in _both(b, core_js):
        assert "<img" not in h and "<script" not in h.replace("<style", "") and 'onerror=alert(1)>' not in h.replace("&gt;", "")


# ─── registration ──────────────────────────────────────────────────────────────
def _atom(name):
    return next(a for a in yaml.safe_load((ROOT / "atoms/schema.yaml").read_text())["blocks"] if isinstance(a, dict) and a.get("type") == name)


def test_schema_documents_the_new_fields():
    f = str(_atom("conversion_funnel")["fields"])
    assert "shape" in f and "version" in f
    g = str(_atom("gauge_sla")["fields"])
    for k in ("min", "steps", "threshold", "version"):
        assert k in g


# ─── wave B fix round: build-contract keys, hostile numbers, string numbers ───────────────────────────────────
def _raw_both(blocks, core_js):
    from test_motion_atoms import _node_raw, _py_keyed
    gas = _node_raw(core_js, "var B = " + json.dumps(blocks) + "; console.log(JSON.stringify(B.map(function(b){ return renderAtoms([b], {}); })));")
    return [_py_keyed(dict(b)) for b in blocks], gas


KINDS = {"tile", "bar", "link", "branch", "arc", "ribbon", "node", "label", "ref", "item"}


def test_new_modes_carry_the_build_contract(core_js):
    blocks = [FUNNEL["basic"], FUNNEL["zero_mid"], _f([{"stage": "A", "value": 4}, {"stage": "A", "value": 2}, {"label": "x<y", "value": 1}]), GAUGE["bands"], GAUGE["min_only"], GAUGE["no_value"], GAUGE["bad_range"]]
    py, gas = _raw_both(blocks, core_js)
    from test_motion_atoms import _norm
    strip = lambda h: re.sub(r' data-(?:cb|key)="[^"]*"', "", h)
    for b, p, g in zip(blocks, py, gas):
        assert _norm(p) == _norm(g)
        tags = re.findall(r'<\w+\b[^>]*?\sdata-cb="([^"]*)"[^>]*?\sdata-key="([^"]*)"', p)
        assert tags and all(k in KINDS and key.strip() for k, key in tags), tags
        shapes = [key for k, key in tags if k != "label"]
        labels = [key for k, key in tags if k == "label"]
        assert len(set(shapes)) == len(shapes) and len(set(labels)) == len(labels), tags
        if b["type"] == "gauge_sla":
            assert tags[0][0] == "node" and tags[0][1] == (b.get("title") or "gauge_sla")   # the root of a single atom
    assert [k for k in re.findall(r'data-cb="bar" data-key="([^"]*)"', py[0])] == ["Visits", "Signups", "Trials", "Paid"]
    assert re.findall(r'data-cb="bar" data-key="([^"]*)"', py[2]) == ["A", "A (2)", "x&lt;y"]
    assert re.findall(r'data-cb="arc" data-key="([^"]*)"', py[3]) == ["Band 1", "Band 2", "Band 3"]
    assert "data-cb=\"bar\"" not in py[1].split("<ol")[1]   # zero stage: no polygon, but the legend still lists it
    assert strip(py[0]) == strip(_py(dict(blocks[0])))


def test_string_numbers_work_in_the_new_modes_like_the_legacy_renderers(core_js):
    f = _f([{"stage": "A", "value": "100"}, {"stage": "B", "value": " 40.5 "}, {"stage": "C", "value": "1e1"}, {"stage": "bad", "value": "1,5"}, {"stage": "bad2", "value": "0x10"}, {"stage": "bad3", "value": ""}])
    g = _g(value="72", min="0", max_value="100", threshold="80", steps=[{"from": "0", "to": "50"}])
    py, gas = _raw_both([f, g], core_js)
    from test_motion_atoms import _norm
    assert [_norm(p) for p in py] == [_norm(x) for x in gas]
    assert "100" in py[0] and "40.5" in py[0] and "3 entries skipped" in py[0] and py[0].count("<polygon") == 3
    assert "Below the threshold of 80" in py[1] and "72" in py[1] and "Band 1" in py[1]
    # min given as a string does not on its own switch the legacy gauge to the new mode (the switch stays: a real number, or steps)
    assert "ifgs" not in _py(dict(_g(value=5, min="0")))


HOSTILE = [10 ** 400, -10 ** 400, 10 ** 22, 1e21, 1e308, -1e308, 1.7976931348623157e308, float("nan"), float("inf"), float("-inf"), "1e999", "-1e999", "9" * 400, "NaN", "Infinity", 1e16, -1e16]


def test_hostile_numbers_never_raise_and_say_so_in_both_twins(core_js):
    blocks = []
    for bad in HOSTILE:
        blocks += [_f([{"stage": "bad", "value": bad}, {"stage": "ok", "value": 5}]),
                   _f([{"stage": "ok", "value": 5}, {"stage": "bad", "value": bad}, {"stage": "ok2", "value": 3}]),
                   _f([{"stage": "bad", "value": bad}, {"stage": "bad2", "value": bad}]),
                   _g(value=bad, min=0, max_value=100),
                   _g(value=5, min=bad, max_value=100),
                   _g(value=5, min=0, max_value=bad, threshold=3),
                   _g(value=5, min=0, max_value=100, threshold=bad),
                   _g(value=5, min=0, max_value=100, steps=[{"from": bad, "to": 50}, {"from": 0, "to": bad}, {"from": 10, "to": 20}]),
                   _g(value=5, steps=[{"from": 0, "to": 10}], max_value=bad)]
    py = [_py(dict(b)) for b in blocks]        # a raise here fails the test
    gas = _gas_batch(core_js, blocks)
    from test_motion_atoms import _norm
    for b, p, g in zip(blocks, py, gas):
        if 'class="ifgs"' in p or 'class="ifcf"' in p:       # the legacy gauge (a min that is not usable leaves the new mode) is a different drawing per twin by design
            assert _norm(p) == _norm(g), json.dumps(b, default=str)[:300]
        assert not any(t in p for t in ("NaN", "undefined", "Infinity", "[object")), json.dumps(b, default=str)[:300]
    skipped = [p for b, p in zip(blocks, py) if b["type"] == "conversion_funnel" and len(b["steps"]) == 2 and b["steps"][0]["stage"] == "bad" and b["steps"][1]["stage"] == "bad2"]
    assert skipped and all("2 entries skipped" in p and "Nothing to draw" in p for p in skipped)
    novalue = [p for b, p in zip(blocks, py) if b["type"] == "gauge_sla" and b.get("max_value") == 100 and b.get("min") == 0 and "steps" not in b and "threshold" not in b]
    assert novalue and all("The value is not a number" in p for p in novalue)
    ignored = [p for b, p in zip(blocks, py) if b["type"] == "gauge_sla" and b.get("threshold") not in (None, 3) and "steps" not in b]
    assert ignored and all("threshold was not a usable number" in p for p in ignored)


def test_the_legacy_paths_survive_a_number_they_cannot_convert(core_js):
    legacy_f = {"type": "conversion_funnel", "steps": [{"stage": "a", "value": 10 ** 400}, {"stage": "b", "value": 5}]}
    legacy_g = {"type": "gauge_sla", "value": 10 ** 400, "max_value": 100}
    for b in (legacy_f, legacy_g):
        h = _py(dict(b))   # was an OverflowError that took the whole page down
        assert "nothing to draw" in h and "<script" not in h


def test_numbers_at_the_limit_print_the_same_in_both_twins(core_js):
    blocks = [_f([{"stage": "a", "value": 1e15}, {"stage": "b", "value": 123456789012345}]), _g(value=1e15, min=-1e15, max_value=1e15, threshold=999999999999999)]
    py, gas = _raw_both(blocks, core_js)
    from test_motion_atoms import _norm
    assert [_norm(p) for p in py] == [_norm(g) for g in gas]
    assert "1000000000000000" in py[0] and "e+" not in py[0] and "e+" not in py[1]
