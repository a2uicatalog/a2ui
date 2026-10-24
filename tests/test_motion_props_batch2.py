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
