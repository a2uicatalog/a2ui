#!/usr/bin/env python3
"""
Generate the machine-readable catalog artifacts served from public/.

Outputs:
  public/spec.json               — full atom catalog (the URL ai-catalog.json points at)
  public/atoms/index.json        — compact index: type + compact_description + surfaces
  public/runbooks/index.json     — runbook library compiled from runbooks/*.yaml
  public/catalogue/gdm-v0.2.json — stable URI copy of the GDM component catalog

Run:
  python3 scripts/gen_public_catalog.py
"""
import json
import os
import shutil
import sys

try:
    import yaml
except ImportError:
    print("pip install pyyaml", file=sys.stderr)
    sys.exit(1)

ROOT = os.path.join(os.path.dirname(__file__), "..")
SCHEMA = os.path.join(ROOT, "atoms", "schema.yaml")
RUNBOOKS_DIR = os.path.join(ROOT, "runbooks")
GDM_SPEC = os.path.join(ROOT, "spec", "gdm-v0.2.json")
PUBLIC = os.path.join(ROOT, "public")

BASE_URL = "https://a2uicatalog.ai"


def load_blocks():
    with open(SCHEMA) as f:
        return yaml.safe_load(f)["blocks"]


def write_json(rel_path, payload):
    path = os.path.join(PUBLIC, rel_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(payload, f, indent=1, ensure_ascii=False)
        f.write("\n")
    size_kb = os.path.getsize(path) / 1024
    print(f"  ✅ public/{rel_path} ({size_kb:.1f} KB)")


def gen_spec(blocks):
    atoms = []
    for b in blocks:
        atoms.append({
            "type": b["type"],
            "description": b.get("description", ""),
            "compact_description": b.get("compact_description", ""),
            "surfaces": b.get("surfaces", {}),
            "fields": b.get("fields", {}),
            "source": b.get("source", {}),
        })
    return {
        "catalogId": "a2ui-atoms-v1",
        "displayName": "A2UI Multi-Surface Renderer",
        "type": "application/vnd.a2ui.renderer+json",
        "atomCount": len(atoms),
        "compactIndex": f"{BASE_URL}/atoms/index.json",
        "runbooks": f"{BASE_URL}/runbooks/index.json",
        "trainingPrompt": f"{BASE_URL}/prompts/training-md-gem.md",
        "builderPrompt": f"{BASE_URL}/prompts/a2ui-builder-gem.md",
        "atoms": atoms,
    }


def gen_compact_index(blocks):
    return {
        "catalogId": "a2ui-atoms-v1",
        "atomCount": len(blocks),
        "fullSpec": f"{BASE_URL}/spec.json",
        "atoms": [
            {
                "type": b["type"],
                "compact": b.get("compact_description", ""),
                "surfaces": b.get("surfaces", {}).get("works_on", []),
            }
            for b in blocks
        ],
    }


def gen_runbooks_index(known_types):
    runbooks = []
    if not os.path.isdir(RUNBOOKS_DIR):
        return {"runbooks": []}
    for name in sorted(os.listdir(RUNBOOKS_DIR)):
        if not name.endswith((".yaml", ".yml")):
            continue
        with open(os.path.join(RUNBOOKS_DIR, name)) as f:
            rb = yaml.safe_load(f)
        unknown = [s["atom"] for s in rb.get("sequence", []) if s.get("atom") not in known_types]
        if unknown:
            print(f"  ❌ {name}: unknown atom types {unknown}", file=sys.stderr)
            sys.exit(1)
        runbooks.append(rb)
    return {"catalogId": "a2ui-atoms-v1", "runbookCount": len(runbooks), "runbooks": runbooks}


def main():
    blocks = load_blocks()
    known_types = {b["type"] for b in blocks}
    print(f"🔄 Generating public catalog artifacts ({len(blocks)} atoms)")

    write_json("spec.json", gen_spec(blocks))
    write_json("atoms/index.json", gen_compact_index(blocks))
    write_json("runbooks/index.json", gen_runbooks_index(known_types))

    # Explicit allowlist — internal working prompts stay unpublished
    PUBLISHED_PROMPTS = ["a2ui-builder-gem.md", "training-md-gem.md"]
    prompts_dir = os.path.join(ROOT, "prompts")
    for name in PUBLISHED_PROMPTS:
        if not os.path.isfile(os.path.join(prompts_dir, name)):
            continue
        out = os.path.join(PUBLIC, "prompts", name)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        shutil.copyfile(os.path.join(prompts_dir, name), out)
        print(f"  ✅ public/prompts/{name} (copied from prompts/)")

    gdm_out = os.path.join(PUBLIC, "catalogue", "gdm-v0.2.json")
    os.makedirs(os.path.dirname(gdm_out), exist_ok=True)
    shutil.copyfile(GDM_SPEC, gdm_out)
    print("  ✅ public/catalogue/gdm-v0.2.json (copied from spec/)")


if __name__ == "__main__":
    main()
