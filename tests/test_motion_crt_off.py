"""motion_crt_off (backlog B-34, motion coverage program 2026-10-24): an old CRT television switching off,
two-phase anisotropic collapse on a curved glass screen.

End state: p = 0 whole, p = 1 black (gone).
Phase timings: vertical squash p 0.08 to 0.50, horizontal shrink to a dot p 0.50 to 0.72,
phosphor dot flash and decay p 0.70 to 1.
Curvature: 32x32 BMP barrel displacement map; curve 0 disables the filter.
Accessibility: the real content is hidden from assistive tech only at p = 1; reduced motion is a plain fade.
WCAG 2.3.1: one small bright pulse (line then dot), never repeating; nothing is random.
Python == GAS byte for byte, options closed, hostile input never becomes markup.
"""
from __future__ import annotations

import base64
import html as _h
import json
import re
import subprocess
import tempfile
from pathlib import Path

import pytest

from test_motion_atoms import CHROMIUM, _gas_batch, _norm, _py, browser, core_js  # noqa: F401

HOSTILE = 'x";}</style><script>alert(1)</script><b onload="1"'
BASE = {"type": "motion_crt_off"}
KID = {"type": "motion_crt_off", "blocks": [{"type": "motion_pill", "text": "Continue"}]}

CASES = [
    BASE,
    dict(BASE, glow=0), dict(BASE, glow=1), dict(BASE, glow=0.5), dict(BASE, glow=1.5), dict(BASE, glow=-0.5), dict(BASE, glow="0.8"), dict(BASE, glow="x"), dict(BASE, glow=None), dict(BASE, glow=True),
    dict(BASE, curve=0), dict(BASE, curve=1), dict(BASE, curve=0.25), dict(BASE, curve=0.5), dict(BASE, curve=-1), dict(BASE, curve=2), dict(BASE, curve="0.6"), dict(BASE, curve="x"), dict(BASE, curve=None),
    dict(BASE, scanlines=True), dict(BASE, scanlines=False), dict(BASE, scanlines="no"), dict(BASE, scanlines=0), dict(BASE, scanlines=None),
    dict(BASE, version=1), dict(BASE, version=2), dict(BASE, version="x"), dict(BASE, version=1.5),
    dict(BASE, glow=0.8, curve=0.3, scanlines=False),
    dict(BASE, glow=0, curve=0),
    KID,
    {"type": "motion_crt_off", "blocks": [{"type": "motion_pill", "id": "a1", "text": "Go"}, {"type": "demo_panel", "title": "T", "rows": [["a", "1"]]}], "curve": 0.7},
    {"type": "motion_crt_off", "blocks": ["x", 3, None, {"type": "nope"}]},
    {"type": "motion_crt_off", "blocks": []},
    {"type": "motion_crt_off", "blocks": [{"type": "motion_pill", "id": "k1", "text": "Go"}] * 6},
    {"type": "motion_crt_off", "blocks": "javascript:alert(1)"},
    dict(BASE, id="c1", enter="rise"),
] + [
    dict(BASE, glow=round((s % 11) * 0.1, 2), curve=round(((s * 3) % 11) * 0.1, 2), scanlines=(s % 2 == 0))
    for s in range(1, 35)
]


def _count(h, name):
    return len(re.findall(r'data-crt="' + name + '"', h))


def test_python_matches_gas_exactly(core_js):
    got = _gas_batch(core_js, CASES)
    bad = [str(b)[:110] for b, g in zip(CASES, got) if _norm(_py(b)) != _norm(g)]
    assert not bad, bad


def test_structure_is_inert_and_scriptless():
    h = _py(KID)
    assert "<script" not in h.lower() and "<button" not in h and "<img" not in h and "Math.random" not in h
    assert _count(h, "root") == 1
    assert _count(h, "scr") == 1
    assert _count(h, "face") == 1
    assert h.count(">Continue<") == _py({"type": "motion_pill", "text": "Continue"}).count(">Continue<")
    flt_svg = re.search(r'<svg\b[^>]*>', h)
    if flt_svg:
        assert 'aria-hidden="true"' in flt_svg.group(0)
    for fx in re.findall(r'<div[^>]*data-crt="(?:scan|glass|line|dot)"[^>]*>', h):
        assert 'aria-hidden="true"' in fx
    scr = re.search(r'<div[^>]*data-crt="scr"[^>]*>', h).group(0)
    assert "aria-hidden" not in scr


def test_options_closed_glow_and_curve():
    h_def = _py(BASE)
    assert "--g:1;" in h_def
    assert _py(dict(BASE, glow=1)) == h_def
    assert _py(dict(BASE, glow="x")) == h_def
    assert _py(dict(BASE, glow=None)) == h_def
    assert "--g:0;" in _py(dict(BASE, glow=0))
    assert "--g:0.4;" in _py(dict(BASE, glow=0.4))
    assert "--g:1;" in _py(dict(BASE, glow=99))
    assert "--g:0;" in _py(dict(BASE, glow=-5))

    assert "id=\"crtc50\"" in h_def
    assert _py(dict(BASE, curve=0.5)) == h_def
    assert _py(dict(BASE, curve="x")) == h_def
    assert _py(dict(BASE, curve=None)) == h_def
    assert "id=\"crtc100\"" in _py(dict(BASE, curve=10))
    assert "id=\"crtc0\"" not in _py(dict(BASE, curve=0))


def test_curve_zero_emits_no_filter_and_no_filter_url():
    h0 = _py(dict(BASE, curve=0))
    assert "<filter" not in h0
    assert "<svg" not in h0
    assert "filter:url" not in h0
    assert 'data-crt="tube" style="position:relative;"' in h0


def test_scanlines_default_true_only_explicit_false_turns_off():
    h = _py(BASE)
    assert _count(h, "scan") == 1
    off = _py(dict(BASE, scanlines=False))
    assert _count(off, "scan") == 0
    for v in ("no", 0, None, True, "false"):
        assert _count(_py(dict(BASE, scanlines=v)), "scan") == 1


def test_bmp_is_valid_32x32_24bit_barrel_displacement_map():
    h = _py(BASE)
    m = re.search(r'data:image/bmp;base64,([A-Za-z0-9+/=]+)', h)
    assert m, "BMP data URI must be present"
    data = base64.b64decode(m.group(1))
    assert data.startswith(b"BM")
    assert len(data) == 3126, f"Expected 3126 bytes, got {len(data)}"
    file_size = int.from_bytes(data[2:6], "little")
    assert file_size == 3126
    offset = int.from_bytes(data[10:14], "little")
    assert offset == 54
    header_size = int.from_bytes(data[14:18], "little")
    assert header_size == 40
    width = int.from_bytes(data[18:22], "little")
    height = int.from_bytes(data[22:26], "little")
    assert width == 32 and height == 32
    bpp = int.from_bytes(data[28:30], "little")
    assert bpp == 24

    # Pixels: 32 rows, each row has 32 pixels * 3 bytes = 96 bytes (padded to multiple of 4: 96 is multiple of 4)
    # Texels order in row: Blue, Green, Red
    # Center texels: i in (15, 16), j in (15, 16).
    def get_pixel(i, j):
        # j from 0 (bottom) to 31 (top)
        row_start = 54 + j * 96
        p_start = row_start + i * 3
        b = data[p_start]
        g = data[p_start + 1]
        r = data[p_start + 2]
        return b, g, r

    for ci, cj in ((15, 15), (15, 16), (16, 15), (16, 16)):
        b, g, r = get_pixel(ci, cj)
        assert b == 128
        assert abs(r - 128) <= 3, f"Center red {r} not within 3 of 128"
        assert abs(g - 128) <= 3, f"Center green {g} not within 3 of 128"

    # Corner texels: (0, 0) bottom-left: nx < 0, ny < 0 -> r < 128, g < 128
    # (31, 31) top-right: nx > 0, ny > 0 -> r > 128, g > 128
    b_bl, g_bl, r_bl = get_pixel(0, 0)
    assert b_bl == 128 and r_bl < 50 and g_bl > 200   # file row 0 is the image BOTTOM (y down, so y*r^2 is positive there)
    b_tr, g_tr, r_tr = get_pixel(31, 31)
    assert b_tr == 128 and r_tr > 200 and g_tr < 50


def test_hostile_values_never_reach_markup():
    h = _py(dict(BASE, glow=HOSTILE, curve=HOSTILE, scanlines=HOSTILE, version=HOSTILE, blocks=HOSTILE))
    h_sub = re.sub(r"<style>[^<]*</style>", "", h, count=1)
    assert "<script" not in h_sub and not re.search(r"<[^>]*onload=", h_sub) and "</style>" not in h_sub and "<style" not in h_sub and "<b " not in h_sub
    assert "NaN" not in h and "undefined" not in h and "Infinity" not in h and "[object" not in h and "alert(1)" not in h


def test_version_note():
    assert "version" not in _py(BASE).lower().replace("data-crt", "") and _py(dict(BASE, version=1)) == _py(BASE)
    h = _py(dict(BASE, version=3))
    assert "Written for motion_crt_off version 3; drawn as version 1." in h
    assert h.replace(re.search(r'<div style="font-size:0.75rem[^>]*>Written for[^<]*</div>', h).group(0), "") == _py(BASE)


def test_reduced_motion_and_print_css_present():
    css = re.search(r"<style>(.*?)</style>", _py(BASE), re.S).group(1).replace(" ", "")
    assert "prefers-reduced-motion:reduce" in css and "print" in css
    assert ".crt-scr{transform:none!important;filter:none!important;" in css
    assert ".crt-fx{display:none!important}" in css
    assert "@keyframescrt-gone{from{visibility:visible}to{visibility:hidden}}" in css
    assert "animation:crt-gone1slinearpausedboth;animation-delay:calc(var(--p,1)*-1s)" in css


def test_registered_everywhere():
    root = Path(__file__).resolve().parent.parent
    import yaml
    schema = yaml.safe_load((root / "atoms" / "schema.yaml").read_text())
    ent = [a for a in schema["blocks"] if isinstance(a, dict) and a.get("type") == "motion_crt_off"]
    assert len(ent) == 1 and ent[0]["stage"] == "preview"
    for k in ("description", "compact_description", "routing_text", "intent_phrases", "fields", "notes", "surfaces", "source"):
        assert ent[0].get(k), k
    assert len(ent[0]["intent_phrases"]) >= 3
    for f in ("blocks", "glow", "curve", "scanlines", "version"):
        assert f in ent[0]["fields"], f
    packs = yaml.safe_load((root / "atoms" / "atom-packs.yaml").read_text())
    assert "motion_crt_off" in packs["a2ui-effects-v1"]
    assert '"motion_crt_off":"a2ui-effects-v1"' in (root / "apps-script-surface" / "gas-wired-renderer" / "PackMap.gs").read_text()
    assert '"motion_crt_off"' in (root / "scripts" / "generate_atom_pages.py").read_text()


# ─── Browser tests ────────────────────────────────────────────────────────────
def _page(block_html: str, p, width: int, js: str, extra_args=()):
    page = ("<!doctype html><meta charset=utf-8><body style='margin:0;font:28px system-ui;background:#0b1020;color:#e8ecf4'><div style='width:" + str(width) + "px;padding:0;--p:" + str(p) + "'>" + block_html
            + "</div><script>document.documentElement.setAttribute('data-probe', JSON.stringify((function(){" + js + "})()));</script>")
    if p is None:
        page = page.replace("--p:None", "")
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "p.html"
        f.write_text(page)
        out = subprocess.run([CHROMIUM, "--headless=new", "--password-store=basic", "--no-sandbox", "--disable-gpu", f"--window-size={width},900", "--virtual-time-budget=1000", *extra_args,
                              "--dump-dom", f"file://{f}"], capture_output=True, text=True, timeout=90).stdout
    m = re.search(r"data-probe='([^']*)'|data-probe=\"([^\"]*)\"", out)
    assert m, out[:300]
    return json.loads(_h.unescape(m.group(1) or m.group(2)))


_CRT_STATE = ("var scr=document.querySelector('[data-crt=scr]'),line=document.querySelector('[data-crt=line]'),dot=document.querySelector('[data-crt=dot]');"
              "var st=getComputedStyle(scr);var tr=st.transform;var m=/matrix\\(([^)]+)\\)/.exec(tr);var parts=m?m[1].split(',').map(function(v){return +v.trim();}):[1,0,0,1,0,0];"
              "return {a:parts[0],d:parts[3],scrOp:+st.opacity,scrVis:st.visibility,lineOp:line?+getComputedStyle(line).opacity:0,dotOp:dot?+getComputedStyle(dot).opacity:0};")


@browser
def test_two_phase_collapse_and_decay(core_js):
    for blk in (BASE, KID):
        for html in (_py(blk), _gas_batch(core_js, [blk])[0]):
            for w in (650, 320):
                st0 = _page(html, 0, w, _CRT_STATE)
                assert abs(st0["a"] - 1.0) < 0.01 and abs(st0["d"] - 1.0) < 0.01 and st0["scrOp"] == 1 and st0["scrVis"] == "visible"

                st30 = _page(html, 0.30, w, _CRT_STATE)
                assert 0.2 < st30["d"] < 0.95 and abs(st30["a"] - 1.0) < 0.01

                st50 = _page(html, 0.50, w, _CRT_STATE)
                assert st50["d"] < 0.02 and abs(st50["a"] - 1.0) < 0.01 and st50["lineOp"] > 0.5

                st62 = _page(html, 0.62, w, _CRT_STATE)
                assert 0.02 < st62["a"] < 0.5 and st62["d"] < 0.02

                st70 = _page(html, 0.70, w, _CRT_STATE)
                assert st70["dotOp"] > 0.5 and st70["scrOp"] == 0

                st85 = _page(html, 0.85, w, _CRT_STATE)
                assert 0 <= st85["dotOp"] < st70["dotOp"]

                st1 = _page(html, 1, w, _CRT_STATE)
                assert st1["scrVis"] == "hidden" and st1["dotOp"] == 0 and st1["lineOp"] == 0

                std = _page(html, None, w, _CRT_STATE)
                assert std["scrVis"] == "hidden" and std["dotOp"] == 0 and std["lineOp"] == 0


@browser
def test_scalex_and_scaley_monotone_non_increasing(core_js):
    js = ("var r=document.querySelector('[data-crt=root]'),scr=document.querySelector('[data-crt=scr]'),out=[];"
          "for(var i=0;i<=100;i++){r.parentNode.style.setProperty('--p',i/100);var m=/matrix\\(([^)]+)\\)/.exec(getComputedStyle(scr).transform);"
          "var p=m?m[1].split(',').map(function(v){return +v.trim();}):[1,0,0,1,0,0];out.push([p[0],p[3]]);}return out;")
    for html in (_py(BASE), _gas_batch(core_js, [BASE])[0]):
        pts = _page(html, 0, 650, js)
        for idx in range(len(pts) - 1):
            assert pts[idx + 1][0] <= pts[idx][0] + 1e-5, f"scaleX not non-increasing at {idx}: {pts[idx][0]} -> {pts[idx+1][0]}"
            assert pts[idx + 1][1] <= pts[idx][1] + 1e-5, f"scaleY not non-increasing at {idx}: {pts[idx][1]} -> {pts[idx+1][1]}"


@browser
def test_no_overflow_at_narrow_screen(core_js):
    js = ("var r=document.querySelector('[data-crt=root]').getBoundingClientRect();"
          "return {w:r.width,sw:document.documentElement.scrollWidth,iw:innerWidth,rl:r.left,rr:r.right};")
    for blk in (BASE, KID):
        for html in (_py(blk), _gas_batch(core_js, [blk])[0]):
            for p in (0, 0.3, 0.5, 0.7, 1):
                d = _page(html, p, 320, js)
                assert d["rl"] >= -0.01 and d["rr"] <= 320 + 0.01 and d["sw"] <= d["iw"], (p, d)


@browser
def test_reduced_motion_behavior(core_js):
    js = ("var r=document.querySelector('[data-crt=root]'),scr=document.querySelector('[data-crt=scr]'),line=document.querySelector('[data-crt=line]'),dot=document.querySelector('[data-crt=dot]');"
          "function g(p){r.parentNode.style.setProperty('--p',p);var st=getComputedStyle(scr);var m=/matrix\\(([^)]+)\\)/.exec(st.transform);"
          "var parts=m?m[1].split(',').map(function(v){return +v.trim();}):[1,0,0,1,0,0];"
          "return {a:parts[0],d:parts[3],op:+st.opacity,lineDisp:getComputedStyle(line).display,dotDisp:getComputedStyle(dot).display};}"
          "return [g(0.3),g(0.6),g(0.65)];")
    for html in (_py(BASE), _gas_batch(core_js, [BASE])[0]):
        res = _page(html, 0, 650, js, ("--force-prefers-reduced-motion",))
        assert abs(res[0]["a"] - 1.0) < 0.01 and abs(res[0]["d"] - 1.0) < 0.01
        assert abs(res[1]["a"] - 1.0) < 0.01 and abs(res[1]["d"] - 1.0) < 0.01
        assert 0 < res[2]["op"] < 1
        for item in res:
            assert item["lineDisp"] == "none" and item["dotDisp"] == "none"


@browser
def test_line_and_dot_opacities_have_no_flicker(core_js):
    js = ("var r=document.querySelector('[data-crt=root]'),line=document.querySelector('[data-crt=line]'),dot=document.querySelector('[data-crt=dot]'),out=[];"
          "for(var i=0;i<=200;i++){r.parentNode.style.setProperty('--p',i/200);out.push([+getComputedStyle(line).opacity,+getComputedStyle(dot).opacity]);}return out;")
    for html in (_py(BASE), _gas_batch(core_js, [BASE])[0]):
        ser = _page(html, 0, 650, js)

        def humps(v):
            changes = 0
            down = False
            for a, b in zip(v, v[1:]):
                if b < a - 1e-5:
                    down = True
                elif b > a + 1e-5 and down:
                    changes += 1
                    down = False
            return changes

        assert humps([s[0] for s in ser]) == 0, "line opacity must have at most one rise and fall"
        assert humps([s[1] for s in ser]) == 0, "dot opacity must have at most one rise and fall"
