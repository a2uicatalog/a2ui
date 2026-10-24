"""scatter3d_static and surface_static in a real browser: the SVG and its HTML captions stay inside the container at 320/650/1200/1400 px
and in a 300 px cell, captions are >= 12px, never clipped, and never overlap each other. Same method as tests/test_waterfall_layout_box.py."""
from __future__ import annotations

import json

import pytest

from test_histogram_layout_box import CHROME, WIDTHS, _run
from test_motion_atoms import _gas_batch, _py, core_js  # noqa: F401
from test_3d_static import PAYLOADS

pytestmark = pytest.mark.skipif(not CHROME, reason="needs chromium")

DRAWN = ["scatter", "scatter_persp", "scatter_eye", "scatter_low", "scatter_neg", "scatter_four_series", "surface", "surface_xy", "surface_persp", "surface_flat"]

HARNESS = r'''<script>
window.addEventListener('load', function () {
  var res = [];
  function hit(a, b, g) { return a.left < b.right + g && b.left < a.right + g && a.top < b.bottom + g && b.top < a.bottom + g; }
  document.querySelectorAll('.case').forEach(function (c) {
    var errs = [], img = c.querySelector('[role=img]'), cs = c.firstElementChild.getBoundingClientRect(), ir = img.getBoundingClientRect(), svg = img.querySelector('svg').getBoundingClientRect();
    if (ir.right > cs.right + 0.5 || ir.left < cs.left - 0.5) errs.push('chart widens its container: ' + ir.width + ' in ' + cs.width);
    if (svg.width < 100 || svg.height < 60) errs.push('svg collapsed ' + svg.width + 'x' + svg.height);
    var caps = Array.prototype.slice.call(img.querySelectorAll(':scope > div')), rects = caps.map(function (e) { return e.getBoundingClientRect(); }), i, j;
    if (caps.length !== 3) errs.push('expected 3 axis captions, got ' + caps.length);
    rects.forEach(function (r, k) {
      if (r.left < ir.left - 0.5 || r.right > ir.right + 0.5 || r.top < ir.top - 0.5 || r.bottom > ir.bottom + 0.5) errs.push('caption "' + caps[k].textContent + '" is clipped by the chart box');
      if (parseFloat(getComputedStyle(caps[k].firstElementChild).fontSize) < 11.5) errs.push('caption font below 12px');
    });
    for (i = 0; i < rects.length; i++) for (j = i + 1; j < rects.length; j++) if (hit(rects[i], rects[j], 1)) errs.push('captions overlap: "' + caps[i].textContent + '" and "' + caps[j].textContent + '"');
    var minx = 1e9;
    Array.prototype.forEach.call(img.querySelectorAll('svg line, svg polygon, svg circle, svg rect'), function (e) { minx = Math.min(minx, e.getBoundingClientRect().left); });
    if (rects.length === 3 && rects[2].right > minx + 1) errs.push('z caption runs into the drawing: ' + rects[2].right + ' > ' + minx);
    if (document.documentElement.scrollWidth > window.innerWidth + 1 && c.scrollWidth > c.clientWidth + 1) errs.push('page scrolls sideways');
    res.push({id: c.id, errs: errs});
  });
  document.getElementById('out').textContent = JSON.stringify(res);
});
</script>'''


@pytest.mark.parametrize("renderer", ["python", "gas"])
def test_captions_never_overlap_or_widen_the_container(renderer, core_js):
    blocks = {n: PAYLOADS[n] for n in DRAWN}
    html = {n: _py(b) for n, b in blocks.items()} if renderer == "python" else dict(zip(blocks, _gas_batch(core_js, list(blocks.values()))))
    res = _run(html, harness=HARNESS)
    assert len(res) == len(DRAWN) * len(WIDTHS)
    bad = {r["id"]: r["errs"] for r in res if r["errs"]}
    assert not bad, json.dumps(bad, indent=1)[:3000]
