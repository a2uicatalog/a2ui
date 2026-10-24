"""polar_chart in a real browser: the angle and radius labels stay inside the chart box and never overlap each other, text is 12px or
more, the plot is a square no wider than its container, and every marker sits inside the plot. Same method and widths as
tests/test_histogram_layout_box.py (320 / 650 / 1200 / 1400 px and a 300 px grid cell)."""
from __future__ import annotations

import json

import pytest

from test_histogram_layout_box import CHROME, WIDTHS, _run
from test_motion_atoms import _gas_batch, _py, core_js  # noqa: F401
from test_polar_chart import PAYLOADS

pytestmark = pytest.mark.skipif(not CHROME, reason="needs chromium")

DRAWN = ["radar", "wind", "negative", "range", "gaps", "single", "big", "six", "long_labels", "twelve"]

HARNESS = r'''<script>
window.addEventListener('load', function () {
  var res = [];
  function hit(a, b, g) { return a.left < b.right + g && b.left < a.right + g && a.top < b.bottom + g && b.top < a.bottom + g; }
  document.querySelectorAll('.case').forEach(function (c) {
    var errs = [], root = c.querySelector('.ifpc'), cs = c.firstElementChild.getBoundingClientRect(), rr = root.getBoundingClientRect(), i, j;
    if (rr.right > cs.right + 0.5 || rr.left < cs.left - 0.5) errs.push('chart widens its container: ' + rr.width + ' in ' + cs.width);
    if (root.scrollWidth > root.clientWidth + 1) errs.push('content is wider than the chart box: ' + root.scrollWidth + ' > ' + root.clientWidth);
    var plot = root.querySelector('[role=img]'), pr = plot.getBoundingClientRect();
    if (Math.abs(pr.width - pr.height) > 1) errs.push('plot is not square: ' + pr.width + ' x ' + pr.height);
    var labs = Array.prototype.slice.call(plot.querySelectorAll('.pca, .pcr')).filter(function (e) { return getComputedStyle(e).display !== 'none'; }), rects = labs.map(function (e) { return e.getBoundingClientRect(); });
    rects.forEach(function (r, k) {
      var t = labs[k].textContent;
      if (r.left < pr.left - 0.5 || r.right > pr.right + 0.5 || r.top < pr.top - 0.5 || r.bottom > pr.bottom + 0.5) errs.push('label "' + t + '" is outside the plot box');
      if (r.width < 1) errs.push('label "' + t + '" has no box');
      if (labs[k].scrollHeight > labs[k].clientHeight + 1) errs.push('label "' + t + '" is cut off');
      if (parseFloat(getComputedStyle(labs[k]).fontSize) < 11.5) errs.push('label font below 12px: ' + getComputedStyle(labs[k]).fontSize);
    });
    for (i = 0; i < rects.length; i++) for (j = i + 1; j < rects.length; j++) if (hit(rects[i], rects[j], 1)) errs.push('labels overlap: "' + labs[i].textContent + '" and "' + labs[j].textContent + '"');
    var marks = Array.prototype.slice.call(plot.querySelectorAll('svg circle[r], svg rect')).filter(function (e) { return e.getAttribute('fill') !== 'none' && !e.getAttribute('stroke-dasharray'); });
    marks.forEach(function (m, k) { var r = m.getBoundingClientRect(); if (r.left < pr.left - 1 || r.right > pr.right + 1 || r.top < pr.top - 1 || r.bottom > pr.bottom + 1) errs.push('marker ' + k + ' outside the plot'); });
    Array.prototype.slice.call(root.querySelectorAll('.pcl')).forEach(function (e) {
      var r = e.getBoundingClientRect();
      if (r.right > rr.right + 0.5 || r.left < rr.left - 0.5) errs.push('legend item clipped');
      if (parseFloat(getComputedStyle(e).fontSize) < 11.5) errs.push('legend font below 12px');
    });
    res.push({id: c.id, labels: labs.length, errs: errs, w: pr.width});
  });
  document.getElementById('out').textContent = JSON.stringify(res);
});
</script>'''


@pytest.mark.parametrize("renderer", ["python", "gas"])
def test_labels_never_overlap_or_leave_the_plot_or_widen_the_container(renderer, core_js):
    blocks = {n: PAYLOADS[n] for n in DRAWN}
    html = {n: _py(b) for n, b in blocks.items()} if renderer == "python" else dict(zip(blocks, _gas_batch(core_js, list(blocks.values()))))
    res = _run(html, harness=HARNESS)
    assert len(res) == len(DRAWN) * len(WIDTHS)
    bad = {r["id"]: r["errs"] for r in res if r["errs"]}
    assert not bad, json.dumps(bad, indent=1)[:3500]
    by = {r["id"]: r["labels"] for r in res}
    assert by["range-w320"] < by["range-w1200"] and by["radar-w320"] > 0                       # the narrow tier shows fewer radius numbers
