#!/usr/bin/env python3
"""check_core — the lean-renderer build gate.

Enforces atoms/atom-packs.yaml as the complete, single-home partition of the atom
catalogue, and keeps the lean base renderer honest:

  1. COVERAGE   — every atom in atoms/schema.yaml is assigned to exactly one bucket
                  (no unsorted atoms, no atom in two buckets, no phantom names).
  2. LEAN CORE  — if a lean-renderer manifest is present, it may only reference atoms in
                  `core` + `promote` + the packs it explicitly declares. Referencing a
                  pack atom it didn't declare = fail (that's fluff leaking back into core).

Exit non-zero on any violation, printing what and where. Wire into CI / pre-publish.

Usage:
  python3 scripts/check_core.py                 # coverage check only
  python3 scripts/check_core.py <renderer.json> # + lean-core check against a manifest

The optional manifest is JSON: {"packs": ["workspace-live", ...], "atoms": ["heading", ...]}
where `atoms` is the flat list of atom types the lean renderer actually wires.
"""
import json
import os
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCHEMA = os.path.join(ROOT, "atoms", "schema.yaml")
PACKS = os.path.join(ROOT, "atoms", "atom-packs.yaml")

ALWAYS = ("a2ui-atoms-v1",)   # the base catalog is always resolved


def _schema_atoms():
    d = yaml.safe_load(open(SCHEMA))
    return {b["type"] for b in d["blocks"] if isinstance(b, dict) and b.get("type")}


def _partition():
    return yaml.safe_load(open(PACKS))


def check_coverage(schema, part):
    """Every schema atom in exactly one bucket; every mapped atom exists in schema."""
    errors = []
    seen = {}
    for bucket, atoms in part.items():
        for a in atoms:
            if a in seen:
                errors.append(f"atom in two buckets: {a} ({seen[a]} + {bucket})")
            seen[a] = bucket
    mapped = set(seen)
    unsorted = sorted(schema - mapped)
    phantom = sorted(mapped - schema)
    if unsorted:
        errors.append(f"{len(unsorted)} atom(s) in schema.yaml with NO bucket "
                      f"(add to atoms/atom-packs.yaml): {', '.join(unsorted)}")
    if phantom:
        errors.append(f"{len(phantom)} atom(s) in atom-packs.yaml not in schema.yaml "
                      f"(stale — remove): {', '.join(phantom)}")
    return errors


def check_lean(manifest_path, part):
    """Lean renderer may only reference core + promote + its declared packs."""
    m = json.load(open(manifest_path))
    declared = set(m.get("packs", []))
    used = set(m.get("atoms", []))
    allowed = set()
    for b in list(ALWAYS) + sorted(declared):
        allowed |= set(part.get(b, []))
    unknown_pack = sorted(declared - (set(part) - set(ALWAYS)))
    leaked = sorted(used - allowed)
    errors = []
    if unknown_pack:
        errors.append(f"manifest declares unknown pack(s): {', '.join(unknown_pack)}")
    if leaked:
        # tell them WHICH pack each leaked atom lives in, so the fix is obvious
        home = {a: b for b, atoms in part.items() for a in atoms}
        detail = ", ".join(f"{a} (pack:{home.get(a,'?')})" for a in leaked)
        errors.append(f"{len(leaked)} atom(s) used but not in core/promote/declared packs "
                      f"— either declare the pack or drop the atom: {detail}")
    return errors


def main():
    schema = _schema_atoms()
    part = _partition()
    errors = check_coverage(schema, part)
    if len(sys.argv) > 1:
        errors += check_lean(sys.argv[1], part)
    if errors:
        print("✗ check_core FAILED:")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    base = ALWAYS[0]
    base_n = len(part.get(base, []))
    print(f"✓ check_core: {len(schema)} atoms fully partitioned across {len(part)} catalogs; "
          f"base catalog {base} = {base_n} atoms (always resolved).")


if __name__ == "__main__":
    main()
