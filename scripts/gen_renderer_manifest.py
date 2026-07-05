#!/usr/bin/env python3
"""gen_renderer_manifest — extract what the wired renderer ACTUALLY implements.

Scans apps-script-surface/gas-wired-renderer/*.gs for `_RENDERERS['<type>']`
registrations — the ground truth of which atoms the renderer can render — and emits
a manifest that `scripts/check_core.py` validates against `atoms/atom-packs.yaml`.

This closes the loop: the gate no longer runs against a hand-written test manifest, it
runs against the renderer's real atom surface. It also reports the file→pack mapping so
building the LEAN renderer is mechanical — you know which .gs files carry core vs which
carry a single pack.

Emits (to stdout, or --out <path>):
  {
    "atoms":  [ ...every implemented type... ],       # for check_core
    "packs":  [ ...every bucket those atoms touch... ],# current renderer = fat = all packs
    "by_file": { "atoms_nav.gs": ["nav_bar", ...], ... },
    "file_pack": { "atoms_nav.gs": {"nav": 4, "core": 3}, ... }  # which packs each file feeds
  }

Reports (to stderr) any drift: atoms implemented but not in the partition, or in the
partition but not implemented. Exit non-zero on drift so a schema/renderer split can't
rot silently.
"""
import json
import os
import re
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RENDERER = os.path.join(ROOT, "apps-script-surface", "gas-wired-renderer")
PACKS = os.path.join(ROOT, "atoms", "atom-packs.yaml")

REG = re.compile(r"_RENDERERS\['([a-z0-9_]+)'\]")


def scan():
    """type -> file, and file -> [types], from the renderer sources."""
    by_file, type_file = {}, {}
    for fn in sorted(os.listdir(RENDERER)):
        if not fn.endswith(".gs"):
            continue
        path = os.path.join(RENDERER, fn)
        types = sorted(set(REG.findall(open(path, encoding="utf-8", errors="ignore").read())))
        if types:
            by_file[fn] = types
            for t in types:
                type_file.setdefault(t, fn)   # first file wins if duplicated
    return by_file, type_file


def main():
    out_path = None
    if "--out" in sys.argv:
        out_path = sys.argv[sys.argv.index("--out") + 1]

    part = yaml.safe_load(open(PACKS))
    home = {a: b for b, atoms in part.items() for a in atoms}   # type -> pack

    by_file, type_file = scan()
    impl = set(type_file)
    mapped = set(home)

    # which packs each file feeds (a file may carry atoms from >1 bucket)
    file_pack = {}
    for fn, types in by_file.items():
        counts = {}
        for t in types:
            b = home.get(t, "UNMAPPED")
            counts[b] = counts.get(b, 0) + 1
        file_pack[fn] = dict(sorted(counts.items(), key=lambda kv: -kv[1]))

    # `core`/`promote` are always-on in the lean renderer, not declarable packs — the
    # manifest's `packs` list is only the on-demand buckets the renderer reaches into.
    ALWAYS = ("a2ui-atoms-v1",)
    manifest = {
        "atoms": sorted(impl),
        "packs": sorted({home[t] for t in impl if t in home and home[t] not in ALWAYS}),
        "by_file": by_file,
        "file_pack": file_pack,
    }
    text = json.dumps(manifest, indent=2)
    if out_path:
        open(out_path, "w").write(text + "\n")
        print(f"wrote {out_path} — {len(impl)} atoms, {len(manifest['packs'])} packs, "
              f"{len(by_file)} source files")
    else:
        print(text)

    # drift report → stderr, non-zero exit
    unmapped = sorted(impl - mapped)     # renderer has it, partition doesn't
    missing = sorted(mapped - impl)      # partition has it, renderer doesn't
    if unmapped:
        print(f"\n✗ {len(unmapped)} implemented atom(s) NOT in atom-packs.yaml "
              f"(add them): {', '.join(unmapped)}", file=sys.stderr)
    if missing:
        print(f"\n⚠ {len(missing)} partitioned atom(s) NOT implemented by the renderer "
              f"(schema-only / aliases): {', '.join(missing)}", file=sys.stderr)
    if unmapped:
        sys.exit(1)


if __name__ == "__main__":
    main()
