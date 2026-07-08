"""Schema integrity tests — every atom must be correctly tagged."""

import json
from pathlib import Path

import pytest
from conftest import SURFACES

MODEL_VERIFICATION_FIXTURES_DIR = Path(__file__).parent / "fixtures" / "model_verification"
EMIT_DEPLOYMENT_SCRIPT = Path(__file__).parent.parent / "scripts" / "emit_deployment.py"


def test_all_atoms_have_type(atoms):
    for name, atom in atoms.items():
        assert "type" in atom, f"{name}: missing 'type'"


def test_all_atoms_have_description(atoms):
    for name, atom in atoms.items():
        assert atom.get("description"), f"{name}: missing 'description'"


def test_all_atoms_have_surfaces(atoms):
    for name, atom in atoms.items():
        assert "surfaces" in atom, f"{name}: missing 'surfaces' — every atom must declare surface compatibility"


def test_all_atoms_have_works_on(atoms):
    for name, atom in atoms.items():
        surfaces = atom.get("surfaces", {})
        assert "works_on" in surfaces, f"{name}: missing 'works_on' in surfaces"
        assert isinstance(surfaces["works_on"], list), f"{name}: 'works_on' must be a list"
        assert len(surfaces["works_on"]) > 0, f"{name}: 'works_on' must not be empty"


def test_works_on_uses_known_surfaces(atoms):
    for name, atom in atoms.items():
        works_on = atom.get("surfaces", {}).get("works_on", [])
        for surface in works_on:
            assert surface in SURFACES, f"{name}: unknown surface '{surface}' in works_on"


def test_incompatible_has_reason(atoms):
    for name, atom in atoms.items():
        for entry in atom.get("surfaces", {}).get("incompatible_on", []):
            assert "reason" in entry, f"{name}: incompatible_on entry missing 'reason'"
            assert "surface" in entry, f"{name}: incompatible_on entry missing 'surface'"


def test_degraded_has_note(atoms):
    for name, atom in atoms.items():
        for entry in atom.get("surfaces", {}).get("degraded_on", []) or []:
            assert "note" in entry, f"{name}: degraded_on entry missing 'note'"
            assert "surface" in entry, f"{name}: degraded_on entry missing 'surface'"


# ── model_compatibility (spec/model-compatibility-v0.1.md) — Tier 1: structural only, no network ──

def test_model_compatibility_degraded_support_shape(atoms):
    """Every degraded_support entry must declare which models it covers and the
    exact compensating procedure — not just a claim that degradation exists."""
    for name, atom in atoms.items():
        for entry in atom.get("model_compatibility", {}).get("degraded_support", []) or []:
            assert entry.get("models"), f"{name}: degraded_support entry missing 'models' list"
            assert isinstance(entry["models"], list), f"{name}: degraded_support 'models' must be a list"
            assert entry.get("compensation_prose"), \
                f"{name}: degraded_support entry for {entry.get('models')} missing 'compensation_prose'"
            assert entry.get("compensation_strategy"), \
                f"{name}: degraded_support entry for {entry.get('models')} missing 'compensation_strategy'"


def test_model_compatibility_verified_requires_fixture(atoms):
    """verified:true is a claim that a live model call actually passed — it must
    point at a recorded Tier 2 fixture, not just be hand-asserted. A claim that
    outruns its evidence is exactly the failure mode this test exists to catch
    (see a2uithoughts.md 2026-07-08: the '44 atoms on Chat' claim that wasn't)."""
    for name, atom in atoms.items():
        for entry in atom.get("model_compatibility", {}).get("degraded_support", []) or []:
            if not entry.get("verified"):
                continue
            fixture_name = entry.get("verification_fixture")
            assert fixture_name, \
                f"{name}: verified:true requires 'verification_fixture' filename"
            fixture_path = MODEL_VERIFICATION_FIXTURES_DIR / fixture_name
            assert fixture_path.exists(), \
                f"{name}: verification_fixture '{fixture_name}' not found under {MODEL_VERIFICATION_FIXTURES_DIR}"
            data = json.loads(fixture_path.read_text())
            assert data.get("passed") is True, \
                f"{name}: fixture '{fixture_name}' does not record passed:true — verified:true is stale or wrong"
            tested = set(data.get("models_tested", []))
            claimed = set(entry["models"])
            missing = claimed - tested
            assert not missing, \
                f"{name}: fixture '{fixture_name}' doesn't cover model(s) {missing} claimed in 'models'"


def test_no_overlap_works_and_incompatible(atoms):
    """An atom cannot be both works_on and incompatible_on the same surface."""
    for name, atom in atoms.items():
        works = set(atom.get("surfaces", {}).get("works_on", []))
        incompatible = {e["surface"] for e in atom.get("surfaces", {}).get("incompatible_on", [])}
        overlap = works & incompatible
        assert not overlap, f"{name}: surface(s) {overlap} appear in both works_on and incompatible_on"


def test_atom_count(atoms):
    """Sanity check — catalogue should have at least 20 atoms."""
    assert len(atoms) >= 20, f"Only {len(atoms)} atoms found — expected at least 20"


def test_googlechat_renderer_covers_works_on(atoms):
    """Every atom tagged works_on: googlechat must have a renderer in googlechat.py."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from renderers.googlechat import RENDERERS as chat_renderers
    for name, atom in atoms.items():
        if 'google-chat' in atom['surfaces'].get('works_on', []):
            assert name in chat_renderers, f"{name}: works_on googlechat but missing from renderers/googlechat.py"


def test_web_renderer_covers_works_on(atoms):
    """Every atom tagged works_on: web must have a renderer in web_article.py."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from renderers.web_article import _RENDERERS as web_renderers
    for name, atom in atoms.items():
        if 'web' in atom['surfaces'].get('works_on', []):
            assert name in web_renderers, f"{name}: works_on web but missing from renderers/web_article.py"


def test_all_atoms_have_source(atoms):
    """Every atom must declare its origin for supply chain transparency."""
    for name, atom in atoms.items():
        assert "source" in atom, f"{name}: missing 'source' — every atom must credit its origin"
        src = atom["source"]
        assert src.get("name"), f"{name}: source missing 'name'"
        assert src.get("url"), f"{name}: source missing 'url'"
        assert src.get("license"), f"{name}: source missing 'license'"


# ── processing (spec/atom-processing-contract-v0.1.md, Tracks B/C) — Tier 1: structural only ──
#
# Tier 2 (live) is explicitly NOT implemented here — same posture as model_compatibility's
# verified:true fixtures. These are the structural checks the spec calls for: shape validation
# plus the regression test that would have caught the 2026-07-08 SCOPE_ATOMS drift before it
# became real (emit_deployment.py's own hardcoded dict silently diverging from schema.yaml).

PAGINATION_VALUES = {"independent", "hub_aggregating", "atomic"}


def test_processing_pagination_is_valid_enum(atoms):
    """processing.pagination, when present, must be one of the three declared values —
    a typo here would silently fall back to 'independent' (the default) and re-open the
    exact module_map splitting incident this field exists to prevent."""
    for name, atom in atoms.items():
        pagination = (atom.get("processing") or {}).get("pagination")
        if pagination is None:
            continue
        assert pagination in PAGINATION_VALUES, (
            f"{name}: processing.pagination '{pagination}' is not one of {sorted(PAGINATION_VALUES)}"
        )


def test_processing_required_scope_matches_emit_deployment():
    """module_map is the ONLY atom in the catalogue with independently-sized nested content
    (modules[].page — an array of atom blocks auto-encoded into its own URL); it must declare
    hub_aggregating so generic splitters refuse to flatten it instead of silently mishandling it."""
    import yaml
    schema = yaml.safe_load(open(Path(__file__).parent.parent / "atoms" / "schema.yaml"))
    hub_aggregating = [b["type"] for b in schema["blocks"]
                        if isinstance(b, dict) and (b.get("processing") or {}).get("pagination") == "hub_aggregating"]
    assert "module_map" in hub_aggregating, \
        "module_map lost its processing.pagination: hub_aggregating declaration"


def test_processing_required_scope_is_string_or_list_of_strings(atoms):
    """processing.required_scope, when present, must be a string or a list of strings —
    the shape emit_deployment.py and the MCP-side consumers both expect to fold into an
    OAuth scopes array."""
    for name, atom in atoms.items():
        required = (atom.get("processing") or {}).get("required_scope")
        if required is None:
            continue
        if isinstance(required, str):
            continue
        assert isinstance(required, list), \
            f"{name}: processing.required_scope must be a string or list, got {type(required).__name__}"
        assert required, f"{name}: processing.required_scope is an empty list"
        assert all(isinstance(s, str) for s in required), \
            f"{name}: processing.required_scope list must contain only strings"


@pytest.mark.skipif(not EMIT_DEPLOYMENT_SCRIPT.exists(),
                    reason="scripts/emit_deployment.py not present (private/local-only tier)")
def test_emit_deployment_scope_atoms_derived_from_schema(atoms):
    """Regression test for the 2026-07-08 drift incident: emit_deployment.py's SCOPE_ATOMS
    used to be its own hand-maintained dict, independently duplicated from schema.yaml (and
    from two MCP-side copies). It's now DERIVED from atoms/schema.yaml's processing.required_scope
    declarations — this proves the derivation actually reconstructs the same atom -> scope
    mapping the schema declares, atom-by-atom, so a future edit to one without the other fails
    here instead of shipping a silently wrong appsscript.json manifest."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("emit_deployment", EMIT_DEPLOYMENT_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    S = "https://www.googleapis.com/auth/"
    expected = {}
    for name, atom in atoms.items():
        required = (atom.get("processing") or {}).get("required_scope")
        if not required:
            continue
        scopes = [required] if isinstance(required, str) else list(required)
        for sc in scopes:
            full = sc if sc.startswith("http") else S + sc
            expected.setdefault(full, set()).add(name)

    assert mod.SCOPE_ATOMS == expected, (
        "emit_deployment.py's derived SCOPE_ATOMS no longer matches atoms/schema.yaml's "
        "processing.required_scope declarations — this is the exact drift the "
        "atom-processing-contract spec exists to prevent"
    )
