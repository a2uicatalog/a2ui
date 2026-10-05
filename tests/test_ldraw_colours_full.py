"""gen_ldraw_colours_full.py: parses the REAL LDConfig.ldr into a full colour+material table (all ~322 codes,
including ALPHA transparency and CHROME/METAL/PEARLESCENT/RUBBER/glitter/speckle finish flags) for the Three.js
render-appearance integration. Verifies parsing against known, real, hand-checked LDConfig.ldr entries -- not
against fabricated expectations."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "public" / "bricksdemo" / "ldraw_colours_full.json"

# The generator reads the real LDConfig.ldr from the fetched LDraw library, which a clean checkout (CI) lacks.
from scripts.ldraw.resolve import LD  # noqa: E402
pytestmark = pytest.mark.skipif(not (Path(LD) / "LDConfig.ldr").exists(),
                                reason="LDraw library not fetched (scripts/ldraw/fetch_library.py)")


def _generate():
    subprocess.run([sys.executable, str(ROOT / "scripts" / "ldraw" / "gen_ldraw_colours_full.py")],
                    check=True, cwd=ROOT)
    return json.loads(OUT.read_text())


def test_full_colour_count_matches_the_real_ldconfig():
    d = _generate()
    assert len(d) == 322, "expected the real, full LDConfig.ldr colour count -- got %d" % len(d)


def test_opaque_default_colour_has_no_alpha_or_finish():
    d = _generate()
    red = d["4"]
    assert red["name"] == "Red" and red["hex"] == "#b40000"
    assert red["alpha"] == 255 and red["finish"] is None


def test_trans_clear_carries_the_real_alpha_value():
    d = _generate()
    tc = d["47"]
    assert tc["name"] == "Trans_Clear"
    assert tc["alpha"] == 128, "LDConfig's own real ALPHA for Trans_Clear (47) is 128, not guessed"
    assert tc["finish"] is None, "plain transparency is not a special finish"


def test_chrome_silver_is_flagged_chrome_and_fully_opaque():
    d = _generate()
    cs = d["383"]
    assert cs["name"] == "Chrome_Silver"
    assert cs["finish"] == "chrome"
    assert cs["alpha"] == 255, "chrome is reflective, not transparent"


def test_pearl_gold_is_flagged_pearlescent():
    d = _generate()
    pg = d["297"]
    assert pg["name"] == "Pearl_Gold" and pg["finish"] == "pearlescent"


def test_glow_in_dark_carries_real_luminance():
    d = _generate()
    g = d["21"]
    assert g["name"] == "Glow_In_Dark_Opaque"
    assert g["luminance"] == 15


def test_glitter_colour_is_flagged_glitter_not_a_generic_material_string():
    d = _generate()
    g = d["117"]
    assert g["name"] == "Glitter_Trans_Clear" and g["finish"] == "glitter"
