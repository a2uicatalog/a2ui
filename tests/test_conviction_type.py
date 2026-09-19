"""Conviction typography (2026-09-19): weighted_words, stance, receipt,
changed_mind -- typographic objects an agent fills to share a point of view.
Proven against BOTH real renderers (GAS via the Node-eval harness
test_agent_sketchpad.py uses; Python via renderers/web_article.py):

1. Parity, identical markup modulo uid -- including apostrophes and unicode,
   since conviction copy is full of both (the Python side mirrors GAS _esc
   exactly rather than using html.escape).
2. Numbers are computed with integer arithmetic on both sides (stance's
   confidence -> weight/size/tracking/opacity; receipt's barcode from a
   djb2+LCG hash over UTF-16 code units), so they cannot drift by a float.
3. Copy is data: hostile strings are escaped, every option is an enum or a
   clamped number, URLs must be http(s).
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

from renderers.web_article import (  # noqa: E402
    _render_weighted_words, _render_stance, _render_receipt, _render_changed_mind,
)

PY = {"weighted_words": _render_weighted_words, "stance": _render_stance,
      "receipt": _render_receipt, "changed_mind": _render_changed_mind}
UID_RE = re.compile(r"\b(ww|st-t|st-r|st-l|st-s|rc|cm-s|cm-a)-[a-z0-9]{6}\b")


@pytest.fixture(scope="module")
def core_js():
    bundle = gen.build_bundle()
    blocks = re.findall(r"<script>\n(.*?)\n</script>", bundle, re.S)
    core = [b for b in blocks if "a2ui-core" in b[:300]]
    assert core, "a2ui-core script block missing"
    return core[0]


def _gas(core_js, block: dict) -> str:
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
    return UID_RE.sub(r"\1-UID", html)


HOSTILE = "It's <b>\"bold\"</b> & 日本語 — 🚀 </script>"

PAYLOADS = {
    "weighted_words": [
        {},
        {"text": "Agents don't need chat, they need surfaces"},
        {"words": [{"text": "AG-UI", "weight": 5}, "standardises", {"text": "the", "weight": 1},
                   {"text": "choreography,", "weight": 4}, {"text": "not", "weight": 3}, {"text": "the costume", "weight": 9},
                   {"text": "", "weight": 3}, {"weight": 2}, 42],
         "voice": "serif", "theme": "light", "accent": "#DC2626", "align": "center", "animate": False},
        {"words": [{"text": HOSTILE, "weight": 5}]},
    ],
    "stance": [
        {},
        {"claim": "A2UI is a document contract, not a Google feature", "confidence": 0.82,
         "because": "it survives a framework switch; the schema is the API",
         "unless": "a host ships a renderer that ignores the schema", "voice": "serif", "theme": "light"},
        {"claim": HOSTILE, "confidence": 82, "interactive": False, "accent": "#a855f7"},
        {"claim": "edge", "confidence": 1.7}, {"claim": "edge", "confidence": -3}, {"claim": "edge", "confidence": "0.125"},
        {"claim": "edge", "confidence": "nope"}, {"claim": "edge", "confidence": True},
    ],
    "receipt": [
        {},
        {"claim": "GAS links can't ship new renderer code today", "issued": "2026-09-19",
         "items": [{"text": "script project at the 200-version cap", "source": "project-ops.yaml", "url": "https://github.com/a2uicatalog/a2ui"},
                   {"text": "clasp deploy fails outright", "source": "ops log"},
                   "versions can never be deleted",
                   {"text": "javascript trap", "source": "x", "url": "javascript:alert(1)"},
                   {"text": ""}, {"nope": 1}],
         "total": 0.9, "accent": "#0e7bb8"},
        {"claim": HOSTILE, "items": [HOSTILE], "total": 55, "merchant": HOSTILE, "footer": HOSTILE, "print_last": False},
        {"claim": "many", "items": [f"item {i}" for i in range(40)]},
    ],
    "changed_mind": [
        {},
        {"before": "AG-UI and A2UI compete", "after": "They're different layers: run vs form",
         "since": "since the sketch demo ran A2UI-free on the same AG-UI runtime", "theme": "light", "animate": False},
        {"before": HOSTILE, "after": HOSTILE, "since": HOSTILE, "accent": "#22c55e", "voice": "mono"},
    ],
}


@pytest.mark.parametrize("atom,block", [(a, b) for a, bs in PAYLOADS.items() for b in bs])
def test_python_matches_gas_exactly(core_js, atom, block):
    assert _norm(_gas(core_js, dict(block, type=atom))) == _norm(PY[atom](dict(block)))


@pytest.mark.parametrize("atom", list(PY))
def test_hostile_copy_is_escaped_on_both_sides(core_js, atom):
    def _has(v):
        if isinstance(v, str):
            return v == HOSTILE
        if isinstance(v, dict):
            return any(_has(x) for x in v.values())
        return isinstance(v, list) and any(_has(x) for x in v)
    block = [b for b in PAYLOADS[atom] if _has(b)][0]
    for html in (PY[atom](block), _gas(core_js, dict(block, type=atom))):
        assert "<b>" not in html and "&lt;b&gt;" in html
        assert "&#39;" in html and "&quot;" in html
        assert "javascript:" not in html
        # only stance carries a script, and only when interactive
        assert html.count("<script>") == (1 if atom == "stance" and block.get("interactive") is not False else 0)


@pytest.mark.parametrize("conf,pct,weight,size,spacing,opacity", [
    (0.82, 82, 800, "2.71rem", "-0.02em", "0.92"),
    (82, 82, 800, "2.71rem", "-0.02em", "0.92"),
    (0, 0, 300, "1.40rem", "0.02em", "0.60"),
    (1, 100, 900, "3.00rem", "-0.03em", "1"),
    (1.7, 2, 300, "1.43rem", "0.02em", "0.60"),   # above 1 reads as percent
    (-3, 0, 300, "1.40rem", "0.02em", "0.60"),
    ("0.125", 13, 400, "1.60rem", "0.02em", "0.65"),
    ("nope", 50, 600, "2.20rem", "0.00em", "0.80"),
    (None, 50, 600, "2.20rem", "0.00em", "0.80"),
])
def test_stance_typography_is_a_function_of_confidence(conf, pct, weight, size, spacing, opacity):
    html = _render_stance({"claim": "c", "confidence": conf})
    assert f"confidence {pct}%" in html and f'value="{pct}"' in html
    assert f"font-weight:{weight};font-size:{size};letter-spacing:{spacing};opacity:{opacity};" in html


def test_stance_slider_script_passes_node_check_and_is_optional():
    html = _render_stance({"claim": "c"})
    script = re.search(r"<script>(.*)</script>", html, re.S).group(1)
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "s.js"
        f.write_text(script)
        assert subprocess.run(["node", "--check", str(f)], capture_output=True, text=True).returncode == 0
    assert "<script>" not in _render_stance({"claim": "c", "interactive": False})


def test_receipt_barcode_is_deterministic_and_claim_specific():
    a = _render_receipt({"claim": "same claim"})
    b = _render_receipt({"claim": "same claim", "items": ["x"]})
    c = _render_receipt({"claim": "other claim"})
    bars = lambda h: re.search(r"<svg[^>]*>(.*?)</svg>", h).group(1)
    assert bars(a) == bars(b) and bars(a) != bars(c)
    assert bars(a).count("<rect") == 48


def test_receipt_caps_items_prints_only_the_last_and_drops_bad_urls():
    html = _render_receipt({"claim": "c", "items": [f"i{n}" for n in range(40)]})
    assert html.count("flex:1 1 auto;min-width:0;") == 24
    assert html.count("animation:rc-") == 1
    assert "24 ITEMS" in html
    html = _render_receipt(PAYLOADS["receipt"][1])
    assert 'href="https://github.com/a2uicatalog/a2ui"' in html
    assert 'href="javascript' not in html and html.count("flex:1 1 auto;min-width:0;") == 4
    assert "<span>CONFIDENCE</span>" in html and ">90%<" in html
    assert "(no evidence yet)" in _render_receipt({"claim": "c"}) and "0 ITEMS" in _render_receipt({"claim": "c"})


def test_weighted_words_clamps_and_falls_back():
    html = _render_weighted_words(PAYLOADS["weighted_words"][2])
    assert 'title="weight 5/5"' in html and html.count("weight 5/5") == 2   # AG-UI and "the costume" (9 -> 5)
    assert "weight 9" not in html and html.count("<span") == 6              # empties and non-strings dropped
    assert "color:#dc2626" in html and "animation:" not in html
    html = _render_weighted_words({"words": [f"w{i}" for i in range(60)]})
    assert html.count("<span") == 40
    assert ">A2UI<" in _render_weighted_words({"words": []})


def test_changed_mind_animates_by_default_and_not_when_told():
    assert "cm-s-" in _render_changed_mind({}) and "cm-a-" in _render_changed_mind({})
    assert "animation:" not in _render_changed_mind({"animate": False})
