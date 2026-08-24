"""agent_sketchpad — a new real catalogue atom (2026-08-24), designed for
progressive multi-stroke drawing over real streaming updates (see
a2a_counterpart/agui_adapter.py's Phase 6 wiring). Verifies BOTH real
renderers (GAS, via the same Node-eval harness
tests/test_v1_template_decode.py already uses; and Python's
renderers/web_article.py) produce the correct "last stroke animates, the
rest are already-drawn" behavior, and that they agree with each other.
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

from renderers.web_article import _render_agent_sketchpad  # noqa: E402

STROKES = [
    {"path": "M 0 180 L 400 180", "color": "#333333", "width": 2},
    {"path": "M 340 20 m -15 0 a 15 15 0 1 0 30 0 a 15 15 0 1 0 -30 0",
     "color": "orange", "width": 3},
]


@pytest.fixture(scope="module")
def core_js():
    bundle = gen.build_bundle()
    blocks = re.findall(r"<script>\n(.*?)\n</script>", bundle, re.S)
    core = [b for b in blocks if "a2ui-core" in b[:300]]
    assert core, "a2ui-core script block missing"
    return core[0]


def _render_via_gas(core_js, block: dict) -> str:
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


def test_gas_renderer_only_animates_the_newest_stroke(core_js):
    html = _render_via_gas(core_js, {
        "type": "agent_sketchpad", "viewBox": "0 0 400 200", "strokes": STROKES,
    })
    # First (oldest) stroke: present, no animation styling.
    assert 'd="M 0 180 L 400 180"' in html
    first_stroke_idx = html.index('d="M 0 180 L 400 180"')
    first_stroke_tag = html[first_stroke_idx - 10:html.index("/>", first_stroke_idx)]
    assert "stroke-dashoffset" not in first_stroke_tag
    # Last (newest) stroke: present, WITH animation styling.
    assert "stroke-dasharray" in html
    assert "stroke-dashoffset" in html
    assert "animation:sketch-draw-" in html


def test_gas_renderer_skips_malformed_strokes_without_crashing(core_js):
    html = _render_via_gas(core_js, {
        "type": "agent_sketchpad", "strokes": [
            {"path": ""},                    # empty -- skipped
            {"color": "red"},                # no path at all -- skipped
            {"path": "M 0 0 L 10 10"},        # real, only survivor
        ],
    })
    assert html.count("<path") == 1
    assert 'd="M 0 0 L 10 10"' in html


def test_python_renderer_matches_gas_renderer_exactly(core_js):
    block = {"viewBox": "0 0 400 200", "label": "Test", "strokes": STROKES}
    gas_html = _render_via_gas(core_js, dict(block, type="agent_sketchpad"))
    py_html = _render_agent_sketchpad(block)
    # Both real strokes present with the same content in both renderers
    # (uid/keyframe-name differ, that's fine -- the drawable content and
    # the animate-only-the-last-stroke rule must match).
    for stroke in STROKES:
        assert f'd="{stroke["path"]}"' in gas_html
        assert f'd="{stroke["path"]}"' in py_html
    assert gas_html.count("<path") == py_html.count("<path") == 2
    assert gas_html.count("stroke-dasharray") == py_html.count("stroke-dasharray") == 1


def test_python_renderer_skips_oversized_and_malformed_strokes():
    html = _render_agent_sketchpad({"strokes": [
        {"path": "x" * 5000},              # over the 4096-char cap -- skipped
        {"path": "M 0 0 L 10 10"},          # real
        {"not_a_path_key": "oops"},         # no path -- skipped
    ]})
    assert html.count("<path") == 1
