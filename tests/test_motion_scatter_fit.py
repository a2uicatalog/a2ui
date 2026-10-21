"""motion_scatter fit (backlog I74, 2026-10-21): many cards in a narrow stage must not hide each other's text at p = 1.

A real headless Chromium renders the atom at p = 1 (the default) in stages 320, 650, 760 and 1200 px wide with 4, 8 and 12
{title, text} cards, with and without `origin`, and checks per stage that (1) no two cards' title/text boxes overlap, (2) no card's
box covers another card's text (elementsFromPoint at the middle of every text box finds its own card on top), (3) the text boxes stay
inside the stage. Each is also run with the longest titles and texts the atom keeps (30 and 50 characters). Stage height is 16:9 from 650 up (760 x 428, the size the PM saw) and 420 px at 320 (a phone column). All stages
are measured in one browser run.
"""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import pytest

from test_motion_atoms import CHROMIUM, _py, browser

WIDTHS = [320, 650, 760, 1200]
COUNTS = [4, 8, 12]
TEXTS = ["Review the draft with the team", "Ship the release on Friday", "Archive the old files", "Invite two more people",
         "Plan the next sprint", "Tag every open ticket", "Write the weekly update", "Book the launch room",
         "Check the budget lines", "Send the invoice", "Fix the login bug", "Thank the volunteers"]


LONG = "Quarterly planning workshop %02d with every team"
LONGTEXT = "Bring the numbers, the open questions and a plan"  # 48 characters: close to the 50-character cap


def _block(n, origin, long=False):
    items = ([{"title": (LONG % (i + 1))[:30].strip(), "text": LONGTEXT + "!" * (i % 2)} for i in range(n)] if long
             else [{"title": "Task " + str(i + 1), "text": TEXTS[i]} for i in range(n)])
    b = {"type": "motion_scatter", "items": items}
    if origin:
        b["origin"] = "center"
    return b


def _height(w):
    return 420 if w == 320 else round(w * 9 / 16)


JS = """
// a text box as its true rotated quad: the offset box inside the card, turned by the card's transform about the card's centre
function quad(card, el, wr){
  var M = new DOMMatrix(getComputedStyle(card).transform), ox = card.offsetWidth / 2, oy = card.offsetHeight / 2;
  var xs = [el.offsetLeft, el.offsetLeft + el.offsetWidth], ys = [el.offsetTop, el.offsetTop + el.offsetHeight], q = [];
  [[0, 0], [1, 0], [1, 1], [0, 1]].forEach(function(c){
    var p = M.transformPoint(new DOMPoint(xs[c[0]] - ox, ys[c[1]] - oy));
    q.push([p.x + ox + card.offsetLeft + wr.left, p.y + oy + card.offsetTop + wr.top]);
  });
  return q;
}
function proj(q, ax){ var d = q.map(function(p){ return p[0] * ax[0] + p[1] * ax[1]; }); return [Math.min.apply(null, d), Math.max.apply(null, d)]; }
function overlap(a, b){  // separating-axis test on two convex quads, 0.5 px tolerance
  var qs = [a, b];
  for (var k = 0; k < 2; k++) for (var i = 0; i < 4; i++) {
    var p = qs[k][i], n = qs[k][(i + 1) % 4], ax = [n[1] - p[1], p[0] - n[0]], l = Math.hypot(ax[0], ax[1]); ax = [ax[0] / l, ax[1] / l];
    var pa = proj(a, ax), pb = proj(b, ax);
    if (pa[1] <= pb[0] + 0.5 || pb[1] <= pa[0] + 0.5) return false;
  }
  return true;
}
var res = {};
document.querySelectorAll('[data-stage]').forEach(function(st){
  var sr = st.getBoundingClientRect(), wrap = st.firstElementChild, wr = wrap.getBoundingClientRect(), cards = Array.prototype.filter.call(wrap.children, function(e){ return e.tagName === 'DIV'; }), bad = [];
  var tx = cards.map(function(c){ return Array.prototype.map.call(c.children, function(e){ return quad(c, e, wr); }); });
  for (var i = 0; i < cards.length; i++) {
    for (var j = i + 1; j < cards.length; j++) tx[i].forEach(function(a){ tx[j].forEach(function(b){ if (overlap(a, b)) bad.push('text ' + i + '/' + j); }); });
    tx[i].forEach(function(q){
      var cx = (q[0][0] + q[2][0]) / 2, cy = (q[0][1] + q[2][1]) / 2, top = document.elementsFromPoint(cx, cy).find(function(e){ return cards.some(function(c){ return c.contains(e); }); });
      if (top && !cards[i].contains(top)) bad.push('covered ' + i);
      if (q.some(function(p){ return p[0] < sr.left - 1 || p[0] > sr.right + 1 || p[1] < sr.top - 1 || p[1] > sr.bottom + 1; })) bad.push('outside ' + i);
    });
  }
  res[st.getAttribute('data-stage')] = bad;
});
document.documentElement.setAttribute('data-probe', JSON.stringify(res));
"""


def _measure():
    stages, keys = "", []
    for w in WIDTHS:
        for n in COUNTS:
            for o in (False, True):
                for lg in (False, True):
                    k = f"{w}x{n}{'o' if o else ''}{'L' if lg else ''}"
                    keys.append(k)
                    stages += f'<div data-stage="{k}" style="position:relative;width:{w}px;height:{_height(w)}px;margin:0 0 40px;background:#223;">{_py(_block(n, o, lg))}</div>'
    html = "<!doctype html><meta charset=utf-8><body style='margin:0'>" + stages + "<script>" + JS + "</script>"
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "p.html"
        f.write_text(html)
        out = subprocess.run([CHROMIUM, "--headless=new", "--password-store=basic", "--no-sandbox", "--disable-gpu", "--window-size=1300,900", "--virtual-time-budget=1500",
                              "--dump-dom", f"file://{f}"], capture_output=True, text=True, timeout=120).stdout
    import html as _h
    import re
    m = re.search(r"data-probe='([^']*)'|data-probe=\"([^\"]*)\"", out)
    assert m, out[:400]
    return json.loads(_h.unescape(m.group(1) or m.group(2))), keys


@browser
def test_scatter_cards_never_overlap_at_p1_in_any_stage_size():
    res, keys = _measure()
    bad = {k: sorted(set(res[k]))[:6] for k in keys if res[k]}
    assert not bad, bad


# ─── the contract: Python == GAS, small payloads untouched, hostile input still inert ────────────────────────────────────────────
from test_motion_atoms import _gas_batch, _norm, core_js  # noqa: E402,F401  (core_js is a fixture)

BASE = {"type": "motion_scatter", "items": ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M"]}
CASES = [_block(n, o, lg) for n in (1, 2, 3, 4, 5, 6, 7, 8, 12) for o in (False, True) for lg in (False, True)] + [
    dict(BASE), dict(BASE, origin={"x": 20, "y": 80}, card_w=18, size=12), dict(BASE, items=BASE["items"][:2], origin="center"),
    {"type": "motion_scatter", "items": ["<img src=x onerror=alert(1)>", {"title": "a & b", "text": "</style><b>"}, "x"], "origin": "center"},
]


def test_scatter_fit_python_matches_gas_exactly(core_js):
    got = _gas_batch(core_js, CASES)
    bad = [str(b)[:90] for b, g in zip(CASES, got) if _norm(_py(b)) != _norm(g)]
    assert not bad, bad


def test_scatter_with_one_or_two_cards_is_byte_for_byte_the_old_markup():
    import subprocess as sp
    old = sp.run(["git", "-C", str(Path(__file__).resolve().parent.parent), "show", "origin/main:renderers/web_article.py"], capture_output=True, text=True).stdout
    if "def _render_motion_scatter" not in old:
        pytest.skip("origin/main not available")
    import types
    mod = types.ModuleType("wa_old")
    mod.__file__ = str(Path(__file__).resolve().parent.parent / "renderers" / "web_article.py")
    exec(compile(old, "wa_old.py", "exec"), mod.__dict__)
    mod._mo_install()
    for b in (dict(BASE, items=["A"]), dict(BASE, items=["A", "B"]), dict(BASE, items=["A", "B"], origin="center"), _block(2, False, True), _block(2, True, True), {"type": "motion_scatter"}):
        assert _py(b) == mod._RENDERERS["motion_scatter"](dict(b)), b


def test_scatter_fit_is_a_scoped_stylesheet_and_adds_no_script_or_hostile_markup():
    h = _py(CASES[-1])
    assert "container-type:size" in h and "@container" in h and "<script" not in h.lower() and "<img" not in h and "&lt;/style&gt;" in h
    assert h.count("<style>") == 1 and "Infinity" not in h and "NaN" not in h and "undefined" not in h
    big = _py(dict(BASE, origin="center"))
    assert "mosf12d" in big and "var(--x," in big and "var(--r," in big
    assert "mosf6d" not in _py(dict(BASE, items=BASE["items"][:6])) and "mosf6" in _py(dict(BASE, items=BASE["items"][:6]))


def test_scatter_old_slots_stay_for_a_wide_stage_with_up_to_8_cards_and_no_origin():
    h = _py(dict(BASE, items=BASE["items"][:5]))
    assert "@container (width>=900px) and (width<1100px)" in h and "(width>=1100px)" not in h
    assert "@container (width>=900px){" in _py(dict(BASE, origin="center"))
