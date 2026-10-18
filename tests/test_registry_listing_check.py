"""The Smithery drift check's comparison logic (no network): it must catch the exact drift that happened (stale count,
stale tool list, default name) and pass the intended listing."""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("check_registry_listings", Path(__file__).resolve().parent.parent / "scripts" / "check_registry_listings.py")
crl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crl)

GOOD = {
    "displayName": "A2UI Atomic Catalog: generative UI for AI agents",
    "description": "Real rendered UI. The A2UI Atomic Catalog is a free MCP server of 500+ typed UI components. No signup, no API key.",
    "tools": [{}] * 40,
}


def test_intended_listing_is_in_step():
    assert crl.compare(GOOD, 40) == []


def test_catches_the_drift_that_actually_happened():
    stale = {**GOOD, "displayName": "a2uicatalog", "tools": [{}] * 15,
             "description": "A2UI Atomic Catalog. MCP server of 474 typed UI components. No signup."}
    problems = crl.compare(stale, 40)
    assert any("display name" in p for p in problems)
    assert any("474" in p for p in problems)
    assert any("15 tools" in p and "40" in p for p in problems)


def test_a_vanished_phrase_is_reported():
    assert any("MCP server" in p for p in crl.compare({**GOOD, "description": "A2UI Atomic Catalog. No signup."}, 40))
