"""confetti_trigger raised NameError ('Math' is not defined) on every payload: a quote closed its JS string early, so Python parsed
Math.random() as code (found 1 Nov 2026 while curating examples). It also put double quotes inside a double-quoted onclick."""
from __future__ import annotations

import re
import shutil
import subprocess

import pytest

import web_article as wa


def _handler(html: str) -> str:
    m = re.search(r'onclick="([^"]*)"', html)
    assert m, html[:300]
    return m.group(1)


def test_every_payload_renders():
    for b in ({"type": "confetti_trigger"}, {"type": "confetti_trigger", "label": "Milestone reached: 1,000 members"}):
        html = wa.render([b])
        assert "<button" in html and "Math.random" in html


def test_the_handler_sits_whole_inside_its_attribute():
    html = wa.render([{"type": "confetti_trigger", "label": 'Hi "there" <b>'}])
    h = _handler(html)
    assert '"' not in h
    assert "&lt;b&gt;" in html and "<b>" not in html          # the label is escaped


@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
def test_the_handler_is_valid_javascript(tmp_path):
    f = tmp_path / "h.js"
    f.write_text(_handler(wa.render([{"type": "confetti_trigger", "label": "Go"}])))
    r = subprocess.run(["node", "--check", str(f)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
