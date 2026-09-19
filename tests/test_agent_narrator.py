"""agent_narrator renderers (2026-09-19) for the schema entry authored with
streaming-testbench's demos/story: ordered prose beats, only the LAST types
itself in (same stateless full-rerender rule as agent_sketchpad). Proven on
both real renderers: parity modulo uid, only one typed beat, raw HTML never
survives, only the declared markdown subset is applied, caps skip not crash."""
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

from renderers.web_article import _render_agent_narrator  # noqa: E402

UID_RE = re.compile(r"\b(an|anc|an-blink)-[a-z0-9]{6}\b")


@pytest.fixture(scope="module")
def core_js():
    bundle = gen.build_bundle()
    blocks = re.findall(r"<script>\n(.*?)\n</script>", bundle, re.S)
    core = [b for b in blocks if "a2ui-core" in b[:300]]
    return core[0]


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


BEATS = [{"text": "It's the **first** beat.", "label": "opening"},
         {"text": "A *second* one with `code` & <b>no html</b>."},
         {"text": "The last beat, still typing…"}]


@pytest.mark.parametrize("block", [
    {}, {"beats": []}, {"title": "A story", "beats": BEATS}, {"beats": BEATS[:1]},
    {"beats": [{"text": ""}, {"nope": 1}, "str", {"text": "x" * 2001}, {"text": "kept"}]},
    {"beats": [{"text": f"beat {i}"} for i in range(105)]},
])
def test_python_matches_gas_exactly(core_js, block):
    g = UID_RE.sub(r"\1-UID", _gas(core_js, dict(block, type="agent_narrator")))
    p = UID_RE.sub(r"\1-UID", _render_agent_narrator(dict(block)))
    assert g == p


def test_only_the_last_beat_types_and_markdown_subset_only():
    html = _render_agent_narrator({"title": "T", "beats": BEATS})
    assert html.count('<span id="an-') == 1 and html.count("<p ") == 3
    assert "<strong>first</strong>" in html and "<em>second</em>" in html and "<code>code</code>" in html
    assert "<b>" not in html and "&lt;b&gt;" in html and "&#39;" in html
    assert html.count("<script>") == 1 and html.endswith("</script></div>")
    assert "prefers-reduced-motion" in html


def test_caps_skip_with_a_comment_and_console_warning_not_a_crash():
    html = _render_agent_narrator({"beats": [{"text": "x" * 2001}, {"text": "kept"}]})
    assert "1 beat(s) skipped" in html and 'console.warn("agent_narrator: 1 beat(s) skipped' in html and ">kept<" in html
    html = _render_agent_narrator({"beats": [{"text": f"b{i}"} for i in range(105)]})
    assert html.count("<p ") == 100 and "5 beat(s) skipped" in html


def test_empty_is_a_sentence_not_a_dead_block():
    html = _render_agent_narrator({})
    assert "(no beats yet)" in html and "<script>" not in html


def test_typing_script_passes_node_check():
    html = _render_agent_narrator({"beats": BEATS})
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "s.js"
        f.write_text(re.search(r"<script>(.*)</script>", html, re.S).group(1))
        assert subprocess.run(["node", "--check", str(f)], capture_output=True, text=True).returncode == 0
