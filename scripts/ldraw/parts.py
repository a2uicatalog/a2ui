"""Connectors and occupancy for a resolved LDraw Part, per spec/brick-parts-v0.1.md sections 2 and 3.

Sockets (anti-studs) are GENERATED, not read from LDraw geometry (see spec section 2's rationale): one per 20x20
LDU footprint cell at the bottom face, for every part whose occupancy is a plain box resting on the LDU grid.
Occupancy is either generated (plain bricks/plates/tiles, from their title) or hand-authored (a small override
table for the fixture-verified non-box parts). Everything else is marked needs_occupancy=True and left for
Phase 3 — never guessed, per the Phase 1 handoff.
"""
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
    return [box(-10 * w, 10 * w, 0, h, -10 * d, 10 * d)]


# Hand-authored occupancy for parts whose plain LDraw geometry does not reduce to one clean box, verified against
# spec/brick-parts/fixtures-v0.1.json (F09, F15 exercise 3700 and 2780 directly).
OVERRIDES = {
    # Technic brick 1x2 with one hole: two end blocks either side of a 12x12 LDU channel along Z through (0, 10).
    "3700": [box(-20, -6, 0, 24, -10, 10), box(6, 20, 0, 24, -10, 10), box(-6, 6, 0, 4, -10, 10), box(-6, 6, 16, 24, -10, 10)],
    # Technic brick 1x1 with hole: same channel shape, 20 LDU wide.
    "6541": [box(-10, -6, 0, 24, -10, 10), box(6, 10, 0, 24, -10, 10), box(-6, 6, 0, 4, -10, 10), box(-6, 6, 16, 24, -10, 10)],
    # Technic pin (2L): a slim box along its axis; the friction ribs are cosmetic, not occupancy-relevant.
    "2780": [box(-20, 20, -6, 6, -6, 6)],
    "3673": [box(-20, 20, -6, 6, -6, 6)],
    "4274": [box(-10, 10, -6, 6, -6, 6)],
    "6558": [box(-20, 20, -6, 6, -6, 6)],
    "32054": [box(-30, 30, -9, 9, -9, 9)],
    # Jumper plate: full 1x2 plate body; its single stud is off-grid and handled by STUD_OVERRIDES below, not occupancy.
    "15573": [box(-20, 20, 0, 8, -10, 10)],
}

# Parts whose generated stud/socket connectors from geometry are wrong or incomplete for our purposes, replaced
# wholesale. Each entry: {"studs": [(pos, dir), ...], "sockets": [(pos, dir), ...]}. Empty list = "has none".
CONNECTOR_OVERRIDES = {
    # A jumper plate has ONE top stud, off-grid at (0,0,0) rather than the usual grid cell centres, and its
    # single bottom socket sits at grid cell (10, 8, 0)-ish per the LDraw geometry (kept from geometry: no override
    # needed for studs since LDraw's own stud primitive is already at the right spot); only sockets need fixing
    # since the generic "one socket per cell" rule would place two.
    "15573": {"sockets": [((0, 8, 0), (0, 1, 0))]},
}


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


def resolve_occupancy_and_sockets(part_id, title):
    """Returns (occupancy_boxes_or_None, sockets, needs_occupancy_bool)."""
    occ = OVERRIDES.get(part_id) or generated_occupancy(title)
    if occ is None:
        return None, [], True
    sockets = generate_sockets(occ)
    over = CONNECTOR_OVERRIDES.get(part_id, {})
    if "sockets" in over:
        sockets = over["sockets"]
    return occ, sockets, False
