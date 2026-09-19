"""sun_path, great_circle, bezier_easing, tonal_scale (2026-09-19): the
maths lives in the atom's own script, so the server bakes only validated
inputs. Proven three ways: GAS/Python parity modulo uid; number spelling
through _ff_num; and the client maths itself, by running each script under
Node against a stub canvas that records what gets drawn (a great-circle
LHR-JFK must come out near 5,555 km on an initial bearing near 288, the
Paris sun on 2026-09-19 must rise a little after 07:30 and set near 20:00)."""
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
    _render_sun_path, _render_great_circle, _render_bezier_easing, _render_tonal_scale, _ff_num,
)

PY = {"sun_path": _render_sun_path, "great_circle": _render_great_circle,
      "bezier_easing": _render_bezier_easing, "tonal_scale": _render_tonal_scale}
UID_RE = re.compile(r"\b(sun|gc|bz|bzc|bzb|bzl|tn|tnc)-[a-z0-9]{6}\b")

STUB = r"""
var __texts = [], __els = {};
function ctx() { var noop = function(){}; var c = {fillText: function(t){ __texts.push(String(t)); }, createLinearGradient: function(){ return {addColorStop: noop}; },
  createRadialGradient: function(){ return {addColorStop: noop}; }, setTransform: noop, fillRect: noop, clearRect: noop, beginPath: noop, moveTo: noop, lineTo: noop,
  arc: noop, arcTo: noop, stroke: noop, fill: noop, save: noop, restore: noop, clip: noop, rect: noop, setLineDash: noop, quadraticCurveTo: noop, translate: noop, rotate: noop,
  scale: noop, strokeRect: noop, closePath: noop, measureText: function(){ return {width: 10}; }, drawImage: noop, getImageData: function(w,h){ return {data: new Uint8Array(4)}; }};
  return c; }
function el(id) { if (!__els[id]) __els[id] = {id: id, style: {}, children: [], clientWidth: 800, clientHeight: 300, width: 0, height: 0, innerHTML: '', textContent: '',
  getContext: function(){ return ctx(); }, addEventListener: function(){}, appendChild: function(c){ this.children.push(c); }, querySelector: function(){ return el(id + ':c'); },
  parentNode: {addEventListener: function(){}}, getBoundingClientRect: function(){ return {left:0, top:0, width:800, height:300}; }}; return __els[id]; }
global.window = global; global.document = {getElementById: el, createElement: function(t){ return el('new' + Math.random()); }};
var __rafN = 0; global.requestAnimationFrame = function(cb){ if (__rafN++ < 1) cb(); return 1; }; global.setInterval = function(){}; global.setTimeout = function(){};
global.matchMedia = function(){ return {matches: false}; }; global.Date.now = function(){ return 0; }; global.addEventListener = function(){};
"""


def _run_script(html: str) -> dict:
    script = re.search(r"<script>(.*)</script>", html, re.S).group(1)
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "s.js"
        f.write_text(STUB + script + "\nconsole.log(JSON.stringify({texts: __texts, els: Object.keys(__els).map(function(k){var e=__els[k];return {id:k,n:e.children.length,tc:e.textContent};})}));")
        proc = subprocess.run(["node", str(f)], capture_output=True, text=True, timeout=30)
        assert proc.returncode == 0, proc.stderr[-1500:]
        return json.loads(proc.stdout.strip().splitlines()[-1])


@pytest.fixture(scope="module")
def core_js():
    bundle = gen.build_bundle()
    blocks = re.findall(r"<script>\n(.*?)\n</script>", bundle, re.S)
    return [b for b in blocks if "a2ui-core" in b[:300]][0]


def _gas(core_js, block: dict) -> str:
    with tempfile.TemporaryDirectory() as td:
        driver = Path(td) / "d.js"
        driver.write_text("global.window = global;\n" + core_js + f"""
var blocks = [{json.dumps(block)}];
console.log(JSON.stringify({{html: renderAtoms(blocks, {{}})}}));
""")
        proc = subprocess.run(["node", str(driver)], capture_output=True, text=True, timeout=30)
        assert proc.returncode == 0, proc.stderr[-1000:]
        return json.loads(proc.stdout)["html"]


PAYLOADS = {
    "sun_path": [{}, {"lat": 48.8566, "lon": 2.3522, "date": "2026-09-19", "tz": 2, "label": "Paris, it's <late>", "theme": "light", "accent": "#F97316", "height": 400, "live": False},
                 {"lat": "91", "lon": -200, "date": "19/09/2026", "tz": "local", "label": ""}, {"lat": 78.22, "lon": 15.63, "date": "2026-12-21", "tz": 1, "label": "Longyearbyen"}],
    "great_circle": [{}, {"from": {"lat": 35.5533, "lon": 139.7811, "label": "HND"}, "to": {"lat": -33.9399, "lon": 151.1753, "label": "SYD"}, "units": "km", "theme": "light"},
                     {"from": "junk", "to": {"lat": "x"}, "units": "furlongs"}],
    "bezier_easing": [{}, {"preset": "overshoot", "duration": 2000, "label": "spring's cousin", "editable": False, "theme": "light"},
                      {"x1": 1.7, "y1": -9, "x2": "0.5", "y2": 0.33333, "duration": 5}, {"preset": "nope", "x1": 0.1}],
    "tonal_scale": [{}, {"accent": "#B91C1C", "steps": 7, "name": "danger", "show_contrast": False, "theme": "light"}, {"accent": "red", "steps": 99, "name": "Bad Name!", "show_code": False}],
}


@pytest.mark.parametrize("atom,block", [(a, b) for a, bs in PAYLOADS.items() for b in bs])
def test_python_matches_gas_exactly(core_js, atom, block):
    assert UID_RE.sub(r"\1-UID", _gas(core_js, dict(block, type=atom))) == UID_RE.sub(r"\1-UID", PY[atom](dict(block)))


@pytest.mark.parametrize("v,expected", [(48.8566, "48.8566"), (-0.4614, "-0.4614"), (2, "2"), ("abc", "0"), (None, "0"), (True, "0"),
                                        (999, "90"), (-999, "-90"), (1e-7, "0"), (-0.00001, "0"), ("  -12.5 ", "-12.5"), (0.33333, "0.3333")])
def test_ff_num_spells_numbers_the_same_as_js(v, expected):
    assert _ff_num(v, 0, -90, 90, 4) == expected


def test_configs_bake_validated_inputs():
    html = _render_sun_path(PAYLOADS["sun_path"][2])
    assert 'lat:90,lon:-180,date:"",tz:null,label:"Sun"' in html
    html = _render_great_circle(PAYLOADS["great_circle"][2])
    assert 'a:[51.47,-0.4614],b:[40.6413,-73.7781],al:"A",bl:"B",units:"nm"' in html
    html = _render_bezier_easing(PAYLOADS["bezier_easing"][2])
    assert "x1:1,y1:-1,x2:0.5,y2:0.333,dur:200" in html and "cubic-bezier(1, -1, 0.5, 0.333)" in html
    assert "x1:0.34,y1:1.56,x2:0.64,y2:1,dur:2000,edit:false" in _render_bezier_easing(PAYLOADS["bezier_easing"][1])
    html = _render_tonal_scale(PAYLOADS["tonal_scale"][2])
    assert 'hex:"#0e7bb8",steps:13,name:"accent"' in html and "<pre" not in html


def test_great_circle_maths_lhr_to_jfk():
    out = _run_script(_render_great_circle({}))
    texts = " | ".join(out["texts"])
    km = int(re.search(r"([\d,]+) km", texts).group(1).replace(",", ""))
    assert 5530 <= km <= 5580
    nm = int(re.search(r"^([\d,]+) nm", texts.split(" | ")[0] if texts.startswith(("1","2","3","4","5","6","7","8","9")) else [t for t in out["texts"] if t.endswith(" nm")][0]).group(1).replace(",", ""))
    assert 2985 <= nm <= 3015
    brg = int(re.search(r"initial bearing (\d+)", texts).group(1))
    assert 284 <= brg <= 292


def test_sun_path_maths_paris_on_the_equinox_week():
    out = _run_script(_render_sun_path({"lat": 48.8566, "lon": 2.3522, "date": "2026-09-19", "tz": 2, "live": False}))
    texts = " | ".join(out["texts"])
    assert re.search(r"rise 07:[2-4]\d", texts), texts
    assert re.search(r"set (19:5\d|20:0\d)", texts), texts
    assert re.search(r"12:[1-3]\d of daylight", texts), texts
    polar = " | ".join(_run_script(_render_sun_path({"lat": 78.22, "lon": 15.63, "date": "2026-12-21", "tz": 1, "live": False}))["texts"])
    assert "polar night" in polar


def test_tonal_scale_builds_the_swatches_and_tokens():
    out = _run_script(_render_tonal_scale({"accent": "#0e7bb8", "steps": 11, "name": "accent"}))
    host = [e for e in out["els"] if e["id"].startswith("tn-")][0]
    code = [e for e in out["els"] if e["id"].startswith("tnc-")][0]
    assert host["n"] == 11
    assert code["tc"].count("--accent-") == 11 and "--accent-50:" in code["tc"] and "--accent-900:" in code["tc"]


@pytest.mark.parametrize("atom", list(PY))
def test_scripts_pass_node_syntax_check(atom):
    html = PY[atom](PAYLOADS[atom][1])
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "s.js"
        f.write_text(re.search(r"<script>(.*)</script>", html, re.S).group(1))
        assert subprocess.run(["node", "--check", str(f)], capture_output=True, text=True).returncode == 0
