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

A second block (renderer-matrix markers) summarises the renderer dimension (`x-renderers`, what draws an
atom, measured per renderer): one row per renderer with status counts, read from the same spec.json, names and
versions from public/catalogue/renderer-matrix-v1.json. The surface block above is unchanged.

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
R_START = "<!-- renderer-matrix:start -->"
R_END = "<!-- renderer-matrix:end -->"
MATRIX = ROOT / "public" / "catalogue" / "renderer-matrix-v1.json"
STATUS_ORDER = [("drawn", "Drawn"), ("native", "Native"), ("drawn_with_differences", "With differences"),
                ("degraded", "Degraded"), ("not_verified", "Not verified"), ("not_supported", "Not supported"),
                ("not_measured", "Not measured")]

# column order + short headers (full surface ids as declared in schema.yaml)
SURFACES = [
    ("web", "web"),
    ("google-apps-script-web", "gas-web"),
    ("google-apps-script-side-panel", "gas-panel"),
    ("google-meet-stage", "meet"),
    ("google-chat", "chat"),
    ("mcp-apps", "mcp-apps"),
    ("claude-code", "claude-code"),
    ("android", "android"),
    ("email", "email"),
    ("pdf", "pdf"),
    ("slides", "slides"),
    ("pptx", "pptx"),
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


def build_renderer_table(atoms: list, matrix: dict) -> str:
    """One row per renderer: status counts over the atoms' `x-renderers` (spec.json), plus name/version/date."""
    counts = {}
    for a in atoms:
        for rid, e in (a.get("x-renderers") or {}).items():
            c = counts.setdefault(rid, {})
            c[e["status"]] = c.get(e["status"], 0) + 1
    used = [(k, lbl) for k, lbl in STATUS_ORDER if any(k in c for c in counts.values())]
    lines = [f"{len(atoms)} atoms · what draws each atom, per renderer, measured against React · generated from "
             f"`public/spec.json` (`x-renderers`) by `scripts/gen_compat_matrix.py` — do not edit by hand. "
             f"Per atom and per check: [a2uicatalog.ai/renderers/](https://a2uicatalog.ai/renderers/).", ""]
    lines.append("| Renderer | Version measured | Measured | " + " | ".join(l for _, l in used) + " |")
    lines.append("|---" * (len(used) + 3) + "|")
    for rid, reg in matrix["renderers"].items():
        ms = reg.get("measurement") or {}
        c = counts.get(rid, {})
        lines.append(f"| [{reg['name']}](https://a2uicatalog.ai/renderers/{rid}/) | {ms.get('renderer_version') or 'not measured'} | "
                     f"{ms.get('measured') or '—'} | " + " | ".join(str(c.get(k, 0)) for k, _ in used) + " |")
    lines += ["", "Independent and unofficial. " + matrix["trademark_note"]]
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
    if R_START in new and R_END in new and MATRIX.exists():
        new = re.sub(re.escape(R_START) + r".*?" + re.escape(R_END),
                     lambda _m: R_START + "\n" + build_renderer_table(atoms, json.loads(MATRIX.read_text())) + "\n" + R_END,
                     new, flags=re.S)
        print("✓ renderer matrix block regenerated → README.md")
    README.write_text(new)
    print(f"✓ compat matrix regenerated — {len(atoms)} atoms × {len(SURFACES)} surfaces → README.md")


if __name__ == "__main__":
    main()
