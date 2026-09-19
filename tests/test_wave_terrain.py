"""wave_terrain (2026-09-19) — a canvas hero background whose whole config
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

from renderers.web_article import _render_wave_terrain  # noqa: E402

UID_RE = re.compile(r"wt-[a-z0-9]{6}")


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
    return UID_RE.sub("wt-UID", html)


def _cfg(html: str) -> str:
    m = re.search(r"var C=(\{.*?\});", html)
    assert m, "config object not found in script"
    return m.group(1)


FULL = {
    "eyebrow": "Terrain", "title": "A landscape that never repeats",
    "body": "Ridgelines scroll on the same **noise field** as flow_field.",
    "align": "left", "colors": ["#38BDF8", "#818cf8", "#f472b6"],
    "background": "#070a12", "density": "high", "relief": "high", "scale": "fine",
    "speed": "fast", "height": 420, "interactive": False,
}


@pytest.mark.parametrize("block", [
    {},
    FULL,
    {"title": "Centered", "align": "center", "relief": "low"},
    {"title": "Right", "align": "right", "colors": ["#ffffff"]},
])
def test_python_renderer_matches_gas_renderer_exactly(core_js, block):
    gas_html = _render_via_gas(core_js, dict(block, type="wave_terrain"))
    py_html = _render_wave_terrain(dict(block))
    assert _norm(gas_html) == _norm(py_html)


def test_script_runs_under_node_syntax_check():
    html = _render_wave_terrain(FULL)
    script = re.search(r"<script>(.*)</script>", html, re.S).group(1)
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "s.js"
        f.write_text(script)
        proc = subprocess.run(["node", "--check", str(f)], capture_output=True, text=True)
        assert proc.returncode == 0, proc.stderr


def test_every_field_is_baked_as_declared():
    cfg = _cfg(_render_wave_terrain(FULL))
    assert cfg == ('{n:48,spd:1.8,amp:0.46,fx:5,'
                   'pal:["56,189,248","129,140,248","244,114,182"],'
                   'bg:"#070a12",inter:false}')


def test_defaults_when_nothing_is_set():
    html = _render_wave_terrain({})
    assert _cfg(html) == ('{n:34,spd:1,amp:0.3,fx:3.2,'
                          'pal:["56,189,248","129,140,248","244,114,182"],'
                          'bg:"#070a12",inter:true}')
    assert "height:380px" in html
    # no copy -> no veil, no overlay
    assert "linear-gradient" not in html and "radial-gradient" not in html


@pytest.mark.parametrize("bad", [
    '#fff");alert(1);//', "red", "#12345", "#1234567", "rgb(1,2,3)", 42, None, ["#000000"],
])
def test_free_form_colour_never_reaches_the_script(core_js, bad):
    block = {"colors": [bad], "background": bad}
    for html in (_render_wave_terrain(block),
                 _render_via_gas(core_js, dict(block, type="wave_terrain"))):
        assert "alert(" not in html
        assert 'bg:"#070a12"' in _cfg(html)
        assert '"56,189,248"' in _cfg(html)


def test_invalid_colours_are_dropped_not_fatal():
    cfg = _cfg(_render_wave_terrain({"colors": ["nope", "#00ff00", "#zzzzzz", "#ff0000"]}))
    assert 'pal:["0,255,0","255,0,0"]' in cfg


def test_palette_capped_at_four():
    cfg = _cfg(_render_wave_terrain({"colors": ["#010101"] * 9}))
    assert cfg.count("1,1,1") == 4


@pytest.mark.parametrize("value,expected", [
    ("huge", "34"), (None, "34"), (12, "34"), (["low"], "34"), ("low", "22"), ("high", "48"),
])
def test_enum_fields_fall_back_to_default(core_js, value, expected):
    block = {"density": value}
    for html in (_render_wave_terrain(block),
                 _render_via_gas(core_js, dict(block, type="wave_terrain"))):
        assert f"{{n:{expected}," in _cfg(html)


@pytest.mark.parametrize("value,expected", [
    ("sideways", "0.3"), (None, "0.3"), (7, "0.3"), (["high"], "0.3"), ("high", "0.46"), ("low", "0.18"),
])
def test_relief_falls_back_to_default(core_js, value, expected):
    block = {"relief": value}
    for html in (_render_wave_terrain(block),
                 _render_via_gas(core_js, dict(block, type="wave_terrain"))):
        assert f"amp:{expected}," in _cfg(html)


@pytest.mark.parametrize("value,expected", [
    ("huge", "3.2"), (None, "3.2"), (7, "3.2"), (["fine"], "3.2"), ("fine", "5"), ("broad", "2"),
])
def test_scale_falls_back_to_default(core_js, value, expected):
    block = {"scale": value}
    for html in (_render_wave_terrain(block),
                 _render_via_gas(core_js, dict(block, type="wave_terrain"))):
        assert f",fx:{expected}," in _cfg(html)


@pytest.mark.parametrize("value,expected", [
    (99999, 900), (-5, 200), (300, 300), ("500", 500), ("abc", 380), (None, 380), (True, 380),
])
def test_height_is_clamped(core_js, value, expected):
    block = {"height": value}
    for html in (_render_wave_terrain(block),
                 _render_via_gas(core_js, dict(block, type="wave_terrain"))):
        assert f"height:{expected}px" in html


def test_copy_is_html_escaped(core_js):
    block = {"title": '<img src=x onerror="alert(1)">', "eyebrow": "<b>x</b>",
             "body": "<script>alert(2)</script>"}
    for html in (_render_wave_terrain(block),
                 _render_via_gas(core_js, dict(block, type="wave_terrain"))):
        assert "onerror" not in html.replace("&quot;", "") or "<img" not in html
        assert "<img" not in html and "<b>" not in html
        assert html.count("<script>") == 1  # only the atom's own
        assert "alert(2)" not in html.split("<script>")[1].split("</script>")[0] or \
               "&lt;script&gt;" in html


def test_reduced_motion_and_offscreen_handling_are_present():
    html = _render_wave_terrain({})
    assert "prefers-reduced-motion" in html
    assert "IntersectionObserver" in html
    assert "devicePixelRatio" in html


def test_gas_output_terminates_its_script_safely(core_js):
    html = _render_via_gas(core_js, {"type": "wave_terrain"})
    assert html.count("<script>") == 1 and html.count("</script>") == 1
    assert html.endswith("</script></div>")


def test_uid_is_content_derived_on_the_python_side():
    a = _render_wave_terrain({"title": "one"})
    b = _render_wave_terrain({"title": "one"})
    c = _render_wave_terrain({"title": "two"})
    assert a == b
    assert UID_RE.search(a).group(0) != UID_RE.search(c).group(0)
