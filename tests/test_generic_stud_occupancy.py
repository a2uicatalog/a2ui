"""scripts/ldraw/parts.py's generic_stud_cell_occupancy (2026-09-26): the library-wide occupancy fallback that lets
the catalogue expand past the hand-curated ROUND_PARTS/CORNER_L_PARTS/SLOPE_BACK_WALL_PARTS tables without hand-
verifying each new part id. It generalises those tables' own justification (a stud flush at y=0 facing up always
has solid material beneath it) into an automated ray-parity PROOF against the part's own real triangles, so a
candidate is only ever accepted once it is actually geometrically demonstrated, never assumed from title/shape
alone. These tests use synthetic geometry (no LDraw library needed, so they run in CI) plus, where the fetched
library is present, real curated parts to prove parity with the hand-verified tables it is meant to subsume."""
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "ldraw"))
import parts as P  # noqa: E402

LDRAW_CACHE = Path(__file__).resolve().parent.parent / "scripts" / "ldraw" / "_ldraw_cache" / "ldraw"


def _box_tris(x0, x1, y0, y1, z0, z1):
    """A closed 12-triangle box (outward winding doesn't matter for ray-parity, which only counts crossings)."""
    v = {(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)}
    faces = [((x0, y0, z0), (x0, y1, z0), (x0, y1, z1), (x0, y0, z1)),
             ((x1, y0, z0), (x1, y0, z1), (x1, y1, z1), (x1, y1, z0)),
             ((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)),
             ((x0, y0, z1), (x0, y1, z1), (x1, y1, z1), (x1, y0, z1)),
             ((x0, y0, z0), (x0, y0, z1), (x1, y0, z1), (x1, y0, z0)),
             ((x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1))]
    del v
    tris = []
    for a, b, c, d in faces:
        tris.append((a, b, c))
        tris.append((a, c, d))
    return tris


def test_solid_fraction_of_a_box_sampled_inside_itself_is_one():
    tris = _box_tris(-10, 10, 0, 24, -10, 10)
    assert P._stud_box_solid_fraction(tris, (-10, 10, 0, 24, -10, 10)) == pytest.approx(1.0)


def test_solid_fraction_of_empty_space_is_zero():
    tris = _box_tris(-10, 10, 0, 24, -10, 10)   # a solid box far from the sampled region
    assert P._stud_box_solid_fraction(tris, (100, 120, 0, 24, 100, 120)) == 0.0


def test_generic_occupancy_accepts_a_plain_flush_stud():
    tris = _box_tris(-10, 10, 0, 24, -10, 10)
    studs = [((0.0, 0.0, 0.0), (0.0, -1.0, 0.0))]
    occ, sockets = P.generic_stud_cell_occupancy((-10, 0, -10), (10, 24, 10), studs, tris)
    assert occ == [(-10.0, 10.0, 0, 24.0, -10.0, 10.0)]
    assert sockets == [((0.0, 24, 0.0), (0, 1, 0))]


def test_generic_occupancy_drops_a_non_flush_stud_but_keeps_the_flush_one():
    """An 'Inverted' slope's second stud sits partway up the ramp (y=4, not y=0). 2026-09-27: the all-or-nothing
    gate that used to reject the WHOLE part over one non-flush stud was relaxed (see generic_stud_cell_occupancy's
    docstring) -- a real boat hull (164c01) has 34 flush studs where only 6 edge ones failed the solidity proof,
    and discarding all 34 over those 6 was the actual blocker for a large share of the real reject pool, not a
    missing family rule. Each surviving box is still individually ray-cast proven solid; the non-flush stud is
    still correctly excluded from EVER getting a box (there is no 'beneath' for it to be proven against), it just
    no longer poisons its flush sibling. Mirrors 3665a/3660a's real behaviour (see the parametrized test below)."""
    tris = _box_tris(-10, 10, 0, 24, -10, 10)
    studs = [((0.0, 0.0, 0.0), (0.0, -1.0, 0.0)), ((0.0, 4.0, 0.0), (0.0, -1.0, 0.0))]
    occ, sockets = P.generic_stud_cell_occupancy((-10, 0, -10), (10, 24, 10), studs, tris)
    assert occ == [(-10.0, 10.0, 0, 24.0, -10.0, 10.0)]
    assert sockets == [((0.0, 24, 0.0), (0, 1, 0))]


def test_generic_occupancy_keeps_both_a_flush_stud_and_a_real_sideways_one():
    """A flush (up-facing) stud and a SNOT (sideways) stud on the same synthetic part each get their own
    independently-proven box now (2026-09-27 SNOT addition, see the module-level comment on
    generic_stud_cell_occupancy) -- the sideways box spans the part's full bounds only along ITS OWN axis
    (Z here), +/-10 on the other two, the direct generalisation of how the flush box already spans full
    bounds only along Y. Real 11211 needs its OVERRIDES entry regardless for the full-body footprint
    (covered by the parametrized test below); this only exercises the generic function directly."""
    tris = _box_tris(-10, 10, 0, 24, -10, 10)
    studs = [((0.0, 0.0, 0.0), (0.0, -1.0, 0.0)), ((0.0, 12.0, -10.0), (0.0, 0.0, -1.0))]
    occ, sockets = P.generic_stud_cell_occupancy((-10, 0, -10), (10, 24, 10), studs, tris)
    assert sorted(occ) == sorted([(-10.0, 10.0, 0, 24.0, -10.0, 10.0), (-10.0, 10.0, 2.0, 22.0, -10, 10)])
    assert sorted(sockets) == sorted([((0.0, 24, 0.0), (0, 1, 0)), ((0.0, 12.0, -10.0), (0.0, 0.0, -1.0))])


def test_generic_occupancy_rejects_a_stud_on_a_floating_nub():
    """A stud whose 20x20xheight column is mostly empty air (attached only by a thin bridge far outside the
    sampled column, never registering) must be rejected -- this is exactly the failure mode the ray-parity proof
    exists to catch, distinct from a merely-hollow-underneath ordinary brick (see the module docstring)."""
    thin_bridge = [((-0.5, 0, -0.5), (0.5, 0, -0.5), (0.5, 24, -0.5)), ((-0.5, 0, -0.5), (0.5, 24, -0.5), (-0.5, 24, -0.5))]
    studs = [((0.0, 0.0, 0.0), (0.0, -1.0, 0.0))]
    occ, _ = P.generic_stud_cell_occupancy((-0.5, 0, -0.5), (0.5, 24, -0.5), studs, thin_bridge)
    assert occ is None


def test_generic_occupancy_uses_the_parts_own_real_y_extent_not_a_zero_based_assumption():
    """Found live 2026-09-26 baking the full library (real part 809, a Baseplate): the stud itself is flush at
    y=0 as always, but the part's declared bounds are y:[-4,+4] -- a raised rim rises 4 LDU ABOVE the stud plane
    (unlike an ordinary brick, whose top surface and bounds_min both sit at y=0). A box hardcoded to y:[0, height]
    silently shifted every stud's box off the part's real geometry on both ends, caught by pipeline.py's gate
    (456/2854 parts flagged in that run, all the same root cause). The box must span the part's OWN declared y
    bounds, whatever they are, not an assumed y:[0, bounds_max-bounds_min]."""
    tris = _box_tris(-10, 10, -4, 4, -10, 10)   # solid material from y=-4 to y=+4, NOT y=0 to y=8
    studs = [((0.0, 0.0, 0.0), (0.0, -1.0, 0.0))]   # the stud is still flush at y=0, per real baked data
    occ, sockets = P.generic_stud_cell_occupancy((-10, -4, -10), (10, 4, 10), studs, tris)
    assert occ == [(-10.0, 10.0, -4, 4, -10.0, 10.0)]
    assert sockets == [((0.0, 4, 0.0), (0, 1, 0))]


def test_generic_occupancy_needs_bounds_and_tris_and_studs():
    tris = _box_tris(-10, 10, 0, 24, -10, 10)
    studs = [((0.0, 0.0, 0.0), (0.0, -1.0, 0.0))]
    assert P.generic_stud_cell_occupancy(None, (10, 24, 10), studs, tris) == (None, [])
    assert P.generic_stud_cell_occupancy((-10, 0, -10), (10, 24, 10), [], tris) == (None, [])
    assert P.generic_stud_cell_occupancy((-10, 0, -10), (10, 24, 10), studs, []) == (None, [])


def test_dispatcher_prefers_named_families_and_overrides_over_the_generic_fallback():
    """The generic fallback must be the LAST resort: a part in ROUND_PARTS/OVERRIDES/etc. must still get that
    table's own (possibly different) result, not the generic one, even though the generic path might also apply."""
    occ, sockets, needs = P.resolve_occupancy_and_sockets("2780", "Technic Pin", studs=[], tris=[])
    assert occ == P.OVERRIDES["2780"] and needs is False


@pytest.mark.skipif(not LDRAW_CACHE.exists(), reason="LDraw library not fetched (scripts/ldraw/fetch_library.py)")
def test_generic_fallback_stays_within_bounds_for_a_non_zero_origin_real_part():
    """Real regression case for the y-bounds bug above: part 809 (Baseplate 24x40 ...), bounds y:[-4,+4]."""
    from resolve import Library, ColourTable, resolve_part
    lib = Library(str(LDRAW_CACHE))
    colours = ColourTable(lib)
    part = resolve_part(lib, colours, "809.dat")
    occ, sockets = P.generic_stud_cell_occupancy(part.min, part.max, part.studs, part.tris)
    assert occ is not None, "809 should be accepted now that the box spans its real y bounds"
    for x0, x1, y0, y1, z0, z1 in occ:
        assert part.min[0] - 0.5 <= x0 and x1 <= part.max[0] + 0.5
        assert part.min[1] - 0.5 <= y0 and y1 <= part.max[1] + 0.5
        assert part.min[2] - 0.5 <= z0 and z1 <= part.max[2] + 0.5


@pytest.mark.skipif(not LDRAW_CACHE.exists(), reason="LDraw library not fetched (scripts/ldraw/fetch_library.py)")
def test_generic_fallback_reproduces_the_curated_corner_l_result_exactly():
    from resolve import Library, ColourTable, resolve_part
    lib = Library(str(LDRAW_CACHE))
    colours = ColourTable(lib)
    part = resolve_part(lib, colours, "2357.dat")
    curated_occ, curated_sockets = P.stud_cell_occupancy_and_sockets(P.CORNER_L_PARTS["2357"], part.studs)
    gen_occ, gen_sockets = P.generic_stud_cell_occupancy(part.min, part.max, part.studs, part.tris)
    assert sorted(gen_occ) == sorted(curated_occ)
    assert sorted(gen_sockets) == sorted(curated_sockets)


# pid -> expected occ after the 2026-09-27 per-stud relaxation: only each part's genuinely flush (or, since
# the same day's later SNOT addition, genuinely sideways-and-solid) individually-proven studs contribute a
# box now (real values, checked against a live resolve, not asserted blind).
# 11211 has 2 flush top studs AND 2 real sideways (SNOT) studs, both individually solid-proven now -- 4
# boxes total, a SMALLER, different footprint than 11211's own OVERRIDES entry (a full 1x2 body) either
# way, so the dispatcher must still prefer OVERRIDES over this generic result (covered by
# test_dispatcher_prefers_named_families_and_overrides... above) -- production behaviour for 11211 is
# unaffected by the SNOT addition, only this direct unit-level call on the generic function itself.
# 3665a/3660a each have their ramp-side stud(s) at y=4 excluded -- that stud is Y-axis (dir (0,-2,0)), which
# the SNOT path deliberately never touches (it only ever handles X/Z-axis studs), so these two are unchanged.
_RELAXED_REAL_PARTS = {
    "11211": [(0.0, 20.0, 0.0, 24.0, -10.0, 10.0), (-20.0, 0.0, 0.0, 24.0, -10.0, 10.0),
              (0.0, 20.0, 0.0, 20.0, -10.0, 10.0), (-20.0, 0.0, 0.0, 20.0, -10.0, 10.0)],
    "3665a": [(-10.0, 10.0, 0.0, 24.0, -10.0, 10.0)],
    "3660a": [(0.0, 20.0, 0.0, 24.0, -10.0, 10.0), (-20.0, 0.0, 0.0, 24.0, -10.0, 10.0)],
}


@pytest.mark.skipif(not LDRAW_CACHE.exists(), reason="LDraw library not fetched (scripts/ldraw/fetch_library.py)")
@pytest.mark.parametrize("pid", ["11211", "3665a", "3660a"])
def test_generic_fallback_keeps_only_the_flush_studs_on_real_non_flush_parts(pid):
    from resolve import Library, ColourTable, resolve_part
    lib = Library(str(LDRAW_CACHE))
    colours = ColourTable(lib)
    part = resolve_part(lib, colours, pid + ".dat")
    occ, _ = P.generic_stud_cell_occupancy(part.min, part.max, part.studs, part.tris)
    assert occ is not None, "%s has at least one genuinely flush, solid-proven stud and should not be rejected outright" % pid
    assert sorted(occ) == sorted(_RELAXED_REAL_PARTS[pid])


# ── Tyres Family (TYRE_PARTS) ──────────────────────────────────────────────────

def test_tyre_occupancy_pure_math():
    """Tyre occupancy box is an inscribed square in the circular cross-section (XY plane), spanning Z width."""
    # Symmetric 50 LDU diameter, z in [-14, 14]
    half50 = 50.0 / (2 * math.sqrt(2))
    occ = P.tyre_occupancy(50.0, -14.0, 14.0)
    assert occ == [(-half50, half50, -half50, half50, -14.0, 14.0)]

    # From bounds: diameter = 70, z_min = -20, z_max = 10 (asymmetric Z)
    half70 = 70.0 / (2 * math.sqrt(2))
    occ_bounds = P.tyre_occupancy((-35.0, -35.0, -20.0), (35.0, 35.0, 10.0))
    assert occ_bounds == [(-half70, half70, -half70, half70, -20.0, 10.0)]


def test_dispatcher_resolves_tyre_parts_with_exact_values():
    """TYRE_PARTS resolves to an inscribed square in XY, spanning Z, with empty sockets and needs_occupancy=False."""
    # 6015: "Tyre 12/ 40 x 11 Wide" -- diameter 50 LDU, z: [-14.0, 14.0]
    half_6015 = 50.0 / (2 * math.sqrt(2))  # 17.677669529663685
    occ, sockets, needs = P.resolve_occupancy_and_sockets("6015", "Tyre 12/ 40 x 11 Wide")
    assert needs is False
    assert sockets == []
    assert occ == [(-half_6015, half_6015, -half_6015, half_6015, -14.0, 14.0)]

    # 30028b: "Tyre  8/ 40 x  8 Slick Smooth" -- diameter 36 LDU, z: [-10.0, 10.0]
    half_30028b = 36.0 / (2 * math.sqrt(2))  # 12.727922061357855
    occ, sockets, needs = P.resolve_occupancy_and_sockets("30028b", "Tyre  8/ 40 x  8 Slick Smooth")
    assert needs is False
    assert sockets == []
    assert occ == [(-half_30028b, half_30028b, -half_30028b, half_30028b, -10.0, 10.0)]

    # 2346: "Tyre 12/ 50 x 16 Offset Tread" -- diameter 70 LDU, asymmetric z: [-20.0, 10.0]
    half_2346 = 70.0 / (2 * math.sqrt(2))  # 24.74873734152916
    occ, sockets, needs = P.resolve_occupancy_and_sockets("2346", "Tyre 12/ 50 x 16 Offset Tread")
    assert needs is False
    assert sockets == []
    assert occ == [(-half_2346, half_2346, -half_2346, half_2346, -20.0, 10.0)]


@pytest.mark.skipif(not LDRAW_CACHE.exists(), reason="LDraw library not fetched (scripts/ldraw/fetch_library.py)")
@pytest.mark.parametrize("pid,expected_d,expected_z0,expected_z1", [
    ("6015", 50.0, -14.0, 14.0),
    ("30028b", 36.0, -10.0, 10.0),
    ("30391", 76.0, -17.0, 17.0),
    ("3139b", 36.0, -5.5, 5.5),
    ("11209", 52.5, -12.5, 12.5),
    ("32003", 170.01, -30.0, 30.0),
    ("3641", 36.0, -8.0, 8.0),
    ("2346", 70.0, -20.0, 10.0),
    ("44309", 108.0, -27.0, 27.0),
    ("56890", 60.0, -14.0, 14.0),
])
def test_real_resolved_tyre_sample_matches_geometry_and_remains_within_bounds(pid, expected_d, expected_z0, expected_z1):
    """Representative sample of 10 real tyre parts verified against real resolved geometry."""
    from resolve import Library, ColourTable, resolve_part
    lib = Library(str(LDRAW_CACHE))
    colours = ColourTable(lib)
    part = resolve_part(lib, colours, pid + ".dat")

    # Real geometry facts verified: tyres have NO studs, holes, or pins
    assert len(part.studs) == 0, "%s should have no studs" % pid
    assert len(part.holes) == 0, "%s should have no holes" % pid
    assert len(part.pins) == 0, "%s should have no pins" % pid

    # Rotational symmetry in XY: dx == dy, centered at (0, 0)
    dx = part.max[0] - part.min[0]
    dy = part.max[1] - part.min[1]
    assert abs(dx - dy) < 0.25, "%s should be rotationally symmetric in XY (dx=%f, dy=%f)" % (pid, dx, dy)
    assert abs((part.min[0] + part.max[0]) / 2.0) < 0.5, "%s should be centered at X=0" % pid
    assert abs((part.min[1] + part.max[1]) / 2.0) < 0.5, "%s should be centered at Y=0" % pid

    # Resolved diameter and Z bounds match expected constants
    assert round((dx + dy) / 2.0, 2) == expected_d
    assert round(part.min[2], 2) == expected_z0
    assert round(part.max[2], 2) == expected_z1

    # Dispatcher resolves with real bounds
    occ, sockets, needs = P.resolve_occupancy_and_sockets(
        pid, part.title, part.min, part.max, part.holes, part.studs, part.tris
    )
    assert needs is False
    assert sockets == []
    assert len(occ) == 1

    # Inscribed square box is provably within the part's real bounds
    b = occ[0]
    assert b[0] >= part.min[0] - 0.5 and b[1] <= part.max[0] + 0.5
    assert b[2] >= part.min[1] - 0.5 and b[3] <= part.max[1] + 0.5
    assert b[4] >= part.min[2] - 0.5 and b[5] <= part.max[2] + 0.5


@pytest.mark.skipif(not LDRAW_CACHE.exists(), reason="LDraw library not fetched (scripts/ldraw/fetch_library.py)")
@pytest.mark.parametrize("pid", ["2807", "6578c01"])
def test_excluded_deformed_tyres_remain_rejected(pid):
    """2807 ('Needs Work') and 6578c01 ('Deformed') must remain rejected (needs_occupancy=True)."""
    from resolve import Library, ColourTable, resolve_part
    lib = Library(str(LDRAW_CACHE))
    colours = ColourTable(lib)
    part = resolve_part(lib, colours, pid + ".dat")
    occ, sockets, needs = P.resolve_occupancy_and_sockets(
        pid, part.title, part.min, part.max, part.holes, part.studs, part.tris
    )
    assert needs is True, "%s should remain rejected (needs_occupancy=True)" % pid
    assert occ is None


# ── Wheel Rims Family (WHEEL_PARTS) ──────────────────────────────────────────

def test_wheel_occupancy_pure_math():
    """Wheel occupancy is an annular 4-box inscribed square in the circular cross-section (XY plane),
    spanning Z width, with the central axle/pin bore (B=8.0) strictly excluded."""
    # Symmetric 68 LDU diameter, z in [-12, 8], default bore_half=8.0
    half68 = 68.0 / (2 * math.sqrt(2))  # ~24.0416
    occ = P.wheel_occupancy(68.0, -12.0, 8.0)
    assert len(occ) == 4
    # Top, Bottom, Left, Right
    b_top, b_bot, b_left, b_right = occ
    assert b_top == (-half68, half68, 8.0, half68, -12.0, 8.0)
    assert b_bot == (-half68, half68, -half68, -8.0, -12.0, 8.0)
    assert b_left == (-half68, -8.0, -8.0, 8.0, -12.0, 8.0)
    assert b_right == (8.0, half68, -8.0, 8.0, -12.0, 8.0)

    # Prove bore exclusion: no box covers any point in (-8, 8) x (-8, 8)
    for b in occ:
        # A box overlaps the bore square if:
        # b[0] < 8 and b[1] > -8 and b[2] < 8 and b[3] > -8
        overlap_bore = (b[0] < 8.0 and b[1] > -8.0 and b[2] < 8.0 and b[3] > -8.0)
        assert not overlap_bore, f"Box {b} overlaps central bore!"

    # Prove outer cylinder containment: all corners have r <= diameter / 2
    r_out = 68.0 / 2.0
    for b in occ:
        for x in (b[0], b[1]):
            for y in (b[2], b[3]):
                assert math.sqrt(x**2 + y**2) <= r_out + 1e-6

    # From bounds: diameter = 76, z_min = -24, z_max = 8
    half76 = 76.0 / (2 * math.sqrt(2))
    occ_bounds = P.wheel_occupancy((-38.0, -38.0, -24.0), (38.0, 38.0, 8.0))
    assert len(occ_bounds) == 4
    assert occ_bounds[0] == (-half76, half76, 8.0, half76, -24.0, 8.0)

    # Small wheel edge case where half_inscribed <= bore_half returns empty list []
    assert P.wheel_occupancy(20.0, -10.0, 10.0, bore_half=8.0) == []


def test_dispatcher_resolves_wheel_parts_with_exact_values():
    """WHEEL_PARTS resolves to 4 annular boxes in XY, spanning Z, with empty sockets and needs_occupancy=False."""
    # Sample from prompt:
    # 2470: "Wheel  2.8 x 27 with  8 Spokes" -- diameter 68.0 LDU, z: [-12.0, 8.0]
    half_2470 = 68.0 / (2 * math.sqrt(2))
    occ, sockets, needs = P.resolve_occupancy_and_sockets("2470", "Wheel  2.8 x 27 with  8 Spokes")
    assert needs is False
    assert sockets == []
    assert len(occ) == 4
    assert occ[0] == (-half_2470, half_2470, 8.0, half_2470, -12.0, 8.0)

    # 2695: "Wheel Rim 12.7 x 30 Stepped" -- diameter 76.0 LDU, z: [-24.0, 8.0]
    half_2695 = 76.0 / (2 * math.sqrt(2))
    occ, sockets, needs = P.resolve_occupancy_and_sockets("2695", "Wheel Rim 12.7 x 30 Stepped")
    assert needs is False
    assert sockets == []
    assert len(occ) == 4
    assert occ[0] == (-half_2695, half_2695, 8.0, half_2695, -24.0, 8.0)

    # 30155: "Wheel Rim  8 x 18 with 12 Spokes and Peghole" -- diameter 44.0 LDU, z: [-8.0, 8.0]
    half_30155 = 44.0 / (2 * math.sqrt(2))
    occ, sockets, needs = P.resolve_occupancy_and_sockets("30155", "Wheel Rim  8 x 18 with 12 Spokes and Peghole")
    assert needs is False
    assert sockets == []
    assert len(occ) == 4
    assert occ[0] == (-half_30155, half_30155, 8.0, half_30155, -8.0, 8.0)

    # 3482: "Wheel Rim  8 x 17.5 with Axlehole" -- diameter 44.0 LDU, z: [-10.0, 10.0]
    half_3482 = 44.0 / (2 * math.sqrt(2))
    occ, sockets, needs = P.resolve_occupancy_and_sockets("3482", "Wheel Rim  8 x 17.5 with Axlehole")
    assert needs is False
    assert sockets == []
    assert len(occ) == 4
    assert occ[0] == (-half_3482, half_3482, 8.0, half_3482, -10.0, 10.0)


@pytest.mark.skipif(not LDRAW_CACHE.exists(), reason="LDraw library not fetched (scripts/ldraw/fetch_library.py)")
@pytest.mark.parametrize("pid,expected_d,expected_z0,expected_z1", [
    ("2470", 68.0, -12.0, 8.0),
    ("2695", 76.0, -24.0, 8.0),
    ("30155", 44.0, -8.0, 8.0),
    ("32077", 150.0, -35.5, 35.59),
    ("33211", 108.0, -24.0, 0.0),
    ("42716", 76.0, -25.0, 25.0),
    ("3482", 44.0, -10.0, 10.0),
    ("4266", 76.0, -25.0, 25.0),
    ("4489a", 84.0, -12.0, 8.0),
    ("41896", 108.0, -33.0, 33.0),
    ("7877", 140.0, -16.25, 16.25),
    ("6580a", 75.8, -29.0, 29.0),
])
def test_real_resolved_wheel_sample_matches_geometry_and_remains_within_bounds(pid, expected_d, expected_z0, expected_z1):
    """Representative sample of 12 real wheel rim parts verified against real resolved geometry."""
    from resolve import Library, ColourTable, resolve_part
    lib = Library(str(LDRAW_CACHE))
    colours = ColourTable(lib)
    part = resolve_part(lib, colours, pid + ".dat")

    # Rotational symmetry in XY: dx == dy, centered at (0, 0)
    dx = part.max[0] - part.min[0]
    dy = part.max[1] - part.min[1]
    assert abs(dx - dy) < 0.25, "%s should be rotationally symmetric in XY (dx=%f, dy=%f)" % (pid, dx, dy)
    assert abs((part.min[0] + part.max[0]) / 2.0) < 0.5, "%s should be centered at X=0" % pid
    assert abs((part.min[1] + part.max[1]) / 2.0) < 0.5, "%s should be centered at Y=0" % pid

    # Resolved diameter and Z bounds match expected constants
    assert round((dx + dy) / 2.0, 2) == expected_d
    assert round(part.min[2], 2) == expected_z0
    assert round(part.max[2], 2) == expected_z1

    # Dispatcher resolves with real bounds
    occ, sockets, needs = P.resolve_occupancy_and_sockets(
        pid, part.title, part.min, part.max, part.holes, part.studs, part.tris, part.cylinders
    )
    assert needs is False
    assert sockets == []
    assert len(occ) == 4

    r_out = expected_d / 2.0
    for b in occ:
        # Bounds containment
        assert b[0] >= part.min[0] - 0.5 and b[1] <= part.max[0] + 0.5
        assert b[2] >= part.min[1] - 0.5 and b[3] <= part.max[1] + 0.5
        assert b[4] >= part.min[2] - 0.5 and b[5] <= part.max[2] + 0.5

        # Outer cylinder containment: every corner has r <= r_out
        for x in (b[0], b[1]):
            for y in (b[2], b[3]):
                assert math.sqrt(x**2 + y**2) <= r_out + 1e-5, f"{pid}: corner ({x},{y}) exceeds r_out={r_out}"

        # Axle bore clearance: simulated Technic axle ([-6, 6] x [-6, 6]) along Z has zero overlap
        overlap_axle = (b[0] < 6.0 and b[1] > -6.0 and b[2] < 6.0 and b[3] > -6.0)
        assert not overlap_axle, f"{pid}: box {b} overlaps inserted axle!"


@pytest.mark.skipif(not LDRAW_CACHE.exists(), reason="LDraw library not fetched (scripts/ldraw/fetch_library.py)")
@pytest.mark.parametrize("pid", [
    "30027a",  # Small wheel rim (D=20.0, W=7.07 <= 8.0)
    "34337",   # Small wheel rim (D=20.0, W=7.07 <= 8.0)
    "6014a",   # Small wheel rim (D=26.0, W=9.19)
    "54086",   # Decorative wheel cover (5 Spoke for Wheel 20 x 30)
    "62359",   # Decorative wheel cover (7 Spoke for Wheel 14 x 18)
    "30190",   # Wheel Rim with Stub Axles (integral axle)
    "3464b",   # Wheel Centre with Stub Axles (integral axle)
    "55981",   # Wheel Rim 14 x 18 marked 'Needs Work'
])
def test_deliberately_excluded_wheel_subgroups_remain_rejected(pid):
    """Deliberately excluded wheel sub-groups must remain rejected (needs_occupancy=True)."""
    from resolve import Library, ColourTable, resolve_part
    lib = Library(str(LDRAW_CACHE))
    colours = ColourTable(lib)
    part = resolve_part(lib, colours, pid + ".dat")
    occ, sockets, needs = P.resolve_occupancy_and_sockets(
        pid, part.title, part.min, part.max, part.holes, part.studs, part.tris, part.cylinders
    )
    assert needs is True, "%s should remain rejected (needs_occupancy=True)" % pid
    assert occ is None



# bar_grip_points (2026-09-27): real grip position/axis for held/clip-mounted parts, refactored from the
# earlier has_bar_grip boolean so the real data (not just a yes/no) reaches the baked mesh's `bars` connector
# field. Exact expected values checked against a live resolve, same rigor as the tables above.
_REAL_GRIPS = {
    "2714a": [((0.0, 18.0, 0.0), (0.0, 1.0, 0.0))],     # "Bar 8L with Stop Rings and Pin"
    "11090": [((0.0, 0.0, -4.0), (0.0, 0.0, -1.0))],    # "Bar Tube with Clip"
    "11103": [((0.0, 10.0, 0.0), (0.0, 1.0, 0.0))],     # "Minifig Sword Double Blade with Bar Holder"
}


@pytest.mark.skipif(not LDRAW_CACHE.exists(), reason="LDraw library not fetched (scripts/ldraw/fetch_library.py)")
@pytest.mark.parametrize("pid", ["2714a", "11090", "11103"])
def test_bar_grip_points_on_real_held_parts(pid):
    from resolve import Library, ColourTable, resolve_part
    lib = Library(str(LDRAW_CACHE))
    colours = ColourTable(lib)
    part = resolve_part(lib, colours, pid + ".dat")
    grips = P.bar_grip_points(part.min, part.max, part.cylinders, part.tris)
    got = [(tuple(round(v, 1) for v in p), tuple(round(v, 2) for v in d)) for p, d in grips]
    assert got == _REAL_GRIPS[pid]


@pytest.mark.skipif(not LDRAW_CACHE.exists(), reason="LDraw library not fetched (scripts/ldraw/fetch_library.py)")
@pytest.mark.parametrize("pid", ["3001", "5258", "100942"])
def test_bar_grip_points_empty_on_real_non_grip_parts(pid):
    """3001 (plain Brick 2x4, has other cylinders -- studs' anti-stud tubes -- but none at the bar radius),
    5258 (a Door, has real radius-4 hinge-pin-shaped cylinders but none pass the extremity+isolation checks),
    100942 (a Wheel, radius-4 cylinders embedded in the hub, not a free grip) -- same real ids the raw-radius
    prototype over-triggered on before the extremity/isolation filter was added, see the module docstring."""
    from resolve import Library, ColourTable, resolve_part
    lib = Library(str(LDRAW_CACHE))
    colours = ColourTable(lib)
    part = resolve_part(lib, colours, pid + ".dat")
    assert P.bar_grip_points(part.min, part.max, part.cylinders, part.tris) == []


# Technic axle-hole detection (2026-09-27): axl2hole.dat/axl3hole.dat/axl4hole.dat (the receiving axle hole in
# real "... with Axle Holes" Liftarm/Beam parts) are now recognised by resolve.py's AXLE_HOLE_RE alongside
# peghole.dat, populating the same part.holes list -- verified real outer bore radius (6 LDU, measured from
# axl2hol2.dat's own boundary vertices and axl4hole.dat's 1-4cyli.dat scale) matches peghole.dat's radius
# exactly, so no new occupancy math was needed: the existing generic_hole_channel_occupancy already handles
# these once resolve.py hands it the hole positions.
@pytest.mark.skipif(not LDRAW_CACHE.exists(), reason="LDraw library not fetched (scripts/ldraw/fetch_library.py)")
@pytest.mark.parametrize("pid,expect_holes", [("11478", 6), ("33299a", 2), ("33299b", 1)])
def test_axle_holes_populate_part_holes(pid, expect_holes):
    from resolve import Library, ColourTable, resolve_part
    lib = Library(str(LDRAW_CACHE))
    colours = ColourTable(lib)
    part = resolve_part(lib, colours, pid + ".dat")
    assert len(part.holes) == expect_holes


@pytest.mark.skipif(not LDRAW_CACHE.exists(), reason="LDraw library not fetched (scripts/ldraw/fetch_library.py)")
@pytest.mark.parametrize("pid", ["11478", "33299a", "33299b", "2825"])
def test_real_axle_hole_liftarms_get_accepted(pid):
    """Real 'Liftarm with Axle Hole(s)' parts, previously rejected (no round-hole-only detection reached
    them), now accepted via the existing generic_hole_channel_occupancy -- no axle-specific occupancy
    function needed, since the axle hole's outer bore is geometrically identical to a peg hole's."""
    from resolve import Library, ColourTable, resolve_part
    lib = Library(str(LDRAW_CACHE))
    colours = ColourTable(lib)
    part = resolve_part(lib, colours, pid + ".dat")
    occ, sockets, needs = P.resolve_occupancy_and_sockets(pid, part.title or pid, part.min, part.max,
                                                            part.holes, part.studs, part.tris, part.cylinders)
    assert needs is False, "%s should be accepted now that axle holes are detected" % pid
    assert occ


@pytest.mark.skipif(not LDRAW_CACHE.exists(), reason="LDraw library not fetched (scripts/ldraw/fetch_library.py)")
def test_real_alternating_hole_beam_stays_safely_rejected():
    """2391 'Technic Beam 7 with Alternating Holes' has 14 holes in a pattern the single-shared-axis channel
    model can't safely express -- must stay needs_occupancy=True (a safe non-acceptance), not get a wrong or
    guessed box. Confirms the axle-hole change didn't loosen the channel model's own safety checks."""
    from resolve import Library, ColourTable, resolve_part
    lib = Library(str(LDRAW_CACHE))
    colours = ColourTable(lib)
    part = resolve_part(lib, colours, "2391.dat")
    occ, sockets, needs = P.resolve_occupancy_and_sockets("2391", part.title or "2391", part.min, part.max,
                                                            part.holes, part.studs, part.tris, part.cylinders)
    assert needs is True
    assert occ is None


# Minifig headwear socket (2026-09-27): a hair/helmet/hat/headdress/cap/mask/crown part receives the head's own
# real top stud at its own LOCAL ORIGIN -- cross-validated against characters.py's own already-proven headgear
# ids (3896, 3901), not just the reject-pool samples.
def test_minifig_headwear_socket_matches_real_prefixes():
    assert P.minifig_headwear_socket("Minifig Hair Tousled") == [((0.0, 0.0, 0.0), (0.0, -1.0, 0.0))]
    assert P.minifig_headwear_socket("Minifig Helmet Castle with Chin-Guard") == [((0.0, 0.0, 0.0), (0.0, -1.0, 0.0))]
    assert P.minifig_headwear_socket("Minifig Hat Cowboy") == [((0.0, 0.0, 0.0), (0.0, -1.0, 0.0))]
    assert P.minifig_headwear_socket("Brick 2 x 4") is None
    assert P.minifig_headwear_socket("Minifig Neckwear Cape") is None  # a real, deliberately DIFFERENT family


@pytest.mark.skipif(not LDRAW_CACHE.exists(), reason="LDraw library not fetched (scripts/ldraw/fetch_library.py)")
@pytest.mark.parametrize("pid", ["10048", "10051", "3896", "3901"])
def test_minifig_headwear_accepted_on_real_parts(pid):
    """3896 and 3901 are the exact ids characters.py's own Wizard/Male-hair templates already use
    successfully -- cross-validating the socket convention against already-proven data, not just the
    reject-pool samples (10048, 10051)."""
    from resolve import Library, ColourTable, resolve_part
    lib = Library(str(LDRAW_CACHE))
    colours = ColourTable(lib)
    part = resolve_part(lib, colours, pid + ".dat")
    occ, sockets, needs = P.resolve_occupancy_and_sockets(pid, part.title or pid, part.min, part.max,
                                                            part.holes, part.studs, part.tris, part.cylinders)
    assert needs is False
    assert occ == []
    assert sockets == [((0.0, 0.0, 0.0), (0.0, -1.0, 0.0))]


@pytest.mark.skipif(not LDRAW_CACHE.exists(), reason="LDraw library not fetched (scripts/ldraw/fetch_library.py)")
def test_minifig_headwear_does_not_shadow_bar_grip():
    """11103 (a sword, real bar-grip part) must not be affected by the headwear check -- different title,
    different family, no interference between the two."""
    from resolve import Library, ColourTable, resolve_part
    lib = Library(str(LDRAW_CACHE))
    colours = ColourTable(lib)
    part = resolve_part(lib, colours, "11103.dat")
    occ, sockets, needs = P.resolve_occupancy_and_sockets("11103", part.title or "11103", part.min, part.max,
                                                            part.holes, part.studs, part.tris, part.cylinders)
    assert needs is False
    assert occ == []
    assert sockets == []  # bar-grip path: deliberately no socket yet, not the headwear socket


# SNOT studs (2026-09-27): a stud facing sideways (X or Z, not Y) was previously excluded from
# generic_stud_cell_occupancy entirely -- found live: "Minifig Armour Shoulder Pads with 1 Stud on Front, 2
# Studs on Back" (11097) has 3 real studs, ALL sideways, individually 15-19% solid (healthy, comparable to
# other accepted parts), but the up-only flush check discarded the whole part over having zero up-facing
# studs at all. Generalises the same ray-cast proof to any axis-aligned direction.
def test_snot_stud_synthetic_sideways_box():
    """The sideways box spans the part's full real bounds only along the stud's OWN axis (Z, -10..10 here);
    the other two axes (X, Y) get the same +/-10 footprint the up-facing case already uses for X/Z -- so a
    stud sitting at y=12 (not y=0) gets a Y span of 2..22, not the full 0..24 height."""
    tris = _box_tris(-10, 10, 0, 24, -10, 10)
    studs = [((0.0, 12.0, 10.0), (0.0, 0.0, 1.0))]  # a single sideways (Z+) stud, no up-facing stud at all
    occ, sockets = P.generic_stud_cell_occupancy((-10, 0, -10), (10, 24, 10), studs, tris)
    assert occ == [(-10.0, 10.0, 2.0, 22.0, -10, 10)]
    assert sockets == [((0.0, 12.0, 10.0), (0.0, 0.0, 1.0))]


@pytest.mark.skipif(not LDRAW_CACHE.exists(), reason="LDraw library not fetched (scripts/ldraw/fetch_library.py)")
@pytest.mark.parametrize("pid,expect_n", [("11097", 2), ("15086", 3)])
def test_snot_studs_on_real_minifig_armour(pid, expect_n):
    """11097: 2 of its 3 sideways studs pass (the third is individually below STUD_CELL_MIN_SOLID) -- partial
    credit, same under-approximation principle as the boat-hull fix. 15086: all 3 pass."""
    from resolve import Library, ColourTable, resolve_part
    lib = Library(str(LDRAW_CACHE))
    colours = ColourTable(lib)
    part = resolve_part(lib, colours, pid + ".dat")
    occ, sockets = P.generic_stud_cell_occupancy(part.min, part.max, part.studs, part.tris)
    assert occ is not None and len(occ) == expect_n
    assert len(sockets) == expect_n
    for _, d in sockets:
        assert d[1] == 0  # every real stud on these parts is sideways -- no Y-axis socket should appear
