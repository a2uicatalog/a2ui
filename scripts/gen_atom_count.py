#!/usr/bin/env python3
"""
Keep every hand-typed "N atoms" claim equal to the real published count.

Registries (Smithery, MCP Market, the MCP server card) copy these files, and the number went stale once:
the MCP server card still said 474 while 548 atoms were published. The README badge block is already
generated (gen_readme_badges.py); this covers the prose it cannot reach.

Source of truth: the `components` list in public/catalogue/a2ui-atoms-v1.json (the published catalogue
that the live site and the MCP server serve), cross-checked against public/spec.json.

    python3 scripts/gen_atom_count.py            # rewrite the numbers in place
    python3 scripts/gen_atom_count.py --check    # exit 1 if any is stale; writes nothing (CI)

To cover a new place, add a (path, pattern) pair to CLAIMS. The pattern must have exactly one capture
group: the number.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOGUE = ROOT / "public" / "catalogue" / "a2ui-atoms-v1.json"
SPEC = ROOT / "public" / "spec.json"

CLAIMS = [
    ("public/.well-known/mcp/server-card.json", r"(\d+) typed UI atoms"),
    ("SKILL.md", r"(\d+) typed UI atoms"),
    ("SKILL.md", r"whole (\d+)-atom vocabulary"),
    ("mcp/LISTING.md", r"vocabulary of (\d+) typed atoms"),
    ("mcp/README.md", r"`a2ui-atoms-v1` \((\d+) atoms\)"),
    ("README.md", r"Browse all (\d+) atoms"),
    ("README.md", r"## (\d+) atoms across"),
]


def published_count():
    n = len(json.loads(CATALOGUE.read_text(encoding="utf-8"))["components"])
    if SPEC.exists():
        spec = json.loads(SPEC.read_text(encoding="utf-8"))
        m = len(spec.get("atoms", spec if isinstance(spec, list) else []))
        if m and m != n:
            sys.exit(f"gen_atom_count: the catalogue lists {n} atoms but spec.json lists {m}; "
                     "rebuild first (ops.py run catalog-rebuild) so the two agree")
    if n < 100:
        sys.exit(f"gen_atom_count: implausible count ({n}); refusing to write")
    return n


def stale(n):
    """Returns [(path, pattern, found_numbers)] for every claim that does not equal n."""
    out = []
    for path, pattern in CLAIMS:
        text = (ROOT / path).read_text(encoding="utf-8")
        found = re.findall(pattern, text)
        if not found:
            sys.exit(f"gen_atom_count: {path} no longer contains a claim matching {pattern!r}; "
                     "update CLAIMS if the wording changed")
        if any(int(x) != n for x in found):
            out.append((path, pattern, found))
    return out


def main():
    check = "--check" in sys.argv[1:]
    n = published_count()
    bad = stale(n)
    if check:
        if bad:
            for path, _pat, found in bad:
                print(f"STALE {path}: says {', '.join(found)}; {n} atoms are published", file=sys.stderr)
            print("run: python3 scripts/gen_atom_count.py   (or ops.py run catalog-rebuild)", file=sys.stderr)
            return 1
        print(f"✓ atom-count claims match the published catalogue ({n})")
        return 0
    changed = set()
    for path, pattern in CLAIMS:
        p = ROOT / path
        text = p.read_text(encoding="utf-8")
        new = re.sub(pattern, lambda m: m.group(0).replace(m.group(1), str(n), 1), text)
        if new != text:
            p.write_text(new, encoding="utf-8")
            changed.add(path)
    print(f"✓ atom-count claims: {n} atoms" + (f"; updated {', '.join(sorted(changed))}" if changed else " (already current)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
