"""renderers/web_article.py's brick_build_3d must produce the same page as the JS renderer.

The engine and the page wiring are read out of apps-script-surface/gas-wired-renderer/atoms_brick.gs by both
sides, so they cannot differ. What is duplicated by hand — prop sanitising and the HTML shell — is what this
test holds together: the same props go through the real .gs (via Node) and through the Python twin, and the
output must match exactly, modulo the generated element id. Skipped when node is absent."""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from renderers.web_article import _RENDERERS

ROOT = Path(__file__).parent.parent
NODE = shutil.which("node") or "/home/curtis/.config/nvm/versions/node/v24.11.1/bin/node"
UID = re.compile(r"brk[a-z0-9]{3,8}")

BRICKS = [{"x": 0, "y": 0, "z": 0, "w": 2, "d": 2, "h": 1, "c": "#C91A09"},
          {"x": 0, "y": 1, "z": 0, "w": 2, "d": 2, "h": 1, "c": "#0055bf"}]

CASES = [
    {},
    {"shape": "house", "parts": True},
    {"shape": "torus", "mode": "steps", "step": 3, "speed": 2.5, "orbit": False, "height": 500},
    {"shape": "constructor"},                       # inherited Object property, not a shape
    {"shape": "nope", "bg": "red;x", "height": "9999", "speed": "abc"},
    {"bricks": "", "shape": "sphere"},              # an unresolved data-model binding arrives as ''
    {"bricks": BRICKS, "parts": True, "scrubber": False, "checks": False, "bg": "#abc"},
    {"bricks": [{"x": 0, "y": 0, "z": 0, "c": "</script><b>"}, {"x": "1e9", "y": -5, "z": 0},
                {"x": 2.7, "y": None, "z": "3", "w": 99, "d": 0, "h": 50}, "junk", None, 7]},
    {"bricks": [], "shape": "pyramid"},
    {"speed": 0}, {"speed": 10}, {"speed": "2.5"}, {"speed": None}, {"speed": 1.0},
    {"height": "  250px"}, {"height": 0}, {"height": 12.9}, {"step": "3"}, {"step": 0}, {"step": "x"},
    {"orbit": 0}, {"orbit": False}, {"parts": "yes"}, {"mode": "steps"}, {"mode": "STEPS"},
    # model picker
    {"models": [{"name": "Tower", "bricks": BRICKS}]},
    {"models": [{"name": "  Tower  ", "bricks": BRICKS}, {"bricks": BRICKS}, {"name": "x" * 60, "bricks": BRICKS}],
     "model": "Tower"},
    {"models": [{"name": "A", "bricks": BRICKS}, {"name": "B", "bricks": BRICKS}], "model": "B", "picker": False},
    {"models": [{"name": "</script><b>", "bricks": BRICKS}, {"name": "empty", "bricks": []}, {"name": "junk"},
                "junk", None, 7, {"name": 5, "bricks": BRICKS}]},
    {"models": [{"name": "n%d" % i, "bricks": BRICKS} for i in range(12)], "model": "n9"},
    {"models": "not a list"}, {"models": {}}, {"models": []},
    {"picker": True}, {"picker": "yes"}, {"picker": True, "bricks": BRICKS, "scrubber": False},
    {"bricks": BRICKS, "models": [{"name": "M", "bricks": BRICKS}], "model": "M"},   # explicit bricks win
    {"models": [{"name": "M", "bricks": BRICKS}], "model": "nope"}, {"models": [{"name": "M", "bricks": BRICKS}], "model": 3},
    # compact array bricks and palettes
    {"bricks": [[0, 0, 0, 2, 2, "#C91A09"], [0, 1, 0, 2, 2, 2, "#0055bf"], [3, 0, 0, 1, 1, "bad"]]},
    {"palette": ["#C91A09", "#0055BF", "nope", 5], "bricks": [[0, 0, 0, 2, 2, 0], [0, 1, 0, 2, 2, 1], [0, 2, 0, 1, 1, 2],
                                                            [1, 2, 0, 1, 1, 3], [2, 2, 0, 1, 1, 9], [3, 2, 0, 1, 1, -1]]},
    {"palette": ["#00ff00"], "bricks": [{"x": 0, "y": 0, "z": 0, "c": 0}, {"x": 1, "y": 0, "z": 0, "c": 0.9},
                                        {"x": 2, "y": 0, "z": 0, "c": True}, {"x": 3, "y": 0, "z": 0, "c": None}]},
    {"bricks": [[0, 0, 0, 1, 1, 1, 0]]},                                    # numeric colour, no palette: default red
    {"palette": ["#123456"], "bricks": [[0, 0, 0, 1, 1, 0], [1, 2], [1, 2, 3, 4, 5, 6, 7, 8], "junk", [None, "1e9", 0, 99, 0, 0]]},
    {"palette": "not a list", "bricks": [[0, 0, 0, 1, 1, 0]]}, {"palette": ["#abcdef"] * 300, "bricks": [[0, 0, 0, 1, 1, 255]]},
    {"palette": ["#111111"], "models": [{"name": "A", "bricks": [[0, 0, 0, 2, 2, 0]]},
                                       {"name": "B", "palette": ["#222222"], "bricks": [[0, 0, 0, 2, 2, 0]]},
                                       {"name": "C", "palette": "x", "bricks": [[0, 0, 0, 2, 2, 0]]}], "model": "B"},
]


def _norm(html):
    return UID.sub("UID", html)


@pytest.mark.skipif(not Path(NODE).exists() and not shutil.which("node"), reason="node not available")
def test_python_twin_matches_the_js_renderer(tmp_path):
    cases_file = tmp_path / "cases.json"
    cases_file.write_text(json.dumps(CASES))
    out = subprocess.run([NODE, str(ROOT / "scripts" / "brick_render_cases.mjs"), str(cases_file)],
                         capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    js_pages = json.loads(out.stdout)
    assert len(js_pages) == len(CASES)
    for props, js in zip(CASES, js_pages):
        py = _RENDERERS["brick_build_3d"](dict(props))
        assert _norm(py) == _norm(js), "twin diverged for props %r" % (props,)


def test_python_twin_is_deterministic_and_injection_safe():
    props = {"bricks": [{"x": 0, "y": 0, "z": 0, "c": "</script><b>"}]}
    a = _RENDERERS["brick_build_3d"](dict(props))
    assert a == _RENDERERS["brick_build_3d"](dict(props))       # catalog-rebuild must not churn
    assert a.count("</script>") == 1 and "<b>" not in a
