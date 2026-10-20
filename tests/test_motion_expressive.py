"""Expressive motion (2026-10-09): path-following tracks with a trail, and the opt-in text / pill / stack3d / shape options.

Everything here is OFF by default, so the first group of tests proves the old output is untouched, the second proves the GAS and Python
twins agree byte for byte (including on hostile input), and the third runs the timeline in real headless Chromium at fixed instants and
reads back what it did to the DOM. Skipped if no Chromium is installed.

The helpers come from test_motion_atoms.py (the same Node harness and probe).
"""
from __future__ import annotations

import re

import pytest

from test_motion_atoms import (CHROMIUM, _gas_batch, _norm, _probe, _py, _scene, browser, core_js)  # noqa: F401  (core_js is a fixture)

num = lambda v: float(re.search(r"-?[0-9.]+(?:e-?[0-9]+)?", str(v)).group(0))  # noqa: E731

PATH_TL = {
    "type": "motion_timeline", "duration": 4, "controls": False, "autoplay": False, "ease": "linear", "title": "P",
    "blocks": [{"type": "motion_pill", "id": "dot", "text": "Go", "place": {"x": 10, "y": 50, "w": 12}}],
    "tracks": [{"target": "dot", "path": "M10 50 L90 50", "orient": True, "trail": {"n": 3, "lag": 0.2},
                "keys": [{"t": 0, "a": 0}, {"t": 3, "a": 1}]}],
}

TEXT = {"type": "motion_text", "text": "Make work *easier*\nwherever it *happens*", "size": 64}

PAYLOADS = {
    "motion_timeline": [
        PATH_TL,
        dict(PATH_TL, tracks=[dict(PATH_TL["tracks"][0], orient=False, trail={"n": 99, "lag": 99})]),
        dict(PATH_TL, tracks=[dict(PATH_TL["tracks"][0], trail={"n": "x", "lag": "y"})]),
        dict(PATH_TL, tracks=[dict(PATH_TL["tracks"][0], path='M 0 0 L 1 1" onload="x')]),            # hostile path: dropped
        dict(PATH_TL, tracks=[dict(PATH_TL["tracks"][0], path="javascript:alert(1)")]),
        dict(PATH_TL, tracks=[dict(PATH_TL["tracks"][0], path="M0 0 " + "L1 1 " * 400)]),            # over the length limit
        dict(PATH_TL, tracks=[dict(PATH_TL["tracks"][0], path="M10 50\n\tC 30 20, 60 80, 90 50")]),  # whitespace is normalised
        dict(PATH_TL, tracks=[dict(PATH_TL["tracks"][0], keys=[{"t": 0, "x": 5}, {"t": 2, "x": 9}])]),  # no `a` key: path ignored
        dict(PATH_TL, tracks=[dict(PATH_TL["tracks"][0], path=12)]),
        dict(PATH_TL, blocks=[dict(PATH_TL["blocks"][0], place={"x": 10, "y": 50})]),                  # no place.w: the trail is dropped and counted
        dict(PATH_TL, bpm=120, tracks=[dict(PATH_TL["tracks"][0], keys=[{"beat": 0, "a": 0}, {"beat": 8, "a": 1, "ease": "expo-out"}, {"beat": 9, "a": 7}])]),
    ],
    "motion_text": [
        TEXT,
        dict(TEXT, accent_gradient=["#ff2d6f", "#19d3ff"]), dict(TEXT, accent_gradient=["#ff2d6f"]), dict(TEXT, accent_gradient=["red", "<b>"]),
        dict(TEXT, glow=24), dict(TEXT, glow=999, glow_color="#ff0000"), dict(TEXT, glow=-5), dict(TEXT, glow="x", glow_color="javascript:1"),
        dict(TEXT, shine=True), dict(TEXT, shine=True, extrude=4, mode="chars"), dict(TEXT, shine="yes"),
        dict(TEXT, reveal="reel"), dict(TEXT, reveal="reel", text="your role\nyour teams\nhow you operate", align="middle", line_height=1.2),
        dict(TEXT, reveal="reel", text="one", align="end"),
        {"type": "motion_text", "text": "Built for", "cycle": ["developers", "teams", "everyone"]},
        {"type": "motion_text", "text": "", "cycle": ["on your phone", "the web", "the terminal"], "accent_gradient": ["#4285f4", "#34a853"]},
        {"type": "motion_text", "cycle": ["only one"]}, {"type": "motion_text", "cycle": ["<img src=x onerror=alert(1)>", "b", "c", "d", "e", "f", "g", "h"]},
        {"type": "motion_text", "cycle": "nope"}, {"type": "motion_text", "text": "x", "cycle": [1, None, {"a": 1}, "ok", "ok2"]},
        dict(TEXT, glow=20, shine=True, accent_gradient=["#4285f4", "#34a853"], cycle=["a", "b"], reveal="mask", mode="words"),
    ],
    "motion_pill": [
        {"type": "motion_pill", "text": "Compliance *Agent*"}, {"type": "motion_pill", "text": "Glow", "glow": 20},
        {"type": "motion_pill", "text": "Border", "border_gradient": ["#4285f4", "#ea4335"]}, {"type": "motion_pill", "text": "Both", "border_gradient": ["#4285f4", "#ea4335"], "glow": 18, "fill": "#0b1220"},
        {"type": "motion_pill", "text": "Bad", "border_gradient": ["x", "y"], "glow": 999}, {"type": "motion_pill", "text": "One", "border_gradient": ["#ffffff"]},
    ],
    "motion_stack3d": [
        {"type": "motion_stack3d", "items": ["A", {"title": "B", "text": "second"}, {"title": "C", "icon": "◆"}]},
        {"type": "motion_stack3d", "mode": "coverflow", "items": ["Phone", "Web", "Laptop", "Terminal"]},
        {"type": "motion_stack3d", "mode": "coverflow", "w": 300, "h": 200, "items": [{"title": "<b>x</b>", "text": "t"}]},
        {"type": "motion_stack3d", "mode": "<x>", "items": ["A", "B"]},
    ],
    "motion_input": [
        {"type": "motion_input", "text": "Complete the attached RFP", "chip": "Request for Proposal", "label": "Ask for approval"},
        {"type": "motion_input"}, {"type": "motion_input", "text": "x" * 500, "tone": "dark", "accent": "#ff3355", "size": 30},
        {"type": "motion_input", "text": "<img src=x onerror=alert(1)> & \"quotes\" ' and \\ slashes", "chip": "<b>chip</b>", "label": "<script>1</script>", "accent": "red\";}"},
        {"type": "motion_input", "text": "emoji \U0001f600 and  double  spaces", "size": 9999}, {"type": "motion_input", "tone": "<x>", "text": 12},
    ],
    "demo_cursor": [{"type": "demo_cursor"}, {"type": "demo_cursor", "kind": "hand", "label": "Agent"}, {"type": "demo_cursor", "kind": "<x>", "label": "<b>"}],
    "motion_shader": [{"type": "motion_shader", "kind": "dots", "color1": "#f4f7ff", "color2": "#7fa6f7", "color3": "#3b6fe0", "scale": 3},
                      {"type": "motion_shader", "kind": "vortex", "scale": 12, "span": 5, "still": True}, {"type": "motion_shader", "kind": "tunnel"}, {"type": "motion_shader", "kind": "dots", "scale": 99, "radius": 9999}],
    "motion_shape": [
        {"type": "motion_shape", "shape": "ring", "draw": "pulse", "thickness": 6}, {"type": "motion_shape", "shape": "circle", "draw": "pulse", "lag": 0.4, "fill": "#ff3355"},
        {"type": "motion_shape", "shape": "ring", "draw": "pulse", "lag": 9}, {"type": "motion_shape", "shape": "rect", "draw": "pulse"}, {"type": "motion_shape", "shape": "line", "draw": "pulse"},
    ],
}
CASES = [(t, b) for t, bs in PAYLOADS.items() for b in bs]


def test_every_new_option_has_a_parity_case():
    covered = " ".join(str(b) for _t, b in CASES)
    for key in ("path", "orient", "trail", "accent_gradient", "glow_color", "shine", "reel", "cycle", "border_gradient", "coverflow", "pulse", "lag", "motion_input", "hand", "dots", "vortex"):
        assert key in covered, key


def test_python_matches_gas_exactly(core_js):
    got = _gas_batch(core_js, [b for _t, b in CASES])
    bad = []
    for (t, b), g in zip(CASES, got):
        if _norm(_py(b)) != _norm(g):
            bad.append((t, str(b)[:110]))
    assert not bad, bad


def test_new_options_are_inert_when_off():
    """Writing the defaults explicitly must not change a byte, and a block with none of the options keeps its old markup shape."""
    plain = _py(dict(TEXT))
    off = _py(dict(TEXT, glow=0, shine=False, cycle=[], accent_gradient=[]))
    assert _norm(plain) == _norm(off)
    assert "drop-shadow" not in plain and "background-clip" not in plain and "grid-area" not in plain and "reel" not in plain
    assert "box-shadow" not in _py({"type": "motion_pill", "text": "x"})
    assert "abs(var(--d))" not in _py({"type": "motion_stack3d", "items": ["a", "b"]})


def test_hostile_values_never_become_markup():
    html = _py({"type": "motion_text", "cycle": ["<img src=x onerror=alert(1)>", "b"], "accent_gradient": ["red\";}</style><script>1</script>", "#fff"]})
    assert "<img" not in html and "<script>1" not in html and "onerror=alert(1)>" not in html
    tl = _py(dict(PATH_TL, tracks=[dict(PATH_TL["tracks"][0], path='M 0 0" onload="alert(1)')]))
    assert "onload" not in tl and ',d:"' not in tl, "a path outside the strict grammar is dropped, not escaped"
    assert "ignored 1 invalid" in tl or "ignored 2 invalid" in tl, "and it is counted, never silent"
    cfg = re.search(r"var C=(\{.*?\});var root", _py(PATH_TL), re.S).group(1)
    assert re.search(r'd:"M10 50 L90 50"', cfg) and not re.search(r"[<>`\\]", cfg)


def test_trail_needs_a_numeric_width_and_says_so():
    html = _py(dict(PATH_TL, blocks=[dict(PATH_TL["blocks"][0], place={"x": 10, "y": 50})]))
    assert "tr0g1" not in html and "ignored 1 invalid" in html


def test_trail_makes_n_ghosts_behind_the_original():
    html = _py(PATH_TL)
    assert [m for m in re.findall(r'data-mt-id="(tr0g[0-9])"', html)] == ["tr0g1", "tr0g2", "tr0g3"]
    assert re.search(r'data-mt-id="tr0g1"[^>]*aria-hidden="true"[^>]*z-index:0', html)


# ─── the client maths, in real headless Chromium ───────────────────────────────────────────────────────────────────────────────────

def _tr(dom_js_id: str) -> str:
    return "var e=document.querySelector('[data-mt-id=%s]');return e?e.style.transform:null;" % dom_js_id


@browser
def test_element_rides_the_path_to_the_exact_point():
    tl = dict(PATH_TL, tracks=[dict(PATH_TL["tracks"][0], orient=False)])
    # the run is 3 s long on a 1280 px stage: a at t=1.5 is 0.5, so the point is x = 50 percent; the element sits at x = 10, so it moves 40 percent = 512 px
    got = _probe(tl, 1.5, _tr("dot"))
    assert num(re.search(r"translate\(([-0-9.]+)px", got).group(1)) == pytest.approx(512, abs=1.0), got
    start = _probe(tl, 0, _tr("dot"))
    assert num(re.search(r"translate\(([-0-9.]+)px", start).group(1)) == pytest.approx(0, abs=0.5)
    end = _probe(tl, 3, _tr("dot"))
    assert num(re.search(r"translate\(([-0-9.]+)px", end).group(1)) == pytest.approx(1024, abs=1.0)


@browser
def test_a_curved_path_is_followed_not_cut_across():
    tl = dict(PATH_TL, tracks=[{"target": "dot", "path": "M10 50 C 30 10, 70 10, 90 50", "keys": [{"t": 0, "a": 0}, {"t": 4, "a": 1}]}])
    got = _probe(tl, 2, _tr("dot"))
    ty = num(re.search(r"translate\([-0-9.]+px,\s*([-0-9.]+)px", got).group(1))
    assert ty < -100, "the curve bows upward (y percent below the start), a straight line would stay at 0: " + got


@browser
def test_orient_turns_the_element_to_the_direction_of_travel():
    down = dict(PATH_TL, tracks=[{"target": "dot", "path": "M10 10 L10 90", "orient": True, "keys": [{"t": 0, "a": 0}, {"t": 4, "a": 1}]}],
                blocks=[dict(PATH_TL["blocks"][0], place={"x": 10, "y": 10, "w": 12})])
    got = _probe(down, 2, _tr("dot"))
    assert re.search(r"rotate\(([-0-9.]+)deg\)", got) and num(re.search(r"rotate\(([-0-9.]+)deg\)", got).group(1)) == pytest.approx(90, abs=1.0), got
    flat = _probe(PATH_TL, 1.5, _tr("dot"))
    assert num(re.search(r"rotate\(([-0-9.]+)deg\)", flat).group(1)) == pytest.approx(0, abs=1.0)


@browser
def test_trail_ghosts_follow_the_same_path_a_little_later():
    tl = PATH_TL
    got = _probe(tl, 2, "var f=function(i){var e=document.querySelector('[data-mt-id='+i+']');return e?[e.style.transform,+e.style.opacity]:null};return [f('dot'),f('tr0g1'),f('tr0g2'),f('tr0g3')];")
    xs = [num(re.search(r"translate\(([-0-9.]+)px", g[0]).group(1)) for g in got]
    # lag 0.2 s per ghost on a 3 s run across 1024 px: each ghost trails by 0.2/3 * 1024 = 68.3 px
    assert xs[0] - xs[1] == pytest.approx(68.3, abs=1.5) and xs[1] - xs[2] == pytest.approx(68.3, abs=1.5) and xs[2] - xs[3] == pytest.approx(68.3, abs=1.5), xs
    assert [g[1] for g in got] == pytest.approx([got[0][1], 0.5, 0.5 * (1 - 1 / 3), 0.5 * (1 - 2 / 3)], abs=0.01)
    before = _probe(tl, 0, "var e=document.querySelector('[data-mt-id=tr0g2]');return +e.style.opacity;")
    after = _probe(tl, 4, "var e=document.querySelector('[data-mt-id=tr0g2]');return +e.style.opacity;")
    assert before == 0 and after == 0, "ghosts are invisible before the move and gone after it"


def _opac(sel):
    return 'var u=document.querySelectorAll("%s");return Array.prototype.map.call(u,function(e){return +getComputedStyle(e).opacity;});' % sel


@browser
def test_reel_focuses_one_line_and_dims_the_rest_with_the_second_dial():
    blk = _scene([{"type": "motion_text", "id": "t", "text": "your role\nyour teams\nhow you operate", "reveal": "reel", "place": {"x": 5, "y": 5, "w": 80}}],
                 [{"target": "t", "keys": [{"t": 0, "step": 0}, {"t": 4, "step": 1}]}])
    sel = "[data-mt-id=t] span[aria-hidden] > span > span"
    s0 = _probe(blk, 0, _opac(sel))
    assert s0 == pytest.approx([1, 0.34, 0], abs=0.02), "at step 0 the first line has the focus, the next is dimmed, the third is gone"
    mid = _probe(blk, 2, _opac(sel))
    assert mid == pytest.approx([0.34, 1, 0.34], abs=0.02), "halfway the middle line is sharp and both neighbours are dimmed"
    s1 = _probe(blk, 4, _opac(sel))
    assert s1 == pytest.approx([0, 0.34, 1], abs=0.02)


@browser
def test_cycle_swaps_words_in_place_with_a_crossfade():
    blk = _scene([{"type": "motion_text", "id": "t", "text": "", "cycle": ["on your phone", "the web", "the terminal"], "place": {"x": 5, "y": 5, "w": 80}}],
                 [{"target": "t", "keys": [{"t": 0, "step": 0}, {"t": 4, "step": 1}]}])
    sel = "[data-mt-id=t] span[style*='grid-area']"
    assert _probe(blk, 0, _opac(sel)) == pytest.approx([1, 0, 0], abs=0.02)
    assert _probe(blk, 2, _opac(sel)) == pytest.approx([0, 1, 0], abs=0.02)
    assert _probe(blk, 4, _opac(sel)) == pytest.approx([0, 0, 1], abs=0.02)


@browser
def test_shine_is_a_transparent_copy_clipped_to_the_letters():
    blk = _scene([{"type": "motion_text", "id": "t", "text": "24/7", "shine": True, "size": 120, "place": {"x": 5, "y": 5, "w": 80}}], [{"target": "t", "keys": [{"t": 0, "step": 0}, {"t": 4, "step": 1}]}])
    got = _probe(blk, 2, "var e=document.querySelector(\"[data-mt-id=t] span[style*='pointer-events:none']\");var c=getComputedStyle(e);return [c.webkitBackgroundClip||c.backgroundClip,c.color,e.textContent];")
    assert got[0] == "text" and got[2] == "24/7" and got[1] == "rgba(0, 0, 0, 0)"


@browser
def test_coverflow_dims_and_pushes_back_the_cards_away_from_the_focus():
    blk = _scene([{"type": "motion_stack3d", "id": "c", "mode": "coverflow", "items": ["Phone", "Web", "Laptop"], "place": {"x": 10, "y": 10, "w": 80}}],
                 [{"target": "c", "keys": [{"t": 0, "step": 0}, {"t": 4, "step": 1}]}])
    sel = "[data-mt-id=c] div[style*='--d']"
    at0, at2, at4 = (_probe(blk, t, _opac(sel)) for t in (0, 2, 4))
    # d = i - s*(n-1); opacity = clamp(1.1 - |d|*0.34): focus 1.0, one step away 0.76, two away 0.42
    assert at0 == pytest.approx([1, 0.76, 0.42], abs=0.02) and at2 == pytest.approx([0.76, 1, 0.76], abs=0.02) and at4 == pytest.approx([0.42, 0.76, 1], abs=0.02)


@browser
def test_ripple_swells_and_fades_and_lag_delays_it():
    mk = lambda lag: _scene([{"type": "motion_shape", "id": "r", "shape": "ring", "draw": "pulse", "lag": lag, "w": 200, "h": 200, "place": {"x": 30, "y": 20, "w": 20}}],  # noqa: E731
                            [{"target": "r", "keys": [{"t": 0, "step": 0}, {"t": 4, "step": 1}]}])
    js = "var e=document.querySelector('[data-mt-id=r] div');var c=getComputedStyle(e);return [+c.opacity,c.transform];"
    o0, _ = _probe(mk(0), 0, js)
    o1, t1 = _probe(mk(0), 2, js)
    o2, _ = _probe(mk(0), 4, js)
    assert o0 == 0 and o2 == 0 and o1 == pytest.approx(0.5, abs=0.02), "invisible at both ends, half way through it is half faded"
    assert num(re.search(r"matrix\(([-0-9.]+)", t1).group(1)) == pytest.approx(0.8, abs=0.02), "and scaled 0.35 + 0.45"
    late = _probe(mk(0.5), 2, js)
    assert late[0] == 0, "with lag 0.5 nothing has started at s = 0.5"


@browser
def test_input_types_one_character_at_a_time_and_the_caret_sits_on_the_last_one():
    blk = _scene([{"type": "motion_input", "id": "in", "text": "hello", "chip": "File.pdf", "place": {"x": 5, "y": 5, "w": 60}}],
                 [{"target": "in", "keys": [{"t": 0, "p": 0}, {"t": 4, "p": 1}]}])
    js = ("var s=document.querySelectorAll('[data-mt-id=in] div[style*=\"pre-wrap\"] > span');"
          "return Array.prototype.map.call(s,function(e){var c=getComputedStyle(e);var a=(c.boxShadow===\"none\"||/ *\\/ *0\\)/.test(c.boxShadow))?0:1;return [+c.opacity,a];});")
    assert [round(o) for o, _ in _probe(blk, 0, js)] == [0, 0, 0, 0, 0]
    mid = _probe(blk, 2, js)    # p = 0.5 of 5 characters: three are typed (0.5 * 5 = 2.5), and the caret is on the third
    assert [round(o) for o, _ in mid] == [1, 1, 1, 0, 0]
    end = _probe(blk, 4, js)
    assert [round(o) for o, _ in end] == [1, 1, 1, 1, 1]
    carets = lambda rows: [i for i, (_o, c) in enumerate(rows) if c > 0.5]  # noqa: E731
    assert carets(end) == [4], "the caret stays on the last character at the end"
    assert carets(mid) == [2] and carets(_probe(blk, 0, js)) == [], "and it follows the typing, with none before the first key"
    chip = _probe(blk, 0, "return +getComputedStyle(document.querySelector('[data-mt-id=in] div[style*=\"0.62em\"]')).opacity;")
    assert chip == 0


@browser
def test_send_button_presses_with_the_second_dial():
    blk = _scene([{"type": "motion_input", "id": "in", "text": "go", "place": {"x": 5, "y": 5, "w": 60}}],
                 [{"target": "in", "keys": [{"t": 0, "step": 0}, {"t": 4, "step": 1}]}])
    js = "var e=document.querySelector('[data-mt-id=in] span[style*=\"border-radius:50%\"]');return getComputedStyle(e).transform;"
    sc = lambda t: num(re.search(r"matrix\(([-0-9.]+)", _probe(blk, t, js)).group(1))  # noqa: E731
    assert sc(0) == pytest.approx(1, abs=0.01) and sc(2) == pytest.approx(0.86, abs=0.01) and sc(4) == pytest.approx(1, abs=0.01)


def test_hand_cursor_is_its_own_drawing_and_arrow_is_unchanged():
    arrow, hand = _py({"type": "demo_cursor"}), _py({"type": "demo_cursor", "kind": "hand"})
    assert 'viewBox="0 0 22 26"' in arrow and 'viewBox="0 0 26 30"' in hand and 'viewBox="0 0 22 26"' not in hand


# ---- reduced motion (2026-10-10): the new options inherit the engine's guard; these lock that in ----

def test_no_new_option_loops_forever_without_a_reduced_motion_rule():
    for t, b in CASES:
        out = _py(b)
        if re.search(r"animation[^;\"]*infinite", out):
            assert "prefers-reduced-motion" in out, (t, b)


def _moved_after(block, flag):
    """Render in headless Chromium (optionally with the OS reduce-motion setting) and report whether the DOM changed between 0.4 s and 2.4 s.

    Real time, not --virtual-time-budget: under virtual time headless Chromium never fires requestAnimationFrame (and the timeline
    plays from rAF), so the control film stayed still and the test failed (I18). --dump-dom fires at the load event, so a local
    server holds a trailing <script> for 3 s to keep the page alive in real time while the 0.4 s / 2.4 s timers run."""
    import http.server
    import shutil
    import subprocess
    import tempfile
    import threading
    import time
    from pathlib import Path

    class Hold(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            time.sleep(3)
            self.send_response(200)
            self.send_header("Content-Type", "text/javascript")
            self.end_headers()

        def log_message(self, *a):
            pass

    sig = ("function sig(){var o=[];document.querySelectorAll('body *').forEach(function(e){var c=getComputedStyle(e);"
           "o.push(c.transform+c.opacity+c.filter+e.style.cssText+e.textContent.length)});return o.join('|');}")
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Hold)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    profile = tempfile.mkdtemp(prefix="a2ui-chromium-")
    try:
        page = ("<!doctype html><meta charset=utf-8><body style='margin:0'>" + _py(block) + "<script>" + sig
                + "var s1;setTimeout(function(){s1=sig();},400);setTimeout(function(){document.documentElement.setAttribute('data-moved',String(s1!==sig()));},2400);</script>"
                + f"<script src='http://127.0.0.1:{srv.server_port}/hold.js'></script>")
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "p.html"
            f.write_text(page)
            args = [CHROMIUM, "--headless=new", "--password-store=basic", "--no-sandbox", "--disable-gpu", "--window-size=1000,700",
                    f"--user-data-dir={profile}"]
            if flag:
                args.append("--force-prefers-reduced-motion")
            out = subprocess.run(args + ["--dump-dom", f"file://{f}"], capture_output=True, text=True, timeout=120).stdout
    finally:
        srv.shutdown()
        shutil.rmtree(profile, ignore_errors=True)
    m = re.search(r'data-moved="(true|false)"', out)
    assert m, out[:300]
    return m.group(1) == "true"


@browser
def test_an_autoplaying_path_film_holds_still_under_the_reduce_motion_setting():
    tl = dict(PATH_TL, autoplay=True, controls=True)
    assert _moved_after(tl, False), "control: the film should play normally"
    assert not _moved_after(tl, True), "under prefers-reduced-motion the film must not start by itself"
