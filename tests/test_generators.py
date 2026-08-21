"""The generator class has teeth: every generator script must be registered
in project.yaml `generators:`, and every declared output must exist.

Two incidents motivated this (2026-07): generate_atom_pages importing a
stale stub renderer (site would have shipped with zero atom previews), and
ai-catalog.json passing structural checks while its target 404'd for weeks.
Both were unregistered-generator failures: outputs nobody audited because
no schema said they must exist.
"""

from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
MANIFEST = yaml.safe_load((ROOT / "project.yaml").read_text())
GENERATORS = MANIFEST.get("generators", {})


def _generator_scripts():
    return sorted(
        p.relative_to(ROOT).as_posix()
        for pat in ("gen_*.py", "generate_*.py")
        for p in (ROOT / "scripts").glob(pat)
    )


def test_registry_exists_and_nonempty():
    assert GENERATORS, "project.yaml has no generators: section"


def test_every_generator_script_is_registered():
    registered = {g["script"] for g in GENERATORS.values()}
    missing = [s for s in _generator_scripts() if s not in registered]
    assert not missing, (
        f"unregistered generator script(s): {missing} — add them to "
        "project.yaml generators: (a generator that isn't declared is the "
        "failure mode this registry exists to prevent)"
    )


def test_registered_scripts_exist():
    gone = [n for n, g in GENERATORS.items() if not (ROOT / g["script"]).exists()]
    assert not gone, f"registered generator script(s) missing from disk: {gone}"


# Two declared outputs are genuinely never expected to exist on a fresh
# checkout — regenerated on demand, locally, and never committed anywhere:
#   - gen_authoring -> public-full/authoring/: publish: "none — gated
#     full.a2uicatalog.ai only" — public-full/ is itself gitignored, a
#     local-only build (`ops.py run catalog-rebuild-full`).
#   - gen_renderer_manifest -> ops/renderer-manifest.json: publish: "none —
#     build artifact consumed by scripts/check_core.py" — ops/ is a
#     gitignored symlink into a2ui-private's own durable home, and this
#     specific file is a build artifact, not tracked content there either.
# Confirmed live, 2026-08-21 (curtiskrygier/repo-improvement-agent's own
# daily gap-finding agent): a REAL run against this repo's actual current
# HEAD — with a2ui-private checked out as a real sibling, containing real,
# committed generated files for the OTHER private-tier generators
# (gen_worker_renderers, gen_slack_mapping — those DO exist and DO keep
# being checked here, correctly; a sibling repo being checked out doesn't
# mean everything under it is exempt) — still failed only on these two.
_LOCAL_BUILD_ONLY_PREFIXES = ("public-full/", "ops/")


def test_declared_outputs_exist():
    """Dereference check: a declared output that doesn't exist is a
    compliant pointer to a dead target — excluding the small, explicit set
    of outputs that are local-build-only by design (see
    _LOCAL_BUILD_ONLY_PREFIXES's own comment), which are never expected to
    exist on a fresh checkout at all."""
    dead = []
    for name, g in GENERATORS.items():
        for out in g.get("outputs", []):
            if out.startswith(_LOCAL_BUILD_ONLY_PREFIXES):
                continue
            p = ROOT / out
            if out.endswith("/"):
                if not (p.is_dir() and any(p.iterdir())):
                    dead.append(f"{name}: {out} (missing or empty dir)")
            elif not p.exists():
                dead.append(f"{name}: {out}")
    assert not dead, f"declared generator output(s) missing: {dead}"


def test_outputs_declared_or_explicitly_empty():
    undeclared = [n for n, g in GENERATORS.items() if "outputs" not in g]
    assert not undeclared, (
        f"generator(s) without an outputs field: {undeclared} — declare the "
        "artifact list, or [] with a note for in-memory consumers"
    )


def test_stampable_runbook_bom_is_validated_and_published():
    """learning_hub (first stampable runbook) locks: the published runbooks
    index carries the FULL definition (input_contract + composition — the
    Worker embed and the emit_runbook_surface engine depend on it), and every
    atom the BOM references is a real catalogue type. gen_public_catalog.py
    hard-fails on unknown atoms at build time; this locks the contract so a
    future refactor can't quietly slim the index back down to summaries."""
    import json
    idx = json.load(open(ROOT / "public/runbooks/index.json"))
    lh = [r for r in idx["runbooks"] if r.get("name") == "learning_hub"]
    assert lh, "learning_hub missing from public/runbooks/index.json"
    rb = lh[0]
    assert rb.get("kind") == "stampable"
    for field in ("input_contract", "composition", "parsing_guide"):
        assert rb.get(field), f"learning_hub.{field} missing from published index"
    comp = rb["composition"]
    assert comp.get("container_atom") == "hub"
    kinds = comp.get("slide_kind_atoms") or {}
    assert set(kinds) == {"timeline", "drill", "flashcards", "quiz", "takeaways", "method"}
