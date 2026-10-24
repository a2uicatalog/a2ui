from __future__ import annotations

import re

import pytest

from test_motion_atoms import CHROMIUM, _gas_batch, _norm, _probe, _py, _scene, browser, core_js  # noqa: F401

PILL = {"type": "motion_pill", "text": "Go"}
CARD = {"type": "demo_panel", "title": "Card", "rows": [["a", "1"], ["b", "2"]]}
TEXT = {"type": "motion_text", "text": "VILLAIN", "mode": "block"}

BLEND_ENUMS = [
    "multiply", "screen", "overlay", "darken", "lighten",
    "color-dodge", "color-burn", "difference", "exclusion",
    "hue", "saturation", "color", "luminosity",
]

CASES = []

# All 13 enum modes across different components and combinations
for mode in BLEND_ENUMS:
    CASES.append(dict(PILL, blend=mode))
    CASES.append(dict(CARD, blend=mode))
    CASES.append(dict(TEXT, blend=mode))

# Stacked with glitch, halo, enter
CASES.append(dict(CARD, blend="multiply", halo=True, enter="zoom-in"))
CASES.append(dict(TEXT, blend="screen", glitch={"slices": 2}, enter="fade-up"))
CASES.append(dict(PILL, blend="overlay", tilt={"max": 10}, halo={"color": "#ff0055"}))

# Unknown strings, hostile strings, numbers, objects, booleans, inert values
CASES.extend([
    dict(PILL, blend="MULTIPLY"),
    dict(PILL, blend="unknown-mode"),
    dict(CARD, blend='"><script>alert(1)</script>'),
    dict(TEXT, blend=123),
    dict(TEXT, blend=0),
    dict(TEXT, blend=3.14),
    dict(PILL, blend=True),
    dict(CARD, blend={}),
    dict(CARD, blend={"nested": "val"}),
    dict(TEXT, blend=["foo", "bar"]),
    dict(PILL, blend=None),
    dict(CARD, blend=False),
    dict(TEXT, blend=""),
])


def test_i95_python_matches_gas_exactly(core_js):
    got = _gas_batch(core_js, CASES)
    bad = [str(b)[:110] for b, g in zip(CASES, got) if _norm(_py(b)) != _norm(g)]
    assert not bad, bad


def test_i95_inert_when_absent():
    for base in (PILL, CARD, TEXT):
        plain = _py(dict(base))
        for inert in (None, False, ""):
            assert _py(dict(base, blend=inert)) == plain, (base["type"], inert)
        assert "mo-blend" not in plain


def test_i95_unknown_is_ignored_with_note():
    h_str = _py(dict(PILL, blend="bogus"))
    assert 'class="mo-blend"' not in h_str
    assert h_str.endswith('<!-- a2ui: blend "bogus" ignored -->')

    h_num = _py(dict(PILL, blend=42))
    assert 'class="mo-blend"' not in h_num
    assert h_num.endswith('<!-- a2ui: blend "number" ignored -->')

    h_bool = _py(dict(PILL, blend=True))
    assert 'class="mo-blend"' not in h_bool
    assert h_bool.endswith('<!-- a2ui: blend "boolean" ignored -->')

    h_obj = _py(dict(PILL, blend=["a"]))
    assert 'class="mo-blend"' not in h_obj
    assert h_obj.endswith('<!-- a2ui: blend "object" ignored -->')


def test_i95_own_blend_atoms_untouched():
    for atom_type in ("cursor_glow", "wave_terrain", "motion_discs"):
        b = {"type": atom_type, "blend": "multiply"}
        out = _py(b)
        assert "mo-blend" not in out


def test_i95_hostile_never_reaches_markup():
    hostile = '"><script>alert("xss")</script><div foo="'
    out = _py(dict(PILL, blend=hostile))
    assert "<script" not in out.lower()
    assert "mix-blend-mode" not in out
    from renderers import web_article as wa
    direct = wa._mo_blend(hostile, "x")                       # past the payload guard, the note is escaped
    assert "<script" not in direct and "&lt;script" in direct and direct.startswith("x<!--")
