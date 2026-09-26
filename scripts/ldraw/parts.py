"""Connectors and occupancy for a resolved LDraw Part, per spec/brick-parts-v0.1.md sections 2 and 3.

Sockets (anti-studs) are GENERATED, not read from LDraw geometry (see spec section 2's rationale): one per 20x20
LDU footprint cell at the bottom face, for every part whose occupancy is a plain box resting on the LDU grid.
Occupancy is either generated (plain bricks/plates/tiles, from their title) or hand-authored (a small override
table for the fixture-verified non-box parts). Everything else is marked needs_occupancy=True and left for
Phase 3 — never guessed, per the Phase 1 handoff.
"""
import math
import re

# title -> (module, w, d) for a plain rectangular footprint. Module height in LDU: brick=24, plate=8 (a tile is a
# plate-height part). Only titles with NO trailing modifier, or one from SAFE_SUFFIXES (which don't change the
# outer footprint), get a generated box; anything else (rounded corners, curves, hinges...) is left unclassified.
_DIM = re.compile(r"^(Brick|Plate|Tile)\s+(\d+)\s*x\s*(\d+)\s*(.*)$")
SAFE_SUFFIXES = {
    "", "with Groove", "with Center Groove", "with Centre Groove", "with Holes", "with Hole",
    "Grille with Groove",
}
MODULE_H = {"Brick": 24, "Plate": 8, "Tile": 8}


def classify_box(title):
    """Returns (module_h, w, d) for a plain rectangular part, or None."""
    m = _DIM.match(title.strip())
    if not m:
        return None
    kind, w, d, suffix = m.groups()
    if suffix.strip() not in SAFE_SUFFIXES:
        return None
    return (MODULE_H[kind], int(w), int(d))


def box(x0, x1, y0, y1, z0, z1):
    return (x0, x1, y0, y1, z0, z1)


def generated_occupancy(title):
    dims = classify_box(title)
    if dims is None:
        return None
    h, w, d = dims
    # w, d come from the title's own number order ("Brick 2 x 4" -> w=2, d=4) -- but real LDraw geometry puts the
    # FIRST number along Z and the SECOND along X, the opposite of the naive w->x, d->z mapping this had before.
    # Confirmed against real baked bounds for two parts: 3001 "Brick 2 x 4" has real X span 80 (4 studs) / Z span
    # 40 (2 studs), and 3023b "Plate 1 x 2" has real X span 40 (2 studs) / Z span 20 (1 stud) -- both the SECOND
    # title number on X, FIRST on Z. The old code did the reverse, so every non-square generated occupancy box
    # (and everything derived from it: generate_sockets' grid, collision boxes) was rotated 90 degrees off the
    # part's real stud/socket geometry. Found live 2026-09-26 building the Phase 3 validator: a stacked-bricks
    # fixture's stud-socket matching came out short because the generated sockets' grid ran the wrong way.
    return [box(-10 * d, 10 * d, 0, h, -10 * w, 10 * w)]


# Straight Technic bricks whose round holes bore through along Z (spec §2's "hole" connector, pairs of
# peghole.dat on opposite Z faces): solid everywhere except a 12x12 LDU channel at each hole's real X position,
# open between y=4 and y=16 (every part in this family has its hole centred at y=10, radius 6 -- read from the
# resolved connector data, not assumed). Originally hand-authored per part for 3700 and 6541 only (verified
# against spec/brick-parts/fixtures-v0.1.md F09/F15); generalised to a real-geometry-driven formula while adding
# the longer parts in the same family (32000, 3701, 3894, 3702, 3703) -- reproduces the exact original 3700/6541
# boxes byte-for-byte (checked), so F09/F15 still pass on the generalised path, not just the two hand-picked ids.
TECHNIC_HOLES_PARTS = {"3700", "6541", "32000", "3701", "3894", "3702", "3703"}
CHANNEL_HALF = 6


def technic_holes_occupancy(bounds_min, bounds_max, holes):
    """holes: list of (pos, dir) in real LDU (not yet quantised). Returns None if no Z-axis hole is present."""
    half_x = (bounds_max[0] - bounds_min[0]) / 2
    half_z = (bounds_max[2] - bounds_min[2]) / 2
    height = bounds_max[1] - bounds_min[1]
    z_holes = [pos for pos, d in holes if abs(d[2]) > 0.5]
    xs = sorted(set(round(pos[0]) for pos in z_holes))
    if not xs:
        return None
    hy = round(sum(pos[1] for pos in z_holes) / len(z_holes))  # every part in this family has one shared hole y
    boxes, prev = [], -half_x
    for hx in xs:
        if hx - CHANNEL_HALF > prev:
            boxes.append(box(prev, hx - CHANNEL_HALF, 0, height, -half_z, half_z))
        boxes.append(box(hx - CHANNEL_HALF, hx + CHANNEL_HALF, 0, hy - CHANNEL_HALF, -half_z, half_z))
        boxes.append(box(hx - CHANNEL_HALF, hx + CHANNEL_HALF, hy + CHANNEL_HALF, height, -half_z, half_z))
        prev = hx + CHANNEL_HALF
    if prev < half_x:
        boxes.append(box(prev, half_x, 0, height, -half_z, half_z))
    return boxes


# Simple round bricks/plates (always a square N x N footprint -- LDraw round parts are never rectangular): the
# occupancy box is a square INSCRIBED in the real circle (side = diameter/sqrt(2)), not the full N-stud bounding
# square, so two round parts placed edge to edge on the grid (their circles tangent, not overlapping) can never
# be falsely flagged as colliding -- spec §3's "never report a false one" (this is exact, not a heuristic: any
# axis-aligned square with that side length is provably entirely inside a circle of that diameter). Sockets are
# the STANDARD full N-stud grid (studs on these parts sit at the ordinary +/-10-per-stud positions, confirmed
# against real baked stud data for both ids in each entry below, e.g. 6143/3941's four studs at (+/-10,+/-10),
# identical to a normal square 2x2 brick) -- generated from the FULL square, deliberately not the smaller
# inscribed one generate_sockets() would otherwise misplace against.
# id -> (module_h, n_studs). Only the ids checked against real stud data are listed here; a round part NOT in
# this table (e.g. 14769, which has an unusual underside stud instead of a socket) stays needs_occupancy=True
# rather than being guessed by a generic title regex.
ROUND_PARTS = {
    "3062b": (24, 1), "6141": (8, 1), "85861": (8, 1), "98138": (8, 1),
    "6143": (24, 2), "3941": (24, 2), "4032a": (8, 2),
}


def round_occupancy_and_sockets(module_h, n_studs):
    diameter = n_studs * 20
    half_inscribed = diameter / (2 * math.sqrt(2))
    occ = [box(-half_inscribed, half_inscribed, 0, module_h, -half_inscribed, half_inscribed)]
    full_half = n_studs * 10
    sockets = generate_sockets([box(-full_half, full_half, 0, module_h, -full_half, full_half)])
    return occ, sockets


# Rectilinear corner bricks/plates (a clean N x N grid with exactly one corner cell missing, no curve at all --
# NOT the "Corner Round" family, which is a real curve and stays needs_occupancy=True): one 20x20xheight box per
# stud actually present, read from the part's own real geometry (not guessed) -- exact, not an approximation,
# since each present stud position IS the centre of a genuinely solid 20x20 cell for these two ids. Verified
# against real baked stud positions: 2357/2420 both have exactly 3 studs at (0,0),(20,0),(0,20), so the combined
# 3-box envelope (x:[-10,30], z:[-10,30]) matches each part's own real baked bounds exactly.
CORNER_L_PARTS = {"2357": 24, "2420": 8}


def corner_l_occupancy_and_sockets(module_h, studs):
    """studs: list of (pos, dir) in real LDU (not yet quantised)."""
    occ = [box(p[0] - 10, p[0] + 10, 0, module_h, p[2] - 10, p[2] + 10) for p, _ in studs]
    sockets = [((p[0], module_h, p[2]), (0, 1, 0)) for p, _ in studs]
    return occ, sockets


# Hand-authored occupancy for parts whose plain LDraw geometry does not reduce to one clean box or the Technic-
# holes family above, verified against spec/brick-parts/fixtures-v0.1.json (F09, F15 exercise 3700 and 2780
# directly).
OVERRIDES = {
    # Technic pin (2L): a slim box along its axis; the friction ribs are cosmetic, not occupancy-relevant.
    "2780": [box(-20, 20, -6, 6, -6, 6)],
    "3673": [box(-20, 20, -6, 6, -6, 6)],
    "4274": [box(-10, 10, -6, 6, -6, 6)],
    "6558": [box(-20, 20, -6, 6, -6, 6)],
    "32054": [box(-30, 30, -9, 9, -9, 9)],
    # Brick 1x2 with two studs on one side (SNOT): a normal 1x2 brick body underneath the extra side studs, which
    # come from real geometry (no override needed for them) -- x is the "2" direction, z the "1" direction, per
    # the corrected w/d convention above (confirmed against this same part's own real top-stud spread, x=+/-10).
    "11211": [box(-20, 20, 0, 24, -10, 10)],
    # Jumper plate: full 1x2 plate body; its single stud is off-grid and handled by STUD_OVERRIDES below, not occupancy.
    "15573": [box(-20, 20, 0, 8, -10, 10)],
}

# Parts whose generated stud/socket connectors from geometry are wrong or incomplete for our purposes, replaced
# wholesale. Each entry: {"studs": [(pos, dir), ...], "sockets": [(pos, dir), ...]}. Empty list = "has none".
#
# 15573 (jumper plate) is NOT here despite an earlier version of this table overriding its sockets down to one
# ("without Understud" in the title was misread as "without a normal bottom connection at all"). Found wrong
# building the Phase 3 validator against spec/brick-parts/fixtures-v0.1.json F12_jumper_offset (expects
# stud_connections: 3 for a jumper plate on the baseplate with a 1x1 plate on its single top stud): the override
# gave 1 (bottom) + 1 (top) = 2. The generic "one socket per cell" rule for its full 1x2 occupancy footprint gives
# 2 real bottom sockets, both landing on valid baseplate grid positions for this fixture's placement -- 2 + 1 = 3,
# matching exactly. "Without understud" describes the top stud having no reinforcing tube above it, not the
# plate's ordinary two-cell bottom connection -- kept as a documented correction, not silently reverted.
CONNECTOR_OVERRIDES = {}


def generate_sockets(occupancy):
    """One downward-facing socket per 20x20 LDU footprint cell at the lowest face of the given occupancy boxes."""
    if not occupancy:
        return []
    ymax = max(b[3] for b in occupancy)
    x0 = min(b[0] for b in occupancy)
    x1 = max(b[1] for b in occupancy)
    z0 = min(b[4] for b in occupancy)
    z1 = max(b[5] for b in occupancy)
    out = []
    x = x0 + 10
    while x < x1:
        z = z0 + 10
        while z < z1:
            out.append(((x, ymax, z), (0, 1, 0)))
            z += 20
        x += 20
    return out


def resolve_occupancy_and_sockets(part_id, title, bounds_min=None, bounds_max=None, holes=None, studs=None):
    """Returns (occupancy_boxes_or_None, sockets, needs_occupancy_bool). bounds/holes/studs (real LDU,
    unquantised) are only needed for the Technic-holes/round/corner-L families; every other path ignores them,
    so existing callers that omit them keep working."""
    if part_id in ROUND_PARTS:
        occ, sockets = round_occupancy_and_sockets(*ROUND_PARTS[part_id])
        return occ, sockets, False
    if part_id in CORNER_L_PARTS and studs is not None:
        occ, sockets = corner_l_occupancy_and_sockets(CORNER_L_PARTS[part_id], studs)
        return occ, sockets, False
    occ = OVERRIDES.get(part_id) or generated_occupancy(title)
    if occ is None and part_id in TECHNIC_HOLES_PARTS and bounds_min and holes is not None:
        occ = technic_holes_occupancy(bounds_min, bounds_max, holes)
    if occ is None:
        return None, [], True
    sockets = generate_sockets(occ)
    over = CONNECTOR_OVERRIDES.get(part_id, {})
    if "sockets" in over:
        sockets = over["sockets"]
    return occ, sockets, False
