"""Global motion control: every `enter` / `motion_group` / wired `exit` reads the palette's scales.

duration_scale scales durations, intensity_scale scales distance / scale / blur radius, stagger_scale
scales the gap between staggered items. Each element can also carry its own `intensity` (0-2), and the
two multiply. GAS and the Python twin must print identical markup (tests/test_motion_atoms.py holds the
older enter/motion_group behaviour; this file holds the scales).
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
from renderers.web_article import _RENDERERS  # noqa: E402

KID = {"type": "demo_orb"}   # a child both renderers draw identically (paragraph differs between them for reasons unrelated to motion)
CASES = {
    "enter_default": {"type": "stat_card", "label": "a", "value": "1", "enter": "rise"},
    "enter_intensity": {"type": "stat_card", "label": "a", "value": "1", "enter": {"effect": "pop", "intensity": 0.5}},
    "enter_clamped": {"type": "stat_card", "label": "a", "value": "1", "enter": {"effect": "rise", "intensity": 99}},
    "enter_junk": {"type": "stat_card", "label": "a", "value": "1", "enter": {"effect": "rise", "intensity": "<b>"}},
    "group": {"type": "motion_group", "effect": "slide-left", "duration": "quick", "delay": 40, "stagger": 100,
              "intensity": 1.5, "blocks": [KID, KID, KID]},
    "group_plain": {"type": "motion_group", "blocks": [KID, KID]},
}


@pytest.fixture(scope="module")
def gas():
    bundle = gen.build_bundle()
    core = [b for b in re.findall(r"<script>\n(.*?)\n</script>", bundle, re.S) if "a2ui-core" in b[:300]][0]
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "d.js"
        d.write_text("global.window = global;\n" + core + f"""
var cases = {json.dumps(CASES)}; var out = {{}};
Object.keys(cases).forEach(function(k) {{ out[k] = renderAtoms([cases[k]], {{}}); }});
console.log(JSON.stringify(out));""")
        p = subprocess.run(["node", str(d)], capture_output=True, text=True, timeout=60)
        assert p.returncode == 0, p.stderr[-1500:]
        return json.loads(p.stdout)


@pytest.fixture(scope="module")
def py():
    return {k: _RENDERERS[v["type"]](v) for k, v in CASES.items()}


def _norm(h):
    return re.sub(r"mo-[a-z0-9]{6}\b", "mo-X", h)


@pytest.mark.parametrize("name", list(CASES))
def test_gas_and_python_agree(name, gas, py):
    assert _norm(py[name]) in _norm(gas[name]), name


@pytest.fixture(params=["gas", "py"])
def html(request, gas, py):
    return (lambda n: gas[n]) if request.param == "gas" else (lambda n: py[n])


def test_duration_and_stagger_scales_are_read_by_enter(html):
    h = html("enter_default")
    assert "calc(560ms * var(--a2ui-motion-duration-scale,1))" in h
    assert "calc(0ms + 0ms * var(--a2ui-motion-stagger-scale,1))" in h


def test_every_effect_distance_reads_the_intensity_variable(html):
    h = html("enter_intensity")
    assert "scale(calc(1 - 0.4 * var(--mo-k,1)))" in h                    # pop
    assert "--mo-k:calc(var(--a2ui-motion-intensity-scale,1) * 0.5);" in h  # element 0.5 x page scale


def test_element_intensity_is_clamped_and_junk_falls_back_to_one(html):
    assert "* 2);" in html("enter_clamped")
    assert "* 1);" in html("enter_junk") and "<b>" not in html("enter_junk")


def test_motion_group_staggers_through_the_stagger_scale(html):
    h = html("group")
    for i in range(3):
        assert f"calc(40ms + {i * 100}ms * var(--a2ui-motion-stagger-scale,1))" in h
    assert h.count("* 1.5);") == 3 and "calc(240ms * var(--a2ui-motion-duration-scale,1))" in h


def test_unchanged_defaults_compute_the_same_values_as_before(html):
    # with no palette the variables fall back to 1, so durations, delays and distances are the old literals
    h = html("group_plain")
    assert "calc(560ms * var(--a2ui-motion-duration-scale,1))" in h
    assert "translateY(calc(24px * var(--mo-k,1)))" in h


def test_every_effect_keyframe_is_scale_aware_or_scale_free():
    from renderers.web_article import _MO_FX
    calc = re.compile(r"calc\([^()]*(?:\([^()]*\)[^()]*)*\)")
    for name, fx in _MO_FX.items():
        kf = fx["kf"]
        if name in ("fade", "wipe"):
            assert "--mo-k" not in kf, name                     # no distance to scale
            continue
        assert "var(--mo-k,1)" in kf, name
        rest = calc.sub("", kf)                                  # whatever is left outside a calc() is a fixed literal
        assert not re.search(r"\d+px|scale\(\d", rest), (name, rest)


def test_gas_and_python_effect_tables_match(gas):
    from renderers.web_article import _MO_FX
    # the rendered keyframes come straight from each table, so equal renders (above) already prove it; this pins the table too
    assert _MO_FX["pop"]["kf"] == "from{opacity:0;transform:scale(calc(1 - 0.4 * var(--mo-k,1)))}"


# ---- the scales really change what a browser plays (computed values, not just markup) ----
import shutil  # noqa: E402

CHROMIUM = shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome")


def _browser(palette: dict, group: dict):
    assert CHROMIUM
    page_html = _RENDERERS["palette"](dict(palette, type="palette")) + _RENDERERS["motion_group"](group)
    with tempfile.TemporaryDirectory() as td:
        page = Path(td) / "p.html"
        page.write_text(f"""<!doctype html><meta charset=utf-8>{page_html}<script>
var out=[];document.querySelectorAll(".mo-x").forEach(function(el){{
 var cs=getComputedStyle(el),a=el.getAnimations()[0];a.pause();a.currentTime=0;
 out.push(cs.animationDuration+"|"+cs.animationDelay+"|"+getComputedStyle(el).transform);}});
document.title=out.join(" ; ");</script>""")
        o = subprocess.run([CHROMIUM, "--headless=new", "--no-sandbox", "--disable-gpu", f"--user-data-dir={td}/prof",
                            "--virtual-time-budget=1500", "--dump-dom", f"file://{page}"],
                           capture_output=True, text=True, timeout=60).stdout
    m = re.search(r"<title>([^<]*)</title>", o)
    assert m, o[-400:]
    return [r.split("|") for r in m.group(1).split(" ; ")]


GROUP3 = {"type": "motion_group", "effect": "rise", "duration": 400, "delay": 100, "stagger": 200, "blocks": [KID, KID, KID]}


@pytest.mark.skipif(not CHROMIUM, reason="no Chromium for the in-browser check")
def test_browser_defaults_play_the_authored_values():
    rows = _browser({}, GROUP3)
    assert [r[0] for r in rows] == ["0.4s"] * 3
    assert [r[1] for r in rows] == ["0.1s", "0.3s", "0.5s"]
    assert rows[0][2] == "matrix(1, 0, 0, 1, 0, 24)"                 # starts 24 px low


@pytest.mark.skipif(not CHROMIUM, reason="no Chromium for the in-browser check")
def test_browser_palette_scales_change_duration_stagger_and_distance():
    rows = _browser({"duration_scale": 2, "stagger_scale": 0.5, "intensity_scale": 0.5}, GROUP3)
    assert [r[0] for r in rows] == ["0.8s"] * 3                      # 400 ms x 2
    assert [r[1] for r in rows] == ["0.1s", "0.2s", "0.3s"]          # 100 + (0,200,400) x 0.5
    assert rows[0][2] == "matrix(1, 0, 0, 1, 0, 12)"                 # 24 px x 0.5


@pytest.mark.skipif(not CHROMIUM, reason="no Chromium for the in-browser check")
def test_browser_zero_stagger_and_zero_intensity_collapse_the_choreography():
    rows = _browser({"stagger_scale": 0, "intensity_scale": 0}, GROUP3)
    assert [r[1] for r in rows] == ["0.1s"] * 3                      # everything together
    assert rows[0][2] in ("none", "matrix(1, 0, 0, 1, 0, 0)")        # no travel, only the fade


@pytest.mark.skipif(not CHROMIUM, reason="no Chromium for the in-browser check")
def test_browser_element_intensity_multiplies_with_the_page_scale():
    rows = _browser({"intensity_scale": 0.5}, dict(GROUP3, intensity=1.5))
    assert rows[0][2] == "matrix(1, 0, 0, 1, 0, 18)"                 # 24 x 0.5 x 1.5
