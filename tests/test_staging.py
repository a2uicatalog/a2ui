"""Staging policy: stage: preview atoms are repo-only — they must not
appear in any published artifact. CI/CD drinks from the stage field.

visibility: private is a SEPARATE axis from stage (maturity vs. access —
see gemini-enterprise-agent/RETRO.md §20/a2uithoughts.md for why they must
not be conflated): a private atom stays out of the PUBLIC build regardless
of stage, including once promoted to stable. It's only ever generated into
the gated full-catalogue build (A2UI_CATALOG_FULL=1), never public/."""

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
BLOCKS = yaml.safe_load((ROOT / "atoms/schema.yaml").read_text())["blocks"]
PREVIEW = {b["type"] for b in BLOCKS if b.get("stage", "stable") == "preview"}
STABLE = {b["type"] for b in BLOCKS if b.get("stage", "stable") == "stable"}
PRIVATE = {b["type"] for b in BLOCKS if b.get("visibility") == "private"}
NOT_PUBLIC = PREVIEW | PRIVATE
PUBLIC = STABLE - PRIVATE


def test_stage_values_are_known():
    bad = [b["type"] for b in BLOCKS if b.get("stage", "stable") not in ("stable", "preview")]
    assert not bad, f"unknown stage values on: {bad}"


def test_visibility_values_are_known():
    bad = [b["type"] for b in BLOCKS if b.get("visibility") not in (None, "private")]
    assert not bad, f"unknown visibility values on: {bad}"


def test_spec_json_is_stable_only():
    spec = json.loads((ROOT / "public/spec.json").read_text())
    published = {a["type"] for a in spec["atoms"]}
    leaked = sorted(published & NOT_PUBLIC)
    assert not leaked, f"preview/private atoms leaked into public spec.json: {leaked}"
    assert published == PUBLIC, "spec.json out of sync with public set — regenerate"


def test_compact_index_is_stable_only():
    idx = json.loads((ROOT / "public/atoms/index.json").read_text())
    published = {a["type"] for a in idx["atoms"]}
    assert not (published & NOT_PUBLIC), f"preview/private atoms in compact index: {sorted(published & NOT_PUBLIC)}"


def test_ard_catalog_is_stable_only():
    ard = (ROOT / "public/.well-known/ai-catalog.json").read_text()
    leaked = sorted(t for t in NOT_PUBLIC if f":atom:{t}\"" in ard or f"/atoms/{t}\"" in ard)
    assert not leaked, f"preview/private atoms in ai-catalog.json: {leaked}"


def test_no_preview_atom_pages_published():
    leaked = sorted(t for t in NOT_PUBLIC if (ROOT / "public/atoms" / t).exists())
    assert not leaked, f"preview/private atom pages exist in public/: {leaked}"


def test_builder_prompts_advertise_stable_only():
    for name in ("a2ui-builder-gem.md", "a2ui-builder-gem-offline.md"):
        text = (ROOT / "prompts" / name).read_text()
        leaked = sorted(t for t in NOT_PUBLIC if re.search(rf"^- `{t}` —", text, re.M)
                        or re.search(rf"^#### {t}$", text, re.M))
        assert not leaked, f"preview/private atoms in {name}: {leaked}"


def test_catalog_index_references_resolve_and_are_stable_only():
    """The selection menu must never advertise what publication refuses to
    write: every catalogId in index.json has its catalog file on disk, and no
    preview atom appears in any index entry. Found live 2026-07-10: the first
    preview-only catalog (a2ui-competition-v1) produced a dangling catalogId
    and a base atomCount one higher than the published base catalog file."""
    idx = json.loads((ROOT / "public/catalogue/index.json").read_text())
    # PRE-EXISTING drift, declared not hidden: the 12 extension catalogIds have
    # never had published files (only the base + state catalogs exist on disk).
    # Known debt — any NEW dangling ref beyond these fails. Shrink this set as
    # per-pack publication lands; never grow it.
    KNOWN_UNPUBLISHED = {
        "a2ui-aviation-v1", "a2ui-charts-v1", "a2ui-display-v1", "a2ui-editorial-v1",
        "a2ui-effects-v1", "a2ui-embeds-v1", "a2ui-google-workspace-live-v1",
        "a2ui-learning-v1", "a2ui-marketing-v1", "a2ui-meta-v1", "a2ui-ops-v1",
        "a2ui-presentation-v1",
    }
    for cat in idx["catalogs"]:
        fname = cat["catalogId"].rsplit("/", 1)[-1]
        f = ROOT / "public/catalogue" / fname
        if not f.exists():
            assert cat["slug"] in KNOWN_UNPUBLISHED, \
                f"index advertises {fname} but the file is not published (new dangling ref)"
            continue
        leaked = sorted(a["type"] for a in cat["atoms"] if a["type"] in NOT_PUBLIC)
        assert not leaked, f"preview/private atoms in index catalog {cat['slug']}: {leaked}"
        published = json.loads(f.read_text())
        comps = published.get("components") or {}
        missing = sorted(a["type"] for a in cat["atoms"] if a["type"] not in comps)
        assert not missing, (
            f"{cat['slug']}: index advertises atoms absent from {fname}: {missing[:6]}")
