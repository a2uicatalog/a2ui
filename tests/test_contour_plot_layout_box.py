"""contour_plot in a real browser: the drawing keeps its 3:2 shape and never widens its container, the bands and dots stay inside it, the axis labels (y at the
left, x below) are at least 12px, inside the chart and overlap nothing, the legend entries stay inside their container without overlapping, and the drawing clips
anything a density band draws past the plot. Same method and widths as tests/test_histogram_layout_box.py (320 / 650 / 1200 / 1400 px and a 300 px grid cell)."""
from __future__ import annotations

import json

import pytest

from test_contour_plot import PAYLOADS
from test_histogram_layout_box import CHROME, WIDTHS, _run
from test_motion_atoms import _gas_batch, _py, core_js  # noqa: F401

pytestmark = pytest.mark.skipif(not CHROME, reason="needs chromium")

DRAWN = ["temp", "hill", "crater", "smooth", "two_cols", "delivery", "delivery_default", "pts_small", "pts_same_x", "pts_negative", "pts_bw60", "pts_edge"]

HARNESS = r'''<script>
window.addEventListener('load', function () {
  var res = [];
  function hit(a, b, g) { return a.left < b.right + g && b.left < a.right + g && a.top < b.bottom + g && b.top < a.bottom + g; }
  document.querySelectorAll('.case').forEach(function (c) {
    var errs = [], cont = c.firstElementChild.getBoundingClientRect(), root = c.querySelector('.ifcn'), rr = root.getBoundingClientRect(), i, j;
    if (rr.right > cont.right + 0.5 || rr.left < cont.left - 0.5) errs.push('chart widens its container: ' + rr.width + ' in ' + cont.width);
    if (root.scrollWidth > root.clientWidth + 1) errs.push('content wider than the chart box: ' + root.scrollWidth + ' > ' + root.clientWidth);
    var plot = root.querySelector('[role=img]'), svg = plot.querySelector('svg'), sr = svg.getBoundingClientRect();
    if (Math.abs(sr.width / sr.height - 1.5) > 0.01) errs.push('drawing is not 3:2: ' + sr.width + ' x ' + sr.height);
    if (sr.width < 150) errs.push('drawing too narrow: ' + sr.width);
    var bands = Array.prototype.slice.call(svg.querySelectorAll('path.cnb'));
    if (!bands.length) errs.push('no bands');
    bands.forEach(function (p, k) {
      var r = p.getBoundingClientRect();
      if (r.width < 0.5 || r.height < 0.5) errs.push('band ' + k + ' has no size');
      // a density band may run past the plot (the blur is padded); the svg clips it. A grid band never does.
      if (!svg.querySelector('path.cnp') && (r.left < sr.left - 1 || r.right > sr.right + 1 || r.top < sr.top - 1 || r.bottom > sr.bottom + 1)) errs.push('band ' + k + ' outside the drawing');
    });
    if (getComputedStyle(svg).overflow !== 'hidden') errs.push('the drawing does not clip');
    var dots = svg.querySelector('path.cnp');
    if (dots) { var dr = dots.getBoundingClientRect(); if (dr.left < sr.left - 3 || dr.right > sr.right + 3 || dr.top < sr.top - 3 || dr.bottom > sr.bottom + 3) errs.push('dots outside the drawing'); }
    var xl = Array.prototype.slice.call(root.querySelectorAll('.hgx')).filter(function (e) { return getComputedStyle(e).display !== 'none'; }).map(function (e) { return e.children[1]; });
    var yl = Array.prototype.slice.call(root.querySelectorAll('.cny'));
    var labs = xl.concat(yl), rects = labs.map(function (e) { return e.getBoundingClientRect(); });
    rects.forEach(function (r, k) {
      if (r.left < rr.left - 0.5 || r.right > rr.right + 0.5 || r.top < rr.top - 0.5 || r.bottom > rr.bottom + 0.5) errs.push('label "' + labs[k].textContent + '" is clipped by the chart box');
      if (r.width < 1) errs.push('label "' + labs[k].textContent + '" has no box');
      if (parseFloat(getComputedStyle(labs[k]).fontSize) < 11.5) errs.push('label font below 12px: ' + getComputedStyle(labs[k]).fontSize);
    });
    for (i = 0; i < rects.length; i++) for (j = i + 1; j < rects.length; j++) if (hit(rects[i], rects[j], 1)) errs.push('labels overlap: "' + labs[i].textContent + '" and "' + labs[j].textContent + '"');
    xl.forEach(function (e) { if (e.getBoundingClientRect().top < sr.bottom) errs.push('x label above the axis'); });
    yl.forEach(function (e) { if (e.getBoundingClientRect().right > sr.left + 0.5) errs.push('y label inside the plot'); });
    var items = Array.prototype.slice.call(c.querySelectorAll('.cnleg span[style*="inline-flex"]')), ir = items.map(function (e) { return e.getBoundingClientRect(); });
    if (items.length < 2) errs.push('no legend');
    ir.forEach(function (r, k) {
      if (r.left < cont.left - 0.5 || r.right > cont.right + 0.5) errs.push('legend entry "' + items[k].textContent + '" leaves its container');
      if (parseFloat(getComputedStyle(items[k]).fontSize) < 11.5) errs.push('legend font below 12px');
    });
    for (i = 0; i < ir.length; i++) for (j = i + 1; j < ir.length; j++) if (hit(ir[i], ir[j], 0)) errs.push('legend entries overlap');
    res.push({id: c.id, bands: bands.length, xlabels: xl.length, ylabels: yl.length, errs: errs});
  });
  document.getElementById('out').textContent = JSON.stringify(res);
});
</script>'''


@pytest.mark.parametrize("renderer", ["python", "gas"])
def test_drawing_labels_and_legend_never_overlap_or_widen_the_container(renderer, core_js):
    blocks = {n: PAYLOADS[n] for n in DRAWN}
    html = {n: _py(b) for n, b in blocks.items()} if renderer == "python" else dict(zip(blocks, _gas_batch(core_js, list(blocks.values()))))
    res = _run(html, harness=HARNESS)
    assert len(res) == len(DRAWN) * len(WIDTHS)
    bad = {r["id"]: r["errs"] for r in res if r["errs"]}
    assert not bad, json.dumps(bad, indent=1)[:3000]
    by = {r["id"]: r for r in res}
    assert by["temp-w320"]["xlabels"] < by["temp-w1200"]["xlabels"]                      # the narrow tier thins the x labels
    assert all(r["bands"] == html[r["id"].split("-")[0]].count('class="cnb') for r in res)
