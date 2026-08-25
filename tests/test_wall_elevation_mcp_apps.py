"""wall_elevation's mcp-apps (JS) renderer -- apps-script-surface/gas-
wired-renderer/atoms_wall.gs. Deliberately AI-free: real semantic
parameters in (height_m, width_m, block_id, pattern, load_bearing,
include_dpc, builders), deterministic layout/course math out -- ported
from a real prior agent's tested formulas (wall-builder-agent, a Gemini
Enterprise A2A demo), not redesigned. A parallel Python renderer
(renderers/web_article.py) targets the identical field contract and
formulas; this file's golden-case numbers are independently verified
against the real Python math (see each test's own docstring), not just
copied from a spec.

Drives the atom through the REAL browser-portable bundle
(gen_mcp_apps_bundle.build_bundle()) via a single Node process per test
module -- .gs renderer files aren't Node-requireable modules, matching
this repo's established pattern for testing them (see
test_freeform_canvas_mcp_apps.py / test_mcp_apps_bundle.py).
"""

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


@pytest.fixture(scope="module")
def core_js():
    bundle = gen.build_bundle()
    blocks = re.findall(r"<script>\n(.*?)\n</script>", bundle, re.S)
    core = [b for b in blocks if "a2ui-core" in b[:300]]
    assert core, "a2ui-core script block missing"
    return core[0]


def _render_all(core_js, cases):
    """{name: block} -> {name: html or 'THREW: <message>'}, one real Node
    process for the whole batch (matches this repo's established single-
    invocation-per-module discipline)."""
    for c in cases.values():
        c.setdefault("component", c["type"])
    with tempfile.TemporaryDirectory() as td:
        driver = Path(td) / "driver.js"
        driver.write_text(
            "global.window = global;\n" + core_js +
            "\nvar cases = " + json.dumps(cases) + ";\n"
            "var out = {};\n"
            "for (var k in cases) {\n"
            "  try { out[k] = renderAtoms([cases[k]], {theme: 'light'}); }\n"
            "  catch (e) { out[k] = 'THREW: ' + e.message; }\n"
            "}\n"
            "console.log(JSON.stringify(out));\n"
        )
        proc = subprocess.run(["node", str(driver)], capture_output=True,
                               text=True, timeout=60)
        assert proc.returncode == 0, proc.stderr[-2000:]
        return json.loads(proc.stdout)


def _calc_all(core_js, cases):
    """Like _render_all, but returns the raw _wallCalc() result for each
    case instead of rendered HTML -- for tests that need to assert on the
    actual computed numbers, not just "did it render"."""
    with tempfile.TemporaryDirectory() as td:
        driver = Path(td) / "driver.js"
        driver.write_text(
            "global.window = global;\n" + core_js +
            "\nvar cases = " + json.dumps(cases) + ";\n"
            "var out = {};\n"
            "for (var k in cases) {\n"
            "  var c = cases[k];\n"
            "  out[k] = _wallCalc(c.block_id, c.height_m, c.width_m, c.pattern, "
            "c.load_bearing, c.include_dpc, c.builders);\n"
            "}\n"
            "console.log(JSON.stringify(out));\n"
        )
        proc = subprocess.run(["node", str(driver)], capture_output=True,
                               text=True, timeout=60)
        assert proc.returncode == 0, proc.stderr[-2000:]
        return json.loads(proc.stdout)


def _base(**overrides):
    b = {"type": "wall_elevation", "height_m": 2.0, "width_m": 3.0}
    b.update(overrides)
    return b


def test_golden_case_matches_the_real_python_formula(core_js):
    """height_m=2.0, width_m=3.0, parpaing200, running -- verified
    independently against the real Python math (courses=ceil(2000/210)=10,
    per_course=ceil(3000/510)=6, total=60, weight=60*18.0=1080.0,
    cost=60*1.80=108.0), not copied from the build prompt blindly."""
    calc = _calc_all(core_js, {"case": {
        "block_id": "parpaing200", "height_m": 2.0, "width_m": 3.0,
        "pattern": "running", "load_bearing": False, "include_dpc": False,
        "builders": 2,
    }})["case"]
    assert calc["courses"] == 10
    assert calc["perCourse"] == 6
    assert calc["totalUnits"] == 60
    assert calc["totalWeightKg"] == 1080.0
    assert calc["totalCost"] == 108.0


def test_brique_stack_bond_matches_independently_verified_python(core_js):
    """height_m=1.0, width_m=2.0, brique, stack -- verified independently:
    courses=ceil(1000/65)=16, per_course=ceil(2000/230)=9, total=144."""
    calc = _calc_all(core_js, {"case": {
        "block_id": "brique", "height_m": 1.0, "width_m": 2.0,
        "pattern": "stack", "load_bearing": False, "include_dpc": False,
        "builders": 2,
    }})["case"]
    assert calc["courses"] == 16
    assert calc["perCourse"] == 9
    assert calc["totalUnits"] == 144


def test_parpaing150_renders(core_js):
    out = _render_all(core_js, {"case": _base(block_id="parpaing150")})["case"]
    assert not out.startswith("THREW:")
    assert "<svg" in out


def test_dimension_clamping_and_snapping(core_js):
    """0.2 <= dims <= 20.0, snapped to 0.2 increments -- below-min and
    above-max both clamp rather than error."""
    calc = _calc_all(core_js, {"case": {
        "block_id": "parpaing200", "height_m": 0.05, "width_m": 25.0,
        "pattern": "running", "load_bearing": False, "include_dpc": False,
        "builders": 2,
    }})["case"]
    assert calc["heightM"] == 0.2
    assert calc["widthM"] == 20.0


def test_builder_count_clamping(core_js):
    """1 <= builders <= 6; a non-numeric value falls back to the default
    (2), not an error."""
    driver_cases = {
        "below": {"block_id": "parpaing200", "height_m": 2.0, "width_m": 3.0,
                   "pattern": "running", "load_bearing": False, "include_dpc": False, "builders": 0},
        "above": {"block_id": "parpaing200", "height_m": 2.0, "width_m": 3.0,
                   "pattern": "running", "load_bearing": False, "include_dpc": False, "builders": 10},
        "nan": {"block_id": "parpaing200", "height_m": 2.0, "width_m": 3.0,
                 "pattern": "running", "load_bearing": False, "include_dpc": False, "builders": "not a number"},
    }
    calcs = _calc_all(core_js, driver_cases)
    assert calcs["below"]["builders"] == 1
    assert calcs["above"]["builders"] == 6
    assert calcs["nan"]["builders"] == 2


def test_load_bearing_advisory_fires_only_for_light_blocks(core_js):
    """brique (2.3kg) is below WALL_LOAD_BEARING_MIN_WEIGHT_KG (10.0) --
    advisory fires. parpaing200 (18.0kg) is above it -- advisory doesn't."""
    calcs = _calc_all(core_js, {
        "light": {"block_id": "brique", "height_m": 2.0, "width_m": 3.0,
                   "pattern": "running", "load_bearing": True, "include_dpc": False, "builders": 2},
        "heavy": {"block_id": "parpaing200", "height_m": 2.0, "width_m": 3.0,
                   "pattern": "running", "load_bearing": True, "include_dpc": False, "builders": 2},
        "light_not_selected": {"block_id": "brique", "height_m": 2.0, "width_m": 3.0,
                                 "pattern": "running", "load_bearing": False, "include_dpc": False, "builders": 2},
    })
    assert calcs["light"]["loadBearingAdvisory"] is True
    assert calcs["heavy"]["loadBearingAdvisory"] is False
    assert calcs["light_not_selected"]["loadBearingAdvisory"] is False


def test_height_advisory_fires_above_threshold(core_js):
    calcs = _calc_all(core_js, {
        "tall": {"block_id": "parpaing200", "height_m": 2.5, "width_m": 3.0,
                  "pattern": "running", "load_bearing": False, "include_dpc": False, "builders": 2},
        "short": {"block_id": "parpaing200", "height_m": 1.5, "width_m": 3.0,
                   "pattern": "running", "load_bearing": False, "include_dpc": False, "builders": 2},
    })
    assert calcs["tall"]["heightAdvisory"] is True
    assert calcs["short"]["heightAdvisory"] is False


def test_include_dpc_sets_length_to_width_otherwise_zero(core_js):
    calcs = _calc_all(core_js, {
        "with_dpc": {"block_id": "parpaing200", "height_m": 2.0, "width_m": 3.0,
                      "pattern": "running", "load_bearing": False, "include_dpc": True, "builders": 2},
        "without_dpc": {"block_id": "parpaing200", "height_m": 2.0, "width_m": 3.0,
                         "pattern": "running", "load_bearing": False, "include_dpc": False, "builders": 2},
    })
    assert calcs["with_dpc"]["dpcLengthM"] == 3.0
    assert calcs["without_dpc"]["dpcLengthM"] == 0.0


def test_build_days_curve_has_six_entries_and_is_monotonically_decreasing(core_js):
    calc = _calc_all(core_js, {"case": {
        "block_id": "parpaing200", "height_m": 2.0, "width_m": 3.0,
        "pattern": "running", "load_bearing": False, "include_dpc": False,
        "builders": 2,
    }})["case"]
    curve = calc["buildDaysCurve"]
    assert len(curve) == 6  # WALL_BUILDERS_MAX - WALL_BUILDERS_MIN + 1
    for i in range(len(curve) - 1):
        assert curve[i + 1] <= curve[i]


def test_running_bond_and_stack_bond_produce_different_svg_geometry(core_js):
    """Running bond staggers alternate courses by half a unit width; stack
    bond doesn't -- the two patterns must produce genuinely different SVG
    output for the same dimensions, not just a different label."""
    out = _render_all(core_js, {
        "running": _base(pattern="running"),
        "stack": _base(pattern="stack"),
    })
    assert out["running"] != out["stack"]
    assert "Running bond" in out["running"]
    assert "Stack bond" in out["stack"]


def test_full_render_includes_real_stats_not_just_the_svg(core_js):
    out = _render_all(core_js, {"case": _base()})["case"]
    assert "<svg" in out
    assert "Courses" in out
    assert "Total units" in out
    assert "Estimated cost" in out
