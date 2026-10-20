"""chord_diagram in a real browser (undirected and directed): the chart is a square no wider than its container, every group label stays inside the
chart box, clear of the ring and of every other label (the rotated boxes are tested corner by corner, not by their bounding boxes), reads outward and is
never upside down, text is at least 12px, and the legend wraps inside the container. Same method and widths as tests/test_histogram_layout_box.py."""
from __future__ import annotations

import json

import pytest

from test_chord_diagram import PAYLOADS
from test_histogram_layout_box import CHROME, WIDTHS, _run
from test_motion_atoms import _gas_batch, _py, core_js  # noqa: F401

pytestmark = pytest.mark.skipif(not CHROME, reason="needs chromium")

DRAWN = ["migration", "migration_directed", "traffic", "traffic_directed", "two", "two_directed", "zero_row", "self_loop", "twelve", "twelve_directed",
         "tight", "gated", "long_names", "twelve_plus"]

HARNESS = r'''<script>
window.addEventListener('load', function () {
  var res = [];
  function corners(e, box) {
    var cs = getComputedStyle(e), o = cs.transformOrigin.split(' ').map(parseFloat), m = new DOMMatrix(cs.transform), w = e.offsetWidth, h = e.offsetHeight;
    var bx = box.getBoundingClientRect(), pts = [[0, 0], [w, 0], [w, h], [0, h]];
    return pts.map(function (p) { var q = m.transformPoint(new DOMPoint(p[0] - o[0], p[1] - o[1])); return [bx.left + e.offsetLeft + o[0] + q.x, bx.top + e.offsetTop + o[1] + q.y]; });
  }
  function axes(poly) { var a = [], i; for (i = 0; i < 4; i++) { var p = poly[i], q = poly[(i + 1) % 4]; a.push([q[1] - p[1], p[0] - q[0]]); } return a; }
  function sep(a, b) {
    var ax = axes(a).concat(axes(b)), i, k;
    for (i = 0; i < ax.length; i++) {
      var A = a.map(function (p) { return p[0] * ax[i][0] + p[1] * ax[i][1]; }), B = b.map(function (p) { return p[0] * ax[i][0] + p[1] * ax[i][1]; });
      var len = Math.sqrt(ax[i][0] * ax[i][0] + ax[i][1] * ax[i][1]) || 1;
      if (Math.max.apply(null, A) / len < Math.min.apply(null, B) / len - 0.5 || Math.max.apply(null, B) / len < Math.min.apply(null, A) / len - 0.5) return true;
    }
    return false;
  }
  document.querySelectorAll('.case').forEach(function (c) {
    var errs = [], root = c.querySelector('[role=img]'), cs = c.firstElementChild.getBoundingClientRect(), rr = root.getBoundingClientRect(), i, j;
    if (rr.right > cs.right + 0.5 || rr.left < cs.left - 0.5) errs.push('chart widens its container: ' + rr.width + ' in ' + cs.width);
    if (Math.abs(rr.width - rr.height) > 1) errs.push('chart is not square: ' + rr.width + ' x ' + rr.height);
    if (root.scrollWidth > root.clientWidth + 1 || root.scrollHeight > root.clientHeight + 1) errs.push('content is larger than the chart box');
    var wrap = root.parentElement, wr = wrap.getBoundingClientRect();
    if (wrap.scrollWidth > wrap.clientWidth + 1) errs.push('block is wider than its container');
    var cx = rr.left + rr.width / 2, cy = rr.top + rr.height / 2, ringPx = 190 / 600 * rr.width;
    var labs = Array.prototype.slice.call(root.querySelectorAll('.chl')).filter(function (e) { return getComputedStyle(e).display !== 'none'; });
    var polys = labs.map(function (e) { return corners(e, root); });
    labs.forEach(function (e, k) {
      var cs2 = getComputedStyle(e), m = new DOMMatrix(cs2.transform), ang = Math.atan2(m.b, m.a) * 180 / Math.PI;
      if (Math.abs(ang) > 90.01) errs.push('label "' + e.textContent + '" is upside down (' + ang.toFixed(1) + 'deg)');
      if (parseFloat(cs2.fontSize) < 11.5) errs.push('label font below 12px');
      if (e.offsetWidth < 4) errs.push('label "' + e.textContent + '" has no width');
      polys[k].forEach(function (p) {
        if (p[0] < rr.left - 0.5 || p[0] > rr.right + 0.5 || p[1] < rr.top - 0.5 || p[1] > rr.bottom + 0.5) errs.push('label "' + e.textContent + '" is clipped by the chart box');
        if (Math.sqrt((p[0] - cx) * (p[0] - cx) + (p[1] - cy) * (p[1] - cy)) < ringPx - 0.5) errs.push('label "' + e.textContent + '" touches the ring');
      });
    });
    for (i = 0; i < labs.length; i++) for (j = i + 1; j < labs.length; j++) if (!sep(polys[i], polys[j])) errs.push('labels overlap: "' + labs[i].textContent + '" and "' + labs[j].textContent + '"');
    var leg = Array.prototype.slice.call(root.parentElement.querySelectorAll('.chs'));
    leg.forEach(function (e) { var r = e.getBoundingClientRect(); if (r.right > wr.right + 0.5 || r.left < wr.left - 0.5) errs.push('legend entry "' + e.textContent + '" sticks out'); });
    if (!root.querySelectorAll('.cha').length) errs.push('no group arcs');
    res.push({id: c.id, labels: labs.length, legend: leg.length, errs: errs});
  });
  document.getElementById('out').textContent = JSON.stringify(res);
});
</script>'''


@pytest.mark.parametrize("renderer", ["python", "gas"])
def test_labels_ring_and_legend_never_overlap_clip_or_widen_the_container(renderer, core_js):
    blocks = {n: PAYLOADS[n] for n in DRAWN}
    html = {n: _py(b) for n, b in blocks.items()} if renderer == "python" else dict(zip(blocks, _gas_batch(core_js, list(blocks.values()))))
    res = _run(html, harness=HARNESS)
    assert len(res) == len(DRAWN) * len(WIDTHS)
    bad = {r["id"]: r["errs"] for r in res if r["errs"]}
    assert not bad, json.dumps(bad, indent=1)[:3000]
    by = {r["id"]: r for r in res}
    assert all(r["legend"] >= 2 for r in res)
    assert by["migration-w1200"]["labels"] == 5                          # nothing is dropped where there is room
    assert by["twelve-w320"]["labels"] <= by["twelve-w1200"]["labels"]
