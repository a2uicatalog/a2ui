"""scatter_matrix and parallel_categories in a real browser: nothing clipped or overlapping, text at least 12px, never wider than the
container, at the widths of tests/test_histogram_layout_box.py (320, 650, 1200, 1400 and a 300 px grid cell)."""
from __future__ import annotations

import json

import pytest

from test_histogram_layout_box import CHROME, WIDTHS, _run
from test_motion_atoms import _gas_batch, _py, core_js  # noqa: F401
from test_splom_parcats import ALL

pytestmark = pytest.mark.skipif(not CHROME, reason="needs chromium")

SM = ["sm_iris", "sm_upper", "sm_six", "sm_equal", "sm_negatives", "sm_many_rows"]
PC = ["pc_three", "pc_two", "pc_six", "pc_other", "pc_mixed_types", "pc_uneven", "pc_long_names"]

COMMON = r'''
  function hit(a, b, g) { return a.left < b.right + g && b.left < a.right + g && a.top < b.bottom + g && b.top < a.bottom + g; }
  function vis(e) { var r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(e).display !== 'none'; }
  function common(c, root, errs) {
    var cs = c.firstElementChild.getBoundingClientRect(), rr = root.getBoundingClientRect();
    if (rr.right > cs.right + 0.5 || rr.left < cs.left - 0.5) errs.push('chart widens its container: ' + rr.width + ' in ' + cs.width);
    if (root.scrollWidth > root.clientWidth + 1) errs.push('content is wider than the chart box: ' + root.scrollWidth + ' > ' + root.clientWidth);
    return rr;
  }
  function texts(root, sel, rr, errs) {
    var els = Array.prototype.slice.call(root.querySelectorAll(sel)).filter(vis), rects = els.map(function (e) { return e.getBoundingClientRect(); }), i, j;
    els.forEach(function (e, k) {
      var r = rects[k];
      if (r.left < rr.left - 0.5 || r.right > rr.right + 0.5) errs.push('"' + e.textContent + '" is clipped by the chart box');
      if (parseFloat(getComputedStyle(e).fontSize) < 11.5) errs.push('"' + e.textContent + '" below 12px');
      if (e.scrollWidth > e.clientWidth + 1 || e.scrollHeight > e.clientHeight + 1) errs.push('"' + e.textContent.slice(0, 30) + '" is cut off: ' + e.scrollWidth + 'x' + e.scrollHeight + ' in ' + e.clientWidth + 'x' + e.clientHeight);
    });
    for (i = 0; i < rects.length; i++) for (j = i + 1; j < rects.length; j++) if (hit(rects[i], rects[j], -0.5) && !els[i].contains(els[j]) && !els[j].contains(els[i])) errs.push('text overlaps: "' + els[i].textContent.slice(0, 20) + '" and "' + els[j].textContent.slice(0, 20) + '"');
    return els.length;
  }
'''
SM_H = '<script>window.addEventListener("load", function () {' + COMMON + r'''
  var res = [];
  document.querySelectorAll('.case').forEach(function (c) {
    var errs = [], root = c.querySelector('.ifsm'), rr = common(c, root, errs);
    var cells = Array.prototype.slice.call(root.querySelectorAll('.smc')).map(function (e) { return e.getBoundingClientRect(); });
    cells.forEach(function (r, k) { if (r.width < 20) errs.push('cell ' + k + ' is only ' + r.width + 'px wide'); if (Math.abs(r.width - r.height) > 1.5) errs.push('cell ' + k + ' is not square'); });
    for (var i = 0; i < cells.length; i++) for (var j = i + 1; j < cells.length; j++) if (hit(cells[i], cells[j], -0.5)) errs.push('cells ' + i + ' and ' + j + ' overlap');
    root.querySelectorAll('.smx').forEach(function (s) {
      var sr = s.getBoundingClientRect();
      s.querySelectorAll('circle').forEach(function (d) { var r = d.getBoundingClientRect(); if (r.left < sr.left - 0.5 || r.right > sr.right + 0.5 || r.top < sr.top - 0.5 || r.bottom > sr.bottom + 0.5) errs.push('a dot leaves its cell'); });
    });
    var n = texts(root, '.smn, .sml, .sma, li', rr, errs);
    res.push({id: c.id, cells: cells.length, texts: n, errs: errs.slice(0, 6)});
  });
  document.getElementById('out').textContent = JSON.stringify(res);
});</script>'''
PC_H = '<script>window.addEventListener("load", function () {' + COMMON + r'''
  var res = [];
  document.querySelectorAll('.case').forEach(function (c) {
    var errs = [], root = c.querySelector('.ifpc'), rr = common(c, root, errs), chart = root.querySelector('[role=img]'), cr = chart.getBoundingClientRect();
    var bars = Array.prototype.slice.call(root.querySelectorAll('.pcb'));
    bars.forEach(function (e) {
      var r = e.getBoundingClientRect();
      if (r.top < cr.top - 0.5 || r.bottom > cr.bottom + 0.5 || r.left < cr.left - 0.5 || r.right > cr.right + 0.5) errs.push('bar ' + e.textContent + ' leaves the chart');
      if (r.height < 20) errs.push('bar ' + e.textContent + ' is only ' + r.height + 'px tall');
      if (parseFloat(getComputedStyle(e).fontSize) < 11.5) errs.push('bar number below 12px');
      if (e.scrollWidth > e.clientWidth + 1 || e.scrollHeight > e.clientHeight + 1) errs.push('bar number cut off');
    });
    for (var i = 0; i < bars.length; i++) for (var j = i + 1; j < bars.length; j++) if (hit(bars[i].getBoundingClientRect(), bars[j].getBoundingClientRect(), -0.5)) errs.push('bars overlap');
    var svg = chart.querySelector('svg').getBoundingClientRect();
    if (Math.abs(svg.width - cr.width) > 1 || Math.abs(svg.height - cr.height) > 1) errs.push('ribbons do not fill the chart');
    var n = texts(root, 'li, [role=img] ~ ul b, div > span', rr, errs);
    res.push({id: c.id, bars: bars.length, texts: n, errs: errs.slice(0, 6)});
  });
  document.getElementById('out').textContent = JSON.stringify(res);
});</script>'''


def _check(names, harness, renderer, core_js):
    blocks = {n: ALL[n] for n in names}
    html = {n: _py(b) for n, b in blocks.items()} if renderer == "python" else dict(zip(blocks, _gas_batch(core_js, list(blocks.values()))))
    res = _run(html, harness=harness)
    assert len(res) == len(names) * len(WIDTHS)
    bad = {r["id"]: r["errs"] for r in res if r["errs"]}
    assert not bad, json.dumps(bad, indent=1)[:3000]
    return res


@pytest.mark.parametrize("renderer", ["python", "gas"])
def test_scatter_matrix_cells_dots_and_text_stay_inside_and_apart(renderer, core_js):
    res = _check(SM, SM_H, renderer, core_js)
    assert all(r["texts"] >= 3 for r in res)


@pytest.mark.parametrize("renderer", ["python", "gas"])
def test_parallel_categories_bars_numbers_and_text_stay_inside_and_apart(renderer, core_js):
    res = _check(PC, PC_H, renderer, core_js)
    assert all(r["bars"] >= 4 for r in res)
