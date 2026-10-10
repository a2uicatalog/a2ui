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


def test_every_svg_has_a_name_or_is_hidden_from_assistive_tech(rendered):
    for k, h in rendered.items():
        for m in re.finditer(r"<svg\b([^>]*)>(.{0,40})", h, re.S):
            at, rest = m.group(1), m.group(2)
            assert re.search(r"aria-hidden=|role=\"?img|aria-label=|aria-labelledby=", at) or rest.lstrip().startswith("<title"), (k, m.group(0)[:120])


def test_an_icon_only_button_is_named_after_its_atom(rendered):
    for k, h in rendered.items():
        for m in re.finditer(r"<(button|a)\b([^>]*)>((?:(?!</\1>).)*?)</\1>", re.sub(r"<script\b.*?</script>", "", h, flags=re.S), re.S):
            inner = m.group(3)
            if "<svg" in inner and not re.sub(r"<[^>]*>", "", re.sub(r"<svg\b.*?</svg>", "", inner, flags=re.S)).strip():
                assert re.search(r"aria-label=|aria-labelledby=|title=", m.group(2)), (k, m.group(0)[:160])


def _in_browser(html, js):
    page = "<!doctype html><meta charset=utf-8><body>" + html + "<script>" + js + "</script>"
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "p.html"
        f.write_text(page)
        return subprocess.run([CHROMIUM, "--headless=new", "--password-store=basic", "--no-sandbox", "--disable-gpu", "--virtual-time-budget=1500", "--dump-dom", f"file://{f}"],
                              capture_output=True, text=True, timeout=90).stdout


MENU = {"type": "menu", "trigger": {"kind": "button", "label": "Actions"},
        "items": [{"type": "link", "label": "Open", "url": "#a"}, {"type": "link", "label": "Rename", "url": "#b"}, {"type": "link", "label": "Delete", "url": "#c"}]}


@browser
def test_menu_arrow_keys_home_end_and_escape(core_js):
    html = _gas_batch(core_js, [MENU])[0]
    js = ("function key(el,k){el.dispatchEvent(new KeyboardEvent('keydown',{key:k,bubbles:true,cancelable:true}));}"
          "var s=document.querySelector('summary'),d=document.querySelector('details'),o=[];"
          "s.focus();key(s,'ArrowDown');o.push(d.open,document.activeElement.textContent);"
          "key(document.activeElement,'ArrowDown');o.push(document.activeElement.textContent);"
          "key(document.activeElement,'End');o.push(document.activeElement.textContent);"
          "key(document.activeElement,'ArrowDown');o.push(document.activeElement.textContent);"
          "key(document.activeElement,'ArrowUp');o.push(document.activeElement.textContent);"
          "key(document.activeElement,'Home');o.push(document.activeElement.textContent);"
          "key(document.activeElement,'Escape');o.push(d.open,document.activeElement===s);"
          "document.documentElement.setAttribute('data-o',JSON.stringify(o));")
    out = _in_browser(html, js)
    m = re.search(r"data-o='([^']*)'|data-o=\"([^\"]*)\"", out)
    assert m, out[:300]
    import html as _h
    got = json.loads(_h.unescape(m.group(1) or m.group(2)))
    assert got == [True, "Open", "Rename", "Delete", "Open", "Delete", "Open", False, True], got


def test_a_payload_cannot_use_the_fixer_to_break_out_of_an_attribute(core_js):
    """Regression (2026-10-10, caught by a2ui-private/security/xss-fuzz): '<svg' inside a quoted title is data; the fixer once wrote attributes there."""
    from html.parser import HTMLParser

    class Tags(HTMLParser):
        def __init__(self):
            super().__init__()
            self.tags = []

        def handle_starttag(self, tag, attrs):
            self.tags.append(tag)

    evil = '"><img src=x onerror=alert(1)>\'"><svg onload=alert(1)></script><script>alert(4)</script> onclick=x <input type=radio style=display:none>'
    h = _gas_batch(core_js, [{"type": "glossary_inline", "term": "API", "definition": evil}])[0]
    p = Tags()
    p.feed(h)
    assert not {"svg", "img", "script", "input"} & set(p.tags), (p.tags, h)
