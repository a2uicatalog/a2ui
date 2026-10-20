"""I22: the Apps Script globe_3d renderers (gas-schema-renderer, gas-wired-renderer) must draw
schema-conformant arcs ({from, to}) and honour per-pin `color`, as the Python twin does (I11).

Level of check: the real GAS renderer is executed in node (bundle via gen_mcp_apps_bundle, the
way test_motion_atoms does), its emitted <script> is then executed against a recording canvas
stub. It is not a browser; it proves what is drawn (strokes/fills), not pixels.
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_motion_atoms import core_js  # noqa: F401,E402  (fixture)

ROOT = Path(__file__).resolve().parent.parent
GAS_DIRS = ["gas-schema-renderer", "gas-wired-renderer"]

HARNESS = r"""
var out = {html: renderAtoms([BLOCK], {})};
var m = out.html.match(/<script>([\s\S]*?)<\/script>/);
var rec = {fills: [], strokes: [], arcDraws: 0, error: null};
var ctx = {};
['scale','beginPath','moveTo','lineTo','arc','fill','stroke','clearRect','fillText','setLineDash','save','restore','translate','rotate','closePath','clip','fillRect','strokeRect'].forEach(function(k){ctx[k]=function(){};});
var fs = '', ss = '';
Object.defineProperty(ctx, 'fillStyle', {get:function(){return fs;}, set:function(v){fs=v;}});
Object.defineProperty(ctx, 'strokeStyle', {get:function(){return ss;}, set:function(v){ss=v;}});
ctx.createRadialGradient = ctx.createLinearGradient = function(){return {addColorStop:function(){}};};
var nLine = 0;
ctx.moveTo = function(){};
ctx.fill = function(){ rec.fills.push(String(fs)); };
ctx.stroke = function(){ rec.strokes.push(String(ss)); };
var canvas = {width: 480, height: 480, style: {}, getContext: function(){return ctx;}, addEventListener: function(){}};
global.document = {getElementById: function(){return canvas;}, addEventListener: function(){}};
global.requestAnimationFrame = function(){};
global.window = global;
try { (new Function(m[1]))(); } catch (e) { rec.error = String(e); }
console.log(JSON.stringify(rec));
"""


def _run(core, block, gas_dir):
    """gas-wired-renderer: through the real bundle (renderAtoms). gas-schema-renderer: the file is
    self-contained, so it is loaded alone against a bare _RENDERERS (the bundle only builds from
    the wired directory)."""
    if gas_dir == "gas-wired-renderer":
        pre = "global.window = global;\n" + core + "\n"
        body = HARNESS.replace("BLOCK", json.dumps(block))
    else:
        src = (ROOT / "apps-script-surface" / gas_dir / "atoms_globe.gs").read_text()
        pre = "var _RENDERERS = {};\n" + src + "\n"
        body = HARNESS.replace("renderAtoms([BLOCK], {})", "_RENDERERS.globe_3d(BLOCK)").replace("BLOCK", json.dumps(block))
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "d.js"
        p.write_text(pre + body)
        proc = subprocess.run(["node", str(p)], capture_output=True, text=True, timeout=120)
        assert proc.returncode == 0, proc.stderr[-1500:]
        return json.loads(proc.stdout.strip().split("\n")[-1])


BASE = {"type": "globe_3d", "size": 240, "color": "#10b981"}


@pytest.mark.parametrize("gas_dir", GAS_DIRS)
def test_schema_conformant_from_to_arc_is_drawn(core_js, gas_dir):
    b = dict(BASE, arcs=[{"from": [48.85, 2.35], "to": [-33.87, 151.21], "color": "#f59e0b"}])
    rec = _run(core_js, b, gas_dir)
    assert rec["error"] is None, rec["error"]
    assert any(s.lower().startswith("#f59e0b") for s in rec["strokes"]), rec["strokes"][-5:]


@pytest.mark.parametrize("gas_dir", GAS_DIRS)
def test_legacy_start_end_arc_still_drawn(core_js, gas_dir):
    b = dict(BASE, arcs=[{"start": [48.85, 2.35], "end": [-33.87, 151.21], "color": "#f59e0b"}])
    rec = _run(core_js, b, gas_dir)
    assert rec["error"] is None, rec["error"]
    assert any(s.lower().startswith("#f59e0b") for s in rec["strokes"])


@pytest.mark.parametrize("gas_dir", GAS_DIRS)
def test_malformed_arcs_and_pins_are_skipped_not_thrown(core_js, gas_dir):
    b = dict(BASE, arcs=[{}, {"from": [1]}, None, "x", {"from": ["a", "b"], "to": [0, 0]},
                         {"from": [0, 0], "to": [10, 10], "color": "#f59e0b"}],
             dots=[None, {"lat": "x", "lon": 1}, {"lat": 10, "lon": 0, "color": "#ef4444"}])
    rec = _run(core_js, b, gas_dir)
    assert rec["error"] is None, rec["error"]
    assert any(s.lower().startswith("#f59e0b") for s in rec["strokes"])
    assert any(f.lower() == "#ef4444" for f in rec["fills"])


@pytest.mark.parametrize("gas_dir", GAS_DIRS)
def test_per_pin_color_is_honoured_and_default_falls_back(core_js, gas_dir):
    b = dict(BASE, dots=[{"lat": 10, "lon": 0, "color": "#ef4444"}, {"lat": 12, "lon": 5}])
    rec = _run(core_js, b, gas_dir)
    assert rec["error"] is None, rec["error"]
    assert any(f.lower() == "#ef4444" for f in rec["fills"]), rec["fills"]
    assert any(f.lower() == "#10b981" for f in rec["fills"]), rec["fills"]
