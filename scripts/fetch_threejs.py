#!/usr/bin/env python3
"""Fetches, verifies and vendors a pinned Three.js release -- the MIT-licensed render-appearance proof-of-concept
(see /home/ck/.claude/plans/cozy-forging-newt.md, Track B "Render appearance" schema gap; provenance recorded in
THIRD-PARTY-NOTICES.md).

Pinned release: three@0.186.1, the npm registry's "latest" dist-tag as of 2026-09-29 (published 2026-09-24).
THREEJS_SHA256 below is independently computed from the downloaded tarball with Python's own hashlib -- not just
copied from the registry metadata -- and cross-checked at fetch time against npm's own published dist.shasum
(sha1) and dist.integrity (sha512) for this exact tarball, so three independent hashes agree, not one.

Extracts only the files this repo actually vendors (not the whole ~4.6MB package -- no CJS/WebGPU/TSL builds, no
examples/ tree beyond the one OrbitControls add-on the demo needs). `three.module.js` re-exports its actual
implementation from a sibling `./three.core.js` (this version split the build across two files for WebGPU
tree-shaking) -- both are needed, or the module import silently 404s and the whole script never runs (confirmed
the hard way: a headless-Chromium check against a first version of this vendoring that only had three.module.js
loaded the page with zero console output and zero exceptions, because a failed static import aborts module
evaluation before the script's own error listeners even register -- see the demo's own render() never firing):
  package/LICENSE                                  -> public/vendors/threejs/LICENSE
  package/build/three.module.js                    -> public/vendors/threejs/three.module.js
  package/build/three.core.js                      -> public/vendors/threejs/three.core.js
  package/examples/jsm/controls/OrbitControls.js   -> public/vendors/threejs/addons/controls/OrbitControls.js

Follows the same discipline as scripts/ldraw/fetch_library.py: a pinned version + a hardcoded hash checked
against the actual download, never a live fetch trusted at commit time. Unlike that script's huge (~145MB)
external cache (never committed), three.js's needed files (~700KB total) ARE committed to the repo here -- same
precedent as public/vendors/pdfjs/pdf.min.mjs (a real binary-format parser, out of scope to reimplement, wholesale
vendored rather than recompiled). Re-run this script only to re-verify the committed files, or to bump the pin
deliberately (update VERSION + THREEJS_SHA256 together, never one without the other).

Usage:
    python3 scripts/fetch_threejs.py             # download + verify + (re)write public/vendors/threejs/
    python3 scripts/fetch_threejs.py --check      # verify the committed vendored files still match the pin
"""
import argparse
import hashlib
import os
import sys
import tarfile
import urllib.request

VERSION = "0.186.1"
URL = "https://registry.npmjs.org/three/-/three-%s.tgz" % VERSION
# library.ldraw.org-style UA requirement doesn't apply to registry.npmjs.org, but a real client identifier is
# sent anyway, per this repo's own fetch_library.py norm of never sending a spoofed/blank one.
UA_HEADERS = {"User-Agent": "a2ui-fetch-threejs (https://github.com/a2uicatalog/a2ui)"}
THREEJS_SHA256 = "8cd068708ea44f2c73c944b1cead2ba2f0d5c15c8fc194e5700f4e4f4a033fe7"
# Cross-check only -- registry.npmjs.org's own published hashes for the SAME tarball (not re-derived from
# THREEJS_SHA256, fetched independently from https://registry.npmjs.org/three/latest at pin time 2026-09-29):
NPM_SHA1 = "6d50f70c2c437f844179bbb56d6f5b774e1ca38a"
NPM_SHA512_B64 = "blFeqb49wRCSGUGj7gtpfnSGHy2lwDk94RhUmS1c/hTby70kvChbWpkJ4Pm1390LqzzvTmzgXKHPEafJwCb8jA=="

ROOT = os.path.join(os.path.dirname(__file__), "..")
VENDOR_DIR = os.path.join(ROOT, "public", "vendors", "threejs")
CACHE_DIR = os.path.join(os.path.dirname(__file__), "_threejs_cache")
TGZ_PATH = os.path.join(CACHE_DIR, "three-%s.tgz" % VERSION)

# tarball member path -> vendored destination, relative to VENDOR_DIR
FILES = {
    "package/LICENSE": "LICENSE",
    "package/build/three.module.js": "three.module.js",
    "package/build/three.core.js": "three.core.js",
    "package/examples/jsm/controls/OrbitControls.js": "addons/controls/OrbitControls.js",
    # Procedural studio-lighting environment (PMREMGenerator input) for the design page's Three.js
    # environment-map work (2026-09-29) -- real reflections on chrome/metal, real refraction on trans-clear
    # parts. No external HDRI asset/licensing needed: RoomEnvironment builds its scene from primitives only.
    "package/examples/jsm/environments/RoomEnvironment.js": "addons/environments/RoomEnvironment.js",
    # Postprocessing (2026-09-30, threejs-viewer-feature-survey-and-priority item 2): GTAO (ambient
    # occlusion). Full real dependency closure (traced by reading every file's own import list, not guessed)
    # -- EffectComposer/RenderPass/OutputPass/ShaderPass/MaskPass/Pass are the composer scaffolding every pass
    # needs; GTAOPass is the actual effect; CopyShader/OutputShader/GTAOShader/PoissonDenoiseShader/
    # SimplexNoise are its own shader-level dependencies. NOT OutlinePass (item 3, click-to-inspect's
    # highlight): OutlinePass masks whole scene OBJECTS, which doesn't map onto ONE instance inside an
    # InstancedMesh without fragile camera-layer-toggling workarounds (it would outline every instance in
    # that bucket, not just the clicked one) -- used a simpler, well-established inflated-backface-shell
    # technique instead, which needs no extra vendoring at all.
    "package/examples/jsm/postprocessing/EffectComposer.js": "addons/postprocessing/EffectComposer.js",
    "package/examples/jsm/postprocessing/RenderPass.js": "addons/postprocessing/RenderPass.js",
    "package/examples/jsm/postprocessing/Pass.js": "addons/postprocessing/Pass.js",
    "package/examples/jsm/postprocessing/ShaderPass.js": "addons/postprocessing/ShaderPass.js",
    "package/examples/jsm/postprocessing/MaskPass.js": "addons/postprocessing/MaskPass.js",
    "package/examples/jsm/postprocessing/OutputPass.js": "addons/postprocessing/OutputPass.js",
    "package/examples/jsm/postprocessing/GTAOPass.js": "addons/postprocessing/GTAOPass.js",
    "package/examples/jsm/shaders/CopyShader.js": "addons/shaders/CopyShader.js",
    "package/examples/jsm/shaders/OutputShader.js": "addons/shaders/OutputShader.js",
    "package/examples/jsm/shaders/GTAOShader.js": "addons/shaders/GTAOShader.js",
    "package/examples/jsm/shaders/PoissonDenoiseShader.js": "addons/shaders/PoissonDenoiseShader.js",
    "package/examples/jsm/math/SimplexNoise.js": "addons/math/SimplexNoise.js",
}


def _hash(path, algo="sha256"):
    h = hashlib.new(algo)
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _hash_b64(path, algo):
    import base64
    h = hashlib.new(algo)
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return base64.b64encode(h.digest()).decode()


def _download():
    os.makedirs(CACHE_DIR, exist_ok=True)
    if os.path.isfile(TGZ_PATH) and _hash(TGZ_PATH) == THREEJS_SHA256:
        print("cached tarball already matches pinned sha256, skipping download")
        return
    print("downloading %s ..." % URL)
    req = urllib.request.Request(URL, headers=UA_HEADERS)
    with urllib.request.urlopen(req, timeout=60) as resp, open(TGZ_PATH, "wb") as out:
        for chunk in iter(lambda: resp.read(1 << 20), b""):
            out.write(chunk)
    got = _hash(TGZ_PATH)
    if got != THREEJS_SHA256:
        os.remove(TGZ_PATH)
        sys.exit("checksum mismatch: expected %s, got %s (a published npm tarball for an exact version string "
                  "never legitimately changes -- investigate before updating THREEJS_SHA256, don't just paper "
                  "over it)" % (THREEJS_SHA256, got))
    got_sha1 = _hash(TGZ_PATH, "sha1")
    got_sha512 = _hash_b64(TGZ_PATH, "sha512")
    if got_sha1 != NPM_SHA1 or got_sha512 != NPM_SHA512_B64:
        sys.exit("downloaded tarball matches the pinned sha256 but NOT npm's own published sha1/sha512 for "
                  "three@%s -- registry metadata and content have drifted apart, stop and investigate" % VERSION)
    print("sha256 verified:", got, "(sha1 + sha512 cross-checked against npm registry metadata too)")


def vendor():
    _download()
    os.makedirs(VENDOR_DIR, exist_ok=True)
    with tarfile.open(TGZ_PATH) as tf:
        for member, dest_rel in FILES.items():
            f = tf.extractfile(member)
            if f is None:
                sys.exit("tarball layout changed: %s not found in three@%s -- pin update needs re-review, "
                          "not a blind re-run" % (member, VERSION))
            dest = os.path.join(VENDOR_DIR, dest_rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "wb") as out:
                out.write(f.read())
            print("vendored", os.path.relpath(dest, ROOT))
    print("ok:", VENDOR_DIR)


def check():
    if not os.path.isfile(TGZ_PATH) or _hash(TGZ_PATH) != THREEJS_SHA256:
        _download()
    with tarfile.open(TGZ_PATH) as tf:
        for member, dest_rel in FILES.items():
            want = tf.extractfile(member).read()
            dest = os.path.join(VENDOR_DIR, dest_rel)
            if not os.path.isfile(dest):
                sys.exit("missing vendored file: %s (run `python3 scripts/fetch_threejs.py` to vendor it)" % dest)
            with open(dest, "rb") as fh:
                got = fh.read()
            if got != want:
                sys.exit("%s does not match the pinned tarball's %s -- re-run `python3 scripts/fetch_threejs.py`"
                          % (os.path.relpath(dest, ROOT), member))
    print("all vendored three.js@%s files match the pinned, verified tarball" % VERSION)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                     help="verify the committed vendored files match the pin, don't re-vendor")
    args = ap.parse_args()
    check() if args.check else vendor()
