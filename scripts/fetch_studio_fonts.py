#!/usr/bin/env python3
"""Fetches, verifies and vendors the studio typefaces: four SIL OFL 1.1 variable fonts whose axes the motion atoms animate
(motion_text `font` + `vary`, motion_object3d 3D type). See apps-script-surface/gas-wired-renderer/atoms_studio.gs (_MO_VFONTS)
for what each axis does, and THIRD-PARTY-NOTICES.md for provenance.

Each file is the Google Fonts latin subset (woff2, all variable axes kept) at a pinned, versioned fonts.gstatic.com URL, checked
against a sha256 computed when it was pinned (2026-10-03). A versioned gstatic URL never legitimately changes content; a mismatch
means stop and investigate, not re-pin. The licence text is taken from the font's own directory in github.com/google/fonts.

Same discipline as scripts/fetch_threejs.py: pinned source + hash, never a live fetch trusted at commit time.

    python3 scripts/fetch_studio_fonts.py           # download + verify + (re)write public/vendors/fonts/
    python3 scripts/fetch_studio_fonts.py --check   # verify the committed files still match the pins
"""
import argparse
import hashlib
import os
import sys
import urllib.request

UA = {"User-Agent": "a2ui-fetch-studio-fonts (https://github.com/a2uicatalog/a2ui)"}
ROOT = os.path.join(os.path.dirname(__file__), "..")
VENDOR_DIR = os.path.join(ROOT, "public", "vendors", "fonts")

# Published-file integrity pins (sha256 of each exact versioned gstatic file, computed 2026-10-03). Named *_FONT_SHA256 so the
# pre-push audit's allowlist can recognise them as public checksums, same as THREEJS_SHA256 / LDRAW_SHA256.
RECURSIVE_FONT_SHA256 = "14ef41458aeba3d812284c4e32ee956910b88845062c61e91cc8578c2b78bccb"
ANYBODY_FONT_SHA256 = "041c675622919a7a380210851ecb00be81458a886441dab13269e1339b492354"
NABLA_FONT_SHA256 = "a065b5e6e2878ec6b9f90c5b45ca3fd9983f8300deaf7d0b32e5788aea7eaa29"
FRAUNCES_FONT_SHA256 = "7e744849028e2219e2aa1bc467dc4032980dc4487c9c3da3010081cd72d3b103"

# name -> (font url, font sha256, licence url, upstream project)
FONTS = {
    "recursive": ("https://fonts.gstatic.com/s/recursive/v44/8vIK7wMr0mhh-RQChyHuE2Za.woff2",
                  RECURSIVE_FONT_SHA256,
                  "https://raw.githubusercontent.com/google/fonts/main/ofl/recursive/OFL.txt", "https://github.com/arrowtype/recursive"),
    "anybody": ("https://fonts.gstatic.com/s/anybody/v13/VuJxdNvK2Ib2ppdWSKHdOQ.woff2",
                ANYBODY_FONT_SHA256,
                "https://raw.githubusercontent.com/google/fonts/main/ofl/anybody/OFL.txt", "https://github.com/Etcetera-Type-Co/Anybody"),
    "nabla": ("https://fonts.gstatic.com/s/nabla/v17/j8_l6-LI0Lvpe5kWu--kFw.woff2",
              NABLA_FONT_SHA256,
              "https://raw.githubusercontent.com/google/fonts/main/ofl/nabla/OFL.txt", "https://github.com/justvanrossum/nabla"),
    "fraunces": ("https://fonts.gstatic.com/s/fraunces/v38/6NUV8FyLNQOQZAnv9ZwIlOk.woff2",
                 FRAUNCES_FONT_SHA256,
                  "https://raw.githubusercontent.com/google/fonts/main/ofl/fraunces/OFL.txt", "https://github.com/undercasetype/Fraunces"),
}


def _get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read()


def vendor():
    os.makedirs(VENDOR_DIR, exist_ok=True)
    for name, (url, sha, lic_url, _proj) in FONTS.items():
        data = _get(url)
        got = hashlib.sha256(data).hexdigest()
        if got != sha:
            sys.exit("%s: checksum mismatch (expected %s, got %s) -- investigate before re-pinning" % (name, sha, got))
        lic = _get(lic_url)
        if b"SIL OPEN FONT LICENSE" not in lic:
            sys.exit("%s: licence file does not look like the SIL OFL -- stop and check" % name)
        with open(os.path.join(VENDOR_DIR, name + ".woff2"), "wb") as f:
            f.write(data)
        with open(os.path.join(VENDOR_DIR, name + "-OFL.txt"), "wb") as f:
            f.write(lic)
        print("%-10s %7d bytes  sha256 ok" % (name, len(data)))


def check():
    bad = 0
    for name, (_url, sha, _l, _p) in FONTS.items():
        path = os.path.join(VENDOR_DIR, name + ".woff2")
        ok = os.path.isfile(path) and hashlib.sha256(open(path, "rb").read()).hexdigest() == sha
        ok = ok and os.path.isfile(os.path.join(VENDOR_DIR, name + "-OFL.txt"))
        print("%-10s %s" % (name, "ok" if ok else "MISSING OR CHANGED"))
        bad += not ok
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    check() if ap.parse_args().check else vendor()
