"""ternary_plot and quiver (Plotly wave A, package ternary-quiver), written by hand into BOTH renderers.

GOLDEN (tests/fixtures/quiver_d3_golden.json, from quiver_d3_golden_gen.mjs) holds what the REAL d3-scale 4.0.2 gives for a
linear scale: nice(5) domain, ticks(5) and the placed values (d3's interpolateNumber a*(1-t)+b*t), plus the ternary 0..1 ticks.
Both twins must reproduce it exactly. The barycentric and arrow geometry is plain trigonometry, checked against the
markup. Also held: Python/GAS HTML parity, hidden table, aria label, caps with notes, malformed input, version note,
escaping and registration.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

import pytest
import yaml

from test_histogram import ATTACK, _table
from test_motion_atoms import _gas_batch, _node, _py, core_js  # noqa: F401  (core_js is a fixture)
from test_motion_atoms import wa  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
D = json.loads((ROOT / "tests/fixtures/quiver_d3_golden.json").read_text())
AXES = {k: v for k, v in D.items() if k != "ternary_ticks"}


# ─── the axis against real d3-scale ────────────────────────────────────────────
@pytest.mark.parametrize("name", list(AXES))
def test_python_axis_and_placement_match_d3_exactly(name):
    c = AXES[name]
    dom, ticks = wa._qv_axis([float(v) for v in c["values"]])
    assert list(dom) == c["domain"] and ticks == c["ticks"]
    assert [wa._qv_place(float(v), dom, c["r0"], c["r1"]) for v in c["values"]] == c["mapped"]
    assert [wa._qv_place(float(v), dom, c["y0"], c["y1"]) for v in c["values"]] == c["mapped_y"]


def test_gas_axis_and_placement_match_d3_exactly(core_js):
    names = list(AXES)
    res = _node(core_js, "var C = " + json.dumps([AXES[n] for n in names]) +
                "; console.log(JSON.stringify(C.map(function(c){ var a = _qvAxis(c.values); return [a[0], a[1], c.values.map(function(v){ return _qvPlace(v, a[0], c.r0, c.r1); }),"
                " c.values.map(function(v){ return _qvPlace(v, a[0], c.y0, c.y1); })]; })));")
    for n, (dom, ticks, mapped, mapped_y) in zip(names, res):
        assert dom == AXES[n]["domain"] and ticks == AXES[n]["ticks"] and mapped == AXES[n]["mapped"] and mapped_y == AXES[n]["mapped_y"], n


def test_ternary_ticks_match_d3_exactly(core_js):
    assert wa._hg_ticks(0, 1, 5) == D["ternary_ticks"]
    assert _node(core_js, "console.log(JSON.stringify(_hgTicks(0, 1, 5)));") == D["ternary_ticks"]


# ─── payloads ──────────────────────────────────────────────────────────────────
SOIL = [{"label": "Plot %d" % k, "a": a, "b": b, "c": c} for k, (a, b, c) in enumerate([(60, 30, 10), (20, 50, 30), (10, 10, 80), (34, 33, 33), (0, 100, 0), (5, 0, 95)])]
TERN = {
    "basic": {"type": "ternary_plot", "title": "Soil mix", "a_label": "Sand", "b_label": "Silt", "c_label": "Clay", "points": SOIL},
    "connect": {"type": "ternary_plot", "title": "Path", "connect": True, "points": SOIL},
    "defaults": {"type": "ternary_plot", "points": [{"a": 1, "b": 1, "c": 1}]},
    "fractions": {"type": "ternary_plot", "points": [{"a": 0.2, "b": 0.3, "c": 0.5}, {"a": 1, "b": 0, "c": 0}]},
    "corners": {"type": "ternary_plot", "points": [{"a": 1, "b": 0, "c": 0}, {"a": 0, "b": 1, "c": 0}, {"a": 0, "b": 0, "c": 1}]},
    "malformed": {"type": "ternary_plot", "a_label": ["x"], "points": [None, 7, "x", {"a": 1, "b": 2, "c": 3, "label": 5}, {"a": -1, "b": 2, "c": 3}, {"a": 0, "b": 0, "c": 0},
                                                                         {"a": "1", "b": 2, "c": 3}, {"a": 1e30, "b": 1, "c": 1}, {"a": 1, "b": 2}, {"a": True, "b": 1, "c": 1}, {"a": 2, "b": 2, "c": 2, "label": {"x": 1}}]},
    "no_points": {"type": "ternary_plot", "title": "T"},
    "points_not_a_list": {"type": "ternary_plot", "points": {"a": 1, "b": 1, "c": 1}},
    "none_usable": {"type": "ternary_plot", "points": [{"a": 0, "b": 0, "c": 0}, {"a": -1, "b": 1, "c": 1}]},
    "many": {"type": "ternary_plot", "points": [{"a": (k * 7) % 11 + 1, "b": (k * 5) % 13 + 1, "c": (k * 3) % 7 + 1} for k in range(230)]},
    "hostile": {"type": "ternary_plot", "title": ATTACK, "a_label": ATTACK, "b_label": ATTACK, "c_label": ATTACK, "points": [{"label": ATTACK, "a": 1, "b": 2, "c": 3}]},
    "version_2": {"type": "ternary_plot", "version": 2, "points": [{"a": 1, "b": 2, "c": 3}]},
    "version_junk": {"type": "ternary_plot", "version": True, "points": [{"a": 1, "b": 2, "c": 3}]},
}
FIELD = [{"x": x, "y": y, "u": u, "v": v} for x, y, u, v in [(0, 0, 1, 0), (1, 0, 0, 1), (2, 0, -1, 0), (0, 1, 1, 1), (1, 1, 0, 0), (2, 1, -1, -1), (0, 2, 2, 0), (1, 2, 0, -2), (2, 2, -2, 1)]]
QUIV = {
    "basic": {"type": "quiver", "title": "Wind", "x_label": "East", "y_label": "North", "unit": "m/s", "arrows": FIELD},
    "single": {"type": "quiver", "arrows": [{"x": 1, "y": 1, "u": 3, "v": 4}]},
    "all_zero": {"type": "quiver", "arrows": [{"x": 0, "y": 0, "u": 0, "v": 0}, {"x": 1, "y": 1, "u": 0, "v": 0}]},
    "same_xy": {"type": "quiver", "arrows": [{"x": 2, "y": 2, "u": 1, "v": 1}, {"x": 2, "y": 2, "u": -1, "v": 1}]},
    "negatives": {"type": "quiver", "arrows": [{"x": -3.5, "y": -1, "u": 0.5, "v": -0.25}, {"x": 4, "y": 2.25, "u": -1, "v": 2}]},
    "scaled": {"type": "quiver", "arrow_scale": 0.5, "arrows": FIELD},
    "scale_junk": {"type": "quiver", "arrow_scale": "big", "arrows": FIELD},
    "malformed": {"type": "quiver", "x_label": ["a"], "arrows": [None, 7, "x", {"x": 1, "y": 1, "u": 1, "v": 1}, {"x": "1", "y": 1, "u": 1, "v": 1}, {"x": 1, "y": 1, "u": 1},
                                                              {"x": 1e30, "y": 1, "u": 1, "v": 1}, {"x": 1, "y": True, "u": 1, "v": 1}, {"x": 2, "y": 2, "u": 1e30, "v": 1}, {"x": 3, "y": 3, "u": 2, "v": 2, "label": {"a": 1}}]},
    "no_arrows": {"type": "quiver", "title": "T"},
    "arrows_not_a_list": {"type": "quiver", "arrows": {"x": 1}},
    "none_usable": {"type": "quiver", "arrows": [{"x": "a", "y": 1, "u": 1, "v": 1}]},
    "many": {"type": "quiver", "arrows": [{"x": k % 20, "y": k // 20, "u": math.cos(k), "v": math.sin(k)} for k in range(230)]},
    "hostile": {"type": "quiver", "title": ATTACK, "x_label": ATTACK, "y_label": ATTACK, "unit": ATTACK, "arrows": [{"x": 1, "y": 1, "u": 1, "v": 1, "label": ATTACK}]},
    "version_2": {"type": "quiver", "version": 2, "arrows": FIELD},
    "version_junk": {"type": "quiver", "version": True, "arrows": FIELD},
}
PAYLOADS = {**{"tp_" + k: v for k, v in TERN.items()}, **{"qv_" + k: v for k, v in QUIV.items()}}


@pytest.mark.parametrize("name", list(PAYLOADS))
def test_python_and_gas_emit_identical_html(name, core_js):
    assert _py(PAYLOADS[name]) == _gas_batch(core_js, [PAYLOADS[name]])[0]


@pytest.mark.parametrize("name", list(PAYLOADS))
def test_no_script_no_nan_and_hostile_text_is_escaped(name):
    html = _py(PAYLOADS[name])
    assert "<script" not in html
    for bad in ("NaN", "undefined", "Infinity", "[object Object]", "null"):
        assert bad not in html, bad
    if name.endswith("hostile"):
        assert "<img" not in html and "<svg onload" not in html and "onerror=alert(1)>" not in html.replace("&quot;", "")
        assert "&lt;img" in html


# ─── ternary_plot ──────────────────────────────────────────────────────────────
H = math.sqrt(3) / 2


def _tp_dots(html):
    return [(float(a), float(b)) for a, b in re.findall(r'<div class="tpd"(?: data-cb="node")? style="position:absolute;left:([\d.]+)%;top:([\d.]+)%;', html)]


def test_ternary_points_sit_at_their_barycentric_place(core_js):
    b = TERN["basic"]
    for html in (_py(b), _gas_batch(core_js, [b])[0]):
        dots = _tp_dots(html)
        assert len(dots) == len(SOIL)
        for (px, py), p in zip(dots, SOIL):
            s = p["a"] + p["b"] + p["c"]
            fa, fc = p["a"] / s, p["c"] / s
            assert abs(px - (fc + fa / 2) * 100) < 0.002 and abs(py - (1 - fa) * 100) < 0.002, p


def test_ternary_corners_are_the_three_vertices():
    dots = _tp_dots(_py(TERN["corners"]))
    assert dots == [(50.0, 0.0), (0.0, 100.0), (100.0, 100.0)]


def test_ternary_shares_are_normalised_and_the_table_lists_them(core_js):
    for html in (_py(TERN["basic"]), _gas_batch(core_js, [TERN["basic"]])[0]):
        head, rows = _table(html)
        assert head == ["Point", "Sand", "Silt", "Clay"]
        assert [r[0] for r in rows] == [p["label"] for p in SOIL]
        assert rows[0][1:] == ["60%", "30%", "10%"] and rows[3][1:] == ["34%", "33%", "33%"]
        t = html.index("<table")
        assert 'role="img"' in html[:t] and 'role="img"' not in html[t:]
    _, rows = _table(_py(TERN["fractions"]))
    assert rows[0][1:] == ["20%", "30%", "50%"] and rows[1][0] == "Point 2"


def test_ternary_default_axis_names_and_aria_gist():
    html = _py(TERN["defaults"])
    assert _table(html)[0] == ["Point", "A", "B", "C"]
    a = re.search(r'role="img" aria-label="([^"]*)"', _py(TERN["basic"])).group(1)
    assert a.startswith("Ternary plot of 6 points. Sand, Silt and Clay shares sum to 100%. Average: Sand ")
    assert "Silt " in a and "Clay " in a


def test_ternary_grid_and_tick_labels_at_every_fifth():
    html = _py(TERN["basic"])
    assert len(re.findall(r'class="tpg"', html)) == 12                      # 4 interior ticks per axis, 3 axes
    ticks = re.findall(r'<div class="tpt"[^>]*>(\d+%)</div>', html)
    assert sorted(set(ticks)) == ["20%", "40%", "60%", "80%"] and len(ticks) == 12


def test_ternary_connect_draws_one_line_through_the_points_in_order():
    assert "tpl" not in _py(TERN["basic"])
    html = _py(TERN["connect"])
    assert len(re.findall(r'<polyline class="tpl"', html)) == 1
    pts = re.search(r'<polyline class="tpl"[^>]* points="([^"]*)"', html).group(1).split(" ")
    assert len(pts) == len(SOIL)


def test_ternary_skips_unusable_points_and_says_so(core_js):
    for html in (_py(TERN["malformed"]), _gas_batch(core_js, [TERN["malformed"]])[0]):
        assert len(_tp_dots(html)) == 2 and "were not a usable point and were left out" in html
    assert "needs at least one point" in _py(TERN["no_points"]) and "needs at least one point" in _py(TERN["none_usable"])
    assert "needs at least one point" in _py(TERN["points_not_a_list"])


def test_ternary_caps_at_200_points_with_a_note():
    html = _py(TERN["many"])
    assert len(_tp_dots(html)) == 200 and "30 points beyond the first 200 were not drawn." in html
    assert len(_table(html)[1]) == 200


# ─── quiver ────────────────────────────────────────────────────────────────────
def _shaft(d):
    m = re.match(r"M(-?[\d.]+) (-?[\d.]+)L(-?[\d.]+) (-?[\d.]+)", d)
    return tuple(float(x) for x in m.groups())


def test_quiver_arrows_point_the_way_their_u_v_say_and_scale_with_length(core_js):
    b = QUIV["basic"]
    for html in (_py(b), _gas_batch(core_js, [b])[0]):
        ds = re.findall(r'<path class="qva"(?: data-cb="node")? d="([^"]*)"', html)
        assert len(ds) == len(FIELD) - 1                                     # the (1,1) arrow has length 0 and is a dot
        assert len(re.findall(r'<circle class="qvz"', html)) == 1
        it = iter(ds)
        lens = []
        for a in FIELD:
            if a["u"] == 0 and a["v"] == 0:
                continue
            x0, y0, x1, y1 = _shaft(next(it))
            dx, dy = x1 - x0, y0 - y1                                        # screen y runs down
            lens.append(math.hypot(dx, dy) / math.hypot(a["u"], a["v"]))
            assert abs(math.atan2(dy, dx) - math.atan2(a["v"], a["u"])) < 0.01, a
        assert max(lens) - min(lens) < 0.05 and abs(max(lens) * math.sqrt(5) - 120) < 0.5     # longest arrow (u,v = -2,1) is 120 units; the rest in proportion


def test_quiver_arrows_are_centred_on_their_point_and_stay_inside_the_plot():
    html = _py(QUIV["negatives"])
    (dom_x, _), (dom_y, _) = wa._qv_axis([-3.5, 4.0]), wa._qv_axis([-1.0, 2.25])
    for d, a in zip(re.findall(r'<path class="qva"(?: data-cb="node")? d="([^"]*)"', html), QUIV["negatives"]["arrows"]):
        x0, y0, x1, y1 = _shaft(d)
        px, py = wa._qv_place(float(a["x"]), dom_x, 65, 935), wa._qv_place(float(a["y"]), dom_y, 555, 65)
        assert abs((x0 + x1) / 2 - px) < 0.01 and abs((y0 + y1) / 2 - py) < 0.01
        assert min(x0, x1) >= 0 and max(x0, x1) <= 1000 and min(y0, y1) >= 0 and max(y0, y1) <= 620


def test_quiver_arrow_scale_shrinks_and_junk_scale_is_ignored():
    longest = lambda h: max(math.hypot(_shaft(d)[2] - _shaft(d)[0], _shaft(d)[3] - _shaft(d)[1]) for d in re.findall(r'<path class="qva"(?: data-cb="node")? d="([^"]*)"', h))
    assert abs(longest(_py(QUIV["basic"])) - 120) < 0.5 and abs(longest(_py(QUIV["scaled"])) - 60) < 0.5
    assert _py(QUIV["scale_junk"]) == _py(dict(QUIV["scaled"], arrow_scale=1))


def test_quiver_zero_arrows_are_dots_and_all_zero_draws():
    html = _py(QUIV["all_zero"])
    assert len(re.findall(r'class="qvz"', html)) == 2 and "qva" not in html


def test_quiver_table_and_aria(core_js):
    for html in (_py(QUIV["basic"]), _gas_batch(core_js, [QUIV["basic"]])[0]):
        head, rows = _table(html)
        assert head == ["Arrow", "East", "North", "Across", "Up", "Length"]
        assert len(rows) == 9 and rows[0][0] == "Arrow 1" and rows[0][1:] == ["0", "0", "1 m/s", "0 m/s", "1 m/s"]
        assert rows[8][3:] == ["-2 m/s", "1 m/s", "2.236 m/s"]
        t = html.index("<table")
        assert 'role="img"' in html[:t] and 'role="img"' not in html[t:]
        a = re.search(r'role="img" aria-label="([^"]*)"', html).group(1)
        assert a.startswith("Quiver plot of 9 arrows, East 0 to 2, North 0 to 2. Longest arrow: ") and "m/s" in a
    assert _table(_py(QUIV["single"]))[0] == ["Arrow", "x", "y", "Across", "Up", "Length"]


def test_quiver_skips_unusable_arrows_and_caps_at_200_with_notes(core_js):
    for html in (_py(QUIV["malformed"]), _gas_batch(core_js, [QUIV["malformed"]])[0]):
        assert len(re.findall(r'class="qva"', html)) == 2 and "were not a usable arrow and were left out" in html
    for n in ("no_arrows", "arrows_not_a_list", "none_usable"):
        assert "needs at least one arrow" in _py(QUIV[n])
    html = _py(QUIV["many"])
    assert len(re.findall(r'class="qva"', html)) + len(re.findall(r'class="qvz"', html)) == 200 and "30 arrows beyond the first 200 were not drawn." in html


@pytest.mark.parametrize("name", ["tp_version_2", "qv_version_2"])
def test_version_above_one_adds_a_note_and_junk_does_not(name):
    html = _py(PAYLOADS[name])
    assert re.search(r"Written for (ternary_plot|quiver) version 2; drawn as version 1\.", html)
    junk = _py(PAYLOADS[name.replace("2", "junk")])
    assert "Written for" not in junk
    assert html.replace(re.search(r'<div[^>]*>Written for[^<]*</div>', html).group(0), "") == junk


# ─── registration ──────────────────────────────────────────────────────────────
@pytest.mark.parametrize("atom", ["ternary_plot", "quiver"])
def test_registered_as_a_preview_chart_atom(atom):
    schema = yaml.safe_load((ROOT / "atoms/schema.yaml").read_text())
    entries = [e for e in schema["blocks"] if e.get("type") == atom]
    assert len(entries) == 1
    e = entries[0]
    assert e["stage"] == "preview" and "version" in e["fields"] and len(e["intent_phrases"]) == 3
    for k in ("description", "compact_description", "routing_text", "notes", "surfaces", "source"):
        assert e.get(k), k
    packs = yaml.safe_load((ROOT / "atoms/atom-packs.yaml").read_text())
    assert atom in packs["a2ui-charts-v1"]
    assert '"%s"' % atom in (ROOT / "apps-script-surface/gas-wired-renderer/PackMap.gs").read_text()
    assert '"%s": {"type": "%s"' % (atom, atom) in (ROOT / "scripts/generate_atom_pages.py").read_text()
    assert "d3-scale" in (ROOT / "THIRD-PARTY-NOTICES.md").read_text()


# ─── round 2 review findings ──────────────────────────────────────────────────
def test_q1_ternary_hint_says_the_third_part_counts_down_the_right_edge(core_js):
    for html in (_py(TERN["basic"]), _gas_batch(core_js, [TERN["basic"]])[0]):
        assert "Clay counts down the right edge towards its corner" in html
        assert "Clay up the right edge" not in html
        assert "Sand counts up the left edge" in html


def test_q2_quiver_routing_text_says_direction_ignores_axes_and_arrows_are_centred():
    sch = yaml.safe_load((ROOT / "atoms/schema.yaml").read_text())
    atom = next(a for a in sch["blocks"] if isinstance(a, dict) and a.get("type") == "quiver")
    rt = " ".join(atom["routing_text"].split())
    assert "ignores the axis scales" in rt and "centred on their point, not tail-anchored" in rt
