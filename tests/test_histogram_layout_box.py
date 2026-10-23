"""histogram in a real browser: no overlapping bars or labels, nothing clipped, never wider than its container.

Renders every payload in 320 / 650 / 1200 / 1400 px containers and in a 300 px cell of a 2-column grid, in both renderers'
HTML. A test-only script runs in headless Chromium and writes measurements into the DOM; the atom's own output carries no script.
Same method as tests/test_org_chart_layout_box.py.
"""
from __future__ import annotations

import html as H
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from test_histogram import PAYLOADS
from test_motion_atoms import _gas_batch, _py, core_js  # noqa: F401

CHROME = shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome")
pytestmark = pytest.mark.skipif(not CHROME, reason="needs chromium")

DRAWN = ["normalish", "skewed", "bimodal", "max_bins", "all_equal", "negatives", "decimals", "tiny", "big", "three_bins", "odd_options"]
WIDTHS = (("w320", 320), ("w650", 650), ("w1200", 1200), ("w1400", 1400), ("cell300", 300))

HARNESS = r'''<script>
window.addEventListener('load', function () {
  var res = [];
  function hit(a, b, g) { return a.left < b.right + g && b.left < a.right + g && a.top < b.bottom + g && b.top < a.bottom + g; }
  document.querySelectorAll('.case').forEach(function (c) {
    var errs = [], root = c.querySelector('.ifhg'), cs = c.firstElementChild.getBoundingClientRect(), rr = root.getBoundingClientRect(), i, j;
    if (rr.right > cs.right + 0.5 || rr.left < cs.left - 0.5) errs.push('chart widens its container: ' + rr.width + ' in ' + cs.width);
    if (root.scrollWidth > root.clientWidth + 1) errs.push('content is wider than the chart box: ' + root.scrollWidth + ' > ' + root.clientWidth);
    var plot = root.querySelector('[role=img]'), pr = plot.getBoundingClientRect();
    var bars = Array.prototype.slice.call(root.querySelectorAll('rect.hgb')).map(function (r) { return r.getBoundingClientRect(); });
    if (!bars.length) errs.push('no bars');
    bars.forEach(function (b, k) {
      if (b.width <= 0.05) errs.push('bar ' + k + ' has no width (' + b.width + ')');
      if (b.left < pr.left - 0.6 || b.right > pr.right + 0.6 || b.top < pr.top - 0.6 || b.bottom > pr.bottom + 0.6) errs.push('bar ' + k + ' outside the plot');
      if (k && b.left < bars[k - 1].right - 0.6) errs.push('bars ' + (k - 1) + ',' + k + ' overlap');
    });
    var xl = Array.prototype.slice.call(root.querySelectorAll('.hgx')).filter(function (e) { return getComputedStyle(e).display !== 'none'; }).map(function (e) { return e.children[1]; });
    var yl = Array.prototype.slice.call(plot.querySelectorAll('div[style*="right:100%"]'));
    var labs = xl.concat(yl), rects = labs.map(function (e) { return e.getBoundingClientRect(); });
    rects.forEach(function (r, k) {
      if (r.left < rr.left - 0.5 || r.right > rr.right + 0.5 || r.top < rr.top - 0.5 || r.bottom > rr.bottom + 0.5) errs.push('label "' + labs[k].textContent + '" is clipped by the chart box');
      if (r.width < 1) errs.push('label "' + labs[k].textContent + '" has no box');
      if (parseFloat(getComputedStyle(labs[k]).fontSize) < 11.5) errs.push('label font below 12px: ' + getComputedStyle(labs[k]).fontSize);
    });
    for (i = 0; i < rects.length; i++) for (j = i + 1; j < rects.length; j++) if (hit(rects[i], rects[j], 2)) errs.push('labels overlap: "' + labs[i].textContent + '" and "' + labs[j].textContent + '"');
    // x labels sit under the plot, y labels left of it
    xl.forEach(function (e) { if (e.getBoundingClientRect().top < pr.bottom) errs.push('x label above the axis'); });
    yl.forEach(function (e) { if (e.getBoundingClientRect().right > pr.left + 0.5) errs.push('y label inside the plot'); });
    var cap = Array.prototype.slice.call(root.children).pop();
    res.push({id: c.id, bars: bars.length, xlabels: xl.length, errs: errs, w: rr.width});
  });
  document.getElementById('out').textContent = JSON.stringify(res);
});
</script>'''


def _run(blocks, extra_css='', harness=None):
    cases = []
    for name, html in blocks.items():
        for label, px in WIDTHS:
            if label == 'cell300':
                cases.append('<div class="case" id="%s-%s"><div style="display:grid;grid-template-columns:300px 1fr;gap:24px;width:1300px"><div>%s</div><div></div></div></div>' % (name, label, html))
            else:
                cases.append('<div class="case" id="%s-%s"><div style="width:%dpx">%s</div></div>' % (name, label, px, html))
    page = '<!doctype html><meta charset="utf-8"><body style="margin:0;font-family:sans-serif">' + extra_css + ''.join(cases) + '<pre id="out"></pre>' + (harness or HARNESS)
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "p.html"
        f.write_text(page)
        prof = tempfile.mkdtemp()
        try:
            out = subprocess.run([CHROME, "--headless=new", "--use-angle=swiftshader", "--no-sandbox", "--user-data-dir=" + prof, "--window-size=1500,900",
                                  "--virtual-time-budget=3000", "--dump-dom", "file://" + str(f)], capture_output=True, text=True, timeout=180).stdout
        finally:
            shutil.rmtree(prof, ignore_errors=True)
    m = re.search(r'<pre id="out">(.*?)</pre>', out, re.S)
    assert m and m.group(1).strip(), out[-500:]
    return json.loads(H.unescape(m.group(1)))


@pytest.mark.parametrize("renderer", ["python", "gas"])
def test_bars_and_labels_never_overlap_or_widen_the_container(renderer, core_js):
    blocks = {n: PAYLOADS[n] for n in DRAWN}
    html = {n: _py(b) for n, b in blocks.items()} if renderer == "python" else dict(zip(blocks, _gas_batch(core_js, list(blocks.values()))))
    res = _run(html)
    assert len(res) == len(DRAWN) * len(WIDTHS)
    bad = {r["id"]: r["errs"] for r in res if r["errs"]}
    assert not bad, json.dumps(bad, indent=1)[:3000]
    by = {r["id"]: r for r in res}
    # the narrow tier shows fewer edge labels than the wide one, and a wide container shows them all
    assert by["normalish-w320"]["xlabels"] < by["normalish-w1200"]["xlabels"]
    # every bar in the markup is laid out. Count from the markup, not by re-binning the raw payload: odd_options asks
    # for bins=1e9, which the renderer clamps to 40 but a bare _hg_bin call would honour (a billion ticks, out of memory).
    assert all(r["bars"] == html[r["id"].split("-")[0]].count('class="hgb') for r in res)


def test_a_leaking_page_stylesheet_does_not_break_the_chart(core_js):
    leak = '<style>div{position:relative}svg{max-width:50%}rect{stroke:red}ul,li{position:relative}</style>'
    res = _run({n: _py(PAYLOADS[n]) for n in ("normalish", "max_bins", "big")}, leak)
    # a hostile stylesheet may change the look but the chart must still stay inside its container
    assert not [r for r in res if any("widens" in e or "wider" in e for e in r["errs"])], res


RIDGE_HARNESS = r'''<script>
window.addEventListener('load', function () {
  var res = [];
  function hit(a, b, g) { return a.left < b.right + g && b.left < a.right + g && a.top < b.bottom + g && b.top < a.bottom + g; }
  document.querySelectorAll('.case').forEach(function (c) {
    var errs = [], root = c.querySelector('.ifhg'), cs = c.firstElementChild.getBoundingClientRect(), rr = root.getBoundingClientRect(), i, j;
    if (rr.right > cs.right + 0.5 || rr.left < cs.left - 0.5) errs.push('chart widens its container: ' + rr.width + ' in ' + cs.width);
    if (root.scrollWidth > root.clientWidth + 1) errs.push('content is wider than the chart box: ' + root.scrollWidth + ' > ' + root.clientWidth);
    var plots = Array.prototype.slice.call(root.querySelectorAll('.hgrp')).map(function (p) { return p.getBoundingClientRect(); });
    var ridges = Array.prototype.slice.call(root.querySelectorAll('path.hgr')).map(function (p) { return p.getBoundingClientRect(); });
    if (!ridges.length || ridges.length !== plots.length) errs.push('ridges ' + ridges.length + ' for ' + plots.length + ' rows');
    ridges.forEach(function (r, k) {
      if (r.width < plots[k].width - 1) errs.push('ridge ' + k + ' narrower than its row');
      if (r.left < plots[k].left - 0.6 || r.right > plots[k].right + 0.6) errs.push('ridge ' + k + ' outside its row');
      if (r.bottom > plots[k].bottom + 0.6) errs.push('ridge ' + k + ' below its baseline');
      if (r.top < rr.top - 0.5) errs.push('ridge ' + k + ' clipped at the top');
      if (plots[k].width < 120) errs.push('row ' + k + ' plot too narrow: ' + plots[k].width);
    });
    var rl = Array.prototype.slice.call(root.querySelectorAll('.hgrl'));
    var xl = Array.prototype.slice.call(root.querySelectorAll('.hgx')).filter(function (e) { return getComputedStyle(e).display !== 'none'; }).map(function (e) { return e.children[1]; });
    var labs = rl.concat(xl), rects = labs.map(function (e) { return e.getBoundingClientRect(); });
    rects.forEach(function (r, k) {
      if (r.left < rr.left - 0.5 || r.right > rr.right + 0.5 || r.top < rr.top - 0.5 || r.bottom > rr.bottom + 0.5) errs.push('label "' + labs[k].textContent + '" is clipped by the chart box');
      if (parseFloat(getComputedStyle(labs[k]).fontSize) < 11.5) errs.push('label font below 12px');
    });
    rl.forEach(function (e, k) { if (rects[k].right > plots[k].left + 0.5) errs.push('row label "' + e.textContent + '" runs into its plot'); if (e.scrollHeight > e.clientHeight + 1 && e.getClientRects().length && e.clientHeight > 46) errs.push('row label taller than its row'); });
    for (i = 0; i < rects.length; i++) for (j = i + 1; j < rects.length; j++) if (hit(rects[i], rects[j], 1)) errs.push('labels overlap: "' + labs[i].textContent + '" and "' + labs[j].textContent + '"');
    xl.forEach(function (e) { if (e.getBoundingClientRect().top < plots[plots.length - 1].bottom) errs.push('x label above the axis'); });
    res.push({id: c.id, ridges: ridges.length, xlabels: xl.length, errs: errs});
  });
  document.getElementById('out').textContent = JSON.stringify(res);
});
</script>'''

RIDGE_DRAWN = ["three", "one", "unequal", "disjoint", "all_equal", "eight", "tiny", "max_bins"]


@pytest.mark.parametrize("renderer", ["python", "gas"])
def test_ridges_and_labels_never_overlap_or_widen_the_container(renderer, core_js):
    from test_histogram_ridge import PAYLOADS as RP
    blocks = {n: RP[n] for n in RIDGE_DRAWN}
    html = {n: _py(b) for n, b in blocks.items()} if renderer == "python" else dict(zip(blocks, _gas_batch(core_js, list(blocks.values()))))
    res = _run(html, harness=RIDGE_HARNESS)
    assert len(res) == len(RIDGE_DRAWN) * len(WIDTHS)
    bad = {r["id"]: r["errs"] for r in res if r["errs"]}
    assert not bad, json.dumps(bad, indent=1)[:3000]
    assert all(r["ridges"] == len(RP[r["id"].split("-")[0]]["series"]) for r in res)
