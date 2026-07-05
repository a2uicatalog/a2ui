"""Staging policy: stage: preview atoms are repo-only — they must not
appear in any published artifact. CI/CD drinks from the stage field."""

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
BLOCKS = yaml.safe_load((ROOT / "atoms/schema.yaml").read_text())["blocks"]
PREVIEW = {b["type"] for b in BLOCKS if b.get("stage", "stable") == "preview"}
STABLE = {b["type"] for b in BLOCKS if b.get("stage", "stable") == "stable"}


def test_stage_values_are_known():
    bad = [b["type"] for b in BLOCKS if b.get("stage", "stable") not in ("stable", "preview")]
    assert not bad, f"unknown stage values on: {bad}"


def test_spec_json_is_stable_only():
    spec = json.loads((ROOT / "public/spec.json").read_text())
    published = {a["type"] for a in spec["atoms"]}
    leaked = sorted(published & PREVIEW)
    assert not leaked, f"preview atoms leaked into public spec.json: {leaked}"
    assert published == STABLE, "spec.json out of sync with stable set — regenerate"


def test_compact_index_is_stable_only():
    idx = json.loads((ROOT / "public/atoms/index.json").read_text())
    published = {a["type"] for a in idx["atoms"]}
    assert not (published & PREVIEW), f"preview atoms in compact index: {sorted(published & PREVIEW)}"


def test_ard_catalog_is_stable_only():
    ard = (ROOT / "public/.well-known/ai-catalog.json").read_text()
    leaked = sorted(t for t in PREVIEW if f":atom:{t}\"" in ard or f"/atoms/{t}\"" in ard)
    assert not leaked, f"preview atoms in ai-catalog.json: {leaked}"


def test_no_preview_atom_pages_published():
    leaked = sorted(t for t in PREVIEW if (ROOT / "public/atoms" / t).exists())
    assert not leaked, f"preview atom pages exist in public/: {leaked}"


def test_builder_prompts_advertise_stable_only():
    for name in ("a2ui-builder-gem.md", "a2ui-builder-gem-offline.md"):
        text = (ROOT / "prompts" / name).read_text()
        leaked = sorted(t for t in PREVIEW if re.search(rf"^- `{t}` —", text, re.M)
                        or re.search(rf"^#### {t}$", text, re.M))
        assert not leaked, f"preview atoms in {name}: {leaked}"
