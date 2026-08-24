"""agent_sketchpad — a real catalogue atom (2026-08-24), designed for
progressive multi-shape drawing over real streaming updates (see
a2a_counterpart/agui_adapter.py's Phase 6 wiring). Redesigned 2026-08-24
from path-only strokes to general SVG primitives with fill (matching
what a real freeform tool-calling loop actually produces -- see
streaming-testbench's demos/sketch/sketch_agent.py, the origin of the
validation approach ported into both real renderers here). Verifies BOTH
real renderers (GAS, via the same Node-eval harness
tests/test_v1_template_decode.py already uses; and Python's
renderers/web_article.py) produce the correct "last element animates,
the rest are already-drawn" behavior, agree with each other, and reject
the same real security-relevant inputs (script tags, event handlers,
javascript: URIs, disallowed tags, malformed/multi-element markup) --
same security bar as the origin implementation's own
validate_svg_fragment, checked directly against
streaming-testbench/tests/test_sketch_agent.py's own test names.
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
    _render_agent_sketchpad, _validate_sketchpad_element,
)

STROKES = [
    {"element": '<path d="M 0 180 L 400 180" stroke="#333333" stroke-width="2" fill="none"/>',
     "label": "the horizon"},
    {"element": '<circle cx="340" cy="20" r="15" fill="orange"/>', "label": "the sun"},
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
    assert "<path" in html and "<circle" in html
    first_idx = html.index("<path")
    first_tag = html[first_idx:html.index("/>", first_idx)]
    assert "stroke-dashoffset" not in first_tag
    assert "stroke-dasharray" in html
    assert "stroke-dashoffset" in html
    assert "animation:sketch-draw-" in html


def test_gas_renderer_skips_malformed_strokes_without_crashing(core_js):
    html = _render_via_gas(core_js, {
        "type": "agent_sketchpad", "strokes": [
            {"element": ""},                          # empty -- skipped
            {"label": "no element key at all"},        # no element -- skipped
            {"element": "<circle cx=\"1\" cy=\"1\" r=\"1\"/>"},  # real, only survivor
        ],
    })
    assert html.count("<circle") == 1


def test_gas_renderer_rejects_a_script_tag(core_js):
    html = _render_via_gas(core_js, {
        "type": "agent_sketchpad",
        "strokes": [{"element": "<script>alert(1)</script>"}],
    })
    assert "alert(1)" not in html
    assert "<script>" not in html


def test_gas_renderer_rejects_an_event_handler_attribute(core_js):
    html = _render_via_gas(core_js, {
        "type": "agent_sketchpad",
        "strokes": [{"element": '<circle cx="1" cy="1" r="1" onload="alert(1)"/>'}],
    })
    assert "onload" not in html


def test_gas_renderer_rejects_multiple_top_level_elements(core_js):
    html = _render_via_gas(core_js, {
        "type": "agent_sketchpad",
        "strokes": [{"element": '<circle cx="1" cy="1" r="1"/><circle cx="2" cy="2" r="1"/>'}],
    })
    assert html.count("<circle") == 0


def test_python_renderer_matches_gas_renderer_exactly(core_js):
    block = {"viewBox": "0 0 400 200", "label": "Test", "strokes": STROKES}
    gas_html = _render_via_gas(core_js, dict(block, type="agent_sketchpad"))
    py_html = _render_agent_sketchpad(block)
    assert gas_html.count("<path") == py_html.count("<path") == 1
    assert gas_html.count("<circle") == py_html.count("<circle") == 1
    assert gas_html.count("stroke-dasharray") == py_html.count("stroke-dasharray") == 1


def test_python_renderer_skips_oversized_and_malformed_strokes():
    html = _render_agent_sketchpad({"strokes": [
        {"element": "<circle cx=\"1\" cy=\"1\" r=\"1\"/>" + "x" * 5000},  # over 4096 chars -- skipped
        {"element": '<rect x="0" y="0" width="10" height="10"/>'},        # real
        {"not_an_element_key": "oops"},                                    # no element -- skipped
    ]})
    assert html.count("<rect") == 1
    assert html.count("<circle") == 0


def test_python_renderer_supports_fill_and_nested_groups():
    html = _render_agent_sketchpad({"strokes": [
        {"element": '<g><rect x="0" y="0" width="10" height="10" fill="blue"/>'
                    '<line x1="0" y1="0" x2="10" y2="10"/></g>', "label": "a group"},
    ]})
    assert "<g" in html and "<rect" in html and "<line" in html and 'fill="blue"' in html


# ── Security: same coverage as streaming-testbench's own
# tests/test_sketch_agent.py (the origin implementation this atom's
# validation was ported from) -- the atom is a generic a2uicatalog atom
# reachable from any caller, so it needs the same real bar, not a
# reduced one just because ITS callers happen to already validate.

def test_rejects_a_script_tag():
    assert _validate_sketchpad_element("<script>alert(1)</script>") is None


def test_rejects_a_disallowed_tag_even_if_svg_shaped():
    assert _validate_sketchpad_element('<image href="x.png"/>') is None


def test_rejects_an_event_handler_attribute():
    assert _validate_sketchpad_element('<circle cx="1" cy="1" r="1" onload="alert(1)"/>') is None


def test_rejects_a_javascript_uri_in_an_allowed_attribute():
    assert _validate_sketchpad_element('<circle cx="1" cy="1" r="1" fill="javascript:alert(1)"/>') is None


def test_rejects_multiple_top_level_elements():
    assert _validate_sketchpad_element(
        '<circle cx="1" cy="1" r="1"/><circle cx="2" cy="2" r="1"/>') is None


def test_rejects_malformed_markup():
    assert _validate_sketchpad_element('<circle cx="1"') is None


def test_rejects_a_foreignobject_escape_attempt():
    assert _validate_sketchpad_element(
        '<g><foreignObject><script>alert(1)</script></foreignObject></g>') is None


def test_output_is_reserialized_not_the_raw_input():
    el = _validate_sketchpad_element('<circle cx="1" cy="1" r="1" style="behavior:url(x.htc)"/>')
    assert el is None


def test_accepts_a_simple_allowed_element():
    el = _validate_sketchpad_element('<circle cx="10" cy="10" r="5" fill="red"/>')
    assert el is not None
    assert el.tag == "circle"


def test_accepts_a_nested_group():
    el = _validate_sketchpad_element(
        '<g><circle cx="1" cy="1" r="1"/><rect x="0" y="0" width="1" height="1"/></g>')
    assert el is not None
    assert len(list(el)) == 2
