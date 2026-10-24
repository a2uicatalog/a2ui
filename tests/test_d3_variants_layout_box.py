"""The d3-variants options in a real browser at 320 / 650 / 1200 / 1400 px and in a 300 px cell: every visible text is at least 12px, sits inside the chart
box and overlaps no other text, and the chart is never wider than its container. Same method as tests/test_box_plot_layout_box.py."""
from __future__ import annotations

import json

import pytest

from test_d3_variants import G3, V, W
from test_histogram_layout_box import CHROME, WIDTHS, _run
from test_motion_atoms import _gas_batch, _py, core_js  # noqa: F401

pytestmark = pytest.mark.skipif(not CHROME, reason="needs chromium")

MANY = [{"label": "Region number %d" % (k + 1), "values": [k + x for x in V]} for k in range(12)]
CASES = {
    "box_violin_notch_mean": {"type": "box_plot", "groups": G3[:2], "shape": "violin", "notches": True, "show_mean": True, "unit": "ms", "x_label": "Latency"},
    "box_vertical": {"type": "box_plot", "groups": MANY, "orientation": "v", "quartile_method": "inclusive"},
    "box_vertical_violin": {"type": "box_plot", "groups": MANY[:5], "orientation": "v", "shape": "violin", "show_mean": True},
    "box_stats": {"type": "box_plot", "groups": [{"label": "S", "stats": {"q1": 2, "median": 3, "q3": 5, "n": 20}}], "notches": True},
    "hist_percent_cum": {"type": "histogram", "values": V, "bin_size": 5, "norm": "percent", "cumulative": True, "x_label": "Value"},
    "hist_sum_negative": {"type": "histogram", "values": V, "bin_size": 7, "func": "sum", "weights": [w - 5 for w in W]},
    "hist_density": {"type": "histogram", "values": V, "bin_size": 0.5, "norm": "density", "bin_start": 0, "bin_end": 60},
    "treemap_30": {"type": "treemap", "max_items": 30, "items": [{"category": "A", "name": "Item %d" % k, "value": 100 - k} for k in range(30)]},
}

HARNESS = r'''<script>
window.addEventListener('load', function () { try {
  var res = [];
  function hit(a, b) { return a.left < b.right && b.left < a.right && a.top < b.bottom && b.top < a.bottom; }
  document.querySelectorAll('.case').forEach(function (c) {
    var errs = [], cs = c.firstElementChild.getBoundingClientRect(), root = c.querySelector('.ifbp,.ifhg') || c.firstElementChild;
    var rr = root.getBoundingClientRect(), txt = [];
    if (rr.right > cs.right + 0.5) errs.push('chart widens its container: ' + rr.width + ' in ' + cs.width);
    if (root.scrollWidth > root.clientWidth + 1) errs.push('content wider than the chart: ' + root.scrollWidth + ' > ' + root.clientWidth);
    root.querySelectorAll('div,span').forEach(function (e) {
      if (e.children.length || !e.textContent.trim() || e.closest('table') || e.closest('style')) return;
      var cs2 = getComputedStyle(e), r = e.getBoundingClientRect();
      if (cs2.display === 'none' || cs2.visibility === 'hidden' || r.width === 0 || e.closest('[style*="display:none"]')) return;
      if (parseFloat(cs2.fontSize) < 11.5 && !e.closest('[style*="position:absolute"][style*="background"]')) errs.push('font below 12px: ' + e.textContent.slice(0, 20));
      txt.push([e, r]);
    });
    txt.forEach(function (t) { var r = t[1]; if (r.left < rr.left - 0.5 || r.right > rr.right + 0.5) errs.push('text clipped by the chart: ' + t[0].textContent.slice(0, 20)); });
    for (var i = 0; i < txt.length; i++) for (var j = i + 1; j < txt.length; j++) if (hit(txt[i][1], txt[j][1]) && !txt[i][0].contains(txt[j][0]) && !txt[j][0].contains(txt[i][0])) errs.push('texts overlap: "' + txt[i][0].textContent.slice(0, 15) + '" and "' + txt[j][0].textContent.slice(0, 15) + '"');
    res.push({id: c.id, texts: txt.length, errs: errs});
  });
  document.getElementById('out').textContent = JSON.stringify(res);
 } catch (e) { document.getElementById('out').textContent = JSON.stringify([{id: 'error', texts: 0, errs: [String(e)]}]); }
});
</script>'''


@pytest.mark.parametrize("renderer", ["python", "gas"])
def test_new_options_never_overlap_clip_or_widen_the_container(renderer, core_js):
    html = {n: _py(b) for n, b in CASES.items()} if renderer == "python" else dict(zip(CASES, _gas_batch(core_js, list(CASES.values()))))
    res = _run(html, harness=HARNESS)
    assert len(res) == len(CASES) * len(WIDTHS)
    bad = {r["id"]: r["errs"] for r in res if r["errs"]}
    assert not bad, json.dumps(bad, indent=1)[:3000]
    assert all(r["texts"] > 0 for r in res)
