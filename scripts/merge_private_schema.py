#!/usr/bin/env python3
"""
Splice the private-visibility atom blocks into atoms/schema.yaml for the
duration of a catalog-rebuild-full run, then restore the public-only file.

Real boundary, not a render-time filter: visibility:private atom
DEFINITIONS used to live in this repo's own atoms/schema.yaml (public repo,
public GitHub remote) — the Cloudflare Access gate on full.a2uicatalog.ai
protected the *rendered* output, but the source was one `git clone` away
regardless of that gate. Fixed 2026-07-19: private atom blocks now live in
a2ui-private/private-atoms/private-schema-blocks.yaml (private repo) and
are merged into schema.yaml ONLY here, ONLY for the duration of the full
build, then removed again. No new dependency, no re-parse of the whole
schema (which would risk the comment/formatting loss a yaml round-trip
causes on a large hand-maintained file) — pure text splice, since the two
private blocks happen to be a clean trailing slice of the file.

Usage (called by ops/project-ops.yaml's catalog-rebuild-full, in order):
  python3 scripts/merge_private_schema.py --merge     # before the A2UI_CATALOG_FULL=1 steps
  python3 scripts/merge_private_schema.py --restore   # immediately after, before anything commits

--restore is also safe to call speculatively (no-op) if --merge was never
run, so a failed/interrupted build can't leave the public file in the
merged state.
"""
import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
SCHEMA = ROOT / "atoms" / "schema.yaml"
BACKUP = ROOT / "atoms" / ".schema.yaml.public-only.bak"
PRIVATE_BLOCKS = Path.home() / "a2ui-private" / "private-atoms" / "private-schema-blocks.yaml"


def merge():
    if BACKUP.exists():
        print("merge: backup already exists — a previous run didn't restore. "
              "Refusing to merge again (would double-append). Run --restore first.",
              file=sys.stderr)
        sys.exit(1)
    if not PRIVATE_BLOCKS.exists():
        print(f"merge: {PRIVATE_BLOCKS} not found — nothing to merge, leaving schema.yaml as-is.",
              file=sys.stderr)
        return
    shutil.copy2(SCHEMA, BACKUP)
    public_text = SCHEMA.read_text(encoding="utf-8")
    private_text = PRIVATE_BLOCKS.read_text(encoding="utf-8")
    if not public_text.endswith("\n"):
        public_text += "\n"
    SCHEMA.write_text(public_text + private_text, encoding="utf-8")
    print(f"merge: spliced {PRIVATE_BLOCKS.name} into atoms/schema.yaml "
          f"(backup at {BACKUP.name})")


def restore():
    if not BACKUP.exists():
        print("restore: no backup found — nothing to restore (merge was never run, or "
              "restore already happened). No-op.", file=sys.stderr)
        return
    shutil.move(str(BACKUP), str(SCHEMA))
    print("restore: atoms/schema.yaml restored to public-only state")


def main():
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--merge", action="store_true")
    g.add_argument("--restore", action="store_true")
    args = p.parse_args()
    merge() if args.merge else restore()


if __name__ == "__main__":
    main()
