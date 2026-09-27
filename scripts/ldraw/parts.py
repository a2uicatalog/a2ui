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


# Round dishes: same provably-safe inscribed-square occupancy as ROUND_PARTS (a dish's title size, e.g. "Dish
# 2 x 2", names its outer diameter in studs, same as any other round part) -- but NOT the same sockets. A dish
# is a single-point mount: 4740/3960 each have exactly ONE real stud at the centre (confirmed against real baked
# connector data), not the full N-stud grid of studs a normal round brick/plate has, so generate_sockets()'s
# "one per cell" rule would fabricate sockets this part does not have. Deliberately sockets=[] here rather than
# guess at whether/where a bottom connector exists -- this id gets real collision detection (new value) without
# inventing connection data the geometry does not support. The part's own real top stud (already read correctly
# from geometry regardless of this table) still works for anchoring if something rests on it.
DISH_PARTS = {"4740": (8, 2), "3960": (16, 4)}


def dish_occupancy(module_h, n_studs):
    diameter = n_studs * 20
    half_inscribed = diameter / (2 * math.sqrt(2))
    return [box(-half_inscribed, half_inscribed, 0, module_h, -half_inscribed, half_inscribed)]


# Tyres: rotationally symmetric about the Z axis (wheel axle) with their circular cross-section in the XY plane,
# centered at (0, 0). Like ROUND_PARTS and DISH_PARTS, occupancy is an axis-aligned square inscribed in that
# outer circle (half-side = diameter / (2 * sqrt(2))), spanning the part's own real Z bounds (the tyre's width).
# Any point within this square has distance from origin r <= half_inscribed * sqrt(2) = diameter / 2, so it is
# provably contained within the outer cylinder of the tyre and can never over-report an external collision (spec §3's
# "never report a false one"). Sockets are empty ([]): tyres carry no studs, anti-studs, pegholes, or pins (confirmed
# against real resolved geometry for all 95 Tyre-category parts in the library -- nothing normally stacks onto a tyre;
# wheels mount via axle/rim submodels).
#
# Unlike ROUND_PARTS/DISH_PARTS, a tyre's outer diameter is NOT expressed in stud units in its title -- LEGO tyre
# nomenclature encodes rim diameter in mm, aspect ratio %, or width in mm (e.g. "Tyre 12/ 40 x 11 Wide" has rim=12mm,
# aspect=40%, width=11mm, giving real diameter 50 LDU; "Tyre 14/ 50 x 17" has real diameter 76 LDU; "Tyre for Wheel
# 41mm Znap" has diameter 130 LDU), so diameter cannot be derived from a single title regex without guessing.
#
# Like SLOPE_BACK_WALL_PARTS, this family supports reading dimensions directly from real resolved bounds (bounds_min
# and bounds_max) at the resolve_occupancy_and_sockets call site, while also providing pre-calculated constants
# (diameter, z_min, z_max) for when bounds are omitted.
#
# Verified against real resolved geometry for all 94 official Tyre-category parts in the library:
# 92 parts are verified clean, rotationally symmetric in XY (dx == dy to within 0.1 LDU), centered at (0, 0) in XY,
# and strictly non-empty (dz > 0). Two parts are excluded: 2807 ('Tyre Minifig Bicycle (Needs Work)' -- marked
# incomplete) and 6578c01 ('Tyre 14/ 36 x 20 VR (Deformed to 10/ 67 x 24)' -- conically/mechanically deformed variant).
TYRE_PARTS = {
    "11209": (52.5, -12.5, 12.5), "11957": (251.72, -24.0, 24.0), "15413": (123.52, -25.25, 25.25),
    "18450": (208.6, -55.5, 55.5), "18977": (60.0, -14.0, 14.0), "2346": (70.0, -20.0, 10.0),
    "23798": (267.77, -55.0, 55.0), "23799": (204.0, -55.0, 55.0), "2696": (108.0, -24.0, 8.0),
    "2857": (121.99, -25.0, 25.0), "2902": (204.0, -17.5, 17.5), "2995": (170.0, -50.0, 50.0),
    "2997": (202.77, -42.0, 42.0), "30028b": (36.0, -10.0, 10.0), "30391": (76.0, -17.0, 17.0),
    "30648": (60.0, -17.0, 17.0), "30699": (109.0, -18.0, 18.0), "3139b": (36.0, -5.5, 5.5),
    "32003": (170.01, -30.0, 30.0), "32019": (156.6, -34.5, 15.5), "32076": (174.58, -17.5, 17.5),
    "32078": (174.58, -35.2, 35.2), "32180": (140.0, -37.75, 38.75), "32196": (204.0, -40.0, 40.0),
    "32296": (206.0, -62.0, 62.0), "32296p01": (206.0, -62.0, 62.0), "32298": (262.0, -76.0, 76.0),
    "32298p01": (262.0, -76.0, 76.0), "3483": (62.0, -9.0, 9.0), "35578": (89.6, -17.0, 17.0),
    "36": (106.0, -9.0, 9.0), "3634": (108.26, -16.0, 9.0), "3641": (36.0, -8.0, 8.0),
    "3740": (205.22, -30.0, 30.0), "4084": (50.0, -12.0, 8.0), "41893": (171.99, -45.0, 45.0),
    "41897": (140.0, -35.0, 35.0), "4267": (160.0, -25.0, 25.0), "4410": (204.17, -55.0, 55.0),
    "44308": (108.0, -28.0, 28.0), "44309": (108.0, -27.0, 27.0), "4455": (219.23, -44.5, 44.5),
    "44771": (172.12, -44.0, 44.0), "44799": (76.0, -9.0, 9.0), "451b": (36.0, -8.5, 8.5),
    "458": (44.0, -6.0, 6.0), "45982": (204.63, -48.0, 48.0), "46335": (236.0, -44.1, 44.1),
    "50861": (53.11, -7.5, 7.5), "50951": (38.0, -8.0, 8.0), "51011": (43.84, -8.0, 8.0),
    "52985": (172.5, -34.0, 34.0), "539": (130.0, -21.0, 21.0), "54120": (236.73, -55.0, 55.0),
    "55976": (142.0, -32.0, 32.0), "55978": (92.35, -28.0, 28.0), "56890": (60.0, -14.0, 14.0),
    "56891": (92.0, -28.0, 17.0), "56897": (76.0, -17.0, 9.0), "56898": (107.07, -18.0, 18.0),
    "56907": (204.0, -44.0, 44.0), "574": (108.26, -18.0, 7.0), "58090": (76.0, -17.0, 17.0),
    "59895": (36.0, -5.5, 5.5), "6015": (50.0, -14.0, 14.0), "61254": (59.26, -9.0, 9.0),
    "61480": (171.37, -43.0, 43.0), "61481": (108.0, -33.0, 33.0), "6292": (114.0, -31.0, 31.0),
    "6578": (76.0, -17.5, 17.5), "6579": (102.0, -33.0, 33.0), "6581": (121.99, -25.0, 25.0),
    "6594": (124.06, -35.0, 35.0), "6596": (204.01, -17.5, 17.5), "67140": (238.0, -35.0, 35.0),
    "69909": (188.0, -35.0, 35.0), "69912": (201.85, -42.88, 42.88), "70490": (123.52, -18.0, 18.0),
    "70695": (139.53, -32.0, 32.0), "71721": (332.0, -34.0, 34.0), "71722": (350.0, -46.0, 46.0),
    "7860": (187.64, -16.25, 16.25), "80279": (220.0, -55.0, 55.0), "80542": (187.83, -25.0, 25.0),
    "87414": (35.83, -8.0, 8.0), "87697": (50.0, -14.0, 14.0), "88516": (237.49, -25.77, 25.77),
    "89201": (60.0, -17.0, 17.0), "92402": (76.0, -17.0, 17.0), "92409": (43.83, -8.0, 8.0),
    "92912": (236.32, -48.0, 48.0), "u9131": (60.0, -9.0, 9.0),
}


def tyre_occupancy(bounds_min, bounds_max=None, z_max=None):
    """Returns an inscribed-square occupancy box in the XY plane spanning Z.
    Can be called with (bounds_min, bounds_max) or (diameter, z_min, z_max)."""
    if z_max is not None:
        diameter, z_min = bounds_min, bounds_max
    else:
        diameter = (bounds_max[0] - bounds_min[0] + bounds_max[1] - bounds_min[1]) / 2.0
        z_min, z_max = bounds_min[2], bounds_max[2]
    half_inscribed = diameter / (2 * math.sqrt(2))
    return [box(-half_inscribed, half_inscribed, -half_inscribed, half_inscribed, z_min, z_max)]


# Wheel Rims: rotationally symmetric about the Z axis (wheel axle) with their circular cross-section in the
# XY plane, centered at (0, 0).
#
# Critical difference from tyres:
# Tyres mount around the outside of a wheel rim and have no axle or pin passing through their local coordinate
# center (nothing normally stacks onto or through a tyre in a model). Most wheel rims DO mount onto a Technic axle
# or wheel-holder pin through a hole at or near their rotational center (0, 0).
#
# If wheel occupancy naively copied the tyre approach (a solid inscribed square spanning the center), it would
# place solid occupancy directly inside the axle bore, falsely reporting physical collisions between the wheel
# and its own axle or pin in every assembly -- a severe false positive that violates spec §3's "never report a
# false one" mandate.
#
# Furthermore, generic_hole_channel_occupancy (used for Technic beams) is NOT usable for wheel rims because:
# 1. Wheels with radial/spoke holes (e.g. 41896) have holes varying across both X and Y, failing the 1D-varying
#    line requirement and returning None immediately.
# 2. Wheels with a single center hole decompose into large rectangular channel boxes extending to the outer
#    bounding box corners, failing the raycast solid-fraction check (STUD_CELL_MIN_SOLID) because spoked wheels
#    are mostly empty air between hub and rim.
# 3. Many wheel rims reference primitives like axlehol5.dat or custom subfiles not recognized by peghole.dat /
#    AXLE_HOLE_RE detectors, leaving part.holes empty even though an axle hole exists.
#
# Wheel rim occupancy therefore uses an annular 4-box inscribed square decomposition that provably satisfies
# two simultaneous safety guarantees:
#
# 1. Outer cylinder containment (never over-reports external collisions):
#    The outer boundary is an axis-aligned square inscribed in the circular rim cross-section of diameter D:
#    half_inscribed = W = D / (2 * sqrt(2)). For any point (x, y) with |x| <= W and |y| <= W:
#    x^2 + y^2 <= 2 * W^2 = 2 * (D^2 / 8) = (D / 2)^2 = R_out^2.
#    Thus, every point in the occupancy is provably inside the physical outer cylinder of the wheel rim,
#    never projecting into surrounding empty space (spec §3's under-approximation guarantee).
#
# 2. Central bore exclusion (never collides with mounting axle or pin):
#    The central square region (-B, B) x (-B, B) x [z_min, z_max] with B = WHEEL_BORE_HALF = 8.0 LDU is
#    strictly excluded from occupancy.
#    - Standard Technic axles fit within a 12x12 LDU square (|x| <= 6.0, |y| <= 6.0; outer boundary radius 6.0 LDU).
#    - Standard Technic pins (2780, 3673) have shaft radius 6.0 LDU, with flange radius 8.0 LDU.
#    - Wheel holding pins (2470, 4489a) have pin shaft radius 4.0 LDU, with hub collar radius <= 8.0 LDU.
#    The 4 boxes:
#      Top:    [-W,  W] x [ B,  W] x [z_min, z_max]
#      Bottom: [-W,  W] x [-W, -B] x [z_min, z_max]
#      Left:   [-W, -B] x [-B,  B] x [z_min, z_max]
#      Right:  [ B,  W] x [-B,  B] x [z_min, z_max]
#    have no point satisfying both |x| < B and |y| < B. Every point in Box Top has y >= 8.0; Box Bottom has
#    y <= -8.0; Box Left has x <= -8.0; Box Right has x >= 8.0. An axle or pin passing along Z at (0, 0) has
#    zero intersection with any of the 4 boxes, completely eliminating false-positive axle collisions.
#
# Sockets are empty ([]): wheel rims mount via axle/pin connections and carry no bottom studs/sockets.
#
# Hand-verified against real resolved geometry for all 74 clean, undeformed, rotationally symmetric vehicle wheel
# rims in the library with outer diameter D >= 34.0 LDU (ensuring W >= 12.02 LDU > B = 8.0 LDU, so W - B >= 4.02 LDU).
#
# Deliberately unaddressed sub-groups (remain needs_occupancy=True):
# - Small wheel rims (D <= 28.0 LDU, W <= 8.0 LDU; e.g. 30027a-d, 34337, 42610, 50944, 6014a/b, 74967):
#   W <= 8.0 is smaller than or equal to the standard bore exclusion width, so 4 annular boxes cannot fit.
# - Composite shortcut assemblies (e.g. 3482c01, 30155c01, 2695c01): multi-part assemblies with tyres,
#   not atomic parts.
# - Wheels with integral/stub axles (e.g. 30190, 3464b, 50862, u9163, u9167): have protruding solid axle shafts.
# - Decorative wheel covers (e.g. 54086, 58088, 61738, 62359, 62701): thin cosmetic face clips.
# - Tracks/belts (43903-f1, 53992-f1..f3, 71965-f1, 85543-f5) and mechanisms (32060, 3465a, 4142).
# - Obsolete or incomplete parts (22969 obsolete, 55981 marked 'Needs Work', 2496 trolley, 3739 off-center).

WHEEL_BORE_HALF = 8.0  # Standard Technic axle/pin bore exclusion half-width (LDU)

WHEEL_PARTS = {
    # Hand-verified against real resolved geometry (bake_parts.py / resolve_part):
    "100942": (123.77, -47.0, 47.0),    # Wheel 37 x 45 Hard-Plastic with  6 Curved Spokes
    "105645": (125.08, -27.5, 27.5),    # Wheel 22 x 50 with Integral Smooth Racing Tyre
    "110638": (125.08, -27.5, 47.5),    # Wheel 30 x 50 with Integral Smooth Racing Tyre
    "11094": (155.74, -46.0, 26.0),     # Wheel 30 x 64 with  7 Pin Holes and  6 Small Holes
    "11208": (36.4, -12.5, 12.5),       # Wheel Rim 10 x 14 with Fake Bolts and  6 Spokes
    "15038": (140.0, -45.0, 39.0),      # Wheel Rim 34 x 56 with  6 Spokes and  6 Pegholes
    "1872": (37.5, -6.48, 4.0),         # Wheel Rim 11 x 18 Front with 36 Spokes and Knock-off Hub Nut
    "18978a": (37.5, -3.5, 4.0),        # Wheel Rim 11 x 18 Front with  5 Spokes
    "18978b": (37.5, -4.0, 4.0),        # Wheel Rim 11 x 18 Front with 10 Angled Spokes
    "18979a": (37.5, -3.5, 4.0),        # Wheel Rim 11 x 18 Front with  7 Y-Shaped Spokes
    "18979b": (37.5, -4.0, 4.0),        # Wheel Rim 11 x 18 Front with 10 Spokes
    "22253": (90.0, -31.0, 31.0),       # Wheel 25 x 28 VR with 35mm Diameter Rear Rim and Complete Cross Axle Hole
    "22410": (93.0, -26.52, 26.52),     # Wheel 21 x 37 Hard-Plastic with  7 Pin Holes
    "22969a": (152.0, -58.0, 58.0),     # Wheel 56 x 46 Technic Racing
    "23800": (156.0, -52.0, 52.0),      # Wheel Rim 42 x 62 with 10 Spokes and  3 Pegholes
    "24308a": (37.5, -4.0, 4.0),        # Wheel Rim 11 x 18 Front with 10 Parallel Spokes
    "24308b": (37.5, -4.5, 4.0),        # Wheel Rim 11 x 18 Front with 10 Y-Spokes
    "2470": (68.0, -12.0, 8.0),         # Wheel  2.8 x 27 with  8 Spokes
    "2515a": (139.99, -40.0, 40.0),     # Wheel 32 x 56 Hard-Plastic without Inner Supports
    "2593": (87.6, -38.0, 38.0),        # Wheel 30 x 35 with Tread on Sidewall
    "2695": (76.0, -24.0, 8.0),         # Wheel Rim 12.7 x 30 Stepped
    "27254": (155.64, -64.38, 30.0),    # Wheel 37 x 62 with Rocky Spikes and  7 Pegholes
    "2903": (158.52, -16.96, 16.96),    # Wheel Rim 14 x 62 Motorcycle
    "29117a": (37.5, -3.9, 4.0),        # Wheel Rim 11 x 18 Front with  5 Wide Spokes
    "29117b": (37.5, -4.1, 4.0),        # Wheel Rim 11 x 18 Front with  5 Split Spokes
    "2994": (60.0, -15.0, 20.0),        # Wheel 12 x 20 with Technic Axle Hole and 6 Pegholes
    "2996": (108.0, -37.0, 37.0),       # Wheel Rim 30 x 30 with 40mm Diameter Rear Rim
    "2998": (160.0, -40.0, 40.0),       # Wheel Rim 32 x 56 with Peghole and 6 Spokes with Pegholes
    "30155": (44.0, -8.0, 8.0),         # Wheel Rim  8 x 18 with 12 Spokes and Peghole
    "30285": (42.0, -17.0, 20.0),       # Wheel Rim 14.8 x 16.8 with Centre Groove
    "32004a": (108.0, -23.0, 22.0),     # Wheel Rim 18 x 41 Model Team Type  1
    "32004b": (108.0, -23.0, 22.0),     # Wheel Rim 18 x 41 Model Team Type  2
    "32020": (110.0, -32.0, 13.0),      # Wheel Rim 18 x 37 with 6 Pegholes and Long Axle Bush
    "32057": (148.0, -17.5, 17.5),      # Wheel Rim 14 x 60 with 3 Spokes and 3 Pegholes
    "32077": (150.0, -35.5, 35.59),     # Wheel Rim 28 x 60 with 3 Spokes and 3 Pegholes
    "32146": (76.0, -27.5, 10.0),       # Wheel 14 x 30 Smooth
    "32197": (172.0, -37.0, 37.0),      # Wheel Rim 30 x 61 with 3 Spokes Swirled
    "32219": (76.0, -18.0, 30.0),       # Wheel 14 x 30 Znap
    "32220": (172.0, -50.0, 10.0),      # Wheel 16 x 68 Znap
    "33211": (108.0, -24.0, 0.0),       # Wheel  3.2 x 43 with 10 Spokes Wooden
    "33212": (140.0, -24.0, 0.0),       # Wheel  3.2 x 56 with 10 Spokes Wooden
    "3482": (44.0, -10.0, 10.0),        # Wheel Rim  8 x 17.5 with Axlehole
    "39367": (140.0, -17.5, 17.5),      # Wheel 14 x 48 with 4 Spokes with Integral Tyre
    "41896": (108.0, -33.0, 33.0),      # Wheel Rim 26 x 43 with 6 Spokes and 3 Pegholes
    "4266": (76.0, -25.0, 25.0),        # Wheel Rim 20 x 30 Smooth with 6 Pinholes
    "42716": (76.0, -25.0, 25.0),       # Wheel Rim 20 x 30 "Torq Thrust" with  5 Spokes and External Ribs
    "44292": (76.01, -25.0, 25.0),      # Wheel Rim 20 x 30 with 3 Pegholes
    "44772": (140.0, -45.0, 39.0),      # Wheel Rim 34 x 56 with 6 Spokes and 3 Pegholes
    "4489a": (84.0, -12.0, 8.0),        # Wheel  2.8 x 34 with  8 Spokes with Round Hole for Wheel Holding Pin
    "4489b": (84.0, -12.0, 8.0),        # Wheel  2.8 x 34 with  8 Spokes with Notched Hole for Wheel Holding Pin
    "46334": (188.0, -20.0, 20.0),      # Wheel 16 x 75 Motorcycle Solid
    "49294": (140.0, -43.5, 42.0),      # Wheel Rim 34 x 56 with  6 Double Spokes and  6 Pegholes
    "49295": (219.53, -17.5, 17.5),     # Wheel 14 x 80 with  4 Spokes with Integral Tyre
    "51378": (187.0, -36.0, 15.0),      # Wheel Rim 20 x 75 with 6 Double Spokes
    "54087": (76.0, -25.0, 25.0),       # Wheel Rim 20 x 30 with  6 Spokes and No Pegholes
    "55982": (42.0, -17.0, 20.0),       # Wheel Rim 14 x 18 with Axlehole
    "56145": (76.0, -25.0, 25.0),       # Wheel Rim 20 x 30 with  6 Dual Spokes and External Ribs
    "56908": (108.0, -33.0, 33.0),      # Wheel Rim 26 x 43 with 6 Spokes and 6 Pegholes
    "60208": (76.0, -28.0, 10.0),       # Wheel Rim 16 x 31 with 6 Pegholes
    "6118": (60.0, -50.0, 8.0),         # Wheel 23 x 24 with Tread on Sidewall
    "6580a": (75.8, -29.0, 29.0),       # Wheel Rim 23 x 22 Offroad with Axlehole
    "6580b": (75.8, -29.0, 29.0),       # Wheel Rim 23 x 22 Offroad with Split Axlehole
    "6582": (92.0, -25.0, 25.0),        # Wheel Rim 20 x 33 with  6 Pinholes
    "65834": (108.0, -17.5, 17.5),      # Wheel 14 x 35 with 4 Spokes with Integral Tyre
    "6595": (90.0, -31.0, 31.0),        # Wheel 25 x 28 VR with 35mm Diameter Rear Rim and Partial Cross Axle Hole
    "66155": (76.0, -40.0, 40.0),       # Wheel Rim 20 x 30 with  3 Dual Angled Spokes and  4L Hub
    "68327": (100.0, -30.0, 10.0),      # Wheel 16 x 40 with  7 Pin Holes
    "71720": (268.0, -29.0, 29.0),      # Wheel 24 x 107 Motorcycle with  7 Spokes
    "72210a": (45.0, -4.0, 4.0),        # Wheel Rim 11 x 24 Front with  5 Spokes
    "72210b": (45.0, -4.0, 4.0),        # Wheel Rim 11 x 24 Front with  9 Spokes
    "7877": (140.0, -16.25, 16.25),     # Wheel Rim 13 x 56 with 12 Spokes and Axlehole
    "84772": (156.0, -25.0, 25.0),      # Wheel 20 x 62 Motorcycle Solid
    "86652": (110.0, -32.0, 13.0),      # Wheel Rim 18 x 37 with 6 Pegholes and Short Axle Bush
    "88517": (188.0, -21.25, 21.25),    # Wheel 17 x 75 Motorcycle with Holes in Rim
}


def wheel_occupancy(bounds_min, bounds_max=None, z_max=None, bore_half=WHEEL_BORE_HALF):
    """Returns an annular 4-box occupancy in the XY plane spanning Z, with the central
    axle/pin bore excluded to avoid false-positive collisions against mounting axles.
    Can be called with (bounds_min, bounds_max) or (diameter, z_min, z_max)."""
    if z_max is not None:
        diameter, z_min = bounds_min, bounds_max
    else:
        diameter = (bounds_max[0] - bounds_min[0] + bounds_max[1] - bounds_min[1]) / 2.0
        z_min, z_max = bounds_min[2], bounds_max[2]
    half_inscribed = diameter / (2 * math.sqrt(2))
    b = bore_half
    if half_inscribed <= b:
        return []
    return [
        box(-half_inscribed, half_inscribed, b, half_inscribed, z_min, z_max),
        box(-half_inscribed, half_inscribed, -half_inscribed, -b, z_min, z_max),
        box(-half_inscribed, -b, -b, b, z_min, z_max),
        box(b, half_inscribed, -b, b, z_min, z_max),
    ]


# One 20x20xheight box per stud actually present (real geometry, not guessed), used by two different families
# below for two different reasons -- see each dict's own comment for which:
def stud_cell_occupancy_and_sockets(module_h, studs):
    """studs: list of (pos, dir) in real LDU (not yet quantised). Every id using this MUST be checked first that
    all its studs sit at y=0 facing the normal up direction (-Y) -- a stud anywhere else (an "Inverted" or
    "Double" slope variant can have one partway up the ramp, at a non-zero y) means the simple "solid 20x20xheight
    cell under this stud" assumption this function makes does not hold, and the id must NOT be added here.
    Confirmed live 2026-09-26: 3665a and 3660a ("Inverted" 45-degree slopes) both have a second stud at y=4, not
    y=0 -- excluded from SLOPE_BACK_WALL_PARTS below for exactly this reason."""
    occ = [box(p[0] - 10, p[0] + 10, 0, module_h, p[2] - 10, p[2] + 10) for p, _ in studs]
    sockets = [((p[0], module_h, p[2]), (0, 1, 0)) for p, _ in studs]
    return occ, sockets


# Rectilinear corner bricks/plates (a clean N x N grid with exactly one corner cell missing, no curve at all --
# NOT the "Corner Round" family, which is a real curve and stays needs_occupancy=True): the stud-cell boxes are
# EXACT here, not an approximation -- each present stud position IS the centre of a genuinely solid 20x20 cell
# for these two ids. Verified against real baked stud positions: 2357/2420 both have exactly 3 studs at
# (0,0),(20,0),(0,20), so the combined 3-box envelope (x:[-10,30], z:[-10,30]) matches each part's own real
# baked bounds exactly.
CORNER_L_PARTS = {"2357": 24, "2420": 8}

# Slope bricks (angle encoded in the title -- 31/33/45/65/75 degrees -- but that angle is NOT used here at all):
# the stud-cell boxes cover only the flat, full-height "back wall" a slope's studs actually sit on, NOT the
# angled ramp itself (occupancy can only express axis-aligned boxes, and a tight staircase approximation of the
# real ramp was judged not worth the added risk for this pass) -- a deliberate UNDER-approximation, safe per
# spec §3 ("miss an overlap ... but never report a false one"): every box here is provably solid material (a
# stud cannot be moulded floating in air), so this can only ever under-report a collision on the ramp portion,
# never over-report one anywhere. Only ids where EVERY stud is confirmed at y=0 facing up are listed (checked
# individually against real baked connector data -- see stud_cell_occupancy_and_sockets' docstring for the two
# excluded "Inverted" ids this ruled out). Slopes with zero studs at all (3043, all "Curved" variants, the
# 0.667-height "31" variants) are NOT covered by this and stay needs_occupancy=True -- there is no stud to hang
# even this partial an approximation off, and guessing a bare box would have no real-geometry anchor at all.
#
# A SET, not an {id: height} dict like CORNER_L_PARTS -- most "Slope Brick N W x D" titles are one brick tall
# (24 LDU), but 60481a ("... 2 x 1 x 2 ...") and 4460b ("... 2 x 1 x 3 ...") are 2 and 3 bricks tall (48/72 LDU)
# respectively, per their own real baked bounds. A hardcoded 24 for these two (an earlier version of this table)
# gave a technically-still-safe but needlessly wrong occupancy height -- found by checking bounds height against
# the assumed constant for every id, not by inspection. Height is now always read from the part's own real
# bounds at the resolve_occupancy_and_sockets call site, never assumed.
SLOPE_BACK_WALL_PARTS = {"3040b", "3039", "4286", "3298", "3747b", "60481a", "4460b", "3037", "3038"}


# Hand-authored occupancy for parts whose plain LDraw geometry does not reduce to one clean box or the Technic-
# holes family above, verified against spec/brick-parts/fixtures-v0.1.json (F09, F15 exercise 3700 and 2780
# directly).
OVERRIDES = {
    # Technic pin (2L): a slim box along its axis; the friction ribs are cosmetic, not occupancy-relevant.
    "2780": [box(-20, 20, -6, 6, -6, 6)],
    "3673": [box(-20, 20, -6, 6, -6, 6)],
    "4274": [box(-20, 0, -6, 6, -6, 6)],   # pin lies along -x from its origin: bounds x -20..0
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


# A full-height occupancy box is NOT literally solid plastic for most real parts -- LEGO bricks are deliberately
# hollow underneath (open bottom, anti-stud tube structure), so even the CURRENTLY TRUSTED, hand-verified 81-part
# catalogue only measures 19-100% solid by this exact ray-parity test (part_checks.py, measured 2026-09-26): the
# most hollow accepted case is 4274 (a Technic pin) at 19.2%. 0.15 sits just below that real floor -- comfortable
# margin to accept ordinary hollow parts, while still catching a genuinely pathological candidate (a stud on a
# thin unconnected nub/bridge with real empty space beneath it), which registers near 0%, not merely "hollow."
STUD_CELL_MIN_SOLID = 0.15


def _stud_box_solid_fraction(tris, box_, n=48):
    """Fraction of n sample points inside `box_` that also lie inside the real mesh (ray-parity), used to PROVE a
    candidate occupancy box is genuinely solid before accepting it -- see generic_stud_cell_occupancy."""
    import numpy as np
    if not tris:
        return 0.0
    x0, x1, y0, y1, z0, z1 = box_
    rng = np.random.default_rng(20260926)
    pts = np.stack([rng.uniform(x0, x1, n), rng.uniform(y0, y1, n), rng.uniform(z0, z1, n)], axis=1)
    T = np.array([t[:3] for t in tris], dtype=float)   # tris may be (p0,p1,p2) or (p0,p1,p2,colour); colour ignored
    v0, v1, v2 = T[:, 0], T[:, 1], T[:, 2]
    e1, e2 = v1 - v0, v2 - v0
    d = np.array([1.0, 0.6180339887, 0.4142135624])   # deliberately irrational-ratio direction: low odds of exact
    d = d / np.linalg.norm(d)                          # algebraic alignment with axis-aligned or 45-degree LDraw geometry
    h = np.cross(d, e2)
    a = np.einsum("ij,ij->i", e1, h)
    ok = np.abs(a) > 1e-9
    v0, e1, e2, h, a = v0[ok], e1[ok], e2[ok], h[ok], a[ok]
    inside = np.zeros(len(pts), dtype=bool)
    for i in range(len(pts)):
        s = pts[i] - v0
        u = np.einsum("ij,ij->i", s, h) / a
        qv = np.cross(s, e1)
        v = qv @ d / a                       # v = dot(d, cross(s, e1)) / a -- must use the REAL ray direction d
        t = np.einsum("ij,ij->i", qv, e2) / a  # here, not qv[:,0] (only valid when d happens to be the x-unit vector,
        hit = (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-9)  # as in part_checks.py's fixed-direction inside_points)
        inside[i] = (hit.sum() % 2) == 1
    return float(inside.mean())


def generic_stud_cell_occupancy(bounds_min, bounds_max, studs, tris):
    """Library-wide fallback (2026-09-26, relaxed to per-stud 2026-09-27) for any part not covered by a named
    family above. The curated tables above (ROUND_PARTS, CORNER_L_PARTS, SLOPE_BACK_WALL_PARTS) all rest on the
    same underlying fact, verified BY HAND per id against real baked connector data: a stud sitting flush at y=0
    facing straight up always has solid material in a 20x20xheight column directly beneath it (a stud cannot be
    moulded floating in air). This generalises that verification into an automated, per-part geometric PROOF
    instead of hand-picking ids: for every stud that sits flush (y~=0, facing up), propose the same box the
    curated families use, then ray-cast sample points against the part's OWN real triangles and require at least
    STUD_CELL_MIN_SOLID of them to land inside the mesh.

    2026-09-27: originally a single non-flush or non-solid stud excluded the WHOLE part (needs_occupancy=True).
    Surveying the ~12,800 real rejects (scripts/ldraw/survey_rejects.py) found this all-or-nothing gate was the
    actual blocker for a large share of them, not a missing family rule: e.g. boat hull 164c01 has 34 flush studs,
    28 of which pass comfortably (0.6-0.85 solid) -- only the 6 studs in its tapered bow/stern row fail (0.06-0.08,
    genuinely thin material there), and the ALL-must-pass gate discarded all 34 over those 6. Relaxed to keep only
    the individual studs that pass (or are flush at all) and drop the rest -- each surviving box is still a real,
    individually-proven-solid PROOF, nothing is guessed, and dropping a failing/non-flush stud's cell is the same
    kind of safe under-approximation SLOPE_BACK_WALL_PARTS already relies on deliberately (spec section 3: miss a
    real collision on the dropped area, never report a false one). A part where EVERY stud fails or is non-flush
    still returns None (unchanged) -- there is nothing proven to offer.
    """
    if not studs or not tris or bounds_min is None or bounds_max is None:
        return None, []
    flush = [(p, d) for p, d in studs if abs(p[1]) < 0.5 and d[1] < -0.9]
    # NOTE: no `if not flush: return None, []` here -- a part can have ZERO up-facing studs and still have
    # real sideways (SNOT) ones the loop below checks (e.g. 11097, all 3 studs sideways, 0 flush). The
    # final `if not boxes: return None, []` after both passes is the real bail-out.
    # Span the box over the part's OWN real y extent, not an assumed y:[0, height] -- found live, 2026-09-26:
    # ordinary bricks have bounds_min[1]==0 (origin at the top surface), but plenty of real parts don't (a
    # baseplate's origin sits at its vertical CENTRE, e.g. bounds y:[-4,+4]; a mudguard/curved-slope's flare can
    # rise above the stud plane, e.g. bounds y:[-12,+8]) -- hardcoding [0, bounds_max-bounds_min] silently shifted
    # every such box off the part's real geometry, caught by pipeline.py's gate (456/2854 parts flagged: every
    # occupancy box landing partly or wholly outside the part's own declared bounds). Using the real bounds
    # instead is self-limiting via the existing ray-parity proof below: a genuinely too-tall box (mostly empty at
    # the extremes) fails STUD_CELL_MIN_SOLID on its own, no separate special-casing needed.
    y0, y1 = bounds_min[1], bounds_max[1]
    kept = [p for p, _ in flush if _stud_box_solid_fraction(
        tris, box(p[0] - 10, p[0] + 10, y0, y1, p[2] - 10, p[2] + 10)) >= STUD_CELL_MIN_SOLID]
    boxes = [box(p[0] - 10, p[0] + 10, y0, y1, p[2] - 10, p[2] + 10) for p in kept]
    sockets = [((p[0], y1, p[2]), (0, 1, 0)) for p in kept]

    # SNOT (Studs Not On Top) addition, 2026-09-27: a stud facing sideways (X or Z, not Y) was previously
    # excluded from this whole function entirely by the `flush` filter above, which only recognises the
    # up-facing case -- found live surveying real rejects: "Minifig Armour Shoulder Pads with 1 Stud on
    # Front, 2 Studs on Back" (11097) has 3 real studs, all sideways (dir (0,0,-1)/(0,0,1)), individually
    # ~17-19% solid -- healthy, comparable to other accepted parts -- but the up-only flush check discarded
    # the whole part regardless. Generalises the SAME ray-cast proof to any axis-aligned stud direction,
    # deliberately WITHOUT copying the Y-axis path's `abs(p[1]) < 0.5` position pre-filter: that check
    # encodes a real LDraw convention specific to Y (an ordinary brick's own local origin sits at y=0, its
    # top stud surface) that has no equivalent for X/Z -- there's no universal "sideways studs sit at
    # x/z=0" convention to check against. The ray-cast solid-fraction proof is the actual safety
    # mechanism either way (a stud on a ramp's raised nub still needs a real solid column to pass, position
    # or not); dropping an inapplicable heuristic is not the same as dropping the proof. Left as fully
    # separate code (not merged into the `flush` list above) so the proven Y-axis path is byte-for-byte
    # unchanged -- zero regression risk on already-verified results.
    for p, d in studs:
        axis = max(range(3), key=lambda i: abs(d[i]))
        if axis == 1 or abs(d[axis]) <= 0.9:
            continue   # Y-axis studs already handled above; a non-axis-aligned direction is never a real stud
        sign = 1.0 if d[axis] > 0 else -1.0
        spans = [None, None, None]
        spans[axis] = (bounds_min[axis], bounds_max[axis])
        for other in range(3):
            if other != axis:
                spans[other] = (p[other] - 10, p[other] + 10)
        b = _axis_box(axis, spans)
        if _stud_box_solid_fraction(tris, b) >= STUD_CELL_MIN_SOLID:
            boxes.append(b)
            sdir = [0.0, 0.0, 0.0]
            sdir[axis] = sign
            sockets.append((tuple(p), tuple(sdir)))

    if not boxes:
        return None, []
    return boxes, sockets


def _axis_box(bore, spans):
    """spans: {axis_index: (lo, hi)} for all three axes -- returns the box() 6-tuple regardless of which axis
    is which (the channel builder below works in axis-index terms, not x/y/z names, so it can reuse the same
    logic no matter which real axis a given part's holes bore through)."""
    return box(*spans[0], *spans[1], *spans[2])


def generic_hole_channel_occupancy(bounds_min, bounds_max, studs, holes, tris):
    """Generalises technic_holes_occupancy (hand-verified 2026-09-26 for 7 straight-beam ids, ALWAYS bored along
    Z with holes spaced along X) to any part whose holes bore straight through along one shared axis -- X, Y or
    Z, not just Z -- and are spaced along a second axis at one shared position on the third. That's the real
    shape of an ordinary Technic beam/liftarm/panel, just not always oriented the same way as the original 7.

    Unlike the hand-verified original, this runs on parts NOBODY has checked individually, so it does not trust
    the parametric channel construction alone: every proposed box is ray-cast verified solid first (reusing
    _stud_box_solid_fraction, the same proof generic_stud_cell_occupancy uses), and if even one box in the
    result fails, the WHOLE part is excluded (needs_occupancy=True) -- no partial credit here, unlike the stud
    relaxation above, since a hole-channel construction's boxes are interdependent (each one only correctly
    represents "solid" if the geometry really is the assumed straight-beam-with-holes shape throughout).

    Bails (returns None, []) rather than guess whenever the assumed shape doesn't hold: holes that don't all
    bore along one shared axis, holes spread across BOTH remaining axes (a true 2D hole grid, e.g. a perforated
    panel -- a materially different shape this decomposition can't express), or any box that fails the solidity
    proof.
    """
    if not holes or not tris or bounds_min is None or bounds_max is None:
        return None, []
    AXES = (0, 1, 2)
    bore = next((ax for ax in AXES if all(abs(d[ax]) > 0.9 for _, d in holes)), None)
    if bore is None:
        return None, []
    other = [a for a in AXES if a != bore]
    spread = {a: max(p[a] for p, _ in holes) - min(p[a] for p, _ in holes) for a in other}
    varying = [a for a in other if spread[a] > 1.0]
    if len(varying) > 1:
        return None, []
    space_axis = varying[0] if varying else other[0]
    const_axis = other[1] if space_axis == other[0] else other[0]
    const_val = round(sum(p[const_axis] for p, _ in holes) / len(holes))

    lo = [bounds_min[0], bounds_min[1], bounds_min[2]]
    hi = [bounds_max[0], bounds_max[1], bounds_max[2]]
    full_bore = (lo[bore], hi[bore])
    full_const = (lo[const_axis], hi[const_axis])
    positions = sorted(set(round(p[space_axis]) for p, _ in holes))

    boxes, prev = [], lo[space_axis]
    for s in positions:
        if s - CHANNEL_HALF > prev:
            spans = {bore: full_bore, const_axis: full_const, space_axis: (prev, s - CHANNEL_HALF)}
            boxes.append(_axis_box(bore, spans))
        for k_lo, k_hi in ((lo[const_axis], const_val - CHANNEL_HALF), (const_val + CHANNEL_HALF, hi[const_axis])):
            if k_hi > k_lo:
                spans = {bore: full_bore, const_axis: (k_lo, k_hi), space_axis: (s - CHANNEL_HALF, s + CHANNEL_HALF)}
                boxes.append(_axis_box(bore, spans))
        prev = s + CHANNEL_HALF
    if prev < hi[space_axis]:
        spans = {bore: full_bore, const_axis: full_const, space_axis: (prev, hi[space_axis])}
        boxes.append(_axis_box(bore, spans))
    if not boxes:
        return None, []
    for b in boxes:
        if _stud_box_solid_fraction(tris, b) < STUD_CELL_MIN_SOLID:
            return None, []

    flush = [(p, d) for p, d in (studs or []) if abs(p[1]) < 0.5 and d[1] < -0.9]
    sockets = [((p[0], hi[1], p[2]), (0, 1, 0)) for p, _ in flush]
    return boxes, sockets


# Bar-grip detection (2026-09-27): a "held" part (minifig accessory, tool, weapon -- also technic/door pivot
# pins, which are the same physical connector, just clip-mounted instead of hand-held) has a cylindrical grip of
# radius 4 LDU -- confirmed against two independent real references: a genuine "Bar 8L" part (2714a) measures
# exactly radius 4, and the standard clip1.dat primitive's own inner opening is also exactly radius 4 -- the real
# LEGO/LDraw bar-clip manufacturing standard, not a fitted constant. A raw radius match alone over-triggers
# (v1 prototype: 3,514 hits across categories that clearly aren't held items -- Windscreen, Wheel, Door, Brick --
# because plenty of unrelated features, hinge posts, axle stubs, technic bosses, share the same standard radius).
# Two more checks bring it down to genuine grips (prototype v2: 1,814 hits, false positives gone on inspection):
#   1. EXTREMITY: a real grip sticks out to the part's own bounding-box edge; an embedded post does not.
#   2. ISOLATION: a real grip is a thin rod protruding from a much narrower stem -- a ray-cast box straddling its
#      base, just wider than the rod itself, is mostly EMPTY. An embedded post's equivalent box is mostly solid
#      (it's flush inside the part's main body). Reuses _stud_box_solid_fraction, the same proof the stud/hole
#      paths use, just checking for LOW solid fraction instead of high.
# These parts don't need occupancy at all -- nothing is ever stacked on a held sword or a hinge pin -- so a match
# here means "genuinely no occupancy claim, not a guess", the same honest empty-occupancy the DISH_PARTS family
# also intentionally uses. Sockets are deliberately left empty too: a bar/clip connector pair is a real, different
# attachment TYPE (not a stud/socket), and this data model doesn't yet have anywhere to safely express it end to
# end (see BRICK_CATALOGUE_STATUS.md scoping note) -- claiming a socket here would be exactly the kind of
# fabricated connection data this module's own convention (CONNECTOR_OVERRIDES's docstring, sockets=[] pattern in
# DISH_PARTS) already refuses to do.
BAR_RADIUS = 4.0
BAR_RADIUS_TOL = 0.4
BAR_EXTREMITY_TOL = 3.0
BAR_ISOLATION_MAX_SOLID = 0.35


def _cluster_cylinders(cylinders):
    hits = [(centre, axis, radius) for centre, axis, radius in cylinders if abs(radius - BAR_RADIUS) <= BAR_RADIUS_TOL]
    clusters = []
    for centre, axis, radius in hits:
        length = (axis[0] ** 2 + axis[1] ** 2 + axis[2] ** 2) ** 0.5
        placed = False
        for c in clusters:
            if math.dist(c["centre"], centre) < 2.0:
                c["length"] = max(c["length"], length)
                placed = True
                break
        if not placed:
            clusters.append({"centre": centre, "axis": axis, "length": length})
    return clusters


def _at_extremity(p, bounds_min, bounds_max):
    return any(abs(p[i] - bounds_min[i]) <= BAR_EXTREMITY_TOL or abs(p[i] - bounds_max[i]) <= BAR_EXTREMITY_TOL
               for i in range(3))


def bar_grip_points(bounds_min, bounds_max, cylinders, tris):
    """Returns a list of (pos, dir) for every genuine bar/clip-type grip on this part -- pos is the rod's own
    OUTER tip (where a hand/clip would actually grip it), dir is the unit vector pointing outward along the
    rod's axis (inner attachment -> outer tip), the same "axis of insertion" convention part.pins already uses
    for technic friction pins -- a bar grip is physically the same kind of connector (a rod mating with a
    receiving socket-shaped feature), just clip/hand-held instead of pin/hole-mated. See the module-level
    comment above for the two-check detection method (extremity + isolation) and why it's needed beyond a bare
    radius match. A part can genuinely have more than one grip (e.g. a double-ended bar), so this returns all
    of them, not just the first. Empty list (not None/False) when there's no genuine grip, so callers can use
    it directly as a falsy/truthy check (`if bar_grip_points(...):`) exactly like the old has_bar_grip did."""
    if not cylinders or not tris or bounds_min is None or bounds_max is None:
        return []
    grips = []
    for c in _cluster_cylinders(cylinders):
        if c["length"] < 4:
            continue
        # `centre` is the primitive's local origin, which is one TRUE END (cyli/cylo span local Y 0..1, not
        # -0.5..+0.5) -- the other true end is centre + axis (axis already has magnitude == length).
        end_a = c["centre"]
        end_b = tuple(c["centre"][i] + c["axis"][i] for i in range(3))
        if _at_extremity(end_a, bounds_min, bounds_max):
            outer, inner = end_a, end_b
        elif _at_extremity(end_b, bounds_min, bounds_max):
            outer, inner = end_b, end_a
        else:
            continue
        axis_len = c["length"] or 1.0
        u = tuple(c["axis"][i] / axis_len for i in range(3))
        # probe box centred half a rod-length further INWARD of the attachment end, radius 7 (just past the
        # rod's own radius 4) -- empty here means a thin rod on a narrow stem; solid means an embedded post.
        p = tuple(inner[i] - u[i] * c["length"] * 0.5 for i in range(3))
        probe = box(p[0] - 7, p[0] + 7, p[1] - 7, p[1] + 7, p[2] - 7, p[2] + 7)
        if _stud_box_solid_fraction(tris, probe) <= BAR_ISOLATION_MAX_SOLID:
            # direction points OUTWARD (inner -> outer), i.e. away from the part's body, matching "axis of
            # insertion" pointing out of the part the way a pin's axis points out of its part.
            out_dir = tuple(outer[i] - inner[i] for i in range(3))
            out_len = (out_dir[0] ** 2 + out_dir[1] ** 2 + out_dir[2] ** 2) ** 0.5 or 1.0
            grips.append((outer, tuple(d / out_len for d in out_dir)))
    return grips


# Minifig headwear (2026-09-27): a hair/helmet/hat/headdress/cap/mask/crown part mounts by RECEIVING the
# head's own real top stud (confirmed live: the curated head part 3626bp01's own title literally says
# "Blocked Hollow Stud") -- so it needs a socket, not occupancy (nothing is ever stacked on top of a hat in
# normal building). The mount point is the part's own LOCAL ORIGIN (0,0,0), not a bounding-box computation
# -- this is NOT a guess: `characters.py`'s OFFSETS table already places both "head" and "headgear" at the
# identical relative offset from the torso's neck, and that file's own minifig templates already compose 16
# real characters successfully on this exact convention (LDraw authors every minifig accessory with its own
# origin AT its attachment point, the same way a stud's or a pin's local origin IS its own connector
# position). Direction faces down (0,-1,0) to receive an upward-facing stud, matching the existing
# stud/socket opposite-direction convention `renderers/brick_parts_validate.py` already uses. Title
# prefixes are the real ones found sampling the actual reject pool (scripts/ldraw/survey_rejects.py), not
# guessed -- covering roughly 3/4 of the real "Minifig Headwear" category by sampled count.
MINIFIG_HEADWEAR_PREFIXES = ("minifig hair", "minifig helmet", "minifig hat", "minifig headdress",
                              "minifig cap", "minifig mask", "minifig crown")


def minifig_headwear_socket(title):
    """Returns a single (pos, dir) socket list if `title` matches a real minifig headwear family, else None."""
    t = (title or "").strip().lower()
    if any(t.startswith(p) for p in MINIFIG_HEADWEAR_PREFIXES):
        return [((0.0, 0.0, 0.0), (0.0, -1.0, 0.0))]
    return None


def _boxes_within_bounds(occ, bounds_min, bounds_max, tol=0.5):
    """True if every box in `occ` fits inside [bounds_min-tol, bounds_max+tol] on all three axes. Skipped (treated
    as passing) when bounds aren't supplied, matching this module's existing "bounds/studs/tris are optional"
    contract for callers that don't have real geometry (e.g. unit tests exercising one family in isolation)."""
    if bounds_min is None or bounds_max is None:
        return True
    lo = [bounds_min[i] - tol for i in range(3)]
    hi = [bounds_max[i] + tol for i in range(3)]
    for x0, x1, y0, y1, z0, z1 in occ:
        if x0 < lo[0] or x1 > hi[0] or y0 < lo[1] or y1 > hi[1] or z0 < lo[2] or z1 > hi[2]:
            return False
    return True


def resolve_occupancy_and_sockets(part_id, title, bounds_min=None, bounds_max=None, holes=None, studs=None,
                                   tris=None, cylinders=None):
    """Returns (occupancy_boxes_or_None, sockets, needs_occupancy_bool). bounds/holes/studs (real LDU,
    unquantised) are only needed for the Technic-holes/round/corner-L/slope families and the generic fallback;
    every other path ignores them, so existing callers that omit them keep working. `tris`: the part's own real
    triangles (list of (p0,p1,p2)), needed only by the generic fallback's geometric proof. `cylinders`: list of
    (centre, axis, radius) from resolve.py's cyli/cylo primitive detection, needed only by has_bar_grip.

    EVERY path's result is verified against the part's own real bounds before being trusted (2026-09-26): found
    live expanding the catalogue past the original 116 that generated_occupancy's title-based box assumes a
    part's footprint is CENTRED on its origin, which is not universal -- id 3176 ("Plate 3 x 2 with Hole") has a
    genuinely off-centre real footprint (an asymmetric extension "with Hole" doesn't rule out), producing a box
    that overshoots the part's real bounds on one side. This was a LATENT bug in the pre-existing, previously-
    trusted plain-box path -- it just never triggered against the original hand-picked 116, since none of them
    happened to be asymmetric. Caught by pipeline.py's gate, not by inspection.
    """
    def verified(occ, sockets):
        return (occ, sockets, False) if _boxes_within_bounds(occ, bounds_min, bounds_max) else (None, [], True)

    if part_id in ROUND_PARTS:
        occ, sockets = round_occupancy_and_sockets(*ROUND_PARTS[part_id])
        return verified(occ, sockets)
    if part_id in DISH_PARTS:
        return verified(dish_occupancy(*DISH_PARTS[part_id]), [])
    if part_id in TYRE_PARTS:
        if bounds_min is not None and bounds_max is not None:
            occ = tyre_occupancy(bounds_min, bounds_max)
        else:
            occ = tyre_occupancy(*TYRE_PARTS[part_id])
        return verified(occ, [])
    if part_id in WHEEL_PARTS:
        if bounds_min is not None and bounds_max is not None:
            occ = wheel_occupancy(bounds_min, bounds_max)
        else:
            occ = wheel_occupancy(*WHEEL_PARTS[part_id])
        return verified(occ, [])
    if part_id in CORNER_L_PARTS and studs is not None:
        occ, sockets = stud_cell_occupancy_and_sockets(CORNER_L_PARTS[part_id], studs)
        return verified(occ, sockets)
    if part_id in SLOPE_BACK_WALL_PARTS and studs is not None and bounds_min and bounds_max:
        occ, sockets = stud_cell_occupancy_and_sockets(bounds_max[1] - bounds_min[1], studs)
        return verified(occ, sockets)
    headwear_sockets = minifig_headwear_socket(title)
    if headwear_sockets is not None:
        return [], headwear_sockets, False
    occ = OVERRIDES.get(part_id) or generated_occupancy(title)
    if occ is None and part_id in TECHNIC_HOLES_PARTS and bounds_min and holes is not None:
        occ = technic_holes_occupancy(bounds_min, bounds_max, holes)
    if occ is None:
        gen_occ, gen_sockets = generic_stud_cell_occupancy(bounds_min, bounds_max, studs, tris)
        if gen_occ:
            return verified(gen_occ, gen_sockets)
        gen_occ, gen_sockets = generic_hole_channel_occupancy(bounds_min, bounds_max, studs, holes, tris)
        if gen_occ:
            return verified(gen_occ, gen_sockets)
        if bar_grip_points(bounds_min, bounds_max, cylinders, tris):
            # occupancy/sockets stay empty here (unchanged contract) -- the real grip position/axis data is
            # exposed separately via bar_grip_points() itself, called directly by bake_parts.py, so it can go
            # into its own `bars` connector field rather than being force-fit into this function's plain
            # (occ, sockets, needs_occupancy) return shape, which every existing caller already depends on.
            return [], [], False
        return (None, [], True)
    sockets = generate_sockets(occ)
    over = CONNECTOR_OVERRIDES.get(part_id, {})
    if "sockets" in over:
        sockets = over["sockets"]
    return verified(occ, sockets)
