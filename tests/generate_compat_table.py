"""Generate the surface compatibility table for the README from atoms/schema.yaml.

Usage:
    python tests/generate_compat_table.py

Prints the markdown table to stdout. Redirect to update the README section.
"""

import sys
from pathlib import Path
import yaml

CATALOGUE_ROOT = Path(__file__).parent.parent
SCHEMA_PATH = CATALOGUE_ROOT / "atoms" / "schema.yaml"
SURFACES = ["web", "meet-stage", "googlechat", "email", "pdf", "google-apps-script-web"]

SYMBOLS = {
    "works":        "✅",
    "degraded":     "⚠️",
    "incompatible": "❌",
    "unknown":      "—",
}


def surface_status(atom: dict, surface: str) -> str:
    s = atom.get("surfaces", {})
    works_on      = s.get("works_on", [])
    degraded_on   = [e["surface"] for e in (s.get("degraded_on") or [])]
    incompatible  = [e["surface"] for e in (s.get("incompatible_on") or [])]

    if surface in incompatible:
        return SYMBOLS["incompatible"]
    if surface in degraded_on:
        return SYMBOLS["degraded"]
    if surface in works_on:
        return SYMBOLS["works"]
    return SYMBOLS["unknown"]


def source_label(atom: dict) -> str:
    src = atom.get("source", {})
    name = src.get("name", "—")
    url  = src.get("url", "")
    if url:
        # Shorten label for table display
        short = name.split("/")[-1] if "/" in name else name
        return f"[{short}]({url})"
    return name


def generate_table(schema: dict) -> str:
    atoms = schema["blocks"]
    header = "| Atom | " + " | ".join(SURFACES) + " | Source |"
    sep    = "|---|" + "---|" * len(SURFACES) + "---|"
    rows   = []
    for atom in atoms:
        name   = f"`{atom['type']}`"
        cells  = [surface_status(atom, s) for s in SURFACES]
        source = source_label(atom)
        rows.append(f"| {name} | " + " | ".join(cells) + f" | {source} |")

    legend = (
        "\n\n"
        f"{SYMBOLS['works']} works fully  "
        f"{SYMBOLS['degraded']} degraded — renders with caveats  "
        f"{SYMBOLS['incompatible']} incompatible — do not use\n"
    )

    return "\n".join([header, sep] + rows) + legend


if __name__ == "__main__":
    with open(SCHEMA_PATH) as f:
        schema = yaml.safe_load(f)
    print(generate_table(schema))
