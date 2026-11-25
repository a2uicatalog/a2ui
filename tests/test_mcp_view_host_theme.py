"""MCP Apps view theme follows the host (2026-11-25, Antigravity painted a white card in a dark window).

Rule: an explicit payload.theme (light|dark|terminal) always wins; with none, hostContext.theme
('dark'|'light', from ui/initialize and ui/notifications/host-context-changed) decides; with neither the
view is light, exactly as before. Both boots (MCP Apps handshake and plain-HTTP) share ONE helper in PRELUDE.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import gen_mcp_apps_bundle as bundle  # noqa: E402

NODE = shutil.which("node")


def _run_helper(payload, host):
    """Run the real PRELUDE helper against a stub DOM; return effective theme, classes, colorScheme, html bg."""
    js = bundle.PRELUDE + """
var cls = {};
var document = {
  body: { classList: { toggle: function (c, on) { cls[c] = !!on; } } },
  documentElement: { style: {} }
};
var getComputedStyle = function () { return { getPropertyValue: function () { return ' #1c1c1e '; } }; };
var t = _a2uiApplyTheme(%s, %s);
console.log(JSON.stringify({ t: t, cls: cls, cs: document.documentElement.style.colorScheme,
  bg: document.documentElement.style.backgroundColor }));
""" % (json.dumps(payload), json.dumps(host))
    out = subprocess.run([NODE, "-e", js], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def test_both_boots_share_one_helper_and_no_inline_theme_logic_remains():
    assert "function _a2uiApplyTheme(" in bundle.PRELUDE
    assert "_a2uiApplyTheme(payload, _hostContext)" in bundle.HANDSHAKE
    assert "_a2uiApplyTheme(payload, null)" in bundle.HTTP_BOOT
    for block in (bundle.HANDSHAKE, bundle.HTTP_BOOT):
        assert "classList.toggle('asw-dark-theme'" not in block


def test_host_context_changed_with_theme_repaints_the_last_payload():
    js = bundle.HANDSHAKE
    assert "patch.hasOwnProperty('theme') && _lastPayload" in js
    assert "paint(_lastPayload)" in js


@pytest.mark.skipif(not NODE, reason="node not installed")
@pytest.mark.parametrize("payload,host,theme,dark,terminal", [
    ({}, {"theme": "dark"}, "dark", True, False),                 # follow host dark
    ({}, {"theme": "light"}, "light", False, False),
    ({}, {}, "light", False, False),                              # no host theme: as before
    ({}, None, "light", False, False),
    ({"theme": "light"}, {"theme": "dark"}, "light", False, False),   # explicit payload wins
    ({"theme": "dark"}, {"theme": "light"}, "dark", True, False),
    ({"theme": "terminal"}, {"theme": "light"}, "terminal", True, True),
    ({}, {"theme": "sepia"}, "light", False, False),              # unknown host value ignored
    ({"theme": "bogus"}, {"theme": "dark"}, "dark", True, False), # unknown payload value does not pin light
])
def test_effective_theme_rule(payload, host, theme, dark, terminal):
    r = _run_helper(payload, host)
    assert r["t"] == theme
    assert r["cls"] == {"asw-dark-theme": dark, "asw-terminal-theme": terminal}
    assert r["cs"] == ("dark" if dark else "light")
    assert r["bg"] == ("#1c1c1e" if dark else "")


def test_sequence_diagram_follows_dark_host_page_when_block_has_no_theme():
    src = (ROOT / "apps-script-surface" / "gas-wired-renderer" / "atoms_charts.gs").read_text()
    i = src.index("_RENDERERS['sequence_diagram']")
    assert "if (!theme && typeof document !== 'undefined'" in src[i:i + 1500]
    assert "theme = 'site'" in src[i:i + 1500]
