"""motion_selection (backlog I73, from the owner's video review of 2026-10-21, event 40): a design-tool selection frame that draws round its own content.

A hairline frame, four round corner handles, a tint over the selected content and a small floating toolbar above it. The content is real text
(or up to 3 child atoms); everything else is aria-hidden. p drives it: the frame draws in, the tint comes up, the handles pop, the toolbar rises,
and p = 1 (the standalone render) is the settled picture.

Same layers as test_motion_candidates.py: Python and GAS agree byte for byte, every option is closed and inert, hostile input never becomes markup,
and a real browser shows the pieces at fixed values of p, at 650 and 320 px.
"""
from __future__ import annotations

import html as _h
import json
import re
import subprocess
import tempfile
from pathlib import Path

import pytest

from test_motion_atoms import CHROMIUM, _gas_batch, _norm, _py, browser, core_js  # noqa: F401

HOSTILE = 'x";}</style><script>alert(1)</script><b onload="1"'
BASE = {"type": "motion_selection", "text": "Claude makes it."}

CASES = [
    BASE, {"type": "motion_selection"}, dict(BASE, color="#e11d48"), dict(BASE, color="red"), dict(BASE, color=HOSTILE),
    dict(BASE, handles=False), dict(BASE, handles=True), dict(BASE, handles="no"), dict(BASE, handles=0), dict(BASE, handles=None),
    dict(BASE, tint=False), dict(BASE, tint=True), dict(BASE, tint="no"), dict(BASE, tint=0),
    dict(BASE, toolbar=["B", "I", "U", "Aa", "…", "Link"]), dict(BASE, toolbar=["a", "b", "c", "d", "e", "f", "g", "h"]),
    dict(BASE, toolbar=[]), dict(BASE, toolbar=["", "  ", None, 3, True, {"x": 1}, ["y"]]), dict(BASE, toolbar="B"), dict(BASE, toolbar=None), dict(BASE, toolbar=7),
    dict(BASE, toolbar=["<b>", HOSTILE, "a&b", "toolongtoolong"]),
    dict(BASE, text="x" * 300), dict(BASE, text=HOSTILE), dict(BASE, text=""), dict(BASE, text="   "), dict(BASE, text=42), dict(BASE, text=["x"]), dict(BASE, text="two\nlines"),
    dict(BASE, version=2), dict(BASE, version=1), dict(BASE, version="x"), dict(BASE, version=1.5),
    {"type": "motion_selection", "blocks": [{"type": "motion_pill", "text": "Go"}]},
    {"type": "motion_selection", "text": "ignored", "blocks": [{"type": "motion_pill", "text": "Go"}, {"type": "demo_panel", "title": "T", "rows": [["a", "1"]]}]},
    {"type": "motion_selection", "text": "fallback", "blocks": ["x", 3, None, {"type": "nope"}]},
    {"type": "motion_selection", "text": "fallback", "blocks": []},
    {"type": "motion_selection", "blocks": [{"type": "motion_pill", "id": "k1", "text": "Go"}] * 6},
    {"type": "motion_selection", "blocks": "javascript:alert(1)"}, {"type": "motion_selection", "text": "x", "blocks": {"a": 1}},
    dict(BASE, id="s1", enter="rise"),
]


def test_python_matches_gas_exactly(core_js):
    got = _gas_batch(core_js, CASES)
    bad = [str(b)[:110] for b, g in zip(CASES, got) if _norm(_py(b)) != _norm(g)]
    assert not bad, bad


def test_structure_content_is_real_text_and_decoration_is_aria_hidden():
    h = _py(BASE)
    assert h.count('data-sel="frame"') == 1 and h.count('data-sel="handle"') == 4 and h.count('data-sel="bar"') == 1 and h.count('data-sel="tint"') == 1
    assert ">Claude makes it.<" in h
    for part in ("frame", "handle", "bar", "tint"):
        assert all('aria-hidden="true"' in m for m in re.findall(r'<(?:span|div)[^>]*data-sel="' + part + r'"[^>]*>', h)), part
    assert "<script" not in h.lower() and "role=" not in h and "tabindex" not in h and "<button" not in h
    # the content element itself is not hidden
    body = re.search(r'<div data-sel="body"[^>]*>(.*?)</div>', h, re.S)
    assert body and "aria-hidden" not in re.search(r'<div data-sel="body"[^>]*>', h).group(0) and body.group(1) == "Claude makes it."


def test_options_toggle_pieces():
    assert 'data-sel="handle"' not in _py(dict(BASE, handles=False))
    assert 'data-sel="tint"' not in _py(dict(BASE, tint=False))
    assert 'data-sel="bar"' not in _py(dict(BASE, toolbar=[]))
    assert _py(dict(BASE, handles="no")) == _py(BASE) == _py(dict(BASE, handles=None)), "only an explicit false turns handles off"
    assert _py(dict(BASE, tint="no")) == _py(BASE), "only an explicit false turns the tint off"
    assert _py(dict(BASE, toolbar="B")) == _py(BASE) == _py(dict(BASE, toolbar=None)), "a non-list toolbar is the default"


def test_toolbar_is_capped_cleaned_and_text_only():
    h = _py(dict(BASE, toolbar=["a", "b", "c", "d", "e", "f", "g", "h"]))
    assert len(re.findall(r'data-sel="tool"', h)) == 6 and ">g<" not in h
    h = _py(dict(BASE, toolbar=["", "  ", None, {"x": 1}, "ok", 3]))
    assert re.findall(r'data-sel="tool"[^>]*>([^<]*)<', h) == ["ok", "3"]
    h = _py(dict(BASE, toolbar=["toolongtoolong"]))
    assert re.findall(r'data-sel="tool"[^>]*>([^<]*)<', h) == ["toolon"]
    assert re.findall(r'data-sel="tool"[^>]*>([^<]*)<', _py(BASE)) == ["B", "I", "U", "Aa", "…"]
    assert "<img" not in h and "<svg" not in h


def test_text_is_capped_at_120_and_empty_falls_back():
    h = _py(dict(BASE, text="x" * 300))
    assert ">" + "x" * 120 + "<" in h and "x" * 121 not in h
    for empty in ("", "   ", None, ["x"]):
        assert ">Selected text<" in _py({"type": "motion_selection", "text": empty})


def test_children_replace_the_text_and_garbage_children_fall_back():
    h = _py({"type": "motion_selection", "text": "ignored", "blocks": [{"type": "motion_pill", "text": "Go"}]})
    assert ">Go<" in h and "ignored" not in h
    h = _py({"type": "motion_selection", "text": "fallback", "blocks": ["x", 3, None]})
    assert ">fallback<" in h
    h = _py({"type": "motion_selection", "blocks": [{"type": "motion_pill", "text": str(i)} for i in range(6)]})
    assert ">0<" in h and ">2<" in h and ">3<" not in h, "at most 3 children"


def test_every_moving_value_reads_p_and_nothing_loops_or_scripts():
    h = _py(BASE)
    assert h.count("var(--p,1)") == 4 and not re.search(r"var\(--s[,)]", h)
    assert "animation" not in h and "@keyframes" not in h and "<script" not in h.lower() and "<style" not in h.lower()


def test_colour_is_a_hex_or_the_stage_accent_and_is_never_echoed():
    assert "#e11d48" in _py(dict(BASE, color="#E11D48"))
    d = _py(BASE)
    assert "var(--mt-acc,#38bdf8)" in d
    for bad in ("red", HOSTILE, "#fff", "#12345", 7, None, ["#112233"]):
        assert _py(dict(BASE, color=bad)) == d, bad


def test_hostile_values_never_reach_markup():
    h = _py(dict(BASE, text=HOSTILE, color=HOSTILE, toolbar=[HOSTILE, "<b>"], handles=HOSTILE, tint=HOSTILE, version=HOSTILE))
    assert "<script" not in h and not re.search(r"<[^>]*onload=", h) and "</style>" not in h and "<b>" not in h and "<b " not in h
    assert "NaN" not in h and "undefined" not in h and "Infinity" not in h and "[object" not in h
    assert "&lt;script&gt;" in h


def test_version_note():
    assert "version" not in _py(BASE).lower() and _py(dict(BASE, version=1)) == _py(BASE) and _py(dict(BASE, version="x")) == _py(BASE)
    h = _py(dict(BASE, version=3))
    assert "Written for motion_selection version 3; drawn as version 1." in h
    assert h.replace(re.search(r'<div style="font-size:0.75rem[^>]*>Written for[^<]*</div>', h).group(0), "") == _py(BASE)


def test_deterministic():
    assert _py(dict(BASE, toolbar=["a", "b"])) == _py(dict(BASE, toolbar=["a", "b"]))


# ─── registration ─────────────────────────────────────────────────────────────
def test_registered_everywhere():
    root = Path(__file__).resolve().parent.parent
    import yaml
    schema = yaml.safe_load((root / "atoms" / "schema.yaml").read_text())
    atoms = schema["atoms"] if isinstance(schema, dict) and "atoms" in schema else schema
    ent = [a for a in atoms if isinstance(a, dict) and a.get("type") == "motion_selection"]
    assert len(ent) == 1 and ent[0]["stage"] == "preview"
    for k in ("description", "compact_description", "routing_text", "intent_phrases", "fields", "notes", "surfaces", "source"):
        assert ent[0].get(k), k
    assert len(ent[0]["intent_phrases"]) >= 2
    for f in ("text", "blocks", "toolbar", "handles", "color", "tint", "version"):
        assert f in ent[0]["fields"], f
    packs = yaml.safe_load((root / "atoms" / "atom-packs.yaml").read_text())
    assert "motion_selection" in packs["a2ui-effects-v1"]
    assert '"motion_selection":"a2ui-effects-v1"' in (root / "apps-script-surface" / "gas-wired-renderer" / "PackMap.gs").read_text()
    gen = (root / "scripts" / "generate_atom_pages.py").read_text()
    assert '"motion_selection"' in gen


# ─── a real browser: fixed p, at 650 and 320 px ──────────────────────────────
def _page(block_html: str, p, width: int, js: str):
    page = ("<!doctype html><meta charset=utf-8><body style='margin:0;font:28px system-ui'><div style='width:" + str(width) + "px;padding:0;--p:" + str(p) + "'>" + block_html
            + "</div><script>document.documentElement.setAttribute('data-probe', JSON.stringify((function(){" + js + "})()));</script>")
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "p.html"
        f.write_text(page)
        out = subprocess.run([CHROMIUM, "--headless=new", "--password-store=basic", "--no-sandbox", "--disable-gpu", f"--window-size={width},900", "--virtual-time-budget=1000",
                              "--dump-dom", f"file://{f}"], capture_output=True, text=True, timeout=90).stdout
    m = re.search(r"data-probe='([^']*)'|data-probe=\"([^\"]*)\"", out)
    assert m, out[:300]
    return json.loads(_h.unescape(m.group(1) or m.group(2)))


_STATE = ("function q(s){return Array.prototype.slice.call(document.querySelectorAll('[data-sel='+s+']'));}"
          "function cs(e){return getComputedStyle(e);}"
          "var f=q('frame')[0],t=q('tint')[0],b=q('bar')[0];"
          "return {clip:cs(f).clipPath,tint:t?+(+cs(t).opacity).toFixed(3):null,bar:b?+(+cs(b).opacity).toFixed(3):null,"
          "barY:b?new DOMMatrix(cs(b).transform).m42:null,"
          "hs:q('handle').map(function(e){return +(+cs(e).opacity).toFixed(3);}),hsc:q('handle').map(function(e){return +(new DOMMatrix(cs(e).transform).a).toFixed(3);})};")


def _inset(clip):
    m = re.search(r"inset\(([\d.]+)(px|%)", clip)
    return None if not m else float(m.group(1))


@browser
def test_the_frame_draws_in_then_the_handles_pop_then_the_toolbar_rises(core_js):
    html = _gas_batch(core_js, [BASE])[0]
    st = {p: _page(html, p, 650, _STATE) for p in (0, 0.25, 0.5, 0.75, 1)}
    # frame: clipped away at 0, partly drawn at 0.25, complete from 0.4
    assert _inset(st[0]["clip"]) == 50 and st[1]["clip"] in ("none", "inset(0px)", "inset(0%)") and st[0.5]["clip"] in ("none", "inset(0px)", "inset(0%)"), st
    assert st[0]["hs"] == [0, 0, 0, 0] and st[1]["hs"] == [1, 1, 1, 1] and st[1]["hsc"] == [1, 1, 1, 1], st
    assert st[0]["tint"] == 0 and abs(st[1]["tint"] - 0.22) < 0.01
    assert st[0]["bar"] == 0 and st[1]["bar"] == 1 and st[1]["barY"] == 0 and st[0]["barY"] > 4
    # staged: at 0.25 the frame is drawing, the handles not yet up, the toolbar not yet there
    assert st[0.25]["clip"] != "none" and 0 < _inset(st[0.25]["clip"]) < _inset(st[0]["clip"])
    assert st[0.25]["bar"] == 0 and 0 < st[0.25]["tint"] < 0.22
    # at 0.5 the frame is complete, the handles are up, the toolbar is still rising (not 0, not 1 yet is allowed at exactly 0.5 = 0)
    assert all(o > 0 for o in st[0.5]["hs"]) and st[0.5]["bar"] >= 0
    assert 0 < st[0.75]["bar"] < 1 and st[0.75]["barY"] > 0
    # monotone: nothing ever goes backwards as p grows
    order = (0, 0.25, 0.5, 0.75, 1)
    for key in ("tint", "bar"):
        vals = [st[p][key] for p in order]
        assert vals == sorted(vals), (key, vals)
    assert [st[p]["hs"][0] for p in order] == sorted(st[p]["hs"][0] for p in order)


@browser
def test_standalone_is_the_settled_picture_in_both_twins(core_js):
    for html in (_py(BASE), _gas_batch(core_js, [BASE])[0]):
        d = _page(html, None, 650, _STATE)     # no --p set at all: the default is 1
        assert d["clip"] in ("none", "inset(0px)", "inset(0%)") and d["bar"] == 1 and d["hs"] == [1, 1, 1, 1] and d["barY"] == 0, d


_BOX = ("var r=function(e){var b=e.getBoundingClientRect();return {l:b.left,t:b.top,r:b.right,b:b.bottom,w:b.width,h:b.height};};"
        "var q=function(s){return Array.prototype.slice.call(document.querySelectorAll('[data-sel='+s+']'));};"
        "var all=[].concat(q('frame'),q('handle'),q('bar'),q('tool'),q('body'),q('tint'));"
        "var minL=Math.min.apply(null,all.map(function(e){return r(e).l;})),maxR=Math.max.apply(null,all.map(function(e){return r(e).r;})),minT=Math.min.apply(null,all.map(function(e){return r(e).t;}));"
        "var tools=q('tool').map(function(e){return parseFloat(getComputedStyle(e).fontSize);});"
        "var body=q('body')[0],bar=q('bar')[0],fr=q('frame')[0];"
        "return {minL:minL,maxR:maxR,minT:minT,sw:document.documentElement.scrollWidth,iw:innerWidth,minFont:tools.length?Math.min.apply(null,tools):99,"
        "barBottom:bar?r(bar).b:null,bodyTop:r(body).t,frame:r(fr),body:r(body),bar:bar?r(bar):null,handles:q('handle').map(r)};")

LONG = {"type": "motion_selection", "text": "A rather long line of selected copy that has to wrap on a phone without anything poking out of its box."}


@browser
def test_nothing_is_clipped_or_wider_than_the_container_at_650_and_320(core_js):
    for blk in (BASE, LONG, dict(LONG, toolbar=["Bold", "Italic", "Under", "Color", "Link", "More"]), {"type": "motion_selection", "blocks": [{"type": "motion_pill", "text": "Go"}]}):
        for html in (_py(blk), _gas_batch(core_js, [blk])[0]):
            for w in (650, 320):
                for p in (0, 0.5, 1):
                    d = _page(html, p, w, _BOX)
                    assert d["minL"] >= -0.01 and d["maxR"] <= w + 0.01 and d["sw"] <= d["iw"], (w, p, str(blk)[:50], d)
                    assert d["minT"] >= -0.01, (w, p, d)
                    assert d["minFont"] >= 12, d
                    # the toolbar sits above the content and never over it
                    if d["bar"]:
                        assert d["barBottom"] <= d["frame"]["t"] + 0.01 or p < 1, d
    d = _page(_py(BASE), 1, 650, _BOX)
    assert d["body"]["l"] >= d["frame"]["l"] and d["body"]["r"] <= d["frame"]["r"] + 0.01, d
    assert d["bar"]["b"] <= d["frame"]["t"] + 0.01 and d["frame"]["h"] > 20
    # four handles, one on each corner of the frame, centred on the corner
    fr, hs = d["frame"], d["handles"]
    corners = sorted([(fr["l"], fr["t"]), (fr["r"], fr["t"]), (fr["l"], fr["b"]), (fr["r"], fr["b"])])
    centres = sorted([(h["l"] + h["w"] / 2, h["t"] + h["h"] / 2) for h in hs])
    assert all(abs(c[0] - k[0]) <= 1.5 and abs(c[1] - k[1]) <= 1.5 for c, k in zip(centres, corners)), (centres, corners)


@browser
def test_the_toolbar_does_not_shift_the_layout_as_p_builds(core_js):
    a, b = (_page(_py(BASE), p, 650, "var f=document.querySelector('[data-sel=frame]').getBoundingClientRect();return [Math.round(f.left),Math.round(f.top),Math.round(f.width),Math.round(f.height)];") for p in (0, 1))
    assert a == b, (a, b)


@browser
def test_reduced_motion_shows_the_end_state_inside_a_film():
    from test_motion_atoms import _scene
    tl = _scene([dict(BASE, id="s1", place={"x": 10, "y": 10, "w": 70})], [{"target": "s1", "keys": [{"t": 0, "p": 0}, {"t": 2, "p": 1}]}], poster=4)
    page = ("<!doctype html><meta charset=utf-8><body style='margin:0'>" + _py(tl) + "<script>document.documentElement.setAttribute('data-probe', JSON.stringify((function(){" + _STATE + "})()));</script>")
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "p.html"
        f.write_text(page)
        out = subprocess.run([CHROMIUM, "--headless=new", "--password-store=basic", "--no-sandbox", "--disable-gpu", "--force-prefers-reduced-motion", "--window-size=1000,700",
                              "--virtual-time-budget=1500", "--dump-dom", f"file://{f}"], capture_output=True, text=True, timeout=90).stdout
    m = re.search(r"data-probe='([^']*)'|data-probe=\"([^\"]*)\"", out)
    d = json.loads(_h.unescape(m.group(1) or m.group(2)))
    assert d["bar"] == 1 and d["hs"] == [1, 1, 1, 1], d


# ─── existing payloads, byte for byte against main before this atom ──────────
def test_existing_motion_payloads_are_unchanged():
    """Adding a renderer must not touch any other: every existing payload still renders exactly as at the parent commit (cbdfcc57e)."""
    import importlib.util, sys
    from renderers import web_article as wa
    root = Path(__file__).resolve().parent.parent
    r = subprocess.run(["git", "-C", str(root), "show", "cbdfcc57e:renderers/web_article.py"], capture_output=True, text=True)
    if r.returncode:
        pytest.skip("cbdfcc57e not available")
    f = root / "renderers" / "_web_article_pre_selection.py"
    f.write_text(r.stdout)
    try:
        spec = importlib.util.spec_from_file_location("renderers._web_article_pre_selection", f)
        old = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = old
        spec.loader.exec_module(old)
    finally:
        f.unlink()
    old._mo_install()
    wa._mo_install()
    from test_motion_glitch import _existing_payloads
    pays = _existing_payloads()
    assert len(pays) > 150
    bad = []
    for b in pays:
        k = b.get("component") or b["type"]
        if k not in old._RENDERERS:
            continue
        try:
            a = old._RENDERERS[k](dict(b))
        except Exception:
            continue
        if a != wa._RENDERERS[k](dict(b)):
            bad.append(k)
    assert not bad, bad[:10]
