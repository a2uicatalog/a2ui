"""motion_shatter (backlog I69, from the owner's video review of 2026-10-21, event 11): crack lines radiate from an impact point across a block, the block
splits into polygonal shards that fall and spin away, revealing what is behind.

Cracks are the borders of a seeded Voronoi partition of the box (never a random call); each shard is an aria-hidden, inert copy of the content clipped to
its cell. END STATE: p = 1 is GONE (the source shows the block gone), p = 0 is whole. The real content is in the accessibility tree while it is visible and
is hidden from it (visibility) only when gone. Reduced motion: no shards, no cracks, no falling; a plain fade to the same gone end state. Print: whole.

ACCESSIBILITY (WCAG 2.3.1): nothing oscillates (no sin(), no keyframed loops); every opacity is monotone or one rise and one fall, so no flashing at all.
Same layers as test_motion_lightning.py: Python == GAS byte for byte, options closed and inert, hostile input never becomes markup, a real browser at fixed p.
"""
from __future__ import annotations

import html as _h
import json
import re
import subprocess
import tempfile
from pathlib import Path

import pytest

from test_motion_atoms import CHROMIUM, _gas_batch, _norm, _py, browser, core_js  # noqa: F401

HOSTILE = 'x";}</style><script>alert(1)</script><b onload="1"'
BASE = {"type": "motion_shatter"}
KID = {"type": "motion_shatter", "blocks": [{"type": "motion_pill", "text": "Continue"}]}

CASES = [
    BASE, dict(BASE, shards=4), dict(BASE, shards=24), dict(BASE, shards=0), dict(BASE, shards=99), dict(BASE, shards="9"), dict(BASE, shards="x"), dict(BASE, shards=None), dict(BASE, shards=True), dict(BASE, shards=7.9), dict(BASE, shards=-3),
    dict(BASE, origin="top"), dict(BASE, origin="bottom"), dict(BASE, origin="left"), dict(BASE, origin="right"), dict(BASE, origin="center"), dict(BASE, origin="nope"), dict(BASE, origin=HOSTILE), dict(BASE, origin=7), dict(BASE, origin=None),
    dict(BASE, origin={"x": 20, "y": 80}), dict(BASE, origin={"x": 50}), dict(BASE, origin={}), dict(BASE, origin={"x": "70", "y": "x"}), dict(BASE, origin={"x": 999, "y": -999}), dict(BASE, origin=[10, 20]),
    dict(BASE, cracks=False), dict(BASE, cracks=True), dict(BASE, cracks="no"), dict(BASE, cracks=0), dict(BASE, cracks=None),
    dict(BASE, fall="down"), dict(BASE, fall="out"), dict(BASE, fall="up"), dict(BASE, fall=HOSTILE), dict(BASE, fall=5), dict(BASE, fall=None),
    dict(BASE, spin=0), dict(BASE, spin=180), dict(BASE, spin=999), dict(BASE, spin=-5), dict(BASE, spin="x"), dict(BASE, spin=None), dict(BASE, spin=33.6),
    dict(BASE, seed=0), dict(BASE, seed=7), dict(BASE, seed=9999), dict(BASE, seed=123456), dict(BASE, seed=-5), dict(BASE, seed="x"), dict(BASE, seed=None), dict(BASE, seed=3.7),
    dict(BASE, version=2), dict(BASE, version=1), dict(BASE, version="x"), dict(BASE, version=1.5),
    dict(BASE, shards=24, origin={"x": 33, "y": 41}, fall="out", spin=120, seed=4242),
    KID,
    {"type": "motion_shatter", "blocks": [{"type": "motion_pill", "id": "a1", "text": "Go"}, {"type": "demo_panel", "title": "T", "rows": [["a", "1"]]}], "fall": "out"},
    {"type": "motion_shatter", "blocks": ["x", 3, None, {"type": "nope"}]}, {"type": "motion_shatter", "blocks": []},
    {"type": "motion_shatter", "blocks": [{"type": "motion_pill", "id": "k1", "text": "Go"}] * 6}, {"type": "motion_shatter", "blocks": "javascript:alert(1)"},
    dict(BASE, id="s1", enter="rise"),
] + [dict(BASE, seed=s, shards=4 + s % 21, origin=["top", "bottom", "left", "right", "center", {"x": s * 3 % 100, "y": s * 7 % 100}][s % 6], fall=["down", "out"][s % 2], spin=s * 5 % 181) for s in range(1, 40)]


def _count(h, name):
    return len(re.findall(r'data-sh="' + name + '"', h))


def _polys(h):
    out = []
    for m in re.findall(r'data-sh="shard"[^>]*?clip-path:polygon\(([^)]*)\)', h):
        out.append([tuple(float(v) for v in pt.replace('%', '').split()) for pt in m.split(',')])
    return out


def _area(p):
    return abs(sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))) / 2


def test_python_matches_gas_exactly(core_js):
    got = _gas_batch(core_js, CASES)
    bad = [str(b)[:110] for b, g in zip(CASES, got) if _norm(_py(b)) != _norm(g)]
    assert not bad, bad


def test_structure_is_decorative_inert_and_scriptless():
    h = _py(KID)
    assert "<script" not in h.lower() and "<button" not in h and "<img" not in h and "<foreignObject" not in h and "role=" not in h and "tabindex" not in h and "Math.random" not in h
    box = re.search(r'<div[^>]*data-sh="shards"[^>]*>', h).group(0)
    assert 'aria-hidden="true"' in box and " inert" in box and "pointer-events:none" in box
    assert 'aria-hidden="true"' in re.search(r'<svg\b[^>]*>', h).group(0)
    assert _count(h, "face") == 1 + 12 and h.count(">Continue<") % 13 == 0 and ">Continue<" in h, "the real content once, plus one inert copy per shard"
    body = re.search(r'<div[^>]*data-sh="body"[^>]*>', h).group(0)
    assert "aria-hidden" not in body and " inert" not in body


def test_copies_carry_no_duplicate_ids():
    h = _py({"type": "motion_shatter", "blocks": [{"type": "motion_pill", "id": "dup", "text": "Go"}]})
    assert h.count('data-mt-id="dup"') == 1 and len(re.findall(r'[ \t]id="dup"', h)) <= 1


def test_shard_count_is_closed_and_default_twelve():
    for n in range(4, 25):
        assert _count(_py(dict(BASE, shards=n)), "shard") == n
    assert _count(_py(BASE), "shard") == 12
    for bad in ("x", None, True):
        assert _count(_py(dict(BASE, shards=bad)), "shard") in (12, 4), bad
    assert _count(_py(dict(BASE, shards=99)), "shard") == 24 and _count(_py(dict(BASE, shards=0)), "shard") == 4 and _count(_py(dict(BASE, shards=-3)), "shard") == 4
    for s in range(0, 600, 13):
        for o in ("top", "center", {"x": 100, "y": 100}):
            assert _count(_py(dict(BASE, shards=24, seed=s, origin=o)), "shard") == 24, (s, o)


def test_the_shards_tile_the_box_and_are_seeded():
    for s in (0, 7, 55, 9999):
        for n in (4, 12, 24):
            ps = _polys(_py(dict(BASE, shards=n, seed=s)))
            assert len(ps) == n and all(len(p) >= 3 for p in ps)
            assert abs(sum(_area(p) for p in ps) - 10000) < 12, (s, n, sum(_area(p) for p in ps))
            assert all(0 <= x <= 100 and 0 <= y <= 100 for p in ps for x, y in p)
    assert _py(dict(BASE, seed=5)) == _py(dict(BASE, seed=5)) != _py(dict(BASE, seed=6))
    assert _py(dict(BASE, seed="x")) == _py(BASE) == _py(dict(BASE, seed=7))


def test_shards_are_small_near_the_impact_point_and_bigger_far_from_it():
    for o, (ox, oy) in (("top", (50, 0)), ("center", (50, 50)), ({"x": 20, "y": 80}, (20, 80))):
        ps = _polys(_py(dict(BASE, shards=16, origin=o)))
        cen = [(sum(x for x, _ in p) / len(p), sum(y for _, y in p) / len(p)) for p in ps]
        d = [((1.6 * (cx - ox)) ** 2 + (0.9 * (cy - oy)) ** 2) ** .5 for cx, cy in cen]   # shards are made in a 160 x 90 space
        near = sorted(range(len(ps)), key=lambda i: d[i])[:4]
        far = sorted(range(len(ps)), key=lambda i: d[i])[-4:]
        assert sum(_area(ps[i]) for i in near) < sum(_area(ps[i]) for i in far), o


def test_origin_is_a_named_edge_or_a_percent_point_and_bad_values_are_the_default():
    top = _py(BASE)
    assert _py(dict(BASE, origin="top")) == top
    for bad in ("nope", HOSTILE, 7, None, [10, 20], True):
        assert _py(dict(BASE, origin=bad)) == top, bad
    assert _py(dict(BASE, origin="left")) != top and _py(dict(BASE, origin="center")) != top
    assert _py(dict(BASE, origin={"x": 50})) == _py(dict(BASE, origin={"x": 50, "y": 50})) == _py(dict(BASE, origin="center"))
    assert _py(dict(BASE, origin={"x": 999, "y": -999})) == _py(dict(BASE, origin={"x": 100, "y": 0}))
    assert "circle(" in _py(BASE) and " at 50% 0%" in _py(BASE) and " at 20% 80%" in _py(dict(BASE, origin={"x": 20, "y": 80}))


def test_cracks_are_on_by_default_and_only_an_explicit_false_turns_them_off():
    h = _py(BASE)
    assert _count(h, "cracks") == 1 and "<path" in h
    off = _py(dict(BASE, cracks=False))
    assert _count(off, "cracks") == 0 and "<svg" not in off and off != h
    for v in ("no", 0, None, True):
        assert _py(dict(BASE, cracks=v)) == h, v


def test_fall_down_goes_down_and_out_goes_away_from_the_origin_and_bad_is_down():
    d = _py(BASE)
    assert _py(dict(BASE, fall="down")) == d
    for bad in ("up", HOSTILE, 5, None):
        assert _py(dict(BASE, fall=bad)) == d, bad
    assert _py(dict(BASE, fall="out")) != d
    ys = [float(m) for m in re.findall(r'--ty:(-?[\d.]+)', d)]
    assert len(ys) == 12 and all(y > 0 for y in ys), ys
    h = _py(dict(BASE, fall="out", origin="center", shards=16))
    xs = [float(m) for m in re.findall(r'--tx:(-?[\d.]+)', h)]
    ys = [float(m) for m in re.findall(r'--ty:(-?[\d.]+)', h)]
    cen = [(sum(x for x, _ in p) / len(p) - 50, sum(y for _, y in p) / len(p) - 50) for p in _polys(h)]
    same = sum(1 for (cx, cy), x, y in zip(cen, xs, ys) if cx * x + cy * y > 0)
    assert same >= 14, (same, "shards move away from the impact point")


def test_spin_is_capped_in_degrees_and_zero_means_no_rotation():
    for cap in (0, 20, 90, 180):
        rots = [abs(float(m)) for m in re.findall(r'--rz:(-?[\d.]+)', _py(dict(BASE, spin=cap, shards=24)))]
        assert len(rots) == 24 and max(rots) <= cap + 1e-9, (cap, max(rots))
    assert max(abs(float(m)) for m in re.findall(r'--rz:(-?[\d.]+)', _py(dict(BASE, spin=0)))) == 0
    big = [abs(float(m)) for m in re.findall(r'--rz:(-?[\d.]+)', _py(dict(BASE, spin=999, shards=24)))]
    assert max(big) <= 180 and _py(dict(BASE, spin=999)) == _py(dict(BASE, spin=180))
    assert _py(dict(BASE, spin=-5)) == _py(dict(BASE, spin=0)) and _py(dict(BASE, spin="x")) == _py(BASE)
    assert max(abs(float(m)) for m in re.findall(r'--rz:(-?[\d.]+)', _py(BASE))) <= 40


def test_defaults_written_out_are_inert():
    assert _py(dict(BASE, shards=12, cracks=True, fall="down", spin=40, seed=7, version=1)) == _py(BASE)


# ─── WCAG 2.3.1: nothing oscillates ──────────────────────────────────────────
def test_nothing_in_the_output_oscillates():
    for blk in (BASE, KID, dict(BASE, shards=24, fall="out")):
        h = _py(blk)
        assert "sin(" not in h and "cos(" not in h and "steps(" not in h and "infinite" not in h and "Math.random" not in h
        assert h.count("animation:sh-gone") == 1 and "iteration-count" not in h


def test_hostile_values_never_reach_markup():
    h = _py(dict(BASE, origin=HOSTILE, cracks=HOSTILE, fall=HOSTILE, spin=HOSTILE, seed=HOSTILE, shards=HOSTILE, version=HOSTILE))
    h = re.sub(r"<style>[^<]*</style>", "", h, count=1)
    assert "<script" not in h and not re.search(r"<[^>]*onload=", h) and "</style>" not in h and "<style" not in h and "<b " not in h
    assert "NaN" not in h and "undefined" not in h and "Infinity" not in h and "[object" not in h and "alert(1)" not in h


def test_children_stay_readable_and_are_capped_at_three():
    h = _py({"type": "motion_shatter", "shards": 4, "blocks": [{"type": "motion_pill", "text": str(i)} for i in range(6)]})
    assert ">0<" in h and ">2<" in h and ">3<" not in h
    assert 'data-sh="body"' in _py({"type": "motion_shatter", "blocks": ["x", 3, None]}), "no usable child: the plain panel"
    assert _py({"type": "motion_shatter", "blocks": ["x", 3, None]}) == _py(BASE)


def test_every_moving_value_reads_p():
    h = _py(KID)
    assert "var(--p,1)" in h and not re.search(r"var\(--s[,)]", h) and "<script" not in h.lower()


def test_reduced_motion_is_a_plain_fade_to_the_same_gone_end_and_print_is_whole():
    css = re.search(r"<style>(.*?)</style>", _py(BASE), re.S).group(1).replace(" ", "")
    assert "prefers-reduced-motion:reduce" in css and "print" in css
    assert ".sh-shards,.sh-cracks{display:none!important}" in css
    red = css.split("@media(prefers-reduced-motion:reduce)")[1].split("}}")[0]
    assert ".sh-body{opacity:clamp(0," in red and "var(--p,1)" in red
    prn = css.split("@mediaprint")[1]
    assert "opacity:1!important" in prn and "animation:none!important" in prn


def test_the_real_content_is_hidden_from_assistive_tech_only_when_gone():
    css = re.search(r"<style>(.*?)</style>", _py(BASE), re.S).group(1).replace(" ", "")
    assert "@keyframessh-gone{from{visibility:visible}to{visibility:hidden}}" in css
    assert "animation-delay:calc(var(--p,1)*-1s)" in css and "paused" in css


def test_version_note():
    assert "version" not in _py(BASE).lower().replace("data-sh", "") and _py(dict(BASE, version=1)) == _py(BASE) and _py(dict(BASE, version="x")) == _py(BASE)
    h = _py(dict(BASE, version=3))
    assert "Written for motion_shatter version 3; drawn as version 1." in h
    assert h.replace(re.search(r'<div style="font-size:0.75rem[^>]*>Written for[^<]*</div>', h).group(0), "") == _py(BASE)


def test_registered_everywhere():
    root = Path(__file__).resolve().parent.parent
    import yaml
    schema = yaml.safe_load((root / "atoms" / "schema.yaml").read_text())
    ent = [a for a in schema["blocks"] if isinstance(a, dict) and a.get("type") == "motion_shatter"]
    assert len(ent) == 1 and ent[0]["stage"] == "preview"
    for k in ("description", "compact_description", "routing_text", "intent_phrases", "fields", "notes", "surfaces", "source"):
        assert ent[0].get(k), k
    assert len(ent[0]["intent_phrases"]) >= 2
    for f in ("blocks", "shards", "origin", "cracks", "fall", "spin", "seed", "version"):
        assert f in ent[0]["fields"], f
    packs = yaml.safe_load((root / "atoms" / "atom-packs.yaml").read_text())
    assert "motion_shatter" in packs["a2ui-effects-v1"]
    assert '"motion_shatter":"a2ui-effects-v1"' in (root / "apps-script-surface" / "gas-wired-renderer" / "PackMap.gs").read_text()
    assert '"motion_shatter"' in (root / "scripts" / "generate_atom_pages.py").read_text()


# ─── a real browser: fixed p, at 650 and 320 px ──────────────────────────────
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


_STATE = ("var b=document.querySelector('[data-sh=body]'),c=document.querySelector('[data-sh=cracks]'),sh=Array.prototype.slice.call(document.querySelectorAll('[data-sh=shard]'));"
          "var cm=c?/circle\\(([\\d.]+)(px|%)/.exec(getComputedStyle(c).clipPath):null;var so=sh.map(function(e){return +getComputedStyle(e).opacity;});"
          "return {body:+getComputedStyle(b).opacity,vis:getComputedStyle(b).visibility,cracks:c?+getComputedStyle(c).opacity:null,reach:cm?+cm[1]:null,mx:so.length?Math.max.apply(null,so):0,"
          "n:so.length,vs:sh.filter(function(e){return +getComputedStyle(e).opacity>0}).length};")


@browser
def test_whole_at_zero_cracking_then_shards_then_gone_at_one(core_js):
    for blk in (BASE, KID):
        for html in (_py(blk), _gas_batch(core_js, [blk])[0]):
            st = {p: _page(html, p, 650, _STATE) for p in (0, 0.15, 0.25, 0.5, 0.75, 0.99, 1)}
            assert st[0]["body"] == 1 and st[0]["reach"] == 0 and st[0]["mx"] == 0 and st[0]["vis"] == "visible", st[0]
            assert st[0.15]["body"] == 1 and st[0.15]["cracks"] == 1 and st[0.15]["reach"] > 0 and st[0.25]["reach"] > st[0.15]["reach"] and st[0.15]["mx"] == 0, st[0.15]
            assert st[0.5]["body"] == 0 and st[0.5]["mx"] > 0.5 and st[0.5]["vs"] == st[0.5]["n"] == 12, st[0.5]
            assert st[0.75]["body"] == 0 and 0 < st[0.75]["mx"] <= 1 and st[0.75]["vis"] == "visible"
            assert st[0.99]["vis"] == "visible", "still in the accessibility tree until it is gone"
            assert st[1]["vis"] == "hidden" and st[1]["mx"] == 0 and st[1]["cracks"] == 0 and st[1]["body"] == 0, st[1]
            d = _page(html, None, 650, _STATE)
            assert d["vis"] == "hidden" and d["mx"] == 0, "the standalone render is the finished picture: gone"


@browser
def test_opacities_only_ever_fall_or_rise_once_so_nothing_flashes(core_js):
    js = ("var r=document.querySelector('[data-sh=root]'),b=document.querySelector('[data-sh=body]'),c=document.querySelector('[data-sh=cracks]'),sh=Array.prototype.slice.call(document.querySelectorAll('[data-sh=shard]')),out=[];"
          "for(var i=0;i<=200;i++){r.parentNode.style.setProperty('--p',i/200);var s=sh.map(function(e){return +getComputedStyle(e).opacity;});out.push([+getComputedStyle(b).opacity,+getComputedStyle(c).opacity,s]);}return out;")
    blk = dict(KID, shards=24)
    for html in (_py(blk), _gas_batch(core_js, [blk])[0]):
        ser = _page(html, 0, 650, js)

        def peaks(v):
            """number of direction changes that are rises after a fall (a second hump)"""
            n, down = 0, False
            for a, b in zip(v, v[1:]):
                if b < a - 1e-6:
                    down = True
                elif b > a + 1e-6 and down:
                    n += 1
                    down = False
            return n
        assert peaks([s[0] for s in ser]) == 0 and peaks([s[1] for s in ser]) == 0
        for i in range(24):
            assert peaks([s[2][i] for s in ser]) == 0, i
        assert sum(1 for s in ser if s[2][0] > 0 and s[0] > 0) <= 3, "the real content and the shards swap over at one instant, they do not overlap for long"


_BOX = ("var r=document.querySelector('[data-sh=root]').getBoundingClientRect();return {w:r.width,h:r.height,sw:document.documentElement.scrollWidth,iw:innerWidth,rl:r.left,rr:r.right};")


@browser
def test_nothing_is_wider_than_the_container_even_when_the_shards_fly_out(core_js):
    for blk in (BASE, dict(BASE, fall="out", shards=24, spin=180), dict(KID, fall="out", origin="left"), {"type": "motion_shatter", "fall": "out", "blocks": [{"type": "motion_text", "text": "Hello there", "size": 40}]}):
        for html in (_py(blk), _gas_batch(core_js, [blk])[0]):
            for w in (650, 320):
                for p in (0, 0.4, 0.6, 0.8, 1):
                    d = _page(html, p, w, _BOX)
                    assert d["rl"] >= -0.01 and d["rr"] <= w + 0.01 and d["sw"] <= d["iw"], (w, p, d)
                    assert d["h"] > 20, d


@browser
def test_the_content_is_present_in_the_tree_and_the_copies_are_not(core_js):
    js = ("var b=document.querySelector('[data-sh=body]');var cp=document.querySelectorAll('[data-sh=shards] [data-sh=shard]');"
          "return {txt:b.textContent.replace(/\\s+/g,' ').trim(),inert:document.querySelector('[data-sh=shards]').inert,fs:getComputedStyle(b.querySelector('span,div,p')||b).fontSize,n:cp.length};")
    for html in (_py(KID), _gas_batch(core_js, [KID])[0]):
        d = _page(html, 0.5, 650, js)
        assert d["txt"].replace("Continue", "") == "" and "Continue" in d["txt"] and d["inert"] is True and d["n"] == 12 and float(d["fs"][:-2]) >= 12, d


@browser
def test_reduced_motion_is_a_plain_fade_with_no_shards_and_no_cracks(core_js):
    for html in (_py(KID), _gas_batch(core_js, [KID])[0]):
        js = ("var r=document.querySelector('[data-sh=root]').parentNode;function g(p){r.style.setProperty('--p',p);var b=document.querySelector('[data-sh=body]');return [+getComputedStyle(b).opacity,getComputedStyle(b).visibility,"
              "getComputedStyle(document.querySelector('[data-sh=shards]')).display,getComputedStyle(document.querySelector('[data-sh=cracks]')).display];}return [g(0),g(0.3),g(0.65),g(0.99),g(1)];")
        s = _page(html, 0, 650, js, ("--force-prefers-reduced-motion",))
        assert s[0][0] == 1 and s[1][0] == 1 and 0 < s[2][0] < 1 and 0 < s[3][0] < 0.1 and s[4][0] == 0 and s[4][1] == "hidden" and s[3][1] == "visible", s
        assert all(x[2] == "none" and x[3] == "none" for x in s), s
        s = _page(html, 0, 650, js)
        assert s[2][0] == 0 and s[2][2] == "block", s
