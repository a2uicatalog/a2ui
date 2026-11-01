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
    ("plugin.json", r"(\d+) typed A2UI components"),
    ("docs/quickstart-claude.md", r"\((\d+) atoms across"),
]

# Whole places where count claims keep appearing (owner 2026-11-01: "correct the harness to mechanically update
# that", after skills/a2ui-catalog/SKILL.md still said 480 with 573 published). Every "<N> atoms" / "<N> typed
# (UI) atoms" in these files is held to the published count, so a new skill or doc page is covered the day it is
# added, without anyone remembering to extend CLAIMS.
SWEEP_GLOBS = ["skills/*/SKILL.md", "docs/quickstart*.md", "payloads/learn-a2ui*.json", "payloads/learn-a2ui-modules/*.json"]
SWEEP_PATTERN = r"\b(\d{3}) (?:typed )?(?:UI )?atoms\b"


def _claims():
    out = list(CLAIMS)
    for g in SWEEP_GLOBS:
        for f in sorted(ROOT.glob(g)):
            rel = f.relative_to(ROOT).as_posix()
            if re.search(SWEEP_PATTERN, f.read_text(encoding="utf-8")):
                out.append((rel, SWEEP_PATTERN))
    return out


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
    for path, pattern in _claims():
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
    for path, pattern in _claims():
        p = ROOT / path
        text = p.read_text(encoding="utf-8")
        new = re.sub(pattern, lambda m: m.group(0).replace(m.group(1), str(n), 1), text)
        if new != text:
            p.write_text(new, encoding="utf-8")
            changed.add(path)
    print(f"✓ atom-count claims: {n} atoms" + (f"; updated {', '.join(sorted(changed))}" if changed else " (already current)"))
    if any(c.startswith("skills/") for c in changed):
        # the skills index carries a sha256 of each SKILL.md; a count edit must not leave it stale
        import subprocess
        subprocess.run([sys.executable, str(ROOT / "scripts" / "gen_agent_skills_index.py")], check=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
