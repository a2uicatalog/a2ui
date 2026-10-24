"""choropleth_map in a real browser: never wider than its container, legend entries readable (>= 12px) and not overlapping or clipped, notes readable,
at 320 / 650 / 1200 / 1400 px and in a 300 px grid cell. Same method as tests/test_geo_map_layout_box.py."""
from __future__ import annotations

import json

import pytest

from test_choropleth_map import EUROPE, STATES, US, WORLD, _vals
from test_histogram_layout_box import CHROME, WIDTHS, _run
from test_motion_atoms import _gas_batch, _py, core_js  # noqa: F401

pytestmark = pytest.mark.skipif(not CHROME, reason="needs chromium")

DRAWN = {"world": WORLD, "us": US, "eu": {"type": "choropleth_map", "region_set": "europe-countries", "values": _vals(EUROPE)},
         "equal": {"type": "choropleth_map", "region_set": "us-states", "scale": {"kind": "diverging"}, "values": [{"id": "CA", "value": 4}, {"id": "TX", "value": 4}]},
         "partial": {"type": "choropleth_map", "region_set": "us-states", "values": _vals(STATES[:10]), "unit": "%", "legend_title": "Rate"}}

HARNESS = r'''<script>
window.addEventListener('load', function () {
  var res = [];
  function hit(a, b, g) { return a.left < b.right + g && b.left < a.right + g && a.top < b.bottom + g && b.top < a.bottom + g; }
  document.querySelectorAll('.case').forEach(function (c) {
    var errs = [], root = c.querySelector('[data-cb-root]'), cs = c.firstElementChild.getBoundingClientRect(), rr = root.getBoundingClientRect(), i, j;
    if (rr.right > cs.right + 0.5 || rr.left < cs.left - 0.5) errs.push('map widens its container: ' + rr.width + ' in ' + cs.width);
    if (root.scrollWidth > root.clientWidth + 1) errs.push('content is wider than the box: ' + root.scrollWidth + ' > ' + root.clientWidth);
    var svg = root.querySelector('svg[role=img]'), sr = svg.getBoundingClientRect();
    if (sr.width < 100 || sr.height < 40) errs.push('map too small: ' + sr.width + 'x' + sr.height);
    var tiles = svg.querySelectorAll('[data-cb=tile]');
    var lis = Array.prototype.slice.call(root.querySelectorAll('li')), rects = lis.map(function (e) { return e.getBoundingClientRect(); });
    rects.forEach(function (r, k) {
      if (r.right > rr.right + 0.5 || r.left < rr.left - 0.5) errs.push('legend entry "' + lis[k].textContent + '" is clipped');
      if (parseFloat(getComputedStyle(lis[k].querySelector('span:last-child')).fontSize) < 11.5) errs.push('legend font below 12px');
    });
    for (i = 0; i < rects.length; i++) for (j = i + 1; j < rects.length; j++) if (hit(rects[i], rects[j], 0)) errs.push('legend entries overlap: "' + lis[i].textContent + '" and "' + lis[j].textContent + '"');
    Array.prototype.slice.call(root.querySelectorAll('p')).forEach(function (p) { if (parseFloat(getComputedStyle(p).fontSize) < 11.5) errs.push('note font below 12px'); });
    res.push({id: c.id, tiles: tiles.length, lis: lis.length, errs: errs});
  });
  document.getElementById('out').textContent = JSON.stringify(res);
});
</script>'''


@pytest.mark.parametrize("renderer", ["python", "gas"])
def test_map_and_legend_stay_inside_at_every_width(renderer, core_js):
    html = {n: _py(b) for n, b in DRAWN.items()} if renderer == "python" else dict(zip(DRAWN, _gas_batch(core_js, list(DRAWN.values()))))
    res = _run(html, harness=HARNESS)
    assert len(res) == len(DRAWN) * len(WIDTHS)
    bad = {r["id"]: r["errs"] for r in res if r["errs"]}
    assert not bad, json.dumps(bad, indent=1)[:3000]
    assert all(r["tiles"] == html[r["id"].split("-")[0]].count('data-cb="tile"') > 0 for r in res)
