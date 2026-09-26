#!/usr/bin/env python3
"""Import a LDraw Official Model Repository (OMR) set (.mpd/.ldr) as a brick_build_3d partsModel.

OMR files carry every part's position, rotation matrix and colour in build steps, so unlike Rebrickable (which only
lists a set's part inventory) they are enough to reproduce a real LEGO set. This module:
  * splits the MPD into its FILE sections and flattens nested sub-models into one list of leaf parts,
  * resolves colour 16 (inherit) through the sub-model chain,
  * maps each 3x3 matrix onto the renderer's 24 axis-aligned rotations (PART_ROT) -- tilted/mirrored parts are
    counted, never guessed,
  * reports coverage against the baked parts in public/parts/ (a part with no baked mesh cannot be drawn),
  * normalises the model so its lowest part sits on the baseplate (y=0) and its footprint is stud-aligned.
Source models are CC BY (LDraw OMR, CCAL 2.0): callers must keep the attribution.
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from renderers.brick_parts_validate import PART_ROT  # noqa: E402

PARTS_DIR = ROOT / "public" / "parts"
PART_ID_ALIAS = {"3023": "3023b", "3665": "3665a", "3660": "3660a", "60481": "60481a", "4032": "4032a",
                 "2654": "2654a", "4073": "6141"}   # twin of PART_ID_ALIAS in atoms_brick.gs


def baked_ids():
    idx = json.loads((PARTS_DIR / "index.json").read_text())
    return set(idx["parts"])


def _mmul(a, b):
    return tuple(sum(a[3 * i + k] * b[3 * k + j] for k in range(3)) for i in range(3) for j in range(3))


def _apply(m, t, p):
    return tuple(m[3 * i] * p[0] + m[3 * i + 1] * p[1] + m[3 * i + 2] * p[2] + t[i] for i in range(3))


def split_files(text):
    """{lower-cased file name: [lines]} plus the name of the main (first) file."""
    files, cur, main = {}, None, None
    for raw in text.splitlines():
        line = raw.strip()
        m = re.match(r"0\s+FILE\s+(.+)$", line, re.I)
        if m:
            cur = m.group(1).strip().lower()
            files[cur] = []
            main = main or cur
            continue
        if cur is None:
            cur = "main.ldr"
            files[cur] = []
            main = cur
        if line:
            files[cur].append(line)
    return files, main


def flatten(text):
    """Leaf parts: [{'part','colour','m','t','step'}]. `step` counts 0 STEP boundaries in the main file."""
    files, main = split_files(text)
    leaves = []
    ident = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)

    def walk(name, m, t, colour, step_of, depth=0):
        if depth > 12:
            return
        step = 1
        for line in files[name]:
            tok = line.split()
            if tok[0] == "0":
                if len(tok) > 1 and tok[1].upper() == "STEP":
                    step += 1
                continue
            if tok[0] != "1" or len(tok) < 15:
                continue
            col = int(tok[1])
            x, y, z = (float(v) for v in tok[2:5])
            lm = tuple(float(v) for v in tok[5:14])
            ref = " ".join(tok[14:]).strip().lower().replace("\\", "/")
            wcol = colour if col in (16, 24) and colour is not None else col
            wm, wt = _mmul(m, lm), _apply(m, t, (x, y, z))
            st = step_of if step_of is not None else step
            if ref in files:
                walk(ref, wm, wt, wcol, st, depth + 1)
            elif ref.endswith(".dat") and not ref.startswith(("s/", "48/", "8/")):
                leaves.append({"part": ref[:-4], "colour": 16 if wcol in (16, 24) else wcol, "m": wm, "t": wt, "step": st})
    walk(main, ident, (0.0, 0.0, 0.0), None, None)
    return leaves


def rot_index(m, tol=0.02):
    """Index into PART_ROT for an axis-aligned proper rotation, else None."""
    for i, r in enumerate(PART_ROT):
        if all(abs(a - b) <= tol for a, b in zip(m, r)):
            return i
    return None


def coverage(leaves, baked=None):
    baked = baked if baked is not None else baked_ids()
    n = len(leaves)
    have = [l for l in leaves if PART_ID_ALIAS.get(l["part"], l["part"]) in baked]
    ok = [l for l in have if rot_index(l["m"]) is not None]
    missing = {}
    for l in leaves:
        if PART_ID_ALIAS.get(l["part"], l["part"]) not in baked:
            missing[l["part"]] = missing.get(l["part"], 0) + 1
    return {"parts": n, "baked": len(have), "renderable": len(ok), "tilted": len(have) - len(ok),
            "fraction": (len(ok) / n) if n else 0.0, "missing": dict(sorted(missing.items(), key=lambda kv: -kv[1]))}


def to_parts_model(leaves, baked=None):
    """partsModel entries [id, x, y, z, r, colour, step] for the renderable leaves, lowest part on y=0, stud-aligned."""
    baked = baked if baked is not None else baked_ids()
    rows = []
    for l in leaves:
        pid = PART_ID_ALIAS.get(l["part"], l["part"])
        r = rot_index(l["m"])
        if pid in baked and r is not None:
            rows.append((pid, l, r))
    if not rows:
        return []
    meshes = {pid: json.loads((PARTS_DIR / (pid + ".json")).read_text()) for pid in {p for p, _, _ in rows}}
    q = 16.0

    def bottom_y(pid, l, r):
        b = meshes[pid]["bounds"]
        m = PART_ROT[r]
        ys = []
        for x in (b["min"][0], b["max"][0]):
            for y in (b["min"][1], b["max"][1]):
                for z in (b["min"][2], b["max"][2]):
                    ys.append(m[3] * x / q + m[4] * y / q + m[5] * z / q)
        return l["t"][1] + max(ys)
    floor = max(bottom_y(p, l, r) for p, l, r in rows)          # LDraw y is down: the largest y is the lowest point
    xs = [l["t"][0] for _, l, _ in rows]
    zs = [l["t"][2] for _, l, _ in rows]
    cx = round((min(xs) + max(xs)) / 2 / 20) * 20
    cz = round((min(zs) + max(zs)) / 2 / 20) * 20
    out = []
    for pid, l, r in sorted(rows, key=lambda t: (t[1]["step"], -t[1]["t"][1])):
        out.append([pid, round(l["t"][0] - cx), round(l["t"][1] - floor), round(l["t"][2] - cz), r, l["colour"], l["step"]])
    return out


if __name__ == "__main__":
    text = Path(sys.argv[1]).read_text(errors="replace")
    leaves = flatten(text)
    c = coverage(leaves)
    print(json.dumps({k: v for k, v in c.items() if k != "missing"}), "missing top:", list(c["missing"].items())[:8])
