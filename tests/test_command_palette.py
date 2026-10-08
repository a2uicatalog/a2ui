"""command_palette: the documented field is `text`, and both renderers must read it.

Found 2026-10-08 while planning an extension: schema.yaml says commands are {text, shortcut},
but the GAS renderer read `cmd.name`, so a payload written to the schema drew blank command
names on GAS, MCP Apps and Android; and the Python renderer was a hardcoded stub that drew
"Command 1 / Command 2" for every payload. Both now read the payload. `name` keeps working,
`group` is an alias of `category`, and `icon` / `id` are accepted.
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

CASES = {
    "documented": {"type": "command_palette", "commands": [
        {"text": "New post", "shortcut": "⌘N"}, {"text": "New video"}]},
    "legacy_name": {"type": "command_palette", "commands": [
        {"name": "Old style", "category": "Nav", "description": "kept working"}]},
    "grouped": {"type": "command_palette", "placeholder": "Find…", "commands": [
        {"text": "Edit", "group": "Create", "icon": "✎", "id": "edit"},
        {"text": "Home", "group": "Navigate"}, {"text": "Share", "group": "Create"}]},
    "empty": {"type": "command_palette"},
    "junk": {"type": "command_palette", "commands": [None, 5, "x", {"text": ""}]},
    "hostile": {"type": "command_palette", "placeholder": "\"><img src=x onerror=alert(1)>", "commands": [
        {"text": "<script>alert(1)</script>", "group": "'><b>g", "icon": "<img src=x>", "id": "a\" onmouseover=\"x",
         "shortcut": "</kbd><i>", "description": "</span><script>1</script>"}]},
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
    return {k: _RENDERERS["command_palette"](v) for k, v in CASES.items()}


def _norm(h):
    h = re.sub(r"<style>.*?</style>", "", h, flags=re.S)       # Python inlines the class CSS; GAS ships it globally
    return re.sub(r"cp-[A-Za-z0-9]+", "cp-X", h)


@pytest.fixture(params=["gas", "py"])
def html(request, gas, py):
    return (lambda n: gas[n]) if request.param == "gas" else (lambda n: py[n])


@pytest.mark.parametrize("name", list(CASES))
def test_gas_and_python_agree(name, gas, py):
    assert _norm(py[name]) in _norm(gas[name]), name


def test_documented_text_field_is_drawn(html):
    h = html("documented")
    assert ">New post<" in h and ">New video<" in h and "⌘N" in h
    assert "Command 1" not in h


def test_legacy_name_and_category_still_work(html):
    h = html("legacy_name")
    assert ">Old style<" in h and ">Nav<" in h and "kept working" in h


def test_group_icon_and_id(html):
    h = html("grouped")
    assert h.index(">Create<") < h.index(">Navigate<")
    assert h.count('class="a2ui-cmd-cat"') == 2             # Edit and Share share one Create heading
    assert 'data-id="edit"' in h and "✎" in h and 'placeholder="Find…"' in h


def test_empty_and_junk_render_without_error(html):
    assert "a2ui-cmd-palette" in html("empty") and "a2ui-cmd-palette" in html("junk")


def test_hostile_values_do_not_become_markup(html):
    h = html("hostile")
    body = h.split('<div class="a2ui-cmd-list">', 1)[1]
    for bad in ("<script>", "<img", "<b>", "<i>", "onmouseover=\"x"):
        assert bad not in body, bad
    assert 'placeholder="&quot;&gt;&lt;img' in h
