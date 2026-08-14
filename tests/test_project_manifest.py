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
    """known_debt.unregistered_atoms has two independent legitimate members
    (check_core.py's own docstring: "declared-exception pattern... one
    list, not two"): (a) atoms with a GAS .gs renderer registration but
    missing from schema.yaml (this test's original purpose — catch stale
    GAS-drift debt entries), and (b) atoms with NO GAS surface at all
    (e.g. google-chat-chromium-render-only, visibility:private) that
    check_core.py's atom-packs.yaml coverage check needs declared as
    schema-absent for an unrelated reason. Only (a) is this test's
    business — an entry that was never GAS-registered to begin with isn't
    "stale GAS debt," it's simply outside this check's domain, so it's
    excluded from the stale_debt computation rather than flagged."""
    renderer_atoms = set()
    for f in glob.glob(str(ROOT / "apps-script-surface/gas-wired-renderer/*.gs")):
        renderer_atoms |= set(re.findall(r"_RENDERERS\['([a-z_0-9]+)'\]",
                                         Path(f).read_text()))
    schema_types = {b["type"] for b in
                    yaml.safe_load((ROOT / "atoms/schema.yaml").read_text())["blocks"]}
    actual_missing = renderer_atoms - schema_types
    declared = set(MANIFEST["known_debt"]["unregistered_atoms"])

    undeclared_drift = sorted(actual_missing - declared)
    stale_debt = sorted((declared & renderer_atoms) - actual_missing)
    assert not undeclared_drift, (
        "renderer atoms missing from schema and NOT declared as debt "
        f"(add to project.yaml known_debt or register them): {undeclared_drift}")
    assert not stale_debt, (
        "declared debt entries that ARE GAS-registered and are now also "
        f"in schema.yaml — remove from project.yaml known_debt: {stale_debt}")


# ─── One engine, one compiler, and no unsigned mirrors ───────────────────────

MAINTAINED_ENGINE = "apps-script-surface/gas-wired-renderer/A2UIState.html"
COMPILED_ENGINE = "public/surfaces/mcp-apps/renderer-bundle.html"


def test_no_undeclared_renderer_engine_copies():
    """Every file carrying the output-wire dispatch is accounted for.

    Declared 2026-08-14. form_radio_group's binding was fixed in the one
    maintained engine and compiled into the one generated target — and the
    honest question "is it fixed catalogue-wide?" turned out to need a list,
    because two further hand-copies of the same dispatch have been sitting
    frozen since the 2026-07-05 import.

    The risk this guards is not those two. It is the FIFTH copy: every
    additional mirror is a hand-sync that no process owns, and the repo has
    already been bitten by that shape twice (MCP_VERBS, training_parser). A new
    one must be a deliberate, declared act.
    """
    # TRACKED files only, deliberately. public-full/ is a gitignored local
    # build of the gated full mirror and is present or absent depending on
    # whether anyone has run catalog-rebuild-full lately — scanning it would
    # make this gate pass in CI and fail on a developer's machine for a reason
    # that is not drift. It is a compiled target of that process, and stale
    # until it next runs, exactly like the bundle is until renderer-release.
    tracked = subprocess.run(
        ["git", "ls-files", "*.html", "*.js", "*.gs"],
        cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    dispatch = sorted(
        rel for rel in tracked
        if "node_modules" not in rel
        and "prop === 'onChange'" in (ROOT / rel).read_text(errors="ignore")
    )
    accounted = ({MAINTAINED_ENGINE, COMPILED_ENGINE}
                 | set(MANIFEST["known_debt"]["frozen_renderer_copies"]))
    undeclared = sorted(set(dispatch) - accounted)
    assert not undeclared, (
        "new copies of the wired output-wire dispatch, owned by no generator "
        "and declared nowhere — each is a hand-sync waiting to drift. Compile "
        "it from the engine, or declare it in project.yaml "
        f"known_debt.frozen_renderer_copies: {undeclared}")

    gone = sorted(accounted - set(dispatch) - {COMPILED_ENGINE})
    assert not gone, (
        "declared frozen renderer copies that no longer carry the dispatch — "
        f"delete the entry from project.yaml known_debt: {gone}")


def test_the_frozen_copies_really_are_frozen():
    """The claim the entry above rests on, checked rather than asserted.

    If someone starts maintaining one of these again, the debt entry becomes a
    lie in the direction that matters — it would tell a reader "already dead,
    ignore it" about a file that is live. Cheapest true signal: the renderer
    changes that landed after the import are absent.
    """
    since_import = ("same_tab", "sortable_list")
    for rel in MANIFEST["known_debt"]["frozen_renderer_copies"]:
        engine = (ROOT / rel).read_text()
        sibling = (ROOT / rel).parent / "atom.gs"
        body = engine + (sibling.read_text() if sibling.exists() else "")
        present = [m for m in since_import if m in body]
        assert not present, (
            f"{rel} has picked up post-import renderer work {present} — it is "
            "being maintained after all, so it is not frozen debt. Either "
            "bring it fully in sync (and give it a generator) or remove the "
            "declaration.")
