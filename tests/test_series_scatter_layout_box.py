"""chartjs_line / scatter_trend `series[]` in a real browser: axis labels never overlap or run out of the card, text is at least 12px,
nothing is wider than its container, markers stay inside the plot.

Renders every payload in 320 / 650 / 1200 / 1400 px containers and in a 300 px grid cell, in both renderers' HTML. The test-only script
writes measurements into the DOM; the atom's own output carries no script. Same method as tests/test_histogram_layout_box.py.
"""
from __future__ import annotations

import json

import pytest

from test_histogram_layout_box import CHROME, WIDTHS, _run
from test_motion_atoms import _gas_batch, _py, core_js  # noqa: F401
from test_series_scatter import PAYLOADS, _ser

pytestmark = pytest.mark.skipif(not CHROME, reason="needs chromium")

HARNESS = r'''<script>
window.addEventListener('load', function () {
  var res = [];
  function hit(a, b, g) { return a.left < b.right + g && b.left < a.right + g && a.top < b.bottom + g && b.top < a.bottom + g; }
  function inside(r, c, t) { return r.left >= c.left - t && r.right <= c.right + t && r.top >= c.top - t && r.bottom <= c.bottom + t; }
  document.querySelectorAll('.case').forEach(function (c) {
    var errs = [], cs = c.firstElementChild.getBoundingClientRect(), wrap = c.querySelector('div > div'), root = c.querySelector('.ifps'), rr = root.getBoundingClientRect();
    var plot = root.querySelector('[role=img]'), pr = plot.getBoundingClientRect(), svg = plot.querySelector('svg'), i, j;
    if (rr.right > cs.right + 0.5 || rr.left < cs.left - 0.5) errs.push('chart widens its container: ' + rr.width + ' in ' + cs.width);
    if (root.scrollWidth > root.clientWidth + 1) errs.push('content is wider than the card: ' + root.scrollWidth + ' > ' + root.clientWidth);
    if (pr.width < 150) errs.push('plot too narrow: ' + pr.width);
    if (Math.abs(pr.width / pr.height - 1.6) > 0.02) errs.push('plot aspect ' + pr.width / pr.height);
    var yl = Array.prototype.slice.call(plot.querySelectorAll(':scope > div[style*="right:100%"]'));
    var xl = Array.prototype.slice.call(plot.querySelectorAll(':scope > div[style*="top:100%;left"]'));
    var tl = Array.prototype.slice.call(plot.querySelectorAll(':scope > div[style*="translate(-50%,-135%)"]'));
    var axt = root.querySelector(':scope > div[style*="text-align:center"]');
    var leg = Array.prototype.slice.call(root.querySelectorAll('span[style*="inline-flex"]'));
    var labs = yl.concat(xl, tl, axt ? [axt] : [], leg.map(function (e) { return e.lastElementChild; })), rects = labs.map(function (e) { return e.getBoundingClientRect(); });
    rects.forEach(function (r, k) {
      if (!inside(r, rr, 0.5)) errs.push('label "' + labs[k].textContent + '" is clipped by the card');
      if (r.width < 1) errs.push('label "' + labs[k].textContent + '" has no box');
      if (parseFloat(getComputedStyle(labs[k]).fontSize) < 11.5) errs.push('label font below 12px: ' + getComputedStyle(labs[k]).fontSize);
    });
    var axis = yl.concat(xl, axt ? [axt] : []), ar = axis.map(function (e) { return e.getBoundingClientRect(); });
    for (i = 0; i < ar.length; i++) for (j = i + 1; j < ar.length; j++) if (hit(ar[i], ar[j], 1)) errs.push('axis labels overlap: "' + axis[i].textContent + '" and "' + axis[j].textContent + '"');
    xl.forEach(function (e) { if (e.getBoundingClientRect().top < pr.bottom - 0.5) errs.push('x label above the axis'); });
    yl.forEach(function (e) { if (e.getBoundingClientRect().right > pr.left + 0.5) errs.push('y label inside the plot'); });
    var lr = leg.map(function (e) { return e.getBoundingClientRect(); });
    for (i = 0; i < lr.length; i++) { if (!inside(lr[i], rr, 0.5)) errs.push('legend item clipped'); for (j = i + 1; j < lr.length; j++) if (hit(lr[i], lr[j], 0)) errs.push('legend items overlap'); }
    if (lr.length && lr.some(function (r) { return r.top < pr.bottom; })) errs.push('legend above the plot bottom');
    Array.prototype.slice.call(svg.querySelectorAll('path[fill-opacity="0.15"], path[stroke-linejoin]')).forEach(function (p) { var r = p.getBoundingClientRect(); if (r.width > pr.width + 8 || r.height > pr.height + 8) errs.push('a line is far larger than the plot'); });
    Array.prototype.slice.call(svg.querySelectorAll('path:not([stroke-linejoin]):not([fill-opacity="0.15"])')).forEach(function (p) {
      var r = p.getBoundingClientRect(); if (r.width && (r.left < pr.left - 14 || r.right > pr.right + 14 || r.top < pr.top - 14 || r.bottom > pr.bottom + 14)) errs.push('a marker is outside the plot');
    });
    tl.forEach(function (e) { var r = e.getBoundingClientRect(); if (r.left < pr.left - 40 || r.right > pr.right + 40) errs.push('point label far outside the plot'); });
    var tb = root.parentNode.querySelector('table'), ts = getComputedStyle(tb);
    if (ts.position !== 'absolute' || ts.clip.replace(/\s/g, '') !== 'rect(0px,0px,0px,0px)') errs.push('hidden table is not visually hidden');
    var wr = root.parentNode.getBoundingClientRect();
    if (wr.width > cs.width + 0.5) errs.push('wrapper widens its container');
    res.push({id: c.id, errs: errs, w: rr.width, xl: xl.length, yl: yl.length});
  });
  document.getElementById('out').textContent = JSON.stringify(res);
});
</script>'''

LONG = {"type": "chartjs_line", "title": "A long title that wraps over more than one line in a narrow container " * 2, "x_label": "A long x axis title " * 3, "y_label": "A long y axis title " * 3,
        "series": [_ser("A very long series name that has to wrap inside the legend " * 2, y=[1200000, 3400000, 2200000, 5100000]), _ser("second", y=[5, 6, 7, 8])]}
BIG = {"type": "scatter_trend", "series": [{"label": "big", "x": list(range(5000)), "y": [(i * 37) % 101 for i in range(5000)], "mode": "markers"}]}
TEXT = {"type": "chartjs_line", "series": [{"label": "t", "x": list(range(12)), "y": [(i * 7) % 11 for i in range(12)], "mode": "lines+markers+text"}]}
DRAWN = {**PAYLOADS, "long": LONG, "big": BIG, "text": TEXT,
         "years": {"type": "chartjs_line", "series": [{"label": "y", "x": ["1990", "2005", "2024"], "y": [1, 9, 4]}]},
         "seconds": {"type": "chartjs_line", "series": [{"label": "s", "x": ["2024-01-01T00:00:00", "2024-01-01T00:00:20"], "y": [1, 2]}]}}


@pytest.mark.parametrize("renderer", ["python", "gas"])
def test_axes_labels_and_legend_never_overlap_or_widen_the_container(renderer, core_js):
    names = list(DRAWN)
    html = {n: _py(dict(DRAWN[n])) for n in names} if renderer == "python" else dict(zip(names, _gas_batch(core_js, [DRAWN[n] for n in names])))
    res = _run(html, harness=HARNESS)
    assert len(res) == len(names) * len(WIDTHS)
    bad = {r["id"]: r["errs"] for r in res if r["errs"]}
    assert not bad, json.dumps(bad, indent=1)[:3500]
