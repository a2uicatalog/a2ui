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
