from __future__ import annotations

import json
import re

import pytest

from test_motion_atoms import CHROMIUM, _gas_batch, _norm, _probe, _py, _scene, browser, core_js  # noqa: F401

PILL = {"type": "motion_pill", "text": "Go"}
CARD = {"type": "demo_panel", "title": "Card", "rows": [["a", "1"], ["b", "2"]]}
TEXT = {"type": "motion_text", "text": "VILLAIN", "mode": "block"}
BASE_SHA = "cd1af1abe"  # origin/main before this batch


# --- I99: more motion_mask shapes ---------------------------------------------------------------------------
def test_i99_python_matches_gas_exactly(core_js):
    shapes = ['blob', 'circle', 'diagonal', 'rounded', 'bars', 'diamond', 'halftone', 'conic', 'slats']
    cases = []
    for s in shapes:
        cases.append({'type': 'motion_mask', 'shape': s, 'blocks': [{'type': 'motion_pill', 'text': f'Mask {s}'}]})
    cases.extend([
        {'type': 'motion_mask', 'shape': 'unknown_xyz', 'blocks': []},
        {'type': 'motion_mask', 'shape': 1234, 'blocks': []},
        {'type': 'motion_mask', 'shape': {'malicious': 'payload'}, 'blocks': []},
        {'type': 'motion_mask', 'shape': None, 'blocks': []},
        {'type': 'motion_mask', 'shape': 'diamond', 'blocks': [{'type': 'motion_pill', 'text': 'A'}, {'type': 'motion_pill', 'text': 'B'}]},
    ])
    got = _gas_batch(core_js, cases)
    bad = [i for i, (b, g) in enumerate(zip(cases, got)) if _norm(_py(b)) != _norm(g)]
    assert not bad, f"Mismatches at indices {bad}"


def test_i99_markup_new_shapes():
    diamond_html = _py({'type': 'motion_mask', 'shape': 'diamond'})
    assert 'clip-path:polygon(50% calc(50% - var(--m)*100%),calc(50% + var(--m)*100%) 50%,50% calc(50% + var(--m)*100%),calc(50% - var(--m)*100%) 50%)' in diamond_html
    assert '-webkit-clip-path:' in diamond_html

    conic_html = _py({'type': 'motion_mask', 'shape': 'conic'})
    assert 'mask-image:conic-gradient(#000 calc(var(--m)*360deg),transparent 0)' in conic_html
    assert '-webkit-mask-image:' in conic_html

    slats_html = _py({'type': 'motion_mask', 'shape': 'slats'})
    assert 'mask-image:repeating-linear-gradient(180deg,#000 0,#000 calc(var(--m)*24px),transparent calc(var(--m)*24px),transparent 24px)' in slats_html

    halftone_html = _py({'type': 'motion_mask', 'shape': 'halftone'})
    assert 'mask-image:radial-gradient(circle,#000 calc(var(--m)*104% - 4%),transparent calc(var(--m)*104%))' in halftone_html
    assert '-webkit-mask-size:14px 14px;mask-size:14px 14px;-webkit-mask-repeat:repeat;mask-repeat:repeat;' in halftone_html

    fallback_html = _py({'type': 'motion_mask', 'shape': 'invalid'})
    blob_html = _py({'type': 'motion_mask', 'shape': 'blob'})
    assert _norm(fallback_html) == _norm(blob_html)


@browser
def test_i99_browser_probe_new_shapes():
    for shape in ('diamond', 'halftone', 'conic', 'slats'):
        blk = {
            'type': 'motion_mask',
            'shape': shape,
            'blocks': [{'type': 'motion_pill', 'text': f'Probe {shape}'}]
        }
        res = _probe(blk, 0.0, """
            var wrapper = document.querySelector('div[style*="--m:clamp"]');
            var child = wrapper ? wrapper.firstElementChild : null;
            var cstyle = wrapper ? window.getComputedStyle(wrapper) : null;
            var rect = child ? child.getBoundingClientRect() : null;
            return {
                hasChild: !!child,
                width: rect ? rect.width : 0,
                height: rect ? rect.height : 0,
                clipPath: cstyle ? (cstyle.clipPath || cstyle.webkitClipPath || '') : '',
                maskImage: cstyle ? (cstyle.maskImage || cstyle.webkitMaskImage || '') : ''
            };
        """)
        assert res['hasChild'] is True
        assert res['width'] > 0 and res['height'] > 0
        if shape == 'diamond':
            assert res['clipPath'] != 'none' and res['clipPath'] != ''
        else:
            assert res['maskImage'] != 'none' and res['maskImage'] != ''


def test_i99_old_shapes_unchanged_and_new_shapes_are_distinct():
    old = _renderer_at(BASE_SHA)
    old._mo_install()
    for s in ("blob", "circle", "diagonal", "rounded", "bars", "bogus", None, 3):
        b = {"type": "motion_mask", "shape": s, "blocks": [PILL]}
        assert old._RENDERERS["motion_mask"](dict(b)) == _renderer_now()._RENDERERS["motion_mask"](dict(b)), s
    outs = {s: _py({"type": "motion_mask", "shape": s, "blocks": [PILL]}) for s in ("diamond", "halftone", "conic", "slats", "bars")}
    assert len(set(outs.values())) == 5


def _renderer_now():
    from renderers import web_article as wa
    wa._mo_install()
    return wa


def _renderer_at(sha):
    import importlib.util, subprocess, sys
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    r = subprocess.run(["git", "-C", str(root), "show", sha + ":renderers/web_article.py"], capture_output=True, text=True)
    if r.returncode:
        pytest.skip(sha + " not available")
    f = root / "renderers" / "_web_article_pre_mprops2.py"
    f.write_text(r.stdout)
    try:
        spec = importlib.util.spec_from_file_location("renderers._web_article_pre_mprops2", f)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
    finally:
        f.unlink()
    return mod


# --- I97: blur_dir and blur_radial ------------------------------------------------------------------------
CASES_I97 = [
    # blur_dir truthy / defaults
    {'type': 'motion_pill', 'text': 'Pill 1', 'blur_dir': True},
    {'type': 'motion_pill', 'text': 'Pill 2', 'blur_dir': {}},
    {'type': 'motion_pill', 'text': 'Pill 3', 'blur_dir': {'angle': 45, 'amount': 20}},
    {'type': 'motion_pill', 'text': 'Pill 4', 'blur_dir': {'angle': -90, 'amount': 15, 'static': True}},
    {'type': 'motion_pill', 'text': 'Pill 5', 'blur_dir': {'angle': 720, 'amount': 999}},
    {'type': 'motion_pill', 'text': 'Pill 6', 'blur_dir': {'angle': -500, 'amount': -10}},
    # blur_dir no-op / falsy
    {'type': 'motion_pill', 'text': 'Pill 7', 'blur_dir': False},
    {'type': 'motion_pill', 'text': 'Pill 8', 'blur_dir': None},
    {'type': 'motion_pill', 'text': 'Pill 9', 'blur_dir': 'fast'},
    {'type': 'motion_pill', 'text': 'Pill 10', 'blur_dir': 42},
    {'type': 'motion_pill', 'text': 'Pill 11', 'blur_dir': [1, 2]},
    {'type': 'motion_pill', 'text': 'Pill 12', 'blur_dir': {'amount': 0}},
    # blur_radial truthy / defaults
    {'type': 'demo_panel', 'title': 'Card 1', 'blur_radial': True},
    {'type': 'demo_panel', 'title': 'Card 2', 'blur_radial': {}},
    {'type': 'demo_panel', 'title': 'Card 3', 'blur_radial': {'amount': 0.3, 'cx': 20, 'cy': 80}},
    {'type': 'demo_panel', 'title': 'Card 4', 'blur_radial': {'amount': 0.15, 'static': True}},
    {'type': 'demo_panel', 'title': 'Card 5', 'blur_radial': {'amount': 5, 'cx': 150, 'cy': -20}},
    # blur_radial no-op / falsy
    {'type': 'demo_panel', 'title': 'Card 6', 'blur_radial': False},
    {'type': 'demo_panel', 'title': 'Card 7', 'blur_radial': None},
    {'type': 'demo_panel', 'title': 'Card 8', 'blur_radial': 'zoom'},
    {'type': 'demo_panel', 'title': 'Card 9', 'blur_radial': 12},
    {'type': 'demo_panel', 'title': 'Card 10', 'blur_radial': [1, 2]},
    {'type': 'demo_panel', 'title': 'Card 11', 'blur_radial': {'amount': 0}},
    # both together
    {'type': 'motion_text', 'text': 'Combo 1', 'blur_dir': {'angle': 30, 'amount': 10}, 'blur_radial': {'amount': 0.2}},
    {'type': 'motion_text', 'text': 'Combo 2', 'blur_dir': True, 'blur_radial': {'static': True}},
    # combined with glitch, smear, tilt, blend, enter
    {'type': 'motion_pill', 'text': 'All Props', 'blur_dir': {'angle': 15}, 'blur_radial': {'amount': 0.08}, 'tilt': True, 'blend': 'multiply', 'enter': 'fade'},
    # hostile / script containment in child
    {'type': 'motion_pill', 'text': '<script>alert(1)</script>', 'blur_dir': True},
    {'type': 'motion_pill', 'text': '<SCRIPT src="x"></script>', 'blur_radial': True},
    # hostile spec injection
    {'type': 'motion_pill', 'text': 'Hostile', 'blur_dir': {'angle': '"><img src=x onerror=1>', 'amount': '<script>'}},
    {'type': 'demo_panel', 'title': 'Hostile2', 'blur_radial': {'amount': '"><script>', 'cx': '"><script>'}},
]


def test_i97_python_matches_gas_exactly(core_js):
    got = _gas_batch(core_js, CASES_I97)
    bad = [str(b)[:110] for b, g in zip(CASES_I97, got) if _norm(_py(b)) != _norm(g)]
    assert not bad, bad


def test_i97_inert_when_absent_or_falsy():
    for base in (PILL, CARD, TEXT):
        plain = _py(dict(base))
        for k in ("blur_dir", "blur_radial"):
            for inert in (None, False, "", 0, "fast", 42, [1], {}, {"amount": 0}):
                assert _py(dict(base, **{k: inert})) == plain, (base["type"], k, inert)
        assert "mo-bd" not in plain and "mo-br" not in plain
    assert _py(dict(PILL, blur_dir={"static": "yes"}, blur_radial={"static": 1})).count('inert style') == 4  # non-True static is not static


def test_i97_markup():
    h = _py(dict(PILL, blur_dir={"angle": 45, "amount": 16}))
    assert 'transform:rotate(45deg);filter:url(#mo-' in h and '<div style="transform:rotate(-45deg);">' in h and 'stdDeviation="16 0"' in h
    assert "flood-opacity:calc(1 - clamp(0,var(--p,1),1))" in h and "prefers-reduced-motion" in h
    n = _py(dict(PILL, blur_dir={"angle": -30, "amount": 5}))
    assert "rotate(-30deg);filter" in n and 'style="transform:rotate(30deg);"' in n and "--" not in n.split("<svg")[1].split("</svg>")[0].replace("var(--p", "")
    s = _py(dict(PILL, blur_dir={"angle": 10, "static": True}))
    assert "flood" not in s and "prefers-reduced-motion" not in s and '<feGaussianBlur in="SourceGraphic" stdDeviation="12 0"/>' in s
    fid = re.search(r'<filter id="(mo-[a-z0-9]{6})"', h).group(1)
    assert "url(#" + fid + ")" in h
    r = _py(dict(PILL, blur_radial={"amount": 0.25, "cx": 40, "cy": 60}))
    assert r.count('class="mo-br-c"') == 4 and "transform-origin:40% 60%;" in r
    assert "transform:scale(calc(1 + 0.25*0.25*(1 - clamp(0,var(--p,1),1))))" in r and "transform:scale(calc(1 + 0.25*1*(1 - clamp(0,var(--p,1),1))))" in r
    rs = _py(dict(PILL, blur_radial={"static": True}))
    assert "prefers-reduced-motion" not in rs and "calc(1 + 0.12*0.5*1)" in rs


def test_i97_radial_copies_carry_no_ids_and_are_hidden_from_assistive_tech():
    from renderers import web_article as wa
    h = wa._mo_blur_radial(True, '<div id="x1" data-id="k">a</div>')
    assert h.count('id="x1"') == 1 and h.count('data-id="k"') == 5
    assert h.count('aria-hidden="true" inert') == 4


def test_i97_scripts_and_hostile_values_never_reach_markup():
    from renderers import web_article as wa
    assert wa._mo_blur_dir(True, "<script>x</script>") == "<script>x</script>"
    assert wa._mo_blur_radial(True, "<SCRIPT>x</SCRIPT>") == "<SCRIPT>x</SCRIPT>"
    for b in (dict(PILL, blur_dir={"angle": '"><img src=x onerror=1>', "amount": "<script>"}),
              dict(PILL, blur_radial={"amount": '"><script>', "cx": '"><script>', "cy": "x;}</style>"}),
              dict(PILL, blur_dir={"angle": 1e999, "amount": 1e999}, blur_radial={"amount": float("nan")})):
        out = _py(b)
        assert "<script" not in out.lower() and "onerror" not in out and "NaN" not in out and "undefined" not in out and "inf" not in out.lower().replace("info", ""), out[:200]


@browser
def test_i97_filter_resolves_and_settles_sharp_in_a_browser():
    js = "var e=document.querySelector('.mo-bd');return getComputedStyle(e).filter;"
    assert "url(" in _probe(dict(PILL, blur_dir={"angle": 30, "amount": 10}), 0, js)
    js2 = "var e=document.querySelector('.mo-br-c');return +getComputedStyle(e).opacity;"
    assert _probe(dict(PILL, blur_radial={"amount": 0.2}), 0, js2) == 0, "p defaults to 1: copies invisible when settled"
    assert abs(_probe(dict(PILL, blur_radial={"amount": 0.2, "static": True}), 0, js2) - 0.22) < 0.01


# --- I90: spring easing on timeline tracks --------------------------------------------------------------------
def _extract_prop_points(html, prop):
    m = re.search(r'\b' + re.escape(prop) + r':\[(\[[^\]]+\](?:,\[[^\]]+\])*)\]', html)
    if not m:
        return []
    pts_raw = re.findall(r'\[([^\]]+)\]', m.group(1))
    pts = []
    for raw in pts_raw:
        parts = [p.strip() for p in raw.split(',')]
        pts.append((float(parts[0]), float(parts[1]), parts[2] if len(parts) > 2 else '0'))
    return pts


def test_i90_python_matches_gas_exactly(core_js):
    cases = [
        # 1. basic spring defaults true
        _scene([{"type": "motion_pill", "id": "a", "text": "Go", "place": {"x": 10, "y": 10, "w": 40}}],
               [{"target": "a", "keys": [{"t": 0, "x": 0, "ease": {"spring": True}}, {"t": 1.0, "x": 100}]}]),
        # 2. spring with explicit params
        _scene([{"type": "motion_pill", "id": "a", "text": "Go", "place": {"x": 10, "y": 10, "w": 40}}],
               [{"target": "a", "keys": [{"t": 0, "x": 10, "ease": {"spring": {"stiffness": 200, "damping": 15, "mass": 2.0}}}, {"t": 2.0, "x": 50}]}]),
        # 3. hostile spring params (negative, string, huge, NaN-like)
        _scene([{"type": "motion_pill", "id": "a", "text": "Go", "place": {"x": 10, "y": 10, "w": 40}}],
               [{"target": "a", "keys": [{"t": 0, "x": 0, "ease": {"spring": {"stiffness": -10, "damping": "bad", "mass": 999}}}, {"t": 1.0, "x": 20}]}]),
        # 4. empty spring dict {} -> defaults
        _scene([{"type": "motion_pill", "id": "a", "text": "Go", "place": {"x": 10, "y": 10, "w": 40}}],
               [{"target": "a", "keys": [{"t": 0, "x": 0, "ease": {"spring": {}}}, {"t": 0.5, "x": 30}]}]),
        # 5. spring on the last key (ignored -> regular ease)
        _scene([{"type": "motion_pill", "id": "a", "text": "Go", "place": {"x": 10, "y": 10, "w": 40}}],
               [{"target": "a", "keys": [{"t": 0, "x": 0}, {"t": 1.0, "x": 10, "ease": {"spring": True}}]}]),
        # 6. spring on key whose next key has a different property set
        _scene([{"type": "motion_pill", "id": "a", "text": "Go", "place": {"x": 10, "y": 10, "w": 40}}],
               [{"target": "a", "keys": [{"t": 0, "x": 0, "ease": {"spring": True}}, {"t": 0.5, "y": 10}, {"t": 1.0, "x": 100}]}]),
        # 7. duplicate / same t keys
        _scene([{"type": "motion_pill", "id": "a", "text": "Go", "place": {"x": 10, "y": 10, "w": 40}}],
               [{"target": "a", "keys": [{"t": 0, "x": 0, "ease": {"spring": True}}, {"t": 0, "x": 5}, {"t": 1.0, "x": 10}]}]),
        # 8. zero duration segment (t0 == t1)
        _scene([{"type": "motion_pill", "id": "a", "text": "Go", "place": {"x": 10, "y": 10, "w": 40}}],
               [{"target": "a", "keys": [{"t": 1.0, "x": 0, "ease": {"spring": True}}, {"t": 1.0, "x": 10}]}]),
        # 9. multiple props both with springs
        _scene([{"type": "motion_pill", "id": "a", "text": "Go", "place": {"x": 10, "y": 10, "w": 40}}],
               [{"target": "a", "keys": [{"t": 0, "x": 0, "y": 0, "ease": {"spring": {"stiffness": 100, "damping": 20, "mass": 1}}}, {"t": 1.5, "x": 40, "y": 80}]}]),
        # 10. non-spring ease dict without 'spring' key
        _scene([{"type": "motion_pill", "id": "a", "text": "Go", "place": {"x": 10, "y": 10, "w": 40}}],
               [{"target": "a", "keys": [{"t": 0, "x": 0, "ease": {"foo": 123}}, {"t": 1.0, "x": 50}]}]),
        # 11. multi-segment track with mixed spring and linear
        _scene([{"type": "motion_pill", "id": "a", "text": "Go", "place": {"x": 10, "y": 10, "w": 40}}],
               [{"target": "a", "keys": [{"t": 0, "x": 0, "ease": "linear"}, {"t": 1.0, "x": 10, "ease": {"spring": True}}, {"t": 2.0, "x": 20}]}]),
        # 12. hostile types for spring itself (list, number, string)
        _scene([{"type": "motion_pill", "id": "a", "text": "Go", "place": {"x": 10, "y": 10, "w": 40}}],
               [{"target": "a", "keys": [{"t": 0, "x": 0, "ease": {"spring": "invalid"}}, {"t": 1.0, "x": 10}]}]),
    ]
    got = _gas_batch(core_js, cases)
    bad = [(i, _norm(_py(b)), _norm(g)) for i, (b, g) in enumerate(zip(cases, got)) if _norm(_py(b)) != _norm(g)]
    assert not bad, f"Mismatches in {len(bad)} cases: indices {[b[0] for b in bad]}"


def test_i90_inert_when_no_spring():
    old = _renderer_at(BASE_SHA)
    old._mo_install()
    for ease in (None, {"foo": 1}, "expo-out", [0.2, 0, 0.4, 1], "hold", {"spring": False}, {"spring": "x"}):
        keys = [{"t": 0, "x": 0}, {"t": 1.0, "x": 10}]
        if ease is not None:
            keys[0]["ease"] = ease
        b = _scene([{"type": "motion_pill", "id": "a", "text": "Go", "place": {"x": 10, "y": 10, "w": 40}}], [{"target": "a", "keys": keys}])
        assert _norm(_py(b)) == _norm(old._RENDERERS["motion_timeline"](dict(b))), ease


def test_i90_samples_count_and_settled_exact():
    block = _scene([{"type": "motion_pill", "id": "a", "text": "Go", "place": {"x": 10, "y": 10, "w": 40}}],
                   [{"target": "a", "keys": [{"t": 0, "x": 0, "ease": {"spring": True}}, {"t": 1.0, "x": 100}]}])
    html = _py(block)
    pts = _extract_prop_points(html, 'x')
    # 24 samples for segment 0->1, plus the next authored keyframe at t=1.0 => 25 points total
    assert len(pts) == 25
    assert pts[0][0] == 0.0 and pts[0][1] == 0.0
    assert pts[-1][0] == 1.0 and pts[-1][1] == 100.0


def test_i90_underdamped_overshoots_critically_damped_does_not():
    # underdamped spring: stiffness 300, damping 5, mass 1 (will overshoot 1.0 on 0 -> 1)
    block_under = _scene([{"type": "motion_pill", "id": "a", "text": "Go", "place": {"x": 10, "y": 10, "w": 40}}],
                         [{"target": "a", "keys": [{"t": 0, "x": 0, "ease": {"spring": {"stiffness": 300, "damping": 5, "mass": 1}}}, {"t": 1.0, "x": 1.0}]}])
    pts_under = _extract_prop_points(_py(block_under), 'x')
    max_under = max(p[1] for p in pts_under)
    assert max_under > 1.0

    # critically damped spring: stiffness 100, damping 20, mass 1 (should not exceed 1.0005)
    block_crit = _scene([{"type": "motion_pill", "id": "a", "text": "Go", "place": {"x": 10, "y": 10, "w": 40}}],
                        [{"target": "a", "keys": [{"t": 0, "x": 0, "ease": {"spring": {"stiffness": 100, "damping": 20, "mass": 1}}}, {"t": 1.0, "x": 1.0}]}])
    pts_crit = _extract_prop_points(_py(block_crit), 'x')
    max_crit = max(p[1] for p in pts_crit)
    assert max_crit <= 1.0005

def test_i90_spring_false_or_junk_is_not_a_spring():
    def film(ease):
        return _scene([{"type": "motion_pill", "id": "a", "text": "Go", "place": {"x": 10, "y": 10, "w": 40}}], [{"target": "a", "keys": [{"t": 0, "x": 0, "ease": ease}, {"t": 1.0, "x": 10}]}])
    ref = _norm(_py(film({"foo": 1})))
    for junk in (False, None, "invalid", 3, [1]):
        assert _norm(_py(film({"spring": junk}))) == ref, junk


def test_i90_parameters_are_clamped_and_hostile_values_are_defaults():
    from renderers import web_article as wa
    assert wa._mo_spring_params({"spring": True}) == (170.0, 26.0, 1.0)
    assert wa._mo_spring_params({"spring": {"stiffness": -5, "damping": 1e9, "mass": 0}}) == (1.0, 100.0, 0.1)
    assert wa._mo_spring_params({"spring": {"stiffness": 1e9, "damping": "x", "mass": 1e9}}) == (1000.0, 26.0, 10.0)
    assert wa._mo_spring_params({"spring": {"stiffness": float("nan"), "damping": True, "mass": None}}) == (170.0, 26.0, 1.0)
    assert wa._mo_spring_params("spring") is None and wa._mo_spring_params(None) is None


def test_i90_each_spring_segment_is_24_linear_samples_and_the_rest_is_unchanged():
    h = _py(_scene([{"type": "motion_pill", "id": "a", "text": "Go", "place": {"x": 10, "y": 10, "w": 40}}],
                   [{"target": "a", "keys": [{"t": 0, "x": 0, "opacity": 0}, {"t": 1.0, "x": 10, "opacity": 1, "ease": {"spring": True}}, {"t": 2.0, "x": 20, "opacity": 1}]}]))
    xs, ops = _extract_prop_points(h, "x"), _extract_prop_points(h, "opacity")
    assert len(xs) == 26 and len(ops) == 26, "key 0 stays one point, the spring key becomes 24 samples, the last key is one exact point"
    h2 = _py(_scene([{"type": "motion_pill", "id": "a", "text": "Go", "place": {"x": 10, "y": 10, "w": 40}}],
                    [{"target": "a", "keys": [{"t": 0, "x": 0}, {"t": 1.0, "x": 10, "ease": {"spring": True}}, {"t": 2.0, "x": 20}]}]))
    pts = _extract_prop_points(h2, "x")
    assert len(pts) == 26 and pts[-1][:2] == (2.0, 20.0) and all(p[2] == "0" for p in pts[1:25])


def test_i90_integration_is_deterministic_and_settles():
    from renderers import web_article as wa
    a = wa._mo_spring_samples(0, 0, 3, 1, (170.0, 26.0, 1.0), (-100, 200))
    assert a == wa._mo_spring_samples(0, 0, 3, 1, (170.0, 26.0, 1.0), (-100, 200)) and len(a) == 24
    assert a[0] == "[0,0,0]" and abs(float(a[-1].split(",")[1]) - 1) < 0.01


def test_i90_lint_accepts_a_spring_film():
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
    import motion_lint
    film = _scene([{"type": "motion_pill", "id": "a", "text": "Go", "place": {"x": 10, "y": 10, "w": 40}}],
                  [{"target": "a", "keys": [{"t": 0, "opacity": 0, "x": 0, "ease": {"spring": {"stiffness": 300, "damping": 8}}}, {"t": 1.5, "opacity": 1, "x": 40}]}])
    rep = motion_lint.lint(film)
    assert not [f for f in rep if f["level"] == "error" or "flash" in f["rule"]], rep


@browser
def test_i90_spring_rings_around_the_target_and_settles_exactly_in_a_browser():
    f = _scene([{"type": "motion_pill", "id": "a", "text": "Go", "place": {"x": 10, "y": 10, "w": 40}}],
               [{"target": "a", "keys": [{"t": 0, "x": 0, "ease": {"spring": {"stiffness": 300, "damping": 8}}}, {"t": 2, "x": 50}]}], duration=4)
    js = "return parseFloat(document.querySelector('[data-mt-id=a]').style.transform.match(/translate\\(([-0-9.]+)px/)[1]);"
    end = _probe(f, 4, js)
    seen = [_probe(f, t, js) for t in (0.2, 0.35, 0.6)]
    assert max(seen) > end + 1 and min(seen) < end - 1, (seen, end)
    assert _probe(f, 2, js) == end


# --- absent props: every existing motion payload renders byte for byte as on origin/main cd1af1abe --------------------
NEW_KEYS = ("blur_dir", "blur_radial")


def test_existing_motion_payloads_render_byte_for_byte_as_before_the_batch():
    from test_motion_glitch import _existing_payloads
    from renderers import web_article as wa
    old = _renderer_at(BASE_SHA)
    old._mo_install()
    wa._mo_install()
    pays = _existing_payloads() + [{"type": "motion_mask", "shape": s, "blocks": [PILL]} for s in ("blob", "circle", "diagonal", "rounded", "bars", "unknown", None)]
    pays += [_scene([PILL | {"id": "a", "place": {"x": 1, "y": 1, "w": 30}}], [{"target": "a", "keys": [{"t": 0, "x": 0, "ease": e}, {"t": 1, "x": 9}]}])
             for e in ("expo-out", [0.1, 0, 0.3, 1], "hold", "linear", {"foo": 1}, {"spring": "no"})]
    assert len(pays) > 150, len(pays)
    kinds, bad = set(), []
    for b in pays:
        k = b.get("component") or b["type"]
        if k not in old._RENDERERS or "glitch" in b or "blend" in b or any(n in b for n in NEW_KEYS):
            continue
        try:
            a = old._RENDERERS[k](dict(b))
        except Exception:
            continue
        kinds.add(k)
        if a != wa._RENDERERS[k](dict(b)):
            bad.append(k)
    assert not bad, bad[:10]
    assert {"motion_mask", "motion_timeline", "motion_pill"} <= kinds, kinds
