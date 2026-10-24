"""heatmap (extended path) in a real browser: cells never overlap, labels stay >= 12px and unclipped, the block is never wider than its
container (a wide grid is squeezed to fit, never scrolled or clipped). Same method and widths as tests/test_histogram_layout_box.py."""
from __future__ import annotations

import json

import pytest

from test_heatmap import EXT
from test_histogram_layout_box import CHROME, WIDTHS, _run
from test_motion_atoms import _gas_batch, _py, core_js  # noqa: F401

pytestmark = pytest.mark.skipif(not CHROME, reason="needs chromium")

DRAWN = ["hostile", "plain", "values", "diverging", "range", "percent", "custom", "holes", "all_equal", "big", "version2"]

HARNESS = r'''<script>
window.addEventListener('load', function () {
  var res = [];
  function hit(a, b) { return a.left < b.right - 0.5 && b.left < a.right - 0.5 && a.top < b.bottom - 0.5 && b.top < a.bottom - 0.5; }
  document.querySelectorAll('.case').forEach(function (c) {
    var errs = [], root = c.querySelector('.ifhm'), cs = c.firstElementChild.getBoundingClientRect(), rr = root.getBoundingClientRect(), i, j;
    if (rr.right > cs.right + 0.5 || rr.left < cs.left - 0.5) errs.push('block widens its container: ' + rr.width + ' in ' + cs.width);
    if (root.scrollWidth > root.clientWidth + 1) errs.push('content is wider than the block: ' + root.scrollWidth + ' > ' + root.clientWidth);
    var sc = root.querySelector('.hms'), sr = sc.getBoundingClientRect();
    var compact = !!root.querySelector('[style*="grid-column:span"]');
    var cells = Array.prototype.slice.call(root.querySelectorAll('.hmc'));
    var rects = cells.map(function (e) { return e.getBoundingClientRect(); });
    for (i = 0; i < rects.length; i++) {
      if (rects[i].width < (compact ? 3 : 20) || rects[i].height < (compact ? 14 : 20)) errs.push('cell ' + i + ' too small: ' + rects[i].width + 'x' + rects[i].height);
      if (i && hit(rects[i], rects[i - 1])) errs.push('cells ' + (i - 1) + ',' + i + ' overlap');
      if (cells[i].scrollWidth > cells[i].clientWidth + 1) errs.push('cell ' + i + ' text clipped');
    }
    var texts = Array.prototype.slice.call(root.querySelectorAll('.hms [role=img] > div, .hmb span'));
    texts.forEach(function (e) {
      if (e.textContent && parseFloat(getComputedStyle(e).fontSize) < 11.5) errs.push('font below 12px: ' + e.textContent);
      if (e.scrollWidth > e.clientWidth + 1 && getComputedStyle(e).overflowWrap !== 'anywhere') errs.push('label clipped: ' + e.textContent);
    });
    var rowlab = Array.prototype.slice.call(root.querySelectorAll('.hms [role=img] > div[style*="justify-content:flex-end"]'));
    rowlab.forEach(function (e) { if (e.getBoundingClientRect().width < 60) errs.push('row label column collapsed: ' + e.textContent + ' ' + e.getBoundingClientRect().width); if (e.getBoundingClientRect().height > 40) errs.push('row label wraps to ' + e.getBoundingClientRect().height + 'px: ' + e.textContent); });
    var bar = root.querySelector('.hmb');
    if (bar && bar.getBoundingClientRect().right > rr.right + 0.5) errs.push('colour bar outside block');
    if (bar && bar.getBoundingClientRect().top < sr.bottom - 0.5) errs.push('colour bar overlaps the grid');
    res.push({id: c.id, cells: cells.length, errs: errs, scrolls: sc.scrollWidth > sc.clientWidth + 1});
  });
  document.getElementById('out').textContent = JSON.stringify(res);
});
</script>'''


@pytest.mark.parametrize("renderer", ["python", "gas"])
def test_cells_and_labels_never_overlap_or_widen_the_container(renderer, core_js):
    blocks = {n: EXT[n] for n in DRAWN}
    html = {n: _py(dict(b)) for n, b in blocks.items()} if renderer == "python" else dict(zip(blocks, _gas_batch(core_js, list(blocks.values()))))
    res = _run(html, harness=HARNESS)
    assert len(res) == len(DRAWN) * len(WIDTHS)
    bad = {r["id"]: r["errs"] for r in res if r["errs"]}
    assert not bad, json.dumps(bad, indent=1)[:3000]
    assert all(r["cells"] == html[r["id"].split("-")[0]].count('class="hmc') for r in res)
    by = {r["id"]: r for r in res}
    assert not any(r["scrolls"] for r in res)   # no grid scrolls: a 40-column grid is squeezed into its box, never cut off (HM-4)
