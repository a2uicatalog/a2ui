#!/usr/bin/env python3
"""
Generate ARD-compliant ai-catalog.json from atoms/schema.yaml.

Output goes to public/.well-known/ai-catalog.json — the Cloudflare Pages
root for aicatalog.ai.

Run:
  python3 scripts/generate_ard_catalog.py

Or with a custom domain:
  python3 scripts/generate_ard_catalog.py --domain aicatalog.ai
"""
import argparse
import json
import os
import sys

try:
    import yaml
except ImportError:
    print("pip install pyyaml", file=sys.stderr)
    sys.exit(1)

SCHEMA = os.path.join(os.path.dirname(__file__), "..", "atoms", "schema.yaml")
OUTPUT = os.path.join(os.path.dirname(__file__), "..", "public", ".well-known", "ai-catalog.json")


def type_to_display(type_str):
    return type_str.replace("_", " ").title()


def get_capabilities(atom):
    surfaces = atom.get("surfaces", {})
    works_on = surfaces.get("works_on", [])
    return works_on if isinstance(works_on, list) else []


def generate_queries(atom):
    queries = []
    atom_type  = atom.get("type", "")
    desc       = atom.get("description", "")
    compact    = atom.get("compact_description", "")

    if compact:
        queries.append(f"show a {compact.rstrip('.')}")

    if desc and desc.lower() != compact.lower():
        # Trim to a clean sentence if long
        q = desc[:120].rstrip()
        if len(desc) > 120:
            q = q.rsplit(" ", 1)[0]
        queries.append(q.rstrip(".").lower())

    human = atom_type.replace("_", " ")
    queries.append(f"render a {human}")

    # Deduplicate, max 3
    seen, result = set(), []
    for q in queries:
        q = q.strip()
        if q and q not in seen:
            seen.add(q)
            result.append(q)
        if len(result) >= 3:
            break

    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", default="a2uicatalog.ai")
    parser.add_argument("--output", default=OUTPUT)
    args = parser.parse_args()

    domain = args.domain
    base   = f"https://{domain}"

    with open(SCHEMA) as f:
        raw = yaml.safe_load(f)

    blocks = raw.get("blocks", [])

    # Deduplicate by type — keep first occurrence
    seen_types, unique = set(), []
    for block in blocks:
        t = block.get("type")
        if t and t not in seen_types:
            seen_types.add(t)
            unique.append(block)

    entries = []

    # Top-level renderer capability entry
    entries.append({
        "identifier": f"urn:air:{domain}:renderer:a2ui",
        "displayName": "A2UI Multi-Surface Renderer",
        "type": "application/vnd.a2ui.renderer+json",
        "url": f"{base}/spec.json",
        "capabilities": ["web", "meet-stage", "apps-script-web", "googlechat", "email", "pdf"],
        "description": (
            f"Open-source renderer with {len(unique)} typed atoms for generating rich UI "
            "across Google Meet stages, Chat Cards, Apps Script web apps, and web surfaces "
            "from a single JSON schema payload."
        ),
        "representativeQueries": [
            "render a rich UI from structured JSON data",
            "generate Google Meet stage content from a schema",
            "build Google Chat cards from a data payload",
            "display interactive components in an Apps Script web app",
            "create multi-surface UI from a single atom schema",
        ],
    })

    # One entry per unique atom
    for atom in unique:
        atom_type = atom.get("type", "")
        if not atom_type:
            continue
        entries.append({
            "identifier": f"urn:air:{domain}:atom:{atom_type}",
            "displayName": type_to_display(atom_type),
            "type": "application/vnd.a2ui.atom+json",
            "url": f"{base}/atoms/{atom_type}",
            "capabilities": get_capabilities(atom),
            "description": atom.get("description", ""),
            "representativeQueries": generate_queries(atom),
        })

    catalog = {
        "specVersion": "1.0",
        "host": {
            "displayName": "A2UI Atomic Catalog",
            "identifier": f"did:web:{domain}",
        },
        "entries": entries,
    }

    out_path = args.output
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(catalog, f, indent=2)

    print(f"✓ {len(entries)} entries ({len(unique)} atoms + 1 renderer) → {out_path}")


if __name__ == "__main__":
    main()
