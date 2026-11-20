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
    ("mcp/package.json", r"(\d+)-atom vocabulary"),   # the npm listing; Ora quoted the stale 474 on 2026-11-01
    ("sdk/python/pyproject.toml", r"(\d+)-atom vocabulary"),   # the PyPI listing
    # The landing page and llms.txt were the places that said "550+" / "474" while 573 were published (outside review,
    # 2026-11-15). Both are generated (generate_atom_pages.py, gen_openapi.py); holding them here means a generator that
    # regresses to a rounded or typed figure fails --check. tests/test_site_count_consistency.py sweeps every other page.
    ("public/index.html", r'<span class="stat-num">(\d+\+?)</span><span class="stat-lbl">Typed atoms'),   # home redesign 2026-11-20: the stat strip
    ("public/index.html", r"(\d+\+?) typed UI atoms for web"),   # the JSON-LD description
    ("public/index.html", r"Search and preview (\d+\+?) atoms"),
    ("public/index.html", r"Explore (\d+\+?) atoms"),
    ("public/index.html", r"Search all (\d+\+?) atoms"),
    ("public/llms.txt", r"vocabulary \((\d+) atoms\)"),
    ("public/what-is-a2ui.md", r"catalog of (\d+) published components"),
]

# The number of surfaces, held to the same rule: distinct surface ids in public/spec.json (works_on). The README said "8"
# while spec.json and the home page say 13 (outside audit W4).
SURFACE_CLAIMS = [
    ("README.md", r"## \d+ atoms across (\d+) surfaces"),
    ("README.md", r"which of the \*\*(\d+) surfaces\*\*"),
    ("README.md", r"all atoms × (\d+) surfaces"),
]

# Whole places where count claims keep appearing (owner 2026-11-01: "correct the harness to mechanically update
# that", after skills/a2ui-catalog/SKILL.md still said 480 with 573 published). Every "<N> atoms" / "<N> typed
# (UI) atoms" in these files is held to the published count, so a new skill or doc page is covered the day it is
# added, without anyone remembering to extend CLAIMS.
SWEEP_GLOBS = ["skills/*/SKILL.md", "prompts/a2ui-builder-gem*.md", "docs/quickstart*.md", "payloads/learn-a2ui*.json", "payloads/learn-a2ui-modules/*.json"]
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


def surface_count():
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    ids = {s for a in spec.get("atoms", []) for s in ((a.get("surfaces") or {}).get("works_on") or [])}
    if len(ids) < 5:
        sys.exit(f"gen_atom_count: implausible surface count ({len(ids)})")
    return len(ids)


def stale(n):
    """Returns [(path, pattern, found_numbers)] for every claim that does not equal n (surface claims: the surface count)."""
    out = []
    m = surface_count()
    for path, pattern in SURFACE_CLAIMS:
        found = re.findall(pattern, (ROOT / path).read_text(encoding="utf-8"))
        if not found:
            sys.exit(f"gen_atom_count: {path} no longer contains a claim matching {pattern!r}")
        if any(x != str(m) for x in found):
            out.append((path, pattern, found))
    for path, pattern in _claims():
        text = (ROOT / path).read_text(encoding="utf-8")
        found = re.findall(pattern, text)
        if not found:
            sys.exit(f"gen_atom_count: {path} no longer contains a claim matching {pattern!r}; "
                     "update CLAIMS if the wording changed")
        if any(x != str(n) for x in found):
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
    sc = surface_count()
    for path, pattern in [(a, b) for a, b in SURFACE_CLAIMS] + _claims():
        val = sc if (path, pattern) in SURFACE_CLAIMS else n
        p = ROOT / path
        text = p.read_text(encoding="utf-8")
        new = re.sub(pattern, lambda m, val=val: m.group(0).replace(m.group(1), str(val), 1), text)
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
