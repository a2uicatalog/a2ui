"""The android surface: works_on: android must be exactly the atoms the Android library
(android/a2ui-atoms) can draw.

The library draws every atom through a WebView running the MCP Apps renderer bundle,
so an atom works on android if and only if it works on mcp-apps AND the bundle has a
renderer for it. A whole-catalogue sweep at phone width (2026-10-04) found 12 preview
atoms tagged mcp-apps with no renderer in the bundle (Python twin only); tagged android
they would register on Android and draw a blank, so they are not tagged android.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUNDLE = ROOT / "public" / "surfaces" / "mcp-apps" / "renderer-bundle.html"


def _bundle_renderers():
    src = BUNDLE.read_text()
    return (set(re.findall(r"_RENDERERS\[['\"]([a-z0-9_]+)['\"]\]\s*=", src))
            | set(re.findall(r"_RENDERERS\.([a-z0-9_]+)\s*=", src)))


def _works_on(atom):
    return (atom.get("surfaces") or {}).get("works_on") or []


def test_every_android_atom_has_a_renderer_in_the_bundle(atoms):
    have = _bundle_renderers()
    missing = sorted(t for t, a in atoms.items() if "android" in _works_on(a) and t not in have)
    assert not missing, f"tagged android but the bundle cannot draw them (blank on a device): {missing}"


def test_every_drawable_mcp_apps_atom_is_tagged_android(atoms):
    have = _bundle_renderers()
    untagged = sorted(t for t, a in atoms.items()
                      if "mcp-apps" in _works_on(a) and t in have and "android" not in _works_on(a))
    assert not untagged, f"work on mcp-apps with a bundle renderer, so the Android library draws them: {untagged}"


def test_every_mcp_apps_atom_has_a_renderer_in_the_bundle(atoms):
    """mcp-apps hosts draw with the same bundle (and the Worker's renderers are built
    from the same GAS sources), so an atom tagged mcp-apps without a bundle renderer
    draws nothing there either. The 2026-10-04 sweep found 12 preview atoms in that
    state (Python twin only); their mcp-apps tag was removed."""
    have = _bundle_renderers()
    missing = sorted(t for t, a in atoms.items() if "mcp-apps" in _works_on(a) and t not in have)
    assert not missing, f"tagged mcp-apps but the bundle cannot draw them: {missing}"
