"""arc_diagram in a real browser: the chart never widens its container (and stops at 800 px), the arcs and dots stay inside the drawing, the node dots do not
overlap, every shown label sits under its own dot, inside the chart, below the line, at least 12px, with no two labels overlapping, and a container too
narrow for all of them shows fewer (never overlapping ones) while a wide one shows every label. Same method and widths as tests/test_histogram_layout_box.py
(320 / 650 / 1200 / 1400 px and a 300 px grid cell)."""
from __future__ import annotations

import json

import pytest

from test_histogram_layout_box import CHROME, WIDTHS, _run
from test_motion_atoms import _gas_batch, _py, core_js  # noqa: F401
from test_arc_diagram import PAYLOADS

pytestmark = pytest.mark.skipif(not CHROME, reason="needs chromium")

DRAWN = ["authors", "authors_group", "modules", "forty", "forty_degree", "two", "no_links", "long_labels", "twelve_groups", "dirty"]

HARNESS = r'''<script>
window.addEventListener('load', function () {
  var res = [];
  document.querySelectorAll('.case').forEach(function (c) {
    var errs = [], root = c.querySelector('[role=img]'), cs = c.firstElementChild.getBoundingClientRect(), rr = root.getBoundingClientRect(), n = 0, i, j;
    if (rr.right > cs.right + 0.5 || rr.left < cs.left - 0.5) errs.push('chart widens its container: ' + rr.width + ' in ' + cs.width);
    if (root.scrollWidth > root.clientWidth + 1) errs.push('content wider than the chart box');
    if (rr.width > 800.5) errs.push('wider than 800');
    var svg = root.querySelector('svg'), sr = svg.getBoundingClientRect();
    if (Math.abs(sr.width - (rr.width - 16)) > 1) errs.push('drawing is not the chart width inside its 8px margins');
    var dots = Array.prototype.slice.call(svg.querySelectorAll('circle')).map(function (e) { var r = e.getBoundingClientRect(); return {x: r.left + r.width / 2, y: r.top + r.height / 2, r: r.width / 2}; });
    dots.forEach(function (d, t) {
      if (d.x - d.r < sr.left - 0.5 || d.x + d.r > sr.right + 0.5 || d.y + d.r > sr.bottom + 0.5 || d.y - d.r < sr.top - 0.5) errs.push('dot outside the drawing');
      if (d.r < 2) errs.push('dot radius under 2px: ' + d.r);
      if (t && dots[t - 1].x + dots[t - 1].r > d.x - d.r + 0.01) errs.push('dots overlap');
    });
    svg.querySelectorAll('path').forEach(function (p) {
      var r = p.getBoundingClientRect();
      if (r.top < sr.top - 3.5 || r.left < sr.left - 3.5 || r.right > sr.right + 3.5 || r.bottom > sr.bottom + 3.5) errs.push('arc outside the drawing');
    });
    var labs = Array.prototype.slice.call(root.querySelectorAll('.adl')), all = labs.length;
    var shown = labs.map(function (e, t) { return {e: e, t: t}; }).filter(function (o) { return getComputedStyle(o.e).display !== 'none'; });
    var rects = shown.map(function (o) { return o.e.getBoundingClientRect(); });
    shown.forEach(function (o, k) {
      var e = o.e, r = rects[k], d = dots[o.t];
      n++;
      if (parseFloat(getComputedStyle(e).fontSize) < 11.5) errs.push('label font below 12px');
      if (Math.abs(r.left + r.width / 2 - d.x) > 1) errs.push('label "' + e.textContent + '" is not under its dot');
      if (r.top < sr.bottom - 1) errs.push('label "' + e.textContent + '" is above the line');
      if (r.left < rr.left - 0.5 || r.right > rr.right + 0.5 || r.bottom > rr.bottom + 0.5) errs.push('label "' + e.textContent + '" outside the chart');
      if (e.clientHeight < Math.min(20, 5 * e.textContent.length)) errs.push('label "' + e.textContent + '" is cut to ' + e.clientHeight + 'px');
    });
    for (i = 0; i < rects.length; i++) for (j = i + 1; j < rects.length; j++) {
      if (rects[i].left < rects[j].right - 0.01 && rects[j].left < rects[i].right - 0.01 && rects[i].top < rects[j].bottom && rects[j].top < rects[i].bottom) errs.push('labels overlap: "' + shown[i].e.textContent + '" and "' + shown[j].e.textContent + '"');
    }
    res.push({id: c.id, labels: n, all: all, dots: dots.length, errs: errs.slice(0, 6)});
  });
  document.getElementById('out').textContent = JSON.stringify(res);
});
</script>'''


@pytest.mark.parametrize("renderer", ["python", "gas"])
def test_arc_diagram_stays_in_its_container_and_labels_never_overlap(renderer, core_js):
    blocks = {n: PAYLOADS[n] for n in DRAWN}
    html = {n: _py(b) for n, b in blocks.items()} if renderer == "python" else dict(zip(blocks, _gas_batch(core_js, list(blocks.values()))))
    res = _run(html, harness=HARNESS)
    assert len(res) == len(DRAWN) * len(WIDTHS)
    bad = {r["id"]: r["errs"] for r in res if r["errs"]}
    assert not bad, json.dumps(bad, indent=1)[:3000]
    by = {r["id"]: r for r in res}
    f = [by["forty-" + k]["labels"] for k in ("w320", "cell300", "w650", "w1200")]
    assert f[0] <= f[2] <= f[3] and f[3] == 40 and f[0] < 40 and f[0] >= 5, f      # 40 nodes: thinned at 320 and 650 px, all of them from 660 px
    assert by["forty-w1400"]["labels"] == 40 and by["authors-w320"]["labels"] == 10
