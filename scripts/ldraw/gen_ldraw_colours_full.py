#!/usr/bin/env python3
"""Builds public/bricksdemo/ldraw_colours_full.json -- the REAL, FULL LDraw colour table (all ~322 codes from
the pinned LDConfig.ldr), including material-appearance fields (ALPHA transparency, CHROME/METAL/PEARLESCENT/
RUBBER/glitter finish flags) that atoms_brick.gs's small 17-entry LDRAW_COLOURS subset does not carry at all.

Why this exists separately from atoms_brick.gs's own colour table: that table is deliberately small (only the
curated demo/sketch palette), and has no concept of transparency or finish -- the live hand-rolled shader can't
render them anyway. This is for the Three.js render-appearance integration (Brick Design Lab's "View in
Three.js" toggle), which needs the REAL colour a curated part or imported set can carry (any of the ~322 real
codes), not just the small picker palette, and needs the real finish data to pick a physically-plausible
material (MeshPhysicalMaterial transmission/clearcoat for trans, metalness for chrome/metal, etc.).

Parses the SAME real LDConfig.ldr line format resolve.py's ColourTable already parses for CODE/VALUE/EDGE,
extended here with ALPHA/LUMINANCE/finish keywords -- real LDraw data, not guessed or RGB-matched.

Usage: python3 scripts/ldraw/gen_ldraw_colours_full.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LDCONFIG = ROOT / "scripts" / "ldraw" / "_ldraw_cache" / "ldraw" / "LDConfig.ldr"
OUT = ROOT / "public" / "bricksdemo" / "ldraw_colours_full.json"

LINE_RE = re.compile(
    r"^0\s+!COLOUR\s+(\S+)\s+CODE\s+(\d+)\s+VALUE\s+(#[0-9A-Fa-f]{6})\s+EDGE\s+(#[0-9A-Fa-f]{6})(.*)$")
ALPHA_RE = re.compile(r"\bALPHA\s+(\d+)\b")
LUMINANCE_RE = re.compile(r"\bLUMINANCE\s+(\d+)\b")
FINISH_KEYWORDS = ["CHROME", "PEARLESCENT", "RUBBER", "METAL"]  # checked in this order; METAL last (METALLIC-
                                                                  # named colours like Metallic_Gold don't carry
                                                                  # the bare METAL keyword, only true chrome/metal
                                                                  # finishes do -- real data, not name-guessed)


def parse():
    out = {}
    for line in LDCONFIG.read_text(encoding="utf-8", errors="replace").splitlines():
        m = LINE_RE.match(line.strip())
        if not m:
            continue
        name, code, rgb, edge, rest = m.groups()
        code = int(code)
        alpha_m = ALPHA_RE.search(rest)
        lum_m = LUMINANCE_RE.search(rest)
        finish = None
        if "MATERIAL GLITTER" in rest:
            finish = "glitter"
        elif "MATERIAL SPECKLE" in rest:
            finish = "speckle"
        else:
            for kw in FINISH_KEYWORDS:
                if re.search(r"\b%s\b" % kw, rest):
                    finish = kw.lower()
                    break
        out[code] = {
            "name": name,
            "hex": rgb.lower(),
            "edge": edge.lower(),
            "alpha": int(alpha_m.group(1)) if alpha_m else 255,
            "luminance": int(lum_m.group(1)) if lum_m else 0,
            "finish": finish,
        }
    return out


def main():
    colours = parse()
    assert len(colours) > 300, "expected ~322 real LDConfig colours, got %d -- LDConfig.ldr format may have changed" % len(colours)
    transparent = sum(1 for c in colours.values() if c["alpha"] < 255)
    finished = sum(1 for c in colours.values() if c["finish"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(colours, separators=(",", ":"), sort_keys=True), encoding="utf-8")
    print("wrote %s: %d colours (%d transparent, %d with a special finish)" %
          (OUT, len(colours), transparent, finished))


if __name__ == "__main__":
    main()
