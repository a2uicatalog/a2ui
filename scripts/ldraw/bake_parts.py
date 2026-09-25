#!/usr/bin/env python3
"""Bakes the curated LDraw part set (spec/brick-parts/curated-parts-v1.json) into public/parts/<id>.json plus
public/parts/index.json, per spec/brick-parts-v0.1.md section 5.

Each part mesh has its top studs stripped (the renderer draws studs as instances at the connector positions,
as it already does for procedural bricks) and its triangle positions quantised to 1/16 LDU as integers, which
keeps the baked set small without visible error (1/16 LDU = 0.025mm).

Declared process: ldraw-parts-build (a2ui-private/ops/project-ops.yaml). Run:
    python3 scripts/ldraw/fetch_library.py     # once, or whenever the pin changes
    python3 scripts/ldraw/bake_parts.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from resolve import Library, ColourTable, resolve_part  # noqa: E402
from parts import resolve_occupancy_and_sockets  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
CURATED = os.path.join(ROOT, "..", "a2ui-private", "spec", "brick-parts", "curated-parts-v1.json")
OUT_DIR = os.path.join(ROOT, "public", "parts")
QUANT = 16   # positions stored as round(ldu * QUANT), an integer; decode by dividing by QUANT

ATTRIBUTION = (
    "Part geometry from the LDraw.org Parts Library (https://www.ldraw.org), used under CC BY 4.0 / CC BY 2.0. "
    "LDraw is not affiliated with the LEGO Group. LEGO(R) is a trademark of the LEGO Group, which does not "
    "sponsor, authorize or endorse this content."
)


def q(v):
    return round(v * QUANT)


def qpt(p):
    return [q(p[0]), q(p[1]), q(p[2])]


def bake_one(lib, colours, entry):
    pid, title_hint = entry["id"], entry["title"]
    part = resolve_part(lib, colours, pid + ".dat")
    if part.missing:
        raise RuntimeError("%s: could not resolve %s" % (pid, sorted(part.missing)))
    title = part.title or title_hint

    # group triangles by colour tag so the mesh can share one draw call per colour group; 'main'/'edge' groups get
    # tinted by the instance's colour and edge colour at render time, anything else is a baked #rrggbb.
    groups = {}
    for p0, p1, p2, colour in part.tris:
        groups.setdefault(colour, []).append((p0, p1, p2))
    tri_groups = [{"colour": c, "pos": [qpt(v) for tri in tris for v in tri]} for c, tris in sorted(groups.items())]

    edge_groups = {}
    for p0, p1, colour in part.edges:
        edge_groups.setdefault(colour, []).append((p0, p1))
    edges = [{"colour": c, "pos": [qpt(v) for seg in segs for v in seg]} for c, segs in sorted(edge_groups.items())]

    cond_groups = {}
    for p0, p1, c0, c1, colour in part.cond:
        cond_groups.setdefault(colour, []).append((p0, p1, c0, c1))
    cond = [{"colour": c, "pos": [qpt(v) for seg in segs for v in seg[:2]],
             "ctl": [qpt(v) for seg in segs for v in seg[2:]]} for c, segs in sorted(cond_groups.items())]

    occ, sockets, needs_occ = resolve_occupancy_and_sockets(pid, title)

    mesh = {
        "id": pid,
        "title": title,
        "license": part.license,
        "quant": QUANT,
        "bounds": {"min": qpt(part.min), "max": qpt(part.max)},
        "triangles": tri_groups,
        "edges": edges,
        "conditional": cond,
        "connectors": {
            "studs": [{"pos": qpt(p), "dir": [round(d, 3) for d in dr]} for p, dr in part.studs],
            "sockets": [{"pos": qpt(p), "dir": [round(d, 3) for d in dr]} for p, dr in sockets],
            "holes": [{"pos": qpt(p), "dir": [round(d, 3) for d in dr]} for p, dr in part.holes],
            "pins": [{"pos": qpt(p), "dir": [round(d, 3) for d in dr]} for p, dr in part.pins],
        },
        "occupancy": [list(b) for b in occ] if occ else None,
        "needs_occupancy": needs_occ,
    }
    return mesh


def main():
    curated = json.load(open(CURATED))
    lib = Library()
    colours = ColourTable(lib)
    os.makedirs(OUT_DIR, exist_ok=True)

    index = {"attribution": ATTRIBUTION, "quant": QUANT, "parts": {}}
    errors = []
    for entry in curated:
        pid = entry["id"]
        try:
            mesh = bake_one(lib, colours, entry)
        except Exception as e:
            errors.append("%s: %s" % (pid, e))
            continue
        out_path = os.path.join(OUT_DIR, pid + ".json")
        text = json.dumps(mesh, separators=(",", ":"))
        open(out_path, "w").write(text)
        index["parts"][pid] = {
            "title": mesh["title"],
            "bounds": mesh["bounds"],
            "studs": len(mesh["connectors"]["studs"]),
            "sockets": len(mesh["connectors"]["sockets"]),
            "holes": len(mesh["connectors"]["holes"]),
            "pins": len(mesh["connectors"]["pins"]),
            "needs_occupancy": mesh["needs_occupancy"],
            "bytes": len(text),
            "license": mesh["license"],
        }
        print("baked %-8s %6d B  studs=%d sockets=%d%s" % (
            pid, len(text), index["parts"][pid]["studs"], index["parts"][pid]["sockets"],
            "  [needs_occupancy]" if mesh["needs_occupancy"] else ""))

    if errors:
        for e in errors:
            print("ERROR", e, file=sys.stderr)
        sys.exit("%d part(s) failed to resolve" % len(errors))

    index_path = os.path.join(OUT_DIR, "index.json")
    open(index_path, "w").write(json.dumps(index, indent=1))
    total = sum(v["bytes"] for v in index["parts"].values())
    needs = sum(1 for v in index["parts"].values() if v["needs_occupancy"])
    print("\n%d parts baked, %d bytes raw (%d need occupancy in Phase 3)" % (len(index["parts"]), total, needs))
    print("wrote", index_path)


if __name__ == "__main__":
    main()
