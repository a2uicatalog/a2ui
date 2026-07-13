#!/usr/bin/env python3
"""
Regenerate README.md's surface-compatibility matrix from public/spec.json.

spec.json is ground truth (it is itself compiled from atoms/schema.yaml by
gen_public_catalog.py): every atom carries surfaces.works_on, an optional
surfaces.degraded_on list, and a source {name, url, license}. The README
matrix was previously hand-maintained and drifted — duplicate rows,
label/URL mismatches, only 5 of the 8 surfaces. This script replaces the
block between the compat-matrix markers wholesale; never edit that block by
hand.

Run:
  python3 scripts/gen_public_catalog.py   # if schema.yaml changed first
  python3 scripts/gen_compat_matrix.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
SPEC = ROOT / "public" / "spec.json"
README = ROOT / "README.md"

START = "<!-- compat-matrix:start -->"
END = "<!-- compat-matrix:end -->"

# column order + short headers (full surface ids as declared in schema.yaml)
SURFACES = [
    ("web", "web"),
    ("google-apps-script-web", "gas-web"),
    ("google-apps-script-side-panel", "gas-panel"),
    ("google-meet-stage", "meet"),
    ("google-chat", "chat"),
    ("mcp-apps", "mcp-apps"),
    ("email", "email"),
    ("pdf", "pdf"),
]


def cell(atom: dict, surface: str) -> str:
    surf = atom.get("surfaces", {}) or {}
    if surface in (surf.get("works_on") or []):
        return "✅"
    degraded = {d.get("surface") for d in (surf.get("degraded_on") or [])}
    if surface in degraded:
        return "⚠️"
    return "—"


def source_cell(atom: dict) -> str:
    s = atom.get("source") or {}
    name = s.get("name", "?")
    url = s.get("url", "")
    lic = s.get("license", "")
    link = f"[{name}]({url})" if url else name
    return f"{link} · {lic}" if lic else link


def build_table(atoms: list) -> str:
    lines = []
    lines.append(f"{len(atoms)} atoms · generated from `public/spec.json` by "
                 f"`scripts/gen_compat_matrix.py` — do not edit by hand.")
    lines.append("")
    header = "| Atom | " + " | ".join(h for _, h in SURFACES) + " | Source · license |"
    sep = "|---" * (len(SURFACES) + 2) + "|"
    lines.append(header)
    lines.append(sep)
    for atom in sorted(atoms, key=lambda a: a["type"]):
        cells = " | ".join(cell(atom, sid) for sid, _ in SURFACES)
        lines.append(f"| `{atom['type']}` | {cells} | {source_cell(atom)} |")
    lines.append("")
    lines.append("✅ full support  ⚠️ renders with caveats (degradation note in "
                 "spec.json)  — not declared for this surface — treat as unsupported")
    return "\n".join(lines)


def main() -> None:
    atoms = json.loads(SPEC.read_text())["atoms"]
    readme = README.read_text()
    if START not in readme or END not in readme:
        print(f"markers {START} / {END} not found in README.md", file=sys.stderr)
        sys.exit(1)
    table = build_table(atoms)
    new = re.sub(
        re.escape(START) + r".*?" + re.escape(END),
        START + "\n" + table + "\n" + END,
        readme, flags=re.S,
    )
    README.write_text(new)
    print(f"✓ compat matrix regenerated — {len(atoms)} atoms × {len(SURFACES)} surfaces → README.md")


if __name__ == "__main__":
    main()
