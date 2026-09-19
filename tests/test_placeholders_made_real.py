"""Until 2026-09-19 four a2ui-effects-v1 atoms -- floating_particles,
parallax_section, meteor_shower, effect_overlay -- rendered a dashed grey
"[... requires canvas/physics engine]" box on GAS and MCP Apps (the
_animFallback stub) while the Python web renderer drew something real, and
two of them were schema-declared "canvas fallback placeholders" everywhere.
This file pins the fix: real renderers on BOTH sides, identical modulo uid,
and the fallback text gone for good.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import gen_mcp_apps_bundle as gen  # noqa: E402

from renderers.web_article import (  # noqa: E402
    _render_floating_particles, _render_parallax_section, _render_meteor_shower, _render_effect_overlay,
)

PY = {"floating_particles": _render_floating_particles, "parallax_section": _render_parallax_section,
      "meteor_shower": _render_meteor_shower, "effect_overlay": _render_effect_overlay}
UID_RE = re.compile(r"\b(fp|px|met|ep-pulse|ep-fall|ep-trophy|ep-p)-[a-z0-9]{6}\b")


@pytest.fixture(scope="module")
def core_js():
    bundle = gen.build_bundle()
    blocks = re.findall(r"<script>\n(.*?)\n</script>", bundle, re.S)
    core = [b for b in blocks if "a2ui-core" in b[:300]]
    assert core, "a2ui-core script block missing"
    return core[0]


def _gas(core_js, block: dict) -> str:
    with tempfile.TemporaryDirectory() as td:
        driver = Path(td) / "d.js"
        driver.write_text(
            "global.window = global;\n" + core_js + f"""
var blocks = [{json.dumps(block)}];
console.log(JSON.stringify({{html: renderAtoms(blocks, {{}})}}));
""")
        proc = subprocess.run(["node", str(driver)], capture_output=True,
                              text=True, timeout=30)
        assert proc.returncode == 0, proc.stderr[-1000:]
        return json.loads(proc.stdout)["html"]


def _norm(html: str) -> str:
    return UID_RE.sub(r"\1-UID", html)


PAYLOADS = {
    "floating_particles": [{}, {"title": "It's alive", "body": "no more **grey** box", "colors": ["#ffffff"], "density": "high", "speed": "fast", "height": 400, "interactive": False},
                           {"label": "alias label"}, {"text": "alias text", "background": "#100010"}],
    "parallax_section": [{}, {"title": "Depth", "eyebrow": "layers", "depth": "deep", "height": 500}, {"label": "x", "depth": "nope", "interactive": False}],
    "meteor_shower": [{}, {"count": 40, "speed": "slow", "color": "#ff0000", "background": "#000000", "title": "Rain's here", "body": "**bold**"},
                      {"count": 999, "speed": "fast"}, {"count": 0}, {"count": "abc", "color": "red"}],
    "effect_overlay": [{}, {"trigger": "trophy", "status": "resolved", "message": "It's done"}, {"trigger": "pulse", "color": "#ff00ff", "message": "live"},
                       {"trigger": "fireworks"}, {"trigger": "nope", "color": "bad"}],
}


@pytest.mark.parametrize("atom,block", [(a, b) for a, bs in PAYLOADS.items() for b in bs])
def test_python_matches_gas_exactly(core_js, atom, block):
    gas_html = _gas(core_js, dict(block, type=atom))
    assert "requires canvas" not in gas_html and "_animFallback" not in gas_html
    assert _norm(gas_html) == _norm(PY[atom](dict(block)))


def test_no_fallback_stub_left_in_the_bundle():
    bundle = gen.build_bundle()
    assert "return _animFallback(" not in bundle


def test_meteor_count_is_clamped_and_timings_are_integer_hundredths():
    html = _render_meteor_shower({"count": 999, "speed": "fast"})
    assert html.count("<span") == 40
    assert "animation:met-" in html and " 0.6s linear 0s infinite" in html
    assert html.count("<span") == 40
    assert _render_meteor_shower({"count": 0}).count("<span") == 0
    assert "background:linear-gradient(transparent,#38bdf8)" in _render_meteor_shower({"color": "red"})


def test_effect_overlay_variants_and_fallbacks():
    assert "🏆" in _render_effect_overlay({"trigger": "trophy"}) and "ep-trophy-" in _render_effect_overlay({"trigger": "trophy"})
    assert "🎆" in _render_effect_overlay({"trigger": "fireworks"})
    pulse = _render_effect_overlay({"trigger": "pulse", "color": "bad"})
    assert "ep-pulse-" in pulse and "#00f2ff50" in pulse
    assert "🎉" in _render_effect_overlay({"trigger": "nope"})
    assert _render_effect_overlay({"trigger": "confetti"}).count('class="ep-p-') == 26


def test_canvas_versions_carry_the_kit_and_the_copy():
    html = _render_floating_particles({"title": "T <b>", "body": "B"})
    assert "window._a2uiCK=window._a2uiCK||" in html and "prefers-reduced-motion" in html
    assert "&lt;b&gt;" in html and "radial-gradient" in html
    assert "{n:120,spd:1," in html
    html = _render_parallax_section({"depth": "deep"})
    assert "{n:[3,6,14],depth:0.14," in html and "linear-gradient" not in html  # no copy -> no veil
