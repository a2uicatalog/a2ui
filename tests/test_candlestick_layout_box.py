"""candlestick_chart in a real browser: candles stay inside the plot, the axis, legend and volume labels never overlap or clip, text is at
least 12px and the chart is never wider than its container. Same method and widths as tests/test_histogram_layout_box.py."""
from __future__ import annotations

import json

import pytest

from test_histogram_layout_box import CHROME, WIDTHS, _run
from test_motion_atoms import _gas_batch, _py, core_js  # noqa: F401
from test_candlestick import PAYLOADS

pytestmark = pytest.mark.skipif(not CHROME, reason="needs chromium")

DRAWN = ["small", "small_ohlc", "thirty", "thirty_ohlc", "no_volume", "hundred", "full_cap", "weekly", "intraday", "one_bar", "flat", "big", "tiny", "negative", "years", "volume_gaps"]

HARNESS = r'''<script>
window.addEventListener('load', function () {
  var res = [];
  function hit(a, b, g) { return a.left < b.right + g && b.left < a.right + g && a.top < b.bottom + g && b.top < a.bottom + g; }
  document.querySelectorAll('.case').forEach(function (c) {
    var errs = [], root = c.querySelector('.ifcs'), cs = c.firstElementChild.getBoundingClientRect(), rr = root.getBoundingClientRect(), i, j;
    if (rr.right > cs.right + 0.5 || rr.left < cs.left - 0.5) errs.push('chart widens its container: ' + rr.width + ' in ' + cs.width);
    if (root.scrollWidth > root.clientWidth + 1) errs.push('content is wider than the chart box: ' + root.scrollWidth + ' > ' + root.clientWidth);
    var plot = root.querySelector('.csp').getBoundingClientRect();
    if (plot.width < 110) errs.push('plot too narrow: ' + plot.width);
    var cands = Array.prototype.slice.call(root.querySelectorAll('.csc'));
    cands.forEach(function (e, k) {
      var r = e.getBoundingClientRect();
      if (r.left < plot.left - 1.5 || r.right > plot.right + 1.5) errs.push('candle ' + k + ' outside the plot');
      var inner = e.querySelectorAll('.csk,.cso,.csb');
      Array.prototype.forEach.call(inner, function (x) { var q = x.getBoundingClientRect(); if (q.top < plot.top - 2 || q.bottom > plot.bottom + 2) errs.push('candle ' + k + ' above or below the plot'); });
    });
    var vq = root.querySelector('.csq');
    if (vq) Array.prototype.forEach.call(vq.querySelectorAll('.csv'), function (e, k) { var q = e.getBoundingClientRect(), p = vq.getBoundingClientRect(); if (q.left < p.left - 1.5 || q.right > p.right + 1.5 || q.top < p.top - 1.5) errs.push('volume bar ' + k + ' outside its panel'); });
    var labs = Array.prototype.slice.call(root.querySelectorAll('.csyl,.cscap,.csl > span'))
      .concat(Array.prototype.slice.call(root.querySelectorAll('.hgx')).filter(function (e) { return getComputedStyle(e).display !== 'none'; }).map(function (e) { return e.children[1]; }));
    var rects = labs.map(function (e) { return e.getBoundingClientRect(); });
    rects.forEach(function (r, k) {
      if (r.left < rr.left - 0.5 || r.right > rr.right + 0.5 || r.top < rr.top - 0.5 || r.bottom > rr.bottom + 0.5) errs.push('label "' + labs[k].textContent + '" is clipped by the chart box');
      if (parseFloat(getComputedStyle(labs[k]).fontSize) < 11.99) errs.push("label font below 12px");
    });
    for (i = 0; i < rects.length; i++) for (j = i + 1; j < rects.length; j++) if (hit(rects[i], rects[j], 1)) errs.push('labels overlap: "' + labs[i].textContent + '" and "' + labs[j].textContent + '"');
    res.push({id: c.id, cands: cands.length, xlabels: labs.length, errs: errs});
  });
  document.getElementById('out').textContent = JSON.stringify(res);
});
</script>'''


@pytest.mark.parametrize("renderer", ["python", "gas"])
def test_candles_and_labels_never_overlap_or_widen_the_container(renderer, core_js):
    blocks = {n: PAYLOADS[n] for n in DRAWN}
    html = {n: _py(b) for n, b in blocks.items()} if renderer == "python" else dict(zip(blocks, _gas_batch(core_js, list(blocks.values()))))
    res = _run(html, harness=HARNESS)
    assert len(res) == len(DRAWN) * len(WIDTHS)
    bad = {r["id"]: r["errs"] for r in res if r["errs"]}
    assert not bad, json.dumps(bad, indent=1)[:3000]
    assert all(r["cands"] == html[r["id"].split("-")[0]].count('class="csc ') for r in res)


NARROW = r'''<script>
window.addEventListener('load', function () {
  var res = [];
  document.querySelectorAll('.case').forEach(function (c) {
    var vis = Array.prototype.slice.call(c.querySelectorAll('.hgx')).filter(function (e) { return getComputedStyle(e).display !== 'none'; }).map(function (e) { return e.children[1].textContent; });
    res.push({id: c.id, labels: vis});
  });
  document.getElementById('out').textContent = JSON.stringify(res);
});
</script>'''


@pytest.mark.parametrize("renderer", ["python", "gas"])
def test_three_daily_bars_show_a_date_at_320px(renderer, core_js):
    """C2: the narrow rule used to keep only the 12 PM ticks, so the axis had no date at all."""
    blocks = {"daily3": PAYLOADS["small"]}
    html = {n: _py(b) for n, b in blocks.items()} if renderer == "python" else dict(zip(blocks, _gas_batch(core_js, list(blocks.values()))))
    res = {r["id"]: r["labels"] for r in _run(html, harness=NARROW)}
    labs = res["daily3-w320"]
    assert labs and any(not l.endswith(("AM", "PM")) for l in labs), labs
