"""motion_build (2026-10-21, decision D9): the generic wrapper that draws any D3 chart atom's server-side SVG on the film's --p dial.

Same layers as test_motion_candidates.py: GAS and Python twins agree byte for byte, hostile input never becomes markup, a child
that emits no build contract passes through untouched, and a real browser shows the dash / scale / opacity values moving with --p.
The contract the wrapper reads is pm/evidence/2026-10-21-build-contract.md (data-cb kinds, --k, --n, pathLength=1, .cb-fade).
"""
from __future__ import annotations

import html as _h
import json
import re
import subprocess
import tempfile
from pathlib import Path

import pytest

import renderers.web_article as wa
from test_motion_atoms import CHROMIUM, _gas_batch, _norm, _py, browser, core_js  # noqa: F401

PANEL = {"type": "demo_panel", "title": "Card", "rows": [["a", "1"]]}
PILL = {"type": "motion_pill", "text": "Go"}
ATT = '"><img src=x onerror=alert(1)><script>alert(2)</script>'

CASES = [
    {"type": "motion_build", "blocks": [PANEL]},
    {"type": "motion_build", "blocks": [PANEL, PILL], "order": "together", "from": "center", "span": 2, "ink_last": False},
    {"type": "motion_build", "blocks": [PILL], "order": "by-kind", "from": "origin", "span": 8},
    {"type": "motion_build", "blocks": [PILL], "order": "stagger", "from": "baseline", "span": 1, "ink_last": True, "version": 1},
    {"type": "motion_build", "blocks": [PANEL, PILL, PANEL, PILL, PANEL]},  # over the cap of 4: the fifth is dropped
    {"type": "motion_build", "blocks": [dict(PILL, id="c1")]},
    {"type": "motion_build", "blocks": []},
    {"type": "motion_build"},
    {"type": "motion_build", "blocks": "no", "order": 3, "from": [], "span": "x", "ink_last": "false"},
    {"type": "motion_build", "blocks": [PILL], "order": ATT, "from": ATT, "span": ATT, "ink_last": ATT, "version": ATT},
    {"type": "motion_build", "blocks": [PILL], "span": 99},
    {"type": "motion_build", "blocks": [PILL], "span": -4},
    {"type": "motion_build", "blocks": [PILL], "span": 4.7},
    {"type": "motion_build", "blocks": [{"type": "motion_text", "text": ATT}]},
    {"type": "motion_build", "blocks": [{"type": "motion_build", "blocks": [PILL]}]},
]


def test_python_twin_matches_gas_exactly(core_js):
    got = _gas_batch(core_js, CASES)
    bad = [(str(c)[:90], _norm(_py(c))[:160], g[:160]) for c, g in zip(CASES, got) if _norm(_py(c)) != _norm(g)]
    assert not bad, bad


def test_hostile_input_never_becomes_markup_and_options_are_closed(core_js):
    for h in [_py(CASES[8]), _py(CASES[9])] + _gas_batch(core_js, [CASES[8], CASES[9]]):
        low = h.lower()
        assert "<script" not in low and "onerror" not in low and "<img" not in low
        assert 'data-mob="stagger"' in h and "--cb-span:4;" in h and "--cb-org:50% 100%;" in h and 'data-mob-ink="last"' in h
    assert "--cb-span:8;" in _py(CASES[10]) and "--cb-span:1;" in _py(CASES[11]) and "--cb-span:4;" in _py(CASES[12])
    assert "<script" not in _py(CASES[13]).lower() and "&lt;script&gt;alert(2)" in _py(CASES[13]), "child text is escaped by the child's renderer"


def test_wrapper_passes_a_contract_free_child_through_untouched():
    """The wrapper adds one div and one <style>; the child's own markup is byte-identical to rendering it alone."""
    child = _py(PANEL)
    h = _py({"type": "motion_build", "blocks": [PANEL]})
    assert child in h
    rest = h.replace(child, "")
    assert rest.startswith('<div class="mo-build" data-mob="stagger" data-mob-ink="last" data-mob-v="1" style="--cb-span:4;--cb-org:50% 100%;"><style>')
    assert rest.endswith("</style></div>") and rest.count("<style>") == 1 and rest.count("<div") == 1
    assert "aria-hidden" not in rest and "role=" not in rest and "<script" not in rest.lower()
    assert "--p:" not in rest.split("<style>")[0], "the wrapper never sets the dial itself; a motion_timeline p track does"
    css = rest.split("<style>")[1]
    assert css.count("--p:") == 1 and "[data-cb]{--p:max(calc(var(--pb,1)*var(--n,1e9)" in css, "the only --p the wrapper writes is the re-timed copy of the inherited dial on the moving elements"


def test_every_rule_sits_inside_the_reduced_motion_gate_and_only_touches_data_cb():
    h = _py({"type": "motion_build", "blocks": [PANEL]})
    css = re.search(r"<style>(.*?)</style>", h, re.S).group(1)
    assert css.startswith("@media (prefers-reduced-motion:no-preference){") and css.endswith("}")
    assert css.count("@media") == 1 and css.count("{") == css.count("}")
    assert not re.search(r"=\d", css), "unquoted attribute values must be identifiers ([data-mob-ink=0] is an invalid selector and drops the rule)"
    body = css[len("@media (prefers-reduced-motion:no-preference){"):-1]
    for sel in re.findall(r"(?:^|})([^{}]+)\{", body):
        for s in sel.split(","):
            s = s.strip()
            assert s.startswith(".mo-build"), s
            assert s == ".mo-build" or "[data-cb" in s, "every moving rule is keyed on the contract: " + s
    assert "[data-cb=label]" in css and "transform" not in css.split("[data-cb=label]{")[1].split("}")[0], "labels only ever fade"
    for kind in ("link", "branch", "ref"):
        assert "[data-cb=" + kind + "][pathLength]{" in css.replace(",.mo-build ", ",").replace("}.mo-build ", "}") or "[data-cb=" + kind + "][pathLength]" in css
    assert "stroke-dasharray:1;stroke-dashoffset:calc(1 - var(--cb-r))" in css
    assert "'" not in css and '"' not in css, "quote-free template, stamped identically into both runtimes"


def test_cap_of_four_blocks_and_the_sixty_element_budget_note():
    h = _py(CASES[4])
    assert h.count("<span>Go</span>") == 2 and h.count(">Card<") == 2 and "showed 4 of 5" in h
    big = "<svg data-cb-root style=\"--n:70\">" + "".join('<rect data-cb="bar" style="--k:1"/>' for _ in range(70)) + "</svg>"
    wa._RENDERERS["cb_test_big"] = lambda b: big
    try:
        h = _py({"type": "motion_build", "blocks": [{"type": "cb_test_big"}]})
    finally:
        del wa._RENDERERS["cb_test_big"]
    assert "motion_build block 0 has 70 moving elements (budget 60)" in h


# ─── a synthetic sankey-like child that carries the full contract (the real D3 atoms emit it on their own branches) ───────────
def _synth(with_i: bool) -> str:
    """3 bars, 2 links, 2 labels, 1 ref: n = 8 moving elements, --k = clamp(0, p*9 - i, 1) in build order, optional --i."""
    def k(i):
        return "--k:clamp(0,calc(var(--p,1)*9 - " + str(i) + "),1);" + ("--i:" + str(i) + ";" if with_i else "")
    out = ['<svg data-cb-root viewBox="0 0 200 100" style="--n:8;width:200px;height:100px">']
    for i in range(3):
        out.append('<rect data-cb="bar" class="cb-fade" x="' + str(10 + i * 60) + '" y="20" width="20" height="60" fill="#4f8cff" style="' + k(i) + '"/>')
    for i in range(3, 5):
        out.append('<path data-cb="link" class="cb-fade" pathLength="1" d="M30 50 L70 50" fill="none" stroke="#999" stroke-width="4" style="' + k(i) + '"/>')
    for i in range(5, 7):
        out.append('<text data-cb="label" class="cb-fade" x="10" y="95" style="' + k(i) + '">L' + str(i) + "</text>")
    out.append('<line data-cb="ref" pathLength="1" x1="0" y1="10" x2="200" y2="10" stroke="#f00" style="' + k(7) + '"/>')
    out.append("</svg><table style=\"position:absolute;left:-9999px\"><tr><td>a</td><td>1</td></tr></table>")
    return "".join(out)


def _page(block, p, extra_flags=(), js=""):
    """Render block, set --p on the body (as a timeline would on an ancestor), read computed styles in headless Chromium."""
    probe = ("if(" + json.dumps(p is not None) + ")document.body.style.setProperty('--p'," + json.dumps(p if p is not None else 1) + ");"
             "var q=function(s){return Array.prototype.slice.call(document.querySelectorAll(s));};"
             "var out={bar:q('[data-cb=bar]').map(function(e){var m=/matrix\\(([^)]*)\\)/.exec(getComputedStyle(e).transform);return m?+m[1].split(',')[3].trim():1;}),"
             "op:q('[data-cb=bar]').map(function(e){return +getComputedStyle(e).opacity;}),"
             "link:q('[data-cb=link],[data-cb=ref]').map(function(e){var m=/-?[\\d.]+/.exec(getComputedStyle(e).strokeDashoffset);return m?+m[0]:0;}),"  # Chrome reports calc(0.2px)
             "lab:q('[data-cb=label]').map(function(e){return +getComputedStyle(e).opacity;}),"
             "tf:q('[data-cb=label]').map(function(e){return getComputedStyle(e).transform;}),"
             "org:q('[data-cb=bar]').map(function(e){return getComputedStyle(e).transformOrigin;})};" + js + "return out;")
    html = ("<!doctype html><meta charset=utf-8><body style='margin:0'>" + _py(block)
            + "<script>document.documentElement.setAttribute('data-probe', JSON.stringify((function(){" + probe + "})()));</script>")
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "p.html"
        f.write_text(html)
        out = subprocess.run([CHROMIUM, "--headless=new", "--password-store=basic", "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage", "--window-size=1000,700",
                              "--virtual-time-budget=1500", *extra_flags, "--dump-dom", f"file://{f}"], capture_output=True, text=True, timeout=90).stdout
    m = re.search(r"data-probe='([^']*)'|data-probe=\"([^\"]*)\"", out)
    assert m, out[:400]
    return json.loads(_h.unescape(m.group(1) or m.group(2)))


@pytest.fixture
def synth():
    wa._RENDERERS["cb_test_chart"] = lambda b: _synth(False)
    wa._RENDERERS["cb_test_chart_i"] = lambda b: _synth(True)
    yield
    del wa._RENDERERS["cb_test_chart"], wa._RENDERERS["cb_test_chart_i"]


@browser
def test_stagger_follows_the_child_index_space_on_p(synth):
    blk = {"type": "motion_build", "blocks": [{"type": "cb_test_chart"}]}
    # the child's k_i = clamp(0, p'*9 - i, 1), bars i=0..2, links 3..4, labels 5..6, ref 7; the wrapper re-times p' = max(p*8/9, 2p-1)
    a = _page(blk, 0.2)  # p' = 0.1778 -> 1.6 - i
    assert a["bar"] == pytest.approx([1, 0.6, 0], abs=0.01) and a["op"] == pytest.approx([1, 0.6, 0], abs=0.01)
    assert a["link"] == pytest.approx([1, 1, 1], abs=0.01) and a["lab"] == pytest.approx([0, 0], abs=0.01)
    b = _page(blk, 0.6)  # p' = 0.5333 -> 4.8 - i
    assert b["bar"] == pytest.approx([1, 1, 1], abs=0.01) and b["link"] == pytest.approx([0, 0.2, 1], abs=0.01)
    assert b["lab"] == pytest.approx([0, 0], abs=0.01) and all(t == "none" for t in b["tf"]), "labels never transform"
    assert _page(blk, 0.8)["lab"] == pytest.approx([1, 0.4], abs=0.01)  # p' = 0.7111 -> 6.4 - i: the chart ends at p = 1, not 8/9
    c = _page(blk, 1)
    assert c["bar"] == [1, 1, 1] and c["link"] == [0, 0, 0] and c["lab"] == [1, 1]
    assert all(o.startswith("10px 60px") for o in c["org"]), ("baseline = 50% 100% of the 20x60 fill box", c["org"])
    # dash-drawn kinds never fade as well (the .cb-fade rule is replaced by the draw)
    d = _page(blk, 0.2, js="out.lop=q('[data-cb=link]').map(function(e){return +getComputedStyle(e).opacity;});")
    assert d["lop"] == [1, 1]


@browser
def test_span_widens_the_windows_when_the_child_carries_an_index(synth):
    blk = {"type": "motion_build", "blocks": [{"type": "cb_test_chart_i"}], "span": 4}
    # kb_i = clamp(0, (p*(8+4) - i)/4, 1): at p = 0.2 -> 2.4 - i over 4: bars [0.6, 0.35, 0.1], links [0,0]
    a = _page(blk, 0.2)
    assert a["bar"] == pytest.approx([0.6, 0.35, 0.1], abs=0.01) and a["op"] == pytest.approx([0.6, 0.35, 0.1], abs=0.01)
    b = _page(blk, 0.6)  # 7.2 - i over 4: links i=3,4 -> 1, 0.8 drawn (offset 0, 0.2); label 5 -> 0.55; ref 7 -> 0.05
    assert b["link"] == pytest.approx([0, 0.2, 0.95], abs=0.01) and b["lab"] == pytest.approx([0.55, 0.3], abs=0.01)
    assert _page(blk, 1)["bar"] == [1, 1, 1]
    one = _page({"type": "motion_build", "blocks": [{"type": "cb_test_chart_i"}], "span": 1}, 0.2)
    assert one["bar"] == pytest.approx([1, 0.8, 0], abs=0.01), "span 1 is one element after another, ending at p = 1"


@browser
def test_together_by_kind_and_ink_last(synth):
    tg = {"type": "motion_build", "blocks": [{"type": "cb_test_chart"}], "order": "together"}
    a = _page(tg, 0.6)  # everything on clamp(p*1.25): 0.75; labels and ref wait for 0.8
    assert a["bar"] == pytest.approx([0.75] * 3, abs=0.01) and a["link"] == pytest.approx([0.25, 0.25, 1], abs=0.01) and a["lab"] == [0, 0]
    assert _page(tg, 1)["lab"] == [1, 1]
    bk = {"type": "motion_build", "blocks": [{"type": "cb_test_chart"}], "order": "by-kind"}
    b = _page(bk, 0.2)  # geometry 0..0.4 -> 0.5; links 0.4..0.7 -> 0; labels 0.7..0.9; ref 0.9..1
    assert b["bar"] == pytest.approx([0.5] * 3, abs=0.01) and b["link"] == pytest.approx([1, 1, 1], abs=0.01) and b["lab"] == [0, 0]
    c = _page(bk, 0.6)
    assert c["bar"] == [1, 1, 1] and c["link"] == pytest.approx([1 / 3, 1 / 3, 1], abs=0.01) and c["lab"] == [0, 0]
    ink = {"type": "motion_build", "blocks": [{"type": "cb_test_chart"}], "order": "by-kind", "ink_last": False}
    assert _page(ink, 0.2)["lab"] == pytest.approx([0.6, 0.6], abs=0.01), "ink_last false: labels fade in over the first third"
    assert _page(dict(ink, order="stagger"), 0.2)["lab"] == pytest.approx([0.6, 0.6], abs=0.01)


@browser
def test_from_sets_the_growth_origin(synth):
    o = _page({"type": "motion_build", "blocks": [{"type": "cb_test_chart"}], "from": "center"}, 1)["org"]
    assert all(x.startswith("10px 30px") or x.endswith("30px") for x in o), o
    o = _page({"type": "motion_build", "blocks": [{"type": "cb_test_chart"}], "from": "origin"}, 1)["org"]
    assert all(x.startswith("0px 0px") for x in o), o


@browser
def test_static_paths_leave_the_child_untouched(synth):
    blk = {"type": "motion_build", "blocks": [{"type": "cb_test_chart"}]}
    for r in (_page(blk, None), _page(blk, 0.2, ["--force-prefers-reduced-motion"])):
        assert r["bar"] == [1, 1, 1] and r["op"] == [1, 1, 1] and r["link"] == [0, 0, 0] and r["lab"] == [1, 1]


def _kinds() -> str:
    """One of each kind the builders reported (2026-10-21): a filled sunburst arc and a chord ribbon (no pathLength), a sankey node rect,
    an org card node with its own rise, a dashed reference line, a dashed waterfall connector and a solid branch."""
    k = "--k:clamp(0,calc(var(--p,1)*8 - 0),1);"
    return ('<svg data-cb-root viewBox="0 0 200 100" style="--n:7;width:200px;height:100px">'
            '<path data-cb="arc" class="cb-fade" d="M100 50 L140 50 A40 40 0 0 1 100 90 Z" fill="#4f8cff" style="' + k + '"/>'
            '<path data-cb="ribbon" class="cb-fade" d="M60 50 Q100 50 100 10 Q100 50 140 50 Z" fill="#f59e0b" style="' + k + '"/>'
            '<rect data-cb="node" class="cb-fade" x="10" y="20" width="20" height="60" fill="#10b981" style="' + k + '"/>'
            '<line data-cb="ref" class="cb-fade" pathLength="1" x1="0" y1="10" x2="200" y2="10" stroke="#f00" stroke-dasharray="6 3" style="' + k + '"/>'
            '<path data-cb="link" class="cb-fade" pathLength="1" d="M30 50 L70 50" fill="none" stroke="#999" style="' + k + 'stroke-dasharray:4 2;"/>'
            '<path data-cb="branch" class="cb-fade" pathLength="1" d="M30 60 L70 60" fill="none" stroke="#999" style="' + k + '"/>'
            '</svg><div data-cb="node" class="cb-fade" style="' + k + 'transform:translateY(calc((1 - var(--k,1))*8px));">Ada</div>')


@browser
def test_kinds_from_the_real_atoms_get_the_right_treatment():
    wa._RENDERERS["cb_test_kinds"] = lambda b: _kinds()
    try:
        js = ("var g=function(s){return getComputedStyle(document.querySelector(s));};"
              "out.arc=[g('[data-cb=arc]').transform,g('[data-cb=arc]').transformOrigin,g('[data-cb=arc]').transformBox,+g('[data-cb=arc]').opacity];"
              "out.rib=[g('[data-cb=ribbon]').transform,g('[data-cb=ribbon]').transformOrigin];"
              "out.rect=[g('rect[data-cb=node]').transform,g('rect[data-cb=node]').transformOrigin];"
              "out.card=[g('div[data-cb=node]').transform,+g('div[data-cb=node]').opacity];"
              "out.ref=[g('[data-cb=ref]').strokeDasharray,+g('[data-cb=ref]').opacity];"
              "out.dl=[g('[data-cb=link]').strokeDasharray,+g('[data-cb=link]').opacity];"
              "out.br=[g('[data-cb=branch]').strokeDasharray,g('[data-cb=branch]').strokeDashoffset,+g('[data-cb=branch]').opacity];")
        r = _page({"type": "motion_build", "blocks": [{"type": "cb_test_kinds"}]}, 0.0625, js=js)  # p' = max(0.0547, -0.875) -> k = 0.4375
        k = 0.4375
        assert r["arc"][0] == "matrix(%g, 0, 0, %g, 0, 0)" % (k, k) and r["arc"][1] == "100px 50px" and r["arc"][2] == "view-box" and r["arc"][3] == pytest.approx(k, abs=0.01)
        assert r["rib"][0] == r["arc"][0] and r["rib"][1] == "100px 50px", "arcs and ribbons scale out from the viewBox centre"
        assert r["rect"][0] == "matrix(1, 0, 0, %g, 0, 0)" % k and r["rect"][1] == "10px 60px", "a sankey node rect grows from its base"
        # the card sits outside the chart root, so no --n reaches it and the re-time is the identity: k = 0.5, rise 4px
        assert r["card"][0] == "matrix(1, 0, 0, 1, 0, 4)" and r["card"][1] == pytest.approx(0.5, abs=0.01), "a card node keeps its own rise and only fades"
        assert r["ref"][0] == "6px, 3px" and r["ref"][1] == pytest.approx(k, abs=0.01), "a dashed reference line keeps its dash and fades"
        assert r["dl"][0] == "4px, 2px" and r["dl"][1] == pytest.approx(k, abs=0.01), "a dashed connector keeps its dash and fades"
        assert r["br"][0] == "1px" and r["br"][1].startswith("calc(0.5625") and r["br"][2] == 1, "a solid branch draws and does not fade"
    finally:
        del wa._RENDERERS["cb_test_kinds"]
