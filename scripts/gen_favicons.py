#!/usr/bin/env python3
"""Generate the browser icon set from the source logo.

Committed as a GENERATOR rather than five committed binaries, because the
interesting part is the CROP and it needs to be reproducible: a favicon is read
at 16-32px, where "A2UI CATALOG" is a smear rather than a wordmark. The tab icon
is therefore the orbital MARK alone, cropped away from the text, keeping the
gradient so it still reads as the same brand.

Verified by rendering the 32px result and looking at it — two earlier crops were
rejected for catching the top of the lettering, which at tab size reads as dirt
along the bottom edge rather than as type.

Run:  python3 scripts/gen_favicons.py     (after changing the source logo)
"""
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).absolute().parent.parent
SRC = ROOT / "public" / "avatar" / "a2ui-chat-app.png"
OUT = ROOT / "public"

# Crop window on the source, as fractions. Tuned by eye at 32px, not derived.
SIDE_F, TOP_F = 0.40, 0.13


def main():
    if not SRC.exists():
        sys.exit(f"source logo missing: {SRC}")
    src = Image.open(SRC).convert("RGB")
    w, h = src.size
    side = int(h * SIDE_F)
    left, top = (w - side) // 2, int(h * TOP_F)
    mark = src.crop((left, top, left + side, top + side))

    # .ico carries 16/32/48 in one file. It must exist at /favicon.ico even with
    # a <link> tag present — browsers request that path implicitly.
    mark.resize((256, 256), Image.LANCZOS).save(
        OUT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    for name, px in (("apple-touch-icon.png", 180), ("icon-192.png", 192), ("icon-512.png", 512)):
        mark.resize((px, px), Image.LANCZOS).save(OUT / name)
        print(f"  wrote {name} ({px}x{px})")
    print("  wrote favicon.ico (16/32/48)")


if __name__ == "__main__":
    main()
