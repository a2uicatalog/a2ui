"""The agentic-typeface family + orbit_mark (2026-09-18): particle_type,
light_type, living_type take WORDS from an agent and set them on canvas;
orbit_mark draws the catalogue's own logo inside a flow field. All four sit
on the canvas hero kit flow_field introduced (see tests/test_flow_field.py).

Two things matter and are proven against BOTH real renderers (GAS via the
Node-eval harness test_agent_sketchpad.py uses; Python via web_article.py):

1. Parity: identical markup modulo uid, for ordinary, unicode and hostile text.
2. Agent-supplied text is data, never code: it is JSON-encoded into the
   inline script with "<" escaped, so "</script>" inside a headline cannot
   end the script element, and "$&" cannot expand through JS String.replace
   (the GAS side inserts the config with a function replacer for exactly
   this reason). Lines are capped at 3 x 40 chars on both sides.
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
    _render_particle_type, _render_light_type, _render_living_type, _render_orbit_mark,
)

PY = {"particle_type": _render_particle_type, "light_type": _render_light_type,
      "living_type": _render_living_type, "orbit_mark": _render_orbit_mark}
TYPE_ATOMS = ["particle_type", "light_type", "living_type"]
UID_RE = re.compile(r"\b(pt|lt|lv|om)-[a-z0-9]{6}\b")


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
    m = re.search(r"var C=(\{.*?\});\s*var ", html)
    assert m, "config object not found"
    return m.group(1)


def _script(html: str) -> str:
    return re.search(r"<script>(.*)</script>", html, re.S).group(1)


PAYLOADS = [
    {},
    {"text": "Agent messages\nbecome interface", "font": "serif", "weight": "bold",
     "colors": ["#FBBF24", "#f97316"], "background": "#0b0704", "height": 400, "interactive": False},
    {"text": "Ünïcödé — 日本語 🚀", "font": "display"},
    {"text": '</script><img src=x onerror=alert(1)>\n$& $1 %%UID%% %%CFG%%\nHe said "hi" \\ ok'},
    {"text": "one\ntwo\nthree\nfour\nfive", "font": "mono", "density": "high", "speed": "fast",
     "trail": "long", "scale": "fine", "motion": "wild", "dot": "bold", "glow": False},
]


@pytest.mark.parametrize("atom", TYPE_ATOMS)
@pytest.mark.parametrize("block", PAYLOADS)
def test_python_matches_gas_exactly(core_js, atom, block):
    gas_html = _gas(core_js, dict(block, type=atom))
    py_html = PY[atom](dict(block))
    assert _norm(gas_html) == _norm(py_html)


@pytest.mark.parametrize("block", [
    {}, {"title": "Orbit", "eyebrow": "the mark", "body": "streams **captured** into orbit",
         "align": "left", "mark_position": "right", "size": "large", "electron": False,
         "colors": ["#ffffff"], "density": "high"},
])
def test_orbit_mark_python_matches_gas_exactly(core_js, block):
    assert _norm(_gas(core_js, dict(block, type="orbit_mark"))) == _norm(_render_orbit_mark(dict(block)))


@pytest.mark.parametrize("atom", list(PY))
def test_scripts_pass_node_syntax_check(atom):
    html = PY[atom](PAYLOADS[3])
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "s.js"
        f.write_text(_script(html))
        proc = subprocess.run(["node", "--check", str(f)], capture_output=True, text=True)
        assert proc.returncode == 0, proc.stderr


@pytest.mark.parametrize("atom", TYPE_ATOMS)
def test_hostile_text_never_leaves_the_string(core_js, atom):
    block = dict(PAYLOADS[3], type=atom)
    for html in (PY[atom](block), _gas(core_js, block)):
        # exactly one script element, and it is the atom's own
        assert html.count("<script>") == 1 and html.count("</script>") == 1
        assert html.endswith("</script></div>")
        assert "\\u003c/script>" in html and "<img" not in html and "&lt;img" in html
        # $& did not expand into the surrounding markup, %% tokens were not re-substituted
        assert '$& $1 %%UID%% %%CFG%%' in _cfg(html)
        # the visually-hidden copy is escaped
        assert "&lt;/script&gt;" in html.split("<script>")[0]


def test_lines_are_capped_at_three_by_forty(core_js):
    long = "x" * 60
    block = {"type": "living_type", "text": f"  a  \n\n{long}\nb\nc\nd\ne"}
    for html in (_render_living_type(block), _gas(core_js, block)):
        assert f'lines:["a","{"x" * 40}","b"]' in _cfg(html)


def test_missing_text_falls_back_to_the_catalog_name(core_js):
    for atom in TYPE_ATOMS:
        for html in (PY[atom]({}), _gas(core_js, {"type": atom})):
            assert 'lines:["A2UI"]' in _cfg(html)


@pytest.mark.parametrize("bad", [None, 42, "comic", ["sans"], {"font": "sans"}])
def test_font_and_weight_enums_fall_back(core_js, bad):
    block = {"type": "particle_type", "font": bad, "weight": bad}
    for html in (_render_particle_type(block), _gas(core_js, block)):
        cfg = _cfg(html)
        assert 'font:"system-ui,-apple-system,Segoe UI,Helvetica Neue,Arial,sans-serif"' in cfg
        assert 'weight:"900"' in cfg


def test_every_type_field_is_baked_as_declared():
    cfg = _cfg(_render_light_type(PAYLOADS[4]))
    assert cfg == ('{lines:["one","two","three"],font:"ui-monospace,SFMono-Regular,Menlo,Consolas,monospace",'
                   'weight:"900",pal:["56,189,248","129,140,248","244,114,182"],bg:"#070a12",bgRgb:"7,10,18",'
                   'cap:3000,per:70,spd:1.5,trail:0.035,sc:0.012,glow:false,inter:true}')
    cfg = _cfg(_render_particle_type(PAYLOADS[4]))
    assert cfg.endswith(',cap:4200,dot:2.1,inter:true}')
    cfg = _cfg(_render_living_type(PAYLOADS[4]))
    assert cfg.endswith(',amp:32,spd:1.8,inter:true}')
    cfg = _cfg(_render_orbit_mark({"size": "small", "mark_position": "left", "electron": False}))
    assert cfg == ('{n:500,spd:1,trail:0.07,sc:0.0034,pal:["99,102,241","168,85,247","34,211,238"],'
                   'bg:"#070a12",bgRgb:"7,10,18",pos:"left",size:0.5,el:false,inter:true}')


@pytest.mark.parametrize("atom", list(PY))
def test_kit_manners_are_present(atom):
    html = PY[atom]({})
    for needle in ("prefers-reduced-motion", "IntersectionObserver", "devicePixelRatio", "window._a2uiCK=window._a2uiCK||"):
        assert needle in html


def test_orbit_mark_copy_is_escaped_and_veiled(core_js):
    block = {"type": "orbit_mark", "title": "<b>x</b>", "align": "center"}
    for html in (_render_orbit_mark(block), _gas(core_js, block)):
        assert "<b>" not in html and "&lt;b&gt;" in html
        assert "radial-gradient" in html
