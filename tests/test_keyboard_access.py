"""Keyboard access (WCAG 2.1.1, 2.4.7): hidden radios/checkboxes must stay focusable, clickable non-controls must be operable.

Found 2026-10-10 by the IBM Equal Access cross-check in a2ui-private/a11y (axe-core does not report these): the CSS radio/checkbox
trick used `display:none`, which removes the input from the tab order, so a keyboard user could not change a tab, rating or slide;
and `<span onclick>` had no role, tab stop or key handler. renderAtoms now wraps every renderer (atom.gs `_a11yInstall`) and fixes
the final markup. This test renders every atom's example through the real core and holds that line.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "scripts"), str(Path(__file__).parent)]
from test_motion_atoms import CHROMIUM, _gas_batch, browser, core_js  # noqa: E402,F401  (core_js is a fixture)

FOCUS_ATOMS = ["tabs", "content_tabs", "tabbed_code", "segmented_control", "star_rating_input", "custom_checkbox_group", "multi_select_input",
               "carousel", "seat_map", "step_reveal_sequence", "gmail_inbox"]


def _examples():
    import generate_atom_pages as g
    out = {}
    for a in yaml.safe_load((ROOT / "atoms/schema.yaml").read_text())["blocks"]:
        try:
            out[a["type"]] = g._EXAMPLE_BLOCKS.get(a["type"]) or json.loads(g.example_payload(a))
        except Exception:
            pass
    return out


@pytest.fixture(scope="module")
def rendered(core_js):
    ex = _examples()
    keys = sorted(ex)
    return dict(zip(keys, _gas_batch(core_js, [ex[k] for k in keys])))


def test_no_radio_or_checkbox_is_removed_from_the_tab_order(rendered):
    for k, h in rendered.items():
        assert not re.search(r'<input\b[^>]*type="?(?:radio|checkbox)[^>]*style="display:none', h), k
        if re.search(r'type="?(?:radio|checkbox)', h):
            assert not re.search(r"input(?:\[type=(?:radio|checkbox)\])?\s*\{\s*display:\s*none", h), k


def test_every_clickable_non_control_is_a_tab_stop_with_a_key_handler(rendered):
    for k, h in rendered.items():
        for m in re.finditer(r"<(\w+)\b([^>]*\sonclick=[^>]*)>", re.sub(r"<script\b.*?</script>", "", h, flags=re.S)):
            tag, at = m.group(1).lower(), m.group(2)
            if tag in ("a", "button", "input", "select", "textarea", "summary", "label", "option", "details", "svg", "path", "circle", "rect", "g", "line", "polygon", "text"):
                continue
            assert "tabindex=" in at and "onkeydown=" in at, (k, m.group(0)[:160])


def test_output_is_unchanged_when_there_is_nothing_to_fix(core_js):
    from_core = _gas_batch(core_js, [{"type": "heading", "text": "Hello", "level": 2}])[0]
    assert "a2ui-vh" not in from_core and "data-a2ui-vh" not in from_core and "tabindex" not in from_core


@browser
@pytest.mark.parametrize("atom", FOCUS_ATOMS)
def test_the_hidden_input_can_actually_take_keyboard_focus(rendered, atom):
    h = rendered.get(atom)
    if not h or not re.search(r'type="?(?:radio|checkbox)', h):
        pytest.skip(f"{atom}: no radio/checkbox in its example")
    page = ("<!doctype html><meta charset=utf-8><body>" + h + "<script>var i=document.querySelector('input[type=radio]:not([disabled]),input[type=checkbox]:not([disabled])');"
            "i.focus();document.documentElement.setAttribute('data-ok',String(document.activeElement===i));</script>")
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "p.html"
        f.write_text(page)
        out = subprocess.run([CHROMIUM, "--headless=new", "--password-store=basic", "--no-sandbox", "--disable-gpu", "--virtual-time-budget=1000", "--dump-dom", f"file://{f}"],
                             capture_output=True, text=True, timeout=90).stdout
    assert 'data-ok="true"' in out, atom
