"""Motion variants (backlog I71, 2026-10-21): five small optional additions to existing motion atoms.

  motion_orbit   shape "pill": rectangular tiles that size to a label of up to 24 characters (the default square tile stays at 8)
  motion_timeline  scene transition "collapse": the old scene squeezes to a thin band and vanishes
  motion_text    reveal "bloom": the text resolves out of a soft glow
  motion_rays    angle for kind "speed": the direction the lines run
  motion_scatter origin: tiles burst out from a point; more than 8 cards

Every addition is OFF by default. Per item: Python == GAS byte for byte, writing the default explicitly changes nothing, hostile
input never becomes markup, and a real headless Chromium reads back the motion at fixed instants. Helpers come from test_motion_atoms.
"""
from __future__ import annotations

import re

import pytest

from test_motion_atoms import (STITCHED, _gas_batch, _norm, _probe, _py, _scene, browser, core_js)  # noqa: F401  (core_js is a fixture)

ORBIT = {"type": "motion_orbit", "items": ["A", "Bb", "Notes", "Docs"], "size": 64}
PILLS = ["Plan the sprint", "Review the draft", "Ship it today", "Archive old files", "Invite the team"]
TEXT = {"type": "motion_text", "text": "Make work *easier*\nwherever it *happens*", "size": 64}
RAYS = {"type": "motion_rays", "kind": "speed"}
SCATTER = {"type": "motion_scatter", "items": ["A", "B", "C", "D", "E", "F"]}

CASES = {
    "orbit": [
        dict(ORBIT, shape="pill", items=PILLS), dict(ORBIT, shape="pill", items=PILLS, size=40, rx=50, ry=30), dict(ORBIT, shape="pill", items=["x", "y"]),
        dict(ORBIT, shape="pill", items=["<img src=x onerror=alert(1)>", {"text": "a & b \"q\""}, "y" * 99, 7, None]), dict(ORBIT, shape="pill", items=PILLS, fill="#112233", ink="#ffeedd", ring=False),
        dict(ORBIT, shape="square"), dict(ORBIT, shape="<x>"), dict(ORBIT, shape=5), dict(ORBIT, shape="pill", items=[]),
        dict(ORBIT, items=["a long label that is cut"]),
    ],
}
ALL = [b for bs in CASES.values() for b in bs]


def test_python_matches_gas_exactly(core_js):
    got = _gas_batch(core_js, ALL)
    bad = [str(b)[:110] for b, g in zip(ALL, got) if _norm(_py(b)) != _norm(g)]
    assert not bad, bad


# ─── 1. motion_orbit shape "pill" ──────────────────────────────────────────────────────────────────────────────────────────────────

def test_orbit_default_is_unchanged_and_shape_square_writes_nothing_new():
    plain = _py(ORBIT)
    assert _norm(_py(dict(ORBIT, shape="square"))) == _norm(plain) == _norm(_py(dict(ORBIT, shape="<x>")))
    assert "nowrap" not in plain and "translate(-50%" not in plain


def test_orbit_labels_stay_capped_at_8_without_pill():
    assert "a long l" in _py(dict(ORBIT, items=["a long label that is cut"])) and "a long la" not in _py(dict(ORBIT, items=["a long label that is cut"]))


def test_orbit_pill_keeps_longer_labels_up_to_24_and_sizes_to_content():
    html = _py(dict(ORBIT, shape="pill", items=PILLS))
    for t in PILLS:
        assert ">" + t + "<" in html
    assert "y" * 24 in _py(dict(ORBIT, shape="pill", items=["y" * 99])) and "y" * 25 not in _py(dict(ORBIT, shape="pill", items=["y" * 99]))
    assert html.count("white-space:nowrap") == len(PILLS) and "width:auto" in html and "border-radius:999px" in html


def test_orbit_pill_hostile_text_is_escaped():
    html = _py(dict(ORBIT, shape="pill", items=["<img src=x onerror=alert(1)>"]))
    assert "<img" not in html and "&lt;img" in html


@browser
def test_orbit_pill_tiles_are_wider_than_tall_and_hug_their_label():
    blk = _scene([dict(ORBIT, id="o", shape="pill", items=PILLS, place={"x": 0, "y": 0, "w": 100, "h": 100})], [{"target": "o", "keys": [{"t": 0, "p": 1}, {"t": 4, "p": 1}]}])
    js = "var t=document.querySelectorAll('[data-mt-id=o] > div > div:not([aria-hidden])');return Array.prototype.map.call(t,function(e){var r=e.getBoundingClientRect();return [r.width,r.height];});"
    sizes = [s for s in _probe(blk, 2, js) if s[0] > 0]
    assert len(sizes) == len(PILLS) and all(w > 1.5 * h for w, h in sizes), sizes
    assert len({round(w) for w, _h in sizes}) > 1, "tiles size to their own label, not one shared width"


# ─── 2. motion_timeline scene transition "collapse" ────────────────────────────────────────────────────────────────────────────────

def _col(**kw):
    return dict(STITCHED, stitch="collapse", bpm=0, overlap=2.0, duration=9, controls=False, autoplay=False, scenes=[{"layer": "s1", "t": 0}, {"layer": "s2", "t": 3}], **kw)


CASES["timeline"] = [
    _col(), dict(STITCHED, stitch="collapse"), dict(STITCHED, scenes=[{"layer": "s1", "t": 0}, {"layer": "s2", "t": 3, "transition": "collapse"}, {"layer": "s3", "t": 6, "transition": "wipe"}]),
    dict(STITCHED, scenes=[{"layer": "s1", "t": 0}, {"layer": "s2", "t": 3, "transition": "wipe"}, {"layer": "s3", "t": 6, "transition": "collapse"}]),
    dict(STITCHED, scenes=[{"layer": "s1", "t": 0, "transition": "collapse"}, {"layer": "s2", "t": 3, "transition": "iris"}, {"layer": "s3", "t": 6, "transition": "collapse"}]),
    dict(STITCHED, stitch="Collapse"), dict(STITCHED, stitch="collapse<x>", scenes=[{"layer": "s1", "t": 0}, {"layer": "s2", "t": 3, "transition": "collapse\"><script>"}]),
]
ALL = [b for bs in CASES.values() for b in bs]


def test_collapse_python_matches_gas_exactly(core_js):
    cs = CASES["timeline"]
    got = _gas_batch(core_js, cs)
    bad = [str(b)[:90] for b, g in zip(cs, got) if _norm(_py(b)) != _norm(g)]
    assert not bad, bad


def test_collapse_is_new_and_other_transitions_are_unchanged():
    assert _norm(_py(dict(STITCHED, stitch="Collapse"))) == _norm(_py(dict(STITCHED, stitch="dissolve"))), "unknown names still fall back to dissolve"
    assert _norm(_py(_col())) != _norm(_py(dict(_col(), stitch="dissolve")))
    assert 'collapse"><script>' not in _py(CASES["timeline"][-1]), "a hostile transition name is dropped, never echoed"


@browser
def test_collapse_squeezes_the_old_scene_to_a_thin_band_then_shows_the_new_one():
    clip = "var e=document.querySelector('[data-mt-id=%s]');return [getComputedStyle(e).clipPath, +e.style.opacity];"
    wide = lambda c: [float(v) for v in re.findall(r"inset\(0(?:px)? ([0-9.]+)%? ", c)]
    assert _probe(_col(), 2, clip % "s1")[0] in ("none", "inset(0px)"), "before the transition the old scene is whole"
    mid = _probe(_col(), 4, clip % "s1")[0]
    assert mid.startswith("inset("), mid
    late = _probe(_col(), 4.8, clip % "s1")[0]
    assert late.startswith("inset(") and late != mid, (mid, late)
    assert _probe(_col(), 4, clip % "s2")[1] == 0, "the new scene waits while the old one collapses"
    assert _probe(_col(), 5.5, clip % "s2")[1] == 1, "and is whole once the collapse is done"


# ─── 3. motion_text reveal "bloom" ─────────────────────────────────────────────────────────────────────────────────────────────────
CASES["text"] = [
    dict(TEXT, reveal="bloom"), dict(TEXT, reveal="bloom", mode="words"), dict(TEXT, reveal="bloom", mode="chars", text="HELLO"), dict(TEXT, reveal="bloom", mode="block"),
    dict(TEXT, reveal="bloom", glow=20, accent_gradient=["#ff2d6f", "#19d3ff"], overlap=6, order="centre"), dict(TEXT, reveal="Bloom"), dict(TEXT, reveal="bloom<x>"),
    dict(TEXT, reveal="bloom", text="<img src=x onerror=alert(1)> & \"q\""),
]
ALL = [b for bs in CASES.values() for b in bs]


def test_bloom_python_matches_gas_exactly(core_js):
    cs = CASES["text"]
    got = _gas_batch(core_js, cs)
    bad = [str(b)[:90] for b, g in zip(cs, got) if _norm(_py(b)) != _norm(g)]
    assert not bad, bad


def test_bloom_is_opt_in_and_unknown_names_still_mean_rise():
    assert _norm(_py(dict(TEXT, reveal="Bloom"))) == _norm(_py(TEXT)) == _norm(_py(dict(TEXT, reveal="rise")))
    assert "brightness" not in _py(TEXT) and "brightness" not in _py(dict(TEXT, reveal="blur"))


def test_bloom_differs_from_blur_and_decode_and_is_hostile_safe():
    bloom, blur, dec = (_py(dict(TEXT, reveal=r)) for r in ("bloom", "blur", "decode"))
    assert len({bloom, blur, dec}) == 3
    assert "brightness(" in bloom and "drop-shadow(" in bloom and "blur(" in bloom and "scale(" in bloom
    assert "translateY" not in bloom.split("<br>")[0], "bloom does not slide: it condenses in place"
    h = _py(dict(TEXT, reveal="bloom", text="<img src=x onerror=alert(1)>"))
    assert "<img" not in h


@browser
def test_bloom_starts_blurred_glowing_and_bright_and_ends_clean():
    blk = _scene([dict(TEXT, id="t", reveal="bloom", mode="block", text="Hello", place={"x": 5, "y": 5, "w": 80})], [{"target": "t", "keys": [{"t": 0, "p": 0}, {"t": 4, "p": 1}]}])
    js = "var u=document.querySelector('[data-mt-id=t] span[aria-hidden] > span');var c=getComputedStyle(u);return [+c.opacity, c.filter];"
    early = _probe(blk, 1.6, js)
    assert "blur(" in early[1] and "brightness(" in early[1] and "drop-shadow(" in early[1], early
    done = _probe(blk, 4, js)
    assert done[0] == 1 and ("blur(0px)" in done[1] or done[1] == "none"), done


# ─── 4. motion_rays angle (kind speed) ─────────────────────────────────────────────────────────────────────────────────────────────
CASES["rays"] = [
    dict(RAYS, angle=30), dict(RAYS, angle=-45, count=12, thickness=0.3, strength=0.6, accent="#ff6a2b"), dict(RAYS, angle=90), dict(RAYS, angle=999), dict(RAYS, angle=-999),
    dict(RAYS, angle="x"), dict(RAYS, angle=None), dict(RAYS, angle=12.7), dict(RAYS, angle=0), dict(RAYS, angle="30deg;}</style>"),
    dict(RAYS, kind="burst", angle=40), {"type": "motion_rays", "angle": 20},
]
ALL = [b for bs in CASES.values() for b in bs]


def test_rays_python_matches_gas_exactly(core_js):
    cs = CASES["rays"]
    got = _gas_batch(core_js, cs)
    bad = [str(b)[:90] for b, g in zip(cs, got) if _norm(_py(b)) != _norm(g)]
    assert not bad, bad


def test_rays_angle_is_inert_when_off_or_not_speed():
    plain = _py(RAYS)
    for off in (dict(RAYS, angle=0), dict(RAYS, angle="x"), dict(RAYS, angle=None), dict(RAYS, angle=[]), dict(RAYS, angle=True)):
        assert _py(off) == plain, off
    assert _py(dict(RAYS, kind="burst", angle=40)) == _py(dict(RAYS, kind="burst")) and _py({"type": "motion_rays", "angle": 20}) == _py({"type": "motion_rays"})
    assert "rotate(" not in plain


def test_rays_angle_rotates_inside_a_clipping_frame_and_clamps():
    html = _py(dict(RAYS, angle=30))
    assert "rotate(30deg)" in html and "overflow:hidden" in html
    assert "rotate(180deg)" in _py(dict(RAYS, angle=999)) and "rotate(-180deg)" in _py(dict(RAYS, angle=-999))
    assert "}</style>" not in _py(dict(RAYS, angle="30deg;}</style>")) and "rotate(" not in _py(dict(RAYS, angle="30deg;}</style>"))


@browser
def test_rays_angle_turns_the_lines_and_the_frame_stays_16_9():
    blk = _scene([dict(RAYS, id="r", angle=30, place={"x": 0, "y": 0, "w": 100})], [{"target": "r", "keys": [{"t": 0, "p": 1}, {"t": 4, "p": 1}]}])
    js = ("var f=document.querySelector('[data-mt-id=r] > div'),i=f.firstElementChild;var m=new DOMMatrix(getComputedStyle(i).transform);var r=f.getBoundingClientRect();"
          "return [Math.round(Math.atan2(m.b,m.a)*180/Math.PI), Math.round(r.width/r.height*100)/100];")
    ang, aspect = _probe(blk, 2, js)
    assert ang == 30 and aspect == pytest.approx(1.78, abs=0.01)
