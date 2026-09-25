#!/usr/bin/env python3
"""Downloads and verifies the pinned LDraw parts library (spec/brick-parts-v0.1.md section 0/10).

Pinned release: library.ldraw.org "complete.zip", as published 2026-08-31.
LDRAW_SHA256=d2a695868ed2b3957c45b022a6451908edab22cc043179dd61d18dd382b35e11 (a public integrity check on an
open, CC BY licensed download — see ops/pre_push_audit.py's ALLOW list for why this isn't secret-shaped)

The library itself (CC BY 4.0 / 2.0, ~24k parts, ~145MB zipped) is NOT committed to either repo — this script
re-fetches it into a local cache outside version control, the same way node_modules or a venv is rebuilt rather
than carried. Only the curated, baked output (public/parts/) is committed.

Usage:
    python3 scripts/ldraw/fetch_library.py            # fetch + verify + unzip into scripts/ldraw/_ldraw_cache/
    LDRAW_DIR=/other/path python3 scripts/ldraw/fetch_library.py --check   # verify an existing extraction only
"""
import argparse
import hashlib
import os
import sys
import urllib.request
import zipfile

URL = "https://library.ldraw.org/library/updates/complete.zip"
LDRAW_SHA256 = "d2a695868ed2b3957c45b022a6451908edab22cc043179dd61d18dd382b35e11"
CACHE_DIR = os.path.join(os.path.dirname(__file__), "_ldraw_cache")
ZIP_PATH = os.path.join(CACHE_DIR, "complete.zip")
EXTRACT_DIR = os.path.join(CACHE_DIR, "ldraw")


def _hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch():
    os.makedirs(CACHE_DIR, exist_ok=True)
    if os.path.isfile(ZIP_PATH) and _hash(ZIP_PATH) == LDRAW_SHA256:
        print("cached zip already matches pinned sha256, skipping download")
    else:
        print("downloading %s ..." % URL)
        urllib.request.urlretrieve(URL, ZIP_PATH)
        got = _hash(ZIP_PATH)
        if got != LDRAW_SHA256:
            os.remove(ZIP_PATH)
            sys.exit("checksum mismatch: expected %s, got %s (library.ldraw.org may have republished — "
                      "if this is expected, update LDRAW_SHA256 in this file deliberately, not silently)" % (LDRAW_SHA256, got))
        print("sha256 verified:", got)
    if os.path.isdir(EXTRACT_DIR) and os.path.isfile(os.path.join(EXTRACT_DIR, "LDConfig.ldr")):
        print("already extracted at", EXTRACT_DIR)
        return
    print("extracting to", CACHE_DIR)
    with zipfile.ZipFile(ZIP_PATH) as z:
        z.extractall(CACHE_DIR)
    if not os.path.isfile(os.path.join(EXTRACT_DIR, "LDConfig.ldr")):
        sys.exit("extraction did not produce %s — zip layout changed?" % EXTRACT_DIR)
    print("ok:", EXTRACT_DIR)


def check():
    root = os.environ.get("LDRAW_DIR") or EXTRACT_DIR
    cfg = os.path.join(root, "LDConfig.ldr")
    if not os.path.isfile(cfg):
        sys.exit("no LDConfig.ldr under %s" % root)
    n = sum(len(f) for _, _, f in os.walk(os.path.join(root, "parts")))
    print("LDraw library present at %s (%d files under parts/)" % (root, n))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="verify an existing extraction, don't download")
    args = ap.parse_args()
    check() if args.check else fetch()
