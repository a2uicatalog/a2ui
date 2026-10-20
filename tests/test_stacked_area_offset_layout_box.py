"""stacked_area with an offset in a real browser: the picture fills its plot, the axis labels never overlap or clip, the legend stays inside, and
the chart is never wider than its container. Same method and widths as tests/test_waterfall_layout_box.py (widths 320 / 650 / 1200 / 1400 and a 300 px grid cell)."""
from __future__ import annotations

import json

import pytest

from test_histogram_layout_box import CHROME, WIDTHS, _run
from test_motion_atoms import _gas_batch, _py, core_js  # noqa: F401
from test_stacked_area_offset import CHARTS, PAYLOADS

pytestmark = pytest.mark.skipif(not CHROME, reason="needs chromium")

HARNESS = r'''<script>
window.addEventListener('load', function () {
  var res = [];
  function hit(a, b, g) { return a.left < b.right + g && b.left < a.right + g && a.top < b.bottom + g && b.top < a.bottom + g; }
  document.querySelectorAll('.case').forEach(function (c) {
    var errs = [], root = c.querySelector('.ifsa'), cs = c.firstElementChild.getBoundingClientRect(), rr = root.getBoundingClientRect(), i, j;
    if (rr.right > cs.right + 0.5 || rr.left < cs.left - 0.5) errs.push('chart widens its container: ' + rr.width + ' in ' + cs.width);
    if (root.scrollWidth > root.clientWidth + 1) errs.push('content is wider than the chart box: ' + root.scrollWidth + ' > ' + root.clientWidth);
    var svg = root.querySelector('svg'), sr = svg.getBoundingClientRect(), plot = svg.parentNode.getBoundingClientRect();
    if (sr.width < 110) errs.push('plot too narrow: ' + sr.width);
    if (Math.abs(sr.height - 240) > 1 || Math.abs(sr.width - plot.width) > 1.5) errs.push('picture does not fill the plot: ' + sr.width + 'x' + sr.height + ' in ' + plot.width);
    var polys = Array.prototype.slice.call(svg.querySelectorAll('polygon')).map(function (p) { return p.getBoundingClientRect(); });
    polys.forEach(function (r, k) { if (r.left < sr.left - 1.5 || r.right > sr.right + 1.5 || r.top < sr.top - 1.5 || r.bottom > sr.bottom + 1.5) errs.push('layer ' + k + ' outside the plot'); });
    var xl = Array.prototype.slice.call(root.querySelectorAll('.sax')).filter(function (e) { return getComputedStyle(e).display !== 'none'; }).map(function (e) { return e.children[1]; });
    var yl = Array.prototype.slice.call(root.querySelectorAll('.say'));
    var lg = Array.prototype.slice.call(root.querySelectorAll('.ifsa > div:last-child > span'));
    var labs = xl.concat(yl, lg).filter(function (e) { return e.textContent !== ''; }), rects = labs.map(function (e) { return e.getBoundingClientRect(); });
    rects.forEach(function (r, k) {
      if (r.left < rr.left - 0.5 || r.right > rr.right + 0.5 || r.top < rr.top - 0.5 || r.bottom > rr.bottom + 0.5) errs.push('label "' + labs[k].textContent + '" is clipped by the chart box');
      if (r.width < 1) errs.push('label "' + labs[k].textContent + '" has no box');
      if (parseFloat(getComputedStyle(labs[k]).fontSize) < 11.5) errs.push('label font below 12px: ' + getComputedStyle(labs[k]).fontSize);
    });
    for (i = 0; i < rects.length; i++) for (j = i + 1; j < rects.length; j++) if (hit(rects[i], rects[j], 1)) errs.push('labels overlap: "' + labs[i].textContent + '" and "' + labs[j].textContent + '"');
    xl.forEach(function (e) { if (e.getBoundingClientRect().top < sr.bottom) errs.push('x label above the axis'); });
    yl.forEach(function (e) { if (e.getBoundingClientRect().right > sr.left + 0.5) errs.push('y label inside the plot'); });
    res.push({id: c.id, layers: polys.length, xlabels: xl.length, ylabels: yl.length, errs: errs, w: rr.width});
  });
  document.getElementById('out').textContent = JSON.stringify(res);
});
</script>'''


@pytest.mark.parametrize("renderer", ["python", "gas"])
def test_layers_axis_labels_and_legend_never_overlap_clip_or_widen_the_container(renderer, core_js):
    blocks = {n: PAYLOADS[n] for n in CHARTS}
    html = {n: _py(b) for n, b in blocks.items()} if renderer == "python" else dict(zip(blocks, _gas_batch(core_js, list(blocks.values()))))
    res = _run(html, harness=HARNESS)
    assert len(res) == len(CHARTS) * len(WIDTHS)
    bad = {r["id"]: r["errs"] for r in res if r["errs"]}
    assert not bad, json.dumps(bad, indent=1)[:3000]
    by = {r["id"]: r for r in res}
    assert by["expand-w320"]["xlabels"] <= by["expand-w1200"]["xlabels"] and by["expand-w1200"]["xlabels"] >= 3      # a wide container shows more of the x axis
    assert all(r["ylabels"] == (5 if PAYLOADS[r["id"].split("-")[0]]["offset"] == "expand" else 0) for r in res)    # only expand has a value axis
    assert all(r["layers"] == html[r["id"].split("-")[0]].count("<polygon") for r in res)


def test_a_leaking_page_stylesheet_does_not_break_the_chart(core_js):
    leak = '<style>div{position:relative}svg{max-width:50%}polygon{stroke:red}span{position:relative}</style>'
    res = _run({n: _py(PAYLOADS[n]) for n in ("expand", "wiggle", "long_labels")}, leak, harness=HARNESS)
    assert not [r for r in res if any("widens" in e or "wider" in e for e in r["errs"])], res
