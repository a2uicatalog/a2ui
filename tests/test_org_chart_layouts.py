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


# ─── what is drawn ─────────────────────────────────────────────────────────────
BOX = re.compile(r'<div style="position:absolute;left:([\d.]+)%;top:([\d.]+)%;width:([\d.]+)%;height:(\d+)px;')
LABEL = re.compile(r'>(L\d+x*[^<]*)</div>')
KEY = re.compile(r'var\(--p,1\)\*(\d+)\s*-\s*(\d+)\)')
BAD = re.compile(r"NaN|undefined|Infinity|\[object|<script")


def _labels_in_order(html):
    """The text of every node, in document order: what a screen reader reads from the nested list."""
    got = re.findall(r'<div (?:class="ocr-l"[^>]*|style="position:absolute;left:[^"]*line-height:1\.25[^"]*")>([^<]*)</div>', html)
    return got[:len(got) // 2] if 'data-oc="both"' in html else got          # a wide tree carries a second, left-to-right copy of the boxes


def _cluster_payload(g):
    kids = g["kids"]
    forest = g["forest"]
    parent = {c: i for i, ks in enumerate(kids) for c in ks}
    nodes = []
    for i in range(1 if forest else 0, len(kids)):
        p = parent.get(i)
        nodes.append({"id": "n%d" % i, "label": g["labels"][i], "parent_id": "" if (p is None or (forest and p == 0)) else "n%d" % p})
    return {"type": "org_chart", "title": "T", "nodes": nodes, "layout": "cluster"}


@pytest.mark.parametrize("name", [n for n in CL_CASES if not CL_CASES[n]["forest"] or n == "forest_virtual_root"][:40])
def test_cluster_boxes_follow_the_d3_cluster_layout_in_both_twins(name, core_js):
    g = CL_CASES[name]
    block = _cluster_payload(g)
    forest = g["forest"]
    first = 1 if forest else 0
    idx = list(range(first, len(g["kids"])))
    sh = 1 if forest else 0
    nh = g["nh"]
    lo = min(g["x"][i] - g["w"][i] / 2 for i in idx)
    hi = max(g["x"][i] + g["w"][i] / 2 for i in idx)
    tiers = max(g["row"][i] - sh for i in idx) + 1
    rowh = nh + 28
    ht = tiers * rowh - 28
    wide = hi - lo > 640
    for html in (_py(block), _gas_batch(core_js, [block])[0]):
        assert 'data-oc-layout="cluster"' in html and not BAD.search(html)
        boxes = BOX.findall(html)
        assert len(boxes) == len(idx) * (2 if wide else 1)
        labels = LABEL.findall(html)
        by_idx = {int(re.match(r"L(\d+)", l).group(1)): b for l, b in zip(labels[:len(idx)], boxes[:len(idx)])}
        for i in idx:
            l, t, w, _ = by_idx[i]
            assert abs(float(l) - max(0, (g["x"][i] - g["w"][i] / 2 - lo) / (hi - lo) * 100)) <= 2e-3, (name, i)
            assert abs(float(t) - (g["row"][i] - sh) * rowh / ht * 100) <= 2e-3, (name, i)
            assert abs(float(w) - g["w"][i] / (hi - lo) * 100) <= 2e-3, (name, i)
        assert all(int(m) - int(i) >= 1 for m, i in KEY.findall(html))


def test_cluster_puts_every_leaf_on_the_last_tier_and_trees_do_not():
    nodes = [("r", "Root", ""), ("a", "Shallow leaf", "r"), ("b", "Branch", "r"), ("c", "Deeper", "b"), ("d", "Deepest", "c")]
    blk = {"type": "org_chart", "nodes": [{"id": i, "label": l, "parent_id": p} for i, l, p in nodes]}
    tops = lambda h: {re.search(r">([^<]*)</div>", m).group(1): float(t) for m, t in re.findall(r'(<div style="position:absolute;left:[\d.]+%;top:([\d.]+)%[^>]*>[^<]*</div>)', h)}
    tree, clu = tops(_py(blk)), tops(_py(dict(blk, layout="cluster")))
    assert tree["Shallow leaf"] < tree["Deepest"] and clu["Shallow leaf"] == clu["Deepest"] == max(clu.values())
    assert clu["Root"] == 0


def test_cluster_links_never_run_through_a_box():
    """Leaves skip tiers; their links drop through the skipped tiers, which must be clear of boxes. Checked on the rendered geometry."""
    bad = []
    for n, p in CORPUS.items():
        html = _py(dict(p, layout="cluster"))
        if 'data-oc="td"' not in html and 'data-oc="both"' not in html:
            continue
        td = html.split('class="ocl"')[0] if 'class="ocl"' in html else html
        m = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', td)
        if not m:
            continue
        cw, ch = float(m.group(1)), float(m.group(2))
        boxes = [(float(l) / 100 * cw, float(t) / 100 * ch, float(w) / 100 * cw, int(h)) for l, t, w, h in BOX.findall(td)]
        for d in re.findall(r'<path d="M([\d.]+) ([\d.]+)V([\d.]+)H([\d.]+)V([\d.]+)"', td):
            x0, y0, yb, x1, y1 = map(float, d)
            for bx, by, bw, bh in boxes:       # the vertical at x1 from yb to y1, and the bus at yb from x0 to x1
                if bx + 0.01 < x1 < bx + bw - 0.01 and by + 0.01 < y1 and by + bh > yb + 0.01 and by < y1 - 0.01:
                    bad.append((n, "vertical", x1))
                lo_, hi_ = sorted((x0, x1))
                if by < yb < by + bh and bx < hi_ and bx + bw > lo_:
                    bad.append((n, "bus", yb))
    assert not bad, bad[:5]


def test_layouts_keep_the_same_hierarchy_for_a_screen_reader(core_js):
    """The tree has no aria-label and no hidden table: the nested list carries the hierarchy. Cluster and radial keep exactly that."""
    for n in ("leadership", "golden_tree30_max", "malformed", "hostile", "golden_forest_virtual_root", "fuzz3"):
        t = _py(CORPUS[n])
        assert "<table" not in t and "aria-label" not in t
        for lay in ("cluster", "radial"):
            h = _py(dict(CORPUS[n], layout=lay))
            assert "<table" not in h and "aria-label" not in h and h.count("<ul") == h.count("</ul>") and h.count("<li ") == h.count("</li>")
            exp = [re.sub(r"\s+", " ", x) for x in _labels_in_order(t)]
            got = [re.sub(r"\s+", " ", x) for x in _labels_in_order(h)]
            assert got == exp and got, (n, lay)
            assert h.count("<li ") == len(got) * (2 if 'data-oc="both"' in h else 1)


def test_python_and_gas_emit_identical_html_for_every_payload_in_both_layouts(core_js):
    names = list(CORPUS)
    for lay in ("cluster", "radial"):
        blocks = [dict(CORPUS[n], layout=lay) for n in names]
        gas = _gas_batch(core_js, blocks)
        bad = [n for n, b, g in zip(names, blocks, gas) if _norm(_py(b)) != _norm(g)]
        assert not bad, (lay, bad)


def test_the_cluster_and_radial_of_every_payload_have_no_nan_or_script(core_js):
    for n, p in CORPUS.items():
        for lay in ("cluster", "radial"):
            assert not BAD.search(_py(dict(p, layout=lay))), (n, lay)


def test_wide_clusters_carry_both_orientations_like_the_tree():
    h = _py(dict(CORPUS["golden_tree20"], layout="cluster"))
    assert 'data-oc="both"' in h and "@container (min-width:" in h and 'class="ocl"' in h and "@media print" in h
    assert 'data-oc="td"' in _py(dict(CORPUS["small"], layout="cluster"))


# ─── radial ────────────────────────────────────────────────────────────────────
LBL = re.compile(r'<div class="ocr-l"[^>]*?(?: title="([^"]*)")? style="position:absolute;left:([\d.]+)%;top:([\d.]+)%;[^"]*?--la:(\d+)px;--lb:(\d+)px;transform-origin:0 0;transform:rotate\((-?[\d.]+)deg\) translate\(([^)]*\)?[^)]*)\)[^"]*">([^<]*)</div>')
DOT = re.compile(r'<div aria-hidden="true" style="position:absolute;left:([\d.]+)%;top:([\d.]+)%;width:(\d+)px;')


def test_radial_text_is_never_upside_down_and_the_right_half_is_not_flipped():
    for n in ("leadership", "golden_tree30_max", "fuzz5", "golden_forest_virtual_root"):
        h = _py(dict(CORPUS[n], layout="radial"))
        ls = LBL.findall(h)
        assert ls and len(ls) == h.count("<li ")
        for title, left, top, la, lb, deg, tr, text in ls:
            assert -90.01 <= float(deg) <= 90.01, (n, deg)                       # the text always reads left to right, within a quarter turn of level
            assert ("calc(-100% - 9px)" in tr) == (float(left) < 50 - 1e-6 or (abs(float(left) - 50) < 0.5 and False)) or abs(float(left) - 50) < 3, (n, left, tr)


def test_radial_chart_is_a_square_that_scales_and_never_widens_its_container():
    h = _py(dict(CORPUS["golden_tree30_max"], layout="radial"))
    assert "aspect-ratio:1/1" in h and "width:100%" in h and "max-width:640px" in h and "min-width:300px" in h
    assert 'viewBox="0 0 1000 1000"' in h and "contain:inline-size" in h and "overflow-x:auto" in h


def test_radial_labels_are_fitted_with_an_ellipsis_and_the_full_text_stays():
    n = {"type": "org_chart", "layout": "radial", "nodes": [{"id": "r", "label": "Chief executive officer", "parent_id": ""}] +
         [{"id": "c%d" % i, "label": "Long department name %d" % i, "parent_id": "r"} for i in range(6)] +
         [{"id": "g%d" % i, "label": "Subteam long label %d" % i, "parent_id": "c%d" % (i % 6)} for i in range(12)]}
    h = _py(n)
    assert "text-overflow:ellipsis" in h and "overflow:hidden" in h and "white-space:nowrap" in h
    assert "Chief executive officer</div>" in h and "Long department name 3</div>" in h     # the whole text is in the DOM
    cut = [t for t in LBL.findall(h) if t[0]]
    assert cut and all(t[0] == t[7] for t in cut)                                                  # a title carries the full text where it can be cut
    for t in LBL.findall(h):
        assert 14 <= int(t[3]) <= 210 and 14 <= int(t[4]) <= 210 and int(t[3]) <= int(t[4])         # narrow-side length never above the wide-side one


def test_radial_label_boxes_never_touch_each_other_or_a_dot_or_leave_the_square():
    """Geometry from the emitted numbers: every label's oriented box at the chart sides 300..640, in steps of 10."""
    import math
    worst = []
    for n, p in CORPUS.items():
        h = _py(dict(p, layout="radial"))
        ls = LBL.findall(h)
        dots = [(float(l), float(t), int(w) / 2) for l, t, w in DOT.findall(h)]
        for side in range(300, 641, 10):
            lens = [int(x[3] if side < 520 else x[4]) for x in ls]
            boxes = []
            for (title, left, top, la, lb, deg, tr, text), L in zip(ls, lens):
                a = math.radians(float(deg)) + (math.pi if "calc(-100%" in tr else 0)
                cx, cy = float(left) / 100 * side, float(top) / 100 * side
                ux, uy = math.cos(a), math.sin(a)
                m = 9 + L / 2
                boxes.append((cx + m * ux, cy + m * uy, ux, uy, L / 2, 7.5))
                for k in (-1, 1):                                  # inside the square
                    for e in (0, 1):
                        ex, ey = cx + (9 + L * e) * ux - k * 7.5 * uy, cy + (9 + L * e) * uy + k * 7.5 * ux
                        if not (-0.5 <= ex <= side + 0.5 and -0.5 <= ey <= side + 0.5):
                            worst.append((n, side, "outside"))
            for i in range(len(boxes)):
                for j in range(i + 1, len(boxes)):
                    if wa._oc_rad_hit(boxes[i], boxes[j], 0):
                        worst.append((n, side, "labels", i, j))
                for k, (dl, dt, dr) in enumerate(dots):
                    if k != i and wa._oc_rad_dot(boxes[i], dl / 100 * side, dt / 100 * side, dr, 0):
                        worst.append((n, side, "dot", i, k))
    assert not worst, (len(worst), worst[:6])


def test_radial_version_field_and_motion(core_js):
    for lay in ("cluster", "radial", "tree"):
        blk = dict(CORPUS["leadership"], layout=lay)
        for v, note in ((None, False), (1, False), (2, True), (7, True), (1.5, False), ("2", False), (True, False)):
            b = dict(blk) if v is None else dict(blk, version=v)
            for html in (_py(b), _gas_batch(core_js, [b])[0]):
                assert ("Written for org_chart version %s; drawn as version 1." % v in html) == note, (lay, v)
        h = _py(blk)
        assert all(int(m) - int(i) >= 1 for m, i in KEY.findall(h)) and len(KEY.findall(h)) >= 10


def test_radial_hostile_text_is_escaped_in_text_and_title():
    h = _py({"type": "org_chart", "layout": "radial", "nodes": [{"id": "a", "label": '"><img src=x onerror=alert(1)>', "parent_id": ""}, {"id": "b", "label": "a&b", "parent_id": "a"}]})
    assert "<img" not in h and "&lt;img" in h and 'title=""' not in h


def test_radial_forest_hides_the_virtual_root_and_single_node_has_no_links():
    h = _py(dict(CORPUS["golden_forest_virtual_root"], layout="radial"))
    assert h.count("<li ") == 7 and h.count("<path") == 4
    one = _py({"type": "org_chart", "layout": "radial", "nodes": [{"id": "a", "label": "Only", "parent_id": ""}]})
    assert one.count("<path") == 0 and "Only</div>" in one


def test_radial_fitting_is_fast_enough_for_thirty_nodes():
    import time
    t = time.time()
    _py(dict(CORPUS["golden_tree30_max"], layout="radial"))
    assert time.time() - t < 2.0
