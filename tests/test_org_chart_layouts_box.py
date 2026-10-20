"""org_chart cluster and radial in a real browser (headless Chromium): widths 300 (a narrow grid cell), 320, 650, 1200 and 1400 px.

Cluster: the existing tree harness (tests/test_org_chart_layout_box.py: one visible orientation, no overlap, nothing clipped, nothing wider than its
container, connectors end on box edges) run over cluster payloads, plus the 300 px width.
Radial: every label's rotated box (its layout box carried through the computed transform) is checked against every other label's box and against every
node dot (separating-axis test), must lie inside the square, text must be at least 12 px, the chart must be a square no wider than its container
and the container must not scroll sideways at or above 300 px. Test-only script; the atom's own output carries no script.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

import test_org_chart_layout_box as tlb
from org_chart_corpus import corpus
from test_motion_atoms import _gas_batch, _py, core_js  # noqa: F401

CHROME = tlb.CHROME
pytestmark = pytest.mark.skipif(not CHROME, reason="needs chromium")
C = corpus()

HARNESS = r'''<script>
function poly(el, base) {
  var cs = getComputedStyle(el), m = new DOMMatrix(cs.transform), w = el.offsetWidth, h = el.offsetHeight, ox = base.left + el.offsetLeft, oy = base.top + el.offsetTop;
  return [[0, 0], [w, 0], [w, h], [0, h]].map(function (p) { var q = m.transformPoint(new DOMPoint(p[0], p[1])); return [ox + q.x, oy + q.y]; });
}
function axes(P) { var a = [], i; for (i = 0; i < 4; i++) { var j = (i + 1) % 4, dx = P[j][0] - P[i][0], dy = P[j][1] - P[i][1], l = Math.hypot(dx, dy); if (l) a.push([-dy / l, dx / l]); } return a; }
function span(P, a) { var lo = 1e9, hi = -1e9; P.forEach(function (p) { var d = p[0] * a[0] + p[1] * a[1]; lo = Math.min(lo, d); hi = Math.max(hi, d); }); return [lo, hi]; }
function hit(P, Q) { var ax = axes(P).concat(axes(Q)), i; for (i = 0; i < ax.length; i++) { var s = span(P, ax[i]), t = span(Q, ax[i]); if (s[1] <= t[0] + 0.01 || t[1] <= s[0] + 0.01) return false; } return true; }
window.addEventListener('load', function () {
  var res = [];
  document.querySelectorAll('.case').forEach(function (c) {
    var root = c.querySelector('.ifoct'), errs = [], chart = root.children[root.children.length - 1], i, j;
    if (chart.tagName === 'STYLE') chart = root.children[root.children.length - 1];
    var cr = chart.getBoundingClientRect(), vis = root.getBoundingClientRect(), cell = c.firstElementChild.getBoundingClientRect();
    var labels = Array.prototype.slice.call(chart.querySelectorAll('.ocr-l')), dots = Array.prototype.slice.call(chart.querySelectorAll('div[aria-hidden]'));
    var base = {left: 0, top: 0};
    var P = labels.map(function (l) { return poly(l, {left: l.offsetParent === chart ? cr.left : 0, top: l.offsetParent === chart ? cr.top : 0}); });
    if (Math.abs(cr.width - cr.height) > 1.5) errs.push('chart is not square ' + cr.width + 'x' + cr.height);
    if (cr.right > cell.right + 1) errs.push('chart wider than its cell: ' + cr.width + ' > ' + cell.width);
    if (root.scrollWidth > root.clientWidth + 1 && cell.width >= 300) errs.push('container scrolls sideways');
    labels.forEach(function (l, k) {
      if (parseFloat(getComputedStyle(l).fontSize) < 12) errs.push('label ' + k + ' under 12px');
      var ang = Math.atan2(new DOMMatrix(getComputedStyle(l).transform).b, new DOMMatrix(getComputedStyle(l).transform).a) * 180 / Math.PI;
      if (ang > 90.5 || ang < -90.5) errs.push('label ' + k + ' reads upside down: ' + ang);
      P[k].forEach(function (p) { if (p[0] < cr.left - 0.5 || p[0] > cr.right + 0.5 || p[1] < cr.top - 0.5 || p[1] > cr.bottom + 0.5) errs.push('label ' + k + ' outside the chart'); });
    });
    for (i = 0; i < P.length; i++) for (j = i + 1; j < P.length; j++) if (hit(P[i], P[j])) errs.push('labels ' + i + ' and ' + j + ' overlap');
    dots.forEach(function (d, k) {
      var r = d.getBoundingClientRect(), cx = (r.left + r.right) / 2, cy = (r.top + r.bottom) / 2, rad = r.width / 2;
      for (i = 0; i < P.length; i++) {
        if (i === k) continue;
        var ax = axes(P[i]), lo, hi, inside = true, q;
        // circle against polygon: the polygon is a rectangle, so test the centre in the rectangle's own frame
        var o = P[i][0], u = [P[i][1][0] - o[0], P[i][1][1] - o[1]], v = [P[i][3][0] - o[0], P[i][3][1] - o[1]], lu = Math.hypot(u[0], u[1]), lv = Math.hypot(v[0], v[1]);
        var dx = cx - o[0], dy = cy - o[1], a = (dx * u[0] + dy * u[1]) / lu, b = (dx * v[0] + dy * v[1]) / lv;
        var qx = Math.max(-a, 0, a - lu), qy = Math.max(-b, 0, b - lv);
        if (Math.hypot(qx, qy) < rad - 0.01) errs.push('label ' + i + ' covers the dot of node ' + k);
      }
    });
    res.push({id: c.id, n: labels.length, errs: errs, w: Math.round(cr.width)});
  });
  document.getElementById('out').textContent = JSON.stringify(res);
});
</script>'''

WIDTHS = (("w300", 300), ("w320", 320), ("w650", 650), ("w1200", 1200), ("w1400", 1400))


def _run_radial(blocks):
    cases = []
    for name, html in blocks.items():
        for label, px in WIDTHS:
            cases.append('<div class="case" id="%s-%s"><div style="width:%dpx">%s</div></div>' % (name, label, px, html))
        cases.append('<div class="case" id="%s-cell300"><div style="display:grid;grid-template-columns:300px 300px;gap:24px;width:624px"><div>%s</div><div></div></div></div>' % (name, html))
    page = '<!doctype html><meta charset="utf-8"><body style="margin:0">' + ''.join(cases) + '<pre id="out"></pre>' + HARNESS
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "p.html"
        f.write_text(page)
        prof = tempfile.mkdtemp()
        try:
            out = subprocess.run([CHROME, "--headless=new", "--use-angle=swiftshader", "--no-sandbox", "--user-data-dir=" + prof, "--window-size=1500,900",
                                  "--virtual-time-budget=3000", "--dump-dom", "file://" + str(f)], capture_output=True, text=True, timeout=240).stdout
        finally:
            shutil.rmtree(prof, ignore_errors=True)
    import html as H
    m = re.search(r'<pre id="out">(.*?)</pre>', out, re.S)
    assert m and m.group(1).strip(), out[-500:]
    return json.loads(H.unescape(m.group(1)))


RADIAL = ["leadership", "unbalanced", "small", "golden_tree30_max", "golden_tree20", "golden_six_children", "golden_chain3", "golden_single", "golden_forest_virtual_root", "golden_full_cap_10",
          "fuzz1", "fuzz2", "fuzz3", "fuzz8", "fuzz13", "fuzz21", "fuzz29", "fuzz34", "fuzzforest102", "hostile"]


def test_radial_labels_do_not_overlap_clip_or_widen_the_container_at_every_width(core_js):
    blocks = {n: _py(dict(C[n], layout="radial")) for n in RADIAL}
    blocks.update({n + "_gas": _gas_batch(core_js, [dict(C[n], layout="radial")])[0] for n in ("golden_tree30_max", "leadership", "fuzz8")})
    res = _run_radial(blocks)
    assert len(res) == len(blocks) * (len(WIDTHS) + 1)
    bad = [(r["id"], r["errs"][:3]) for r in res if r["errs"] or not r["n"]]
    assert not bad, bad[:8]
    by = {r["id"]: r for r in res}
    assert by["golden_tree30_max-w650"]["w"] == 634 or by["golden_tree30_max-w650"]["w"] <= 640        # fills the column up to 640 px
    assert by["golden_tree30_max-w1400"]["w"] == 640 and by["golden_tree30_max-w300"]["w"] == 300 and by["golden_tree30_max-cell300"]["w"] == 300


def test_cluster_boxes_and_connectors_hold_at_every_width(monkeypatch, core_js):
    monkeypatch.setattr(tlb, "WIDTHS", tlb.WIDTHS + (("w300", 300),))
    names = ["leadership", "unbalanced", "small", "golden_full_cap_10", "golden_tree20", "golden_tree30_max", "golden_interleave", "fuzz1", "fuzz8", "fuzz21", "fuzz29", "fuzzforest102", "golden_forest_virtual_root"]
    blocks = {n: _py(dict(C[n], layout="cluster")) for n in names}
    blocks.update({n + "_gas": _gas_batch(core_js, [dict(C[n], layout="cluster")])[0] for n in ("golden_tree30_max", "fuzz8")})
    res = tlb._run(blocks, False)
    assert len(res) == len(blocks) * (len(tlb.WIDTHS) + 1)
    bad = [(r["id"], r["errs"][:3]) for r in res if r["errs"] or not r["n"]]
    assert not bad, bad[:8]
    by = {r["id"]: r for r in res}
    assert by["golden_tree30_max-w300"]["mode"] == "ltr" and by["golden_tree30_max-w650"]["mode"] == "ltr" and by["small-w650"]["mode"] == "td" and by["small-w1400"]["mode"] == "td"
