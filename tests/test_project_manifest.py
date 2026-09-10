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
import tomllib
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
MANIFEST = yaml.safe_load((ROOT / "project.yaml").read_text())


def _matches(path, pattern):
    if pattern.endswith("/**"):
        return path.startswith(pattern[:-2])
    return fnmatch.fnmatch(path, pattern)


# Only things that could appear on disk AFTER a checkout that a plain walk
# wouldn't already correctly exclude -- see _tracked_files()'s own
# docstring for why the checkout's origin already handles everything else.
_RUNTIME_ARTIFACT_DIRS = {"__pycache__", ".pytest_cache", ".git"}
_RUNTIME_ARTIFACT_SUFFIXES = (".pyc", ".pyo")


def _tracked_files():
    """Files git considers part of the repo. Falls back to a plain
    filesystem walk when there's no `.git` at all -- this repo is
    sometimes checked out from a tarball/archive export rather than a git
    clone (confirmed live 2026-08-20: curtiskrygier/repo-improvement-
    agent's own daily gap-finding agent does exactly this, deliberately,
    to avoid needing a git binary/credentials in its own container).

    The fallback is SAFE, not just convenient, for what these two tests
    actually need: GitHub's tarball/archive endpoint exports ONLY
    git-tracked content in the first place (the same as `git archive`
    would produce) -- gitignored files (public-full/, etc.) were never
    present in the checkout to begin with, so a plain walk over a
    freshly-extracted tree already matches what `git ls-files` would have
    said. Two real gaps, both filtered out explicitly below rather than
    assumed away: (1) artifacts created LOCALLY during THIS test run
    itself (bytecode caches, pytest's own cache dir) never went through
    git at all, and nothing about the checkout's origin excludes them;
    (2) a checkout tool can add SYMLINKS after extraction for its own
    purposes (confirmed live, 2026-08-20: the daily gap-finding agent
    above recreates a2uithoughts.md etc. as symlinks into a sibling
    checkout, purely for its own convenience) -- Path.is_file() follows a
    symlink and would happily report one as a normal tracked-looking
    file, exactly the git-sees-a-symlink-as-a-FILE problem this repo's own
    .gitignore already anchors these same paths to avoid. Excluding
    symlinks entirely in the fallback keeps this test's real question
    ("is this genuinely tracked in a2uicatalog's OWN history") from being
    fooled by something a checkout mechanism bolted on afterward."""
    if (ROOT / ".git").exists():
        out = subprocess.run(["git", "ls-files"], cwd=ROOT,
                             capture_output=True, text=True)
        return out.stdout.splitlines()
    return sorted(
        str(p.relative_to(ROOT)) for p in ROOT.rglob("*")
        if p.is_file() and not p.is_symlink()
        and not any(part in _RUNTIME_ARTIFACT_DIRS for part in p.relative_to(ROOT).parts)
        and p.suffix not in _RUNTIME_ARTIFACT_SUFFIXES
    )


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
# public-play/'s own copy is byte-identical output of the SAME generator
# (gen_mcp_apps_bundle.py — see its own OUT_PLAY comment and project.yaml's
# gen_mcp_apps_bundle entry) written for play.a2uicatalog.ai's isolated,
# deliberately stateless origin — not a hand-sync, and not debt: it's
# compiled every run alongside COMPILED_ENGINE, from the same source, by
# the same script. Declared 2026-09-10.
COMPILED_ENGINE_COPIES = {COMPILED_ENGINE, "public-play/renderer-bundle.html"}


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
    # Reuses _tracked_files() (see its own docstring for the no-.git
    # fallback) rather than a second, unguarded git subprocess call.
    tracked = [f for f in _tracked_files() if f.endswith((".html", ".js", ".gs"))]
    dispatch = sorted(
        rel for rel in tracked
        if "node_modules" not in rel
        and "prop === 'onChange'" in (ROOT / rel).read_text(errors="ignore")
    )
    accounted = ({MAINTAINED_ENGINE} | COMPILED_ENGINE_COPIES
                 | set(MANIFEST["known_debt"]["frozen_renderer_copies"]))
    undeclared = sorted(set(dispatch) - accounted)
    assert not undeclared, (
        "new copies of the wired output-wire dispatch, owned by no generator "
        "and declared nowhere — each is a hand-sync waiting to drift. Compile "
        "it from the engine, or declare it in project.yaml "
        f"known_debt.frozen_renderer_copies: {undeclared}")

    gone = sorted(accounted - set(dispatch) - COMPILED_ENGINE_COPIES)
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


# ─── stateless_origins — a promise checked, not just written ─────────────────
#
# Roast panel finding, 2026-09-10: play.a2uicatalog.ai's ENTIRE security
# argument (an iframe embedding it may safely grant allow-same-origin,
# because that hostname's cookies/DOM are worthless to steal) was enforced
# by a code comment only. Nothing stopped a future PR from quietly adding a
# Worker script or a state-bearing binding to it and invalidating that
# argument without touching the iframe's own sandbox attribute at all — the
# regression would be invisible at the call site that actually depends on it.
#
# `main` (a Worker script) is the specific thing this guards hardest: with
# no script attached, Cloudflare Workers Assets serves static files and
# nothing else — there is no code path that could dynamically set a cookie,
# read a binding, or do anything per-request at all. Once `main` exists,
# state can arrive by definition; that's the bright line, not "does it
# currently misbehave."
_STATE_BEARING_BINDING_KEYS = (
    "kv_namespaces", "d1_databases", "r2_buckets",
    "durable_objects", "queues", "vectorize", "hyperdrive",
)


def test_stateless_origins_carry_no_worker_script_or_state_bindings():
    for hostname, decl in MANIFEST["stateless_origins"].items():
        config_path = ROOT / decl["wrangler_config"]
        assert config_path.exists(), (
            f"{hostname}: declared wrangler_config {decl['wrangler_config']} "
            "does not exist")
        config = tomllib.loads(config_path.read_text())
        assert "main" not in config, (
            f"{hostname} ({decl['wrangler_config']}) now declares a Worker "
            "script (`main`) — this origin's whole reason an iframe may "
            "grant it allow-same-origin is that NOTHING here can set a "
            "cookie or hold state. A Worker script is exactly the thing "
            "that could. Either this origin no longer belongs in "
            "project.yaml's stateless_origins (and every allow-same-origin "
            "grant to it needs re-justifying), or the script must be "
            "provably stateless itself, which this test cannot verify — "
            "don't add one without a real conversation about what it does.")
        present_bindings = [k for k in _STATE_BEARING_BINDING_KEYS if k in config]
        assert not present_bindings, (
            f"{hostname} ({decl['wrangler_config']}) now declares state-"
            f"bearing binding(s) {present_bindings} — same reasoning as the "
            "`main` check above: this origin is only safe to grant "
            "allow-same-origin to because it holds nothing worth reading.")


def test_play_origin_bundle_source_never_writes_a_cookie():
    """Defense in depth alongside the wrangler-config check above: even
    with no server-side state possible (no Worker script, no bindings),
    a future atom's own client-side JS could still call
    `document.cookie = ...` inside the served bundle and start
    accumulating real per-visitor state that way — the wrangler-level
    guard can't see that, since it never executes any code to check.

    Scoped to gen_mcp_apps_bundle.py's own renderer_files() -- the exact
    source set concatenated into public-play/renderer-bundle.html, no
    more, no less, so this stays a real check on what actually ships
    there rather than a repo-wide grep that would also flag unrelated
    surfaces this origin never serves."""
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    import gen_mcp_apps_bundle  # noqa: E402

    hits = []
    for path in gen_mcp_apps_bundle.renderer_files():
        if not path.exists():
            continue
        if re.search(r"document\.cookie\s*=", path.read_text(errors="ignore")):
            hits.append(str(path.relative_to(ROOT)))
    assert not hits, (
        f"document.cookie write(s) found in the play-origin bundle source: "
        f"{hits} — play.a2uicatalog.ai (project.yaml stateless_origins) is "
        "only safe to grant allow-same-origin to because nothing served "
        "there can hold real state. A client-side cookie write is exactly "
        "the kind of state that guarantee assumes doesn't exist.")
