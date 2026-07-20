#!/usr/bin/env python3
"""
Regenerate README.md's badge row from public/spec.json — the same
marker-block pattern as gen_compat_matrix.py, for the same reason: the old
hand-written badges said "450+" while the catalog had grown to 473, and
nothing could catch the drift. Wired into catalog-rebuild, so every schema
change refreshes the counts the moment the pipeline runs.

Only the atoms/surfaces badges are computed; the MCP/ARD/license/spec
badges are stable declarations and stay literal inside the same block (the
whole block is rewritten, so edit THIS template, not the README).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
SPEC = ROOT / "public" / "spec.json"
README = ROOT / "README.md"
START, END = "<!-- readme-badges:start -->", "<!-- readme-badges:end -->"

TEMPLATE = """{start}
[![Atoms](https://img.shields.io/badge/atoms-{n_atoms}-7c9cff?style=flat-square&labelColor=0a0e17)](https://a2uicatalog.ai/)
[![Surfaces](https://img.shields.io/badge/surfaces-{n_surfaces}-38bdf8?style=flat-square&labelColor=0a0e17)](https://a2uicatalog.ai/spec.json)
[![MCP](https://img.shields.io/badge/MCP_server-a2uicatalog.ai%2Fmcp-7c9cff?style=flat-square&labelColor=0a0e17)](https://a2uicatalog.ai/mcp)
[![ARD](https://img.shields.io/badge/ARD-ai--catalog.json-38bdf8?style=flat-square&labelColor=0a0e17)](https://a2uicatalog.ai/.well-known/ai-catalog.json)
[![License](https://img.shields.io/badge/license-MIT-34d399?style=flat-square&labelColor=0a0e17)](LICENSE)
[![A2UI](https://img.shields.io/badge/spec-v1.0_candidate-a78bfa?style=flat-square&labelColor=0a0e17)](renderers/a2ui_v1.py)
{end}"""


def main():
    data = json.loads(SPEC.read_text(encoding="utf-8"))
    atoms = data.get("atoms", data if isinstance(data, list) else [])
    n_atoms = len(atoms)
    surfaces = set()
    for a in atoms:
        surfaces.update((a.get("surfaces") or {}).get("works_on") or [])
    n_surfaces = len(surfaces)
    if not n_atoms or not n_surfaces:
        sys.exit(f"gen_readme_badges: implausible counts (atoms={n_atoms}, "
                 f"surfaces={n_surfaces}) — refusing to write")

    readme = README.read_text(encoding="utf-8")
    if START not in readme or END not in readme:
        sys.exit(f"gen_readme_badges: markers {START} / {END} not found in README.md")
    before = readme.split(START)[0]
    after = readme.split(END)[1]
    block = TEMPLATE.format(start=START, end=END, n_atoms=n_atoms, n_surfaces=n_surfaces)
    README.write_text(before + block + after, encoding="utf-8")
    print(f"✓ README badges: {n_atoms} atoms, {n_surfaces} surfaces (from public/spec.json)")


if __name__ == "__main__":
    main()
