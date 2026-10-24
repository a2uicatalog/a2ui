"""image_plot in a real browser: ticks are >= 12px text, never overlap or leave the block, the picture is never wider than its container.
Same method and widths as tests/test_histogram_layout_box.py."""
from __future__ import annotations

import json

import pytest

from test_histogram_layout_box import CHROME, WIDTHS, _run
from test_image_plot import PAYLOADS
from test_motion_atoms import _gas_batch, _py, core_js  # noqa: F401

pytestmark = pytest.mark.skipif(not CHROME, reason="needs chromium")

DRAWN = ["matrix", "matrix_plain", "data_uri", "holes", "big", "version"]
EXTRA = {"wide": {"type": "image_plot", "z": [["#%02x%02x%02x" % (i * 3, j * 4, 90) for j in range(64)] for i in range(3)], "x_range": [-1000000, 1000000], "y_range": [0.001, 0.009], "x_label": "x", "y_label": "y"},
         "tall": {"type": "image_plot", "z": [["#%02x%02x%02x" % (i * 4, 40, 90)] for i in range(64)], "y_range": [100, 0]},
         "one": {"type": "image_plot", "z": [["#336699"]], "x_range": [0, 1], "y_range": [0, 1]}}

HARNESS = r'''<script>
window.addEventListener('load', function () {
  var res = [];
  function hit(a, b) { return a.left < b.right + 1 && b.left < a.right + 1 && a.top < b.bottom + 1 && b.top < a.bottom + 1; }
  document.querySelectorAll('.case').forEach(function (c) {
    var errs = [], root = c.querySelector('.ifip'), cs = c.firstElementChild.getBoundingClientRect(), rr = root.getBoundingClientRect();
    if (rr.right > cs.right + 0.5 || rr.left < cs.left - 0.5) errs.push('block widens its container: ' + rr.width + ' in ' + cs.width);
    if (root.scrollWidth > root.clientWidth + 1) errs.push('content is wider than the block: ' + root.scrollWidth + ' > ' + root.clientWidth);
    var plot = root.querySelector('[role=img]'), pr = plot.getBoundingClientRect();
    if (pr.width < 20 || pr.height < 1) errs.push('picture has no size: ' + pr.width + 'x' + pr.height);
    var svg = plot.querySelector('svg');
    if (svg && svg.getBoundingClientRect().height > 40) { var ar = svg.viewBox.baseVal; if (Math.abs(svg.getBoundingClientRect().width / svg.getBoundingClientRect().height - ar.width / ar.height) > 0.02) errs.push('picture aspect is off'); }
    var spans = Array.prototype.slice.call(root.querySelectorAll('span[style*="position:absolute"]'));
    var rects = spans.map(function (e) { return e.getBoundingClientRect(); });
    spans.forEach(function (e, k) {
      var r = rects[k];
      if (parseFloat(getComputedStyle(e).fontSize) < 11.5) errs.push('tick font below 12px: ' + e.textContent);
      if (r.left < rr.left - 0.5 || r.right > rr.right + 0.5) errs.push('tick "' + e.textContent + '" leaves the block');
      var vertical = e.style.right === '0px';
      if (vertical && r.right > pr.left + 0.5) errs.push('y tick inside the picture: ' + e.textContent);
      if (!vertical && r.top < pr.bottom - 0.5) errs.push('x tick above the picture bottom: ' + e.textContent);
    });
    for (var i = 0; i < rects.length; i++) for (var j = i + 1; j < rects.length; j++) if (hit(rects[i], rects[j])) errs.push('ticks overlap: ' + spans[i].textContent + ' / ' + spans[j].textContent);
    res.push({id: c.id, ticks: spans.length, errs: errs, w: rr.width});
  });
  document.getElementById('out').textContent = JSON.stringify(res);
});
</script>'''


@pytest.mark.parametrize("renderer", ["python", "gas"])
def test_ticks_and_picture_fit_at_every_width(renderer, core_js):
    blocks = {**{n: PAYLOADS[n] for n in DRAWN}, **EXTRA}
    html = {n: _py(dict(b)) for n, b in blocks.items()} if renderer == "python" else dict(zip(blocks, _gas_batch(core_js, list(blocks.values()))))
    res = _run(html, harness=HARNESS)
    assert len(res) == len(blocks) * len(WIDTHS)
    bad = {r["id"]: r["errs"] for r in res if r["errs"]}
    assert not bad, json.dumps(bad, indent=1)[:3000]
    assert any(r["ticks"] > 0 for r in res)
