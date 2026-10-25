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


# ─── I100: trim on motion_path and motion_sketch ───────────────────────────────────────────────────────────
SK = [{"d": "M 0 0 L 50 50"}, {"d": "M 10 10 L 80 80", "fill": "#00ff00"}]
PATH = {"type": "motion_path"}
SKETCH = {"type": "motion_sketch", "strokes": SK}
TRIMS = [
    {}, None, "x", [0, 1], True, 5, {"start": 0, "end": 1, "offset": 0}, {"start": "a", "end": None, "offset": []},
    {"start": 0.2, "end": 0.8}, {"start": 0.1, "end": 0.9, "offset": 0.05}, {"start": 0.2, "end": 0.7, "offset": -0.3},
    {"start": -5, "end": 5, "offset": 3}, {"start": 0.8, "end": 0.2}, {"start": 0.5, "end": 0.5}, {"offset": 0.5}, {"end": 0.4},
    {"start": 0.3, "end": 0.6, "offset": 1.7}, {"start": 1e9, "end": 2},
]
TRIM_CASES = ([dict(PATH, trim=t) for t in TRIMS] + [dict(SKETCH, trim=t) for t in TRIMS]
              + [dict(PATH, marker=False, nodes=[{"x": 100, "y": 100, "label": "A"}], trim={"start": 0.3, "end": 0.6}),
                 dict(PATH, d="M 0 0 L 90 90", w=100, h=100, label="r", color="#112233", trim={"start": 0.1, "offset": 0.2}),
                 dict(SKETCH, strokes=[{"d": "M 0 0 L 9 9", "color": "#ff0000", "width": 3, "fill": "#0000ff", "fill_opacity": 0.5}], trim={"end": 0.5}),
                 dict(SKETCH, strokes=[], trim={"end": 0.5})])


def test_i100_python_matches_gas_exactly(core_js):
    got = _gas_batch(core_js, TRIM_CASES)
    bad = [str(b)[:110] for b, g in zip(TRIM_CASES, got) if _norm(_py(b)) != _norm(g)]
    assert not bad, bad


def test_i100_inert_trims_equal_the_no_trim_output():
    for base in (PATH, SKETCH):
        plain = _py(dict(base))
        for t in ({}, None, "x", [0, 1], True, 5, {"start": 0, "end": 1, "offset": 0}, {"start": "a", "end": None, "offset": []}, {"offset": 0}):
            assert _py(dict(base, trim=t)) == plain, (base["type"], t)
        assert "1000" not in plain


def test_i100_window_markup():
    h = _py(dict(PATH, trim={"start": 0.25, "end": 0.75, "offset": 0.1}))
    assert "stroke-dasharray:calc(calc((0.75 - 0.25)*clamp(0,var(--p,1),1))) 1;stroke-dashoffset:calc(-1*(0.35));" in h
    assert "opacity:clamp(0,calc(calc((0.75 - 0.25)*clamp(0,var(--p,1),1))*1000),1)" in h
    assert "calc(-1*(0.35 + calc((0.75 - 0.25)*clamp(0,var(--p,1),1)))*0.9999)" in h, "the marker rides the head of the window"
    s = _py(dict(SKETCH, trim={"start": 0.5, "end": 1}))
    assert s.count("stroke-dasharray:calc(calc((1 - 0.5)*var(--u))) 1") == 2 and s.count("fill:#00ff00") == 1


def test_i100_empty_window_draws_no_bold_stroke_but_keeps_the_rest():
    h = _py(dict(PATH, trim={"start": 0.8, "end": 0.2}, nodes=[{"x": 10, "y": 10, "label": "A"}]))
    assert h.count("<path") == 1 and "opacity:0.16" in h and ">A</text>" in h and "stroke-dasharray" not in h
    s = _py(dict(SKETCH, trim={"start": 0.8, "end": 0.2}))
    assert s.count("<path") == 1 and "fill:#00ff00" in s and "stroke-dasharray" not in s


def test_i100_hostile_values_never_reach_markup():
    h = _py(dict(PATH, trim={"start": '"><script>alert(1)</script>', "end": "x;}</style>", "offset": "javascript:1"}))
    assert "alert" not in h and "<script" not in h and "NaN" not in h and "undefined" not in h


_TRIM_JS = ("var ps=document.querySelectorAll('path');var b=Array.prototype.filter.call(ps,function(e){return getComputedStyle(e).strokeDasharray!=='none';})[0];var c=getComputedStyle(b);"
            "return {da:c.strokeDasharray,off:c.strokeDashoffset,n:ps.length};")


def _drawn(block, p):
    d = _probe(dict(block, trim=block["trim"]), 0, "document.querySelector('svg').parentNode.style.setProperty('--p','%s');" % p + _TRIM_JS)
    return [float(x) for x in re.findall(r"-?[0-9.]+", d["da"])], float(re.search(r"-?[0-9.]+", d["off"]).group())


@browser
def test_i100_visible_window_is_where_it_should_be():
    blk = dict(PATH, trim={"start": 0.25, "end": 0.75})
    da, off = _drawn(blk, 1)
    assert abs(da[0] - 0.5) < 0.01 and abs(off + 0.25) < 0.01, (da, off)
    da, off = _drawn(blk, 0.5)
    assert abs(da[0] - 0.25) < 0.01 and abs(off + 0.25) < 0.01, (da, off)
    da, off = _drawn(dict(PATH, trim={"start": 0.1, "end": 0.4, "offset": 0.2}), 1)
    assert abs(da[0] - 0.3) < 0.01 and abs(off + 0.3) < 0.01, (da, off)
    da, off = _drawn(dict(SKETCH, trim={"start": 0.5, "end": 1}), 1)
    assert abs(da[0] - 0.5) < 0.01 and abs(off + 0.5) < 0.01, (da, off)


# ─── absent props: every existing motion payload renders byte for byte as before this batch (origin/main 935844645) ──────
def _renderer_at(sha):
    import importlib.util, subprocess, sys
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    r = subprocess.run(["git", "-C", str(root), "show", sha + ":renderers/web_article.py"], capture_output=True, text=True)
    if r.returncode:
        pytest.skip(sha + " not available")
    f = root / "renderers" / "_web_article_pre_mprops.py"
    f.write_text(r.stdout)
    try:
        spec = importlib.util.spec_from_file_location("renderers._web_article_pre_mprops", f)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
    finally:
        f.unlink()
    return mod


def test_existing_motion_payloads_render_byte_for_byte_as_before_the_batch():
    from test_motion_glitch import _existing_payloads
    from renderers import web_article as wa
    old = _renderer_at("935844645")
    old._mo_install()
    wa._mo_install()
    pays = _existing_payloads() + [dict(PATH), dict(SKETCH), dict(PATH, marker=False, nodes=[{"x": 1, "y": 2, "label": "A"}]),
                                   dict(SKETCH, strokes=[{"d": "M 0 0 L 9 9", "fill": "#ff0000"}])]
    assert len(pays) > 150, len(pays)
    kinds, bad = set(), []
    for b in pays:
        k = b.get("component") or b["type"]
        if k not in old._RENDERERS or "glitch" in b or "blend" in b:
            continue
        try:
            a = old._RENDERERS[k](dict(b))
        except Exception:
            continue
        kinds.add(k)
        # dark stages re-point the page tokens (--a2ui-text ... --bg) at the film palette (2026-10-25, 5eea3f9ae): style only
        if a != re.sub(r"--a2ui-text:[^\"]*?--bg:[^;\"]*;", "", wa._RENDERERS[k](dict(b))):
            bad.append(k)
    assert not bad, bad[:10]
    assert {"motion_path", "motion_sketch", "motion_timeline"} <= kinds, kinds
