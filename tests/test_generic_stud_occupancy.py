"""scripts/ldraw/parts.py's generic_stud_cell_occupancy (2026-09-26): the library-wide occupancy fallback that lets
the catalogue expand past the hand-curated ROUND_PARTS/CORNER_L_PARTS/SLOPE_BACK_WALL_PARTS tables without hand-
verifying each new part id. It generalises those tables' own justification (a stud flush at y=0 facing up always
has solid material beneath it) into an automated ray-parity PROOF against the part's own real triangles, so a
candidate is only ever accepted once it is actually geometrically demonstrated, never assumed from title/shape
alone. These tests use synthetic geometry (no LDraw library needed, so they run in CI) plus, where the fetched
library is present, real curated parts to prove parity with the hand-verified tables it is meant to subsume."""
import math
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "ldraw"))
import parts as P  # noqa: E402

LDRAW_CACHE = Path(os.environ.get("LDRAW_DIR") or (Path(__file__).resolve().parent.parent / "scripts" / "ldraw" / "_ldraw_cache" / "ldraw"))


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


# -----------------------------------------------------------------------------
# Tile family generic occupancy (2026-09-27)
# -----------------------------------------------------------------------------

def _cylinder_tris(r, y0, y1, segments=16):
    """A closed polygonal cylinder for synthetic round tile tests."""
    tris = []
    pts_bot = []
    pts_top = []
    for i in range(segments):
        th = 2 * math.pi * i / segments
        x = r * math.cos(th)
        z = r * math.sin(th)
        pts_bot.append((x, y0, z))
        pts_top.append((x, y1, z))
    for i in range(segments):
        nxt = (i + 1) % segments
        tris.append(((0, y0, 0), pts_bot[i], pts_bot[nxt]))
        tris.append(((0, y1, 0), pts_top[nxt], pts_top[i]))
        tris.append((pts_bot[i], pts_top[i], pts_top[nxt]))
        tris.append((pts_bot[i], pts_top[nxt], pts_bot[nxt]))
    return tris


def test_generic_tile_occupancy_synthetic_rect():
    """Synthetic 2x2 rectangular tile with 0 studs and plate height [0, 8]."""
    tris = _box_tris(-20, 20, 0, 8, -20, 20)
    occ, sockets = P.generic_tile_occupancy((-20, 0, -20), (20, 8, 20), [], tris, "Tile 2 x 2 with Pattern")
    assert occ == [(-20, 20, 0.0, 8.0, -20, 20)]
    assert len(sockets) == 4
    # All sockets face down at y=8
    for pos, d in sockets:
        assert pos[1] == 8
        assert d == (0, 1, 0)


def test_generic_tile_occupancy_synthetic_corner_l():
    """Synthetic 2x2 L-shaped corner tile (3 cells solid, 1 missing)."""
    tris = (_box_tris(-10, 10, 0, 8, -10, 10) +
            _box_tris(10, 30, 0, 8, -10, 10) +
            _box_tris(-10, 10, 0, 8, 10, 30))
    occ, sockets = P.generic_tile_occupancy((-10, 0, -10), (30, 8, 30), [], tris, "Tile 2 x 2 Corner with Pattern")
    assert occ is not None and len(occ) == 3
    assert len(sockets) == 3
    expected_centers = {(0.0, 0.0), (20.0, 0.0), (0.0, 20.0)}
    actual_centers = {(pos[0], pos[2]) for pos, _ in sockets}
    assert actual_centers == expected_centers


def test_generic_tile_occupancy_synthetic_round():
    """Synthetic 2x2 round tile: inscribed square box [-14.14, 14.14], no sockets."""
    tris = _cylinder_tris(20, 0, 8)
    occ, sockets = P.generic_tile_occupancy((-20, 0, -20), (20, 8, 20), [], tris, "Tile 2 x 2 Round with Pattern")
    assert occ is not None and len(occ) == 1
    half = 40.0 / (2 * math.sqrt(2))
    assert math.isclose(occ[0][0], -half, rel_tol=1e-5)
    assert math.isclose(occ[0][1], half, rel_tol=1e-5)
    assert occ[0][2] == 0.0 and occ[0][3] == 8.0
    assert sockets == []


def test_generic_tile_occupancy_synthetic_1x1_round():
    """Synthetic 1x1 round tile receives a single center socket at (0, 8, 0)."""
    tris = _cylinder_tris(10, 0, 8)
    occ, sockets = P.generic_tile_occupancy((-10, 0, -10), (10, 8, 10), [], tris, "Tile 1 x 1 Round with Pattern")
    assert occ is not None and len(occ) == 1
    assert sockets == [((0.0, 8.0, 0.0), (0.0, 1.0, 0.0))]


def test_generic_tile_occupancy_synthetic_exclusions():
    """Exclusions required by spec §3 (under-approximate, never guess)."""
    tris = _box_tris(-20, 20, 0, 8, -20, 20)
    # Top studs must not enter tile path
    top_studs = [((0.0, 0.0, 0.0), (0.0, -1.0, 0.0))]
    assert P.generic_tile_occupancy((-20, 0, -20), (20, 8, 20), top_studs, tris, "Tile 2 x 2") == (None, [])

    # Functional clip feature
    assert P.generic_tile_occupancy((-10, -10, -10), (10, 8, 10), [], tris, "Tile 1 x 1 with Clip") == (None, [])

    # Through-hole feature
    assert P.generic_tile_occupancy((-20, 0, -20), (20, 8, 20), [], tris, "Tile 2 x 2 Round with Hole") == (None, [])

    # Non-plate height bounds
    assert P.generic_tile_occupancy((-20, 0, -20), (20, 24, 20), [], tris, "Tile 2 x 2") == (None, [])


@pytest.mark.skipif(not LDRAW_CACHE.exists(), reason="LDraw library not fetched (scripts/ldraw/fetch_library.py)")
@pytest.mark.parametrize("pid,expect_n_occ,expect_n_sock", [
    ("10202", 1, 36),     # Tile 6 x 6 with Groove and Underside Studs
    ("10202p04", 1, 36),  # Tile 6 x 6 with "Soap Suds Cleans it all" Pattern
    ("10202p05", 1, 36),  # Tile 6 x 6 with Minifig and Washing Machine Pattern
    ("14719", 3, 3),      # Tile 2 x 2 Corner
    ("14719p00", 3, 3),   # Tile 2 x 2 Corner with Orange and Yellow Diamonds Pattern
    ("14769", 1, 0),      # Tile 2 x 2 Round with Round Underside Stud
    ("14769p0a", 1, 0),   # Tile 2 x 2 Round with Round Underside Stud with Pattern
    ("3068bp06", 1, 4),   # Tile 2 x 2 with Red Warning Triangle Pattern
    ("3068bp09", 1, 4),   # Tile 2 x 2 with Transport Text on Crate Pattern
    ("3069bp01", 1, 2),   # Tile 1 x 2 with Letter Pattern
    ("3069bp02", 1, 2),   # Tile 1 x 2 with Tape Reels Pattern
    ("3070bp01", 1, 1),   # Tile 1 x 1 with Black "1" Pattern
    ("2431p01", 1, 4),    # Tile 1 x 4 with Wood Grain and 4 Nails Pattern
    ("6636p01", 1, 6),    # Tile 1 x 6 with "Rockefeller" Pattern
    ("4150", 1, 0),       # Tile 2 x 2 Round with Cross Underside Stud
    ("4150p01", 1, 0),    # Tile 2 x 2 Round with Grille Pattern
    ("98138p01", 1, 1),   # Tile 1 x 1 Round with Venomari Pattern
])
def test_real_tile_parts_accepted(pid, expect_n_occ, expect_n_sock):
    """Real tile parts (including printed variants and base tiles) verified via resolve_part."""
    from resolve import Library, ColourTable, resolve_part
    lib = Library(str(LDRAW_CACHE))
    colours = ColourTable(lib)
    part = resolve_part(lib, colours, pid + ".dat")
    occ, sockets, needs = P.resolve_occupancy_and_sockets(
        pid, part.title or pid, part.min, part.max, part.holes, part.studs, part.tris, part.cylinders
    )
    assert needs is False, f"{pid} should be accepted"
    assert occ is not None and len(occ) == expect_n_occ
    assert len(sockets) == expect_n_sock


@pytest.mark.skipif(not LDRAW_CACHE.exists(), reason="LDraw library not fetched (scripts/ldraw/fetch_library.py)")
@pytest.mark.parametrize("pid", [
    "15535",  # Tile 2 x 2 Round with Hole (through-hole)
    "12825",  # Tile 1 x 1 with Clip with Rounded Tips (functional clip)
    "22385",  # Tile 3 x 2 with Angled End (angled/cut corner)
    "27925",  # Tile 2 x 2 Corner Round (curved corner)
])
def test_real_tile_feature_exclusions_stay_rejected(pid):
    """Feature-bearing tiles that cannot be safely under-approximated as plain rectangular/round tiles."""
    from resolve import Library, ColourTable, resolve_part
    lib = Library(str(LDRAW_CACHE))
    colours = ColourTable(lib)
    part = resolve_part(lib, colours, pid + ".dat")
    occ, sockets, needs = P.resolve_occupancy_and_sockets(
        pid, part.title or pid, part.min, part.max, part.holes, part.studs, part.tris, part.cylinders
    )
    assert needs is True, f"{pid} should remain needs_occupancy=True"
    assert occ is None


# ── Flat Wall Panels Family (PANEL_FLAT_WALL_PARTS) ──────────────────────────────

def test_panel_flat_wall_occupancy_pure_math():
    """Flat wall panel occupancy is a rectangular box spanning the part's footprint and 24 LDU height."""
    # 1 x 2 x 1 panel: x in [-20, 20], y in [0, 24], z in [-10, 10]
    occ, sockets = P.panel_flat_wall_occupancy_and_sockets(-20.0, 20.0, 0.0, 24.0, -10.0, 10.0)
    assert occ == [(-20.0, 20.0, 0.0, 24.0, -10.0, 10.0)]
    assert sockets == [((-10.0, 24.0, 0.0), (0, 1, 0)), ((10.0, 24.0, 0.0), (0, 1, 0))]

    # Calling with bounds tuples
    occ_b, sockets_b = P.panel_flat_wall_occupancy_and_sockets((-30.0, 0.0, -10.0), (30.0, 24.0, 10.0))
    assert occ_b == [(-30.0, 30.0, 0.0, 24.0, -10.0, 10.0)]
    assert sockets_b == [((-20.0, 24.0, 0.0), (0, 1, 0)), ((0.0, 24.0, 0.0), (0, 1, 0)), ((20.0, 24.0, 0.0), (0, 1, 0))]


@pytest.mark.parametrize("pid,expected_box,expected_sockets", [
    ("4865a", (-20.0, 20.0, 0.0, 24.0, -10.0, 10.0), [((-10.0, 24.0, 0.0), (0, 1, 0)), ((10.0, 24.0, 0.0), (0, 1, 0))]),
    ("23950", (-30.0, 30.0, 0.0, 24.0, -10.0, 10.0), [((-20.0, 24.0, 0.0), (0, 1, 0)), ((0.0, 24.0, 0.0), (0, 1, 0)), ((20.0, 24.0, 0.0), (0, 1, 0))]),
    ("15207", (-40.0, 40.0, 0.0, 24.0, -10.0, 10.0), [((-30.0, 24.0, 0.0), (0, 1, 0)), ((-10.0, 24.0, 0.0), (0, 1, 0)), ((10.0, 24.0, 0.0), (0, 1, 0)), ((30.0, 24.0, 0.0), (0, 1, 0))]),
    ("23969", (-20.0, 20.0, 0.0, 24.0, -10.0, 10.0), [((-10.0, 24.0, 0.0), (0, 1, 0)), ((10.0, 24.0, 0.0), (0, 1, 0))]),
    ("30413", (-40.0, 40.0, 0.0, 24.0, -10.0, 10.0), [((-30.0, 24.0, 0.0), (0, 1, 0)), ((-10.0, 24.0, 0.0), (0, 1, 0)), ((10.0, 24.0, 0.0), (0, 1, 0)), ((30.0, 24.0, 0.0), (0, 1, 0))]),
    ("6231",  (-10.0, 10.0, 0.0, 24.0, -10.0, 10.0), [((0.0, 24.0, 0.0), (0, 1, 0))]),
])
def test_dispatcher_resolves_panel_flat_wall_parts_without_bounds(pid, expected_box, expected_sockets):
    """PANEL_FLAT_WALL_PARTS resolves to full 1-brick box with downward sockets at y=24 and needs_occupancy=False."""
    occ, sockets, needs = P.resolve_occupancy_and_sockets(pid, f"Panel {pid}")
    assert needs is False
    assert occ == [expected_box]
    assert sockets == expected_sockets


@pytest.mark.skipif(not LDRAW_CACHE.exists(), reason="LDraw library not fetched (scripts/ldraw/fetch_library.py)")
@pytest.mark.parametrize("pid,expected_w,expected_sockets_count", [
    ("4865a", 40.0, 2),
    ("4865b", 40.0, 2),
    ("4865",  40.0, 2),
    ("23969", 40.0, 2),
    ("93095", 40.0, 2),
    ("30010", 40.0, 2),
    ("23950", 60.0, 3),
    ("15207", 80.0, 4),
    ("30413", 80.0, 4),
    ("43337", 80.0, 4),
    ("6231",  20.0, 1),
])
def test_real_resolved_flat_wall_panels(pid, expected_w, expected_sockets_count):
    """All 11 flat wall panel parts verified against real resolved geometry, bounds, and ray-cast solidity."""
    from resolve import Library, ColourTable, resolve_part
    lib = Library(str(LDRAW_CACHE))
    colours = ColourTable(lib)
    part = resolve_part(lib, colours, pid + ".dat")

    # Real geometry facts: flat wall panels have zero studs
    assert len(part.studs) == 0, f"{pid} should have 0 studs"

    # Bounds dimensions: width matches expected_w, height is 24 LDU (1 brick), depth is 20 LDU (1 stud)
    dx = part.max[0] - part.min[0]
    dy = part.max[1] - part.min[1]
    dz = part.max[2] - part.min[2]
    assert dx == pytest.approx(expected_w, abs=0.1)
    assert dy == pytest.approx(24.0, abs=0.1)
    assert dz == pytest.approx(20.0, abs=0.5)

    # Ray-cast solidity proof: bounding box must exceed STUD_CELL_MIN_SOLID (0.15)
    bbox = P.box(part.min[0], part.max[0], part.min[1], part.max[1], part.min[2], part.max[2])
    solid_frac = P._stud_box_solid_fraction(part.tris, bbox, n=200)
    assert solid_frac >= P.STUD_CELL_MIN_SOLID, f"{pid} solidity {solid_frac:.3f} below {P.STUD_CELL_MIN_SOLID}"

    # Dispatcher resolution with real geometry
    occ, sockets, needs = P.resolve_occupancy_and_sockets(
        pid, part.title or pid, part.min, part.max, part.holes, part.studs, part.tris, part.cylinders
    )
    assert needs is False
    assert occ is not None and len(occ) == 1
    assert len(sockets) == expected_sockets_count
    # All sockets face downward at y=24
    for pos, direction in sockets:
        assert pos[1] == pytest.approx(24.0, abs=0.1)
        assert direction == (0, 1, 0)


@pytest.mark.skipif(not LDRAW_CACHE.exists(), reason="LDraw library not fetched (scripts/ldraw/fetch_library.py)")
@pytest.mark.parametrize("pid", ["4865ap01", "23969p01"])
def test_panel_flat_wall_patterned_parts(pid):
    """Patterned versions of flat wall panels resolve to valid occupancy via clean_id mapping."""
    from resolve import Library, ColourTable, resolve_part
    lib = Library(str(LDRAW_CACHE))
    colours = ColourTable(lib)
    part = resolve_part(lib, colours, pid + ".dat")

    occ, sockets, needs = P.resolve_occupancy_and_sockets(
        pid, part.title or pid, part.min, part.max, part.holes, part.studs, part.tris, part.cylinders
    )
    assert needs is False
    assert len(occ) == 1
    assert len(sockets) == 2


# ── Sub-family 2: Corner/Curved Wall Panels with Studs (Safely Unresolved) ──────

@pytest.mark.skipif(not LDRAW_CACHE.exists(), reason="LDraw library not fetched (scripts/ldraw/fetch_library.py)")
@pytest.mark.parametrize("pid,reason", [
    ("2345", "crenellated castle wall with studs at y=24, not y=0; stud columns are thin shell (solids 0.06-0.23)"),
    ("2409", "10x10x12 rock corner; full 288 LDU height column is hollow cave interior (solidity 0.01-0.03)"),
    ("2448", "airplane panel with studs at two heights (y=0 and y=128), bounds min Y is -8.0"),
    ("2466", "airplane panel with bounds min Y=-8.0; full-height column solidity is only 0.07 (< 0.15)"),
    ("2468", "corner convex panel with bounds min Y=-8.0; column solidity is only 0.07 (< 0.15)"),
    ("2571", "curved top panel; thin shell fuselage gives column solidity of 0.03-0.04 (< 0.15)"),
    ("2572", "curved top panel; thin shell fuselage gives column solidity of 0.01-0.03 (< 0.15)"),
])
def test_corner_curved_wall_panels_with_studs_stay_safely_rejected(pid, reason):
    """Sub-family 2 parts must remain needs_occupancy=True: none can be safely approximated by
    stud_cell_occupancy_and_sockets without over-reporting collisions in empty air (spec section 3)."""
    from resolve import Library, ColourTable, resolve_part
    lib = Library(str(LDRAW_CACHE))
    colours = ColourTable(lib)
    part = resolve_part(lib, colours, pid + ".dat")

    occ, sockets, needs = P.resolve_occupancy_and_sockets(
        pid, part.title or pid, part.min, part.max, part.holes, part.studs, part.tris, part.cylinders
    )
    assert needs is True, f"{pid} should stay needs_occupancy=True ({reason})"
    assert occ is None

# ── Technic Gears Family (TECHNIC_GEAR_PARTS) ───────────────────────────────

def test_gear_occupancy_pure_math():
    """Gear occupancy is an annular 4-box inscribed square in the circular cross-section (XY plane),
    spanning Z width, with the central axle bore (B=6.0) strictly excluded."""
    # 8-tooth gear: diameter 24.86 LDU, z in [-10.0, 10.0], default bore_half=6.0
    half24 = 24.86 / (2 * math.sqrt(2))  # ~8.7895 LDU
    occ = P.gear_occupancy(24.86, -10.0, 10.0)
    assert len(occ) == 4
    # Top, Bottom, Left, Right
    b_top, b_bot, b_left, b_right = occ
    assert b_top == (-half24, half24, 6.0, half24, -10.0, 10.0)
    assert b_bot == (-half24, half24, -half24, -6.0, -10.0, 10.0)
    assert b_left == (-half24, -6.0, -6.0, 6.0, -10.0, 10.0)
    assert b_right == (6.0, half24, -6.0, 6.0, -10.0, 10.0)

    # Prove bore exclusion: no box covers any interior point in (-6, 6) x (-6, 6)
    for b in occ:
        overlap_bore = (b[0] < 6.0 and b[1] > -6.0 and b[2] < 6.0 and b[3] > -6.0)
        assert not overlap_bore, f"Box {b} overlaps central axle bore!"

    # Prove outer cylinder containment: all corners have r <= diameter / 2
    r_out = 24.86 / 2.0
    for b in occ:
        for x in (b[0], b[1]):
            for y in (b[2], b[3]):
                assert math.sqrt(x**2 + y**2) <= r_out + 1e-6

    # From bounds: diameter = 54.0 (20-tooth double bevel), z_min = -10.0, z_max = 10.0
    half54 = 54.0 / (2 * math.sqrt(2))
    occ_bounds = P.gear_occupancy((-27.0, -27.0, -10.0), (27.0, 27.0, 10.0))
    assert len(occ_bounds) == 4
    assert occ_bounds[0] == (-half54, half54, 6.0, half54, -10.0, 10.0)

    # Small gear edge case where half_inscribed <= bore_half returns empty list []
    assert P.gear_occupancy(16.0, -5.0, 5.0, bore_half=6.0) == []


def test_dispatcher_resolves_technic_gear_parts_with_exact_values():
    """TECHNIC_GEAR_PARTS resolves to 4 annular boxes in XY, spanning Z, with empty sockets and needs_occupancy=False."""
    # 10928: Technic Gear 8 Tooth Reinforced -- D=24.86, z: [-10.0, 10.0]
    half_10928 = 24.86 / (2 * math.sqrt(2))
    occ, sockets, needs = P.resolve_occupancy_and_sockets("10928", "Technic Gear  8 Tooth Reinforced")
    assert needs is False
    assert sockets == []
    assert len(occ) == 4
    assert occ[0] == (-half_10928, half_10928, 6.0, half_10928, -10.0, 10.0)

    # 3647: Technic Gear 8 Tooth -- D=24.86, z: [-10.0, 10.0]
    occ, sockets, needs = P.resolve_occupancy_and_sockets("3647", "Technic Gear  8 Tooth")
    assert needs is False
    assert sockets == []
    assert len(occ) == 4
    assert occ[0] == (-half_10928, half_10928, 6.0, half_10928, -10.0, 10.0)

    # 4019: Technic Gear 16 Tooth -- D=43.28, z: [-10.0, 10.0]
    half_4019 = 43.28 / (2 * math.sqrt(2))
    occ, sockets, needs = P.resolve_occupancy_and_sockets("4019", "Technic Gear 16 Tooth")
    assert needs is False
    assert sockets == []
    assert len(occ) == 4
    assert occ[0] == (-half_4019, half_4019, 6.0, half_4019, -10.0, 10.0)

    # 94925: Technic Gear 16 Tooth Reinforced -- D=43.28, z: [-10.0, 10.0]
    occ, sockets, needs = P.resolve_occupancy_and_sockets("94925", "Technic Gear 16 Tooth Reinforced")
    assert needs is False
    assert sockets == []
    assert len(occ) == 4
    assert occ[0] == (-half_4019, half_4019, 6.0, half_4019, -10.0, 10.0)

    # 6589: Technic Gear 12 Tooth Bevel -- D=32.0, z: [-3.0, 7.0]
    half_6589 = 32.0 / (2 * math.sqrt(2))
    occ, sockets, needs = P.resolve_occupancy_and_sockets("6589", "Technic Gear 12 Tooth Bevel")
    assert needs is False
    assert sockets == []
    assert len(occ) == 4
    assert occ[0] == (-half_6589, half_6589, 6.0, half_6589, -3.0, 7.0)

    # 32269: Technic Gear 20 Tooth Double Bevel -- D=54.0, z: [-10.0, 10.0]
    half_32269 = 54.0 / (2 * math.sqrt(2))
    occ, sockets, needs = P.resolve_occupancy_and_sockets("32269", "Technic Gear 20 Tooth Double Bevel")
    assert needs is False
    assert sockets == []
    assert len(occ) == 4
    assert occ[0] == (-half_32269, half_32269, 6.0, half_32269, -10.0, 10.0)

    # 18575: Technic Gear 20 Tooth Double Bevel Reinforced -- D=54.0, z: [-10.0, 10.0]
    occ, sockets, needs = P.resolve_occupancy_and_sockets("18575", "Technic Gear 20 Tooth Double Bevel Reinforced")
    assert needs is False
    assert sockets == []
    assert len(occ) == 4
    assert occ[0] == (-half_32269, half_32269, 6.0, half_32269, -10.0, 10.0)

    # 32072: Technic Gear 4 Knob -- D=60.0, z: [-10.0, 10.0]
    half_32072 = 60.0 / (2 * math.sqrt(2))
    occ, sockets, needs = P.resolve_occupancy_and_sockets("32072", "Technic Gear  4 Knob")
    assert needs is False
    assert sockets == []
    assert len(occ) == 4
    assert occ[0] == (-half_32072, half_32072, 6.0, half_32072, -10.0, 10.0)

    # 3648b: Technic Gear 24 Tooth with Single Axle Hole -- D=64.78, z: [-9.62, 9.62]
    half_3648b = 64.78 / (2 * math.sqrt(2))
    occ, sockets, needs = P.resolve_occupancy_and_sockets("3648b", "Technic Gear 24 Tooth with Single Axle Hole")
    assert needs is False
    assert sockets == []
    assert len(occ) == 4
    assert occ[0] == (-half_3648b, half_3648b, 6.0, half_3648b, -9.62, 9.62)

    # 3649: Technic Gear 40 Tooth -- D=104.70, z: [-10.0, 10.0]
    half_3649 = 104.70 / (2 * math.sqrt(2))
    occ, sockets, needs = P.resolve_occupancy_and_sockets("3649", "Technic Gear 40 Tooth")
    assert needs is False
    assert sockets == []
    assert len(occ) == 4
    assert occ[0] == (-half_3649, half_3649, 6.0, half_3649, -10.0, 10.0)


@pytest.mark.skipif(not LDRAW_CACHE.exists(), reason="LDraw library not fetched (scripts/ldraw/fetch_library.py)")
@pytest.mark.parametrize("pid,expected_d,expected_z0,expected_z1", [
    ("10928", 24.86, -10.0, 10.0),   # Technic Gear 8 Tooth Reinforced
    ("3647", 24.86, -10.0, 10.0),    # Technic Gear 8 Tooth
    ("94925", 43.28, -10.0, 10.0),   # Technic Gear 16 Tooth Reinforced
    ("4019", 43.28, -10.0, 10.0),    # Technic Gear 16 Tooth
    ("6589", 32.00, -3.0, 7.0),      # Technic Gear 12 Tooth Bevel
    ("18575", 54.00, -10.0, 10.0),   # Technic Gear 20 Tooth Double Bevel Reinforced
    ("32269", 54.00, -10.0, 10.0),   # Technic Gear 20 Tooth Double Bevel
    ("32072", 60.00, -10.0, 10.0),   # Technic Gear 4 Knob
    ("3648b", 64.78, -9.62, 9.62),   # Technic Gear 24 Tooth with Single Axle Hole
    ("3649", 104.70, -10.0, 10.0),   # Technic Gear 40 Tooth
    ("3650a", 65.96, -8.0, 12.0),    # Technic Gear 24 Tooth Crown Type 1
    ("4143", 35.88, -4.0, 3.0),      # Technic Gear 14 Tooth Bevel
    ("32198a", 52.00, -7.0, 3.0),    # Technic Gear 20 Tooth Bevel with Two Axlehole Slots
])
def test_real_resolved_technic_gear_sample_matches_geometry_and_remains_within_bounds(pid, expected_d, expected_z0, expected_z1):
    """Representative sample of 13 real Technic gear parts verified against real resolved geometry."""
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
    assert round((dx + dy) / 2.0, 2) == pytest.approx(expected_d, abs=0.1)
    assert round(part.min[2], 2) == pytest.approx(expected_z0, abs=0.1)
    assert round(part.max[2], 2) == pytest.approx(expected_z1, abs=0.1)

    # Dispatcher resolves with real bounds
    occ, sockets, needs = P.resolve_occupancy_and_sockets(
        pid, part.title, part.min, part.max, part.holes, part.studs, part.tris, part.cylinders
    )
    assert needs is False
    assert sockets == []
    assert len(occ) == 4

    r_out = (dx + dy) / 4.0
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
    "3743",    # Linear gear rack 1 x 4 (bounds: -40,-6,-10 .. 40,8,10)
    "24014",   # Technic gear 12 tooth double bevel with axle extension (asymmetric X: -16.6 .. 49.5)
    "18940",   # Technic gear rack 1 x 14 with bottom beam housing (linear rack)
    "24121",   # Technic gear ring quarter 11 x 11 (90-degree quadrant segment)
    "32167",   # Technic gear box half
])
def test_deliberately_excluded_gear_subgroups_remain_rejected(pid):
    """Deliberately excluded gear sub-groups (linear racks, asymmetric extensions, quadrants, casings)
    must remain rejected (needs_occupancy=True)."""
    from resolve import Library, ColourTable, resolve_part
    lib = Library(str(LDRAW_CACHE))
    colours = ColourTable(lib)
    part = resolve_part(lib, colours, pid + ".dat")
    occ, sockets, needs = P.resolve_occupancy_and_sockets(
        pid, part.title, part.min, part.max, part.holes, part.studs, part.tris, part.cylinders
    )
    assert needs is True, "%s should remain rejected (needs_occupancy=True)" % pid
    assert occ is None


# -----------------------------------------------------------------------------
# Wheel catalogue extension (2026-09-28, agent/wheel-catalogue-extension, cloud task)
# -----------------------------------------------------------------------------

@pytest.mark.skipif(not LDRAW_CACHE.exists(), reason="LDraw library not fetched (scripts/ldraw/fetch_library.py)")
def test_duplo_wheel_bore_verification():
    """Verify that 12589 safely uses the standard 8.0 LDU bore exclusion (matching its 12588 axle
    shaft radius 8.0), whereas 15315 requires an oversized 10.0 LDU bore (matching 15316 axle) and
    thus properly remains excluded from standard WHEEL_BORE_HALF occupancy."""
    from resolve import Library, ColourTable, resolve_part
    lib = Library(str(LDRAW_CACHE))
    colours = ColourTable(lib)

    # 12589 is accepted
    p12589 = resolve_part(lib, colours, "12589.dat")
    occ, sockets, needs = P.resolve_occupancy_and_sockets(
        "12589", p12589.title, p12589.min, p12589.max, p12589.holes, p12589.studs, p12589.tris, p12589.cylinders
    )
    assert needs is False
    assert len(occ) == 4
    # All 4 boxes strictly outside the Duplo 12588 axle radius of 8.0
    for b in occ:
        overlap_duplo_axle = (b[0] < 8.0 and b[1] > -8.0 and b[2] < 8.0 and b[3] > -8.0)
        assert not overlap_duplo_axle, f"Box {b} overlaps Duplo axle!"

    # 15315 remains rejected because standard bore (8.0) would collide with its 10.0 LDU radius axle
    p15315 = resolve_part(lib, colours, "15315.dat")
    occ15, _, needs15 = P.resolve_occupancy_and_sockets(
        "15315", p15315.title, p15315.min, p15315.max, p15315.holes, p15315.studs, p15315.tris, p15315.cylinders
    )
    assert needs15 is True
    assert occ15 is None


# -----------------------------------------------------------------------------
# Technic remainder survey (2026-09-28, agent/technic-remainder-survey, cloud task)
# -----------------------------------------------------------------------------

TECHNIC_PIN_OVERRIDES = [
    ("89678", [P.box(-20, 0, -6, 6, -6, 6)], 1),
    ("4459", [P.box(-20, 20, -6, 6, -6, 6)], 2),
    ("61332", [P.box(-20, 20, -6, 6, -6, 6)], 2),
    ("32002", [P.box(-20, 10, -6, 6, -6, 6)], 1),
    ("32556a", [P.box(-30, 30, -6, 6, -6, 6)], 3),
    ("32556b", [P.box(-30, 30, -6, 6, -6, 6)], 3),
    ("39888", [P.box(-30, 30, -6, 6, -6, 6)], 3),
    ("42924", [P.box(-30, 30, -6, 6, -6, 6)], 3),
    ("77765", [P.box(-30, 30, -6, 6, -6, 6)], 3),
    ("65304", [P.box(-30, 30, -6, 6, -6, 6)], 3),
]


@pytest.mark.parametrize("pid,expected_boxes,expected_sockets", TECHNIC_PIN_OVERRIDES)
def test_technic_pin_overrides_synthetics(pid, expected_boxes, expected_sockets):
    """Direct dispatcher test: each added pin override returns its verified box and sockets without library."""
    occ, sockets, needs = P.resolve_occupancy_and_sockets(pid, "Technic Pin", [-30, -10, -10], [30, 10, 10], [], [], [], [])
    assert needs is False
    assert occ == expected_boxes
    assert len(sockets) == expected_sockets


@pytest.mark.skipif(not LDRAW_CACHE.exists(), reason="LDraw library not fetched")
@pytest.mark.parametrize("pid,expected_boxes,expected_sockets", TECHNIC_PIN_OVERRIDES)
def test_technic_pin_overrides_real_geometry(pid, expected_boxes, expected_sockets):
    """Real geometry test: verified against resolved LDraw meshes for bounds containment and ray-parity solidity."""
    from resolve import Library, ColourTable, resolve_part
    lib = Library(str(LDRAW_CACHE))
    colours = ColourTable(lib)
    part = resolve_part(lib, colours, pid + ".dat")
    occ, sockets, needs = P.resolve_occupancy_and_sockets(
        pid, part.title or pid, part.min, part.max, part.holes, part.studs, part.tris, part.cylinders
    )
    assert needs is False
    assert occ == expected_boxes
    assert len(sockets) == expected_sockets
    assert P._boxes_within_bounds(occ, part.min, part.max)
    for b in occ:
        sol = P._stud_box_solid_fraction(part.tris, b)
        assert sol >= P.STUD_CELL_MIN_SOLID, f"Part {pid} box {b} solid fraction {sol:.3f} below {P.STUD_CELL_MIN_SOLID}"


@pytest.mark.skipif(not LDRAW_CACHE.exists(), reason="LDraw library not fetched")
@pytest.mark.parametrize("pid", [
    # Bushes: hollow axle bore down center / tri-axial star
    "3713", "4265a", "57585",
    # Cross blocks: orthogonal hole bores along Z vs X; thin corner slivers fail solidity floor
    "32291", "32557", "63869", "98989",
    # Representative irregular / complex mechanical components
    "32039", "32126", "2736", "4716", "64451",
])
def test_technic_remainder_honestly_rejected_parts(pid):
    """Technic remainder survey controls: parts where geometry or insertion physics forbids simple box occupancy
    must strictly remain needs_occupancy=True rather than being guessed."""
    from resolve import Library, ColourTable, resolve_part
    lib = Library(str(LDRAW_CACHE))
    colours = ColourTable(lib)
    part = resolve_part(lib, colours, pid + ".dat")
    occ, sockets, needs = P.resolve_occupancy_and_sockets(
        pid, part.title or pid, part.min, part.max, part.holes, part.studs, part.tris, part.cylinders
    )
    assert needs is True, f"Part {pid} ({part.title}) was falsely accepted"
    assert occ is None
    assert sockets == []


# -----------------------------------------------------------------------------
# Minifig Torso generic occupancy (2026-09-28, agent/minifig-torso, cloud task)
# -----------------------------------------------------------------------------

def test_generic_torso_occupancy_synthetic():
    """Synthetic standard minifig torso: [-19, 19, -12, 32, -10, 10] with solid triangles."""
    tris = _box_tris(-19, 19, -12, 32, -10, 10)
    occ, sockets = P.generic_torso_occupancy((-19.0, -12.0, -10.0), (19.0, 32.0, 10.0), [], tris, "Minifig Torso")
    assert occ == [(-19.0, 19.0, 0.0, 32.0, -10.0, 10.0)]
    assert sockets == []


def test_generic_torso_occupancy_synthetic_exclusions():
    """Exclusions required by spec §3 (under-approximate, never guess)."""
    tris = _box_tris(-19, 19, -12, 32, -10, 10)

    # Top studs must not enter torso path
    top_studs = [((0.0, 0.0, 0.0), (0.0, -1.0, 0.0))]
    assert P.generic_torso_occupancy((-19, -12, -10), (19, 32, 10), top_studs, tris, "Minifig Torso") == (None, [])

    # Flat sticker sheet
    assert P.generic_torso_occupancy((-18, -0.25, -15), (18, 0, 15), [], tris, "Sticker Minifig Torso") == (None, [])

    # Appendages / fantasy non-standard torsos
    assert P.generic_torso_occupancy((-56, -22, -10), (56, 35, 10), [], tris, "Minifig Torso with Bat Wing Arms") == (None, [])
    assert P.generic_torso_occupancy((-37, -12, -12), (37, 45, 12), [], tris, "Minifig Torso with Flipper Arms") == (None, [])
    assert P.generic_torso_occupancy((-34, -12, -30), (34, 46, 10), [], tris, "Minifig Torso with Arms and Boxing Gloves") == (None, [])

    # Non-torso title
    assert P.generic_torso_occupancy((-19, -12, -10), (19, 32, 10), [], tris, "Brick 2 x 4") == (None, [])

    # Non-matching dimensions (e.g. wrong height or width)
    assert P.generic_torso_occupancy((-10, -12, -10), (10, 32, 10), [], tris, "Minifig Torso") == (None, [])
    assert P.generic_torso_occupancy((-19, 0, -10), (19, 24, 10), [], tris, "Minifig Torso") == (None, [])


@pytest.mark.skipif(not LDRAW_CACHE.exists(), reason="LDraw library not fetched (scripts/ldraw/fetch_library.py)")
@pytest.mark.parametrize("pid", [
    "973",       # Base Minifig Torso
    "43370",     # Minifig Torso with Arm Locking Notches
    "973d01",    # Minifig Torso with "TINE" Stickers
    "973d02",    # Minifig Torso with Yellow Buttons and Grey Belt Sticker
    "973d03",    # Minifig Torso with White Buttons and Police Badge Plain Sticker
    "973d04",    # Minifig Torso with Shell Logo on White Background Sticker
    "973d06",    # Minifig Torso with Rear Sticker White "1" on Transparent Background
    "973d07",    # Minifig Torso with Red Cross Sticker
    "973d0f",    # Minifig Torso with MD Foods Logo Sticker on Both Sides
    "973p01",    # Minifig Torso with Vertical Striped Red/Blue Pattern
    "973p04",    # Minifig Torso with Six Button Suit and Airplane Pattern
    "973p0a",    # Minifig Torso with White Diagonal Zip and Pocket Pattern
    "973p14",    # Minifig Torso with "S" Logo Red / Black Pattern
    "973p18",    # Minifig Torso with Suit and Tie Pattern
    "973p1f",    # Minifig Torso with Police Officer Pattern
    "973p21",    # Minifig Torso with Firefighter Pattern
    "973p2a",    # Minifig Torso with Chef Pattern
    "973p31",    # Minifig Torso with Pirate Pattern
    "973p36",    # Minifig Torso with Pirate Captain Pattern
    "973p42",    # Minifig Torso with Castle Knight Pattern
    "973p46",    # Minifig Torso with Forestman Pattern
    "973p4f",    # Minifig Torso with Lion Knight Pattern
    "973p4j",    # Minifig Torso with King Pattern
    "973p90",    # Minifig Torso with Classic Space Astronaut Pattern
    "973p2q",    # Minifig Torso with Viking Armour (x=19.11)
    "973p8j",    # Minifig Torso with Town Vest (y=32.1)
])
def test_real_torso_parts_accepted(pid):
    """Real minifig torso parts (base, sticker, and printed variants) verified via resolve_part."""
    from resolve import Library, ColourTable, resolve_part
    lib = Library(str(LDRAW_CACHE))
    colours = ColourTable(lib)
    part = resolve_part(lib, colours, pid + ".dat")
    occ, sockets, needs = P.resolve_occupancy_and_sockets(
        pid, part.title or pid, part.min, part.max, part.holes, part.studs, part.tris, part.cylinders
    )
    assert needs is False, f"{pid} should be accepted"
    assert occ == [(-19.0, 19.0, 0.0, 32.0, -10.0, 10.0)]
    assert sockets == []


@pytest.mark.skipif(not LDRAW_CACHE.exists(), reason="LDraw library not fetched (scripts/ldraw/fetch_library.py)")
@pytest.mark.parametrize("pid", [
    "10677",     # Minifig Torso with Bat Wing Arms
    "11938",     # Minifig Torso with Bird Wing Arms
    "24319",     # Minifig Torso with Flipper Arms
    "97149",     # Minifig Torso with Arms and Boxing Gloves
    "37777",     # Minifig Torso Half Giant
    "003428b",   # Sticker Minifig Torso with Shirt
])
def test_real_torso_feature_exclusions_stay_rejected(pid):
    """Feature-bearing or novelty torsos that cannot safely use standard rectangular torso occupancy."""
    from resolve import Library, ColourTable, resolve_part
    lib = Library(str(LDRAW_CACHE))
    colours = ColourTable(lib)
    part = resolve_part(lib, colours, pid + ".dat")
    occ, sockets, needs = P.resolve_occupancy_and_sockets(
        pid, part.title or pid, part.min, part.max, part.holes, part.studs, part.tris, part.cylinders
    )
    assert needs is True, f"{pid} should remain needs_occupancy=True"
    assert occ is None


# -----------------------------------------------------------------------------
# Technic Axle generic occupancy (2026-09-28, agent/technic-axle-occupancy)
# -----------------------------------------------------------------------------

def test_generic_axle_occupancy_synthetic_plain():
    """Synthetic plain Technic Axle: [-29.5, 29.5, -6.0, 6.0, -6.0, 6.0] with solid triangles."""
    tris = _box_tris(-29.5, 29.5, -6.0, 6.0, -6.0, 6.0)
    occ, sockets = P.generic_axle_occupancy((-29.5, -6.0, -6.0), (29.5, 6.0, 6.0), [], [], [], tris, "Technic Axle  3")
    assert occ == [(-29.5, 29.5, -6.0, 6.0, -6.0, 6.0)]
    assert sockets == []


def test_generic_axle_occupancy_synthetic_with_stop():
    """Synthetic Axle with Stop: shaft (-29.5..28.0 at +-6) and flange (28.0..30.0 at +-8)."""
    tris_shaft = _box_tris(-29.5, 28.0, -6.0, 6.0, -6.0, 6.0)
    tris_flange = _box_tris(28.0, 30.0, -8.0, 8.0, -8.0, 8.0)
    tris = tris_shaft + tris_flange
    cyl = [((30.0, 0.0, 0.0), (-2.0, 0.0, 0.0), 8.0)]
    occ, sockets = P.generic_axle_occupancy(
        (-29.5, -8.0, -8.0), (30.0, 8.0, 8.0), [], [], cyl, tris, "Technic Axle  3 with Stop"
    )
    assert occ == [
        (-29.5, 28.0, -6.0, 6.0, -6.0, 6.0),
        (28.0, 30.0, -8.0, 8.0, -8.0, 8.0),
    ]
    assert sockets == []


def test_generic_axle_occupancy_synthetic_threaded():
    """Synthetic Z-axis threaded axle: [-6.0, 6.0, -6.0, 6.0, -40.0, 40.0]."""
    tris = _box_tris(-6.0, 6.0, -6.0, 6.0, -40.0, 40.0)
    occ, sockets = P.generic_axle_occupancy((-6.0, -6.0, -40.0), (6.0, 6.0, 40.0), [], [], [], tris, "Technic Axle  4 Threaded")
    assert occ == [(-6.0, 6.0, -6.0, 6.0, -40.0, 40.0)]
    assert sockets == []


def test_generic_axle_occupancy_synthetic_exclusions():
    """Exclusions required by spec §3 (under-approximate, never guess)."""
    tris = _box_tris(-29.5, 29.5, -6.0, 6.0, -6.0, 6.0)

    # Top studs must not enter axle path
    top_studs = [((0.0, 0.0, 0.0), (0.0, -1.0, 0.0))]
    assert P.generic_axle_occupancy((-29.5, -6.0, -6.0), (29.5, 6.0, 6.0), top_studs, [], [], tris, "Technic Axle 3") == (None, [])

    # Holes must not enter axle path
    holes = [((0.0, 0.0, 0.0), (0.0, 0.0, 1.0))]
    assert P.generic_axle_occupancy((-29.5, -6.0, -6.0), (29.5, 6.0, 6.0), [], holes, [], tris, "Technic Axle 3") == (None, [])

    # Axle-pin hybrids
    assert P.generic_axle_occupancy((-20.0, -8.0, -8.0), (19.5, 8.0, 8.0), [], [], [], tris, "Technic Axle Pin with Friction") == (None, [])

    # Axle joiners
    assert P.generic_axle_occupancy((-10.0, -10.0, -20.0), (10.0, 10.0, 20.0), [], [], [], tris, "Technic Axle Joiner") == (None, [])

    # Flexible axles
    assert P.generic_axle_occupancy((-70.0, -6.0, -6.0), (70.0, 6.0, 6.0), [], [], [], tris, "Technic Axle Flexible  7") == (None, [])

    # Non-axle title
    assert P.generic_axle_occupancy((-29.5, -6.0, -6.0), (29.5, 6.0, 6.0), [], [], [], tris, "Brick 2 x 4") == (None, [])

    # Non-matching dimensions (e.g. wrong cross section)
    assert P.generic_axle_occupancy((-29.5, -10.0, -10.0), (29.5, 10.0, 10.0), [], [], [], tris, "Technic Axle 3") == (None, [])

    # Too short (< 15 LDU)
    assert P.generic_axle_occupancy((-5.0, -6.0, -6.0), (5.0, 6.0, 6.0), [], [], [], tris, "Technic Axle") == (None, [])


@pytest.mark.skipif(not LDRAW_CACHE.exists(), reason="LDraw library not fetched")
@pytest.mark.parametrize("pid, expected_x_span", [
    ("3704", (-19.5, 19.5)),       # Axle 2
    ("32062", (-19.5, 19.5)),      # Axle 2 Notched
    ("4109810", (-19.5, 19.5)),    # Axle 2 Notched Black Obsolete
    ("4519", (-29.5, 29.5)),       # Axle 3
    ("4211815", (-29.5, 29.5)),    # Axle 3 Obsolete
    ("3705", (-39.5, 39.5)),       # Axle 4
    ("370526", (-39.5, 39.5)),     # Axle 4 Black Obsolete
    ("99008", (-39.5, 39.5)),      # Axle 4 with Middle Cylindrical Stop
    ("32073", (-49.5, 49.5)),      # Axle 5
    ("3706", (-59.5, 59.5)),       # Axle 6
    ("370626", (-59.5, 59.5)),     # Axle 6 Black Obsolete
    ("44294", (-69.5, 69.5)),      # Axle 7
    ("3707", (-79.5, 79.5)),       # Axle 8
    ("370726", (-79.5, 79.5)),     # Axle 8 Black Obsolete
    ("60485", (-89.5, 89.5)),      # Axle 9
    ("3737", (-99.5, 99.5)),       # Axle 10
    ("23948", (-109.5, 109.5)),    # Axle 11
    ("3708", (-119.5, 119.5)),     # Axle 12
    ("370826", (-119.5, 119.5)),   # Axle 12 Black Obsolete
    ("50451", (-159.5, 159.5)),    # Axle 16
    ("69732", (-159.5, 159.5)),    # =Technic Axle 16
    ("50450", (-319.5, 319.5)),    # Axle 32
    ("u1208a", (-21.5, 20.0)),     # Axle Adapter Metal Short
    ("u1208b", (-21.5, 40.0)),     # Axle Adapter Metal Long
    ("2497", (-80.0, 80.0)),       # Car Wash Brush Axle
    ("t1114", (0.5, 34.5)),        # Circuit Cubes Axle 1.75 Notched
    ("t1115", (0.5, 24.5)),        # Circuit Cubes Axle 1.25 Notched
])
def test_real_plain_axle_parts_accepted(pid, expected_x_span):
    """Real plain Technic Axle parts verified via resolve_part."""
    from resolve import Library, ColourTable, resolve_part
    lib = Library(str(LDRAW_CACHE))
    colours = ColourTable(lib)
    part = resolve_part(lib, colours, pid + ".dat")
    occ, sockets, needs = P.resolve_occupancy_and_sockets(
        pid, part.title or pid, part.min, part.max, part.holes, part.studs, part.tris, part.cylinders
    )
    assert needs is False, f"{pid} ({part.title}) should be accepted"
    x0, x1 = expected_x_span
    assert occ == [(x0, x1, -6.0, 6.0, -6.0, 6.0)]
    assert sockets == []


@pytest.mark.skipif(not LDRAW_CACHE.exists(), reason="LDraw library not fetched")
@pytest.mark.parametrize("pid, expected_z_span", [
    ("3705c01", (-40.0, 40.0)),     # Technic Axle 4 Threaded
    ("73839", (-40.0, 40.0)),       # Technic Axle 4 Threaded Black Obsolete
    ("3737c01", (-100.0, 100.0)),   # Technic Axle 10 Threaded
    ("73485", (-100.0, 100.0)),     # Technic Axle 10 Threaded Black Obsolete
])
def test_real_threaded_axle_parts_accepted(pid, expected_z_span):
    """Real threaded Technic Axle parts spanning along Z verified via resolve_part."""
    from resolve import Library, ColourTable, resolve_part
    lib = Library(str(LDRAW_CACHE))
    colours = ColourTable(lib)
    part = resolve_part(lib, colours, pid + ".dat")
    occ, sockets, needs = P.resolve_occupancy_and_sockets(
        pid, part.title or pid, part.min, part.max, part.holes, part.studs, part.tris, part.cylinders
    )
    assert needs is False, f"{pid} ({part.title}) should be accepted"
    z0, z1 = expected_z_span
    assert occ == [(-6.0, 6.0, -6.0, 6.0, z0, z1)]
    assert sockets == []


@pytest.mark.skipif(not LDRAW_CACHE.exists(), reason="LDraw library not fetched")
@pytest.mark.parametrize("pid, expected_boxes", [
    ("24316", [(-29.5, 28.0, -6.0, 6.0, -6.0, 6.0), (28.0, 30.0, -8.0, 8.0, -8.0, 8.0)]),
    ("87083", [(-39.5, 38.0, -6.0, 6.0, -6.0, 6.0), (38.0, 40.0, -8.0, 8.0, -8.0, 8.0)]),
    ("15462", [(-49.5, 48.0, -6.0, 6.0, -6.0, 6.0), (48.0, 50.0, -8.0, 8.0, -8.0, 8.0)]),
    ("55013", [(-79.5, 78.0, -6.0, 6.0, -6.0, 6.0), (78.0, 80.0, -8.0, 8.0, -8.0, 8.0)]),
    ("32209", [(-55.0, -37.0, -6.0, 6.0, -6.0, 6.0), (-37.0, -35.0, -8.0, 8.0, -8.0, 8.0), (-35.0, 52.5, -6.0, 6.0, -6.0, 6.0)]),
    ("59426", [(-54.5, -37.0, -6.0, 6.0, -6.0, 6.0), (-37.0, -35.0, -8.0, 8.0, -8.0, 8.0), (-35.0, 54.5, -6.0, 6.0, -6.0, 6.0)]),
    ("4263624", [(-55.0, -37.0, -6.0, 6.0, -6.0, 6.0), (-37.0, -35.0, -8.0, 8.0, -8.0, 8.0), (-35.0, 52.5, -6.0, 6.0, -6.0, 6.0)]),
])
def test_real_with_stop_axle_parts_accepted(pid, expected_boxes):
    """Real Technic Axle with Stop parts decomposed into shaft and flange boxes."""
    from resolve import Library, ColourTable, resolve_part
    lib = Library(str(LDRAW_CACHE))
    colours = ColourTable(lib)
    part = resolve_part(lib, colours, pid + ".dat")
    occ, sockets, needs = P.resolve_occupancy_and_sockets(
        pid, part.title or pid, part.min, part.max, part.holes, part.studs, part.tris, part.cylinders
    )
    assert needs is False, f"{pid} ({part.title}) should be accepted"
    assert occ == expected_boxes
    assert sockets == []


@pytest.mark.skipif(not LDRAW_CACHE.exists(), reason="LDraw library not fetched")
@pytest.mark.parametrize("pid", [
    "6587",       # Technic Axle  3 with Stud
    "13670",      # =Technic Axle  3 with Stud
    "11214",      # Technic Axle Pin Long with Friction with 2L Pin
    "18651",      # Technic Axle Pin Long with Friction with 2L Axle
    "43093",      # Technic Axle Pin with Friction
    "11272",      # Technic Axle Connector  2 x  3 Quadruple
    "6538a",      # Technic Axle Joiner
    "21755",      # Technic Axle Joiner  2L Hilt
    "18948",      # Technic Axle Joiner  3L with Ridges for Driving Ring
    "45590",      # Technic Axle Joiner Double Flexible
    "53586",      # Technic Axle Joiner Perpendicular with Extension
    "4698",       # Technic Axle Nut
    "2736",       # Technic Axle Towball
    "10197",      # Technic Axle and Pin Connector Hub with 2 Axles at 90 Degrees
    "72892",      # Technic Axle Flexible 26 with Axle 4.8L and Axle 2L on Ends
])
def test_real_axle_feature_exclusions_stay_rejected(pid):
    """Axle-named components with studs, friction pins, joiner tubes, or flexible cables must remain rejected."""
    from resolve import Library, ColourTable, resolve_part
    lib = Library(str(LDRAW_CACHE))
    colours = ColourTable(lib)
    part = resolve_part(lib, colours, pid + ".dat")
    occ, sockets, needs = P.resolve_occupancy_and_sockets(
        pid, part.title or pid, part.min, part.max, part.holes, part.studs, part.tris, part.cylinders
    )
    assert needs is True, f"{pid} should remain needs_occupancy=True"
    assert occ is None




