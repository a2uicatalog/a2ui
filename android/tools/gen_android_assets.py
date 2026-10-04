#!/usr/bin/env python3
"""Write the a2ui-atoms library's assets into OUT_DIR (run by Gradle, generateA2uiAssets).

  atoms.json            every atom in atoms/schema.yaml: name, pack, field keys.
                        The library registers each one, because androidx.a2ui throws on
                        an unregistered type.
  renderer-bundle.html  public/surfaces/mcp-apps/renderer-bundle.html, byte for byte.
                        The bridge paints atoms into it via window._A2UI_PAINT.

Both come from the checkout the library is built from, so the AAR always matches the
catalogue and renderer of that commit.
"""
import json
import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]          # a2ui-catalogue/


def main(out_dir: str) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    blocks = yaml.safe_load(open(ROOT / "atoms" / "schema.yaml"))["blocks"]
    packs = yaml.safe_load(open(ROOT / "atoms" / "atom-packs.yaml"))
    pack_of = {atom: pack for pack, atoms in packs.items() for atom in atoms}
    atoms = []
    for b in blocks:
        fields = b.get("fields") or {}
        atoms.append({"name": b["type"], "pack": pack_of.get(b["type"], "unpacked"),
                      "fields": sorted(fields) if isinstance(fields, dict) else []})
    (out / "atoms.json").write_text(json.dumps(atoms, separators=(",", ":")))
    shutil.copyfile(ROOT / "public" / "surfaces" / "mcp-apps" / "renderer-bundle.html",
                    out / "renderer-bundle.html")
    print(f"a2ui-atoms assets: {len(atoms)} atoms, renderer bundle -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
