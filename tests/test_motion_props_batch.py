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


# ─── I96: filter track keys (hue, saturation, brightness, contrast, invert) ───────────────────────────────
def _fl(keys, extra=None):
    return _scene([{"type": "motion_pill", "id": "a", "text": "Go", "place": {"x": 10, "y": 10, "w": 40}}], [dict({"target": "a", "keys": keys}, **(extra or {}))])


FILTER_CASES = [
    _fl([{"t": 0, "hue": 0}, {"t": 2, "hue": 90}]),
    _fl([{"t": 0, "saturation": 0}, {"t": 2, "saturation": 2.5}]),
    _fl([{"t": 0, "brightness": 0.5}, {"t": 2, "brightness": 1.5, "ease": "hold"}]),
    _fl([{"t": 0, "contrast": 0.5, "invert": 0}, {"t": 2, "contrast": 3, "invert": 1}]),
    _fl([{"t": 0, "blur": 10, "brightness": 0.4, "hue": -30}, {"t": 3, "blur": 0, "brightness": 1, "hue": 0}]),
    _fl([{"t": 0, "hue": 9999, "saturation": -3, "brightness": "bad", "contrast": None, "invert": 7}, {"t": 2, "hue": -720, "saturation": 6, "brightness": 99, "contrast": [1], "invert": -1}]),
    _fl([{"t": 0, "hue": True, "invert": False}, {"t": 1, "hue": {"x": 1}, "invert": "1"}]),
    _fl([{"t": 0, "blur": 5}, {"t": 1, "blur": 0}]),
]


def test_i96_python_matches_gas_exactly(core_js):
    got = _gas_batch(core_js, FILTER_CASES)
    bad = [i for i, (b, g) in enumerate(zip(FILTER_CASES, got)) if _norm(_py(b)) != _norm(g)]
    assert not bad, bad


def test_i96_ranges_are_clamped_in_the_config():
    h = _py(_fl([{"t": 0, "hue": 9999, "saturation": 10, "brightness": 10, "contrast": -5, "invert": 10}, {"t": 1, "hue": -9999, "saturation": -5, "brightness": -5, "contrast": 10, "invert": -5}]))
    assert "hue:[[0,360," in h and ",[1,-360," in h
    assert "saturation:[[0,4," in h and ",[1,0," in h
    assert "brightness:[[0,4," in h and "contrast:[[0,0," in h and "invert:[[0,1," in h
    assert "9999" not in h


def test_i96_hostile_key_values_are_dropped():
    h = _py(_fl([{"t": 0, "hue": "bad", "invert": True, "contrast": None}, {"t": 1, "hue": [1], "invert": {"a": 1}}]))
    for k in ("hue:[", "invert:[", "contrast:["):
        assert k not in h.split("tg:")[1], k


def test_i96_player_is_unchanged_without_the_new_keys_and_composes_with_them():
    plain = _py(_fl([{"t": 0, "blur": 5}, {"t": 1, "blur": 0}]))
    assert 'e.style.filter=v.blur>0.05?"blur("+Math.min(40,v.blur).toFixed(2)+"px)":"";' in plain and "hue-rotate" not in plain
    from renderers import web_article as wa
    assert wa._mo_tl_js("{W:1,tg:[{i:\"a\",p:{blur:[[0,1,0]]}}]}") is wa._MO_TIMELINE_JS
    assert wa._MO_FILTER_OLD in wa._MO_TIMELINE_JS
    new = _py(_fl([{"t": 0, "hue": 45}, {"t": 1, "hue": 90}]))
    assert "hue-rotate(" in new and wa._MO_FILTER_OLD not in new


@browser
def test_i96_settled_frame_and_composition_in_a_browser():
    js = "return getComputedStyle(document.querySelector('[data-mt-id=a]')).filter;"
    tl = _fl([{"t": 0, "blur": 10, "brightness": 0.5, "hue": 0}, {"t": 4, "blur": 0, "brightness": 1.5, "hue": 90}])
    end = _probe(tl, 4, js)
    assert "brightness(1.5)" in end and "hue-rotate(90deg)" in end and "blur" not in end, end
    mid = _probe(tl, 1, js)
    assert "blur(" in mid and "brightness(" in mid and "hue-rotate(" in mid and mid.count("blur(") == 1, mid
    over = _probe(_fl([{"t": 0, "hue": 0, "invert": 0, "contrast": 1}, {"t": 4, "hue": 9999, "invert": 9, "contrast": 99}]), 4, js)
    assert "hue-rotate(360deg)" in over and "invert(1)" in over and "contrast(4)" in over, over
    ident = _probe(_fl([{"t": 0, "blur": 0, "hue": 0, "saturation": 1, "brightness": 1, "contrast": 1, "invert": 0}, {"t": 1, "blur": 0, "hue": 0, "saturation": 1, "brightness": 1, "contrast": 1, "invert": 0}]), 1, js)
    assert ident == "none", ident
