#!/usr/bin/env python3
"""Write the atomic-catalog library's assets into OUT_DIR (run by Gradle, generateA2uiAssets).

  atoms.json            the atoms in atoms/schema.yaml: name, pack, field keys, and which
                        fields take a single string (see scalar_fields). The
                        library registers each one, because androidx.a2ui throws on an
                        unregistered type. With --stable-only (release builds, the ones
                        that get published) preview atoms are left out: preview atoms are
                        repo-only and every publication pipeline filters them, and a Maven
                        release can never be withdrawn. An unregistered type still reaches
                        the app safely through A2uiAtomicCatalog.adapt()'s placeholder.
  renderer-bundle.html  public/surfaces/mcp-apps/renderer-bundle.html, byte for byte.
                        The bridge paints atoms into it via window._A2UI_PAINT.
  basic-icons.json      atoms/basic-catalog-icons.json: path data for the Basic Catalog
                        Icon's built-in names (shared with the web renderer).

Both come from the checkout the library is built from, so the AAR always matches the
catalogue and renderer of that commit.
"""
import json
import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]          # a2ui-catalogue/


def scalar_fields(fields: dict) -> list:
    """The fields that take one string: free text or one value of an enum, read from the schema's
    description of each ("string ...", or a quoted choice like '"glow" | "grid"'). A ChoicePicker bound
    to one of these writes a one-item list (["grid"]); the bridge unwraps it to "grid" for these fields
    only, so a real list field (blocks, items) holding a single entry is never flattened."""
    out = []
    for name, desc in fields.items():
        d = str(desc).lstrip()
        if not (d.startswith('"') or d.startswith("string")):
            continue
        if "array" in d[:40] or "[" in d[:40]:   # e.g. 'string | [x1,y1,x2,y2]': may legitimately be a list
            continue
        out.append(name)
    return sorted(out)


def main(out_dir: str, stable_only: bool = False) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    blocks = yaml.safe_load(open(ROOT / "atoms" / "schema.yaml"))["blocks"]
    packs = yaml.safe_load(open(ROOT / "atoms" / "atom-packs.yaml"))
    pack_of = {atom: pack for pack, atoms in packs.items() for atom in atoms}
    atoms = []
    for b in blocks:
        if stable_only and b.get("stage") == "preview":
            continue
        fields = b.get("fields") or {}
        atoms.append({"name": b["type"], "pack": pack_of.get(b["type"], "unpacked"),
                      "fields": sorted(fields) if isinstance(fields, dict) else [],
                      "scalars": scalar_fields(fields) if isinstance(fields, dict) else []})
    (out / "atoms.json").write_text(json.dumps(atoms, separators=(",", ":")))
    shutil.copyfile(ROOT / "public" / "surfaces" / "mcp-apps" / "renderer-bundle.html",
                    out / "renderer-bundle.html")
    # the Basic Catalog Icon's 59 built-in names, the same table the web renderer uses
    shutil.copyfile(ROOT / "atoms" / "basic-catalog-icons.json", out / "basic-icons.json")
    kind = "stable" if stable_only else "all"
    print(f"atomic-catalog assets: {len(atoms)} atoms ({kind}), renderer bundle -> {out}")


if __name__ == "__main__":
    main(sys.argv[1], stable_only="--stable-only" in sys.argv[2:])
