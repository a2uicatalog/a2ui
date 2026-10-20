"""org_chart in a real browser: boxes and connectors must share one containing block at any width.

Renders the chart inside 320 / 600 / 1200 px containers and a 2-column grid, with and without a leaking
stylesheet (the previous org_chart CSS used `.ifoc ul/li{position:relative}`, which made every list element a
containing block for the absolutely positioned boxes when both charts were on one page, collapsing the boxes
into a cluster while the SVG connectors still spread over the whole chart). Test-only script runs in headless
Chromium and writes measurements into the DOM; the atom's own output carries no script.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from test_motion_atoms import _gas_batch, _py, core_js  # noqa: F401
from test_org_chart_tree import GOLDEN, _payload  # noqa: F401

CHROME = shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome")
pytestmark = pytest.mark.skipif(not CHROME, reason="needs chromium")


def _tree(title, spec):
    nodes = []
    for nid, label, par in spec:
        nodes.append({"id": nid, "label": label, "parent_id": par})
    return {"type": "org_chart", "title": title, "nodes": nodes}


PAYLOADS = {
    "leadership": _tree("Leadership", [("ceo", "CEO", ""), ("e", "VP Engineering", "ceo"), ("p", "Platform lead", "e"), ("m", "ML lead", "e"), ("s", "VP Sales", "ceo"),
                                       ("a", "Account executives", "s"), ("se", "Solutions engineers", "s"), ("o", "VP Operations", "ceo"), ("f", "Facilities", "o"), ("c", "CFO", "ceo")]),
    "unbalanced": _tree("Unbalanced", [("p", "Programme", ""), ("a", "Workstream A", "p"), ("d", "Discovery", "a"), ("b", "Build", "a"), ("l", "Launch", "a"), ("w", "Workstream B", "p"), ("m", "Migration", "w")]),
    "small": _tree("Small", [("h", "Head of design", ""), ("pd", "Product design", "h"), ("br", "Brand", "h")]),
    "golden_full_cap_10": _payload(GOLDEN["full_cap_10"], False),
    "tree20": _payload(GOLDEN["tree20"], False),
    "tree30": _payload(GOLDEN["tree30_max"], False),
}

LEAK = ('<style>.ifoc ul{display:flex;justify-content:center;margin:0;padding:20px 0 0;list-style:none;position:relative}.ifoc li{position:relative;padding:20px 6px 0;text-align:center}'
        'ul,li{position:relative}</style>')

HARNESS = r'''<script>
window.addEventListener('load', function () {
  var res = [];
  document.querySelectorAll('.case').forEach(function (c) {
    var root = c.querySelector('.ifoct'), errs = [], i, j;
    var charts = Array.prototype.slice.call(root.children).filter(function (e) { return e.tagName === 'DIV'; });
    var shown = charts.filter(function (e) { return getComputedStyle(e).display !== 'none'; });
    if (shown.length !== 1) errs.push('visible layouts: ' + shown.length);
    var chart = shown[0] || charts[0], mode = chart.className === 'ocl' ? 'ltr' : 'td';
    charts.forEach(function (e) { if (e !== chart && e.getBoundingClientRect().width !== 0) errs.push('a hidden layout still has a box'); });
    var cr = chart.getBoundingClientRect(), vis = root.getBoundingClientRect(), cs = c.getBoundingClientRect();
    var nodes = Array.prototype.slice.call(chart.querySelectorAll('div[style*="line-height:1.25"]'));
    var boxes = nodes.map(function (d) { return d.getBoundingClientRect(); });
    nodes.forEach(function (d, k) { if (d.scrollHeight > d.clientHeight + 1 || d.scrollWidth > d.clientWidth + 1) errs.push('label ' + k + ' is clipped'); });
    if (vis.right > cs.right + 1 || (c.id.indexOf('grid') > 0 && vis.width > 660)) errs.push('chart widens its container: ' + vis.width);
    for (i = 0; i < boxes.length; i++) for (j = i + 1; j < boxes.length; j++) {
      var a = boxes[i], b = boxes[j];
      if (a.left < b.right - 0.5 && b.left < a.right - 0.5 && a.top < b.bottom - 0.5 && b.top < a.bottom - 0.5) errs.push('overlap ' + i + ',' + j);
    }
    boxes.forEach(function (b, k) { if (b.left < cr.left - 1 || b.right > cr.right + 1 || b.top < cr.top - 1 || b.bottom > cr.bottom + 1) errs.push('box ' + k + ' outside chart'); });
    var svg = chart.querySelector('svg'), m = svg.getScreenCTM();
    svg.querySelectorAll('path').forEach(function (p, k) {
      var L = p.getTotalLength();
      [0, L].forEach(function (t, e) {
        var pt = p.getPointAtLength(t), x = pt.x * m.a + m.e, y = pt.y * m.d + m.f;
        if (x < cr.left - 1.5 || x > cr.right + 1.5 || y < cr.top - 1.5 || y > cr.bottom + 1.5) errs.push('connector ' + k + ' end ' + e + ' outside chart');
        var ok = boxes.some(function (b) {
          if (mode === 'td') return Math.abs(x - (b.left + b.right) / 2) < 1.5 && (Math.abs(y - b.top) < 1.5 || Math.abs(y - b.bottom) < 1.5);
          return Math.abs(y - (b.top + b.bottom) / 2) < 1.5 && (Math.abs(x - b.left) < 1.5 || Math.abs(x - b.right) < 1.5);
        });
        if (!ok) errs.push('connector ' + k + ' end ' + e + ' not on a box edge');
      });
    });
    var fits = root.scrollWidth <= root.clientWidth, inner = chart.getBoundingClientRect();
    if (fits && Math.abs((inner.left + inner.right) / 2 - (vis.left + vis.right) / 2) > 1.5) errs.push('not centred');
    // the root box (first in document order) is fully visible at scrollLeft 0
    root.scrollLeft = 0;
    var r0 = boxes[0], rootVisible = r0 && r0.left >= vis.left - 0.5 && r0.right <= vis.right + 0.5;
    res.push({id: c.id, n: boxes.length, errs: errs, fits: fits, mode: mode, rootVisible: !!rootVisible});
  });
  document.getElementById('out').textContent = JSON.stringify(res);
});
</script>'''

WIDTHS = (("w320", 320), ("w600", 600), ("w650", 650), ("w1200", 1200), ("w1400", 1400), ("w2400", 2400))


def _run(html_blocks, leak, print_sim=False):
    cases = []
    for name, html in html_blocks.items():
        for label, px in WIDTHS:
            cases.append('<div class="case" id="%s-%s"><div style="width:%dpx">%s</div></div>' % (name, label, px, html))
        cases.append('<div class="case" id="%s-grid"><div style="display:grid;grid-template-columns:1fr 1fr;gap:24px;width:1300px"><div>%s</div><div></div></div></div>' % (name, html))
    page = '<!doctype html><meta charset="utf-8"><body style="margin:0">' + (LEAK if leak else '') + ''.join(cases) + '<pre id="out"></pre>' + HARNESS
    if print_sim:
        page = page.replace("@media print", "@media all")       # emulates print: Chromium cannot be switched to print media from a dumped DOM
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "p.html"
        f.write_text(page)
        prof = tempfile.mkdtemp()
        try:
            out = subprocess.run([CHROME, "--headless=new", "--use-angle=swiftshader", "--no-sandbox", "--user-data-dir=" + prof, "--window-size=2600,900",
                                  "--virtual-time-budget=3000", "--dump-dom", "file://" + str(f)], capture_output=True, text=True, timeout=120).stdout
        finally:
            shutil.rmtree(prof, ignore_errors=True)
    import re
    m = re.search(r'<pre id="out">(.*?)</pre>', out, re.S)
    assert m and m.group(1).strip(), out[-500:]
    import html as H
    return json.loads(H.unescape(m.group(1)))


@pytest.mark.parametrize("leak", [False, True], ids=["clean", "leaking-stylesheet"])
def test_boxes_and_connectors_share_a_containing_block_at_every_width(leak, core_js):
    blocks = {n: _py(p) for n, p in PAYLOADS.items()}
    blocks.update({n + "_gas": _gas_batch(core_js, [p])[0] for n, p in PAYLOADS.items() if n in ("leadership", "golden_full_cap_10", "tree20", "tree30")})
    res = _run(blocks, leak)
    assert len(res) == len(blocks) * (len(WIDTHS) + 1)
    bad = [(r["id"], r["errs"][:3]) for r in res if r["errs"] or not r["n"]]
    assert not bad, bad


def test_ten_node_trees_stay_top_down_and_fit_a_650px_column(core_js):
    blocks = {n: _py(PAYLOADS[n]) for n in ("leadership", "unbalanced", "small")}
    blocks.update({"leadership_gas": _gas_batch(core_js, [PAYLOADS["leadership"]])[0]})
    res = {r["id"]: r for r in _run(blocks, False)}
    for n in blocks:
        for w in ("w650", "w1200"):
            assert res[n + "-" + w]["fits"] and res[n + "-" + w]["mode"] == "td", (n, w)


def test_wide_trees_go_left_to_right_in_a_narrow_column_and_top_down_when_there_is_room(core_js):
    blocks = {"tree20": _py(PAYLOADS["tree20"]), "tree30": _py(PAYLOADS["tree30"]), "tree20_gas": _gas_batch(core_js, [PAYLOADS["tree20"]])[0]}
    res = {r["id"]: r for r in _run(blocks, False)}
    for n in blocks:
        for w in ("w320", "w650"):
            r = res[n + "-" + w]
            assert r["mode"] == "ltr" and r["rootVisible"], (n, w)
        r = res[n + "-w650"]
        assert r["fits"], n                                     # no horizontal scroll at 650
    for n in ("tree20", "tree20_gas"):
        assert res[n + "-w1400"]["mode"] == "td" and res[n + "-w1400"]["fits"] and res[n + "-w1400"]["rootVisible"], n
        assert res[n + "-w1200"]["mode"] == "ltr"               # 1274 px is needed top-down
    assert res["tree30-w1400"]["mode"] == "ltr" and res["tree30-w2400"]["mode"] == "td" and res["tree30-w2400"]["fits"]


def test_print_always_shows_the_top_down_layout(core_js):
    # print media is emulated by rewriting the @media print rule to @media all (the rule text itself is asserted in test_org_chart_tree)
    res = {r["id"]: r for r in _run({"tree20": _py(PAYLOADS["tree20"]), "tree30": _py(PAYLOADS["tree30"])}, False, print_sim=True)}
    for n in ("tree20", "tree30"):
        for w in ("w320", "w650", "w1400"):
            assert res[n + "-" + w]["mode"] == "td" and not res[n + "-" + w]["errs"], (n, w)
