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


def test_declared_outputs_exist():
    """Dereference check: a declared output that doesn't exist is a
    compliant pointer to a dead target."""
    dead = []
    for name, g in GENERATORS.items():
        for out in g.get("outputs", []):
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
