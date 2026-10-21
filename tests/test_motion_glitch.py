"""The glitch tear (backlog I70, from the owner's video review of 2026-10-07, event 2): thin horizontal slices of ANY block displaced sideways
with a short jitter, an optional red/cyan fringe, driven by the film dial. It is an optional `glitch` prop on the shared motion wrapper,
next to halo / smear / tilt, so it works on text, cards, anything.

Same layers as test_motion_candidates.py: Python and GAS agree byte for byte, the prop is inert when off, hostile input never becomes markup,
and a real browser shows the tear at fixed instants and the clean block at p = 1.
"""
from __future__ import annotations

import re

import pytest

from test_motion_atoms import CHROMIUM, _gas_batch, _norm, _probe, _py, _scene, browser, core_js  # noqa: F401

PILL = {"type": "motion_pill", "text": "Go"}
CARD = {"type": "demo_panel", "title": "Card", "rows": [["a", "1"], ["b", "2"]]}
TEXT = {"type": "motion_text", "text": "VILLAIN", "mode": "block"}
HOSTILE = 'x";}</style><script>alert(1)</script><b onload="1"'

CASES = [
    dict(PILL, glitch=True), dict(CARD, glitch=True), dict(TEXT, glitch=True),
    dict(PILL, glitch={"slices": 3, "shift": 20, "fringe": 5, "seed": 42}),
    dict(PILL, glitch={"dial": "s", "fringe": 4}), dict(PILL, glitch={"dial": "S"}), dict(PILL, glitch={"fringe_a": "#112233", "fringe_b": "#aabbcc", "fringe": 6}),
    dict(PILL, glitch={"slices": 999, "shift": 999, "fringe": 999, "seed": 99999}), dict(PILL, glitch={"slices": -5, "shift": -3, "fringe": -1, "seed": -9}),
    dict(PILL, glitch={"slices": "x", "shift": "y", "fringe": "z", "seed": "w", "dial": 7}), dict(PILL, glitch={"shift": 0, "fringe": 0}),
    dict(PILL, glitch={"shift": 0, "fringe": 3}), dict(PILL, glitch={}), dict(PILL, glitch=False), dict(PILL, glitch=None), dict(PILL, glitch=0),
    dict(PILL, glitch="javascript:alert(1)"), dict(PILL, glitch=["x"]), dict(PILL, glitch=1),
    dict(PILL, glitch={"fringe_a": HOSTILE, "fringe_b": HOSTILE, "fringe": 4, "dial": HOSTILE}),
    dict(PILL, glitch=True, halo=True, smear=True, tilt=True, enter="rise"),
    dict(PILL, id="a1", glitch=True), dict(CARD, id="c1", glitch={"seed": 3}),
    {"type": "motion_pill", "text": "<script>alert(1)</script>", "glitch": True},
    {"type": "demo_panel", "title": HOSTILE, "rows": [[HOSTILE, "1"]], "glitch": {"fringe": 3}},
    {"type": "motion_text", "text": "Hi", "split": 6, "glitch": {"dial": "s", "fringe": 3}},
]


def test_python_matches_gas_exactly(core_js):
    got = _gas_batch(core_js, CASES)
    bad = [str(b)[:110] for b, g in zip(CASES, got) if _norm(_py(b)) != _norm(g)]
    assert not bad, bad


def test_inert_when_off_and_existing_payloads_unchanged():
    for base in (PILL, CARD, TEXT):
        plain = _py(dict(base))
        for off in (False, None, 0, "", {}, "javascript:1", ["x"], {"shift": 0, "fringe": 0}):
            assert _py(dict(base, glitch=off)) == plain, (base["type"], off)
        assert "mo-glitch" not in plain


def test_structure_slices_are_aria_hidden_copies_and_one_real_block():
    h = _py(dict(CARD, glitch={"slices": 5, "seed": 1}))
    assert h.count('class="mo-glitch"') == 1 and h.count('class="mo-gl-b"') == 1 and h.count('class="mo-gl-s"') == 5
    assert h.count('aria-hidden="true" inert') >= 5
    assert "<script" not in h.lower()
    # the real copy is the only one a screen reader meets
    base = re.search(r'<div class="mo-gl-b"[^>]*>(.*?)</div><div class="mo-gl-s"', h, re.S)
    assert base and "Card" in base.group(1)
    assert h.count("clip-path:inset(") == 5 and "translateX(calc(" in h and "sin(calc(" in h


def test_ids_are_not_duplicated_into_the_copies():
    from renderers import web_article as wa
    h = wa._mo_glitch({"slices": 4}, '<div id="x1" data-id="k">a</div>')
    assert h.count('id="x1"') == 1 and h.count('data-id="k"') == 5, h
    ids = re.findall(r'\sid="([^"]+)"', h)
    assert len(ids) == len(set(ids)), ids


def test_blocks_with_script_are_left_alone():
    from renderers import web_article as wa
    wa._mo_install()
    out = wa._mo_glitch({}, "<div>a</div><script>1</script>")
    assert out == "<div>a</div><script>1</script>"


def test_deterministic_and_seeded():
    a, b = _py(dict(PILL, glitch={"seed": 5})), _py(dict(PILL, glitch={"seed": 5}))
    assert a == b and "random" not in a.lower()
    assert _py(dict(PILL, glitch={"seed": 6})) != a
    assert _py(dict(PILL, glitch=True)) == _py(dict(PILL, glitch={"seed": 7, "slices": 7, "shift": 8, "fringe": 2, "dial": "p"}))


def test_hostile_values_never_reach_markup():
    h = _py(dict(PILL, glitch={"fringe_a": HOSTILE, "fringe_b": HOSTILE, "fringe": 4, "dial": HOSTILE, "slices": HOSTILE}))
    assert "alert" not in h and "onload" not in h and "</style><script" not in h
    assert "NaN" not in h and "undefined" not in h and "Infinity" not in h
    assert "rgba(255,45,111" in h and "rgba(25,211,255" in h, "invalid colours fall back to the defaults"


def test_the_dial_is_p_by_default_and_s_on_request():
    ours = lambda h: "".join(re.findall(r'<div class="mo-gl-[bs]"[^>]*style="([^"]*)"', h))     # the wrapper's own styles, not the pill's
    p, s = ours(_py(dict(PILL, glitch=True))), ours(_py(dict(PILL, glitch={"dial": "s"})))
    assert "var(--p,1)" in p and "var(--s" not in p
    assert "var(--s,0)" in s and "var(--p" not in s


def test_reduced_motion_and_print_show_the_clean_block():
    h = _py(dict(PILL, glitch=True))
    assert "@media (prefers-reduced-motion:reduce)" in h and ".mo-gl-s{display:none!important}" in h and ".mo-gl-b{opacity:1!important}" in h


def test_seed_bounds_the_slice_pattern():
    h = _py(dict(PILL, glitch={"slices": 12, "shift": 40}))
    vals = [abs(float(x)) for x in re.findall(r"translateX\(calc\((-?[0-9.]+)%", h)]
    assert len(vals) == 12 and max(vals) <= 40 and min(vals) > 0


# ─── a real browser ──────────────────────────────────────────────────────────
_JS = ("var w=document.querySelector('[data-mt-id=g1] .mo-glitch');var b=w.querySelector('.mo-gl-b'),s=w.querySelectorAll('.mo-gl-s');"
       "var tx=Array.prototype.map.call(s,function(e){var m=new DOMMatrix(getComputedStyle(e).transform);return Math.round(m.m41*100)/100;});"
       "var r=b.getBoundingClientRect();"
       "return {b:+getComputedStyle(b).opacity,s:Array.prototype.map.call(s,function(e){return +getComputedStyle(e).opacity;}),tx:tx,disp:getComputedStyle(s[0]).display,w:Math.round(r.width),h:Math.round(r.height)};")


def _tear(glitch, key, t):
    tl = _scene([dict(CARD, id="g1", glitch=glitch, place={"x": 10, "y": 10, "w": 60})], [{"target": "g1", "keys": [{"t": 0, key: 0}, {"t": 4, key: 1}]}])
    return _probe(tl, t, _JS)


@browser
def test_tear_runs_while_p_builds_and_the_end_state_is_clean():
    for t in (0, 1, 2, 3):
        d = _tear({"seed": 4, "shift": 12}, "p", t)
        assert d["b"] == 0 and all(o == 1 for o in d["s"]), (t, d)
        assert any(abs(x) > 0.5 for x in d["tx"]), (t, d)
    end = _tear({"seed": 4, "shift": 12}, "p", 4)
    assert end["b"] == 1 and all(o == 0 for o in end["s"]), end


@browser
def test_slices_move_independently_and_the_tear_decays():
    early, late = _tear({"seed": 4, "shift": 12}, "p", 0.4), _tear({"seed": 4, "shift": 12}, "p", 3.6)
    assert len(set(early["tx"])) >= 4, early                       # slices are not displaced in lock step
    assert max(map(abs, late["tx"])) < max(map(abs, early["tx"])), (early, late)


@browser
def test_dial_s_is_clean_at_zero_and_torn_above():
    assert _tear({"dial": "s"}, "step", 0)["b"] == 1
    d = _tear({"dial": "s", "shift": 12}, "step", 2)
    assert d["b"] == 0 and any(abs(x) > 0.5 for x in d["tx"]), d


@browser
def test_standalone_render_is_the_finished_picture():
    d = _probe(dict(CARD, id="g1", glitch=True), 0, "var w=document.querySelector('.mo-glitch');var b=w.querySelector('.mo-gl-b');return {b:+getComputedStyle(b).opacity,s:+getComputedStyle(w.querySelector('.mo-gl-s')).opacity};")
    assert d == {"b": 1, "s": 0}, d
    d = _probe(dict(CARD, glitch={"dial": "s"}), 0, "var w=document.querySelector('.mo-glitch');var b=w.querySelector('.mo-gl-b');return {b:+getComputedStyle(b).opacity,s:+getComputedStyle(w.querySelector('.mo-gl-s')).opacity};")
    assert d == {"b": 1, "s": 0}, d


@browser
def test_the_block_keeps_its_size_and_never_widens_the_page():
    plain = _probe(_scene([dict(CARD, id="g1", place={"x": 10, "y": 10, "w": 60})], []), 0, "var e=document.querySelector('[data-mt-id=g1]').getBoundingClientRect();return {w:Math.round(e.width),h:Math.round(e.height)};")
    d = _tear({"seed": 4, "shift": 40}, "p", 0.5)
    assert abs(d["w"] - plain["w"]) <= 1 and abs(d["h"] - plain["h"]) <= 1, (plain, d)
    sw = _probe(dict(CARD, glitch={"shift": 40}), 0, "return [document.documentElement.scrollWidth,innerWidth];")
    assert sw[0] <= sw[1], sw


@browser
def test_reduced_motion_shows_the_clean_end_state():
    import json, subprocess, tempfile, html as _h
    from pathlib import Path
    tl = _scene([dict(CARD, id="g1", glitch={"shift": 12}, place={"x": 10, "y": 10, "w": 60})], [{"target": "g1", "keys": [{"t": 0, "p": 0}, {"t": 4, "p": 1}]}])
    page = ("<!doctype html><meta charset=utf-8><body style='margin:0'>" + _py(tl)
            + "<script>document.documentElement.setAttribute('data-probe', JSON.stringify((function(){" + _JS + "})()));</script>")
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "p.html"
        f.write_text(page)
        out = subprocess.run([CHROMIUM, "--headless=new", "--password-store=basic", "--no-sandbox", "--disable-gpu", "--force-prefers-reduced-motion", "--window-size=1000,700",
                              "--virtual-time-budget=1500", "--dump-dom", f"file://{f}#t=0.5"], capture_output=True, text=True, timeout=90).stdout
    m = re.search(r"data-probe='([^']*)'|data-probe=\"([^\"]*)\"", out)
    d = json.loads(_h.unescape(m.group(1) or m.group(2)))
    assert d["b"] == 1 and d["disp"] == "none", d


# ─── existing payloads, byte for byte against the renderer before the glitch prop ────────────────────────────
def _old_renderer():
    """renderers/web_article.py as of 18c8f2b8f (before glitch), loaded beside the real one; skipped if the commit is not in this clone."""
    import importlib.util, subprocess, sys
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    r = subprocess.run(["git", "-C", str(root), "show", "18c8f2b8f:renderers/web_article.py"], capture_output=True, text=True)
    if r.returncode:
        pytest.skip("18c8f2b8f not available")
    f = root / "renderers" / "_web_article_pre_glitch.py"
    f.write_text(r.stdout)
    try:
        spec = importlib.util.spec_from_file_location("renderers._web_article_pre_glitch", f)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
    finally:
        f.unlink()
    return mod


def _existing_payloads():
    import test_motion_atoms as A, test_motion_candidates as C, test_motion_expressive as E
    out = [A.TIMELINE, A.STITCHED, A.MORPHED, C.CARD, C.PILL, C.LIT, C.ARCS, C.LOCK, C.COLL, C.THEME_P, *C.FX, *C.TWIN_CASES]
    out += [c[1] if isinstance(c, tuple) else c for c in C.CASES]
    for P in (A.PAYLOADS, E.PAYLOADS):
        for t, bs in P.items():
            out += [dict(b, type=b.get("type", t)) for b in bs]
    return [b for b in out if isinstance(b, dict) and b.get("type")]


def test_existing_motion_payloads_render_byte_for_byte_as_before_the_glitch_prop():
    from renderers import web_article as wa
    old = _old_renderer()
    old._mo_install()
    wa._mo_install()
    pays = _existing_payloads()
    assert len(pays) > 150, len(pays)
    bad = []
    for b in pays:
        k = b.get("component") or b["type"]
        if k not in old._RENDERERS or "glitch" in b:
            continue
        try:
            a = old._RENDERERS[k](dict(b))
        except Exception:
            continue
        n = wa._RENDERERS[k](dict(b))
        if k == "motion_timeline":
            # the timeline's shared player script grew a branch for the `collapse` transition (I71): existing films behave the
            # same and only that script's text changed, so compare everything outside the <script> exactly
            a, n = (re.sub(r"<script>.*?</script>", "<script/>", x, flags=re.S) for x in (a, n))
        if k == "motion_scatter" and ' class="mosf' in n:
            # I74: from 3 cards up the scatter deliberately gained its fit stylesheet; 1-2 cards stay byte for byte (still compared here, and
            # in test_motion_scatter_fit.py against origin/main)
            continue
        if a != n:
            bad.append(k)
    assert not bad, bad[:10]


def test_a_tear_never_flashes_more_than_three_times():
    """WCAG 2.3.1 (three flashes, and the stricter red-flash rule for the red/cyan fringe): every slice swings at most 9 rad of
    sin over the whole tear, under 1.5 cycles, so a tear of any length has at most 3 flashes. Checked over many seeds and slice counts."""
    worst = 0.0
    for seed in range(0, 400, 7):
        for n in (2, 7, 12):
            h = _py(dict(PILL, glitch={"seed": seed, "slices": n}))
            for f in re.findall(r"sin\(calc\(var\(--p,1\)\*(\d+(?:\.\d+)?) \+", h):
                worst = max(worst, float(f))
    assert 0 < worst <= 9


def test_red_cyan_fringe_is_the_default_and_thin():
    h = _py(dict(PILL, glitch=True))
    assert "rgba(255,45,111,0.85)" in h and "rgba(25,211,255,0.85)" in h and "calc(2px*" in h
