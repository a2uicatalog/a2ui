#!/usr/bin/env python3
"""Bakes the curated LDraw part set (spec/brick-parts/curated-parts-v1.json) into public/parts/<id>.json plus
public/parts/index.json, per spec/brick-parts-v0.1.md section 5.

Each part mesh has its top studs stripped (the renderer draws studs as instances at the connector positions,
as it already does for procedural bricks) and its triangle positions quantised to 1/16 LDU as integers, which
keeps the baked set small without visible error (1/16 LDU = 0.025mm).

Declared process: ldraw-parts-build (a2ui-private/ops/project-ops.yaml). Run:
    python3 scripts/ldraw/fetch_library.py     # once, or whenever the pin changes
    python3 scripts/ldraw/bake_parts.py
    python3 scripts/ldraw/bake_parts.py --characters-only   # just the minifig characters (characters.py)
    python3 scripts/ldraw/bake_parts.py --new-only          # only ids in CURATED not already in index.json
                                                              # (2026-09-28: a full bake takes ~20 minutes;
                                                              # this only regenerates genuinely new entries and
                                                              # patches index.json, leaving every existing baked
                                                              # part file untouched -- smaller diff, faster).
    python3 scripts/ldraw/bake_parts.py --ids=3937,3938     # only the listed CURATED ids, re-baked in place
                                                              # (2026-09-28: for a connector-only change, e.g.
                                                              # HINGE_CONNECTORS, that doesn't touch occupancy --
                                                              # avoids a full rebake for a handful of ids).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from resolve import Library, ColourTable, resolve_part  # noqa: E402
from parts import resolve_occupancy_and_sockets, bar_grip_points, hinge_connectors, HINGE_CONNECTORS, axle_connectors, clip_connectors  # noqa: E402
import characters  # noqa: E402

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
    template = entry.get("character")
    # a character's head stud is hidden under its headgear and nothing attaches to it, so its studs are baked into
    # the mesh (in their real colours) instead of becoming connectors
    part = resolve_part(lib, colours, pid + ".dat", bake_studs=bool(template))
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

    if template:
        (occ, sockets), needs_occ = characters.occupancy_and_sockets(), False
        bars = []
    else:
        occ, sockets, needs_occ = resolve_occupancy_and_sockets(pid, title, part.min, part.max, part.holes,
                                                                part.studs, part.tris, part.cylinders)
        # Called directly (not folded into resolve_occupancy_and_sockets's own return) so the grip's real
        # pos/dir reaches the baked mesh as its own `bars` connector field -- see the call site in parts.py's
        # resolve_occupancy_and_sockets for why the two aren't merged into one return shape. Same HINGE_
        # CONNECTORS exclusion as that call site, for the same real reason (2026-09-28): a verified hinge
        # pivot's cylinders are not a hand-graspable bar, and this is a separate call site that would
        # otherwise still tag e.g. 3937 with a bogus `bars` connector even after that one is fixed.
        bars = [] if (pid in HINGE_CONNECTORS or clip_connectors(pid, title, part.min, part.max, part.cylinders)) else bar_grip_points(part.min, part.max, part.cylinders, part.tris)

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
            # A held/clip-mounted connector (2026-09-27): geometrically the same "rod inserts into a
            # receiving feature" shape as pins/holes, just clip/hand-held instead of pin/hole-mated.
            "bars": [{"pos": qpt(p), "dir": [round(d, 3) for d in dr]} for p, dr in bars],
            # Real hinge pivot(s), curated in parts.py's HINGE_CONNECTORS -- [] for every part not in that
            # registry (not a per-part geometry computation, so cheap to call unconditionally here).
            "hinges": [{"pos": qpt(h["pos"]), "dir": [round(d, 3) for d in h["dir"]], "kind": h["kind"]}
                       for h in hinge_connectors(pid)],
            # Real axle centerline segment(s) for Technic axles and axle-rod parts
            "axles": [{"pos": qpt(a["pos"]), "dir": [round(d, 3) for d in a["dir"]], "len": a["len"]}
                      for a in axle_connectors(pid, title, part.min, part.max, occ, part.cylinders)],
            # Real clip jaw(s) for clip parts (Plate with Clip, Brick with Clip, Tile with Clip)
            "clips": [{"pos": qpt(c["pos"]), "dir": [round(d, 3) for d in c["dir"]]}
                      for c in clip_connectors(pid, title, part.min, part.max, part.cylinders)],
        },
        "occupancy": [list(b) for b in occ] if occ else None,
        "needs_occupancy": needs_occ,
    }
    if template:
        mesh["character"] = {"name": template["name"], "tags": template["tags"], "feet_y": characters.FEET_Y,
                             "slots": {slot: {"part": part_id, "colour": colour}
                                       for slot, (part_id, colour) in characters.template_slots(template).items()}}
    return mesh


def character_entries(lib):
    """Registers every minifig template (characters.py) as an in-memory model and returns bake entries for them."""
    entries = []
    for t in characters.TEMPLATES:
        pid = characters.character_id(t)
        lib.add_virtual(pid + ".dat", characters.template_dat(t))
        entries.append({"id": pid, "title": t["name"], "character": t})
    return entries


def main(characters_only=False, new_only=False, ids=None):
    lib = Library()
    colours = ColourTable(lib)
    os.makedirs(OUT_DIR, exist_ok=True)

    index = {"attribution": ATTRIBUTION, "quant": QUANT, "parts": {}}
    if ids:
        # re-bake exactly the listed CURATED ids in place -- existing index/entries for every other id are left
        # untouched, same additive-patch spirit as --new-only but for ids that already exist and need re-baking
        # (e.g. a connector-only registry addition that doesn't change occupancy).
        index = json.load(open(os.path.join(OUT_DIR, "index.json")))
        curated_by_id = {e["id"]: e for e in json.load(open(CURATED))}
        missing = [i for i in ids if i not in curated_by_id]
        if missing:
            sys.exit("--ids: not in curated-parts-v1.json: %s" % ", ".join(missing))
        todo = [curated_by_id[i] for i in ids]
    elif characters_only:
        # re-bake just the minifig characters into the existing index (a full bake takes ~20 minutes)
        index = json.load(open(os.path.join(OUT_DIR, "index.json")))
        index["parts"] = {k: v for k, v in index["parts"].items() if "character" not in v}
        todo = character_entries(lib)
    elif new_only:
        # only ids added to CURATED since the last bake -- existing baked files/index entries are left exactly
        # as they are (not re-baked, not re-ordered), so this is a strict additive patch, not a rebuild.
        index = json.load(open(os.path.join(OUT_DIR, "index.json")))
        curated = json.load(open(CURATED))
        todo = [e for e in curated if e["id"] not in index["parts"]]
        print("%d new id(s) to bake (%d already in index.json, skipped)" % (
            len(todo), len(curated) - len(todo)), file=sys.stderr)
    else:
        todo = json.load(open(CURATED)) + character_entries(lib)
    errors = []
    for entry in todo:
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
            "bars": len(mesh["connectors"]["bars"]),
            "hinges": len(mesh["connectors"]["hinges"]),
            "needs_occupancy": mesh["needs_occupancy"],
            "bytes": len(text),
            "license": mesh["license"],
        }
        if "character" in mesh:
            index["parts"][pid]["character"] = {"name": mesh["character"]["name"], "tags": mesh["character"]["tags"]}
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
    ids_arg = next((a for a in sys.argv[1:] if a.startswith("--ids=")), None)
    main(characters_only="--characters-only" in sys.argv[1:], new_only="--new-only" in sys.argv[1:],
         ids=ids_arg[len("--ids="):].split(",") if ids_arg else None)
