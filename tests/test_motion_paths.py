from __future__ import annotations

import json
import re

import pytest

from test_motion_atoms import CHROMIUM, _gas_batch, _norm, _probe, _py, browser, core_js  # noqa: F401
from test_motion_props_batch import _renderer_at

CHILD = {"type": "motion_pill", "text": "Go"}
MASK = {"type": "motion_mask", "blocks": [CHILD]}
MORPH = {"type": "motion_morph"}

STAR = "M50 0 L61 35 L98 35 L68 57 L79 91 L50 70 L21 91 L32 57 L2 35 L39 35 Z"
HEART = "M50 90 C10 60 0 30 25 15 C40 8 50 20 50 25 C50 20 60 8 75 15 C100 30 90 60 50 90 Z"
SQUARE = "M0 0H100V100H0Z"
WAVE = "m0 50 q25 -50 50 0 t50 0"
OPEN = "M0 0 C30 100 70 -100 100 0"
SMOOTH = "M0 0 C10 20 30 20 40 0 S70 -20 80 0 s20 20 20 0"
COMPACT = "M0,0L10-5.5.5 20"

GOOD_D = [STAR, HEART, SQUARE, WAVE, OPEN, SMOOTH, COMPACT, "  M 0 0 L 10 10 L 0 10  ", "M0 0L10 10", "M0 0 L10 0 L10 10 L0 10 L0 0",
          "M0 0 L 50 50 M 60 60 L 90 90", "M 1 1 2 2 3 1 z", "M0 0 q10 20 20 0 t20 0 t20 0", "m5 5 h10 v10 h-10 z"]
BAD_D = [
    "", "   ", None, 5, True, [], {}, "x", "M", "M0", "M0 0 L", "M0 0 L1", "L0 0 L1 1", "M0 0 A5 5 0 0 1 10 10", "M0 0 a5 5 0 0 1 10 10",
    "M0 0 L1e3 5", "M0 0 L1E3 5", "M0 0 L1 1 -", "M0 0 L1 1 .", "M0 0 L1 1 Z 5", "M0 0 L1 1 #", "M0 0 L1 1;",
    'M0 0"/><script>alert(1)</script>', 'M0 0 L1 1" onload="x', "M0 0 L1 1\x00", "M0 0 L9999999 1", "M0 0 L-9999999 1",
    "M0 0 L1 1 L" + "9" * 5000, "M0 0" + " L1 1" * 500, "M5 5", "M5 5 L5 5 L5 5", "M0 0 L1 1 NaN", "M0 0 L Infinity 1", "M0 0 C1 1 2 2 3",
    "M0 0 L0 10 L0 20", "M0 0 L100 100", "M0 50 L100 50", "M0 0 L10 0 L20 0 Z", "\x1cM0 0 L10 0 L10 10Z", "\ufeffM0 0 L10 0 L10 10Z", "\x85M0 0 L10 0 L10 10Z", "\x0bM0 0 L10 0 L10 10Z\x0c",
]
CASES = ([dict(MASK, shape="path", d=d) for d in GOOD_D + BAD_D]
         + [dict(MASK, shape=s, d=STAR) for s in ("blob", "circle", "bars", "diagonal", "rounded", "diamond", "halftone", "conic", "slats", None, 5, "PATH")]
         + [dict(MASK, shape="path"), dict(MASK, shape="path", d=STAR, blocks=[CHILD, {"type": "motion_text", "text": "Hi"}])]
         + [dict(MORPH, from_d=a, to_d=b) for a in (STAR, HEART, OPEN) for b in (SQUARE, STAR, WAVE, OPEN, SMOOTH)]
         + [dict(MORPH, from_d=a, to_d=b) for a in BAD_D[:20] + [STAR] for b in (STAR, BAD_D[8], BAD_D[14], BAD_D[16])]
         + [dict(MORPH, from_d=STAR, to_d=HEART, label=lb) for lb in ("A star", 5, '"><b>', None)]
         + [dict(MORPH, from_d=STAR), dict(MORPH, to_d=STAR), dict(MORPH, from_d="", to_d=""), dict(MORPH, from_d=None, to_d=None)]
         + [dict(MORPH, from_d=STAR, to_d=HEART, fill="#ff0000", fill2="#0000ff", glossy=True, rotate=90, aspect=1.78, round=True, shapes=["square", "dot"])]
         + [dict(MORPH, from_d=HEART, to_d=STAR, shapes=["bogus"]), dict(MORPH, from_d=SQUARE, to_d="M0 0H100V100H0Z")])


def test_paths_python_matches_gas_exactly(core_js):
    got = _gas_batch(core_js, CASES)
    bad = [str(b)[:110] for b, g in zip(CASES, got) if _norm(_py(b)) != _norm(g)]
    assert not bad, bad


def test_mask_path_markup_and_note():
    h = _py(dict(MASK, shape="path", d=STAR))
    assert _clip(h).count("calc(50% + ") == 96 and "polygon(" in h and "cos(" not in h and "<!--" not in h
    assert "clamp(0,var(--p,1),1)" in h
    ign = _py(dict(MASK, shape="path", d="nope"))
    assert ign.endswith("<!-- a2ui: mask path ignored -->") and "cos(" in ign        # falls back to the blob
    assert _py(dict(MASK, shape="path")).endswith("<!-- a2ui: mask path ignored -->")
    assert "<!--" not in _py(dict(MASK, shape="circle", d=STAR))


def test_morph_path_markup_and_note():
    h = _py(dict(MORPH, from_d=STAR, to_d=SQUARE))
    assert h.count("clamp(0,var(--p,1),1)") > 40 and 'aria-label="Shape morph"' in h and "<!--" not in h
    one = _py(dict(MORPH, from_d=STAR))
    assert one.endswith("<!-- a2ui: morph path ignored -->") and 'aria-label="circle to star"' in one
    assert _py(dict(MORPH, from_d=STAR, to_d="bad")).endswith("<!-- a2ui: morph path ignored -->")
    same = _py(dict(MORPH, from_d=SQUARE, to_d=SQUARE))
    assert "clamp(" not in _clip(same), "identical paths have nothing to interpolate"


def test_hostile_paths_never_reach_markup():
    hostile = ['M0 0"/><script>alert(1)</script>', 'M0 0 L1 1" onload="x', "M0 0 L9" + "9" * 40 + " 1", "M0 0 LNaN NaN", "M0 0 L-1e999 1",
               "M0 0 L1 1</style><script>"]
    for d in hostile:
        for b in (dict(MASK, shape="path", d=d), dict(MORPH, from_d=d, to_d=STAR), dict(MORPH, from_d=STAR, to_d=d)):
            out = _py(b)
            assert "<script" not in out.lower() and "alert" not in out and "onload" not in out and "NaN" not in out and "Infinity" not in out and "undefined" not in out, (d, out[:200])
            assert re.search(r"<!-- a2ui: (mask|morph) path ignored -->$", out), d


def test_numbers_in_the_polygon_are_bounded_and_finite():
    for b in (dict(MASK, shape="path", d="M0 0 L1000000 1000000 L-1000000 5 Z"), dict(MORPH, from_d="M0 0 L1000000 1000000 L-1000000 5 Z", to_d="M-1000000 -1000000 L1 1 L2 9 Z"),
              dict(MORPH, from_d=STAR, to_d="M0 0 L0.000001 0 L0 0.000001 Z")):
        out = _py(b)
        for n in re.findall(r"-?\d+\.\d", out.split("clip-path:")[1].split(";")[0]):
            assert -1000.1 <= float(n) <= 1500, n
        assert "e+" not in out and "inf" not in out.lower()


def _clip(h):
    return h.split("clip-path:polygon(")[1].split(");")[0]


def _vertices(h):
    out = []
    for v in _clip(h).split(",calc("):
        v = v if v.startswith("calc(") else "calc(" + v
        x, y = v[5:-1].split(") calc(")
        out.append((x, y))
    return out


def test_morph_start_equals_from_and_end_equals_to():
    # evaluate the calc() expressions at p = 0 and p = 1 and compare with the fit of each path on its own
    from renderers import web_article as wa

    def at(h, p):
        pts = []
        for ex, ey in _vertices(h):
            v = []
            for e in (ex, ey):
                e = e.replace("clamp(0,var(--p,1),1)", str(p))
                e = e.replace("%", "")
                v.append(eval(e, {}, {}))  # noqa: S307 - arithmetic from our own renderer
            pts.append(v)
        return pts
    h = _py(dict(MORPH, from_d=STAR, to_d=SQUARE))
    pa, pb = wa._mo_pp_parse(STAR), wa._mo_pp_parse(SQUARE)
    ra, rb = (wa._mo_pp_resample(x["pts"], x["closed"], 64) for x in (pa, pb))
    fa, fb = wa._mo_pp_fit([ra, rb], True)
    fb = wa._mo_pp_align(fa, fb, True)
    start, end = at(h, 0), at(h, 1)
    assert [[round(a * 10), round(b * 10)] for a, b in start] == fa
    assert [[round(a * 10), round(b * 10)] for a, b in end] == fb


def test_flatten_resample_basics():
    from renderers import web_article as wa
    sq = wa._mo_pp_parse(SQUARE)
    assert sq["closed"] and len(sq["pts"]) == 4
    r = wa._mo_pp_resample(sq["pts"], True, 8)
    assert r[0] == [0.0, 0.0] and r[2] == [100.0, 0.0] and r[4] == [100.0, 100.0]
    op = wa._mo_pp_parse("M0 0 L10 0")
    assert not op["closed"] and wa._mo_pp_resample(op["pts"], False, 3) == [[0.0, 0.0], [5.0, 0.0], [10.0, 0.0]]
    assert wa._mo_pp_parse("M0 0 L5 5 M9 9 L99 99")["pts"] == [[0.0, 0.0], [5.0, 5.0]], "first subpath only"
    f = wa._mo_pp_fit([[[0.0, 0.0], [10.0, 0.0], [10.0, 5.0]]], False)
    assert f == [[[0, 0], [1000, 0], [1000, 1000]]]
    u = wa._mo_pp_fit([[[0.0, 0.0], [10.0, 0.0], [10.0, 5.0]]], True)
    assert u == [[[0, 250], [1000, 250], [1000, 750]]]


def test_align_picks_the_rotation_and_orientation():
    from renderers import web_article as wa
    a = [[0, 0], [10, 0], [10, 10], [0, 10]]
    assert wa._mo_pp_align(a, [[10, 10], [0, 10], [0, 0], [10, 0]], True) == a
    assert wa._mo_pp_align(a, [[0, 10], [10, 10], [10, 0], [0, 0]], True) == a, "reversed orientation is flipped back"
    ob = [[1, 1], [2, 2], [3, 3], [4, 4]]
    assert wa._mo_pp_align(a, ob, False) == ob


# ─── absent fields: every existing payload renders byte for byte as on origin/main e8ccc9a59 ───────────────────────
def test_existing_payloads_render_byte_for_byte_as_before():
    from test_motion_glitch import _existing_payloads
    from renderers import web_article as wa
    old = _renderer_at("e8ccc9a59")
    old._mo_install()
    wa._mo_install()
    pays = _existing_payloads() + [dict(MASK, shape=s) for s in (None, "blob", "circle", "diagonal", "rounded", "bars", "diamond", "halftone", "conic", "slats", "path-ish", 3)] \
        + [dict(MASK, shape=s, d=STAR) for s in ("blob", "bars")] + [dict(MORPH), dict(MORPH, shapes=["square", "heart", "dot"], round=True, aspect=2), dict(MORPH, from_d=None, to_d=""), dict(MORPH, glossy=True, rotate=45)]
    kinds, bad = set(), []
    for b in pays:
        k = b.get("component") or b["type"]
        if k not in old._RENDERERS:
            continue
        try:
            a = old._RENDERERS[k](dict(b))
        except Exception:
            continue
        kinds.add(k)
        n = wa._RENDERERS[k](dict(b))
        if k == "motion_timeline":
            # dark stages now re-point the page tokens (--a2ui-text ... --bg) at the film's dark palette (2026-10-25, 5eea3f9ae): style only
            n = re.sub(r"--a2ui-text:[^\"]*?--bg:[^;\"]*;", "", n)
        if a != n:
            bad.append((k, str(b)[:80]))
    assert not bad, bad[:10]
    assert {"motion_mask", "motion_morph"} <= kinds, kinds


# ─── in a browser: mid-p frames and the settled frame ─────────────────────────────────────────────────────────
_BBOX_JS = ("var d=document.querySelector('[style*=clip-path]');var r=d.getBoundingClientRect();"
            "return {w:r.width,h:r.height,cp:getComputedStyle(d).clipPath.slice(0,18)};")


def _set_p_js(p, body):
    return "var d=document.querySelector('[style*=clip-path]');d.parentNode.style.setProperty('--p','%s');document.body.offsetWidth;%s" % (p, body)


def _poly_pts(p, block):
    js = _set_p_js(p, "var r=d.getBoundingClientRect();var cp=getComputedStyle(d).clipPath;var m=cp.match(/polygon\\((.*)\\)/);"
                      "return {cp:cp,w:r.width,h:r.height};")
    got = _probe(block, 0, js)
    nums = re.findall(r"(-?[0-9.]+)(px|%)\s+(-?[0-9.]+)(px|%)", got["cp"])
    return [(float(a), float(c)) for a, _u, c, _v in nums], got


@browser
def test_mask_path_scales_in_from_the_centre_and_settles_on_the_shape():
    blk = dict(MASK, shape="path", d=STAR)
    end, got = _poly_pts(1, blk)
    assert len(end) == 48 and got["cp"].startswith("polygon("), got["cp"][:60]
    xs, ys = [x for x, _ in end], [y for _, y in end]
    w, h = got["w"] or 1, got["h"] or 1
    # units may be px or %: normalise to the box
    fx = max(xs) - min(xs)
    assert fx > 0 and (abs(fx - w) < 2 or abs(fx - 100) < 0.5 or abs(fx - 100 * w / w) < 0.5), (fx, w)
    mid, _g = _poly_pts(0.5, blk)
    zero, _g = _poly_pts(0, blk)
    cx = sum(x for x, _ in end) / 48
    assert max(abs(x - zero[0][0]) for x, _ in zero) < 0.01, "p=0: collapsed to the centre"
    spread_end, spread_mid = max(xs) - min(xs), max(x for x, _ in mid) - min(x for x, _ in mid)
    assert abs(spread_mid / spread_end - 0.5) < 0.02, (spread_mid, spread_end)
    assert cx > 0


@browser
def test_morph_path_mid_frame_is_between_and_settles_on_the_target():
    blk = dict(MORPH, from_d=STAR, to_d=SQUARE)
    p0, _g = _poly_pts(0, blk)
    p5, _g = _poly_pts(0.5, blk)
    p1, _g = _poly_pts(1, blk)
    assert len(p0) == len(p5) == len(p1) == 64
    for a, m, b in zip(p0, p5, p1):
        for i in (0, 1):
            assert abs(m[i] - (a[i] + b[i]) / 2) < 0.6, (a, m, b)
    # the end frame is the square: every vertex sits on the box edge
    xs, ys = [x for x, _ in p1], [y for _, y in p1]
    on_edge = sum(1 for x, y in p1 if min(abs(x - min(xs)), abs(x - max(xs)), abs(y - min(ys)), abs(y - max(ys))) < 0.6)
    assert on_edge == 64, on_edge
    # and the start frame is not the end frame
    assert max(abs(a[0] - b[0]) + abs(a[1] - b[1]) for a, b in zip(p0, p1)) > 5


@browser
def test_settled_markup_without_p_equals_p1():
    for blk in (dict(MASK, shape="path", d=HEART), dict(MORPH, from_d=STAR, to_d=HEART)):
        a, _g = _poly_pts(1, blk)
        js = "var d=document.querySelector('[style*=clip-path]');return {cp:getComputedStyle(d).clipPath};"
        g = _probe(blk, 0, js)
        b = [(float(x), float(y)) for x, _u, y, _v in re.findall(r"(-?[0-9.]+)(px|%)\s+(-?[0-9.]+)(px|%)", g["cp"])]
        assert a == b


def test_zero_area_paths_fall_back_with_the_note():
    for d in ("M0 0 L100 100", "M0 50 L100 50", "M0 0 L10 0 L20 0 Z", "M0 0 L100 0 L100 1 L0 1 Z"):
        assert _py(dict(MORPH, from_d=STAR, to_d=d)).endswith("<!-- a2ui: morph path ignored -->"), d
        assert _py(dict(MORPH, from_d=d, to_d=STAR)).endswith("<!-- a2ui: morph path ignored -->"), d
        if d.endswith("L0 1 Z"):
            continue                                   # a thin rectangle fills the mask box (stretched); only morph keeps proportions
        assert _py(dict(MASK, shape="path", d=d)).endswith("<!-- a2ui: mask path ignored -->"), d
    assert "<!--" not in _py(dict(MASK, shape="path", d="M0 0 L100 0 L100 10 L0 10 Z"))


def test_whitespace_trim_is_an_explicit_set_in_both_twins(core_js):
    ok = "M0 0 L10 0 L10 10Z"
    cases = [dict(MASK, shape="path", d=p + ok + q) for p, q in (("", ""), ("\x0b", "\x0c"), ("\x1c", ""), ("\ufeff", ""), ("\x85", ""), (" \t\n", "\r "))]
    got = _gas_batch(core_js, cases)
    assert [_norm(_py(b)) for b in cases] == [_norm(g) for g in got]
    assert "<!--" not in _py(cases[0]) and "<!--" not in _py(cases[1]) and "<!--" not in _py(cases[5])
    for c in cases[2:5]:
        assert _py(c).endswith("<!-- a2ui: mask path ignored -->")


def test_morph_path_label():
    assert 'aria-label="Shape morph"' in _py(dict(MORPH, from_d=STAR, to_d=HEART))
    assert 'aria-label="Star to heart"' in _py(dict(MORPH, from_d=STAR, to_d=HEART, label="Star to heart"))
    assert 'aria-label="circle to star"' in _py(dict(MORPH, label="x"))
