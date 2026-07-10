"""gen_mcp_apps_bundle.py extracts a fixed atom subset from the GAS renderer
source (ground truth per CLAUDE.md) into a browser-portable MCP Apps View
bundle. Assert structure, not just "did it run" — a broken extraction (wrong
brace matching, a dropped renderer) still produces *some* HTML.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import gen_mcp_apps_bundle as gen  # noqa: E402


def test_bundle_contains_view_protocol_handshake():
    bundle = gen.build_bundle()
    assert "ui/initialize" in bundle
    assert "ui/notifications/initialized" in bundle
    assert "ui/notifications/tool-result" in bundle
    assert "window.parent.postMessage" in bundle


def test_bundle_re_executes_injected_scripts():
    # innerHTML-injected <script> tags never run — the paint() function must
    # manually re-create + re-append them, or flashcard_deck's flip does
    # nothing.
    bundle = gen.build_bundle()
    assert "createElement('script')" in bundle
    assert "replaceChild(fresh, old)" in bundle


def test_bundle_inlines_atom_styles_css():
    bundle = gen.build_bundle()
    # AtomStyles.html styles headings/paragraphs by bare tag selector, not
    # the asw-heading/asw-body class names the renderers emit — assert on
    # what's actually there rather than the renderer's class attributes.
    assert "h2 {" in bundle
    assert ".asw-callout" in bundle
    assert "--accent" in bundle  # AtomStyles.html theme custom properties


def test_static_renderers_render_expected_structure():
    payload = {
        "theme": "dark",
        "blocks": [
            {"type": "heading", "level": 2, "text": "Test Heading"},
            {"type": "body", "text": "Hello **world**."},
            {"type": "paragraph", "text": "A paragraph."},
        ],
    }
    html = _run_render_atoms(payload)
    assert '<h2 class="asw-heading">Test Heading</h2>' in html
    assert '<p class="asw-body">Hello <strong>world</strong>.</p>' in html
    assert '<p class="asw-paragraph">A paragraph.</p>' in html


def test_flashcard_deck_renders_flip_structure():
    payload = {
        "theme": "light",
        "blocks": [
            {
                "type": "flashcard_deck",
                "cards": [{"front": "Q1", "back": "A1"}, {"front": "Q2", "back": "A2"}],
            }
        ],
    }
    html = _run_render_atoms(payload)
    # uid-scoped flip/next/prev controller, matching atoms_lms.gs's contract
    assert "window[" in html
    assert ".flip()" in html
    assert ".next()" in html
    assert ".prev()" in html
    assert "Q1" in html and "A1" in html
    assert "1 / 2" in html
    # the renderer's own <script> block must close and its runtime output
    # is the unescaped tag (the \/ escape only matters at the JS-source
    # level, checked separately below).
    assert "</script>" in html


def test_flashcard_deck_script_close_tag_is_source_escaped():
    # atoms_lms.gs writes the closing tag as <\/script> inside the JS string
    # literal so it can't prematurely close the bundle's own outer <script>
    # block when this renderer's output gets embedded inline. Confirm the
    # extraction preserved that escape at the SOURCE level (pre-execution).
    bundle = gen.build_bundle()
    assert r"<\/script>" in bundle


def test_bundle_contains_curated_rocket_panel():
    # gdm_rocket_panel is NOT a catalog atom -- hand-ported from the Meet
    # Stage add-on, not extracted from any .gs source. Confirm it's present
    # and clearly distinguished in the generator's own comments.
    bundle = gen.build_bundle()
    assert "_RENDERERS['gdm_rocket_panel']" in bundle
    # provenance comment (not a .gs source, so not extracted like the others)
    # lives in the .py source, not the generated output -- check it there.
    assert "gdm_stage_rocket_panel.ts" in Path(gen.__file__).read_text()


def test_rocket_panel_renders_canvas_and_loop():
    html = _run_render_atoms({"blocks": [{"type": "gdm_rocket_panel", "height": 480}]})
    assert "<canvas" in html
    assert "requestAnimationFrame(loop)" in html
    assert "fonts.gstatic.com" in html  # Apps Script logo badge
    assert "APPS SCRIPT · CORE SERVICE" in html  # HUD telemetry text
    assert "</script>" in html


def test_unknown_atom_type_degrades_gracefully():
    html = _run_render_atoms({"blocks": [{"type": "not_a_real_atom"}]})
    assert "not included in this MCP Apps demo bundle" in html


def _run_render_atoms(payload):
    """Extract the bundle's core JS (renderer functions, no protocol
    handshake) and execute renderAtoms() against `payload` via Node."""
    import json
    import re
    import subprocess

    bundle = gen.build_bundle()
    match = re.search(r"<script>\n(.*?)\n</script>\s*</body>", bundle, re.S)
    js = match.group(1)
    core = js[: js.index("// ---- MCP Apps View protocol handshake")]
    script = core + "\nconsole.log(renderAtoms(%s.blocks || [], {theme: %s}));" % (
        json.dumps(payload),
        json.dumps(payload.get("theme")),
    )
    result = subprocess.run(["node", "-e", script], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return result.stdout
