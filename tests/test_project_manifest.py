"""project.yaml is enforced, not advisory.

Three audits, per the manifest's own contract:
1. private globs must have zero tracked files in git
2. every file in public/ must trace to a published rule (or published_prompts)
3. renderer atoms missing from the schema must exactly equal the declared
   debt list — undeclared drift fails, and so does stale debt (an entry
   that got fixed but not removed)
"""

import fnmatch
import glob
import re
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
MANIFEST = yaml.safe_load((ROOT / "project.yaml").read_text())


def _matches(path, pattern):
    if pattern.endswith("/**"):
        return path.startswith(pattern[:-2])
    return fnmatch.fnmatch(path, pattern)


def _tracked_files():
    out = subprocess.run(["git", "ls-files"], cwd=ROOT,
                         capture_output=True, text=True)
    return out.stdout.splitlines()


def test_private_globs_are_untracked():
    tracked = _tracked_files()
    violations = []
    for pattern in MANIFEST["policy"]["private"]:
        for f in tracked:
            if _matches(f, pattern) or fnmatch.fnmatch(f, pattern):
                violations.append(f"{f} (matches private '{pattern}')")
    assert not violations, "private-tier files are tracked in git:\n" + "\n".join(violations)


def test_public_dir_fully_declared():
    rules = MANIFEST["policy"]["published"]
    prompts = set(MANIFEST["published_prompts"])
    undeclared = []
    for f in sorted((ROOT / "public").rglob("*")):
        if not f.is_file():
            continue
        rel = str(f.relative_to(ROOT))
        if rel.startswith("public/prompts/"):
            if f.name not in prompts:
                undeclared.append(f"{rel} (not in published_prompts)")
            continue
        if not any(_matches(rel, p) for p in rules):
            undeclared.append(rel)
    assert not undeclared, (
        "public/ contains files with no publication declaration in project.yaml:\n"
        + "\n".join(undeclared))


def test_unregistered_atoms_match_declared_debt():
    renderer_atoms = set()
    for f in glob.glob(str(ROOT / "apps-script-surface/gas-wired-renderer/*.gs")):
        renderer_atoms |= set(re.findall(r"_RENDERERS\['([a-z_0-9]+)'\]",
                                         Path(f).read_text()))
    schema_types = {b["type"] for b in
                    yaml.safe_load((ROOT / "atoms/schema.yaml").read_text())["blocks"]}
    actual_missing = renderer_atoms - schema_types
    declared = set(MANIFEST["known_debt"]["unregistered_atoms"])

    undeclared_drift = sorted(actual_missing - declared)
    stale_debt = sorted(declared - actual_missing)
    assert not undeclared_drift, (
        "renderer atoms missing from schema and NOT declared as debt "
        f"(add to project.yaml known_debt or register them): {undeclared_drift}")
    assert not stale_debt, (
        "declared debt entries that are now registered — remove from "
        f"project.yaml known_debt: {stale_debt}")
