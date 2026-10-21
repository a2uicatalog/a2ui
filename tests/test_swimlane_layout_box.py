"""swimlane with links / layout auto in a real browser: no card overlaps another, no connector passes through a card, no label chip sits on a card or on
another chip, no text is clipped, and the diagram is never wider than its container (at 320 / 650 / 1200 / 1400 px and in a 300 px grid cell it scrolls
sideways inside its own box, as org_chart does). Same method as tests/test_histogram_layout_box.py."""
from __future__ import annotations

import json

import pytest

from test_histogram_layout_box import CHROME, WIDTHS, _run
from test_motion_atoms import _gas_batch, _py, core_js  # noqa: F401
from test_swimlane_links import LINKED, RANDOM

pytestmark = pytest.mark.skipif(not CHROME, reason="needs chromium")

_ALL = {**LINKED, **RANDOM}
DRAWN = {k: _ALL[k] for k in list(LINKED) + [r for r in RANDOM if 'class="swc"' in _py(RANDOM[r])][:30]}

HARNESS = r'''<script>
window.addEventListener('load', function () {
  var res = [];
  function hit(a, b, g) { return a.left < b.right + g && b.left < a.right + g && a.top < b.bottom + g && b.top < a.bottom + g; }
  document.querySelectorAll('.case').forEach(function (c) {
    var errs = [], root = c.querySelector('.ifsw'), box = root.parentElement.parentElement.getBoundingClientRect(), rr = root.getBoundingClientRect(), i, j;
    var cv = root.querySelector('.swv'), cr = cv.getBoundingClientRect();
    if (rr.right > box.right + 0.5 || rr.left < box.left - 0.5) errs.push('scroller widens its container: ' + rr.width + ' in ' + box.width);
    var cards = Array.prototype.slice.call(root.querySelectorAll('.swc')), chips = Array.prototype.slice.call(root.querySelectorAll('.swl'));
    var cardR = cards.map(function (e) { return e.getBoundingClientRect(); }), chipR = chips.map(function (e) { return e.getBoundingClientRect(); });
    cardR.forEach(function (r, k) {
      if (r.left < cr.left - 0.5 || r.right > cr.right + 0.5 || r.top < cr.top - 0.5 || r.bottom > cr.bottom + 0.5) errs.push('card ' + (k + 1) + ' outside the canvas');
      if (cards[k].scrollHeight > cards[k].clientHeight + 1 || cards[k].scrollWidth > cards[k].clientWidth + 1) errs.push('card text clipped: ' + cards[k].textContent);
      var fs = parseFloat(getComputedStyle(cards[k]).fontSize);
      if (fs < 11.5) errs.push('card font below 12px');
      for (j = 0; j < k; j++) if (hit(cardR[j], r, 0)) errs.push('cards ' + (j + 1) + ' and ' + (k + 1) + ' overlap');
    });
    chipR.forEach(function (r, k) {
      if (chips[k].scrollWidth > chips[k].clientWidth + 1) errs.push('label clipped: ' + chips[k].textContent);
      if (parseFloat(getComputedStyle(chips[k]).fontSize) < 11.5) errs.push('label font below 12px');
      if (r.left < cr.left - 0.5 || r.right > cr.right + 0.5 || r.top < cr.top - 0.5 || r.bottom > cr.bottom + 0.5) errs.push('label outside the canvas: ' + chips[k].textContent);
      cardR.forEach(function (q, m) { if (hit(q, r, 0)) errs.push('label "' + chips[k].textContent + '" over card ' + (m + 1)); });
      for (j = 0; j < k; j++) if (hit(chipR[j], r, 1)) errs.push('labels overlap: "' + chips[j].textContent + '" and "' + chips[k].textContent + '"');
    });
    root.querySelectorAll('.swn').forEach(function (e) { if (e.scrollHeight > e.clientHeight + 1 || e.scrollWidth > e.clientWidth + 1) errs.push('lane name clipped: ' + e.textContent); });
    root.querySelectorAll('.swh').forEach(function (e) { if (e.scrollHeight > e.clientHeight + 1) errs.push('column name clipped: ' + e.textContent); });
    var paths = Array.prototype.slice.call(root.querySelectorAll('path.swp'));
    paths.forEach(function (p) {
      var toks = p.getAttribute('d').match(/[MHV]-?\d+( -?\d+)?/g), x = 0, y = 0, pts = [];
      toks.forEach(function (t) {
        var v = t.slice(1).split(' ').map(Number);
        if (t[0] === 'M') { x = v[0]; y = v[1]; } else if (t[0] === 'H') x = v[0]; else y = v[0];
        pts.push([x + cr.left, y + cr.top]);
      });
      for (i = 1; i < pts.length; i++) {
        var a = pts[i - 1], b = pts[i], lo = [Math.min(a[0], b[0]), Math.min(a[1], b[1])], hi = [Math.max(a[0], b[0]), Math.max(a[1], b[1])];
        cardR.forEach(function (q, m) { if (lo[0] < q.right - 0.5 && hi[0] > q.left + 0.5 && lo[1] < q.bottom - 0.5 && hi[1] > q.top + 0.5) errs.push('link ' + p.getAttribute('data-f') + '->' + p.getAttribute('data-t') + ' crosses card ' + (m + 1)); });
      }
    });
    res.push({id: c.id, cards: cards.length, chips: chips.length, paths: paths.length, scrolls: root.scrollWidth > root.clientWidth + 1, errs: errs, w: rr.width});
  });
  document.getElementById('out').textContent = JSON.stringify(res);
});
</script>'''


@pytest.mark.parametrize("renderer", ["python", "gas"])
def test_cards_connectors_and_labels_never_collide_or_widen_the_container(renderer, core_js):
    html = {n: _py(b) for n, b in DRAWN.items()} if renderer == "python" else dict(zip(DRAWN, _gas_batch(core_js, list(DRAWN.values()))))
    res = _run(html, harness=HARNESS)
    assert len(res) == len(DRAWN) * len(WIDTHS)
    bad = {r["id"]: r["errs"] for r in res if r["errs"]}
    assert not bad, json.dumps(dict(list(bad.items())[:6]), indent=1)[:3500]
    by = {r["id"]: r for r in res}
    assert all(r["paths"] == html[r["id"].rsplit("-", 1)[0]].count('class="swp"') and r["cards"] == html[r["id"].rsplit("-", 1)[0]].count('class="swc"') for r in res)
    import re
    for name in ("arch", "nine", "grid"):
        cw = int(re.search(r'class="swv" style="position:relative;width:(\d+)px', html[name])[1])
        for w, px in WIDTHS:
            assert by[name + "-" + w]["scrolls"] == (cw > px), (name, w, cw)                  # it scrolls inside its own box exactly when it is wider than the container
            assert by[name + "-" + w]["w"] <= px
    assert by["arch-w320"]["scrolls"] and by["arch-cell300"]["scrolls"]
