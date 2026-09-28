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
import math
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from renderers.brick_parts_validate import (  # noqa: E402
    PART_ROT,
    _add3,
    _boxes_overlap,
    _conn_world,
    _dot3,
    _hinge_kinds_mate,
    _hinges_world,
    _pair_holes,
    _point_line_dist,
    _world_boxes,
    rot_ldu,
)

PARTS_DIR = ROOT / "public" / "parts"
PART_ID_ALIAS = {"3023": "3023b", "3665": "3665a", "3660": "3660a", "60481": "60481a", "4032": "4032a",
                 "2654": "2654a", "4073": "6141"}   # twin of PART_ID_ALIAS in atoms_brick.gs
_MESH_CACHE = {}


def load_mesh(pid):
    if pid not in _MESH_CACHE:
        p = PARTS_DIR / (pid + ".json")
        if p.exists():
            try:
                _MESH_CACHE[pid] = json.loads(p.read_text())
            except Exception:
                _MESH_CACHE[pid] = None
        else:
            _MESH_CACHE[pid] = None
    return _MESH_CACHE[pid]


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


def _safe_tilted_indices(have, meshes):
    """Return set of indices into `have` of tilted parts that can be placed safely without collision."""
    tilted_indices = {i for i, l in enumerate(have) if rot_index(l["m"]) is None}
    if not tilted_indices:
        return set()

    boxes = []
    for l in have:
        pid = PART_ID_ALIAS.get(l["part"], l["part"])
        r = rot_index(l["m"])
        rot = r if r is not None else l["m"]
        mesh = meshes.get(pid)
        boxes.append(_world_boxes(mesh, rot, *l["t"]) if mesh else None)

    # Tilted parts without occupancy data cannot be verified safe
    colliding = {i for i in tilted_indices if not boxes[i]}

    # Check for mated pin/hole and hinge connections to exempt intentional interpenetration
    mated_pairs = set()
    pins, hole_segs_world, hinges = [], [], []
    for l in have:
        pid = PART_ID_ALIAS.get(l["part"], l["part"])
        r = rot_index(l["m"])
        rot = r if r is not None else l["m"]
        mesh = meshes.get(pid)
        if not mesh:
            pins.append([])
            hinges.append([])
            hole_segs_world.append([])
            continue
        pins.append(_conn_world(mesh, "pins", rot, *l["t"]))
        hinges.append(_hinges_world(mesh, rot, *l["t"]))
        local_segs = _pair_holes(mesh)
        hole_segs_world.append([
            {"a": _add3(rot_ldu(rot, s[0]), l["t"]),
             "b": _add3(rot_ldu(rot, s[1]), l["t"])}
            for s in local_segs
        ])

    n = len(have)
    for i in range(n):
        if not pins[i]:
            continue
        for p in pins[i]:
            for j in range(n):
                if i == j or not hole_segs_world[j]:
                    continue
                for seg in hole_segs_world[j]:
                    half = _add3(p["pos"], tuple(d * 20 for d in p["dir"]))
                    mid = _add3(p["pos"], tuple(d * 10 for d in p["dir"]))
                    d1, _ = _point_line_dist(p["pos"], seg["a"], seg["b"])
                    d2, _ = _point_line_dist(half, seg["a"], seg["b"])
                    _, tm = _point_line_dist(mid, seg["a"], seg["b"])
                    if d1 < 0.5 and d2 < 0.5 and -0.02 <= tm <= 1.02:
                        mated_pairs.add((min(i, j), max(i, j)))

    for i in range(n):
        if not hinges[i]:
            continue
        for ha in hinges[i]:
            for j in range(i + 1, n):
                if not hinges[j]:
                    continue
                for hb in hinges[j]:
                    if not _hinge_kinds_mate(ha["kind"], hb["kind"]):
                        continue
                    if abs(_dot3(ha["dir"], hb["dir"])) <= 0.99:
                        continue
                    hb_end = _add3(hb["pos"], hb["dir"])
                    dist, _ = _point_line_dist(ha["pos"], hb["pos"], hb_end)
                    if dist < 0.5:
                        mated_pairs.add((i, j))

    # Broadphase 80-LDU spatial grid
    grid = {}
    for i, b_list in enumerate(boxes):
        if not b_list:
            continue
        b_aabbs = [b["aabb"] if isinstance(b, dict) else b for b in b_list]
        lo = [min(ab[ax * 2] for ab in b_aabbs) for ax in range(3)]
        hi = [max(ab[ax * 2 + 1] for ab in b_aabbs) for ax in range(3)]
        candidates = set()
        for gx in range(math.floor(lo[0] / 80), math.floor(hi[0] / 80) + 1):
            for gy in range(math.floor(lo[1] / 80), math.floor(hi[1] / 80) + 1):
                for gz in range(math.floor(lo[2] / 80), math.floor(hi[2] / 80) + 1):
                    candidates.update(grid.setdefault((gx, gy, gz), []))
                    grid[(gx, gy, gz)].append(i)
        for o in candidates:
            if i in tilted_indices or o in tilted_indices:
                if not boxes[o]:
                    continue
                pair = (min(i, o), max(i, o))
                if pair in mated_pairs:
                    continue
                if any(_boxes_overlap(ba, bb) for ba in b_list for bb in boxes[o]):
                    if i in tilted_indices:
                        colliding.add(i)
                    if o in tilted_indices:
                        colliding.add(o)

    return tilted_indices - colliding


def coverage(leaves, baked=None):
    baked = baked if baked is not None else baked_ids()
    n = len(leaves)
    have = [l for l in leaves if PART_ID_ALIAS.get(l["part"], l["part"]) in baked]
    tilted_all = [i for i, l in enumerate(have) if rot_index(l["m"]) is None]

    if tilted_all:
        meshes = {pid: load_mesh(pid) for pid in {PART_ID_ALIAS.get(l["part"], l["part"]) for l in have}}
        safe_tilted = _safe_tilted_indices(have, meshes)
    else:
        safe_tilted = set()

    ok = [l for i, l in enumerate(have) if rot_index(l["m"]) is not None or i in safe_tilted]
    missing = {}
    for l in leaves:
        if PART_ID_ALIAS.get(l["part"], l["part"]) not in baked:
            missing[l["part"]] = missing.get(l["part"], 0) + 1
    return {
        "parts": n,
        "baked": len(have),
        "renderable": len(ok),
        "tilted": len(have) - len(ok),
        "tilted_safe": len(safe_tilted),
        "fraction": (len(ok) / n) if n else 0.0,
        "missing": dict(sorted(missing.items(), key=lambda kv: -kv[1])),
    }


def to_parts_model(leaves, baked=None):
    """partsModel entries [id, x, y, z, r, colour, step] for the renderable leaves, lowest part on y=0, stud-aligned."""
    baked = baked if baked is not None else baked_ids()
    have = [l for l in leaves if PART_ID_ALIAS.get(l["part"], l["part"]) in baked]
    if not have:
        return []

    pids_have = {PART_ID_ALIAS.get(l["part"], l["part"]) for l in have}
    meshes = {pid: load_mesh(pid) for pid in pids_have}

    tilted_all = [i for i, l in enumerate(have) if rot_index(l["m"]) is None]
    safe_tilted = _safe_tilted_indices(have, meshes) if tilted_all else set()

    rows = []
    for i, l in enumerate(have):
        pid = PART_ID_ALIAS.get(l["part"], l["part"])
        r = rot_index(l["m"])
        if r is not None:
            rows.append((pid, l, r))
        elif i in safe_tilted:
            rot_matrix = tuple(round(float(v), 6) for v in l["m"])
            rows.append((pid, l, rot_matrix))

    if not rows:
        return []

    q = 16.0

    def bottom_y(pid, l, r):
        b = meshes[pid]["bounds"]
        m = PART_ROT[r] if isinstance(r, int) else r
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
