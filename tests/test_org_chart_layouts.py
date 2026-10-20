"""org_chart `layout` (I53 cluster, I55 radial): the layout algorithms against REAL d3-hierarchy 3.1.2, and the guarantee that an absent,
"tree" or unknown `layout` renders exactly what org_chart rendered before the field existed.

GOLDEN, from fixtures/org_chart_cluster_d3_golden_gen.mjs and org_chart_radial_d3_golden_gen.mjs (run on the real d3-hierarchy and d3-shape):
 - cluster: d3.cluster().nodeSize([1, 1]).separation(...) with a pixel separation (see the generator for the rule); x is the box centre in px,
   row the tier row (leaves all on the last row). Python and GAS reproduce x and row EXACTLY (==), because the port keeps d3's operation order.
 - radial: d3.tree().size([2 * Math.PI, 1000]).separation((a, b) => (a.parent == b.parent ? 1 : 2) / a.depth). Angle and radius EXACTLY (==); the
   Cartesian points and the linkRadial Bezier control points to 1e-9, not exactly: they call Math.cos / Math.sin, which V8 (fdlibm) and CPython (libm)
   can differ on by an ulp.
BASELINE (fixtures/org_chart_tree_baseline.json) holds sha256 of what the pre-change renderers produced for every org_chart payload the tests use,
plus malformed and seeded random trees (tests/org_chart_corpus.py).
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

from org_chart_corpus import corpus
from test_motion_atoms import _gas_batch, _node, _py, core_js  # noqa: F401  (core_js is a fixture)
from test_motion_atoms import wa  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures"
BASE = json.loads((FIX / "org_chart_tree_baseline.json").read_text())
CL = json.loads((FIX / "org_chart_cluster_d3_golden.json").read_text())
RD = json.loads((FIX / "org_chart_radial_d3_golden.json").read_text())
CL_CASES = {**CL["golden"], **{c["name"]: c for c in CL["fuzz"]}}
RD_CASES = {**RD["golden"], **{c["name"]: c for c in RD["fuzz"]}}
CORPUS = corpus()


def _norm(h):
    return re.sub(r"\s+", " ", h)


# ─── nothing changes without the field ─────────────────────────────────────────
def test_the_baseline_covers_every_corpus_payload():
    assert set(BASE) == set(CORPUS) and len(CORPUS) >= 70


@pytest.mark.parametrize("name", list(CORPUS))
def test_python_without_layout_is_byte_for_byte_what_it_was(name):
    out = _py(CORPUS[name])
    assert hashlib.sha256(out.encode()).hexdigest() == BASE[name]["py"] and len(out) == BASE[name]["len"]


def test_gas_without_layout_is_byte_for_byte_what_it_was(core_js):
    names = list(CORPUS)
    got = _gas_batch(core_js, [CORPUS[n] for n in names])
    bad = [n for n, g in zip(names, got) if hashlib.sha256(_norm(g).encode()).hexdigest() != BASE[n]["gas"]]
    assert not bad, bad


NOT_A_LAYOUT = ["tree", "TREE", "Tree", "", " ", "grid", "force", "cluster ", "Cluster", "radial1", 0, 1, True, False, None, [], ["tree"], {}, {"layout": "radial"}, 1.5]


def test_tree_and_unknown_layout_values_are_the_tree_in_both_twins(core_js):
    names = list(CORPUS)
    blocks = []
    for n in names:
        for v in NOT_A_LAYOUT[:6] + [NOT_A_LAYOUT[10], NOT_A_LAYOUT[17], NOT_A_LAYOUT[19]]:
            blocks.append(dict(CORPUS[n], layout=v))
    k = 0
    gas = _gas_batch(core_js, blocks)
    for n in names:
        for v in NOT_A_LAYOUT[:6] + [NOT_A_LAYOUT[10], NOT_A_LAYOUT[17], NOT_A_LAYOUT[19]]:
            assert hashlib.sha256(_py(blocks[k]).encode()).hexdigest() == BASE[n]["py"], (n, v)
            assert hashlib.sha256(_norm(gas[k]).encode()).hexdigest() == BASE[n]["gas"], (n, v)
            k += 1


def test_every_not_a_layout_value_is_the_tree_for_a_sample():
    for n in ("leadership", "golden_tree20", "malformed", "fuzz7"):
        for v in NOT_A_LAYOUT:
            assert hashlib.sha256(_py(dict(CORPUS[n], layout=v)).encode()).hexdigest() == BASE[n]["py"], (n, v)


# ─── cluster against d3 ────────────────────────────────────────────────────────
@pytest.mark.parametrize("name", list(CL_CASES))
def test_python_cluster_matches_d3_exactly(name):
    g = CL_CASES[name]
    for size, x, row in ((g["w"], g["x"], g["row"]), (g["hs"], g["ltr_x"], g["ltr_row"]), (g["vw"], g["vx"], g["vrow"]), (g["vh"], g["vlx"], g["vrow"])):
        gx, grow = wa._oc_cluster(g["kids"], 0, size)
        assert gx == x and grow == row, (name, gx, x)


def test_gas_cluster_matches_d3_exactly(core_js):
    names = list(CL_CASES)
    calls = []
    for n in names:
        g = CL_CASES[n]
        calls += [[g["kids"], g["w"]], [g["kids"], g["hs"]], [g["kids"], g["vw"]], [g["kids"], g["vh"]]]
    res = _node(core_js, "var G = " + json.dumps(calls) + "; console.log(JSON.stringify(G.map(function(k){ return _ocCluster(k[0], 0, k[1]); })));")
    for j, n in enumerate(names):
        g = CL_CASES[n]
        assert res[4 * j] == [g["x"], g["row"]] and res[4 * j + 1] == [g["ltr_x"], g["ltr_row"]] and res[4 * j + 2] == [g["vx"], g["vrow"]] and res[4 * j + 3] == [g["vlx"], g["vrow"]], n


def test_the_cluster_golden_covers_the_hard_cases():
    g = CL["golden"]
    assert g["single"]["x"] == [0] and g["chain4"]["row"] == [0, 1, 2, 3]
    assert g["skip_rows"]["row"][1] == max(g["skip_rows"]["row"])                       # a depth-1 leaf is drawn on the last row
    assert len(g["tree30"]["kids"]) == 30 and len(g["six_children"]["kids"][0]) == 6
    assert any(c["forest"] for c in CL["fuzz"]) and len(CL["fuzz"]) >= 70
    for c in list(CL_CASES.values()):                                                   # leaves all on the last row; the parent over the mean of its children
        last = max(c["row"])
        for i, ks in enumerate(c["kids"]):
            if not ks:
                assert c["row"][i] == last, c["name"]
            else:
                assert abs(c["x"][i] - sum(c["x"][k] for k in ks) / len(ks)) < 1e-9, c["name"]


# ─── radial against d3 ─────────────────────────────────────────────────────────
@pytest.mark.parametrize("name", list(RD_CASES))
def test_python_radial_matches_d3(name):
    g = RD_CASES[name]
    x, y, depth = wa._oc_radial(g["kids"], 0, 1000)
    assert x == g["x"] and y == g["y"] and depth == g["depth"], name
    for i in range(len(x)):
        px, py = wa._oc_polar(x[i], y[i])
        assert abs(px - g["pt"][i][0]) <= 1e-9 and abs(py - g["pt"][i][1]) <= 1e-9, (name, i)
        if g["link"][i] is not None:
            par = next(p for p, ks in enumerate(g["kids"]) if i in ks)
            got = wa._oc_link_radial(x[par], y[par], x[i], y[i])
            assert len(got) == 8 and all(abs(a - b) <= 1e-9 for a, b in zip(got, g["link"][i])), (name, i, got, g["link"][i])


def test_gas_radial_matches_d3(core_js):
    names = list(RD_CASES)
    res = _node(core_js, "var G = " + json.dumps([RD_CASES[n]["kids"] for n in names]) + """; console.log(JSON.stringify(G.map(function(k) {
      var r = _ocRadial(k, 0, 1000), pts = [], links = [], i, p, par;
      for (i = 0; i < k.length; i++) {
        pts.push(_ocPolar(r[0][i], r[1][i])); par = -1;
        k.forEach(function(ks, q) { if (ks.indexOf(i) >= 0) par = q; });
        links.push(par < 0 ? null : _ocLinkRadial(r[0][par], r[1][par], r[0][i], r[1][i]));
      }
      return [r, pts, links]; })));""")
    for n, (r, pts, links) in zip(names, res):
        g = RD_CASES[n]
        assert r[0] == g["x"] and r[1] == g["y"] and r[2] == g["depth"], n
        for i, pt in enumerate(pts):
            assert abs(pt[0] - g["pt"][i][0]) <= 1e-9 and abs(pt[1] - g["pt"][i][1]) <= 1e-9, (n, i)
            if g["link"][i] is not None:
                assert all(abs(a - b) <= 1e-9 for a, b in zip(links[i], g["link"][i])), (n, i)
            else:
                assert links[i] is None or n == "x"


def test_the_radial_golden_covers_the_hard_cases():
    g = RD["golden"]
    assert g["single"]["y"] == [0] and g["chain4"]["y"][3] == 1000 and len(g["tree30"]["kids"]) == 30 and len(g["six_children"]["kids"][0]) == 6
    assert any(c["forest"] for c in RD["golden"].values()) and len(RD["fuzz"]) >= 70
    assert max(max(c["depth"]) for c in RD["fuzz"]) >= 3
