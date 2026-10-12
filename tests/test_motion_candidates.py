"""Motion candidates from the keynote recordings (2026-10-10): halo, motion_lit, motion_collage, motion_arcs, panel silhouettes, inline marks, settle.

Same layers as test_motion_expressive.py: GAS and Python twins agree byte for byte, every option is inert when off, hostile input never becomes
markup, and a real browser shows the thing happening at fixed instants.
"""
from __future__ import annotations

import re
from pathlib import Path

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


# ─── second batch: smear, tilt, bubbles, beats, pattern, dock, fit ───────────────────────────────────────────────
FX = [dict(PILL, smear=True), dict(PILL, smear="x"), dict(PILL, smear={"axis": "x", "amount": 1, "blur": 30}), dict(PILL, smear={"amount": 0, "blur": 0}), dict(PILL, smear={"amount": "x", "blur": 999}),
      dict(PILL, tilt=True), dict(PILL, tilt={"x": -30, "y": 40, "blur": 4}), dict(PILL, tilt={"x": 0, "y": 0, "blur": 0}), dict(PILL, tilt={"x": 999, "y": "z", "blur": -3}), dict(PILL, tilt="javascript:1"),
      dict(PILL, halo=True, smear=True, tilt=True)]


def test_smear_and_tilt_twins_agree(core_js):
    got = _gas_batch(core_js, FX)
    bad = [(str(b)[:90]) for b, g in zip(FX, got) if _norm(_py(b)) != _norm(g)]
    assert not bad, bad


def test_smear_and_tilt_are_inert_when_off_and_scale_with_p():
    plain = _norm(_py(dict(PILL)))
    assert plain == _norm(_py(dict(PILL, smear=False, tilt=None))) == _norm(_py(dict(PILL, smear={"amount": 0, "blur": 0}, tilt={"x": 0, "y": 0, "blur": 0})))
    h = _py(dict(PILL, smear=True, tilt=True))
    assert h.count("mo-smear") == 1 and h.count("mo-tilt") == 1 and h.count("var(--p,1)") >= 5 and "<script" not in h.lower()


B2 = {
    "bubbles": {"type": "motion_bubbles", "count": 5, "seed": 3},
    "beats": {"type": "motion_beats", "items": [{"text": "4", "bg": "#101010", "color": "#8a8aff"}, {"text": "5", "bg": "#2020c0", "color": "#ffffff", "shape": "star"}, {"text": "6", "bg": "#6a7d4a", "color": "#e6ff3a", "font": "serif"}]},
    "pattern": {"type": "motion_pattern", "text": "Made by Google", "rows": 3, "repeat": 3},
    "dock": {"type": "motion_dock", "items": [{"glyph": "M", "label": "Maps"}, {"glyph": "C", "label": "Chat"}, {"glyph": "31", "label": "Calendar"}]},
    "fit": {"type": "motion_fit", "text": "Live"},
}


def test_batch2_render_with_one_name_and_no_script(core_js):
    out = dict(zip(B2, _gas_batch(core_js, list(B2.values()))))
    for k, h in out.items():
        assert "<script" not in h.lower() and "NaN" not in h and "undefined" not in h, k
    assert 'aria-hidden="true"' in out["bubbles"] and 'role="img"' not in out["bubbles"] and 'role="img"' in _gas_batch(core_js, [dict(B2["bubbles"], label="Bubbles")])[0]
    assert out["beats"].count('role="img"') == 1 and 'aria-label="4, 5, 6"' in out["beats"] and out["beats"].count("<polygon") == 0 and "clip-path:polygon(" in out["beats"]
    assert out["pattern"].count('role="img"') == 1 and 'aria-label="Made by Google"' in out["pattern"] and out["pattern"].count("Made by Google") == 10
    assert "<ul" in out["dock"] and out["dock"].count("<li") == 3 and "Maps" in out["dock"] and out["dock"].count('aria-hidden="true"') == 4   # ring plus three glyphs
    assert ">LIVE<" not in out["fit"] and ">Live<" in out["fit"] and "text-transform:uppercase" in out["fit"] and "aria-hidden" not in out["fit"]


def test_batch2_options_are_closed_and_text_is_inert(core_js):
    att = '"><img src=x onerror=alert(1)><script>alert(2)</script>'
    hostile = [
        {"type": "motion_bubbles", "count": att, "seed": att, "size": att, "drift": att, "color": att, "color2": att, "aspect": att, "label": att},
        {"type": "motion_beats", "size": att, "weight": att, "transition": att, "aspect": att, "items": [{"text": att, "bg": att, "color": att, "font": att, "shape": att}, "x", 7, None]},
        {"type": "motion_pattern", "text": att, "rows": att, "repeat": att, "angle": att, "size": att, "slide": att, "color": att, "weight": att, "font": att, "aspect": att, "label": att},
        {"type": "motion_dock", "size": att, "fill": att, "accent": att, "items": [{"glyph": att, "label": att, "fill": att}, "x", 3]},
        {"type": "motion_fit", "text": att, "fill": att, "upper": att, "recede": att, "color": att, "weight": att, "font": att},
    ]
    for h in _gas_batch(core_js, hostile):
        assert "<script>alert(2)" not in h and "<img" not in h and "NaN" not in h, h[:200]
    for h in _gas_batch(core_js, [{"type": t} for t in ("motion_bubbles", "motion_beats", "motion_pattern", "motion_dock", "motion_fit")]):
        assert len(h) > 40 and "NaN" not in h


@browser
def test_beats_cut_on_the_step_dial_and_hold_the_last(core_js):
    tl = _scene([dict(B2["beats"], id="bt", place={"x": 5, "y": 5, "w": 60})], [{"target": "bt", "keys": [{"t": 0, "p": 1, "step": 0}, {"t": 6, "p": 1, "step": 1}]}])
    js = "var L=document.querySelectorAll('[data-mt-id=bt] [aria-hidden] > div');return Array.prototype.map.call(L,function(e){return +(+getComputedStyle(e).opacity).toFixed(2);});"
    a, m1, m2, z = (_probe_gas(core_js, tl, t, js) for t in (0, 2.0, 3.0, 6))
    assert a == [1, 0, 0] and m1 == [0, 1, 0] and m2[2] == 0 and m2[1] == 1 or m2 == [0, 0, 1], (a, m1, m2)
    assert z == [0, 0, 1], z


@browser
def test_dock_ring_travels_and_icons_pop_in(core_js):
    tl = _scene([dict(B2["dock"], id="dk", place={"x": 5, "y": 5, "w": 60})], [{"target": "dk", "keys": [{"t": 0, "p": 0, "step": 0}, {"t": 2, "p": 1, "step": 0}, {"t": 6, "p": 1, "step": 1}]}])
    js = ("var r=document.querySelector('[data-mt-id=dk] span[aria-hidden][style*=box-shadow]');var li=document.querySelectorAll('[data-mt-id=dk] li');"
          "return {x:new DOMMatrix(getComputedStyle(r).transform).m41,o:Array.prototype.map.call(li,function(e){return +(+getComputedStyle(e).opacity).toFixed(2);})};")
    a, b, z = (_probe_gas(core_js, tl, t, js) for t in (0, 2, 6))
    assert max(a["o"]) < 0.02 and all(v > 0.98 for v in b["o"]), (a, b)
    assert abs(b["x"]) < 0.5 and abs(z["x"] - 2 * 56) < 1, (b, z)


@browser
def test_bubbles_grow_with_p_and_drift_with_s(core_js):
    tl = _scene([dict(B2["bubbles"], id="bb", place={"x": 5, "y": 5, "w": 60})], [{"target": "bb", "keys": [{"t": 0, "p": 0, "step": 0}, {"t": 2, "p": 1, "step": 0}, {"t": 6, "p": 1, "step": 1}]}])
    js = "var s=document.querySelectorAll('[data-mt-id=bb] span');return {o:+(+getComputedStyle(s[0]).opacity).toFixed(2),x:new DOMMatrix(getComputedStyle(s[0]).transform).m41};"
    a, b, z = (_probe_gas(core_js, tl, t, js) for t in (0, 2, 6))
    assert a["o"] < 0.02 and b["o"] > 0.6 and abs(b["x"]) < 0.5 and abs(z["x"]) > 1, (a, b, z)


@browser
def test_fit_fills_the_width_and_recedes_only_when_asked(core_js):
    base = dict(B2["fit"], id="ft", place={"x": 5, "y": 20, "w": 90})
    js = "var d=document.querySelector('[data-mt-id=ft] div[style*=container-type]');var t=d.firstElementChild;return {f:t.scrollWidth/d.clientWidth,o:+(+getComputedStyle(t).opacity).toFixed(2)};"
    tl = lambda blk: _scene([blk], [{"target": "ft", "keys": [{"t": 0, "p": 1, "step": 0}, {"t": 4, "p": 1, "step": 1}]}])
    plain, rec = _probe_gas(core_js, tl(base), 4, js), _probe_gas(core_js, tl(dict(base, recede=True)), 4, js)
    assert 0.6 < plain["f"] <= 1.02 and plain["o"] > 0.98, plain
    assert rec["o"] < 0.5, rec


def test_long_data_image_urls_survive_the_url_guard_and_long_web_urls_do_not(core_js):
    import base64
    from test_motion_atoms import wa
    big = "data:image/jpeg;base64," + base64.b64encode(bytes(range(256)) * 40).decode()      # about 13.7 KB
    web = "https://example.com/" + "a" * 3000
    blk = {"type": "motion_image", "url": big}
    assert len(big) > 2048
    assert wa._gd_clean(dict(blk), "") ["url"] == big and "url" not in wa._gd_clean({"type": "motion_image", "url": web}, "")
    h = _gas_batch(core_js, [blk, {"type": "motion_image", "url": web}, {"type": "motion_image", "url": "data:image/svg+xml;base64," + "A" * 5000}])
    assert "<img" in h[0] and "<img" not in h[1] and "<img" not in h[2]


def test_motion_image_fit_contain_shows_the_whole_picture(core_js):
    blk = {"type": "motion_image", "url": "https://example.com/a.jpg", "fit": "contain"}
    g = _gas_batch(core_js, [blk, dict(blk, fit="x"), {"type": "motion_image", "url": blk["url"]}])
    assert "object-fit:contain" in g[0] and "object-fit:contain" not in g[1] and g[1] == g[2]
    assert _norm(_py(blk)) == _norm(g[0]) and _norm(_py({"type": "motion_image", "url": blk["url"]})) == _norm(g[2])


def test_collage_layouts_place_tiles_without_overlap_or_overflow():
    import re as _re
    src = (Path(__file__).resolve().parent.parent / "apps-script-surface" / "gas-wired-renderer" / "atoms_motion_candidates.gs").read_text()
    body = src[src.index("var _CL_LAYOUTS"):src.index("};", src.index("var _CL_LAYOUTS"))]
    lays = {m.group(1): [list(map(int, t.split(","))) for t in _re.findall(r"\[([\d, ]+)\]", m.group(2))] for m in _re.finditer(r"(\w+): \[(\[.*?\])\](?:,|\s*$)", body, _re.S)}
    assert set(lays) == {"hero", "rail", "grid", "split", "stack", "header", "trio", "mosaic"}, lays.keys()
    for name, ts in lays.items():
        for i, (x, y, w, h) in enumerate(ts):
            assert x >= 0 and y >= 0 and x + w <= 100 and y + h <= 100, (name, i)
            for (a, b, c, d) in ts[:i]:
                assert x >= a + c or a >= x + w or y >= b + d or b >= y + h, (name, i, "overlaps")


def test_collage_layout_names_tile_images_and_overrides(core_js):
    coll = {"type": "motion_collage", "sets": [
        {"layout": "grid", "tiles": [{"label": "A", "image": "https://example.com/a.jpg"}, {"label": "B"}, {"label": "C", "x": 70}]},
        {"layout": "nope", "panel": "tab", "tiles": [{"label": "D", "image": "javascript:alert(1)"}]}]}
    h = _gas_batch(core_js, [coll])[0]
    assert "left:5%;top:6%;width:43%;height:40%" in h and "left:52%;top:6%" in h and "left:70%;top:52%" in h      # grid places the three tiles, C's own x wins
    assert h.count("<img") == 1 and 'src="https://example.com/a.jpg"' in h and "javascript:" not in h and 'alt=""' in h
    assert "left:10%;top:10%;width:30%;height:30%" in h                                                          # an unknown layout falls back to the old default
    assert "<li>A</li>" in h and "<li>D</li>" in h                                                               # labels stay in the hidden list


# ── third batch from the screen recordings (2026-10-11): theme, dialog, dots, sweep ───────────────────────────────────────────────────────────
B3 = {
    "theme": {"type": "motion_theme", "blocks": [{"type": "callout", "variant": "info", "text": "Wall builder: 412 bricks"}]},
    "dialog": {"type": "motion_dialog", "title": "Confirm", "body": "Delete the draft?", "actions": [{"label": "Cancel"}, {"label": "Delete", "primary": True}]},
    "dots": {"type": "motion_dots", "from": "Done", "to": "Ask an agent"},
    "sweep": {"type": "motion_sweep", "blocks": [{"type": "demo_panel", "title": "Card", "rows": [["a", "1"]]}]},
}


def _dial(block, bid, keys):
    return _scene([dict(block, id=bid, place={"x": 5, "y": 5, "w": 60})], [{"target": bid, "keys": keys}])


def test_batch3_render_with_names_and_no_script(core_js):
    out = dict(zip(B3, _gas_batch(core_js, list(B3.values()))))
    for k, h in out.items():
        assert "<script" not in h.lower() and "NaN" not in h and "undefined" not in h, k
    assert out["dialog"].count('role="dialog"') == 1 and 'aria-label="Confirm"' in out["dialog"] and ">Delete the draft?<" in out["dialog"] and ">Cancel<" in out["dialog"]
    assert out["dots"].count('role="img"') == 1 and 'aria-label="ASK AN AGENT"' in out["dots"] and out["dots"].count("<circle") == 7 * (12 * 6 - 1)
    assert 'aria-hidden="true"' in out["sweep"] and "role=" not in out["sweep"]
    assert "color-mix(in srgb" in out["theme"] and "--bg:" in out["theme"]


def test_batch3_options_are_closed_and_text_is_inert(core_js):
    att = '"><img src=x onerror=alert(1)><script>alert(2)</script>'
    hostile = [
        {"type": "motion_theme", "from": att, "to": att, "blocks": [att, 3, None]},
        {"type": "motion_dialog", "title": att, "body": att, "enter": att, "dim": att, "scrim": att, "aspect": att, "actions": [{"label": att, "primary": att}, "x", 4]},
        {"type": "motion_dots", "from": att, "to": att, "color": att, "color2": att, "grid": att, "label": att},
        {"type": "motion_sweep", "angle": att, "width": att, "strength": att, "color": att, "blocks": [att, 1]},
    ]
    for h in _gas_batch(core_js, hostile):
        assert "<script>alert(2)" not in h and "<img" not in h and "NaN" not in h, h[:200]
    for h in _gas_batch(core_js, [{"type": t} for t in ("motion_theme", "motion_dialog", "motion_dots", "motion_sweep")]):
        assert len(h) > 30 and "NaN" not in h


@browser
def test_theme_morphs_between_the_two_palettes_on_the_step_dial(core_js):
    keys = [{"t": 0, "p": 1, "step": 0}, {"t": 2, "p": 1, "step": 0.5}, {"t": 6, "p": 1, "step": 1}]
    js = "var c=getComputedStyle(document.querySelector('[data-mt-id=th] > div')).backgroundColor.match(/[\\d.]+/g).map(Number);var k=c.some(function(v){return v>1;})?1:255;return c.slice(0,3).map(function(v){return Math.round(v*k);});"
    a, m, z = (_probe_gas(core_js, _dial(B3["theme"], "th", keys), t, js) for t in (0, 2, 6))
    assert a == [11, 15, 20] and z == [247, 248, 250], (a, z)
    assert all(abs(m[i] - (a[i] + z[i]) / 2) < 3 for i in range(3)), m


@browser
def test_dialog_scrim_then_dialog_enter_and_rest(core_js):
    keys = [{"t": 0, "p": 0}, {"t": 2, "p": 0.2}, {"t": 6, "p": 1}]
    js = ("var d=document.querySelector('[data-mt-id=dg] [role=dialog]');var s=d.previousElementSibling;"
          "return {d:+(+getComputedStyle(d).opacity).toFixed(2),s:+(+getComputedStyle(s).opacity).toFixed(2)};")
    a, b, z = (_probe_gas(core_js, _dial(B3["dialog"], "dg", keys), t, js) for t in (0, 2, 6))
    assert a == {"d": 0, "s": 0}, a
    assert b["s"] > 0.44 and b["d"] < 0.02, b      # scrim done, dialog not started
    assert z["d"] == 1 and z["s"] > 0.44, z


@browser
def test_dots_resolve_from_one_phrase_to_the_other(core_js):
    keys = [{"t": 0, "p": 1, "step": 0}, {"t": 6, "p": 1, "step": 1}]
    blk = {"type": "motion_dots", "from": "A", "to": "B", "grid": False}
    js = "var c=document.querySelectorAll('[data-mt-id=dt] circle');var o=Array.prototype.map.call(c,function(e){return +getComputedStyle(e).opacity;});return {n:o.length,lit:o.filter(function(v){return v>0.9;}).length};"
    a, z = (_probe_gas(core_js, _dial(blk, "dt", keys), t, js) for t in (0, 6))
    assert a["n"] == z["n"] and a["n"] > 20, (a, z)
    assert a["lit"] > 10 and z["lit"] > 10, (a, z)


@browser
def test_sweep_rests_off_both_edges_and_crosses_in_between(core_js):
    keys = [{"t": 0, "p": 1, "step": 0}, {"t": 2, "p": 1, "step": 0.5}, {"t": 6, "p": 1, "step": 1}]
    js = ("var w=document.querySelector('[data-mt-id=sw] > div');var b=w.lastElementChild.getBoundingClientRect(),r=w.getBoundingClientRect();"
          "return {left:b.right<r.left+1,right:b.left>r.right-1,inside:b.left<r.right&&b.right>r.left};")
    a, m, z = (_probe_gas(core_js, _dial(B3["sweep"], "sw", keys), t, js) for t in (0, 2, 6))
    assert a["left"] and not a["inside"], a
    assert m["inside"], m
    assert z["right"] and not z["inside"], z


@browser
def test_theme_ink_never_matches_the_surface(core_js):
    # sample the step dial finely; the contrast between --text and --bg must stay >= 2.9:1 and the ends must be the full palettes
    js = ("function rgb(c){var m=c.match(/[\\d.]+/g).map(Number);var k=m.some(function(v){return v>1;})?1:255;return m.slice(0,3).map(function(v){return v*k;});}"
          "function L(c){return c.map(function(v){v/=255;return v<=0.03928?v/12.92:Math.pow((v+0.055)/1.055,2.4);}).reduce(function(a,v,i){return a+v*[0.2126,0.7152,0.0722][i];},0);}"
          "var el=document.querySelector('[data-mt-id=th] > div');var cs=getComputedStyle(el);return {bg:rgb(cs.backgroundColor),fg:rgb(cs.color)};")
    worst = 99
    for step in (0, 0.2, 0.4, 0.45, 0.5, 0.55, 0.6, 0.8, 1):
        keys = [{"t": 0, "p": 1, "step": step}, {"t": 6, "p": 1, "step": step}]
        r = _probe_gas(core_js, _dial(B3["theme"], "th", keys), 1, js)

        def lum(c):
            f = [(v / 255 / 12.92) if v / 255 <= 0.03928 else ((v / 255 + 0.055) / 1.055) ** 2.4 for v in c]
            return 0.2126 * f[0] + 0.7152 * f[1] + 0.0722 * f[2]
        a, b = sorted((lum(r["bg"]), lum(r["fg"])), reverse=True)
        worst = min(worst, (a + 0.05) / (b + 0.05))
    assert worst >= 2.9, worst


# ── Python twins of the 13 candidate atoms (9 keynote + 4 screen-recording) must match the GAS renderer byte for byte ─────────────────────────
def _norm_all(h: str) -> str:
    h = _norm(h)
    for i, uid in enumerate(dict.fromkeys(re.findall(r'mar([a-z0-9]{6})\d', h))):   # gradient ids in arcs carry the random uid in GAS
        h = h.replace(uid, f"UID{i}")
    return h


_ATT = '"><img src=x onerror=alert(1)><script>alert(2)</script>'
# demo_panel children: the callout atom itself still differs between the two renderers (class versus inline style), which is not what this test is about
THEME_P = {"type": "motion_theme", "blocks": [{"type": "demo_panel", "title": "Wall", "rows": [["bricks", "412"]]}]}
TWIN_CASES = [
    LIT, dict(LIT, layout="grid", edge=False, ghost=0.5, gap=4), {"type": "motion_lit"}, ARCS, {"type": "motion_arcs"}, dict(ARCS, label="Brand"), LOCK, dict(LOCK, settle=False, align="start", weight="black", font="serif"),
    {"type": "motion_lockup"}, {"type": "motion_lockup", "lines": [["a", "b"], ["c"], [{"mark": {}}, "d"]]},
    COLL, {"type": "motion_collage"}, dict(COLL, title="T", blur=3, ghost=0.4, radius=0, aspect=1.2, fill="#112233"),
    *B2.values(), dict(B2["bubbles"], label="B", count=14, seed=999, size=40, drift=60), dict(B2["beats"], transition="fade", size=80, weight="bold"), dict(B2["pattern"], rows=1, repeat=1, angle=45, label="x"),
    dict(B2["dock"], size=24), dict(B2["fit"], recede=True, upper=False), {"type": "motion_beats"}, {"type": "motion_dock"}, {"type": "motion_pattern"}, {"type": "motion_bubbles"}, {"type": "motion_fit"},
    *(v for k, v in B3.items() if k != "theme"), THEME_P, dict(THEME_P, **{"from": "light", "to": "dark"}), dict(THEME_P, **{"from": "dark", "to": "dark"}), dict(B3["dialog"], enter="rise", dim=0.8, scrim="#102030", aspect=2.4), dict(B3["dialog"], enter="fade"),
    {"type": "motion_dots", "from": "Ok!", "to": "A-B? 9,0.", "grid": False, "color": "#ff0000", "color2": "#00ff00", "label": "L"}, {"type": "motion_dots", "from": "x", "to": "y"}, dict(B3["sweep"], angle=45, width=60, strength=0.8, color="#ff00ff"),
    {"type": "motion_theme"}, {"type": "motion_dialog"}, {"type": "motion_dots"}, {"type": "motion_sweep"},
    {"type": "motion_lit", "layout": _ATT, "ghost": _ATT, "gap": _ATT, "edge": _ATT, "accent": _ATT, "blocks": [_ATT, 3, None]},
    {"type": "motion_arcs", "label": _ATT, "arcs": [{"color": _ATT, "color2": "#fff000", "r": _ATT, "from": _ATT, "sweep": _ATT, "width": _ATT, "dx": _ATT, "spin": _ATT, "blur": _ATT}, "x", 7]},
    {"type": "motion_lockup", "size": _ATT, "lines": [[_ATT, {"mark": {"arcs": [{"color": _ATT}], "label": _ATT}}, 5, None], "x", [" "]]},
    {"type": "motion_collage", "sets": [{"tiles": [{"x": _ATT, "label": _ATT, "image": _ATT, "block": {"type": "nope"}}, "x"], "layout": _ATT, "panel": _ATT}, 4]},
    {"type": "motion_bubbles", "count": _ATT, "seed": _ATT, "label": _ATT}, {"type": "motion_beats", "items": [{"text": _ATT, "shape": _ATT, "font": _ATT}, "x", 3]},
    {"type": "motion_pattern", "text": _ATT, "rows": _ATT, "label": _ATT}, {"type": "motion_dock", "items": [{"glyph": _ATT, "label": _ATT}, 1]}, {"type": "motion_fit", "text": _ATT, "fill": _ATT},
    {"type": "motion_theme", "blocks": [_ATT, 1], "from": _ATT}, {"type": "motion_dialog", "title": _ATT, "body": _ATT, "actions": [{"label": _ATT, "primary": True}, "x"], "enter": _ATT},
    {"type": "motion_dots", "from": _ATT, "to": _ATT, "label": _ATT}, {"type": "motion_sweep", "blocks": [_ATT], "angle": _ATT, "color": _ATT},
]


def test_python_twins_of_all_candidate_atoms_match_gas_exactly(core_js):
    got = _gas_batch(core_js, TWIN_CASES)
    bad = [(b.get("type"), i) for i, (b, g) in enumerate(zip(TWIN_CASES, got)) if _norm_all(_py(b)) != _norm_all(g)]
    assert not bad, bad


# ── Material's sequenced hand-overs: fade-through, shared-x, shared-y, shared-z ─────────────────────────────────────────────────────────────
from test_motion_atoms import STITCHED  # noqa: E402

SEQ_FX = ("fade-through", "shared-x", "shared-y", "shared-z")
PLAIN = dict(STITCHED, scenes=[{"layer": "s1", "t": 0}, {"layer": "s2", "t": 3}, {"layer": "s3", "t": 6}])


def test_sequenced_stitches_agree_between_the_twins(core_js):
    cases = [dict(PLAIN, stitch=fx, overlap=ov) for fx in SEQ_FX for ov in (0.3, 0.6, 1.2)]
    cases += [dict(STITCHED, scenes=[{"layer": "s1", "t": 0}, {"layer": "s2", "t": 2, "transition": "shared-x"}, {"layer": "s3", "t": 4, "transition": "fade-through"}])]
    got = _gas_batch(core_js, cases)
    bad = [i for i, (b, g) in enumerate(zip(cases, got)) if _norm_all(_py(b)) != _norm_all(g)]
    assert not bad, bad


@browser
def test_sequenced_stitches_fade_out_first_then_in(core_js):
    # scene s2 starts at t=3 (STITCHED); overlap 1.0 -> out fades over 3.0-3.3, in fades 3.3-4.0, never both half visible
    js = ("function o(id){var e=document.querySelector('[data-mt-id='+id+']');return e?+(+getComputedStyle(e).opacity).toFixed(2):null;}return {a:o('s1'),b:o('s2')};")
    for fx in SEQ_FX:
        tl = dict(PLAIN, stitch=fx, overlap=1.0, autoplay=False, controls=False)
        mid_out = _probe_gas(core_js, tl, 3.12, js)    # inside the first 30%: old scene fading, new one not started
        mid_in = _probe_gas(core_js, tl, 3.6, js)      # old gone, new one coming up
        done = _probe_gas(core_js, tl, 4.2, js)
        assert mid_out["b"] is not None and mid_out["b"] < 0.02 and 0.0 < mid_out["a"] < 1.0, (fx, mid_out)
        assert mid_in["a"] is not None and mid_in["a"] < 0.02 and 0.0 < mid_in["b"] < 1.0, (fx, mid_in)
        assert done["b"] > 0.98 and done["a"] < 0.02, (fx, done)


def test_dissolve_is_unchanged_by_the_sequenced_stitches(core_js):
    assert _norm_all(_py(dict(STITCHED, stitch="dissolve"))) == _norm_all(_gas_batch(core_js, [dict(STITCHED, stitch="dissolve")])[0])


# ── fourth batch from a brand film: capsule, arrow, swatches, glass, wall, tag ──────────────────────────────────────────────────────
def _ps(block, bid, p=None, s=None):
    """A tiny film that holds p and/or s at fixed values, probed at t=1."""
    key = {"t": 0}
    if p is not None:
        key["p"] = p
    if s is not None:
        key["step"] = s
    return _dial(block, bid, [key, dict(key, t=6)])


@browser
def test_capsule_widens_as_words_land_and_is_not_clipped_at_the_end(core_js):
    blk = {"type": "motion_capsule", "text": "don't have resources at all", "size": 24}
    js = ("var c=document.querySelector('[data-mt-id=cp] > span');var w=c.querySelectorAll('span');var clipped=false;"
          "Array.prototype.forEach.call(w,function(e){if(e.scrollWidth>e.clientWidth+1)clipped=true;});return {w:Math.round(c.getBoundingClientRect().width),clipped:clipped};")
    a, m, z = (_probe_gas(core_js, _ps(blk, "cp", p=v), 1, js) for v in (0.2, 0.55, 1))
    assert a["w"] < m["w"] < z["w"], (a, m, z)
    assert not z["clipped"], z                      # the finished capsule shows every word in full, whatever the font does to the width estimate


@browser
def test_arrow_turns_through_its_directions_and_draws_with_p(core_js):
    blk = {"type": "motion_arrow", "angles": [0, 90, 180], "size": 80}
    js = "var s=document.querySelector('[data-mt-id=ar] svg');var m=new DOMMatrix(getComputedStyle(s).transform);return Math.round(Math.atan2(m.b,m.a)*180/Math.PI);"
    got = [_probe_gas(core_js, _ps(blk, "ar", p=1, s=v), 1, js) for v in (0, 0.5, 1)]
    assert got[0] == 0 and got[1] == 90 and abs(got[2]) == 180, got
    off = "return parseFloat(/-?[\\d.]+/.exec(getComputedStyle(document.querySelector('[data-mt-id=ar] path')).strokeDashoffset)[0]);"
    assert _probe_gas(core_js, _ps(blk, "ar", p=0, s=1), 1, off) > 0.99 and abs(_probe_gas(core_js, _ps(blk, "ar", p=1, s=1), 1, off)) < 0.01


@browser
def test_swatches_arrive_from_their_edges_and_every_label_is_readable(core_js):
    blk = {"type": "motion_swatches", "swatches": [{"name": "Indigo", "hex": "#475eff"}, {"name": "Mellow", "hex": "#f6cf77"}, {"name": "White", "hex": "#ffffff"}, {"name": "Black", "hex": "#111111"}]}
    js = ("var u=document.querySelector('[data-mt-id=sw] ul'),r=u.getBoundingClientRect();return Array.prototype.map.call(u.children,function(l){var b=l.getBoundingClientRect();"
          "return {out:b.right<=r.left+1||b.left>=r.right-1||b.bottom<=r.top+1||b.top>=r.bottom-1,o:+(+getComputedStyle(l).opacity).toFixed(2)};});")
    a, z = (_probe_gas(core_js, _ps(blk, "sw", p=v), 1, js) for v in (0, 1))
    assert all(x["out"] or x["o"] == 0 for x in a), a
    assert not any(x["out"] for x in z) and all(x["o"] == 1 for x in z), z
    from renderers import web_article as w
    def lum(h):
        c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    for hx in ("#475eff", "#f6cf77", "#ffffff", "#111111", "#ff0000", "#00ff00", "#808080", "#767676", "#0000ff", "#7f7f7f", "#a0a0a0"):
        ink = w._sw_ink(hx)
        hi, lo = sorted((lum(hx), lum(ink)), reverse=True)
        assert (hi + 0.05) / (lo + 0.05) >= 4.5, (hx, ink)   # white or black, whichever reads better: at least 4.58:1 on any colour


@browser
def test_glass_blur_grows_with_p(core_js):
    blk = {"type": "motion_glass", "blur": 20, "blocks": [{"type": "quiet_link", "text": "x"}]}
    js = "var e=document.querySelector('[data-mt-id=gl] > div');var f=getComputedStyle(e).backdropFilter||getComputedStyle(e).webkitBackdropFilter;var m=/blur\\(([\\d.]+)px/.exec(f);return {b:m?+(+m[1]).toFixed(1):null,o:+(+getComputedStyle(e).opacity).toFixed(2)};"
    a, m, z = (_probe_gas(core_js, _ps(blk, "gl", p=v), 1, js) for v in (0, 0.5, 1))
    assert a["o"] == 0 and z["o"] == 1 and z["b"] == 20 and 8 < m["b"] < 12, (a, m, z)


@browser
def test_wall_builds_with_p_and_thins_with_s_in_a_stable_order(core_js):
    blk = {"type": "motion_wall", "cols": 4, "rows": 2, "seed": 4}
    js = "return Array.prototype.map.call(document.querySelectorAll('[data-mt-id=wl] > div > span'),function(e){return +(+getComputedStyle(e).opacity).toFixed(2);});"
    built = _probe_gas(core_js, _ps(blk, "wl", p=0, s=1), 1, js)
    full = _probe_gas(core_js, _ps(blk, "wl", p=1, s=1), 1, js)
    half = _probe_gas(core_js, _ps(blk, "wl", p=1, s=0.5), 1, js)
    empty = _probe_gas(core_js, _ps(blk, "wl", p=1, s=0), 1, js)
    again = _probe_gas(core_js, _ps(blk, "wl", p=1, s=0.5), 1, js)
    assert len(full) == 8 and all(v == 0 for v in built) and all(v == 1 for v in full) and all(v == 0 for v in empty), (built, full, empty)
    assert 0 < sum(half) < 8 and half == again, half


@browser
def test_tag_dot_travels_then_the_pill_grows(core_js):
    blk = {"type": "motion_tag", "text": "services", "from": {"x": 10, "y": 20}, "to": {"x": 60, "y": 55}, "size": 24, "aspect": 2}
    js = ("var s=document.querySelector('[data-mt-id=tg] > div');var g=s.firstElementChild,r=s.getBoundingClientRect(),b=g.getBoundingClientRect();"
          "return {x:Math.round((b.left-r.left)/r.width*100),pill:Math.round(g.lastElementChild.getBoundingClientRect().width)};")
    a, m, z = (_probe_gas(core_js, _ps(blk, "tg", p=v), 1, js) for v in (0.01, 0.45, 1))
    assert abs(a["x"] - 10) <= 2 and abs(m["x"] - 60) <= 2 and abs(z["x"] - 60) <= 2, (a, m, z)
    assert a["pill"] < m["pill"] + 1 and m["pill"] < z["pill"] and z["pill"] > 60, (a, m, z)


# ── fifth batch from two motion-designer showreels: ring, highlight, meters, discs ────────────────────────────────────────────────────────────
@browser
def test_ring_turns_with_s_and_the_disc_grows_with_p(core_js):
    blk = {"type": "motion_ring", "text": "Reel", "turns": 1, "size": 300}
    ang = "var s=document.querySelector('[data-mt-id=rg] svg');var m=new DOMMatrix(getComputedStyle(s).transform);return Math.round(Math.atan2(m.b,m.a)*180/Math.PI);"
    a0, a5 = (_probe_gas(core_js, _ps(blk, "rg", p=1, s=v), 1, ang) for v in (0, 0.25))
    assert a0 == 0 and a5 == 90, (a0, a5)
    disc = "var d=document.querySelector('[data-mt-id=rg] [role=img] > div');return Math.round(d.getBoundingClientRect().width);"
    assert _probe_gas(core_js, _ps(blk, "rg", p=0, s=1), 1, disc) == 0 and _probe_gas(core_js, _ps(blk, "rg", p=1, s=1), 1, disc) > 100


@browser
def test_highlight_swipe_follows_p_and_the_words_stay_readable(core_js):
    blk = {"type": "motion_highlight", "text": "made tidy", "size": 48}
    js = ("var h=document.querySelector('[data-mt-id=hl] span span');var m=/inset\\(([\\d.]+)(?:px|%)? ([\\d.]+)%/.exec(getComputedStyle(h).clipPath);"
          "var w=document.querySelector('[data-mt-id=hl]').textContent.trim();return {right:m?+m[2]:null,text:w};")
    a, m, z = (_probe_gas(core_js, _ps(blk, "hl", p=v), 1, js) for v in (0, 0.5, 1))
    assert a["right"] == 100 and abs(m["right"] - 50) < 1 and z["right"] == 0 and z["text"] == "made tidy" == a["text"], (a, m, z)


@browser
def test_meters_rise_with_p_and_move_with_s(core_js):
    blk = {"type": "motion_meters", "bars": 8, "height": 200, "layout": "row"}
    js = "return Array.prototype.map.call(document.querySelectorAll('[data-mt-id=mt] [aria-hidden] > span'),function(e){return Math.round(e.getBoundingClientRect().height);});"
    empty = _probe_gas(core_js, _ps(blk, "mt", p=0, s=0.1), 1, js)
    a = _probe_gas(core_js, _ps(blk, "mt", p=1, s=0.1), 1, js)
    z = _probe_gas(core_js, _ps(blk, "mt", p=1, s=0.37), 1, js)
    assert len(a) == 8 and all(v == 0 for v in empty) and all(v > 0 for v in a) and a != z, (empty, a, z)
    assert len(set(a)) > 2, a       # the columns are not all the same height


@browser
def test_discs_slide_from_apart_to_overlapping(core_js):
    blk = {"type": "motion_discs", "discs": [{"color": "#f4d21f", "r": 24}, {"color": "#2e6fbd", "r": 24}], "aspect": 2}
    js = ("var d=document.querySelectorAll('[data-mt-id=ds] [aria-hidden] > span');var a=d[0].getBoundingClientRect(),b=d[1].getBoundingClientRect();"
          "return {gap:Math.round((b.left+b.width/2)-(a.left+a.width/2)),r:Math.round(a.width/2)};")
    apart, together = (_probe_gas(core_js, _ps(blk, "ds", p=1, s=v), 1, js) for v in (0, 1))
    assert apart["gap"] > 2 * apart["r"] > 0 and 0 < together["gap"] <= together["r"], (apart, together)


# ── sixth batch (food-brand, rebrand and studio films): dotgrid, blade, blueprint, tracking, tabs ──────────────────────────────────────────────
@browser
def test_dotgrid_token_starts_on_the_first_hop_and_rests_on_the_last(core_js):
    blk = {"type": "motion_dotgrid", "cols": 5, "rows": 4, "hops": [[0, 0], [2, 2], [4, 3]], "aspect": 1.25}
    js = ("var g=document.querySelector('[data-mt-id=dg] > div');var r=g.getBoundingClientRect(),t=g.children[1].firstElementChild.getBoundingClientRect();"
          "return {c:Math.round((t.left+t.width/2-r.left)/r.width*5-0.5),r:Math.round((t.top+t.height/2-r.top)/r.height*4-0.5)};")
    a, z = (_probe_gas(core_js, _ps(blk, "dg", p=1, s=v), 1, js) for v in (0, 1))
    assert (a["c"], a["r"]) == (0, 0) and (z["c"], z["r"]) == (4, 3), (a, z)


@browser
def test_blade_reveals_the_words_left_to_right_and_the_text_is_always_in_the_page(core_js):
    blk = {"type": "motion_blade", "text": "any recipe at all", "size": 48}
    js = ("var s=document.querySelector('[data-mt-id=bl] > span > span');var m=/inset\\(0(?:px)? (?:calc\\()?(-?[\\d.]+)%/.exec(getComputedStyle(s).clipPath);"
          "return {frac:m?+m[1]/100:null,text:s.textContent};")
    a, m, z = (_probe_gas(core_js, _ps(blk, "bl", p=1, s=v), 1, js) for v in (0, 0.5, 1))
    assert a["text"] == z["text"] == "any recipe at all" and a["frac"] > 0.95 and 0.4 < m["frac"] < 0.6 and z["frac"] <= 0.02, (a, m, z)


@browser
def test_blueprint_outline_is_visible_and_the_fill_arrives_late(core_js):
    blk = {"type": "motion_blueprint", "text": "atelier", "size": 100}
    js = ("var all=Array.prototype.slice.call(document.querySelector('[data-mt-id=bp]').querySelectorAll('span'));"
          "var out=all.filter(function(e){return getComputedStyle(e).webkitTextFillColor==='rgba(0, 0, 0, 0)';})[0],fill=all[all.length-1];"
          "return {stroke:getComputedStyle(out).webkitTextStrokeColor,strokeOp:+(+getComputedStyle(out).opacity).toFixed(2),fillOp:+(+getComputedStyle(fill).opacity).toFixed(2)};")
    a, m, z = (_probe_gas(core_js, _ps(blk, "bp", p=v), 1, js) for v in (0, 0.5, 1))
    assert a["strokeOp"] == 0 and m["strokeOp"] > 0 and m["fillOp"] < z["fillOp"] == 1 and z["stroke"] != "rgba(0, 0, 0, 0)", (a, m, z)


@browser
def test_tracking_opens_with_s(core_js):
    blk = {"type": "motion_tracking", "text": "open", "size": 40, "from": 0, "to": 0.4}
    js = "return parseFloat(getComputedStyle(document.querySelector('[data-mt-id=tk] span')).letterSpacing);"
    a, m, z = (_probe_gas(core_js, _ps(blk, "tk", p=1, s=v), 1, js) for v in (0, 0.5, 1))
    assert (a or 0) < 0.5 and abs(m - 8) < 1 and abs(z - 16) < 1, (a, m, z)


@browser
def test_tabs_underline_slides_from_first_to_last(core_js):
    blk = {"type": "motion_tabs", "items": ["a", "b", "c", "d"], "size": 20}
    js = "var t=document.querySelector('[data-mt-id=tb] > div');var u=t.lastElementChild.getBoundingClientRect(),r=t.getBoundingClientRect();return Math.round((u.left-r.left)/r.width*100);"
    a, m, z = (_probe_gas(core_js, _ps(blk, "tb", p=1, s=v), 1, js) for v in (0, 0.5, 1))
    assert a < m < z and abs(a - 4) <= 1 and abs(z - 79) <= 1, (a, m, z)


# ── showpiece pack: foil, wrap, drop, flag, disperse, reveal, streak ─────────────────────────────────────────────────────────────────────────────


@browser
def test_drop_letters_land_exactly_at_p1_and_are_displaced_before(core_js):
    for mode in ("bounce", "spring", "rain", "pile", "rise", "swing"):
        blk = {"type": "motion_drop", "text": "land", "mode": mode, "height": 120}
        js = "var o=[];document.querySelectorAll('[data-mt-id=dr] span[aria-hidden] span').forEach(function(s){var m=new DOMMatrix(getComputedStyle(s).transform);o.push(Math.abs(m.e)+Math.abs(m.f)+Math.abs(m.a-1)+Math.abs(m.b));});return o;"
        end = _probe_gas(core_js, _ps(blk, "dr", p=1), 1, js)
        mid = _probe_gas(core_js, _ps(blk, "dr", p=0.12), 1, js)
        assert max(end) < 0.05, (mode, end)
        assert max(mid) > 0.2, (mode, mid)


@browser
def test_flag_is_flat_at_both_ends_of_s_and_waves_between(core_js):
    for mode in ("flag", "ripple", "ribbon", "breeze"):
        blk = {"type": "motion_flag", "text": "wave me", "mode": mode, "amp": 30}
        js = "var o=[];document.querySelectorAll('[data-mt-id=fg] span[aria-hidden] span').forEach(function(s){var m=new DOMMatrix(getComputedStyle(s).transform);o.push(Math.abs(m.f));});return Math.max.apply(null,o);"
        a, m, z = (_probe_gas(core_js, _ps(blk, "fg", p=1, s=v), 1, js) for v in (0, 0.5, 1))
        assert a < 0.5 and z < 0.5 and m > 3, (mode, a, m, z)


@browser
def test_disperse_is_whole_at_s0_and_gone_at_s1(core_js):
    for mode in ("smoke", "shatter", "rise", "sink", "implode", "explode", "wind", "evaporate"):
        blk = {"type": "motion_disperse", "text": "leave", "mode": mode}
        js = "var o=[];document.querySelectorAll('[data-mt-id=dp] span[aria-hidden] span').forEach(function(s){o.push(parseFloat(getComputedStyle(s).opacity));});return [Math.min.apply(null,o),Math.max.apply(null,o)];"
        a = _probe_gas(core_js, _ps(blk, "dp", p=1, s=0), 1, js)
        z = _probe_gas(core_js, _ps(blk, "dp", p=1, s=1), 1, js)
        assert a[0] > 0.99, (mode, a)
        assert z[1] < 0.01, (mode, z)


@browser
def test_reveal_mask_opens_with_p(core_js):
    for mode in ("blinds", "slats", "iris", "clock", "halftone", "searchlight", "laser", "soft", "diagonal"):
        blk = {"type": "motion_reveal", "text": "open up", "mode": mode}
        js = "var s=document.querySelector('[data-mt-id=rv] > div > span');var c=getComputedStyle(s);return c.webkitMaskImage||c.maskImage||'';"
        a = _probe_gas(core_js, _ps(blk, "rv", p=0), 1, js)
        z = _probe_gas(core_js, _ps(blk, "rv", p=1), 1, js)
        assert a and z and a != z, (mode, a, z)
    blk = {"type": "motion_reveal", "text": "open up", "mode": "diamond"}
    js = "return getComputedStyle(document.querySelector('[data-mt-id=rv] > div > span')).clipPath;"
    assert _probe_gas(core_js, _ps(blk, "rv", p=0), 1, js) != _probe_gas(core_js, _ps(blk, "rv", p=1), 1, js)


@browser
def test_wrap_full_turn_returns_to_start_and_mid_turn_does_not(core_js):
    for form in ("cylinder", "wheel", "helix", "ribbon"):
        blk = {"type": "motion_wrap", "text": "spin", "form": form}
        js = "var r=document.querySelector('[data-mt-id=wr] [aria-hidden=true] [aria-hidden=true]').getBoundingClientRect();return [Math.round(r.left),Math.round(r.top)];"
        a, m, z = (_probe_gas(core_js, _ps(blk, "wr", p=1, s=v), 1, js) for v in (0, 0.25, 1))
        assert abs(a[0] - z[0]) <= 1 and abs(a[1] - z[1]) <= 1, (form, a, z)
        assert m != a, (form, a, m)


@browser
def test_streak_ghosts_vanish_at_p1(core_js):
    blk = {"type": "motion_streak", "text": "whip", "ghosts": 4}
    js = "var g=document.querySelectorAll('[data-mt-id=sk] span[aria-hidden] > span');var o=[];g.forEach(function(s){o.push(parseFloat(getComputedStyle(s).opacity));});return o.slice(0,-1);"
    end = _probe_gas(core_js, _ps(blk, "sk", p=1), 1, js)
    mid = _probe_gas(core_js, _ps(blk, "sk", p=0.5), 1, js)
    assert max(end) < 0.01 and max(mid) > 0.05, (end, mid)


@browser
def test_foil_light_band_travels_with_s_and_text_stays_filled(core_js):
    blk = {"type": "motion_foil", "text": "SHINE", "look": "gold"}
    js = "var s=document.querySelector('[data-mt-id=fl] span');var c=getComputedStyle(s);return [c.backgroundPositionX,c.backgroundPositionY,c.webkitTextFillColor,parseFloat(c.opacity)];"
    a, z = (_probe_gas(core_js, _ps(blk, "fl", p=1, s=v), 1, js) for v in (0, 1))
    assert a[0] != z[0] and a[2] == "rgba(0, 0, 0, 0)" and a[3] == 1, (a, z)
