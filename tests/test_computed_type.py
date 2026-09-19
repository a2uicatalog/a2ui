"""type_scale, readability_card, drop_cap, contrast_audit (2026-09-19):
"calcs baked in" for typography and colour. Both renderers must agree
byte for byte (these have no uid at all), and the numbers must be the
numbers: modular-scale steps, Flesch arithmetic, WCAG ratios."""
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
    _render_type_scale, _render_readability_card, _render_drop_cap, _render_contrast_audit,
)

PY = {"type_scale": _render_type_scale, "readability_card": _render_readability_card,
      "drop_cap": _render_drop_cap, "contrast_audit": _render_contrast_audit}


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


PROSE = ("It's a truth universally acknowledged, that a single man in possession of a good fortune, must be in want of a wife. "
         "However little known the feelings or views of such a man may be on his first entering a neighbourhood, this truth is so well "
         "fixed in the minds of the surrounding families, that he is considered the rightful property of some one or other of their daughters. "
         "Short one! Really? Yes.")

PAYLOADS = {
    "type_scale": [{}, {"base": 18, "ratio": "golden", "steps_up": 8, "steps_down": 3, "sample": "Agents don't read; they render <b>", "voice": "serif", "theme": "dark", "accent": "#DC2626", "show_code": False},
                   {"base": 999, "ratio": "nope", "steps_up": 0, "steps_down": 9}],
    "readability_card": [{}, {"text": PROSE, "title": "Austen's opener", "wpm": 200}, {"text": "One sentence only", "highlight_longest": True, "theme": "dark"},
                         {"text": "<script>alert(1)</script> is not prose. Nor is this! Or this?"}],
    "drop_cap": [{}, {"text": '"Quoted" start with it\'s apostrophe & <b>tags</b>.', "style": "raised"}, {"text": "(Bracketed) boxed", "style": "boxed", "lines": 4, "theme": "dark"},
                 {"text": "Ornament style", "style": "ornament", "voice": "display", "accent": "#b45309"}, {"text": "", "style": "nope", "lines": 99}],
    "contrast_audit": [{}, {"pairs": [{"fg": "#000000", "bg": "#ffffff", "label": "black on white"}, {"fg": "#777777", "bg": "#ffffff", "label": "grey's 4.48"},
                                      {"fg": "#38bdf8", "bg": "#0b0d12", "label": "sky on ink"}, {"fg": "nope", "bg": "#ffffff"}, "junk", {"fg": "#ffffff", "bg": "#fbbf24"}], "theme": "dark"},
                       {"fg": "#0e7bb8", "bg": "#f7f7f5", "label": "single pair", "show_fix": False}],
}


@pytest.mark.parametrize("atom,block", [(a, b) for a, bs in PAYLOADS.items() for b in bs])
def test_python_matches_gas_byte_for_byte(core_js, atom, block):
    assert _gas(core_js, dict(block, type=atom)) == PY[atom](dict(block))


def test_type_scale_numbers_are_right():
    html = _render_type_scale({"base": 16, "ratio": "major_third", "steps_up": 3, "steps_down": 1})
    assert "font-size:31.25px" in html and "31.25px <span" in html and "1.953rem" in html   # 16 * 1.25^3
    assert "font-size:12.80px" in html and "0.800rem" in html                              # 16 / 1.25
    assert "--step-3: 1.953rem; /* 31.25px */" in html and "--step-n1: 0.800rem" in html
    assert "Major third <span" in html and ">1.25</span>" in html and "5 steps" in html
    html = _render_type_scale({"base": 999, "ratio": "nope", "steps_up": 0, "steps_down": 9})
    assert "base 32px" in html and "Major third" in html and "5 steps" in html             # clamps: 32, 1, 3


def test_readability_arithmetic():
    html = _render_readability_card({"text": "The cat sat. The dog ran fast! Why?", "wpm": 100})
    # 8 words, 3 sentences, syllables: the(1) cat(1) sat(1) the(1) dog(1) ran(1) fast(1) why(1) = 8
    # flesch = 206.835 - 1.015*(8/3) - 84.6*(8/8) = 206.835 - 2.7067 - 84.6 = 119.528 -> 119.5
    assert ">119.5<" in html and "very easy" in html
    assert ">8</div>" in html and ">3</div>" in html and ">1 min</div>" in html and ">2.67</div>" in html and ">1.00</div>" in html
    assert html.count("<mark") == 1 and "<mark" in html.split("The dog ran fast!")[0]
    html = _render_readability_card({"text": "<script>alert(1)</script> is not prose."})
    assert "<script" not in html and "&lt;script&gt;" in html
    assert "<mark" not in _render_readability_card({"text": "One sentence only"})


def test_drop_cap_skips_leading_quotes_and_styles():
    html = _render_drop_cap({"text": '"Quoted" start', "style": "raised"})
    assert '>Q</span>&quot;uoted&quot; start</p>' in html and "font-size:2.6em" in html and "float:left" not in html
    assert "float:left;font-size:4.2em" in _render_drop_cap({"text": "Boxed", "style": "boxed", "lines": 4})
    assert "border-right:1px solid #b45309" in _render_drop_cap({"text": "Orn", "style": "ornament", "accent": "#b45309"})
    assert "font-size:5em" in _render_drop_cap({"text": "Default", "lines": 99})   # lines clamp to 4 -> 4 * 1.25 and ">A</span>2UI</p>" in _render_drop_cap({"text": ""})


def test_contrast_ratios_and_fix():
    html = _render_contrast_audit(PAYLOADS["contrast_audit"][1])
    assert ">21.00:1<" in html and ">4.48:1<" in html
    assert "AA fail" in html and "nearest pass:" in html and "2 of 4 pass AA" in html    # black/white, sky/ink pass; grey and white/amber fail
    assert "junk" not in html and html.count("Aa <span") == 4
    single = _render_contrast_audit({"fg": "#767676", "bg": "#ffffff"})
    assert ">4.54:1<" in single and "AA pass" in single
    assert "nearest pass" not in _render_contrast_audit({"fg": "#777777", "bg": "#ffffff", "show_fix": False})
