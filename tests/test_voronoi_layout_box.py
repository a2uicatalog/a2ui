"""voronoi in a real browser: the drawing keeps the shape its viewBox asks for and never widens its container (nor passes its 820 px cap), every region stays inside the
drawing, every label that is shown lies inside its own region and overlaps no other label, the axis labels (y at the left, x below) are at least 12px, inside the chart
and overlap nothing, and the legend entries stay inside their container without overlapping. Same method and widths as tests/test_histogram_layout_box.py
(320 / 650 / 1200 / 1400 px and a 300 px grid cell)."""
from __future__ import annotations

import json

import pytest

from test_voronoi import PAYLOADS
from test_histogram_layout_box import CHROME, WIDTHS, _run
from test_motion_atoms import _gas_batch, _py, core_js  # noqa: F401

pytestmark = pytest.mark.skipif(not CHROME, reason="needs chromium")

DRAWN = ["depots", "no_groups", "no_labels", "three", "collinear", "grid", "many", "many_groups", "stretched", "same_x", "far", "long_labels", "negative"]

HARNESS = r'''<script>
window.addEventListener('load', function () {
  var res = [];
  function hit(a, b, g) { return a.left < b.right + g && b.left < a.right + g && a.top < b.bottom + g && b.top < a.bottom + g; }
  document.querySelectorAll('.case').forEach(function (c) {
    var errs = [], cont = c.firstElementChild.getBoundingClientRect(), root = c.querySelector('.ifvo'), rr = root.getBoundingClientRect(), i, j;
    if (rr.right > cont.right + 0.5 || rr.left < cont.left - 0.5) errs.push('chart widens its container: ' + rr.width + ' in ' + cont.width);
    if (rr.width > 820.5) errs.push('chart passes its 820px cap: ' + rr.width);
    if (root.scrollWidth > root.clientWidth + 1) errs.push('content wider than the chart box: ' + root.scrollWidth + ' > ' + root.clientWidth);
    var plot = root.querySelector('[role=img]'), svg = plot.querySelector('svg'), sr = svg.getBoundingClientRect(), vb = svg.getAttribute('viewBox').split(' ').map(Number);
    if (Math.abs(sr.width / sr.height - vb[2] / vb[3]) > 0.01) errs.push('drawing is not ' + vb[2] + ':' + vb[3] + ': ' + sr.width + ' x ' + sr.height);
    if (sr.width < 150) errs.push('drawing too narrow: ' + sr.width);
    var cells = Array.prototype.slice.call(svg.querySelectorAll('g.vog')), dots = [], shown = [];
    if (!cells.length) errs.push('no regions');
    cells.forEach(function (g, k) {
      var p = g.querySelector('path.voc'), r = p.getBoundingClientRect(), d = g.querySelector('circle.vod').getBoundingClientRect();
      if (r.width < 0.5 || r.height < 0.5) errs.push('region ' + k + ' has no size');
      if (r.left < sr.left - 1 || r.right > sr.right + 1 || r.top < sr.top - 1 || r.bottom > sr.bottom + 1) errs.push('region ' + k + ' outside the drawing');
      var dcx = (d.left + d.right) / 2, dcy = (d.top + d.bottom) / 2;   // a dot may cover a region edge when sites are crowded; its centre may not leave the region
      if (dcx < r.left - 0.5 || dcx > r.right + 0.5 || dcy < r.top - 0.5 || dcy > r.bottom + 0.5) errs.push('site ' + k + ' outside its region');
      dots.push({r: r, d: d});
    });
    var labs = Array.prototype.slice.call(plot.querySelectorAll('.vol')).filter(function (e) { return getComputedStyle(e).display !== 'none'; });
    var lr = labs.map(function (e) { return e.getBoundingClientRect(); });
    lr.forEach(function (r, k) {
      if (parseFloat(getComputedStyle(labs[k]).fontSize) < 11.5) errs.push('region label font below 12px');
      // the label belongs to the site whose dot is centred above it
      var best = -1, bd = 1e9, bs = 1e9;
      dots.forEach(function (o, m) {
        var dx = Math.abs((o.d.left + o.d.right) / 2 - (r.left + r.right) / 2), gap = r.top - o.d.bottom;
        if (gap >= -8 && (dx < bd - 0.5 || (dx < bd + 0.5 && gap < bs))) { bd = dx; bs = gap; best = m; }   // the nearest dot above the label in its column
      });
      var dd = best >= 0 ? dots[best] : null;
      if (!dd || bd > 1.5) { errs.push('label "' + labs[k].textContent + '" has no dot above it'); return; }
      if (r.left < dd.r.left - 1 || r.right > dd.r.right + 1 || r.top < dd.r.top - 1 || r.bottom > dd.r.bottom + 1) errs.push('label "' + labs[k].textContent + '" leaves its region');
      if (r.left < sr.left - 0.5 || r.right > sr.right + 0.5 || r.bottom > sr.bottom + 0.5) errs.push('label "' + labs[k].textContent + '" is outside the drawing');
    });
    for (i = 0; i < lr.length; i++) for (j = i + 1; j < lr.length; j++) if (hit(lr[i], lr[j], 0)) errs.push('region labels overlap: "' + labs[i].textContent + '" and "' + labs[j].textContent + '"');
    var xl = Array.prototype.slice.call(root.querySelectorAll('.hgx')).filter(function (e) { return getComputedStyle(e).display !== 'none'; }).map(function (e) { return e.children[1]; });
    var yl = Array.prototype.slice.call(root.querySelectorAll('.voy')).filter(function (e) { return getComputedStyle(e).display !== 'none'; });
    var axl = xl.concat(yl), rects = axl.map(function (e) { return e.getBoundingClientRect(); });
    rects.forEach(function (r, k) {
      if (r.left < rr.left - 0.5 || r.right > rr.right + 0.5 || r.top < rr.top - 0.5 || r.bottom > rr.bottom + 0.5) errs.push('axis label "' + axl[k].textContent + '" is clipped by the chart box');
      if (r.width < 1) errs.push('axis label "' + axl[k].textContent + '" has no box');
      if (parseFloat(getComputedStyle(axl[k]).fontSize) < 11.5) errs.push('axis label font below 12px: ' + getComputedStyle(axl[k]).fontSize);
    });
    for (i = 0; i < rects.length; i++) for (j = i + 1; j < rects.length; j++) if (hit(rects[i], rects[j], 1)) errs.push('axis labels overlap: "' + axl[i].textContent + '" and "' + axl[j].textContent + '"');
    xl.forEach(function (e) { if (e.getBoundingClientRect().top < sr.bottom) errs.push('x label above the axis'); });
    yl.forEach(function (e) { if (e.getBoundingClientRect().right > sr.left + 0.5) errs.push('y label inside the plot'); });
    var items = Array.prototype.slice.call(c.querySelectorAll('.voleg span[style*="inline-flex"]')), ir = items.map(function (e) { return e.getBoundingClientRect(); });
    ir.forEach(function (r, k) {
      if (r.left < cont.left - 0.5 || r.right > cont.right + 0.5) errs.push('legend entry "' + items[k].textContent + '" leaves its container');
      if (parseFloat(getComputedStyle(items[k]).fontSize) < 11.5) errs.push('legend font below 12px');
    });
    for (i = 0; i < ir.length; i++) for (j = i + 1; j < ir.length; j++) if (hit(ir[i], ir[j], 0)) errs.push('legend entries overlap');
    res.push({id: c.id, cells: cells.length, labels: labs.length, xlabels: xl.length, legend: items.length, errs: errs, w: rr.width});
  });
  document.getElementById('out').textContent = JSON.stringify(res);
});
</script>'''


@pytest.mark.parametrize("renderer", ["python", "gas"])
def test_regions_labels_and_legend_never_overlap_or_widen_the_container(renderer, core_js):
    blocks = {n: PAYLOADS[n] for n in DRAWN}
    html = {n: _py(b) for n, b in blocks.items()} if renderer == "python" else dict(zip(blocks, _gas_batch(core_js, list(blocks.values()))))
    res = _run(html, harness=HARNESS)
    assert len(res) == len(DRAWN) * len(WIDTHS)
    bad = {r["id"]: r["errs"] for r in res if r["errs"]}
    assert not bad, json.dumps(bad, indent=1)[:3000]
    by = {r["id"]: r for r in res}
    assert by["depots-w320"]["xlabels"] < by["depots-w1200"]["xlabels"]                  # the narrow tier thins the x labels
    assert by["depots-w320"]["labels"] < by["depots-w650"]["labels"] == 12              # a wider container shows more labels, and from 650 px all twelve
    assert by["depots-w1400"]["w"] == 820 and by["depots-w320"]["w"] == 320
    assert all(r["cells"] == len(PAYLOADS[r["id"].split("-")[0]]["sites"]) for r in res if r["id"].split("-")[0] not in ("many",))
    assert by["depots-w650"]["legend"] == 3 and by["no_groups-w650"]["legend"] == 0
