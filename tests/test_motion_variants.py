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
