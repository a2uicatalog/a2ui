#!/usr/bin/env python3
"""Write the a2ui-atoms library's assets into OUT_DIR (run by Gradle, generateA2uiAssets).

  atoms.json            the atoms in atoms/schema.yaml: name, pack, field keys. The
                        library registers each one, because androidx.a2ui throws on an
                        unregistered type. With --stable-only (release builds, the ones
                        that get published) preview atoms are left out: preview atoms are
                        repo-only and every publication pipeline filters them, and a Maven
                        release can never be withdrawn. An unregistered type still reaches
                        the app safely through A2uiAtomicCatalog.adapt()'s placeholder.
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
                      "fields": sorted(fields) if isinstance(fields, dict) else []})
    (out / "atoms.json").write_text(json.dumps(atoms, separators=(",", ":")))
    shutil.copyfile(ROOT / "public" / "surfaces" / "mcp-apps" / "renderer-bundle.html",
                    out / "renderer-bundle.html")
    kind = "stable" if stable_only else "all"
    print(f"a2ui-atoms assets: {len(atoms)} atoms ({kind}), renderer bundle -> {out}")


if __name__ == "__main__":
    main(sys.argv[1], stable_only="--stable-only" in sys.argv[2:])
