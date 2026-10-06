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


def _scalar_fields():
    import importlib.util
    spec = importlib.util.spec_from_file_location("gen_android_assets", ROOT / "android" / "tools" / "gen_android_assets.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.scalar_fields


def test_picker_unwrap_only_touches_single_string_fields(atoms):
    """The bridge turns a ChoicePicker's ["grid"] into "grid" for the fields atoms.json lists as
    scalars (2026-10-06 studio spike: a bound backdrop picker silently did nothing). A list field
    must never be listed, or a one-entry list (one block, one item) would be flattened."""
    scalar_fields = _scalar_fields()
    film = scalar_fields(atoms["motion_timeline"]["fields"])
    assert {"backdrop", "theme", "accent", "aspect"} <= set(film)
    assert not {"blocks", "tracks", "scenes", "ease"} & set(film)
    wrong = sorted(f"{t}.{f}" for t, a in atoms.items() if isinstance(a.get("fields"), dict)
                   for f in scalar_fields(a["fields"]) if str(a["fields"][f]).lstrip().startswith(("array", "[", "{", "list")))
    assert not wrong, f"list or object fields classed as single strings: {wrong}"
