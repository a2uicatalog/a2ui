"""box_plot optional `show_points` (I48, owner decision D10): every number of each group drawn as a dot, spread by a beeswarm.

GOLDEN (tests/fixtures/box_plot_points_d3_golden.json, from box_plot_points_d3_golden_gen.mjs) holds what the REAL d3-force 3.0.0 gives for
forceSimulation(nodes).force("x", forceX(x).strength(1)).force("y", forceY(0).strength(1)).force("collide", forceCollide(3)).stop().tick(120)
on nodes with no x/y. Both twins must reproduce it EXACTLY (==, not a tolerance). Python needs bit-exact fdlibm cos/sin for that: d3's phyllotaxis start
uses Math.cos / Math.sin, V8's are fdlibm's and glibc's differ in the last bit for ~7% of the angles, which the soft collisions amplify into pixels.
Also held here: with show_points absent, false or not boolean true, both twins render exactly the pre-change bytes (sha256 of the pre-change output,
tests/fixtures/box_plot_baseline_sha.json); Python/GAS HTML parity with it on; the dot cap with its note; the aria label; the unchanged hidden table.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import random
import re
from pathlib import Path

import pytest
import yaml

from test_box_plot import CASES, PAYLOADS, _bp
from test_histogram import _table
from test_motion_atoms import _gas_batch, _node, _py, core_js  # noqa: F401  (core_js is a fixture)
from test_motion_atoms import wa  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
G = json.loads((ROOT / "tests/fixtures/box_plot_points_d3_golden.json").read_text())
SW = {**G["golden"], **{f"fuzz{i}": c for i, c in enumerate(G["fuzz"])}}
BASE = json.loads((ROOT / "tests/fixtures/box_plot_baseline_sha.json").read_text())


# ─── the swarm against real d3-force ───────────────────────────────────────────
@pytest.mark.parametrize("name", list(SW))
def test_python_swarm_matches_d3_force_exactly(name):
    assert wa._sn_swarm(SW[name]["xs"], G["ticks"], G["radius"]) == SW[name]["pos"]


def test_gas_swarm_matches_d3_force_exactly(core_js):
    names = list(SW)
    res = _node(core_js, "var G = " + json.dumps([SW[n]["xs"] for n in names]) + "; console.log(JSON.stringify(G.map(function(xs){ return _snSwarm(xs, %d, %d); })));" % (G["ticks"], G["radius"]))
    for n, pos in zip(names, res):
        assert pos == SW[n]["pos"], n


def test_the_golden_set_covers_the_hard_cases():
    g = G["golden"]
    assert len(g["dense500"]["xs"]) == 500 and len(g["all_equal"]["xs"]) == 40 and len(g["single"]["xs"]) == 1
    assert len(set(g["clustered100"]["xs"])) < 40                                     # many exact ties: d3's jiggle() path
    assert max(abs(p[1]) for p in g["dense500"]["pos"]) > 20                          # the swarm really spreads vertically


def test_the_spring_nodes_layout_still_matches_after_sharing_its_lcg_and_quadtree():
    # the shared helpers were refactored for the swarm (_sn_lcg, the visit callback's y bounds); the layout must not move
    from test_spring_nodes_force import GOLDEN, TICKS, CHARGE, _close
    for g in GOLDEN.values():
        _close(wa._sn_layout(g["n"], g["links"], g["distance"], CHARGE, TICKS), g["pos"])


def test_v8_trig_port_is_bit_exact_against_node(core_js):
    rnd = random.Random(5)
    a = math.pi * (3 - math.sqrt(5))
    xs = [i * a for i in range(1200)] + [rnd.uniform(-900, 900) for _ in range(3000)] + [0.0, 1e-9, math.pi / 4, math.pi / 2, math.pi, -3.0, 0.5]
    res = _node(core_js, "var X = " + json.dumps(xs) + "; console.log(JSON.stringify(X.map(function(v){ return [Math.cos(v), Math.sin(v)]; })));")
    assert all(wa._v8_cos(v) == c and wa._v8_sin(v) == s for v, (c, s) in zip(xs, res))


# ─── the contract: show_points off is today's output, byte for byte ────────────
@pytest.mark.parametrize("name", list(BASE))
def test_without_show_points_both_twins_render_exactly_the_pre_change_bytes(name, core_js):
    b = PAYLOADS[name]
    assert hashlib.sha256(_py(b).encode()).hexdigest() == BASE[name]
    assert hashlib.sha256(_gas_batch(core_js, [b])[0].encode()).hexdigest() == BASE[name]


def test_false_and_non_boolean_show_points_change_nothing(core_js):
    for name in ("three", "malformed", "many_outliers", "all_equal"):
        b = PAYLOADS[name]
        for v in (False, None, 0, 1, "true", "yes", [], [True], {}, 1.0):
            assert _py(dict(b, show_points=v)) == _py(b), (name, v)
        both = _gas_batch(core_js, [dict(b, show_points=v) for v in (False, 1, "true", None)])
        assert all(h == _gas_batch(core_js, [b])[0] for h in both)


# ─── rendering with the dots on ────────────────────────────────────────────────
def _on(b, **kw):
    return dict(b, show_points=True, **kw)


DOTTED = {
    "three": _on(PAYLOADS["three"]),
    "five": _on(PAYLOADS["five"]),
    "all_equal": _on(PAYLOADS["all_equal"]),
    "negatives": _on(PAYLOADS["negatives"]),
    "skewed": _on(PAYLOADS["skewed"]),
    "both_sides": _on(PAYLOADS["both_sides"]),
    "twelve": _on(PAYLOADS["twelve"]),
    "malformed": _on(PAYLOADS["malformed"]),
    "many_outliers": _on(PAYLOADS["many_outliers"]),
    "big_group": _on({"type": "box_plot", "groups": [{"label": "Huge", "values": [round(50 + math.sin(i * 1.7) * 20 + (i % 7), 2) for i in range(1300)]}, {"label": "Small", "values": [1, 2, 3, 4, 5, 6]}]}),
    "version_2": _on(PAYLOADS["version_2"]),
}


@pytest.mark.parametrize("name", list(DOTTED))
def test_python_and_gas_emit_identical_html_with_the_dots_on(name, core_js):
    assert _py(DOTTED[name]) == _gas_batch(core_js, [DOTTED[name]])[0]


def _dots(html):
    """[(group index, left %, top px)] for every point dot."""
    out = []
    for k, row in enumerate(html.split('<div class="bpp"')[1:]):
        out.append([(float(m.group(1)), float(m.group(2))) for m in re.finditer(r'<div class="bpd" style="position:absolute;left:([\d.]+)%;top:calc\(50% \+ (-?[\d.]+)px\);', row)])
    return out


def test_every_usable_number_is_one_dot_inside_its_row(core_js):
    b = DOTTED["three"]
    for html in (_py(b), _gas_batch(core_js, [b])[0]):
        per = _dots(html)
        assert [len(d) for d in per] == [len(g["values"]) for g in b["groups"]]
        assert all(0 <= x <= 100 and abs(y) <= 28 for d in per for x, y in d)               # row is 64px: dots stay 4px inside it
        assert html.count('height:64px;">') == 3 and "height:40px;" not in html
    # dots sit where the values are: the swarm's x is the value's place on a 180-unit axis, moved only by collisions
    (stats, (x0, x1), _) = wa._bp_layout([[float(v) for v in g["values"]] for g in b["groups"]])
    vals = sorted(float(v) for v in b["groups"][0]["values"])
    xs = [(v - x0) / (x1 - x0) * 180 for v in vals]
    sw = wa._sn_swarm(xs, 120, 3)
    got = _dots(_py(b))[0]
    assert [x for x, _ in got] == [float(wa._if_fixed(max(0.0, min(180.0, p[0])) / 180 * 100, 3)) for p in sw]


def test_malformed_numbers_are_not_dots_but_the_group_is_the_same_as_without(core_js):
    b = DOTTED["malformed"]
    for html in (_py(b), _gas_batch(core_js, [b])[0]):
        assert [len(d) for d in _dots(html)] == [5, 6]
        assert _table(html) == _table(_py(PAYLOADS["malformed"]))


def test_dots_are_behind_the_box_and_the_median_and_the_box_is_see_through(core_js):
    for html in (_py(DOTTED["five"]), _gas_batch(core_js, [DOTTED["five"]])[0]):
        assert html.index('class="bpd"') < html.index('class="bpw"') < html.index('class="bpb"') < html.index('class="bpm"')
        assert re.search(r'class="bpb"[^>]*background:transparent', html) and "background:var(--surface,#F8FAFC)" not in html
    assert re.search(r'class="bpb"[^>]*background:var\(--surface,#F8FAFC\)', _py(PAYLOADS["five"]))


def test_outlier_markers_are_still_drawn_on_top(core_js):
    for html in (_py(DOTTED["both_sides"]), _gas_batch(core_js, [DOTTED["both_sides"]])[0]):
        assert html.count('class="bpo"') == 3 and html.rindex('class="bpd"') < html.index('class="bpo"')


def test_hidden_table_and_notes_are_unchanged_and_aria_says_the_dots_show_every_value(core_js):
    for name in ("three", "twelve", "skewed"):
        base = PAYLOADS[name]
        for html in (_py(DOTTED[name]), _gas_batch(core_js, [DOTTED[name]])[0]):
            assert _table(html) == _table(_py(base))
            a = re.search(r'role="img" aria-label="([^"]*)"', html).group(1)
            assert a == re.search(r'role="img" aria-label="([^"]*)"', _py(base)).group(1) + " Dots show every value."
            t = html.index("<table")
            assert 'role="img"' in html[:t] and "<script" not in html


def test_the_axis_geometry_is_the_same_with_and_without_the_dots():
    strip = lambda h: re.sub(r'<div class="bpd"[^>]*></div>', "", h)
    a, b = _py(PAYLOADS["three"]), strip(_py(DOTTED["three"]))
    norm = lambda h: h.replace("height:64px;", "height:40px;").replace("background:transparent", "background:var(--surface,#F8FAFC)").replace(" Dots show every value.", "")
    assert norm(b) == a


def test_zero_width_axis_stacks_the_dots_around_the_middle_without_nan(core_js):
    for h in (_py(DOTTED["all_equal"]), _gas_batch(core_js, [DOTTED["all_equal"]])[0]):
        xs = [x for x, _ in _dots(h)[0]]
        assert len(xs) == 5 and all(35 < x < 65 for x in xs) and "NaN" not in h and "Infinity" not in h and "undefined" not in h


def test_more_than_500_numbers_are_evenly_thinned_and_the_note_says_so(core_js):
    for h in (_py(DOTTED["big_group"]), _gas_batch(core_js, [DOTTED["big_group"]])[0]):
        assert [len(d) for d in _dots(h)] == [500, 6]
        assert "Huge has 1300 numbers; the 500 drawn as dots are evenly spaced through the sorted values. The table counts them all." in h
        assert _table(h)[1][0][1] == "1300"
    pts = wa._bp_points([float(i) for i in range(1300)])
    assert len(pts) == 500 and pts[0] == 0 and pts[-1] == 1299 and all(a < b for a, b in zip(pts, pts[1:]))
    assert wa._bp_points([3.0, 1.0, 2.0]) == [1.0, 2.0, 3.0]


def test_exactly_500_numbers_are_all_drawn_without_a_note():
    b = {"type": "box_plot", "show_points": True, "groups": [{"label": "G", "values": list(range(500))}]}
    h = _py(b)
    assert len(_dots(h)[0]) == 500 and "drawn as dots" not in h


def test_deterministic_and_fast_enough_for_the_largest_case():
    b = {"type": "box_plot", "show_points": True, "groups": [{"label": "G%d" % k, "values": [round(math.sin(i + k) * 40 + 50, 1) for i in range(500)]} for k in range(2)]}
    assert _py(b) == _py(copy.deepcopy(b))


# ─── registration ─────────────────────────────────────────────────────────────
def test_schema_documents_show_points_and_the_d3_force_credit_names_the_swarm():
    blocks = {a["type"]: a for a in yaml.safe_load((ROOT / "atoms/schema.yaml").read_text())["blocks"]}
    f = blocks["box_plot"]["fields"]["show_points"]
    assert "default false" in f and "500" in f and "beeswarm" in f
    t = (ROOT / "THIRD-PARTY-NOTICES.md").read_text()
    assert "forceCollide" in t and "tests/test_box_plot_points.py" in t
