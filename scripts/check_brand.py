#!/usr/bin/env python3
"""check_brand — brand consistency as a build gate; rebrand as a manifest edit.

project.yaml `brand:` is the token source of truth + a USAGE MAP (`surfaces`, each declaring
which tokens it `carries`). This asserts every surface actually contains its tokens, and that
no `retired` (old-brand) string lingers anywhere in the surfaces. So a rebrand is:
  1. change the token(s) in project.yaml brand:
  2. move the old value(s) into brand.retired
  3. run this — it FAILS every surface still carrying the old token and confirms the new one.
The failures ARE the rebrand checklist; green means the rename is complete + consistent.

Wired into catalog-rebuild verify. Exit non-zero on any drift.
"""
import os
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BASE = os.path.join(ROOT, "project.yaml")
OVERLAY = os.path.join(ROOT, "ops", "project-ops.yaml")   # private tier — where brand lives


def _brand():
    """brand: lives in the private overlay (ops/project-ops.yaml), merged over the tracked
    base — same layering ops.py._manifest() does. Overlay wins."""
    for path in (OVERLAY, BASE):                          # overlay first (precedence)
        if os.path.exists(path):
            b = (yaml.safe_load(open(path)) or {}).get("brand")
            if b:
                return b
    return {}


def main():
    brand = _brand()
    if not brand:
        raise SystemExit("✗ no brand: block found (expected in ops/project-ops.yaml)")
    tokens = {k: brand[k] for k in ("name", "wordmark", "tagline", "descriptor")
              if isinstance(brand.get(k), str)}
    surfaces = brand.get("surfaces") or []
    retired = [r for r in (brand.get("retired") or []) if r]

    errors = []
    for s in surfaces:
        path = os.path.join(ROOT, s["path"])
        if not os.path.exists(path):
            errors.append(f"{s['path']}: declared brand surface missing from disk")
            continue
        text = open(path, encoding="utf-8", errors="ignore").read()
        for tok in s.get("carries", []):
            val = tokens.get(tok)
            if val is None:
                errors.append(f"{s['path']}: carries unknown token '{tok}'")
            elif val not in text:
                errors.append(f"{s['path']}: missing brand token {tok} = {val!r}")
        # a rebrand must purge retired strings from every surface
        for old in retired:
            if old in text:
                errors.append(f"{s['path']}: still contains RETIRED brand string {old!r}")

    if errors:
        print("✗ check_brand FAILED (the rebrand checklist):")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    print(f"✓ check_brand: {len(surfaces)} surfaces consistent with {len(tokens)} tokens; "
          f"{len(retired)} retired string(s) absent.")


if __name__ == "__main__":
    main()
