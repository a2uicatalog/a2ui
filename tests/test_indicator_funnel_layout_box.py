"""conversion_funnel (area) and gauge_sla (scale mode) in a real browser: never wider than the container, nothing clipped,
legend rows never overlap, all text >= 12px, the drawing has a real size. Same method and widths as test_histogram_layout_box.py."""
from __future__ import annotations

import json

import pytest

from test_histogram_layout_box import CHROME, WIDTHS, _run
from test_indicator_funnel import FUNNEL, GAUGE
from test_motion_atoms import _gas_batch, _py, core_js  # noqa: F401

pytestmark = pytest.mark.skipif(not CHROME, reason="needs chromium")

DRAWN = {**{"f_" + n: FUNNEL[n] for n in ("basic", "two", "twelve", "zero_mid", "decimals")},
         **{"g_" + n: GAUGE[n] for n in ("bands", "min_only", "above", "below", "nine_steps", "decimals")}}

HARNESS = r'''<script>
window.addEventListener('load', function () {
  var res = [];
  function hit(a, b) { return a.left < b.right && b.left < a.right && a.top < b.bottom && b.top < a.bottom; }
  document.querySelectorAll('.case').forEach(function (c) {
    var errs = [], root = c.querySelector('.ifcf,.ifgs'), cs = c.firstElementChild.getBoundingClientRect(), rr = root.getBoundingClientRect();
    if (rr.right > cs.right + 0.5 || rr.left < cs.left - 0.5) errs.push('widens its container: ' + rr.width + ' in ' + cs.width);
    if (root.scrollWidth > root.clientWidth + 1) errs.push('content wider than the box');
    var svg = root.querySelector('svg[role=img]'), sr = svg.getBoundingClientRect();
    if (sr.width < 100 || sr.height < 40) errs.push('drawing too small: ' + sr.width + 'x' + sr.height);
    if (sr.right > rr.right + 0.5) errs.push('drawing outside the box');
    var rows = Array.prototype.slice.call(root.querySelectorAll('li')), rects = rows.map(function (e) { return e.getBoundingClientRect(); });
    rects.forEach(function (r, k) {
      if (r.right > rr.right + 0.5 || r.left < rr.left - 0.5) errs.push('legend row ' + k + ' clipped');
      if (k && r.top < rects[k - 1].bottom - 0.5) errs.push('legend rows ' + (k - 1) + ',' + k + ' overlap');
    });
    root.querySelectorAll('li, li span, div').forEach(function (e) {
      if (e.children.length === 0 && e.textContent.trim() && parseFloat(getComputedStyle(e).fontSize) < 11.5) errs.push('text below 12px: ' + e.textContent.slice(0, 20));
    });
    res.push({id: c.id, rows: rows.length, errs: errs, w: rr.width});
  });
  document.getElementById('out').textContent = JSON.stringify(res);
});
</script>'''


@pytest.mark.parametrize("renderer", ["python", "gas"])
def test_funnel_and_gauge_fit_every_width(renderer, core_js):
    html = {n: _py(b) for n, b in DRAWN.items()} if renderer == "python" else dict(zip(DRAWN, _gas_batch(core_js, list(DRAWN.values()))))
    res = _run(html, harness=HARNESS)
    assert len(res) == len(DRAWN) * len(WIDTHS)
    bad = {r["id"]: r["errs"] for r in res if r["errs"]}
    assert not bad, json.dumps(bad, indent=1)[:3000]
