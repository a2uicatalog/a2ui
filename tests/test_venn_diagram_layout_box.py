"""Three-set venn_diagram in a real browser: the region geometry.

The layout is fixed, so the test measures it: the three circles are equal and symmetric (A and B level, C centred below, equal spacing),
and every item text box lies wholly inside its own region (sampled across the box, in the circle test of each region), at 320 / 650 / 1200 / 1400 px
and in a 300 px grid cell. Text boxes do not overlap each other or the set names, nothing is clipped or wider than its container, and text is at
least 12px. Same method and widths as tests/test_histogram_layout_box.py.
"""
from __future__ import annotations

import json

import pytest

from test_histogram_layout_box import CHROME, WIDTHS, _run
from test_motion_atoms import _gas_batch, _py, core_js  # noqa: F401
from test_venn_diagram import PAYLOADS

pytestmark = pytest.mark.skipif(not CHROME, reason="needs chromium")

DRAWN = ["full", "sparse", "long", "over_caps", "at_caps", "malformed", "huge"]

HARNESS = r'''<script>
window.addEventListener('load', function () {
  var res = [];
  var MASK = {a: [1,0,0], b: [0,1,0], c: [0,0,1], ab: [1,1,0], ac: [1,0,1], bc: [0,1,1], abc: [1,1,1]};
  function hit(a, b, g) { return a.left < b.right + g && b.left < a.right + g && a.top < b.bottom + g && b.top < a.bottom + g; }
  document.querySelectorAll('.case').forEach(function (c) {
    var errs = [], root = c.querySelector('[role=img]'), cs = c.firstElementChild.getBoundingClientRect(), rr = root.getBoundingClientRect(), i, j, k;
    if (rr.right > cs.right + 0.5 || rr.left < cs.left - 0.5) errs.push('chart widens its container: ' + rr.width + ' in ' + cs.width);
    if (root.scrollWidth > root.clientWidth + 1) errs.push('content is wider than the chart box');
    var circ = Array.prototype.slice.call(root.querySelectorAll('.v3o')).map(function (e) { var r = e.getBoundingClientRect(); return {x: (r.left + r.right) / 2, y: (r.top + r.bottom) / 2, r: r.width / 2, h: r.height / 2}; });
    if (circ.length !== 3) { errs.push('expected 3 circles, got ' + circ.length); res.push({id: c.id, errs: errs}); return; }
    var R = circ[0].r;
    circ.forEach(function (q, n) { if (Math.abs(q.r - R) > 0.5 || Math.abs(q.h - q.r) > 0.5) errs.push('circle ' + n + ' is not an equal circle: ' + q.r + ' x ' + q.h); });
    if (Math.abs(circ[0].y - circ[1].y) > 0.5) errs.push('A and B are not level');
    var mid = (circ[0].x + circ[1].x) / 2;
    if (Math.abs(circ[2].x - mid) > 0.5) errs.push('C is not centred under A and B');
    var dAB = circ[1].x - circ[0].x, dAC = Math.hypot(circ[2].x - circ[0].x, circ[2].y - circ[0].y), dBC = Math.hypot(circ[2].x - circ[1].x, circ[2].y - circ[1].y);
    if (Math.abs(dAC - dAB) > 1 || Math.abs(dBC - dAB) > 1) errs.push('centre spacing not equal: ' + dAB + ' ' + dAC + ' ' + dBC);
    if (Math.abs(dAB - R) > 1) errs.push('centres not one radius apart: ' + dAB + ' vs ' + R);
    var boxes = Array.prototype.slice.call(root.querySelectorAll('.v3t'));
    var inside = function (x, y, m) { return circ.map(function (q) { return Math.hypot(x - q.x, y - q.y) <= q.r - 2 ? 1 : (Math.hypot(x - q.x, y - q.y) >= q.r + 2 ? 0 : -1); }); };
    var rects = boxes.map(function (b) { return b.getBoundingClientRect(); });
    boxes.forEach(function (b, n) {
      var r = rects[n], want = MASK[b.getAttribute('data-r')], bad = 0;
      for (i = 0; i <= 8; i++) for (j = 0; j <= 8; j++) {
        var m = inside(r.left + r.width * i / 8, r.top + r.height * j / 8);
        for (k = 0; k < 3; k++) if (m[k] !== want[k]) bad++;
      }
      if (bad) errs.push('text box ' + b.getAttribute('data-r') + ' leaves its region (' + bad + ' sample misses)');
      if (r.left < rr.left - 0.5 || r.right > rr.right + 0.5) errs.push('text box ' + b.getAttribute('data-r') + ' is clipped by the chart box');
      b.querySelectorAll('.v3i').forEach(function (e) {
        var er = e.getBoundingClientRect();
        if (er.height < 12) errs.push('item line is under 12px tall');
        if (er.top < r.top - 0.5 || er.bottom > r.bottom + 0.5) errs.push('item line outside its text box');
        if (parseFloat(getComputedStyle(e).fontSize) < 11.5) errs.push('item font below 12px');
      });
    });
    for (i = 0; i < rects.length; i++) for (j = i + 1; j < rects.length; j++) if (hit(rects[i], rects[j], 0)) errs.push('text boxes overlap: ' + boxes[i].getAttribute('data-r') + ' and ' + boxes[j].getAttribute('data-r'));
    // the three set names: inside the chart box, legible, not overlapping each other or a circle's text
    var nm = Array.prototype.slice.call(root.querySelectorAll('span[style*="text-overflow"]')).filter(function (e) { return !e.classList.contains('v3i'); });
    if (nm.length !== 3) errs.push('expected 3 set names, got ' + nm.length);
    var nr = nm.map(function (e) { return e.getBoundingClientRect(); });
    nm.forEach(function (e, n) {
      if (nr[n].left < rr.left - 0.5 || nr[n].right > rr.right + 0.5 || nr[n].width < 5) errs.push('set name ' + n + ' clipped or collapsed: ' + nr[n].width);
      if (parseFloat(getComputedStyle(e).fontSize) < 12) errs.push('set name font below 12px');
    });
    for (i = 0; i < nr.length; i++) for (j = i + 1; j < nr.length; j++) if (hit(nr[i], nr[j], 0)) errs.push('set names overlap');
    nr.forEach(function (r, n) { rects.forEach(function (t, m) { if (hit(r, t, 0)) errs.push('set name ' + n + ' overlaps a text box'); }); });
    res.push({id: c.id, boxes: boxes.length, r: Math.round(R), errs: errs});
  });
  document.getElementById('out').textContent = JSON.stringify(res);
});
</script>'''


@pytest.mark.parametrize("renderer", ["python", "gas"])
def test_circles_are_symmetric_and_every_item_box_sits_inside_its_region(renderer, core_js):
    blocks = {n: PAYLOADS[n] for n in DRAWN}
    html = {n: _py(b) for n, b in blocks.items()} if renderer == "python" else dict(zip(blocks, _gas_batch(core_js, list(blocks.values()))))
    res = _run(html, harness=HARNESS)
    assert len(res) == len(DRAWN) * len(WIDTHS)
    bad = {r["id"]: r["errs"] for r in res if r["errs"]}
    assert not bad, json.dumps(bad, indent=1)[:3500]
    by = {r["id"]: r for r in res}
    assert by["full-w1400"]["r"] > by["full-w320"]["r"] > by["full-cell300"]["r"] - 1           # the diagram scales with its container
    assert by["full-w320"]["boxes"] == 7 and by["sparse-w320"]["boxes"] == 1
