"""geo_map in a real browser: never wider than its container, every drawn marker inside the map, legend entries and notes readable (>= 12px) and not overlapping,
at 320 / 650 / 1200 / 1400 px and in a 300 px grid cell. Same method as tests/test_histogram_layout_box.py (a test-only script writes measurements into the DOM)."""
from __future__ import annotations

import json

import pytest

from test_geo_map import EU, GOOD, US, WORLD
from test_histogram_layout_box import CHROME, WIDTHS, _run
from test_motion_atoms import _gas_batch, _py, core_js  # noqa: F401

pytestmark = pytest.mark.skipif(not CHROME, reason="needs chromium")

DRAWN = {"world": WORLD, "us": US, "eu": EU, "one_point": GOOD[3], "antimeridian": GOOD[4], "many_groups": GOOD[6], "skipped": GOOD[7]}

HARNESS = r'''<script>
window.addEventListener('load', function () {
  var res = [];
  function hit(a, b, g) { return a.left < b.right + g && b.left < a.right + g && a.top < b.bottom + g && b.top < a.bottom + g; }
  document.querySelectorAll('.case').forEach(function (c) {
    var errs = [], root = c.querySelector('[data-cb-root]'), cs = c.firstElementChild.getBoundingClientRect(), rr = root.getBoundingClientRect(), i, j;
    if (rr.right > cs.right + 0.5 || rr.left < cs.left - 0.5) errs.push('map widens its container: ' + rr.width + ' in ' + cs.width);
    if (root.scrollWidth > root.clientWidth + 1) errs.push('content is wider than the box: ' + root.scrollWidth + ' > ' + root.clientWidth);
    var svg = root.querySelector('svg[role=img]'), sr = svg.getBoundingClientRect();
    if (sr.width < 100) errs.push('map too narrow: ' + sr.width);
    var nodes = Array.prototype.slice.call(svg.querySelectorAll('[data-shape]'));
    nodes.forEach(function (n, k) {
      var r = n.getBoundingClientRect();
      if (r.width <= 0 || r.height <= 0) errs.push('marker ' + k + ' has no size');
      if (r.left < sr.left - 0.6 || r.right > sr.right + 0.6 || r.top < sr.top - 0.6 || r.bottom > sr.bottom + 0.6) errs.push('marker ' + k + ' outside the map');
    });
    var lis = Array.prototype.slice.call(root.querySelectorAll('li')), rects = lis.map(function (e) { return e.getBoundingClientRect(); });
    rects.forEach(function (r, k) {
      if (r.right > rr.right + 0.5 || r.left < rr.left - 0.5) errs.push('legend entry "' + lis[k].textContent + '" is clipped');
      if (parseFloat(getComputedStyle(lis[k].querySelector('span:last-child')).fontSize) < 11.5) errs.push('legend font below 12px');
    });
    for (i = 0; i < rects.length; i++) for (j = i + 1; j < rects.length; j++) if (hit(rects[i], rects[j], 0)) errs.push('legend entries overlap: "' + lis[i].textContent + '" and "' + lis[j].textContent + '"');
    Array.prototype.slice.call(root.querySelectorAll('p')).forEach(function (p) { if (parseFloat(getComputedStyle(p).fontSize) < 11.5) errs.push('note font below 12px'); });
    res.push({id: c.id, nodes: nodes.length, lis: lis.length, errs: errs});
  });
  document.getElementById('out').textContent = JSON.stringify(res);
});
</script>'''


@pytest.mark.parametrize("renderer", ["python", "gas"])
def test_map_markers_and_legend_stay_inside_at_every_width(renderer, core_js):
    html = {n: _py(b) for n, b in DRAWN.items()} if renderer == "python" else dict(zip(DRAWN, _gas_batch(core_js, list(DRAWN.values()))))
    res = _run(html, harness=HARNESS)
    assert len(res) == len(DRAWN) * len(WIDTHS)
    bad = {r["id"]: r["errs"] for r in res if r["errs"]}
    assert not bad, json.dumps(bad, indent=1)[:3000]
    by = {r["id"]: r for r in res}
    assert by["world-w320"]["nodes"] == 8 and by["us-w650"]["nodes"] == 3
    assert all(r["nodes"] == html[r["id"].split("-")[0]].count("data-shape=") for r in res)


DRAW_HARNESS = r'''<script>
window.addEventListener('load', function () {
  var res = [];
  document.querySelectorAll('.case').forEach(function (c) {
    var root = c.querySelector('[data-cb-root]'), m = c.id.split('-')[1], offs = [];
    if (m !== 'none') root.style.setProperty('--p', m);
    root.querySelectorAll('mask path').forEach(function (p) { offs.push(parseFloat(getComputedStyle(p).strokeDashoffset)); });
    res.push({id: c.id, offs: offs, errs: []});
  });
  document.getElementById('out').textContent = JSON.stringify(res);
});
</script>'''


@pytest.mark.parametrize("renderer", ["python", "gas"])
def test_route_draws_on_leg_by_leg_with_p_and_is_complete_without_it(renderer, core_js):
    trip = {"type": "geo_map", "region_set": "europe-countries", "lines": [{"path": [dict(lat=38.7, lon=-9.1), dict(lat=40.4, lon=-3.7), dict(lat=48.85, lon=2.35)]}]}
    h = _py(trip) if renderer == "python" else _gas_batch(core_js, [trip])[0]
    # the harness reads the case id as name-<p>: one page per p
    out = {}
    import test_histogram_layout_box as hb
    for p in ("none", "0", "0.1", "1"):
        old = hb.WIDTHS
        try:
            hb.WIDTHS = (("w650", 650),)
            res = _run({"x" + p.replace(".", "_"): h}, harness=DRAW_HARNESS.replace("c.id.split('-')[1]", "'" + p + "'"))
        finally:
            hb.WIDTHS = old
        out[p] = res[0]["offs"]
    assert out["none"] == [0.0, 0.0] and out["1"] == [0.0, 0.0]            # settled: no wrapper, and p at the end
    assert out["0"] == [1.0, 1.0]                                           # nothing drawn at the start
    assert 0 < out["0.1"][0] < 1 and out["0.1"][1] == 1.0                   # at p 0.1 the first leg is part-drawn and the second has not begun
