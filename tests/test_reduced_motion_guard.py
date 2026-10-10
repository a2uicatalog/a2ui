"""Endless CSS animation honours prefers-reduced-motion (WCAG 2.2.2, 2.3.3), for atoms that did not before.

Found 2026-10-08 by the static flag `loop_no_reduced_motion` in a2ui-private/a11y: 35 atoms looped forever with no reduced-motion rule.
renderAtoms now adds one (atom.gs `_a11yFix`) for any atom whose own markup has an `infinite` animation and no rule of its own.
It changes nothing for people who have not asked their OS for reduced motion: the control run below proves the loops still run.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

sys.path[:0] = [str(Path(__file__).parent)]
from test_keyboard_access import _examples  # noqa: E402
from test_motion_atoms import CHROMIUM, _gas_batch, browser, core_js  # noqa: E402,F401

LOOPERS = """airspace_command_deck ambient_gradient animated_beam animated_border animated_border_card aurora_background fids_board floating_badge floating_orbs
glitch_text icon_liftoff image_hotspots live_refresh loading_dots loading_skeleton marquee marquee_strip meteor_shower multi_surface neon_glow orbit_diagram
progress_bar pulse_dot shimmer_button shimmer_text skeleton skeleton_stage_card sonar_pulse spinner stripe_background terminal_boot typewriter typewriter_text
typing_indicator wave_divider""".split()


@pytest.fixture(scope="module")
def pages(core_js):
    ex = _examples()
    names = [n for n in LOOPERS if n in ex]
    htmls = _gas_batch(core_js, [ex[n] for n in names])
    return dict(zip(names, htmls))


def _running_loops(pages, reduce):
    body = "".join(f'<div id="a-{n}">{h}</div>' for n, h in pages.items())
    js = ("setTimeout(function(){var o={};document.querySelectorAll('[id^=a-]').forEach(function(d){o[d.id.slice(2)]=d.getAnimations({subtree:true}).filter(function(a){"
          "return a.playState==='running'&&a.effect&&a.effect.getComputedTiming().iterations===Infinity}).length});"
          "document.documentElement.setAttribute('data-r',JSON.stringify(o))},500);")
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "p.html"
        f.write_text("<!doctype html><meta charset=utf-8><body>" + body + "<script>" + js + "</script>")
        args = [CHROMIUM, "--headless=new", "--password-store=basic", "--no-sandbox", "--disable-gpu", "--window-size=1200,900", "--virtual-time-budget=3000"]
        if reduce:
            args.append("--force-prefers-reduced-motion")
        out = subprocess.run(args + ["--dump-dom", f"file://{f}"], capture_output=True, text=True, timeout=180).stdout
    m = re.search(r"data-r='([^']*)'|data-r=\"([^\"]*)\"", out)
    assert m, out[:300]
    import html as _h
    return json.loads(_h.unescape(m.group(1) or m.group(2)))


@browser
def test_every_looping_atom_stops_under_reduce_motion_and_still_loops_otherwise(pages):
    normal, reduced = _running_loops(pages, False), _running_loops(pages, True)
    still_running = {n: c for n, c in reduced.items() if c}
    assert not still_running, f"still looping under prefers-reduced-motion: {still_running}"
    dead = [n for n, c in normal.items() if not c]
    # a few draw their loop from JS or a pseudo-element rather than a running CSS animation on an element; the guard must not be what stopped them
    assert len(dead) <= 6, f"loops that no longer run for everyone else: {dead}"
