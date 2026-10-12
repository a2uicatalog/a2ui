"""motion_text options added 2026-10-12 from the text-motion taxonomy (a2ui-private/briefs/text-motion-taxonomy.yaml):
order (forward, reverse, centre, random + seed), reveal pop and decode, accent_font and accent_style, wave, start_scale, caret.

Same layers as the other motion tests: the GAS and Python renderers agree byte for byte (including hostile input), every option is inert when off,
and a real browser shows each one doing what it says at fixed instants.
"""
from __future__ import annotations

import pytest

from test_motion_atoms import _gas_batch, _norm, _py, browser, core_js  # noqa: F401
from test_motion_candidates import _dial, _probe_gas, _ps

BASE = {"type": "motion_text", "text": "Make work *easier*\nwherever it *happens*", "size": 48}
OPTS = [
    {"order": "reverse"}, {"order": "centre", "mode": "words"}, {"order": "random", "order_seed": 11, "mode": "chars"}, {"order": "random", "order_seed": 999, "mode": "words"},
    {"reveal": "pop", "mode": "chars"}, {"reveal": "pop", "mode": "words"}, {"reveal": "decode", "mode": "chars", "order_seed": 5}, {"reveal": "decode", "mode": "words"}, {"reveal": "decode"},
    {"accent_font": "serif", "accent_style": "italic"}, {"accent_font": "mono"}, {"accent_style": "italic", "accent_gradient": ["#ff0000", "#0000ff"]},
    {"wave": 12, "mode": "chars"}, {"wave": 40, "mode": "words"}, {"start_scale": 4}, {"start_scale": 2.37, "mode": "words"}, {"caret": True, "mode": "chars"}, {"caret": True, "mode": "words"}, {"caret": True},
    {"order": "centre", "reveal": "decode", "caret": True, "wave": 8, "start_scale": 3, "mode": "chars", "accent_font": "display"},
    {"order": "nope", "reveal": "nope", "accent_font": "nope", "accent_style": "bold", "wave": "x", "start_scale": "x", "caret": "yes"},
    {"order": '"><img src=x onerror=alert(1)>', "order_seed": '"><script>alert(2)</script>', "accent_font": '"><img>', "wave": '"><img>', "start_scale": '"><img>'},
    {"wave": 9999, "start_scale": 9999, "order_seed": 99999999},
]
CASES = [dict(BASE, **o) for o in OPTS] + [{"type": "motion_text", **o} for o in OPTS[:6]]


def test_python_matches_gas_for_every_new_option(core_js):
    got = _gas_batch(core_js, CASES)
    bad = [i for i, (c, g) in enumerate(zip(CASES, got)) if _norm(_py(c)) != _norm(g)]
    assert not bad, [str({k: v for k, v in CASES[i].items() if k not in ("text", "type", "size")}) for i in bad]


def test_every_option_is_inert_when_off(core_js):
    plain = _gas_batch(core_js, [BASE])[0]
    off = dict(BASE, order="forward", wave=0, start_scale=1, caret=False, accent_style="roman", accent_font="")
    assert _gas_batch(core_js, [off])[0] == plain and _norm(_py(off)) == _norm(_py(BASE)) == _norm(plain)


def test_hostile_values_never_become_markup(core_js):
    hostile = [dict(BASE, order='"><img src=x onerror=alert(1)>', accent_font='"><img src=x>', wave='"><img src=x>', start_scale='"><img src=x>', order_seed='"><img src=x>')]
    for h in (_gas_batch(core_js, hostile)[0], _py(hostile[0])):
        assert "<img" not in h and "onerror=" not in h.replace("&quot;", "") and "NaN" not in h


def _units_js(sel="[data-mt-id=tx] [aria-hidden=true] > span"):
    return "var u=document.querySelectorAll('[data-mt-id=tx] [aria-hidden=true] > span > span');return Array.prototype.map.call(u,function(e){return +(+getComputedStyle(e).opacity).toFixed(2);});"


@browser
def test_order_reverse_and_centre_and_random_reveal_in_a_different_sequence(core_js):
    js = "var u=document.querySelectorAll('[data-mt-id=tx] [aria-hidden=true] > span');var o=[];Array.prototype.forEach.call(u,function(e){var f=e.firstElementChild;if(f)o.push(+(+getComputedStyle(f).opacity).toFixed(2));});return o;"
    def at(order, p, **kw):
        blk = {"type": "motion_text", "text": "one two three four five", "mode": "words", "overlap": 1, "reveal": "fade", "order": order, **kw}
        return _probe_gas(core_js, _ps(blk, "tx", p=p), 1, "var w=document.querySelectorAll('[data-mt-id=tx] span[style*=\"--u\"]');return Array.prototype.map.call(w,function(e){return +(+getComputedStyle(e).opacity).toFixed(2);});")
    f, r, c, rd = at("forward", 0.5), at("reverse", 0.5), at("centre", 0.5), at("random", 0.5, order_seed=7)
    assert f[0] > f[-1] and r[0] < r[-1] and c[2] >= c[0] and c[2] >= c[4], (f, r, c)
    assert rd != f and rd != r and sorted(rd) == sorted(f), (f, rd)
    assert at("random", 0.5, order_seed=7) == rd                     # seeded: the same every time


@browser
def test_pop_overshoots_then_settles(core_js):
    blk = {"type": "motion_text", "text": "pop", "mode": "words", "reveal": "pop", "overlap": 1}
    js = "var e=document.querySelector('[data-mt-id=tx] span[style*=\"--u\"]');var m=new DOMMatrix(getComputedStyle(e).transform);return +m.a.toFixed(3);"
    vals = [_probe_gas(core_js, _ps(blk, "tx", p=p), 1, js) for p in (0.0, 0.35, 0.55, 1.0)]
    assert max(vals) > 1.05 and vals[-1] == 1 and vals[0] < 0.5, vals


@browser
def test_decode_shows_noise_early_and_the_real_word_late(core_js):
    blk = {"type": "motion_text", "text": "decode me", "mode": "words", "reveal": "decode", "overlap": 1}
    js = ("var s=document.querySelector('[data-mt-id=tx] span[style*=\"--u\"]');var real=s.children[0],noise=s.children[1];"
          "return {real:+(+getComputedStyle(real).opacity).toFixed(2),noise:+(+getComputedStyle(noise).opacity).toFixed(2),n:noise.textContent.length,t:real.textContent};")
    a, m, z = (_probe_gas(core_js, _ps(blk, "tx", p=v), 1, js) for v in (0.0, 0.28, 1.0))
    assert a["real"] == 0 and a["noise"] == 1 and a["n"] == 6 and z["real"] == 1 and z["noise"] == 0 and z["t"] == "decode", (a, m, z)


@browser
def test_accent_word_takes_its_own_face_and_style(core_js):
    blk = {"type": "motion_text", "text": "plain *accent* plain", "mode": "block", "accent_font": "serif", "accent_style": "italic"}
    js = "var a=document.querySelector('[data-mt-id=tx] [aria-hidden=true] span span span, [data-mt-id=tx] [aria-hidden=true] span span');var all=document.querySelectorAll('[data-mt-id=tx] [aria-hidden=true] span');var hit=null;Array.prototype.forEach.call(all,function(e){if(e.textContent==='accent'&&e.children.length===0)hit=e;});var cs=getComputedStyle(hit);return {ff:cs.fontFamily.slice(0,20),st:cs.fontStyle};"
    r = _probe_gas(core_js, _ps(blk, "tx", p=1), 1, js)
    assert r["st"] == "italic" and "serif" in r["ff"].lower() or "georgia" in r["ff"].lower() or "times" in r["ff"].lower(), r


@browser
def test_wave_moves_letters_between_the_ends_and_rests_flat_at_both(core_js):
    blk = {"type": "motion_text", "text": "wave", "mode": "chars", "wave": 20, "reveal": "fade"}
    js = ("var u=document.querySelectorAll('[data-mt-id=tx] [aria-hidden=true] span[style*=\"translateY(calc(\"]');return Array.prototype.map.call(u,function(e){return Math.round(new DOMMatrix(getComputedStyle(e).transform).f);});")
    a, m, z = (_probe_gas(core_js, _ps(blk, "tx", p=1, s=v), 1, js) for v in (0, 0.5, 1))
    assert all(v == 0 for v in a) and all(v == 0 for v in z) and any(v != 0 for v in m) and len(set(m)) > 1, (a, m, z)


@browser
def test_start_scale_zooms_down_with_p_and_is_cropped_by_the_box(core_js):
    blk = {"type": "motion_text", "text": "Zoom", "mode": "block", "start_scale": 5, "size": 80}
    js = "var s=document.querySelector('[data-mt-id=tx] [aria-hidden=true]');return {k:+new DOMMatrix(getComputedStyle(s).transform).a.toFixed(2),clip:getComputedStyle(s.parentElement).overflow};"
    a, z = (_probe_gas(core_js, _ps(blk, "tx", p=v), 1, js) for v in (0, 1))
    assert a["k"] == 5 and z["k"] == 1 and a["clip"] == "hidden", (a, z)


@browser
def test_caret_follows_the_unit_being_typed_and_stays_on_the_last(core_js):
    blk = {"type": "motion_text", "text": "type this out", "mode": "words", "caret": True, "overlap": 1, "reveal": "fade"}
    js = "var c=document.querySelectorAll('[data-mt-id=tx] [aria-hidden=true] span[style*=\"background:currentColor\"], [data-mt-id=tx] [aria-hidden=true] span[style*=\"background: currentcolor\"]');return Array.prototype.map.call(c,function(e){return +(+getComputedStyle(e).opacity).toFixed(2);});"
    mid, end = (_probe_gas(core_js, _ps(blk, "tx", p=v), 1, js) for v in (0.5, 1))
    assert len(mid) == 3 and sum(1 for v in mid if v > 0.5) == 1, mid        # one caret lit while typing
    assert end == [0, 0, 1], end                                              # finished: on the last word
