"""chartjs_bar in a real browser: no overlapping labels, nothing clipped, never wider than its container, text >= 12px.

Same method as tests/test_histogram_layout_box.py (its `_run` renders each payload at 320 / 650 / 1200 / 1400 px and in a 300 px grid
cell, in both renderers' HTML; the harness below is test-only and the atom's own output carries no script).
"""
from __future__ import annotations

import json

import pytest

from test_chartjs_bar import B, PAYLOADS
from test_histogram_layout_box import CHROME, WIDTHS, _run
from test_motion_atoms import _gas_batch, _py, core_js  # noqa: F401

pytestmark = pytest.mark.skipif(not CHROME, reason="needs chromium")

MANY = [f"Category {i}" for i in range(1, 13)]
LAYOUT = {n: PAYLOADS[n] for n in ("plain", "values_h", "stack", "stack_h", "relative", "overlay", "overlay_h", "log", "range", "reverse", "formats", "pct")}
LAYOUT["many_v"] = B(labels=MANY, datasets=[{"label": f"Series {k}", "data": [(i * 7 + k * 3) % 23 - 4 for i in range(12)]} for k in range(3)], show_values=True)
LAYOUT["many_h"] = B(labels=MANY, datasets=[{"label": "Only series", "data": [(i * 7) % 23 + 1 for i in range(12)]}], orientation="h", show_values=True)
LAYOUT["eight_series_h"] = B(datasets=[{"label": f"S{k}", "data": [k + 1, 2 * k, 3, k * 5]} for k in range(8)], orientation="h", show_values=True)
LAYOUT["long_labels"] = B(labels=["A very long category name that wraps", "Another quite long label", "Short", "Medium length"], orientation="h", show_values=True)
LAYOUT["big_numbers"] = B(datasets=[{"label": "A", "data": [1234567, 2345678, 345678, 4567890]}], show_values=True, y_format=",.0f")

HARNESS = r'''<script>
window.addEventListener('load', function () {
  var res = [];
  function hit(a, b, g) { return a.left < b.right + g && b.left < a.right + g && a.top < b.bottom + g && b.top < a.bottom + g; }
  document.querySelectorAll('.case').forEach(function (c) {
    var errs = [], root = c.querySelector('.ifcb'), cs = c.firstElementChild.getBoundingClientRect(), rr = root.getBoundingClientRect(), i, j;
    if (rr.right > cs.right + 0.5 || rr.left < cs.left - 0.5) errs.push('chart widens its container: ' + rr.width + ' in ' + cs.width);
    if (root.scrollWidth > root.clientWidth + 1) errs.push('content is wider than the chart box: ' + root.scrollWidth + ' > ' + root.clientWidth);
    var plot = root.querySelector('[role=img]'), pr = plot.getBoundingClientRect();
    var bars = Array.prototype.slice.call(plot.querySelectorAll('div[style*="box-sizing:border-box;border:1.5px"]'));
    if (!bars.length) errs.push('no bars');
    bars.forEach(function (e, k) {
      var b = e.getBoundingClientRect();
      if (b.left < pr.left - 0.6 || b.right > pr.right + 0.6 || b.top < pr.top - 0.6 || b.bottom > pr.bottom + 0.6) errs.push('bar ' + k + ' outside the plot');
    });
    var leaves = Array.prototype.slice.call(root.querySelectorAll('div,span')).filter(function (e) {
      return !e.children.length && e.textContent.trim() && getComputedStyle(e).display !== 'none' && !e.closest('style');
    });
    function ink(e) { var g = document.createRange(); g.selectNodeContents(e); var r = g.getBoundingClientRect(); return r.width ? r : e.getBoundingClientRect(); }
    var rects = leaves.map(ink), shown = 0;      // the text itself, not the box that centres or pads it
    leaves.forEach(function (e, k) {
      var r = rects[k];
      if (r.width < 1 || r.height < 1) errs.push('label "' + e.textContent + '" has no box');
      if (r.left < rr.left - 0.5 || r.right > rr.right + 0.5 || r.top < rr.top - 0.5 || r.bottom > rr.bottom + 0.5) errs.push('label "' + e.textContent + '" is clipped by the chart box');
      if (parseFloat(getComputedStyle(e).fontSize) < 11.5) errs.push('label font below 12px: ' + getComputedStyle(e).fontSize);
      if (e.scrollHeight > e.clientHeight + 1 && getComputedStyle(e).overflow === 'hidden') errs.push('label "' + e.textContent + '" is cut');
      if (e.classList.contains('cbv')) shown++;
    });
    for (i = 0; i < rects.length; i++) for (j = i + 1; j < rects.length; j++) if (hit(rects[i], rects[j], 1)) errs.push('labels overlap: "' + leaves[i].textContent + '" and "' + leaves[j].textContent + '"');
    res.push({id: c.id, bars: bars.length, chips: shown, errs: errs, w: rr.width});
  });
  document.getElementById('out').textContent = JSON.stringify(res);
});
</script>'''


@pytest.mark.parametrize("renderer", ["python", "gas"])
def test_nothing_overlaps_clips_or_widens_the_container(renderer, core_js):
    html = {n: _py(b) for n, b in LAYOUT.items()} if renderer == "python" else dict(zip(LAYOUT, _gas_batch(core_js, list(LAYOUT.values()))))
    res = _run(html, harness=HARNESS)
    assert len(res) == len(LAYOUT) * len(WIDTHS)
    bad = {r["id"]: r["errs"] for r in res if r["errs"]}
    assert not bad, json.dumps(bad, indent=1)[:3500]
    by = {r["id"]: r for r in res}
    assert by["plain-w1200"]["bars"] == 8 and by["many_v-w1200"]["bars"] == 36
    assert by["values_h-w1400"]["chips"] > 0 and by["many_v-w320"]["chips"] < by["many_v-w1400"]["chips"]      # narrow containers hide value chips, wide ones show them
