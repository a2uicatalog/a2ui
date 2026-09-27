"""scripts/ldraw/parts.py's generic_stud_cell_occupancy (2026-09-26): the library-wide occupancy fallback that lets
the catalogue expand past the hand-curated ROUND_PARTS/CORNER_L_PARTS/SLOPE_BACK_WALL_PARTS tables without hand-
verifying each new part id. It generalises those tables' own justification (a stud flush at y=0 facing up always
has solid material beneath it) into an automated ray-parity PROOF against the part's own real triangles, so a
candidate is only ever accepted once it is actually geometrically demonstrated, never assumed from title/shape
alone. These tests use synthetic geometry (no LDraw library needed, so they run in CI) plus, where the fetched
library is present, real curated parts to prove parity with the hand-verified tables it is meant to subsume."""
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


def test_generic_occupancy_drops_a_sideways_stud_but_keeps_the_flush_one():
    """A SNOT part's side stud (dir facing -Z, not up) must not get a 'solid column beneath it' box -- there is no
    'beneath' for a sideways stud -- but (2026-09-27, see test above) no longer poisons a genuinely flush sibling
    stud on the same part either. Real 11211 needs its OVERRIDES entry regardless (its flush studs alone give a
    different, smaller footprint than the hand-authored override), covered by the parametrized test below."""
    tris = _box_tris(-10, 10, 0, 24, -10, 10)
    studs = [((0.0, 0.0, 0.0), (0.0, -1.0, 0.0)), ((0.0, 12.0, -10.0), (0.0, 0.0, -1.0))]
    occ, sockets = P.generic_stud_cell_occupancy((-10, 0, -10), (10, 24, 10), studs, tris)
    assert occ == [(-10.0, 10.0, 0, 24.0, -10.0, 10.0)]
    assert sockets == [((0.0, 24, 0.0), (0, 1, 0))]


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


# pid -> expected occ after the 2026-09-27 per-stud relaxation: only each part's genuinely flush, individually
# solid-proven studs contribute a box now (real values, checked against a live resolve, not asserted blind).
# 11211 has 2 flush top studs (its 2 SNOT side studs are excluded, same as always) -- note this is a SMALLER,
# different footprint than 11211's own OVERRIDES entry (a full 1x2 body), so the dispatcher must still prefer
# OVERRIDES over this generic result (covered by test_dispatcher_prefers_named_families_and_overrides... above).
# 3665a/3660a each have their ramp-side stud(s) at y=4 excluded, keeping only the flush y=0 stud(s).
_RELAXED_REAL_PARTS = {
    "11211": [(0.0, 20.0, 0.0, 24.0, -10.0, 10.0), (-20.0, 0.0, 0.0, 24.0, -10.0, 10.0)],
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
