"""Motion candidates from the keynote recordings (2026-10-10): halo, motion_lit, motion_collage, motion_arcs, panel silhouettes, inline marks, settle.

Same layers as test_motion_expressive.py: GAS and Python twins agree byte for byte, every option is inert when off, hostile input never becomes
markup, and a real browser shows the thing happening at fixed instants.
"""
from __future__ import annotations

import re

import pytest

from test_motion_atoms import CHROMIUM, _gas_batch, _norm, _probe, _py, _scene, browser, core_js  # noqa: F401

CARD = {"type": "demo_panel", "title": "Card", "rows": [["a", "1"]]}
PILL = {"type": "motion_pill", "text": "Go"}

CASES = [
    ("halo", dict(PILL, halo="#4f8cff")), ("halo", dict(PILL, halo=True)), ("halo", dict(PILL, halo={"color": "#ff5c9d", "size": 30, "strength": 0.8})),
    ("halo", dict(PILL, halo={"size": 0})), ("halo", dict(PILL, halo={"size": 999, "strength": 9})), ("halo", dict(PILL, halo={"size": "x", "strength": "y", "color": "red"})),
    ("halo", dict(PILL, halo="javascript:alert(1)")), ("halo", dict(PILL, halo=["#fff"])), ("halo", dict(CARD, halo=True, enter="rise")),
    ("halo", {"type": "motion_text", "text": "Hi", "halo": {"color": "#34e0c3", "size": 12}}),
]
CASES = [c for c in CASES]


def test_python_matches_gas_exactly(core_js):
    got = _gas_batch(core_js, [b for _t, b in CASES])
    bad = [(t, str(b)[:100]) for (t, b), g in zip(CASES, got) if _norm(_py(b)) != _norm(g)]
    assert not bad, bad


def test_halo_is_inert_when_off():
    plain = _py(dict(PILL))
    assert _norm(plain) == _norm(_py(dict(PILL, halo=False))) == _norm(_py(dict(PILL, halo=None))) == _norm(_py(dict(PILL, halo={"size": 0})))
    assert "mo-halo" not in plain


def test_halo_wraps_one_div_and_never_carries_payload_text():
    h = _py(dict(PILL, halo="#4f8cff"))
    assert h.count('class="mo-halo"') == 1 and "drop-shadow(0 0 calc(18px * var(--p,1)) rgba(79,140,255,0.55))" in h
    bad = _py(dict(PILL, halo={"color": 'red";}</style><script>1</script>', "size": 20}))
    assert "<script>1" not in bad and "rgba(91,140,255" in bad, "an invalid colour falls back to the default, it is not echoed"


@browser
def test_halo_blooms_with_p():
    tl = _scene([dict(PILL, id="p1", halo={"size": 30}, place={"x": 30, "y": 40, "w": 40})], [{"target": "p1", "keys": [{"t": 0, "p": 0}, {"t": 4, "p": 1}]}])
    js = "var e=document.querySelector('[data-mt-id=p1] .mo-halo');return e?getComputedStyle(e).filter:'';"
    start, end = _probe(tl, 0, js), _probe(tl, 4, js)
    r = lambda s: [float(x) for x in re.findall(r"\) 0px 0px ([0-9.]+)px", s)][:1]
    assert r(start) and r(start)[0] < 1 and r(end) and r(end)[0] > 25, (start, end)


# ---- helpers for atoms that exist only in the GAS renderer (preview, no Python twin) -------------------------------------------------------
def _probe_gas(core_js, block, t, js):
    import html as _h, json, subprocess, tempfile
    from pathlib import Path
    page = "<!doctype html><meta charset=utf-8><body style='margin:0'>" + _gas_batch(core_js, [block])[0] + "<script>document.documentElement.setAttribute('data-probe', JSON.stringify((function(){" + js + "})()));</script>"
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "p.html"; f.write_text(page)
        dump = subprocess.run([CHROMIUM, "--headless=new", "--password-store=basic", "--no-sandbox", "--disable-gpu", "--window-size=1000,700", "--virtual-time-budget=1500", "--dump-dom", f"file://{f}#t={t}"], capture_output=True, text=True, timeout=90).stdout
    m = re.search(r"data-probe='([^']*)'|data-probe=\"([^\"]*)\"", dump)
    assert m, dump[:300]
    return json.loads(_h.unescape(m.group(1) or m.group(2)))


LIT = {"type": "motion_lit", "blocks": [{"type": "demo_panel", "title": "Argon", "rows": [["use", "reasoning"]]}, {"type": "demo_panel", "title": "Flash", "rows": [["use", "speed"]]},
                                       {"type": "demo_panel", "title": "Omni", "rows": [["use", "media"]]}, {"type": "demo_panel", "title": "Gemma", "rows": [["use", "open"]]}]}


def test_lit_renders_every_card_and_reads_both_dials(core_js):
    h = _gas_batch(core_js, [LIT])[0]
    assert h.count('class="mlit-i"') == 4 and "var(--p,1)" in h and "var(--s,1)" in h and "<script" not in h.lower()
    assert "conic-gradient" in h and "conic-gradient" not in _gas_batch(core_js, [dict(LIT, edge=False)])[0]


def test_lit_options_are_closed_and_hostile_text_is_inert(core_js):
    att = '"><img src=x onerror=alert(1)><script>alert(2)</script>'
    h = _gas_batch(core_js, [dict(LIT, accent=att, layout=att, ghost=att, gap=att, blocks=[{"type": "motion_text", "text": att}])])[0]
    assert "<script>alert(2)" not in h and "<img" not in h and "onerror" not in h.replace("onerror=alert(1)&gt;", "")


@browser
def test_lit_ghosts_then_lights_in_turn(core_js):
    base = dict(LIT, id="lit", place={"x": 5, "y": 20, "w": 90})
    tl = lambda s_key: _scene([base], [{"target": "lit", "keys": [{"t": 0, "p": 1, "step": 0}, {"t": 4, "p": 1, "step": 1}]}])
    js = "var c=document.querySelectorAll('[data-mt-id=lit] .mlit-i');return Array.prototype.map.call(c,function(e){return +(+getComputedStyle(e).opacity).toFixed(2);});"
    t0, tmid, t1 = (_probe_gas(core_js, tl(0), t, js) for t in (0, 2, 4))
    assert all(abs(v - 0.3) < 0.05 for v in t0), t0                   # all ghosted at step 0
    assert tmid[0] > 0.95 and tmid[1] > 0.95 and tmid[3] < 0.5, tmid  # first two lit, last still ghost at half way
    assert all(v > 0.95 for v in t1), t1


@browser
def test_lit_ghost_cards_build_with_p(core_js):
    tl = _scene([dict(LIT, id="lit", place={"x": 5, "y": 20, "w": 90})], [{"target": "lit", "keys": [{"t": 0, "p": 0, "step": 0}, {"t": 4, "p": 1, "step": 0}]}])
    js = "var c=document.querySelectorAll('[data-mt-id=lit] .mlit-i');return Array.prototype.map.call(c,function(e){return +(+getComputedStyle(e).opacity).toFixed(2);});"
    a, b, c = (_probe_gas(core_js, tl, t, js) for t in (0, 2, 4))
    assert max(a) < 0.02 and 0.05 < b[0] <= 0.3 and b[3] < 0.1 and all(abs(v - 0.3) < 0.05 for v in c), (a, b, c)


# ---- motion_morph panel silhouettes and aspect -------------------------------------------------------------------------------------------------
MORPH_CASES = [("morph", {"type": "motion_morph", "shapes": ["panel", "notch"], "aspect": 1.78}), ("morph", {"type": "motion_morph", "shapes": ["notch", "step", "tab", "panel"]}),
               ("morph", {"type": "motion_morph", "shapes": ["panel", "circle"], "aspect": 99}), ("morph", {"type": "motion_morph", "shapes": ["panel", "tab"], "aspect": "x"}),
               ("morph", {"type": "motion_morph", "shapes": ["square", "star"]})]


def test_morph_panels_agree_between_twins(core_js):
    got = _gas_batch(core_js, [b for _t, b in MORPH_CASES])
    bad = [str(b)[:90] for (_t, b), g in zip(MORPH_CASES, got) if _norm(_py(b)) != _norm(g)]
    assert not bad, bad


def test_morph_default_output_is_unchanged_by_the_new_option():
    h = _py({"type": "motion_morph", "shapes": ["square", "star"]})
    assert "aspect-ratio:1/1" in h and _norm(h) == _norm(_py({"type": "motion_morph", "shapes": ["square", "star"], "aspect": 1}))
    assert "aspect-ratio:1.78" in _py({"type": "motion_morph", "shapes": ["panel", "notch"], "aspect": 1.78})
    assert "aspect-ratio:3" in _py({"type": "motion_morph", "shapes": ["panel", "notch"], "aspect": 99})


def test_every_new_silhouette_has_48_points_that_start_at_the_top_and_stay_inside_the_box():
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from renderers.web_article import _MO_SHAPES
    for name in ("panel", "notch", "step", "tab"):
        pts = _MO_SHAPES[name]
        assert len(pts) == 96, name
        assert pts[0] == 500, name                                   # starts at x = 50, on the top edge
        assert all(0 <= v <= 1000 for v in pts), name
        ys = pts[1::2]; assert pts[1] == min(ys[:8]) or name == "tab", name


@browser
def test_morph_reshapes_the_clip_path_with_p():
    tl = _scene([{"type": "motion_morph", "id": "m1", "shapes": ["panel", "notch"], "aspect": 1.78, "place": {"x": 10, "y": 10, "w": 60}}], [{"target": "m1", "keys": [{"t": 0, "p": 0}, {"t": 4, "p": 1}]}])
    js = "var e=document.querySelector('[data-mt-id=m1] div[style*=clip-path]');return e?getComputedStyle(e).clipPath:'';"
    a, b = _probe(tl, 0, js), _probe(tl, 4, js)
    assert a.startswith("polygon(") and b.startswith("polygon(") and a != b, (a[:80], b[:80])


# ---- motion_arcs and motion_lockup ------------------------------------------------------------------------------------------------------------
ARCS = {"type": "motion_arcs", "arcs": [{"color": "#5b8cff", "color2": "#34e0c3", "r": 34, "from": 200, "sweep": 200, "width": 12}, {"color": "#ff5c9d", "r": 22, "from": 20, "sweep": 250, "dx": -12, "dy": 14}]}
LOCK = {"type": "motion_lockup", "size": 60, "lines": [["The", "new", {"mark": {"arcs": ARCS["arcs"], "label": "a mark"}}, "way"], ["to", "cloud."]]}


def test_arcs_render_one_circle_per_arc_and_read_p(core_js):
    h = _gas_batch(core_js, [ARCS])[0]
    assert h.count("<circle") == 2 and "var(--p,1)" in h and 'role="img"' in h and "<script" not in h.lower() and "linearGradient" in h
    assert _gas_batch(core_js, [{"type": "motion_arcs"}])[0].count("<circle") == 1


def test_lockup_has_one_name_one_mark_and_hides_the_visual(core_js):
    h = _gas_batch(core_js, [LOCK])[0]
    assert h.count("<svg") == 1 and 'aria-label="The new a mark way to cloud."' in h and 'aria-hidden="true"' in h and "translateY(calc((2 - (" in h
    assert "translateY(calc((2 -" not in _gas_batch(core_js, [dict(LOCK, settle=False)])[0]


def test_arcs_and_lockup_options_are_closed_and_text_is_inert(core_js):
    att = '"><img src=x onerror=alert(1)><script>alert(2)</script>'
    arc = {"type": "motion_arcs", "label": att, "arcs": [{"color": att, "color2": att, "r": att, "from": att, "sweep": att, "width": att, "dx": att, "spin": att, "blur": att}]}
    lk = {"type": "motion_lockup", "size": att, "weight": att, "font": att, "color": att, "align": att, "line_height": att, "lines": [[att, {"mark": {"arcs": [{"color": att}], "label": att}}]]}
    for h in _gas_batch(core_js, [arc, lk]):
        assert "<script>alert(2)" not in h and "<img" not in h and "NaN" not in h


@browser
def test_arcs_turn_in_blurred_and_settle(core_js):
    tl = _scene([dict(ARCS, id="arcs", place={"x": 30, "y": 20, "w": 30})], [{"target": "arcs", "keys": [{"t": 0, "p": 0}, {"t": 4, "p": 1}]}])
    js = "var c=document.querySelectorAll('[data-mt-id=arcs] circle');return Array.prototype.map.call(c,function(e){var s=getComputedStyle(e);return [+(+s.opacity).toFixed(2),s.filter,s.transform];});"
    a, b = _probe_gas(core_js, tl, 0, js), _probe_gas(core_js, tl, 4, js)
    assert all(x[0] < 0.02 for x in a) and all(x[0] > 0.98 for x in b), (a, b)
    assert all("blur(0px)" in x[1] or x[1] in ("none", "blur(0px)") for x in b) and any("blur(" in x[1] and "blur(0px)" not in x[1] for x in a), (a, b)


@browser
def test_lockup_mark_first_then_words_and_block_recentres(core_js):
    tl = _scene([dict(LOCK, id="lk", place={"x": 5, "y": 25, "w": 90})], [{"target": "lk", "keys": [{"t": 0, "p": 0}, {"t": 4, "p": 1}]}])
    js = ("var r=document.querySelector('[data-mt-id=lk] [role=img]');var sp=r.querySelectorAll('div[aria-hidden] > div > span');"
          "return {o:Array.prototype.map.call(sp,function(e){return +(+getComputedStyle(e).opacity).toFixed(2);}),ty:new DOMMatrix(getComputedStyle(r).transform).m42};")
    a, mid, z = (_probe_gas(core_js, tl, t, js) for t in (0, 1.2, 4))
    assert max(a["o"]) < 0.02 and a["ty"] > 40, a                       # nothing visible, block pushed down half of two lines (about 69 px)
    assert mid["o"][2] > mid["o"][0] and 0 < mid["ty"] < a["ty"], mid    # the mark (third token of line one) is ahead of "The"; the block has started to rise
    assert all(v > 0.98 for v in z["o"]) and abs(z["ty"]) < 0.5, z       # everything arrived, block at rest


COLL = {"type": "motion_collage", "sets": [
    {"panel": "panel", "tiles": [{"x": 5, "y": 5, "w": 40, "h": 40, "label": "One"}, {"x": 50, "y": 5, "w": 45, "h": 40, "label": "Two"}]},
    {"panel": "notch", "tiles": [{"x": 5, "y": 50, "w": 90, "h": 40, "label": "Three"}]}]}


def test_collage_renders_and_hostile_input_is_inert(core_js):
    att = '"><img src=x onerror=alert(1)><script>alert(2)</script>'
    h, e = _gas_batch(core_js, [COLL, {"type": "motion_collage", "title": att, "blur": att, "ghost": att, "radius": att, "aspect": att, "fill": att,
                                       "sets": [{"panel": att, "tiles": [{"x": att, "y": att, "w": att, "h": att, "fill": att, "label": att}]}, "x", 5]}])
    assert h.count("polygon(") == 2 and "One" in h and "Three" in h and 'aria-hidden="true"' in h and "<script" not in h.lower()
    assert "<script>alert(2)" not in e and "<img" not in e and "NaN" not in e


@browser
def test_collage_swaps_sets_and_reshapes_the_panel(core_js):
    tl = _scene([dict(COLL, id="cl", place={"x": 5, "y": 5, "w": 60})], [{"target": "cl", "keys": [{"t": 0, "p": 1, "step": 0}, {"t": 4, "p": 1, "step": 1}]}])
    js = ("var w=document.querySelectorAll('[data-mt-id=cl] div[aria-hidden] > div[style*=max]');var p=document.querySelector('[data-mt-id=cl] div[style*=clip-path]');"
          "return {o:Array.prototype.map.call(w,function(e){return +(+getComputedStyle(e).opacity).toFixed(2);}),c:getComputedStyle(p).clipPath};")
    a, mid, z = (_probe_gas(core_js, tl, t, js) for t in (0, 1.8, 4))
    assert a["o"][0] > 0.98 and a["o"][1] < 0.3, a              # first set shown, the next only a ghost at most
    assert 0.1 < mid["o"][1] < 1 or mid["o"][0] < 0.98, mid     # mid-swap one of them is in transit
    assert z["o"][0] < 0.02 and z["o"][1] > 0.98, z             # last set shown
    assert a["c"] != z["c"], (a["c"], z["c"])                   # outline changed
