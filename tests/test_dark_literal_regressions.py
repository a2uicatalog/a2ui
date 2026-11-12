"""Dark-theme regressions found by the branch-lane measurement (halftone_wave 1.04:1, flip_card back 2.66:1).

halftone_wave: its canvas paints a fixed light paper, but the dark literal remap turned the headline
white (var(--text)) and darkened the panel -> white on the light canvas. The renderer now wraps itself in
<!--asw-keep-->...<!--/asw-keep--> so the remap skips it; the markers never reach the output (light stays
byte-identical to the unwrapped markup).
flip_card: the global `p{color:var(--muted)}` greyed the back text on the accent card; the back face now
forces `p{color:inherit}` (white on the accent).
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
def render():
    bundle = gen.build_bundle()
    core = [b for b in re.findall(r"<script>\n(.*?)\n</script>", bundle, re.S) if "a2ui-core" in b[:300]][0]
    td = tempfile.mkdtemp()
    drv = Path(td) / "d.js"

    def run(block, theme):
        drv.write_text("global.window = global;\n" + core + "\nconsole.log(JSON.stringify(renderAtoms("
                       + json.dumps([block]) + ", {theme: %s})));" % json.dumps(theme))
        p = subprocess.run(["node", str(drv)], capture_output=True, text=True, timeout=60)
        assert p.returncode == 0, p.stderr[-500:]
        return json.loads(p.stdout)
    return run


HW = {"component": "halftone_wave", "title": "Halftone wave", "body": "A living dot field.", "eyebrow": "Hero"}


def test_halftone_wave_keeps_its_light_paper_and_ink_in_dark(render):
    dark, light = render(HW, "dark"), render(HW, "light")
    assert "asw-keep" not in dark and "asw-keep" not in light
    assert "color:var(--text)" not in dark              # title not remapped to the (white) dark text token
    assert "background:#f7f7f5" in dark and "color-mix" not in dark
    uid = lambda h: re.sub(r"\b(hw)-[a-z0-9]+\b|\b(hws?)[a-z0-9]{4,}\b", "UID", h)
    assert uid(dark) == uid(light)                                  # untouched by the remap: same markup as light


def test_other_atoms_still_remapped_in_dark(render):
    h = render({"component": "alert_banner", "message": "x"}, "dark")
    assert "asw-keep" not in h


def test_flip_card_back_text_inherits_the_card_colour(render):
    for theme in ("light", "dark"):
        h = render({"component": "flip_card", "front_content": "F", "back_content": "B"}, theme)
        assert re.search(r"\.fcb[a-z0-9]+ p\{color:inherit;\}", h)
