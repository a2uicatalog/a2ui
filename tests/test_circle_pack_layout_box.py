"""circle_pack in a real browser: the chart never widens its container and stays square; every visible leaf label lies inside its own circle (its four
corners), every visible group label lies inside the top of its group's circle, no two labels overlap, text is at least 12px and a shown name keeps at
least 3 characters. Same method and widths as tests/test_histogram_layout_box.py (320 / 650 / 1200 / 1400 px and a 300 px grid cell)."""
from __future__ import annotations

import json

import pytest

from test_histogram_layout_box import CHROME, WIDTHS, _run
from test_motion_atoms import _gas_batch, _py, core_js  # noqa: F401
from test_circle_pack import PAYLOADS

pytestmark = pytest.mark.skipif(not CHROME, reason="needs chromium")

DRAWN = ["budget", "flat", "two", "one_group", "deep", "sixty", "tiny_share", "long_names", "twelve_groups", "bad_values"]

HARNESS = r'''<script>
window.addEventListener('load', function () {
  var res = [];
  function vis(e) { return e && getComputedStyle(e).display !== 'none' && !(e.parentElement && e.parentElement.closest && getComputedStyle(e.parentElement).display === 'none'); }
  document.querySelectorAll('.case').forEach(function (c) {
    var errs = [], root = c.querySelector('[role=img]'), cs = c.firstElementChild.getBoundingClientRect(), rr = root.getBoundingClientRect(), n = 0, i, j;
    if (rr.right > cs.right + 0.5 || rr.left < cs.left - 0.5) errs.push('chart widens its container: ' + rr.width + ' in ' + cs.width);
    if (root.scrollWidth > root.clientWidth + 1) errs.push('content wider than the chart box');
    if (Math.abs(rr.width - rr.height) > 1) errs.push('not square: ' + rr.width + ' x ' + rr.height);
    if (rr.width > 640.5) errs.push('wider than 640');
    var k = rr.width / 604, circles = Array.prototype.slice.call(root.querySelectorAll('svg circle')).map(function (e) {
      return {e: e, x: rr.left + (parseFloat(e.getAttribute('cx')) + 2) * k, y: rr.top + (parseFloat(e.getAttribute('cy')) + 2) * k, r: parseFloat(e.getAttribute('r')) * k, group: e.getAttribute('fill') === 'none'};
    });
    var labs = Array.prototype.slice.call(root.querySelectorAll('.cpl, .cpg')).filter(function (e) {
      return !(e.className.indexOf('tmw') >= 0 && getComputedStyle(e).display === 'none') && getComputedStyle(e).display !== 'none';
    });
    var rects = labs.map(function (e) { return e.getBoundingClientRect(); });
    function inside(circ, x, y) { return Math.hypot(x - circ.x, y - circ.y) <= circ.r + 0.5; }
    labs.forEach(function (e, t) {
      var r = rects[t], cx = r.left + r.width / 2, cy = r.top + r.height / 2, isGroup = e.className.indexOf('cpg') === 0, host = null;
      n++;
      if (parseFloat(getComputedStyle(e).fontSize) < 11.5) errs.push('label font below 12px');
      circles.forEach(function (ci) {
        if (isGroup ? (ci.group && Math.abs(cx - ci.x) < 0.6 && Math.abs(cy - (ci.y - ci.r + 18)) < 0.6) : (!ci.group && Math.abs(cx - ci.x) < 0.6 && Math.abs(cy - ci.y) < 0.6)) host = ci;
      });
      if (!host) { errs.push('label "' + e.textContent + '" has no circle'); return; }
      [[r.left, r.top], [r.right, r.top], [r.right, r.bottom], [r.left, r.bottom]].forEach(function (q) {
        if (!inside(host, q[0], q[1])) errs.push('label "' + e.textContent + '" leaves its circle');
      });
      var nm = isGroup ? e : e.querySelector('.cpn');
      if (nm.clientWidth < Math.min(20, 5 * nm.textContent.length)) errs.push('name "' + nm.textContent + '" is too narrow (' + nm.clientWidth + 'px)');
      if (isGroup && host.r < 40) errs.push('group label in a circle under 40px');
      if (r.left < rr.left - 0.5 || r.right > rr.right + 0.5 || r.top < rr.top - 0.5 || r.bottom > rr.bottom + 0.5) errs.push('label outside the chart');
    });
    for (i = 0; i < rects.length; i++) for (j = i + 1; j < rects.length; j++) {
      if (rects[i].left < rects[j].right && rects[j].left < rects[i].right && rects[i].top < rects[j].bottom && rects[j].top < rects[i].bottom) errs.push('labels overlap: "' + labs[i].textContent + '" and "' + labs[j].textContent + '"');
    }
    res.push({id: c.id, labels: n, circles: circles.length, errs: errs.slice(0, 6)});
  });
  document.getElementById('out').textContent = JSON.stringify(res);
});
</script>'''


@pytest.mark.parametrize("renderer", ["python", "gas"])
def test_circle_pack_labels_stay_inside_their_circles_and_the_chart_stays_square(renderer, core_js):
    blocks = {n: PAYLOADS[n] for n in DRAWN}
    html = {n: _py(b) for n, b in blocks.items()} if renderer == "python" else dict(zip(blocks, _gas_batch(core_js, list(blocks.values()))))
    res = _run(html, harness=HARNESS)
    assert len(res) == len(DRAWN) * len(WIDTHS)
    bad = {r["id"]: r["errs"] for r in res if r["errs"]}
    assert not bad, json.dumps(bad, indent=1)[:3000]
    by = {r["id"]: r for r in res}
    # a wider container shows at least as many labels, and the wide ones show some
    assert by["budget-w320"]["labels"] <= by["budget-w650"]["labels"] <= by["budget-w1200"]["labels"] and by["budget-w1200"]["labels"] >= 10
    assert by["budget-w1200"]["labels"] == by["budget-w1400"]["labels"]
    assert by["budget-w1200"]["circles"] == 25
