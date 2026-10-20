"""sunburst in a real browser, both layouts: the chart never widens its container, the sunburst stays square, every visible label lies inside its own arc
(its four corners, found with the SVG path's own hit test), no two labels overlap, labels read outward and are never upside down, text is at least 12px.
The icicle's cells never overlap or leave the chart and the labels fit their cells' height. Same method and widths as tests/test_histogram_layout_box.py
(320 / 650 / 1200 / 1400 px and a 300 px grid cell)."""
from __future__ import annotations

import json

import pytest

from test_histogram_layout_box import CHROME, WIDTHS, _run
from test_motion_atoms import _gas_batch, _py, core_js  # noqa: F401
from test_sunburst import PAYLOADS

pytestmark = pytest.mark.skipif(not CHROME, reason="needs chromium")

RADIAL = ["budget", "flat", "two", "one_group", "deep", "forty", "tiny_share", "long_names", "twelve_groups", "bad_values"]
ICICLE = ["budget_icicle", "flat_icicle", "one_group_icicle", "deep_icicle", "forty_icicle"]

HARNESS = r'''<script>
window.addEventListener('load', function () {
  var res = [];
  function corners(e) {
    var r = e.getBoundingClientRect(), cx = r.left + r.width / 2, cy = r.top + r.height / 2, w = e.offsetWidth, h = e.offsetHeight;
    var m = new DOMMatrix(getComputedStyle(e).transform), a = Math.atan2(m.b, m.a), c = Math.cos(a), s = Math.sin(a);
    var pts = [[-w / 2, -h / 2], [w / 2, -h / 2], [w / 2, h / 2], [-w / 2, h / 2]].map(function (p) { return [cx + p[0] * c - p[1] * s, cy + p[0] * s + p[1] * c]; });
    return {pts: pts, cx: cx, cy: cy, a: a, w: w, h: h};
  }
  function axes(o) { return [[Math.cos(o.a), Math.sin(o.a)], [-Math.sin(o.a), Math.cos(o.a)]]; }
  function proj(o, ax) { var d = o.pts.map(function (p) { return p[0] * ax[0] + p[1] * ax[1]; }); return [Math.min.apply(null, d), Math.max.apply(null, d)]; }
  function overlap(p, q, gap) {
    var all = axes(p).concat(axes(q));
    for (var i = 0; i < all.length; i++) { var a = proj(p, all[i]), b = proj(q, all[i]); if (a[1] + gap <= b[0] || b[1] + gap <= a[0]) return false; }
    return true;
  }
  document.querySelectorAll('.case').forEach(function (c) {
    var errs = [], root = c.querySelector('[role=img]'), cs = c.firstElementChild.getBoundingClientRect(), rr = root.getBoundingClientRect(), i, j, n = 0;
    if (rr.right > cs.right + 0.5 || rr.left < cs.left - 0.5) errs.push('chart widens its container: ' + rr.width + ' in ' + cs.width);
    if (root.scrollWidth > root.clientWidth + 1) errs.push('content wider than the chart box');
    var svg = root.querySelector('svg');
    if (svg) {
      if (Math.abs(rr.width - rr.height) > 1) errs.push('not square: ' + rr.width + ' x ' + rr.height);
      if (rr.width > 640.5) errs.push('wider than 640');
      var paths = Array.prototype.slice.call(svg.querySelectorAll('path')), k = rr.width / 604;
      var labs = Array.prototype.slice.call(root.querySelectorAll('.sbl')).filter(function (e) { return getComputedStyle(e).display !== 'none'; }), os = labs.map(corners);
      labs.forEach(function (e, t) {
        var o = os[t], deg = o.a * 180 / Math.PI;
        n++;
        if (parseFloat(getComputedStyle(e).fontSize) < 11.5) errs.push('label font below 12px');
        if (deg > 90.01 || deg < -90.01) errs.push('label upside down: ' + deg + ' "' + e.textContent + '"');
        if (o.w < Math.min(20, 5 * e.textContent.length)) errs.push('label "' + e.textContent + '" is too narrow to show 3 characters (' + o.w + 'px)');
        var at = function (x, y) { var p = svg.createSVGPoint(); p.x = (x - rr.left) / k - 302; p.y = (y - rr.top) / k - 302; return p; };
        var host = paths.filter(function (p) { return p.isPointInFill(at(o.cx, o.cy)); })[0];
        if (!host) { errs.push('label "' + e.textContent + '" is not on an arc'); return; }
        o.pts.forEach(function (q) {
          var x = q[0] + (o.cx - q[0]) * 0.5 / Math.max(1, Math.hypot(o.cx - q[0], o.cy - q[1])), y = q[1] + (o.cy - q[1]) * 0.5 / Math.max(1, Math.hypot(o.cx - q[0], o.cy - q[1]));
          if (!host.isPointInFill(at(x, y))) errs.push('label "' + e.textContent + '" leaves its arc');
        });
      });
      for (i = 0; i < os.length; i++) for (j = i + 1; j < os.length; j++) if (overlap(os[i], os[j], 1)) errs.push('labels overlap: "' + labs[i].textContent + '" and "' + labs[j].textContent + '"');
      var cen = root.querySelector('.sbc');
      if (cen && getComputedStyle(cen).display !== 'none') {
        var cr = corners(cen);
        cr.pts.forEach(function (q) { var p = svg.createSVGPoint(); p.x = (q[0] - rr.left) / k - 302; p.y = (q[1] - rr.top) / k - 302; if (paths.some(function (h) { return h.isPointInFill(p); })) errs.push('centre label runs onto an arc'); });
        if (parseFloat(getComputedStyle(cen).fontSize) < 11.5) errs.push('centre font below 12px');
      }
    } else {
      var cells = Array.prototype.slice.call(root.children).filter(function (e) { return e.tagName === 'DIV'; }), rects = cells.map(function (e) { return e.getBoundingClientRect(); });
      if (Math.abs(rr.height - 360) > 0.5) errs.push('height ' + rr.height);
      cells.forEach(function (e, t) {
        var r = rects[t], sp = e.firstElementChild, txt = e.textContent, vis = txt && !(sp && getComputedStyle(sp).display === 'none');
        // a sliver thinner than its own 2px of border is clipped by the chart box, so the bounds allow 2.1px
        if (r.left < rr.left - 0.5 || r.right > rr.right + 0.5 || r.top < rr.top - 0.5 || r.bottom > rr.bottom + 2.1) errs.push('cell outside the chart: ' + [r.left - rr.left, rr.right - r.right, r.top - rr.top, rr.bottom - r.bottom].map(function (v) { return v.toFixed(2); }).join(','));
        if (vis) {
          n++;
          if (parseFloat(getComputedStyle(e).fontSize) < 11.5) errs.push('cell font below 12px');
          if (e.clientHeight < 18) errs.push('label taller than its cell: ' + e.clientHeight);
          if (e.clientWidth < 30) errs.push('label cell too narrow: ' + e.clientWidth);
        }
        for (var u = 0; u < t; u++) if (r.left < rects[u].right - 1.5 && rects[u].left < r.right - 1.5 && r.top < rects[u].bottom - 1.5 && rects[u].top < r.bottom - 1.5) errs.push('cells overlap');
      });
    }
    res.push({id: c.id, labels: n, errs: errs.slice(0, 6)});
  });
  document.getElementById('out').textContent = JSON.stringify(res);
});
</script>'''


def _check(names, renderer, core_js):
    blocks = {n: PAYLOADS[n] for n in names}
    html = {n: _py(b) for n, b in blocks.items()} if renderer == "python" else dict(zip(blocks, _gas_batch(core_js, list(blocks.values()))))
    res = _run(html, harness=HARNESS)
    assert len(res) == len(names) * len(WIDTHS)
    bad = {r["id"]: r["errs"] for r in res if r["errs"]}
    assert not bad, json.dumps(bad, indent=1)[:3000]
    return {r["id"]: r for r in res}


@pytest.mark.parametrize("renderer", ["python", "gas"])
def test_sunburst_labels_stay_inside_their_arcs_and_the_chart_stays_square(renderer, core_js):
    by = _check(RADIAL, renderer, core_js)
    # a wider container shows at least as many labels, and the wide ones show some
    assert by["budget-w320"]["labels"] <= by["budget-w650"]["labels"] <= by["budget-w1200"]["labels"] and by["budget-w1200"]["labels"] >= 10
    assert by["budget-w1200"]["labels"] == by["budget-w1400"]["labels"]


@pytest.mark.parametrize("renderer", ["python", "gas"])
def test_icicle_cells_never_overlap_and_labels_fit(renderer, core_js):
    by = _check(ICICLE, renderer, core_js)
    assert by["budget_icicle-w320"]["labels"] <= by["budget_icicle-w1200"]["labels"] and by["budget_icicle-w1200"]["labels"] >= 8
