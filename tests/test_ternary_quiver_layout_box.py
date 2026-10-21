"""ternary_plot and quiver in a real browser: the triangle and the arrow field stay inside their box, tick and corner labels
never overlap or clip, text is at least 12px, and nothing is wider than its container. Same method and widths as
tests/test_histogram_layout_box.py (320, 650, 1200, 1400 and a 300 px grid cell)."""
from __future__ import annotations

import json

import pytest

from test_histogram_layout_box import CHROME, WIDTHS, _run
from test_motion_atoms import _gas_batch, _py, core_js  # noqa: F401
from test_ternary_quiver import PAYLOADS

pytestmark = pytest.mark.skipif(not CHROME, reason="needs chromium")

DRAWN = ["tp_basic", "tp_connect", "tp_defaults", "tp_corners", "tp_many", "tp_malformed",
         "qv_basic", "qv_single", "qv_all_zero", "qv_negatives", "qv_many", "qv_malformed"]

HARNESS = r'''<script>
window.addEventListener('load', function () {
  var res = [];
  function hit(a, b, g) { return a.left < b.right + g && b.left < a.right + g && a.top < b.bottom + g && b.top < a.bottom + g; }
  document.querySelectorAll('.case').forEach(function (c) {
    var errs = [], root = c.querySelector('.iftp,.ifqv'), cs = c.firstElementChild.getBoundingClientRect(), rr = root.getBoundingClientRect(), i, j;
    var plot = root.querySelector('.tpp,.qvp'), pr = plot.getBoundingClientRect();
    if (rr.right > cs.right + 0.5 || rr.left < cs.left - 0.5) errs.push('chart widens its container: ' + rr.width + ' in ' + cs.width);
    if (root.scrollWidth > root.clientWidth + 1) errs.push('content is wider than the chart box: ' + root.scrollWidth + ' > ' + root.clientWidth);
    if (pr.width < 150) errs.push('plot too narrow: ' + pr.width);
    var labs = Array.prototype.slice.call(root.querySelectorAll('.tpt,.tpv,.qvy,.qvx')).filter(function (e) { return getComputedStyle(e).display !== 'none'; });
    var rects = labs.map(function (e) { return e.getBoundingClientRect(); });
    rects.forEach(function (r, k) {
      if (r.left < rr.left - 0.5 || r.right > rr.right + 0.5 || r.top < rr.top - 0.5 || r.bottom > rr.bottom + 0.5) errs.push('label "' + labs[k].textContent + '" is clipped by the chart box');
      if (parseFloat(getComputedStyle(labs[k]).fontSize) < 11.5) errs.push('label font below 12px');
    });
    for (i = 0; i < rects.length; i++) for (j = i + 1; j < rects.length; j++) if (hit(rects[i], rects[j], 0)) errs.push('labels overlap: "' + labs[i].textContent + '" and "' + labs[j].textContent + '"');
    root.querySelectorAll('.tpd').forEach(function (d) {
      var r = d.getBoundingClientRect();
      if (r.left < pr.left - 6 || r.right > pr.right + 6 || r.top < pr.top - 6 || r.bottom > pr.bottom + 6) errs.push('a point is outside the triangle box');
    });
    root.querySelectorAll('.qva,.qvz').forEach(function (a) {
      var r = a.getBoundingClientRect();
      if (r.left < pr.left - 1 || r.right > pr.right + 1 || r.top < pr.top - 1 || r.bottom > pr.bottom + 1) errs.push('an arrow leaves the plot');
    });
    res.push({id: c.id, labels: labs.length, errs: errs});
  });
  document.getElementById('out').textContent = JSON.stringify(res);
});
</script>'''


@pytest.mark.parametrize("renderer", ["python", "gas"])
def test_plots_and_labels_never_overlap_clip_or_widen_the_container(renderer, core_js):
    blocks = {n: PAYLOADS[n] for n in DRAWN}
    html = {n: _py(b) for n, b in blocks.items()} if renderer == "python" else dict(zip(blocks, _gas_batch(core_js, list(blocks.values()))))
    res = _run(html, harness=HARNESS)
    assert len(res) == len(DRAWN) * len(WIDTHS)
    bad = {r["id"]: r["errs"] for r in res if r["errs"]}
    assert not bad, json.dumps(bad, indent=1)[:3000]
    by = {r["id"]: r for r in res}
    assert by["qv_basic-w320"]["labels"] < by["qv_basic-w1200"]["labels"] or by["qv_basic-w320"]["labels"] <= by["qv_basic-w1200"]["labels"]
