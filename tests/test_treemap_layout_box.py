"""treemap in a real browser: no visible label clipped or overlapping, group headers inside their group, nothing wider than the container.

Renders path charts of depth 2, 3 and 4, a 12-item flat payload with very unequal values and the I31 example (thin cells such as
'BI 700' and 'On-call 300' next to a 'Platform' pill) in 320 / 650 / 1200 / 1400 px containers and a 300 px grid cell, in both
renderers' HTML. A test-only script runs in headless Chromium and writes measurements into the DOM. Same method as
tests/test_histogram_layout_box.py.
"""
from __future__ import annotations

import json

import pytest

from test_histogram_layout_box import CHROME, WIDTHS, _run
from test_motion_atoms import _gas_batch, _py, core_js  # noqa: F401
from test_treemap_path import DEPTH2, DEPTH3, DEPTH4, I31

pytestmark = pytest.mark.skipif(not CHROME, reason="needs chromium")

UNEQUAL12 = {"type": "treemap", "items": [{"category": "ABCD"[i % 4], "name": "Item " + str(i), "value": v} for i, v in
                                          enumerate([1000000, 250000, 90000, 4000, 900, 300, 120, 60, 25, 7, 2, 0.5])]}
LONG = {"type": "treemap", "items": [{"path": ["Documents and settings", "Photographs 2024"][:1 + i % 2], "name": "Holiday album number %d" % i, "value": 3000 // (i + 1)} for i in range(12)]}
PAYLOADS = {"depth2": DEPTH2, "depth3": DEPTH3, "depth4": DEPTH4, "unequal12": UNEQUAL12, "i31": I31, "longnames": LONG}

HARNESS = r'''<script>
window.addEventListener('load', function () {
  var res = [];
  function hit(a, b, g) { return a.left < b.right + g && b.left < a.right + g && a.top < b.bottom + g && b.top < a.bottom + g; }
  function inside(a, b, t) { return a.left >= b.left - t && a.right <= b.right + t && a.top >= b.top - t && a.bottom <= b.bottom + t; }
  function textRect(el) { var r = document.createRange(); r.selectNodeContents(el); return r.getBoundingClientRect(); }
  document.querySelectorAll('.case').forEach(function (c) {
    var errs = [], cs = c.firstElementChild.getBoundingClientRect(), root = c.querySelector('div[style*="height:300px"]'), rr = root.getBoundingClientRect(), i, j;
    if (rr.right > cs.right + 0.5 || rr.left < cs.left - 0.5) errs.push('chart widens its container: ' + rr.width + ' in ' + cs.width);
    if (c.firstElementChild.scrollWidth > c.firstElementChild.clientWidth + 1) errs.push('content is wider than the container');
    var kids = Array.prototype.slice.call(root.children).filter(function (e) { return e.tagName === 'DIV'; });
    var boxes = kids.filter(function (e) { return /background:var\(--surface/.test(e.getAttribute('style')) && !e.textContent; });
    var texts = [], shown = 0;
    kids.forEach(function (e) {
      var st = e.getAttribute('style') || '', lab = e.querySelector('span') || e;
      if (!e.textContent) return;
      if (getComputedStyle(lab).display === 'none' || getComputedStyle(e).display === 'none') return;
      var tr = textRect(lab), er = e.getBoundingClientRect(), isCell = /border:1px solid transparent/.test(st), isHead = /line-height:18px/.test(st);
      if (parseFloat(getComputedStyle(lab).fontSize) < 11.5) errs.push('label font below 12px: ' + e.textContent);
      if (lab.scrollWidth > lab.clientWidth + 1 && getComputedStyle(lab).display !== 'inline') errs.push('label "' + e.textContent + '" is clipped sideways');
      if (isCell && !inside(tr, {left: er.left + 1, right: er.right - 1, top: er.top + 1, bottom: er.bottom - 1}, 0.6)) errs.push('label "' + e.textContent + '" is clipped by its cell');
      if (isHead) {
        if (!inside(tr, er, 0.6)) errs.push('header "' + e.textContent + '" is clipped');
        if (!boxes.some(function (b) { return inside(er, b.getBoundingClientRect(), 0.6); })) errs.push('header "' + e.textContent + '" is not inside a group box');
      }
      if (!isCell && !isHead && tr.right > er.right + 0.6) errs.push('pill "' + e.textContent + '" is clipped');
      texts.push({el: e, r: tr}); shown++;
    });
    for (i = 0; i < texts.length; i++) for (j = i + 1; j < texts.length; j++) if (hit(texts[i].r, texts[j].r, 0)) errs.push('labels overlap: "' + texts[i].el.textContent + '" and "' + texts[j].el.textContent + '"');
    res.push({id: c.id, shown: shown, cells: kids.length, errs: errs});
  });
  document.getElementById('out').textContent = JSON.stringify(res);
});
</script>'''


@pytest.mark.parametrize("renderer", ["python", "gas"])
def test_labels_are_never_clipped_or_overlapping_and_the_chart_never_widens_its_container(renderer, core_js):
    html = {n: _py(b) for n, b in PAYLOADS.items()} if renderer == "python" else dict(zip(PAYLOADS, _gas_batch(core_js, list(PAYLOADS.values()))))
    res = _run(html, harness=HARNESS)
    assert len(res) == len(PAYLOADS) * len(WIDTHS)
    bad = {r["id"]: r["errs"] for r in res if r["errs"]}
    assert not bad, json.dumps(bad, indent=1)[:3500]
    by = {r["id"]: r for r in res}
    # the labels are not all hidden: a wide container shows more of them than a narrow one, and shows most
    for n in PAYLOADS:
        assert by[n + "-w320"]["shown"] <= by[n + "-w1400"]["shown"], n
    assert by["i31-w1400"]["shown"] >= 8 and by["depth3-w1200"]["shown"] >= 6 and by["depth4-w1400"]["shown"] >= 8, {k: v["shown"] for k, v in by.items()}
