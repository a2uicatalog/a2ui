"""box_plot in a real browser: boxes, whiskers, medians and dots stay inside their row, labels never overlap or clip,
and the chart is never wider than its container. Same method and widths as tests/test_histogram_layout_box.py."""
from __future__ import annotations

import json

import pytest

from test_box_plot import PAYLOADS
from test_histogram_layout_box import CHROME, WIDTHS, _run
from test_motion_atoms import _gas_batch, _py, core_js  # noqa: F401

pytestmark = pytest.mark.skipif(not CHROME, reason="needs chromium")

DRAWN = ["three", "five", "six", "all_equal", "both_sides", "negatives", "tiny", "big", "skewed", "twelve", "zero_iqr", "many_outliers"]

HARNESS = r'''<script>
window.addEventListener('load', function () {
  var res = [];
  function hit(a, b, g) { return a.left < b.right + g && b.left < a.right + g && a.top < b.bottom + g && b.top < a.bottom + g; }
  document.querySelectorAll('.case').forEach(function (c) {
    var errs = [], root = c.querySelector('.ifbp'), cs = c.firstElementChild.getBoundingClientRect(), rr = root.getBoundingClientRect(), i, j;
    if (rr.right > cs.right + 0.5 || rr.left < cs.left - 0.5) errs.push('chart widens its container: ' + rr.width + ' in ' + cs.width);
    if (root.scrollWidth > root.clientWidth + 1) errs.push('content is wider than the chart box: ' + root.scrollWidth + ' > ' + root.clientWidth);
    var plots = Array.prototype.slice.call(root.querySelectorAll('.bpp'));
    plots.forEach(function (p, k) {
      var pr = p.getBoundingClientRect();
      if (pr.width < 120) errs.push('row ' + k + ' plot too narrow: ' + pr.width);
      p.querySelectorAll('.bpb,.bpm,.bpw,.bpo').forEach(function (e) {
        var r = e.getBoundingClientRect();
        if (r.left < pr.left - 4.5 || r.right > pr.right + 4.5 || r.top < pr.top - 0.5 || r.bottom > pr.bottom + 0.5) errs.push(e.className + ' outside row ' + k);
      });
      var bx = p.querySelector('.bpb').getBoundingClientRect(), md = p.querySelector('.bpm').getBoundingClientRect();
      if (bx.width < 1.5) errs.push('box ' + k + ' has no width');
      if (md.left < bx.left - 2.5 || md.right > bx.right + 2.5) errs.push('median ' + k + ' outside its box');
    });
    var rl = Array.prototype.slice.call(root.querySelectorAll('.bpl'));
    var xl = Array.prototype.slice.call(root.querySelectorAll('.hgx')).filter(function (e) { return getComputedStyle(e).display !== 'none'; }).map(function (e) { return e.children[1]; });
    var labs = rl.concat(xl), rects = labs.map(function (e) { return e.getBoundingClientRect(); });
    rects.forEach(function (r, k) {
      if (r.left < rr.left - 0.5 || r.right > rr.right + 0.5 || r.top < rr.top - 0.5 || r.bottom > rr.bottom + 0.5) errs.push('label "' + labs[k].textContent + '" is clipped by the chart box');
      if (parseFloat(getComputedStyle(labs[k]).fontSize) < 11.5) errs.push('label font below 12px');
    });
    rl.forEach(function (e, k) { if (rects[k].right > plots[k].getBoundingClientRect().left + 0.5) errs.push('row label runs into its plot'); });
    for (i = 0; i < rects.length; i++) for (j = i + 1; j < rects.length; j++) if (hit(rects[i], rects[j], 1)) errs.push('labels overlap: "' + labs[i].textContent + '" and "' + labs[j].textContent + '"');
    res.push({id: c.id, rows: plots.length, xlabels: xl.length, errs: errs});
  });
  document.getElementById('out').textContent = JSON.stringify(res);
});
</script>'''


@pytest.mark.parametrize("renderer", ["python", "gas"])
def test_boxes_and_labels_never_overlap_or_widen_the_container(renderer, core_js):
    blocks = {n: PAYLOADS[n] for n in DRAWN}
    html = {n: _py(b) for n, b in blocks.items()} if renderer == "python" else dict(zip(blocks, _gas_batch(core_js, list(blocks.values()))))
    res = _run(html, harness=HARNESS)
    assert len(res) == len(DRAWN) * len(WIDTHS)
    bad = {r["id"]: r["errs"] for r in res if r["errs"]}
    assert not bad, json.dumps(bad, indent=1)[:3000]
    assert all(r["rows"] == len(PAYLOADS[r["id"].split("-")[0]]["groups"]) for r in res)
    by = {r["id"]: r for r in res}
    assert by["three-w320"]["xlabels"] <= by["three-w1200"]["xlabels"]
