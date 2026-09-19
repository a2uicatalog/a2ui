"""halftone_wave + message_lanes (2026-09-19), on the flow_field canvas kit.
Parity between the GAS and Python renderers modulo uid, config baked as
declared, and the overlay's new ink colour (halftone_wave is the first
light-ground hero, so its copy must be set in ink, not white)."""
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

from renderers.web_article import _render_halftone_wave, _render_message_lanes, _render_flow_field  # noqa: E402

PY = {"halftone_wave": _render_halftone_wave, "message_lanes": _render_message_lanes}
UID_RE = re.compile(r"\b(hw|ml)-[a-z0-9]{6}\b")


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


def _cfg(html: str) -> str:
    return re.search(r"var C=(\{.*?\});\s*var ", html).group(1)


PAYLOADS = {
    "halftone_wave": [
        {},
        {"title": "It's print, alive", "eyebrow": "halftone", "body": "**dots** on paper", "wave": "ripple", "focus": "right",
         "accent": "#0E7BB8", "spacing": "coarse", "speed": "fast", "height": 420, "align": "right", "interactive": False},
        {"ink": "#f1f5f9", "paper": "#0b0d12", "wave": "sweep", "title": "dark flip"},
        {"wave": "nope", "spacing": 12, "accent": "red", "height": 5},
    ],
    "message_lanes": [
        {},
        {"from_label": "Claude's agent", "to_label": "claude.ai <surface>", "lanes": 6, "rate": "fast", "title": "One agent, every surface",
         "colors": ["#ffffff"], "background": "#000000", "height": 500},
        {"from_label": "", "to_label": "x" * 80, "lanes": 99, "rate": "nope"},
    ],
}


@pytest.mark.parametrize("atom,block", [(a, b) for a, bs in PAYLOADS.items() for b in bs])
def test_python_matches_gas_exactly(core_js, atom, block):
    assert _norm(_gas(core_js, dict(block, type=atom))) == _norm(PY[atom](dict(block)))


def test_halftone_config_and_light_ink_overlay():
    html = _render_halftone_wave(PAYLOADS["halftone_wave"][1])
    assert _cfg(html) == '{sp:20,sc:0.0045,spd:1.8,wave:"ripple",focus:"right",ink:"#0f172a",paper:"#f7f7f5",acc:"#0e7bb8",hasAcc:true,inter:false}'
    assert "color:#0f172a;letter-spacing" in html and "rgba(15,23,42,0.78)" in html   # copy set in ink, not white
    assert "background:#f7f7f5" in html and "height:420px" in html
    html = _render_halftone_wave(PAYLOADS["halftone_wave"][3])
    assert _cfg(html) == '{sp:14,sc:0.0045,spd:1,wave:"noise",focus:"center",ink:"#0f172a",paper:"#f7f7f5",acc:"#0f172a",hasAcc:false,inter:true}'
    assert "height:160px" in html


def test_flow_field_overlay_unchanged_for_the_dark_default():
    html = _render_flow_field({"title": "t", "body": "b"})
    assert "color:#ffffff;letter-spacing" in html and "rgba(255,255,255,0.78)" in html


def test_message_lanes_labels_are_json_strings_and_clamped():
    html = _render_message_lanes(PAYLOADS["message_lanes"][1])
    assert 'from:"Claude\'s agent",to:"claude.ai \\u003csurface>"' in html and "lanes:6,rate:1.7" in html
    assert 'pal:["255,255,255","255,255,255"]' in html   # single colour is doubled so pal[1] exists
    html = _render_message_lanes(PAYLOADS["message_lanes"][2])
    assert 'from:"agent"' in html and 'to:"' + "x" * 24 + '"' in html and "lanes:6,rate:1," in html


@pytest.mark.parametrize("atom", list(PY))
def test_scripts_pass_node_syntax_check(atom):
    html = PY[atom](PAYLOADS[atom][1])
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "s.js"
        f.write_text(re.search(r"<script>(.*)</script>", html, re.S).group(1))
        assert subprocess.run(["node", "--check", str(f)], capture_output=True, text=True).returncode == 0
