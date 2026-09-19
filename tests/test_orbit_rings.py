"""orbit_rings (2026-09-19) — a canvas hero whose whole config, INCLUDING the
agent-supplied tier and item labels, is baked into inline JavaScript. Sibling
of flow_field on the same shared kit (_A2UI_CANVAS_KIT_JS). Worth proving on
every run, against BOTH real renderers (GAS via the same Node-eval harness
tests/test_agent_sketchpad.py uses; Python via renderers/web_article.py):

1. Parity: the two renderers emit identical markup modulo the uid, including
   for hostile / malformed ring structures and non-ASCII labels.
2. No free-form value reaches the script unescaped: colours must be #rrggbb,
   every other option is an enum or a clamped int, labels are trimmed,
   length-capped and JSON-encoded with "<" escaped, and copy is HTML-escaped.
3. The client maths runs: the emitted script is executed headless against a
   stub canvas for a few hundred frames and must draw every label with finite
   coordinates.
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

from renderers.web_article import _render_orbit_rings  # noqa: E402

UID_RE = re.compile(r"rg-[a-z0-9]{6}")

DEFAULT_CFG = (
    '{c:"agent",rings:[{"l":"tools","i":["search","code","browser"]},'
    '{"l":"data","i":["docs","sheets","crm","mail"]},'
    '{"l":"surfaces","i":["web","chat","slides","email","pdf"]}],spd:1,'
    'pal:["56,189,248","129,140,248","244,114,182"],bg:"#070a12",pos:"right",inter:true}'
)


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
    return UID_RE.sub("rg-UID", html)


def _cfg(html: str) -> str:
    m = re.search(r"var C=(\{.*?\});var cx=", html)
    assert m, "config object not found in script"
    return m.group(1)


def _both(core_js, block):
    return (_render_orbit_rings(dict(block)),
            _render_via_gas(core_js, dict(block, type="orbit_rings")))


FULL = {
    "center": "Platform",
    "rings": [{"label": "Tools", "items": ["search", "code"]},
              {"label": "Data", "items": ["docs", "crm", "mail"]}],
    "eyebrow": "System map", "title": "Everything an agent touches",
    "body": "Three tiers, **one** centre.",
    "align": "left", "position": "left", "colors": ["#38BDF8", "#818cf8", "#f472b6"],
    "background": "#070a12", "speed": "fast", "height": 460, "interactive": False,
}

HOSTILE_RINGS = [
    "not a ring", None, 7, [], {"label": "no items"}, {"label": "empty", "items": []},
    {"label": "  spaced  ", "items": ["  a  ", "", "   ", 3, None, {"x": 1}, "b"]},
    {"label": "x" * 40, "items": ["y" * 40, "z", "1", "2", "3", "4", "5", "6"]},
    {"label": "Café ✓", "items": ["日本語", "naïve"]},
    {"label": "dropped: fourth valid ring", "items": ["q"]},
]


@pytest.mark.parametrize("block", [
    {},
    FULL,
    {"title": "Centered", "align": "center", "position": "center"},
    {"title": "Right", "align": "right", "position": "left", "colors": ["#ffffff"]},
    {"rings": HOSTILE_RINGS, "center": "  Middle  "},
    {"rings": "nope", "center": 12},
    {"rings": [{"label": "solo", "items": ["only"]}]},
])
def test_python_renderer_matches_gas_renderer_exactly(core_js, block):
    py_html, gas_html = _both(core_js, block)
    assert _norm(gas_html) == _norm(py_html)


def test_script_runs_under_node_syntax_check():
    html = _render_orbit_rings(FULL)
    script = re.search(r"<script>(.*)</script>", html, re.S).group(1)
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "s.js"
        f.write_text(script)
        proc = subprocess.run(["node", "--check", str(f)], capture_output=True, text=True)
        assert proc.returncode == 0, proc.stderr


def test_every_field_is_baked_as_declared():
    assert _cfg(_render_orbit_rings(FULL)) == (
        '{c:"Platform",rings:[{"l":"Tools","i":["search","code"]},'
        '{"l":"Data","i":["docs","crm","mail"]}],spd:1.8,'
        'pal:["56,189,248","129,140,248","244,114,182"],bg:"#070a12",pos:"left",inter:false}')


def test_defaults_when_nothing_is_set():
    html = _render_orbit_rings({})
    assert _cfg(html) == DEFAULT_CFG
    assert "height:420px" in html
    assert "linear-gradient" not in html and "radial-gradient" not in html


def test_rings_are_sanitised():
    cfg = json.loads(re.search(r"rings:(\[.*?\}\]),spd:", _cfg(_render_orbit_rings({"rings": HOSTILE_RINGS}))).group(1))
    assert len(cfg) == 3                                   # capped at three valid rings
    assert cfg[0] == {"l": "spaced", "i": ["a", "b"]}      # trimmed, junk items dropped
    assert cfg[1]["l"] == "x" * 24 and cfg[1]["i"][0] == "y" * 24
    assert len(cfg[1]["i"]) == 6                           # capped at six items
    assert cfg[2] == {"l": "Café ✓", "i": ["日本語", "naïve"]}


def test_ring_label_is_optional_and_invalid_rings_fall_back_to_defaults():
    only = json.loads(re.search(r"rings:(\[.*?\}\]),spd:", _cfg(_render_orbit_rings({"rings": [{"items": ["a"]}]}))).group(1))
    assert only == [{"l": "", "i": ["a"]}]
    for junk in ("nope", 5, None, [], [None, "x", {"items": []}], {"label": "not a list"}):
        assert _cfg(_render_orbit_rings({"rings": junk})) == DEFAULT_CFG


@pytest.mark.parametrize("value,expected", [
    ("  Middle  ", '"Middle"'), ("", '"agent"'), ("   ", '"agent"'), (None, '"agent"'),
    (12, '"agent"'), (["x"], '"agent"'), ("m" * 40, '"' + "m" * 24 + '"'),
])
def test_center_label(core_js, value, expected):
    for html in _both(core_js, {"center": value}):
        assert _cfg(html).startswith("{c:" + expected + ",rings:")


@pytest.mark.parametrize("label", [
    "</script><script>alert(1)</script>", "<img src=x onerror=alert(1)>", '"};alert(1);//',
    "\\u003c", "$&", "a$'b", "line\nbreak", "<!--",
])
def test_labels_can_never_break_out_of_the_script(core_js, label):
    block = {"center": label, "rings": [{"label": label, "items": [label]}]}
    for html in _both(core_js, block):
        assert html.count("<script>") == 1 and html.count("</script>") == 1
        assert html.endswith("</script></div>")
        assert "<img" not in html and "<!--" not in html
        script = html.split("<script>")[1].split("</script>")[0]
        assert "<" not in script.split("var cx=")[0].split("var C=")[1]   # no raw "<" inside the config
    py_html, gas_html = _both(core_js, block)
    assert _norm(py_html) == _norm(gas_html)


def test_dollar_sequences_survive_the_gas_replacer(core_js):
    for html in _both(core_js, {"center": "$&$'", "rings": [{"label": "$`", "items": ["$$"]}]}):
        assert 'c:"$&$\'"' in html and '"l":"$`"' in html and '"i":["$$"]' in html


@pytest.mark.parametrize("bad", [
    '#fff");alert(1);//', "red", "#12345", "#1234567", "rgb(1,2,3)", 42, None, ["#000000"],
])
def test_free_form_colour_never_reaches_the_script(core_js, bad):
    for html in _both(core_js, {"colors": [bad], "background": bad}):
        assert "alert(" not in html
        assert 'bg:"#070a12"' in _cfg(html)
        assert '"56,189,248"' in _cfg(html)


def test_invalid_colours_are_dropped_and_palette_capped():
    assert 'pal:["0,255,0","255,0,0"]' in _cfg(_render_orbit_rings({"colors": ["nope", "#00ff00", "#zzzzzz", "#ff0000"]}))
    assert _cfg(_render_orbit_rings({"colors": ["#010101"] * 9})).count("1,1,1") == 4


@pytest.mark.parametrize("value,expected", [
    ("sideways", "right"), (None, "right"), (7, "right"), (["left"], "right"), ("left", "left"), ("center", "center"),
])
def test_position_falls_back_to_default(core_js, value, expected):
    for html in _both(core_js, {"position": value}):
        assert f'pos:"{expected}"' in _cfg(html)


@pytest.mark.parametrize("value,expected", [
    ("warp", "1"), (None, "1"), (3, "1"), (["fast"], "1"), ("slow", "0.5"), ("fast", "1.8"),
])
def test_speed_falls_back_to_default(core_js, value, expected):
    for html in _both(core_js, {"speed": value}):
        assert f",spd:{expected}," in _cfg(html)


@pytest.mark.parametrize("value,expected", [
    (99999, 900), (-5, 240), (300, 300), ("500", 500), ("abc", 420), (None, 420), (True, 420),
])
def test_height_is_clamped(core_js, value, expected):
    for html in _both(core_js, {"height": value}):
        assert f"height:{expected}px" in html


def test_copy_is_html_escaped(core_js):
    block = {"title": '<img src=x onerror="alert(1)">', "eyebrow": "<b>x</b>",
             "body": "<script>alert(2)</script>"}
    for html in _both(core_js, block):
        assert "<img" not in html and "<b>" not in html
        assert html.count("<script>") == 1  # only the atom's own


def test_reduced_motion_and_offscreen_handling_are_present():
    html = _render_orbit_rings({})
    assert "prefers-reduced-motion" in html
    assert "IntersectionObserver" in html
    assert "devicePixelRatio" in html


def test_uid_is_content_derived_on_the_python_side():
    a = _render_orbit_rings({"title": "one"})
    b = _render_orbit_rings({"title": "one"})
    c = _render_orbit_rings({"title": "two"})
    assert a == b
    assert UID_RE.search(a).group(0) != UID_RE.search(c).group(0)


DRIVER = r"""
var src = require("fs").readFileSync(process.argv[2], "utf8");
var bad = 0, texts = {}, handlers = {};
function chk() { for (var i = 0; i < arguments.length; i++) if (!isFinite(arguments[i])) bad++; }
var ctx = new Proxy({}, {
  get: function (t, p) {
    if (p in t) return t[p];
    if (p === "moveTo" || p === "lineTo") return function (x, y) { chk(x, y); };
    if (p === "arc") return function (x, y, r) { chk(x, y, r); };
    if (p === "ellipse") return function (x, y, rx, ry, rot) { chk(x, y, rx, ry, rot); };
    if (p === "fillText") return function (s, x, y) { chk(x, y); texts[s] = 1; };
    if (p === "createLinearGradient" || p === "createRadialGradient")
      return function () { chk.apply(null, arguments); return { addColorStop: function () {} }; };
    return function () {};
  },
  set: function (t, p, v) { t[p] = v; return true; }
});
var canvas = { getContext: function () { return ctx; }, clientWidth: %W%, clientHeight: %H%, width: 0, height: 0,
  parentNode: { addEventListener: function (n, f) { handlers[n] = f; } },
  getBoundingClientRect: function () { return { left: 0, top: 0 }; } };
global.window = global;
global.document = { getElementById: function () { return canvas; } };
global.matchMedia = undefined; global.IntersectionObserver = undefined; global.devicePixelRatio = 1;
global.addEventListener = function () {};
global.requestAnimationFrame = function (f) { global.__f = f; return 1; };
eval(src);
for (var i = 0; i < 300; i++) {
  if (i === 80 && handlers.pointermove) handlers.pointermove({ clientX: 40, clientY: 10 });
  if (i === 200 && handlers.pointerleave) handlers.pointerleave();
  var f = global.__f; global.__f = null; if (f) f();
}
console.log(JSON.stringify({ bad: bad, texts: Object.keys(texts) }));
"""


@pytest.mark.parametrize("block,w,h,expect", [
    ({}, 880, 420, {"agent", "search", "TOOLS", "DATA", "SURFACES", "pdf"}),
    ({"rings": [{"label": "solo", "items": ["only"]}], "center": "Hub"}, 400, 240, {"Hub", "only", "SOLO"}),
    ({"position": "center", "rings": HOSTILE_RINGS}, 1200, 900, {"agent", "a", "b", "SPACED", "日本語"}),
])
def test_script_draws_every_label_with_finite_coordinates(block, w, h, expect):
    html = _render_orbit_rings(block)
    script = re.search(r"<script>(.*)</script>", html, re.S).group(1)
    with tempfile.TemporaryDirectory() as td:
        js = Path(td) / "s.js"
        js.write_text(script)
        drv = Path(td) / "d.js"
        drv.write_text(DRIVER.replace("%W%", str(w)).replace("%H%", str(h)))
        proc = subprocess.run(["node", str(drv), str(js)], capture_output=True, text=True, timeout=60)
        assert proc.returncode == 0, proc.stderr[-1500:]
    out = json.loads(proc.stdout)
    assert out["bad"] == 0
    assert expect <= set(out["texts"])
