"""voronoi (I56): nearest-site regions of a set of points, ported by hand into BOTH renderers from d3-delaunay 6.0.4 (Voronoi cell clipping), delaunator 5.1.0
(the triangulation: hull, legalize, quicksort, the advancing hull with its angular hash) and robust-predicates 3.0.3 (the adaptive orient2d), with the
Delaunay wrapper's collinear fallback (jitter by sin, cos and hypot).

GOLDEN (tests/fixtures/voronoi_d3_golden.json, from voronoi_d3_golden_gen.mjs) holds what the REAL modules give: for 24 hand cases (3 points, collinear points,
square grids with exact ties, points on and outside the bounds, 1 and 2 points, duplicates, 200 random points) and 44 seeded fuzz cases, the triangles,
halfedges and hull of Delaunay (and the jittered points it ends up with), the raw Delaunator output, and every cellPolygon (null where d3 gives none); plus 367
orient2d calls chosen to reach every stage of the adaptive predicate, and sin / cos / hypot of the V8 that generated the file.
Every number is compared with == (exact). The triangulation and clipping are correctly rounded IEEE operations in the same order as the JavaScript, and orient2d
is the exact-arithmetic code of robust-predicates ported line by line (Python floats are IEEE doubles and never fuse a multiply-add). The one place a library
call is not correctly rounded is the collinear jitter: d3-delaunay applies Math.sin, Math.cos and Math.hypot, and V8's differ from the host libm in the last bit
for about 3% of arguments, so both twins carry their own port of fdlibm sin/cos (the medium-size argument reduction, |x| <= 2^19 * pi/2 = 823,549) and of V8's
hypot, which makes them exact against V8; beyond that argument size the host sin/cos is used and the result is only held to 1e-12 (a collinear set with a
coordinate sum of more than 800 thousand, whose jitter then differs in the last bits, which cannot change a drawn cell by a visible amount).
The fallback stages of orient2d (the tail terms and the full expansion) ARE reached by the golden orient2d calls: see test_orient2d_golden_reaches_every_stage.
Also held here: Python/GAS HTML parity, nearest-site correctness and area sum of the cells (independent of the golden), the hidden table (Share of the area by the
shoelace formula), the aria label, label gating by the inscribed circle, motion index, malformed input, caps with notes, the `version` field, escaping and
registration.
"""
from __future__ import annotations

import json
import math
import re
from functools import lru_cache
from pathlib import Path

import pytest
import yaml

from test_histogram import ATTACK
from test_motion_atoms import _gas_batch, _node, _py, core_js  # noqa: F401  (core_js is a fixture)
from test_motion_atoms import wa  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
D = json.loads((ROOT / "tests/fixtures/voronoi_d3_golden.json").read_text())
CASES = {**D["cases"], **{"fuzz%02d" % i: c for i, c in enumerate(D["fuzz"])}}
NAMES = list(CASES)


# ─── the algorithms against the real modules ──────────────────────────────────────────────────────────────────
def _flat(points):
    return [v for p in points for v in p]


def _py_run(c):
    r = wa._vo_voronoi(c["points"], c["bounds"])
    return r


@pytest.mark.parametrize("name", NAMES)
def test_python_delaunay_and_cells_match_d3_exactly(name):
    c = CASES[name]
    r = _py_run(c)
    assert r["triangles"] == c["triangles"]
    assert r["halfedges"] == c["halfedges"]
    assert r["hull"] == c["hull"]
    assert r["points"] == c["jittered"]
    assert r["cells"] == c["cells"]


@pytest.mark.parametrize("name", NAMES)
def test_python_raw_delaunator_matches(name):
    c = CASES[name]
    r = wa._vo_delaunator(_flat(c["points"]))
    assert r["triangles"] == c["raw"]["triangles"] and r["halfedges"] == c["raw"]["halfedges"] and r["hull"] == c["raw"]["hull"]


def _gas_all(core_js, key):
    body = ("var C = " + json.dumps([[CASES[n]["points"], CASES[n]["bounds"]] for n in NAMES]) +
            "; console.log(JSON.stringify(C.map(function(c){ var r = _voVoronoi(c[0], c[1]); return r." + key + "; })));")
    return _node(core_js, body)


def test_gas_delaunay_and_cells_match_d3_exactly(core_js):
    body = ("var C = " + json.dumps([[CASES[n]["points"], CASES[n]["bounds"]] for n in NAMES]) +
            "; console.log(JSON.stringify(C.map(function(c){ return _voVoronoi(c[0], c[1]); })));")
    res = _node(core_js, body)
    for n, r in zip(NAMES, res):
        c = CASES[n]
        assert r["triangles"] == c["triangles"], n
        assert r["halfedges"] == c["halfedges"], n
        assert r["hull"] == c["hull"], n
        assert r["points"] == c["jittered"], n
        assert r["cells"] == c["cells"], n


def test_gas_raw_delaunator_matches(core_js):
    body = ("var C = " + json.dumps([_flat(CASES[n]["points"]) for n in NAMES]) +
            "; console.log(JSON.stringify(C.map(function(c){ return _voDelaunator(c); })));")
    res = _node(core_js, body)
    for n, r in zip(NAMES, res):
        assert r == CASES[n]["raw"], n


O = D["orient"]


def test_python_orient2d_matches_robust_predicates_exactly():
    for t in O:
        assert wa._vo_orient2d(*t[:6]) == t[6], t


def test_gas_orient2d_matches_robust_predicates_exactly(core_js):
    res = _node(core_js, "var T = " + json.dumps([t[:6] for t in O]) + "; console.log(JSON.stringify(T.map(function(t){ return _voOrient2d(t[0], t[1], t[2], t[3], t[4], t[5]); })));")
    assert res == [t[6] for t in O]


def test_orient2d_golden_reaches_every_stage():
    """Counts, with the Python port instrumented through its own stage marker, which return each golden call takes."""
    seen = set()
    for t in O:
        wa._vo_orient2d(*t[:6])
        seen.add(wa._VO_STAGE[0])
    assert seen == {"A", "B", "Bz", "C", "D"}, seen


TR, HY = D["trig"], D["hypot"]
SMALL = 8.2e5


def test_python_sin_cos_hypot_match_v8():
    for x, s, c in TR:
        if abs(x) < SMALL:
            assert wa._vo_sin(x) == s and wa._vo_cos(x) == c, x
        else:
            assert abs(wa._vo_sin(x) - s) < 1e-12 and abs(wa._vo_cos(x) - c) < 1e-12, x
    for dx, dy, h in HY:
        assert wa._vo_hypot(dx, dy) == h, (dx, dy)


def test_gas_sin_cos_hypot_match_v8(core_js):
    res = _node(core_js, "var T = " + json.dumps([[t[0] for t in TR], [[h[0], h[1]] for h in HY]]) +
                "; console.log(JSON.stringify([T[0].map(function(x){ return [_voSin(x), _voCos(x)]; }), T[1].map(function(p){ return _voHypot(p[0], p[1]); })]));")
    for (x, s, c), (gs, gc) in zip(TR, res[0]):
        if abs(x) < SMALL:
            assert (gs, gc) == (s, c), x
        else:
            assert abs(gs - s) < 1e-12 and abs(gc - c) < 1e-12, x
    assert res[1] == [h[2] for h in HY]


def test_the_golden_set_covers_the_hard_cases():
    c = CASES
    assert c["collinear_horizontal"]["raw"]["triangles"] == [] and c["collinear_horizontal"]["triangles"] != []                  # the jitter path
    assert c["collinear_horizontal"]["jittered"] != _flat(c["collinear_horizontal"]["points"])
    assert any(x is None for x in c["same_point_twice"]["cells"]) and any(x is None for x in c["collinear_with_duplicate"]["cells"])   # a coincident point has no cell
    assert len(c["one_point"]["cells"][0]) == 5 and c["two_points"]["hull"] == [0, 1] or c["two_points"]["hull"] == [1, 0]        # the degenerate 1 and 2 point diagrams
    assert len(c["random_200"]["cells"]) == 200 and len(c["random_200"]["triangles"]) > 1000
    assert len(c["square_grid_5x5"]["triangles"]) // 3 == 32 and len(c["octagon_and_centre"]["hull"]) == 8                     # exact cocircular ties
    assert len(D["fuzz"]) == 44 and len(O) >= 300
    assert sum(1 for f in D["fuzz"] if f["jittered"] != _flat(f["points"])) >= 5                                                 # fuzz cases that take the jitter path (tiny scale: d3's cross <= 1e-10 test)
    assert any(None in f["cells"] for f in D["fuzz"])


# ─── geometry that does not depend on the golden ──────────────────────────────────────────────────────────────
def _shoelace(poly, ox=0.0, oy=0.0):
    s = 0.0
    for i in range(len(poly) - 1):
        s += (poly[i][0] - ox) * (poly[i + 1][1] - oy) - (poly[i + 1][0] - ox) * (poly[i][1] - oy)
    return abs(s) / 2


def _inside(poly, x, y):
    n, c = len(poly) - 1, False
    for i in range(n):
        x0, y0, x1, y1 = poly[i][0], poly[i][1], poly[i + 1][0], poly[i + 1][1]
        if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0:
            c = not c
    return c


@pytest.mark.parametrize("name", ["three_points", "square_grid_4x4", "octagon_and_centre", "random_200", "points_outside_bounds", "right_triangle_with_circumcentre_big"] + ["fuzz%02d" % i for i in (1, 2, 3, 4, 6, 9, 14, 20, 33, 36)])
def test_cells_are_nearest_site_regions_and_tile_the_bounds(name):
    c = CASES[name]
    r = _py_run(c)
    pts, cells = r["points"], r["cells"]
    xs = [pts[2 * i] for i in range(len(pts) // 2)]
    ys = [pts[2 * i + 1] for i in range(len(pts) // 2)]
    x0, y0, x1, y1 = c["bounds"]
    s = [3]

    def rnd():
        s[0] = (1664525 * s[0] + 1013904223) % 4294967296
        return s[0] / 4294967296
    live = [i for i, p in enumerate(cells) if p]
    if len(live) < len(cells):
        pytest.skip("coincident points share a region by construction")
    total = sum(_shoelace(cells[i], x0, y0) for i in live)
    assert abs(total - (x1 - x0) * (y1 - y0)) <= 1e-9 * (x1 - x0) * (y1 - y0), total
    for _ in range(120):
        px, py = x0 + rnd() * (x1 - x0), y0 + rnd() * (y1 - y0)
        d = [(xs[i] - px) ** 2 + (ys[i] - py) ** 2 for i in live]
        best = min(d)
        owners = [live[k] for k, v in enumerate(d) if v - best <= 1e-9 * (1 + best)]
        # the owner's polygon contains the point (a point on a tie may sit on either side of the shared edge)
        assert any(_inside(cells[i], px, py) for i in owners) or len(owners) > 1


# ─── rendering ─────────────────────────────────────────────────────────────────────────────────────────────────
def _lcg(seed):
    s = [seed]

    def r():
        s[0] = (1664525 * s[0] + 1013904223) % 4294967296
        return s[0] / 4294967296
    return r


DEPOTS = [
    {"label": "Harbour", "x": 2.1, "y": 3.4, "group": "Northline", "value": 18},
    {"label": "Old Town", "x": 4.6, "y": 5.2, "group": "Northline", "value": 12.5},
    {"label": "Station", "x": 6.8, "y": 4.1, "group": "Parcelo", "value": 9},
    {"label": "Market", "x": 5.2, "y": 7.9, "group": "Parcelo", "value": 14},
    {"label": "Airport", "x": 10.4, "y": 8.8, "group": "Swiftly", "value": 22.25},
    {"label": "University", "x": 8.1, "y": 9.6, "group": "Swiftly", "value": 11},
    {"label": "Docks East", "x": 11.5, "y": 2.6, "group": "Parcelo", "value": 20},
    {"label": "Ring Road", "x": 8.9, "y": 6.3, "group": "Northline", "value": 8},
    {"label": "Park", "x": 1.4, "y": 8.2, "group": "Swiftly", "value": 16},
    {"label": "Retail Park", "x": 12.3, "y": 6.0, "group": "Northline", "value": 13},
    {"label": "Hospital", "x": 3.5, "y": 10.9, "group": "Parcelo", "value": 10},
    {"label": "Canal", "x": 7.1, "y": 1.7, "group": "Swiftly", "value": 15},
]


def _many(n, seed=9, labels=True):
    r = _lcg(seed)
    return [dict({"x": round(r() * 1000, 1), "y": round(r() * 600, 1)}, **({"label": "S" + str(k)} if labels else {})) for k in range(n)]


PAYLOADS = {
    "depots": {"type": "voronoi", "title": "Nearest depot", "sites": DEPOTS, "x_label": "East (km)", "y_label": "North (km)", "unit": "min"},
    "no_groups": {"type": "voronoi", "sites": [{"label": "A", "x": 1, "y": 1}, {"label": "B", "x": 6, "y": 2}, {"label": "C", "x": 3, "y": 7}, {"label": "D", "x": 8, "y": 8}, {"label": "E", "x": 5, "y": 4.5}, {"label": "F", "x": 9.5, "y": 5}]},
    "no_labels": {"type": "voronoi", "sites": [{"x": 1, "y": 1}, {"x": 6, "y": 2}, {"x": 3, "y": 7}, {"x": 8, "y": 8}, {"x": 5, "y": 4.5}]},
    "three": {"type": "voronoi", "sites": [{"label": "North", "x": 5, "y": 9}, {"label": "West", "x": 1, "y": 1}, {"label": "East", "x": 9, "y": 2}]},
    "collinear": {"type": "voronoi", "title": "A line of sites", "sites": [{"label": "p", "x": 1, "y": 1}, {"label": "q", "x": 3, "y": 3}, {"label": "r", "x": 4, "y": 4}, {"label": "s", "x": 8, "y": 8}]},
    "grid": {"type": "voronoi", "sites": [{"label": "g%d" % i, "x": i % 5, "y": i // 5, "group": "even" if (i % 5 + i // 5) % 2 == 0 else "odd"} for i in range(25)]},
    "many": {"type": "voronoi", "title": "200 sites", "sites": _many(200), "x_label": "x", "y_label": "y"},
    "many_groups": {"type": "voronoi", "sites": [dict(s, group="G%d" % (k % 10)) for k, s in enumerate(_many(40, 4))]},
    "stretched": {"type": "voronoi", "sites": [{"label": "w", "x": 0, "y": 0}, {"label": "x", "x": 1000, "y": 3}, {"label": "y", "x": 500, "y": 9}, {"label": "z", "x": 250, "y": 1}]},
    "same_x": {"type": "voronoi", "sites": [{"label": "a", "x": 4, "y": 1}, {"label": "b", "x": 4, "y": 5}, {"label": "c", "x": 4, "y": 9}, {"label": "d", "x": 4, "y": 12}]},
    "far": {"type": "voronoi", "sites": [{"label": "n", "x": 1000000, "y": 2000000}, {"label": "m", "x": 1000012, "y": 2000007}, {"label": "o", "x": 1000003, "y": 2000019}, {"label": "p", "x": 1000025, "y": 2000011}]},
    "negative": {"type": "voronoi", "sites": [{"label": "a", "x": -0.003, "y": -1200}, {"label": "b", "x": -0.011, "y": -1160}, {"label": "c", "x": -0.007, "y": -1100}, {"label": "d", "x": -0.002, "y": -1130}]},
    "long_labels": {"type": "voronoi", "sites": [{"label": "A very long depot label x", "x": 1, "y": 1, "group": "A group name that is much too long"}, {"label": "Short", "x": 9, "y": 9}, {"label": "Mid length", "x": 9, "y": 1}, {"label": "Ünïcode ✓", "x": 1, "y": 9}]},
    "dup": {"type": "voronoi", "sites": [{"label": "A", "x": 1, "y": 1}, {"label": "A again", "x": 1, "y": 1}, {"label": "B", "x": 5, "y": 2}, {"label": "C", "x": 2, "y": 6}, {"label": "C copy", "x": 2.0, "y": 6}]},
    "dirty": {"type": "voronoi", "sites": [None, 7, "x", {"x": 1}, {"x": "1", "y": 2}, {"label": "ok1", "x": 1, "y": 2}, {"label": "ok2", "x": 4, "y": 9}, {"label": "ok3", "x": 8, "y": 3}, {"x": 1e30, "y": 1}, {"x": float("nan"), "y": 1}, {"x": True, "y": 1}, [1, 2], {"x": float("inf"), "y": 0}]},
    "too_few": {"type": "voronoi", "title": "T", "sites": [{"x": 1, "y": 1}, {"x": 2, "y": 2}]},
    "too_few_distinct": {"type": "voronoi", "sites": [{"x": 1, "y": 1}, {"x": 1, "y": 1}, {"x": 5, "y": 5}, {"x": 5, "y": 5}]},
    "not_list": {"type": "voronoi", "sites": {"x": 1, "y": 2}},
    "missing": {"type": "voronoi", "title": "T"},
    "cap": {"type": "voronoi", "sites": _many(201, 11)},
    "values": {"type": "voronoi", "sites": [{"label": "v1", "x": 1, "y": 1, "value": 1234.5}, {"label": "v2", "x": 6, "y": 2, "value": "x"}, {"label": "v3", "x": 3, "y": 7, "value": float("inf")}, {"label": "v4", "x": 8, "y": 8, "value": -2}], "unit": "kg"},
    "odd_fields": {"type": "voronoi", "sites": [{"label": 5, "x": 1, "y": 1, "group": 7}, {"label": ["a", "b"], "x": 6, "y": 2, "group": True}, {"label": {"q": 1}, "x": 3, "y": 7}, {"x": 8, "y": 8, "group": ""}], "unit": ["a"], "x_label": 4, "y_label": {"k": 1}},
    "version_2": {"type": "voronoi", "version": 2, "sites": DEPOTS[:5]},
    "version_junk": {"type": "voronoi", "version": True, "sites": DEPOTS[:5]},
    "plain": {"type": "voronoi", "sites": DEPOTS[:5]},
}


@pytest.fixture(scope="module")
def gas(core_js):
    names = list(PAYLOADS)
    return dict(zip(names, _gas_batch(core_js, [PAYLOADS[n] for n in names])))


@lru_cache(maxsize=None)
def py(name):
    return _py(PAYLOADS[name])


@pytest.mark.parametrize("name", list(PAYLOADS))
def test_python_and_gas_emit_identical_html(name, gas):
    assert py(name) == gas[name]


def _tables(html):
    out = []
    for m in re.finditer(r'<table style="position:absolute[^"]*"><thead><tr>(.*?)</tr></thead><tbody>(.*?)</tbody></table>', html, re.S):
        out.append((re.findall(r'<th scope="col">(.*?)</th>', m.group(1)), [re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', r) for r in re.findall(r'<tr>(.*?)</tr>', m.group(2), re.S)]))
    return out


def _aria(html):
    return re.search(r'role="img" aria-label="([^"]*)"', html).group(1)


def _cells(html):
    return re.findall(r'<g class="vog" style="([^"]*)"><path class="voc" d="([^"]*)" fill="([^"]*)" fill-opacity="([^"]*)" style="([^"]*)"[^>]*/><circle class="vod" cx="([^"]*)" cy="([^"]*)"[^>]*/><title>(.*?)</title></g>', html)


def _bounds(sites):
    xs, ys = [s["x"] for s in sites], [s["y"] for s in sites]

    def ax(lo, hi):
        if lo == hi:
            lo, hi = lo - 1, hi + 1
        m = (hi - lo) * 0.05
        return wa._hg_nice(lo - m, hi + m, 6)
    return ax(min(xs), max(xs)) + ax(min(ys), max(ys))


def _model(name):
    """The diagram as the port computes it (which the golden holds exact): bounds, cells in data space, the plot height."""
    sites = PAYLOADS[name]["sites"]
    X0, X1, Y0, Y1 = _bounds(sites)
    r = wa._vo_voronoi([[s["x"], s["y"]] for s in sites], [X0, Y0, X1, Y1])
    return sites, (X0, X1, Y0, Y1), r["cells"], r["points"]


def test_bounds_are_the_sites_extent_plus_five_percent_niced_and_no_site_touches_the_border(gas):
    for name in ("depots", "many", "negative", "far", "stretched"):
        sites = PAYLOADS[name]["sites"]
        X0, X1, Y0, Y1 = _bounds(sites)
        xs, ys = [s["x"] for s in sites], [s["y"] for s in sites]
        assert X0 < min(xs) and X1 > max(xs) and Y0 < min(ys) and Y1 > max(ys)
        assert X0 <= min(xs) - 0.05 * (max(xs) - min(xs)) + 1e-9 * (X1 - X0)
        for html in (py(name), gas[name]):
            ex = re.findall(r'<div class="hgx[^"]*"[^>]*><div [^>]*></div><div [^>]*>(.*?)</div></div>', html)
            ticks = wa._hg_ticks(X0, X1, 6)
            dec = wa._hg_decimals(ticks)
            assert ex[0] == wa._hg_num(ticks[0], dec) or len(ex) < len(ticks)               # a narrow tier may thin the labels, the first stays


def test_cells_are_drawn_from_the_d3_polygons_in_site_order(gas):
    sites, (X0, X1, Y0, Y1), cells, pts = _model("depots")
    W = 600
    H = wa._if_round(min(600, max(200, W * (Y1 - Y0) / (X1 - X0))))
    for html in (py("depots"), gas["depots"]):
        got = _cells(html)
        assert len(got) == 12
        assert 'viewBox="0 0 600 %d"' % H in html
        for (style, d, fill, op, stroke, cx, cy, title), poly, s in zip(got, cells, sites):
            exp = "M" + "L".join(wa._cn_r((x - X0) * W / (X1 - X0)) + "," + wa._cn_r((Y1 - y) * H / (Y1 - Y0)) for x, y in poly[:-1]) + "Z"
            assert d == exp
            assert cx == wa._cn_r((s["x"] - X0) * W / (X1 - X0)) and cy == wa._cn_r((Y1 - s["y"]) * H / (Y1 - Y0))
            assert s["label"] in title and s["group"] in title


def test_cells_are_light_fills_by_group_and_the_legend_names_every_group(gas):
    for html in (py("depots"), gas["depots"]):
        got = _cells(html)
        fills = {}
        for (_, _, fill, op, stroke, *_r), s in zip(got, DEPOTS):
            fills.setdefault(s["group"], set()).add(fill)
            assert float(op) <= 0.3 and re.fullmatch(r"#[0-9A-F]{6}", fill)
        assert [len(v) for v in fills.values()] == [1, 1, 1] and len({next(iter(v)) for v in fills.values()}) == 3        # one colour per group, three groups
        leg = re.search(r'<div class="voleg"[^>]*>(.*?)</div>', html, re.S).group(1)
        items = re.findall(r'<span style="display:inline-flex[^>]*><span [^>]*></span>(.*?)</span>', leg)
        assert items == ["Northline", "Parcelo", "Swiftly"]                                                                  # first-appearance order


def test_no_groups_is_one_light_fill_with_outlines_and_no_legend(gas):
    for html in (py("no_groups"), gas["no_groups"]):
        got = _cells(html)
        assert len({c[2] for c in got}) == 1 and all(float(c[3]) <= 0.3 for c in got)
        assert all("stroke-width" in html and c[4] for c in got) and 'class="voleg"' not in html


def test_ungrouped_sites_among_groups_are_listed_in_the_legend_as_no_group(gas):
    for html in (py("odd_fields"), gas["odd_fields"]):
        leg = re.search(r'<div class="voleg"[^>]*>(.*?)</div>', html, re.S).group(1)
        assert "No group" in leg
    for html in (py("grid"), gas["grid"]):
        leg = re.search(r'<div class="voleg"[^>]*>(.*?)</div>', html, re.S).group(1)
        assert re.findall(r'<span style="display:inline-flex[^>]*><span [^>]*></span>(.*?)</span>', leg) == ["even", "odd"]


def test_svg_has_no_script_and_is_aria_hidden_inside_the_labelled_image(gas):
    for html in (py("depots"), gas["depots"], py("many")):
        assert "<script" not in html and "NaN" not in html and "undefined" not in html and "Infinity" not in html and "[object Object]" not in html
        t = html.index("<table")
        assert 'role="img"' in html[:t] and 'role="img"' not in html[t:]
        assert '<svg viewBox="0 0 600 ' in html and 'aria-hidden="true"' in html
        assert "var(--text,#0F172A)" in html and "var(--surface,#F8FAFC)" in html and "var(--border,#CBD5E1)" in html


def _shoelace_share(poly, X0, Y0, X1, Y1):
    return _shoelace(poly, X0, Y0) / ((X1 - X0) * (Y1 - Y0))


def test_hidden_table_has_site_x_y_group_value_and_share_of_the_area(gas):
    sites, (X0, X1, Y0, Y1), cells, _ = _model("depots")
    for html in (py("depots"), gas["depots"]):
        (head, rows), = _tables(html)
        assert head == ["Site", "x", "y", "Group", "Value", "Share of the area"]
        assert len(rows) == 12
        for row, s, poly in zip(rows, sites, cells):
            assert row[0] == s["label"] and row[1] == wa._if_numstr(s["x"]) and row[2] == wa._if_numstr(s["y"]) and row[3] == s["group"]
            assert row[4] == wa._bp_fmt(s["value"], 2) + " min"
            assert row[5] == wa._if_fixed(_shoelace_share(poly, X0, Y0, X1, Y1) * 100, 1) + "%"
        assert abs(sum(float(r[5][:-1]) for r in rows) - 100) < 0.7
        assert 'role="img"' not in html[html.index("<table"):]


def test_table_fills_in_for_missing_labels_groups_and_values(gas):
    for html in (py("no_labels"), gas["no_labels"]):
        (head, rows), = _tables(html)
        assert [r[0] for r in rows] == ["Site 1", "Site 2", "Site 3", "Site 4", "Site 5"]
        assert all(r[3] == "No group" and r[4] == "—" for r in rows)
    for html in (py("values"), gas["values"]):
        (head, rows), = _tables(html)
        assert [r[4] for r in rows] == ["1,234.5 kg", "—", "—", "-2 kg"]


def test_aria_label_gives_site_count_groups_and_the_largest_region(gas):
    sites, (X0, X1, Y0, Y1), cells, _ = _model("depots")
    areas = [_shoelace_share(p, X0, Y0, X1, Y1) for p in cells]
    k = areas.index(max(areas))
    for html in (py("depots"), gas["depots"]):
        assert _aria(html) == "Nearest-site regions of 12 sites in 3 groups. Largest region: %s, %s%% of the area." % (sites[k]["label"], wa._if_fixed(areas[k] * 100, 1))
    for html in (py("no_groups"), gas["no_groups"]):
        assert re.fullmatch(r"Nearest-site regions of 6 sites\. Largest region: [A-F], \d+\.\d% of the area\.", _aria(html))
    assert "Largest region: Site " in _aria(py("no_labels"))


def test_value_is_in_the_tooltip_and_the_table_only(gas):
    for html in (py("depots"), gas["depots"]):
        titles = [c[7] for c in _cells(html)]
        assert titles[1].startswith("Old Town (Northline): 12.5 min, ") and titles[1].endswith("% of the area")
        assert not re.search(r'<div class="vol[^>]*>[^<]*12\.5', html)


def test_duplicate_positions_are_merged_into_the_first_with_a_note(gas):
    for html in (py("dup"), gas["dup"]):
        assert len(_cells(html)) == 3
        assert "2 sites shared a position with an earlier site and were merged into it." in html
        (_, rows), = _tables(html)
        assert [r[0] for r in rows] == ["A", "B", "C"]


def test_each_kind_of_bad_input_gets_its_own_note_and_never_throws(gas):
    expect = {
        "missing": "A Voronoi diagram needs a list of sites, each with a numeric x and y.",
        "not_list": "A Voronoi diagram needs a list of sites, each with a numeric x and y.",
        "too_few": "A Voronoi diagram needs at least 3 sites at different positions; this list has 2.",
        "too_few_distinct": "A Voronoi diagram needs at least 3 sites at different positions; this list has 2.",
    }
    for name, note in expect.items():
        for html in (py(name), gas[name]):
            assert note in html, (name, html[:300])
            assert 'role="img"' not in html and "<svg" not in html and "<table" not in html and "NaN" not in html and "undefined" not in html and "[object Object]" not in html
    assert ">T</div>" in py("too_few")


def test_unusable_entries_are_dropped_with_a_count(gas):
    for html in (py("dirty"), gas["dirty"]):
        assert "10 entries were not a site with a finite numeric x and y and were left out." in html
        assert len(_cells(html)) == 3 and "NaN" not in html and "Infinity" not in html and "undefined" not in html


def test_cap_of_200_sites_has_a_note(gas):
    for html in (py("cap"), gas["cap"]):
        assert "1 site beyond the first 200 was not used." in html
        assert len(_cells(html)) == 200 and len(_tables(html)[0][1]) == 200


def test_odd_fields_are_coerced_never_breaking(gas):
    for html in (py("odd_fields"), gas["odd_fields"]):
        assert "NaN" not in html and "undefined" not in html and "[object Object]" not in html and 'role="img"' in html
        (_, rows), = _tables(html)
        assert rows[0][0] == "5" and rows[0][3] == "7"                                    # a number is text; a list, an object and a boolean are not
        assert [r[0] for r in rows[1:3]] == ["Site 2", "Site 3"] and rows[1][3] == rows[2][3] == rows[3][3] == "No group"


def test_stretched_area_is_noted_and_the_height_is_clamped(gas):
    for html in (py("stretched"), gas["stretched"]):
        assert 'viewBox="0 0 600 200"' in html
        assert "The x and y scales differ in this drawing" in html
    assert "The x and y scales differ" not in py("depots")
    assert "The x and y scales differ" not in py("many")


def test_a_flat_axis_and_far_coordinates_still_draw_without_nan(gas):
    for n in ("same_x", "far", "negative", "collinear", "three"):
        for html in (py(n), gas[n]):
            assert "NaN" not in html and "Infinity" not in html and "undefined" not in html and len(_cells(html)) >= 3, n


def test_axes_use_nice_ticks_in_data_units(gas):
    for html in (py("depots"), gas["depots"]):
        yl = re.findall(r'<div class="voy[^"]*"[^>]*>(.*?)</div>', html)
        sites, (X0, X1, Y0, Y1), _, _ = _model("depots")
        ty = wa._hg_ticks(Y0, Y1, 6)
        assert yl == [wa._hg_num(v, wa._hg_decimals(ty)) for v in ty]
        assert "East (km)" in html and "North (km)" in html


def test_motion_index_per_site_stays_inside_its_clamp(gas):
    for html in (py("depots"), gas["depots"]):
        ks = re.findall(r'<g class="vog" style="--k:clamp\(0,calc\(var\(--p,1\)\*(\d+) - (\d+)\),1\);opacity:var\(--k,1\);"', html)
        assert [int(i) for _, i in ks] == list(range(12)) and all(int(n) == 13 for n, _ in ks)


def _expected_gate(name, i):
    """The label rule: the site's inscribed circle (its distance to the nearest cell edge, in drawing units) must hold the label placed 7 px below it."""
    sites, (X0, X1, Y0, Y1), cells, _ = _model(name)
    W = 600
    H = wa._if_round(min(600, max(200, W * (Y1 - Y0) / (X1 - X0))))
    poly = [((x - X0) * W / (X1 - X0), (Y1 - y) * H / (Y1 - Y0)) for x, y in cells[i]]
    px, py_ = (sites[i]["x"] - X0) * W / (X1 - X0), (Y1 - sites[i]["y"]) * H / (Y1 - Y0)
    best = float("inf")
    for (ax, ay), (bx, by) in zip(poly, poly[1:]):
        dx, dy = bx - ax, by - ay
        l2 = dx * dx + dy * dy
        if l2 == 0:
            continue
        t = min(1.0, max(0.0, ((px - ax) * dx + (py_ - ay) * dy) / l2))
        ex, ey = ax + t * dx - px, ay + t * dy - py_
        best = min(best, math.sqrt(ex * ex + ey * ey))
    chars = len(str(sites[i]["label"]).encode("utf-16-le")) // 2
    wt = chars * 7.2 + 8
    need = math.sqrt((wt / 2) ** 2 + 21 ** 2)
    return wa._cp_q(need * 600 / best + sum(_margins(name)))


def _margins(name):
    """The plot's left and right margins: the widest y label (and half the widest x label) in 7.2 px a character, never under 54 and 30 px."""
    sites, (X0, X1, Y0, Y1), _, _ = _model(name)
    ex, ey = wa._hg_ticks(X0, X1, 6), wa._hg_ticks(Y0, Y1, 6)
    xl = [wa._hg_num(v, wa._hg_decimals(ex)) for v in ex]
    yl = [wa._hg_num(v, wa._hg_decimals(ey)) for v in ey]
    return max(54, math.ceil(max(len(t) for t in yl) * 7.2) + 14), max(30, math.ceil(max(len(t) for t in xl) * 7.2 / 2) + 8)


def test_the_plot_margins_grow_with_the_widest_axis_label_so_none_is_clipped(gas):
    assert _margins("depots") == (54, 30) and _margins("far")[0] > 54 and _margins("far")[1] > 30
    for html in (py("far"), gas["far"]):
        ml, mr = _margins("far")
        assert 'style="position:relative;margin:8px %dpx 34px %dpx;"' % (mr, ml) in html


def test_y_labels_are_thinned_by_the_plot_height_in_both_twins(gas):
    for name in ("stretched", "depots", "far"):
        sites, (X0, X1, Y0, Y1), _, _ = _model(name)
        H = wa._if_round(min(600, max(200, 600 * (Y1 - Y0) / (X1 - X0))))
        n = len(wa._hg_ticks(Y0, Y1, 6))
        padx = sum(_margins(name))
        exp = []
        for i in range(n):
            k = 0 if i == 0 else min((i & -i).bit_length() - 1, 3)
            wm = 0 if (i == 0 or n < 2) else wa._cp_q(padx + 16 * (n - 1) * 600 / ((1 << k) * H))
            exp.append(" tmw%d" % wm if wm > 240 else "")
        for html in (py(name), gas[name]):
            assert re.findall(r'<div class="voy( tmw\d+)?"', html) == exp, name
    assert re.findall(r'<div class="voy( tmw\d+)?"', py("stretched"))[1] != ""        # a flat plot hides its odd labels in a narrow container


def test_labels_are_gated_by_the_inscribed_circle_and_hidden_when_they_can_never_fit(gas):
    for name in ("depots", "no_groups", "many"):
        for html in (py(name), gas[name]):
            labs = re.findall(r'<div class="vol( tmw\d+)?" style="[^"]*">(.*?)</div>', html)
            by_label = {t: g for g, t in labs}
            sites = PAYLOADS[name]["sites"]
            shown = 0
            for i, s in enumerate(sites):
                wm = _expected_gate(name, i)
                lab = wa._cv_esc(s["label"])
                if wm > 820:
                    assert lab not in by_label, (name, lab)
                else:
                    shown += 1
                    assert by_label[lab] == (" tmw%d" % wm if wm > 240 else ""), (name, lab, wm, by_label.get(lab))
            assert shown == len(labs)
            css = re.search(r'<style>(.*?)</style>', html).group(1)
            gates = sorted({int(g) for g in re.findall(r'tmw(\d+)', "".join(g for g, _ in labs))})
            assert all('@container (width<%dpx){.tmw%d{display:none}}' % (g, g) in css for g in gates)


def test_unlabelled_sites_get_no_label_and_the_full_label_is_always_in_the_title_and_table(gas):
    for html in (py("no_labels"), gas["no_labels"]):
        assert 'class="vol' not in html
    for html in (py("long_labels"), gas["long_labels"]):
        titles = [c[7] for c in _cells(html)]
        assert "A very long depot label" in titles[0] and "Ünïcode ✓" in titles[3]
        (_, rows), = _tables(html)
        assert rows[0][0] == "A very long depot label x"[:24] and rows[0][3] == "A group name that is"


def test_caps_on_text_lengths(gas):
    for html in (py("long_labels"), gas["long_labels"]):
        (_, rows), = _tables(html)
        assert len(rows[0][0]) <= 24 and len(rows[0][3]) <= 20


def test_version_above_one_is_noted_and_otherwise_silent(gas):
    for html in (py("version_2"), gas["version_2"]):
        assert "Written for voronoi version 2; drawn as version 1." in html
    assert "version" not in py("version_junk").lower()
    assert py("version_junk") == py("plain") == py("version_junk")


def test_hostile_text_is_escaped_in_both_twins(core_js):
    b = {"type": "voronoi", "title": ATTACK, "x_label": ATTACK, "y_label": ATTACK, "unit": ATTACK,
         "sites": [{"label": ATTACK, "group": ATTACK, "x": 1, "y": 1, "value": 3}, {"label": "b", "group": ATTACK + "2", "x": 5, "y": 2}, {"label": "c", "x": 3, "y": 6}]}
    outs = [_py(b), _gas_batch(core_js, [b])[0]]
    assert outs[0] == outs[1]
    for h in outs:
        assert "<img" not in h and "<svg onload" not in h and "<script" not in h.replace("<style", "") and 'onerror=alert(1)>' not in h.replace("&gt;", "")
        assert "&lt;img" in h


def test_a_broken_diagram_never_throws(core_js):
    # sites so close that the arithmetic has nothing to separate: still a note or a drawing, never an exception, in both twins
    blocks = [{"type": "voronoi", "sites": [{"x": 1e12 - k * 1e-4, "y": 1e12 + k * 3e-4} for k in range(5)]},
              {"type": "voronoi", "sites": [{"x": k * 1e-300, "y": 0} for k in range(5)]},
              {"type": "voronoi", "sites": [{"x": 5e11 * (k % 2), "y": 5e11 * (k // 2)} for k in range(4)]}]
    outs = _gas_batch(core_js, blocks)
    for b, g in zip(blocks, outs):
        h = _py(b)
        assert h == g and "NaN" not in h and "undefined" not in h and "Infinity" not in h


# ─── registration ──────────────────────────────────────────────────────────────────────────────────────────────
def test_registered_as_a_preview_charts_atom_with_an_example_and_every_field_documented():
    blocks = {a["type"]: a for a in yaml.safe_load((ROOT / "atoms/schema.yaml").read_text())["blocks"]}
    a = blocks["voronoi"]
    assert a["stage"] == "preview" and set(a["fields"]) == {"title", "sites", "x_label", "y_label", "unit", "version"}
    assert a["surfaces"] == blocks["treemap"]["surfaces"] and a["source"] == blocks["treemap"]["source"]
    assert len(a["intent_phrases"]) == 3 and a["routing_text"] and "choropleth" in a["routing_text"] and "cluster" in a["routing_text"] and a["compact_description"] and a["notes"]
    assert re.search(r"^a2ui-charts-v1:\n(?:- .*\n)*- voronoi$", (ROOT / "atoms/atom-packs.yaml").read_text(), re.M)
    assert '"voronoi":"a2ui-charts-v1"' in (ROOT / "apps-script-surface/gas-wired-renderer/PackMap.gs").read_text()
    text = (ROOT / "atoms/schema.yaml").read_text()
    assert text.index("- type: voronoi") < text.index("# ── Motion candidates (2026-10-10, preview) ──")
    import generate_atom_pages as g
    ex = g._EXAMPLE_BLOCKS["voronoi"]
    assert ex["type"] == "voronoi" and "<table" in _py(ex) and 'role="img"' in _py(ex) and len(ex["sites"]) == 12


def test_third_party_notices_credit_the_three_modules_with_their_licences():
    t = (ROOT / "THIRD-PARTY-NOTICES.md").read_text()
    assert "d3-delaunay" in t and "delaunator" in t and "robust-predicates" in t
    assert "Mapbox" in t
