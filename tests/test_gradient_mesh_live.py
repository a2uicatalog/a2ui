"""gradient_mesh_live (2026-09-19) — a canvas hero background whose whole config
is baked into inline JavaScript. Sibling of flow_field/signal_tunnel on the
same shared kit (_A2UI_CANVAS_KIT_JS), so the same two things are worth
proving on every run, against BOTH real renderers (GAS via the same Node-eval
harness tests/test_agent_sketchpad.py uses; Python via renderers/web_article.py):

1. Parity: the two renderers emit identical markup modulo the uid, so the
   MCP Apps bundle, the GAS /exec URLs and the Python web surface all show
   the same thing (the GAS/Python drift class that broke Card/Button/Tabs).
2. No free-form value reaches the script: colours must be #rrggbb, every
   other option is an enum or a clamped int, and copy is HTML-escaped. A
   payload that tries to break out of the config object gets the defaults.
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

from renderers.web_article import _render_gradient_mesh_live  # noqa: E402

UID_RE = re.compile(r"gm-[a-z0-9]{6}")


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


def _norm(html: str) -> str:
    return UID_RE.sub("gm-UID", html)


def _cfg(html: str) -> str:
    m = re.search(r"var C=(\{.*?\});", html)
    assert m, "config object not found in script"
    return m.group(1)


FULL = {
    "eyebrow": "Mesh", "title": "Colour that never repeats",
    "body": "Blobs drift on the same **noise field** as flow_field.",
    "align": "left", "colors": ["#38BDF8", "#818cf8", "#f472b6"],
    "background": "#070a12", "density": "high", "motion": "wild", "speed": "fast",
    "height": 420, "interactive": False,
}


@pytest.mark.parametrize("block", [
    {},
    FULL,
    {"title": "Centered", "align": "center", "motion": "subtle"},
    {"title": "Right", "align": "right", "colors": ["#ffffff"]},
])
def test_python_renderer_matches_gas_renderer_exactly(core_js, block):
    gas_html = _render_via_gas(core_js, dict(block, type="gradient_mesh_live"))
    py_html = _render_gradient_mesh_live(dict(block))
    assert _norm(gas_html) == _norm(py_html)


def test_script_runs_under_node_syntax_check():
    html = _render_gradient_mesh_live(FULL)
    script = re.search(r"<script>(.*)</script>", html, re.S).group(1)
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "s.js"
        f.write_text(script)
        proc = subprocess.run(["node", "--check", str(f)], capture_output=True, text=True)
        assert proc.returncode == 0, proc.stderr


def test_every_field_is_baked_as_declared():
    cfg = _cfg(_render_gradient_mesh_live(FULL))
    assert cfg == ('{n:6,spd:1.8,amp:0.34,'
                   'pal:["56,189,248","129,140,248","244,114,182"],'
                   'bg:"#070a12",inter:false}')


def test_defaults_when_nothing_is_set():
    html = _render_gradient_mesh_live({})
    assert _cfg(html) == ('{n:4,spd:1,amp:0.22,'
                          'pal:["56,189,248","129,140,248","244,114,182"],'
                          'bg:"#070a12",inter:true}')
    assert "height:360px" in html
    # no copy -> no veil, no overlay
    assert "linear-gradient" not in html and "radial-gradient" not in html


@pytest.mark.parametrize("bad", [
    '#fff");alert(1);//', "red", "#12345", "#1234567", "rgb(1,2,3)", 42, None, ["#000000"],
])
def test_free_form_colour_never_reaches_the_script(core_js, bad):
    block = {"colors": [bad], "background": bad}
    for html in (_render_gradient_mesh_live(block),
                 _render_via_gas(core_js, dict(block, type="gradient_mesh_live"))):
        assert "alert(" not in html
        assert 'bg:"#070a12"' in _cfg(html)
        assert '"56,189,248"' in _cfg(html)


def test_invalid_colours_are_dropped_not_fatal():
    cfg = _cfg(_render_gradient_mesh_live({"colors": ["nope", "#00ff00", "#zzzzzz", "#ff0000"]}))
    assert 'pal:["0,255,0","255,0,0"]' in cfg


def test_palette_capped_at_four():
    cfg = _cfg(_render_gradient_mesh_live({"colors": ["#010101"] * 9}))
    assert cfg.count("1,1,1") == 4


@pytest.mark.parametrize("value,expected", [
    ("huge", "4"), (None, "4"), (12, "4"), (["low"], "4"), ("low", "3"), ("high", "6"),
])
def test_enum_fields_fall_back_to_default(core_js, value, expected):
    block = {"density": value}
    for html in (_render_gradient_mesh_live(block),
                 _render_via_gas(core_js, dict(block, type="gradient_mesh_live"))):
        assert f"{{n:{expected}," in _cfg(html)


@pytest.mark.parametrize("value,expected", [
    ("sideways", "0.22"), (None, "0.22"), (7, "0.22"), (["wild"], "0.22"), ("wild", "0.34"), ("subtle", "0.14"),
])
def test_motion_falls_back_to_default(core_js, value, expected):
    block = {"motion": value}
    for html in (_render_gradient_mesh_live(block),
                 _render_via_gas(core_js, dict(block, type="gradient_mesh_live"))):
        assert f"amp:{expected}," in _cfg(html)


@pytest.mark.parametrize("value,expected", [
    (99999, 900), (-5, 200), (300, 300), ("500", 500), ("abc", 360), (None, 360), (True, 360),
])
def test_height_is_clamped(core_js, value, expected):
    block = {"height": value}
    for html in (_render_gradient_mesh_live(block),
                 _render_via_gas(core_js, dict(block, type="gradient_mesh_live"))):
        assert f"height:{expected}px" in html


def test_copy_is_html_escaped(core_js):
    block = {"title": '<img src=x onerror="alert(1)">', "eyebrow": "<b>x</b>",
             "body": "<script>alert(2)</script>"}
    for html in (_render_gradient_mesh_live(block),
                 _render_via_gas(core_js, dict(block, type="gradient_mesh_live"))):
        assert "onerror" not in html.replace("&quot;", "") or "<img" not in html
        assert "<img" not in html and "<b>" not in html
        assert html.count("<script>") == 1  # only the atom's own
        assert "alert(2)" not in html.split("<script>")[1].split("</script>")[0] or \
               "&lt;script&gt;" in html


def test_reduced_motion_and_offscreen_handling_are_present():
    html = _render_gradient_mesh_live({})
    assert "prefers-reduced-motion" in html
    assert "IntersectionObserver" in html
    assert "devicePixelRatio" in html


def test_gas_output_terminates_its_script_safely(core_js):
    html = _render_via_gas(core_js, {"type": "gradient_mesh_live"})
    assert html.count("<script>") == 1 and html.count("</script>") == 1
    assert html.endswith("</script></div>")


def test_uid_is_content_derived_on_the_python_side():
    a = _render_gradient_mesh_live({"title": "one"})
    b = _render_gradient_mesh_live({"title": "one"})
    c = _render_gradient_mesh_live({"title": "two"})
    assert a == b
    assert UID_RE.search(a).group(0) != UID_RE.search(c).group(0)
