"""exit (opt-in leave animation) on wired layout elements.

A layout element may carry `exit: "fade"` or `{effect, ease, duration, delay}`, the same shape and
the same effect names as the generic `enter`. The wired renderer writes it onto the element's
wrapper; the engine's `visible` wire (A2UIState.html, _a2uiSetVisible) plays it before hiding.
No `exit` means the old instant hide. The browser half runs the real engine function in Chromium.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import gen_mcp_apps_bundle as gen  # noqa: E402

CHROMIUM = shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome")
ENGINE = ROOT / "apps-script-surface" / "gas-wired-renderer" / "A2UIState.html"

LAYOUT = [
    {"atom": "stat_card", "id": "a", "props": {"label": "A", "value": "1"}, "wire": {"visible": "#s.value"},
     "exit": {"effect": "rise", "duration": 200, "ease": "standard", "delay": 10, "intensity": 0.5}},
    {"atom": "stat_card", "id": "b", "props": {"label": "B", "value": "2"}, "exit": "rise"},
    {"atom": "stat_card", "id": "c", "props": {"label": "C", "value": "3"}},
    {"atom": "stat_card", "id": "d", "props": {"label": "D", "value": "4"}, "exit": {"effect": "nope", "duration": 99999999, "ease": [9, 9, 9, 9], "delay": -5}},
    {"atom": "stat_card", "id": "e", "props": {"label": "E", "value": "5"}, "exit": {"effect": "wipe\"><script>1</script>", "ease": "x\";}", "duration": "quick"}},
    {"atom": "stat_card", "id": "f", "props": {"label": "F", "value": "6"}, "exit": 5},
    {"atom": "stat_card", "id": "g", "props": {"label": "G", "value": "7"}, "exit": {"effect": "drop", "ease": "heavy"}},
]


@pytest.fixture(scope="module")
def core_js():
    bundle = gen.build_bundle()
    return [b for b in re.findall(r"<script>\n(.*?)\n</script>", bundle, re.S) if "a2ui-core" in b[:300]][0]


@pytest.fixture(scope="module")
def html(core_js):
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "d.js"
        d.write_text("global.window = global;\n" + core_js + f"""
console.log(JSON.stringify(_a2uiRenderWiredLayout({{layout: {json.dumps(LAYOUT)}, state_primitives: []}})));""")
        p = subprocess.run(["node", str(d)], capture_output=True, text=True, timeout=60)
        assert p.returncode == 0, p.stderr[-1500:]
        return json.loads(p.stdout)


def _wrapper(html, i):
    m = re.search(r'<div id="a2ui-%s"([^>]*)>' % i, html)
    assert m, i
    return m.group(1)


def test_exit_is_written_on_the_wrapper_with_granular_values(html):
    w = _wrapper(html, "a")
    assert 'data-mo-exit="rise"' in w
    assert "--mo-exit-dur:calc(200ms * var(--a2ui-motion-duration-scale,1))" in w
    assert "--mo-exit-ease:cubic-bezier(0.4,0,0.2,1)" in w          # the `standard` token
    assert "--mo-exit-delay:10ms" in w
    assert "--mo-k:calc(var(--a2ui-motion-intensity-scale,1) * 0.5);" in w     # element intensity x the page-wide scale


def test_string_form_uses_the_leave_defaults(html):
    w = _wrapper(html, "b")
    assert 'data-mo-exit="rise"' in w
    assert "calc(240ms *" in w                                       # quick
    assert "--mo-exit-ease:cubic-bezier(0.4,0,1,1)" in w             # accelerate
    assert "--mo-exit-delay:0ms" in w
    assert "* 1);" in w                                              # intensity defaults to 1


def test_no_exit_means_no_attribute_and_no_leave_css_for_that_element(html):
    assert "data-mo-exit" not in _wrapper(html, "c")
    assert "--mo-exit" not in _wrapper(html, "c")


def test_bad_values_are_clamped_or_defaulted(html):
    w = _wrapper(html, "d")
    assert 'data-mo-exit="fade"' in w                                # unknown effect
    assert "calc(8000ms *" in w                                      # duration clamped
    assert "--mo-exit-delay:0ms" in w                                # negative delay
    assert "9" not in re.search(r"--mo-exit-ease:([^;]*)", w).group(1).replace("0.9", "")  # the four 9s were clamped
    assert "data-mo-exit" not in _wrapper(html, "f")                 # a number is not a spec


def test_hostile_values_do_not_reach_markup(html):
    w = _wrapper(html, "e")
    assert "<script" not in html.lower()                              # the injected tag never became markup
    assert 'data-mo-exit="fade"' in w and "<" not in w and '";}' not in w


def test_each_effect_keyframes_and_the_leave_rule_are_emitted_once(html):
    assert html.count("@keyframes moo-rise{") == 1
    assert ".mo-leave[data-mo-exit=rise]{animation:moo-rise var(--mo-exit-dur) var(--mo-exit-ease) var(--mo-exit-delay) both}" in html
    assert "prefers-reduced-motion:reduce){.mo-leave{animation:none!important}" in html
    assert "@keyframes moo-rise{to{opacity:0;transform:translateY(calc(24px * var(--mo-k,1)))}}" in html     # the enter keyframes, reversed


def test_wipe_exit_reverses_both_halves(core_js):
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "d.js"
        d.write_text("global.window = global;\n" + core_js + "\nconsole.log(_moExitSpec('wipe').kf);")
        out = subprocess.run(["node", str(d)], capture_output=True, text=True, timeout=30).stdout.strip()
    assert out == "@keyframes moo-wipe{from{clip-path:inset(0 0 0 0)}to{clip-path:inset(0 100% 0 0)}}"


def _engine_fn():
    src = ENGINE.read_text()
    i = src.index("function _a2uiSetVisible")
    j = src.index("A2UIStateEngine.prototype.compileWires")
    return src[i:j]


def _run_page(body_js, extra_args=(), root_style=""):
    assert CHROMIUM
    with tempfile.TemporaryDirectory() as td:
        page = Path(td) / "p.html"
        page.write_text(f"""<!doctype html><meta charset=utf-8>
<style>{root_style}@keyframes moo-fade{{to{{opacity:0}}}}.mo-leave[data-mo-exit=fade]{{animation:moo-fade var(--mo-exit-dur) var(--mo-exit-ease) var(--mo-exit-delay) both}}</style>
<div id="a2ui-x" data-mo-exit="fade" style="--mo-exit-dur:calc(200ms * var(--a2ui-motion-duration-scale,1));--mo-exit-ease:linear;--mo-exit-delay:0ms">x</div>
<div id="a2ui-y">y</div><script>{_engine_fn()}
var x=document.getElementById("a2ui-x"),y=document.getElementById("a2ui-y"),log=[];
function snap(k){{log.push(k+":"+x.style.display+"/"+x.classList.contains("mo-leave"))}}
{body_js}
</script>""")
        out = subprocess.run([CHROMIUM, "--headless=new", "--no-sandbox", "--disable-gpu", f"--user-data-dir={td}/prof",
                              "--virtual-time-budget=4000", "--dump-dom", *extra_args, f"file://{page}"],
                             capture_output=True, text=True, timeout=60).stdout
    m = re.search(r"<title>([^<]*)</title>", out)
    assert m, out[-500:]
    return m.group(1)


@pytest.mark.skipif(not CHROMIUM, reason="no Chromium for the in-browser engine test")
def test_engine_plays_the_leave_then_hides():
    log = _run_page("""
_a2uiSetVisible(x,false); snap("t0");
setTimeout(function(){snap("mid")},80);
setTimeout(function(){snap("end");document.title=log.join(" ")},500);""")
    assert log.startswith("t0:/true"), log            # still displayed, leave class on
    assert "mid:/true" in log, log                    # 80 ms into a 200 ms leave
    assert "end:none/false" in log, log               # hidden once it finished, class cleaned up


@pytest.mark.skipif(not CHROMIUM, reason="no Chromium for the in-browser engine test")
def test_showing_again_cancels_a_leave_in_progress():
    log = _run_page("""
_a2uiSetVisible(x,false);
setTimeout(function(){_a2uiSetVisible(x,true);snap("back")},60);
setTimeout(function(){snap("later");document.title=log.join(" ")},500);""")
    assert "back:/false" in log and "later:/false" in log, log


@pytest.mark.skipif(not CHROMIUM, reason="no Chromium for the in-browser engine test")
def test_without_data_mo_exit_the_hide_is_instant():
    log = _run_page("""
_a2uiSetVisible(y,false);log.push("y:"+y.style.display+"/"+y.classList.contains("mo-leave"));
document.title=log.join(" ");""")
    assert log == "y:none/false", log


@pytest.mark.skipif(not CHROMIUM, reason="no Chromium for the in-browser engine test")
def test_reduced_motion_hides_instantly():
    log = _run_page("""
_a2uiSetVisible(x,false);snap("rm");document.title=log.join(" ");""", extra_args=("--force-prefers-reduced-motion",))
    assert log == "rm:none/false", log


def test_a_spring_exit_brings_its_curve_through_a_supports_guarded_variable(html):
    w = _wrapper(html, "g")
    assert 'data-mo-spring="1"' in w and "--mo-exit-lin:linear(0, " in w
    assert "--mo-exit-ease:cubic-bezier(0.34,1.56,0.64,1)" in w and "calc(640ms *" in w   # heavy: fallback bezier, natural 640 ms
    assert "@supports (animation-timing-function:linear(0,1)){.mo-leave[data-mo-spring]{animation-timing-function:var(--mo-exit-lin)}}" in html
    assert "--mo-exit-lin" not in _wrapper(html, "a")                      # a plain ease carries no spring variable


@pytest.mark.skipif(not CHROMIUM, reason="no Chromium for the in-browser engine test")
def test_reduced_motion_with_the_fade_policy_still_plays_the_leave():
    log = _run_page("""
_a2uiSetVisible(x,false);snap("t0");
setTimeout(function(){snap("end");document.title=log.join(" ")},500);""",
                    extra_args=("--force-prefers-reduced-motion",), root_style=":root{--a2ui-reduced-motion:fade}")
    assert log.startswith("t0:/true") and "end:none/false" in log, log      # leave played, then hidden


@pytest.mark.skipif(not CHROMIUM, reason="no Chromium for the in-browser engine test")
def test_reduced_motion_without_the_policy_is_still_instant():
    log = _run_page("""_a2uiSetVisible(x,false);snap("rm");document.title=log.join(" ");""",
                    extra_args=("--force-prefers-reduced-motion",), root_style=":root{--a2ui-reduced-motion:other}")
    assert log == "rm:none/false", log
