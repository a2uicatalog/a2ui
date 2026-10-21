"""parallel_coords in a real browser: axis labels, tick labels and the legend never overlap or clip, the lines stay inside the plot,
and the chart is never wider than its container (it scrolls inside its own box when the axes need more room than a narrow
container has). Same method and widths as tests/test_histogram_layout_box.py."""
from __future__ import annotations

import json

import pytest

from test_histogram_layout_box import CHROME, WIDTHS, _run
from test_motion_atoms import _gas_batch, _py, core_js  # noqa: F401
from test_parallel_coords import PAYLOADS

pytestmark = pytest.mark.skipif(not CHROME, reason="needs chromium")

DRAWN = ["cars", "plain", "iris", "two", "eight", "negatives", "constant", "one_row", "explicit", "huge", "many_rows"]

HARNESS = r'''<script>
window.addEventListener('load', function () {
  var res = [];
  function hit(a, b, g) { return a.left < b.right + g && b.left < a.right + g && a.top < b.bottom + g && b.top < a.bottom + g; }
  document.querySelectorAll('.case').forEach(function (c) {
    var errs = [], root = c.querySelector('.ifpc'), cs = c.firstElementChild.getBoundingClientRect(), rr = root.getBoundingClientRect(), i, j;
    var note = root.querySelector('.pcs'), sc = root.querySelector('[role=region]');
    if (sc.scrollWidth > sc.clientWidth + 1 && getComputedStyle(note).display === 'none') errs.push('scrolls sideways with no hint');
    if (rr.right > cs.right + 0.5 || rr.left < cs.left - 0.5) errs.push('chart widens its container: ' + rr.width + ' in ' + cs.width);
    var inner = root.querySelector('[role=img]'), ir = inner.getBoundingClientRect();
    // header cells are columns that touch edge to edge, so only a real overlap counts for them
    var plot = root.querySelector('svg').getBoundingClientRect();
    var paths = root.querySelectorAll('path.pcr');
    if (!paths.length) errs.push('no lines');
    Array.prototype.forEach.call(paths, function (p, k) {
      var r = p.getBoundingClientRect();
      if (r.left < plot.left - 2 || r.right > plot.right + 2 || r.top < plot.top - 2 || r.bottom > plot.bottom + 2) errs.push('line ' + k + ' outside the plot');
    });
    var labs = Array.prototype.slice.call(root.querySelectorAll('.pch, .pct, .pcl')), rects = labs.map(function (e) { return e.getBoundingClientRect(); });
    rects.forEach(function (r, k) {
      if (r.left < ir.left - 0.5 || r.right > ir.right + 0.5 || r.top < ir.top - 0.5 || r.bottom > ir.bottom + 0.5) errs.push('label "' + labs[k].textContent + '" is clipped by the chart');
      if (labs[k].scrollWidth > labs[k].clientWidth + 1 && labs[k].className !== 'pcl') errs.push('label "' + labs[k].textContent + '" overflows its box');
      if (r.width < 1) errs.push('label "' + labs[k].textContent + '" has no box');
      if (parseFloat(getComputedStyle(labs[k]).fontSize) < 11.5) errs.push('label font below 12px: ' + getComputedStyle(labs[k]).fontSize);
    });
    for (i = 0; i < rects.length; i++) for (j = i + 1; j < rects.length; j++) if (hit(rects[i], rects[j], labs[i].className === 'pch' && labs[j].className === 'pch' ? -0.5 : 1)) errs.push('labels overlap: "' + labs[i].textContent + '" and "' + labs[j].textContent + '"');
    if (document.documentElement.scrollWidth > document.documentElement.clientWidth + 1) errs.push('the page scrolls sideways');
    res.push({id: c.id, lines: paths.length, errs: errs, w: rr.width});
  });
  document.getElementById('out').textContent = JSON.stringify(res);
});
</script>'''


@pytest.mark.parametrize("renderer", ["python", "gas"])
def test_labels_never_overlap_or_clip_and_the_chart_never_widens_the_container(renderer, core_js):
    blocks = {n: PAYLOADS[n] for n in DRAWN}
    html = {n: _py(b) for n, b in blocks.items()} if renderer == "python" else dict(zip(blocks, _gas_batch(core_js, list(blocks.values()))))
    res = _run(html, harness=HARNESS)
    assert len(res) == len(DRAWN) * len(WIDTHS)
    bad = {r["id"]: r["errs"] for r in res if r["errs"]}
    assert not bad, json.dumps(bad, indent=1)[:3000]


PAIR_HARNESS = r'''<script>
window.addEventListener('load', function () {
  var res = [];
  document.querySelectorAll('.case').forEach(function (c) {
    var errs = [];
    c.querySelectorAll('.ifpc').forEach(function (root, k) {
      var note = root.querySelector('.pcs'), sc = root.querySelector('[role=region]');
      var overflows = sc.scrollWidth > sc.clientWidth + 1, shown = getComputedStyle(note).display !== 'none';
      if (shown && !overflows) errs.push('chart ' + k + ' shows the scroll hint though it fits');
      if (overflows && !shown) errs.push('chart ' + k + ' scrolls with no hint');
    });
    res.push({id: c.id, errs: errs});
  });
  document.getElementById('out').textContent = JSON.stringify(res);
});
</script>'''


@pytest.mark.parametrize("renderer", ["python", "gas"])
def test_scroll_hint_belongs_to_its_own_chart_when_two_share_a_page(renderer, core_js):
    """P2: the 8-axis chart's hint threshold must not switch the hint on for a 2-axis chart beside it."""
    blocks = [PAYLOADS["two"], PAYLOADS["eight"], PAYLOADS["two"]]
    htm = "".join(_py(b) for b in blocks) if renderer == "python" else "".join(_gas_batch(core_js, blocks))
    res = _run({"pair": htm}, harness=PAIR_HARNESS)
    assert res
    bad = {r["id"]: r["errs"] for r in res if r["errs"]}
    assert not bad, json.dumps(bad, indent=1)
