"""box_plot optional `show_points` (I48, owner decision D10): every number of each group drawn as a dot, spread by a deterministic DODGE beeswarm.

Each dot is at its exact x (the value's place on the axis, in %), in sorted order, at the smallest |y| from the row centre that does not touch a dot already
placed (centres at least 2 x 2.5px + 0.5px apart in the 180px reference plot), alternating above and below on ties. A dot with no room inside the row is put on the
row's edge and counted; the count is noted. At most 300 dots per chart, shared across the groups in proportion to their sizes. Independent implementation of the
dodge approach (Observable Plot's dodge transform, d3's beeswarm example); the test below checks it against a brute-force reference written here.
Also held here: with show_points absent, false or not boolean true, both twins render exactly the pre-change bytes (sha256 of the pre-change output,
tests/fixtures/box_plot_baseline_sha.json); Python/GAS byte parity with it on; the caps and notes; the aria label; the unchanged hidden table.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import random
import re
import time
from pathlib import Path

import pytest
import yaml

from test_box_plot import CASES, PAYLOADS, _bp
from test_histogram import _table
from test_motion_atoms import _gas_batch, _node, _py, core_js  # noqa: F401  (core_js is a fixture)
from test_motion_atoms import wa  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
BASE = json.loads((ROOT / "tests/fixtures/box_plot_baseline_sha.json").read_text())
REFW, MIND, LIM = 180.0, 5.5, 28.0


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


# ─── the dodge itself ─────────────────────────────────────────────────────────
def _brute_min(xs, ys, over, lim, d=MIND):
    """Independent reference, checked against the dots as placed: for each dot, given the placed (non-edge) dots before it, the smallest |y| of every free candidate
    (0 and each earlier dot's y +/- the touching offset, all earlier dots checked) must be this dot's |y|; an edge dot is one with no free candidate at all."""
    placed = []
    for x, y, o in zip(xs, ys, over):
        cands = [0.0] + [yj + s * math.sqrt(d * d - (x - xj) ** 2) for xj, yj in placed if abs(x - xj) < d for s in (1, -1)]
        ok = [abs(c) for c in cands if abs(c) <= lim and all((x - xj) ** 2 + (c - yj) ** 2 >= d * d - 1e-9 for xj, yj in placed)]
        if o:
            assert not ok, (x, ok)
        else:
            assert ok and abs(abs(y) - min(ok)) < 1e-9, (x, y, min(ok) if ok else None)
            placed.append((x, y))


def _cases():
    rnd = random.Random(11)
    return {
        "empty": [], "single": [90.0], "three_equal": [90.0] * 3, "pair_near": [10.0, 12.0],
        "normal300": sorted(min(REFW, max(0.0, rnd.gauss(90, 18))) for _ in range(300)),
        "clustered": sorted(round(rnd.uniform(0, 180) / 20) * 20.0 for _ in range(120)),
        "uniform200": sorted(rnd.uniform(0, REFW) for _ in range(200)),
        "ties_and_steps": sorted([float(i % 7) * 5.5 for i in range(80)]),
        "all_equal60": [90.0] * 60,
        "all_equal300": [90.0] * 300,
    }


@pytest.mark.parametrize("name", list(_cases()))
def test_dodge_places_each_dot_at_the_smallest_free_offset_and_never_closer_than_the_minimum(name):
    xs = _cases()[name]
    ys, over = wa._bp_dodge(xs, LIM)
    assert len(ys) == len(over) == len(xs)
    _brute_min(xs, ys, over, LIM)
    pts = [(x, y) for x, y, o in zip(xs, ys, over) if not o]
    assert all(abs(y) <= LIM + 1e-9 and (abs(y) == LIM or not o) for y, o in zip(ys, over))
    assert all(abs(y) == LIM for y, o in zip(ys, over) if o)
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            assert math.hypot(pts[i][0] - pts[j][0], pts[i][1] - pts[j][1]) >= MIND - 1e-6


def test_dodge_alternates_above_and_below_and_fills_a_pile_outward():
    ys, over = wa._bp_dodge([90.0] * 5, LIM)
    assert not any(over) and ys == [0.0, -5.5, 5.5, 11.0, -11.0]
    assert wa._bp_dodge([], LIM) == ([], [])
    assert wa._bp_dodge([10.0, 100.0], LIM)[0] == [0.0, 0.0]                         # far apart: both on the centre line


def test_a_pile_that_does_not_fit_puts_the_rest_on_the_row_edge_and_counts_it():
    ys, over = wa._bp_dodge([90.0] * 60, LIM)
    assert sum(over) == 49 and sorted(y for y, o in zip(ys, over) if not o) == [-27.5 + 5.5 * k for k in range(11)]
    assert {y for y, o in zip(ys, over) if o} == {LIM, -LIM}


def test_gas_dodge_is_identical_to_python(core_js):
    cs = _cases()
    res = _node(core_js, "var C = " + json.dumps(list(cs.values())) + "; console.log(JSON.stringify(C.map(function(xs){ return _bpDodge(xs, %s); })));" % LIM)
    for (n, xs), got in zip(cs.items(), res):
        ys, over = wa._bp_dodge(xs, LIM)
        assert got[0] == ys and got[1] == over, n


# ─── rendering with the dots on ────────────────────────────────────────────────
def _on(b, **kw):
    return dict(b, show_points=True, **kw)


def _wave(n, k=0, scale=40):
    return [round(50 + math.sin(i * 1.7 + k) * scale + (i % 7), 2) for i in range(n)]


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
    "big_group": _on({"type": "box_plot", "groups": [{"label": "Huge", "values": _wave(1300)}, {"label": "Small", "values": [1, 2, 3, 4, 5, 6]}]}),
    "pile": _on({"type": "box_plot", "groups": [{"label": "Pile", "values": [7] * 60}, {"label": "Spread", "values": _wave(40)}]}),
    "version_2": _on(PAYLOADS["version_2"]),
}


@pytest.mark.parametrize("name", list(DOTTED))
def test_python_and_gas_emit_identical_html_with_the_dots_on(name, core_js):
    assert _py(DOTTED[name]) == _gas_batch(core_js, [DOTTED[name]])[0]


def _dots(html):
    """Per row: [(left %, top px)] for every point dot."""
    return [[(float(m.group(1)), float(m.group(2))) for m in re.finditer(r'<div class="bpd" style="position:absolute;left:([\d.]+)%;top:calc\(50% \+ (-?[\d.]+)px\);', row)]
            for row in html.split('<div class="bpp"')[1:]]


def test_every_usable_number_is_one_dot_inside_its_row(core_js):
    b = DOTTED["three"]
    for html in (_py(b), _gas_batch(core_js, [b])[0]):
        per = _dots(html)
        assert [len(d) for d in per] == [len(g["values"]) for g in b["groups"]]
        assert all(0 <= x <= 100 and abs(y) <= 28 for d in per for x, y in d)               # row is 64px: dots stay 4px inside it
        assert html.count('height:64px;">') == 3 and "height:40px;" not in html


@pytest.mark.parametrize("name", ["three", "skewed", "negatives", "twelve", "both_sides", "malformed", "five"])
def test_dot_x_is_exactly_the_values_place_on_the_axis(name, core_js):
    b = DOTTED[name]
    groups = [g for g in b["groups"] if isinstance(g, dict) and isinstance(g.get("values"), list)]
    for html in (_py(b), _gas_batch(core_js, [b])[0]):
        got = _dots(html)
        used = [g for g in groups if sum(isinstance(v, (int, float)) and not isinstance(v, bool) and abs(v) < 1e30 for v in g["values"]) >= 5]
        (stats, (x0, x1), _) = wa._bp_layout([[float(v) for v in g["values"] if isinstance(v, (int, float)) and not isinstance(v, bool) and abs(v) < 1e30] for g in used])
        assert len(got) == len(used)
        caps = wa._bp_alloc([sum(isinstance(v, (int, float)) and not isinstance(v, bool) and abs(v) < 1e30 for v in g["values"]) for g in used])
        for g, row in zip(used, got):
            vals = sorted(float(v) for v in g["values"] if isinstance(v, (int, float)) and not isinstance(v, bool) and abs(v) < 1e30)
            vals = wa._bp_points(vals, caps[used.index(g)])
            want = [(v - x0) / (x1 - x0) * 100 for v in vals]
            assert len(row) == len(want) and all(abs(x - w) < 0.0006 for (x, _), w in zip(row, want)), (name, row[:5], want[:5])
            assert all(0 <= x <= 100 for x, _ in row)                                        # nothing beyond the axis


def test_no_two_dots_of_a_row_are_closer_than_two_radii_unless_the_note_counts_them(core_js):
    for name in ("three", "skewed", "twelve", "pile", "negatives", "big_group", "many_outliers"):
        for html in (_py(DOTTED[name]), _gas_batch(core_js, [DOTTED[name]])[0]):
            rows = _dots(html)
            edge = sum(1 for row in rows for _, y in row if abs(y) == 28.0)
            assert edge == sum(int(m) for m in re.findall(r"(\d+) dots? overlaps? in", html)), name      # the note counts exactly the edge dots
            for row in rows:
                pts = [(x * REFW / 100, y) for x, y in row if abs(y) != 28.0]
                assert all(math.hypot(a[0] - c[0], a[1] - c[1]) >= 5.0 for i, a in enumerate(pts) for c in pts[i + 1:]), name
    assert "dots overlap in" in _py(DOTTED["pile"])


def test_overlap_note_names_the_group_and_counts_the_edge_dots(core_js):
    for html in (_py(DOTTED["pile"]), _gas_batch(core_js, [DOTTED["pile"]])[0]):
        assert "49 dots overlap in Pile; the table has every value." in html and " overlap in Spread" not in html
        assert [len(d) for d in _dots(html)] == [60, 40]
    one = {"type": "box_plot", "show_points": True, "groups": [{"label": "G", "values": [7] * 12}]}       # 11 fit, 1 does not
    for html in (_py(one), _gas_batch(core_js, [one])[0]):
        assert "1 dot overlaps in G; the table has every value." in html


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


def test_zero_width_axis_stacks_the_dots_on_the_middle_without_nan(core_js):
    for h in (_py(DOTTED["all_equal"]), _gas_batch(core_js, [DOTTED["all_equal"]])[0]):
        xs = [x for x, _ in _dots(h)[0]]
        assert len(xs) == 5 and set(xs) == {50.0} and "NaN" not in h and "Infinity" not in h and "undefined" not in h


# ─── the cap: 300 dots per chart ──────────────────────────────────────────────
def test_allocation_shares_300_dots_in_proportion_with_a_floor_of_20():
    al = wa._bp_alloc
    assert al([5, 100, 150]) == [5, 100, 150] and al([]) == [] and al([200, 100]) == [200, 100]
    assert al([1300, 6]) == [294, 6]
    assert al([200, 200, 200]) == [100, 100, 100]
    assert al([1000] * 12) == [25] * 12
    r = al([2000, 30, 25, 400])
    assert sum(r) == 300 and r[1] >= 20 and r[2] >= 20 and all(0 <= c <= s for c, s in zip(r, [2000, 30, 25, 400])) and r[0] > r[3] > 20
    rnd = random.Random(2)
    for _ in range(200):
        sizes = [rnd.choice([5, 20, 21, 90, 400, 2000]) for _ in range(rnd.randint(1, 12))]
        r = al(sizes)
        assert sum(r) == min(300, sum(sizes)) and all(min(s, 20) <= c <= s for c, s in zip(r, sizes)), (sizes, r)


def test_gas_allocation_is_identical_to_python(core_js):
    rnd = random.Random(3)
    cases = [[rnd.choice([5, 20, 21, 90, 400, 2000]) for _ in range(rnd.randint(1, 12))] for _ in range(100)]
    res = _node(core_js, "var C = " + json.dumps(cases) + "; console.log(JSON.stringify(C.map(_bpAlloc)));")
    assert res == [wa._bp_alloc(c) for c in cases]


def test_more_than_300_numbers_in_a_chart_are_evenly_thinned_and_the_note_says_so(core_js):
    for h in (_py(DOTTED["big_group"]), _gas_batch(core_js, [DOTTED["big_group"]])[0]):
        assert [len(d) for d in _dots(h)] == [294, 6]
        assert "Huge has 1300 numbers; the 294 drawn as dots are evenly spaced through the sorted values. The table counts them all." in h
        assert "Small has" not in h
        assert _table(h)[1][0][1] == "1300"
    pts = wa._bp_points([float(i) for i in range(1300)], 294)
    assert len(pts) == 294 and pts[0] == 0 and pts[-1] == 1299 and all(a < b for a, b in zip(pts, pts[1:]))
    assert wa._bp_points([3.0, 1.0, 2.0], 300) == [1.0, 2.0, 3.0]


def test_the_cap_is_per_chart_not_per_group(core_js):
    b = _on({"type": "box_plot", "groups": [{"label": "G%d" % k, "values": _wave(200, k)} for k in range(3)]})
    for h in (_py(b), _gas_batch(core_js, [b])[0]):
        assert [len(d) for d in _dots(h)] == [100, 100, 100] and h.count("drawn as dots are evenly spaced") == 3


def test_exactly_300_numbers_in_a_chart_are_all_drawn_without_a_note():
    b = _on({"type": "box_plot", "groups": [{"label": "G", "values": _wave(150)}, {"label": "H", "values": _wave(150, 2)}]})
    h = _py(b)
    assert [len(d) for d in _dots(h)] == [150, 150] and "drawn as dots" not in h


def test_deterministic():
    b = DOTTED["three"]
    assert _py(b) == _py(copy.deepcopy(b))


# ─── speed: the first version of this took 4 s for 500 dots ───────────────────
def _best(f, runs=3):
    t = []
    for _ in range(runs):
        t0 = time.perf_counter()
        f()
        t.append(time.perf_counter() - t0)
    return min(t)


@pytest.mark.parametrize("name,groups", [("one_group", [_wave(300)]), ("three_groups", [_wave(200, k) for k in range(3)]), ("one_pile", [[7.0] * 300]), ("twelve", [_wave(100, k, 30) for k in range(12)])])
def test_300_dots_render_well_inside_a_second(name, groups):
    b = _on({"type": "box_plot", "groups": [{"label": "G%d" % k, "values": v} for k, v in enumerate(groups)]})
    t = _best(lambda: _py(b))
    print("box_plot show_points", name, "best of 3: %.3f s" % t)
    assert t < 1.0, t


# ─── the swarm is gone ────────────────────────────────────────────────────────
def test_the_force_swarm_and_its_trig_port_are_removed_from_both_twins():
    for n in ("_sn_swarm", "_v8_cos", "_v8_sin", "_v8_rem"):
        assert not hasattr(wa, n), n
    gas = (ROOT / "apps-script-surface/gas-wired-renderer/atoms_infographic.gs").read_text()
    assert "_snSwarm" not in gas and "_BP_SWARM_TICKS" not in gas
    assert not (ROOT / "tests/fixtures/box_plot_points_d3_golden.json").exists() and not (ROOT / "tests/fixtures/box_plot_points_d3_golden_gen.mjs").exists()


# ─── registration ─────────────────────────────────────────────────────────────
def test_schema_documents_show_points_and_the_notices_credit_the_dodge_approach():
    blocks = {a["type"]: a for a in yaml.safe_load((ROOT / "atoms/schema.yaml").read_text())["blocks"]}
    f = blocks["box_plot"]["fields"]["show_points"]
    assert "default false" in f and "300" in f and "beeswarm" in f and "d3-force" not in f and "500" not in f
    t = (ROOT / "THIRD-PARTY-NOTICES.md").read_text()
    assert "Observable Plot" in t and "dodge" in t and "forceCollide" not in t
