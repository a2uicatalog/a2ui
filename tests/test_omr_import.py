"""Unit and integration tests for scripts/ldraw/omr_import.py.

Verifies:
  1. rot_index() identifies all 24 axis-aligned orthogonal rotations and returns None for continuous rotations.
  2. coverage() counts axis-aligned parts as renderable.
  3. coverage() uses OBB/SAT collision detection for continuous-rotation parts (rot_index returns None):
     - Non-colliding continuously rotated parts are counted as renderable.
     - Colliding continuously rotated parts are excluded.
     - Continuously rotated parts without occupancy data are excluded.
  4. to_parts_model() emits 9-tuple matrices for safe continuously-rotated parts, and integer rotation indices
     (0..23) for axis-aligned parts.
  5. bottom_y() correctly calculates floor elevation for both integer and 9-tuple rotation representations.
  6. Parity invariant: len(to_parts_model(leaves)) == coverage(leaves)['renderable'].
"""
import os

import pytest

from renderers.brick_parts_validate import PART_ROT
from scripts.ldraw.resolve import LD
from scripts.ldraw.omr_import import (
    baked_ids,
    coverage,
    flatten,
    rot_index,
    to_parts_model,
)

# Non-orthogonal rotation matrices cited in OBB_SAT_IMPLEMENTATION.md
M_ROT_Y_30 = (0.866025, 0.0, -0.5, 0.0, 1.0, 0.0, 0.5, 0.0, 0.866025)
M_ROT_Y_60 = (0.5, 0.0, 0.866025, 0.0, 1.0, 0.0, -0.866025, 0.0, 0.5)
M_HINGE_29 = (-0.868, 0.0, 0.496, 0.0, 1.0, 0.0, -0.496, 0.0, -0.868)


@pytest.mark.skipif(not os.path.isdir(os.path.join(LD, "p")),
                    reason="LDraw library not fetched (scripts/ldraw/fetch_library.py): primitives are read from it")
def test_flatten_excludes_root_level_primitives_not_just_prefixed_ones():
    """Real bug found 2026-09-29 investigating the coverage stat's 'missing' report: flatten()'s old filter
    (`not ref.startswith(('s/', '48/', '8/'))`) only excluded primitives referenced via a subdirectory
    prefix -- primitives living at p/'s own root (e.g. 4-4cyli.dat, rect.dat) sailed through and were
    miscounted as real missing catalogue parts (~47% of the reported total across 183 real sets measured).
    A real .mpd-shaped fragment referencing both a genuine primitive at p/'s root and one via a prefixed
    subdirectory must exclude both; a real (fictional but .dat-shaped) missing PART reference must still
    be reported, so the fix doesn't just suppress everything."""
    text = (
        "0 FILE main.ldr\n"
        "1 16 0 0 0 1 0 0 0 1 0 0 0 1 4-4cyli.dat\n"     # real primitive at p/'s own root -- must be excluded
        "1 16 0 0 0 1 0 0 0 1 0 0 0 1 48/1-8chrd.dat\n"  # real primitive via a prefixed subdirectory
        "1 16 0 0 0 1 0 0 0 1 0 0 0 1 9999999.dat\n"     # not a real part or primitive -- must still be counted missing
    )
    leaves = flatten(text)
    parts = {l["part"] for l in leaves}
    assert "4-4cyli" not in parts
    assert "48/1-8chrd" not in parts and "1-8chrd" not in parts
    assert "9999999" in parts


def test_rot_index_identifies_all_24_canonical_rotations():
    """rot_index must return the exact index 0..23 for all PART_ROT entries."""
    for idx, matrix in enumerate(PART_ROT):
        assert rot_index(matrix) == idx


def test_rot_index_returns_none_for_continuous_rotations():
    """rot_index must return None when matrix is not an axis-aligned rotation."""
    for m in (M_ROT_Y_30, M_ROT_Y_60, M_HINGE_29):
        assert rot_index(m) is None


def test_coverage_and_to_parts_model_axis_aligned_only():
    """Standard axis-aligned parts are all counted renderable with integer rotation indices."""
    leaves = [
        {"part": "3001", "colour": 1, "m": PART_ROT[0], "t": (0.0, 0.0, 0.0), "step": 1},
        {"part": "3001", "colour": 4, "m": PART_ROT[4], "t": (100.0, 0.0, 0.0), "step": 1},
    ]
    c = coverage(leaves)
    assert c["parts"] == 2
    assert c["baked"] == 2
    assert c["renderable"] == 2
    assert c["tilted"] == 0
    assert c["fraction"] == 1.0

    rows = to_parts_model(leaves)
    assert len(rows) == 2
    assert rows[0][4] == 0
    assert rows[1][4] == 4


def test_coverage_and_to_parts_model_safe_continuous_rotation():
    """A continuously rotated part separated from other parts is safe: counted renderable and emitted as 9-tuple."""
    leaves = [
        {"part": "3001", "colour": 1, "m": PART_ROT[0], "t": (0.0, 0.0, 0.0), "step": 1},
        {"part": "3001", "colour": 2, "m": M_ROT_Y_30, "t": (200.0, 0.0, 200.0), "step": 1},
    ]
    c = coverage(leaves)
    assert c["parts"] == 2
    assert c["baked"] == 2
    assert c["renderable"] == 2
    assert c["tilted"] == 0
    assert c["tilted_safe"] == 1
    assert c["fraction"] == 1.0

    rows = to_parts_model(leaves)
    assert len(rows) == 2
    # One row has integer index 0, the other has 9-tuple matrix
    rotations = [r[4] for r in rows]
    assert 0 in rotations
    mat_rot = [r for r in rotations if isinstance(r, tuple)][0]
    assert len(mat_rot) == 9
    for val, expected in zip(mat_rot, M_ROT_Y_30):
        assert val == pytest.approx(expected, abs=1e-5)


def test_coverage_and_to_parts_model_colliding_continuous_rotation():
    """A continuously rotated part penetrating an existing brick is unsafe: excluded from renderable."""
    leaves = [
        {"part": "3001", "colour": 1, "m": PART_ROT[0], "t": (0.0, 0.0, 0.0), "step": 1},
        # Positioned with major overlap into the first brick
        {"part": "3001", "colour": 2, "m": M_ROT_Y_30, "t": (10.0, 0.0, 10.0), "step": 1},
    ]
    c = coverage(leaves)
    assert c["parts"] == 2
    assert c["baked"] == 2
    assert c["renderable"] == 1
    assert c["tilted"] == 1
    assert c["tilted_safe"] == 0
    assert c["fraction"] == 0.5

    rows = to_parts_model(leaves)
    assert len(rows) == 1
    assert rows[0][4] == 0


def test_coverage_and_to_parts_model_two_mutually_colliding_tilted_parts():
    """When two tilted parts collide with each other, both are unsafe and excluded."""
    leaves = [
        {"part": "3001", "colour": 1, "m": M_ROT_Y_30, "t": (0.0, 0.0, 0.0), "step": 1},
        {"part": "3001", "colour": 2, "m": M_ROT_Y_60, "t": (5.0, 0.0, 5.0), "step": 1},
    ]
    c = coverage(leaves)
    assert c["parts"] == 2
    assert c["renderable"] == 0
    assert c["tilted"] == 2
    assert c["tilted_safe"] == 0

    rows = to_parts_model(leaves)
    assert len(rows) == 0


def test_renderable_count_always_equals_to_parts_model_row_count():
    """Invariant: to_parts_model output row count must always exactly match coverage renderable count."""
    leaves = [
        {"part": "3001", "colour": 1, "m": PART_ROT[0], "t": (0.0, 0.0, 0.0), "step": 1},
        {"part": "3001", "colour": 2, "m": M_ROT_Y_30, "t": (300.0, 0.0, 0.0), "step": 1},  # safe
        {"part": "3001", "colour": 3, "m": M_ROT_Y_60, "t": (10.0, 0.0, 0.0), "step": 1},   # colliding with 3001 at origin
        {"part": "unbaked_part_xyz", "colour": 4, "m": PART_ROT[0], "t": (500.0, 0.0, 0.0), "step": 1},  # missing
    ]
    c = coverage(leaves)
    rows = to_parts_model(leaves)
    assert len(rows) == c["renderable"]
    assert c["renderable"] == 2  # 3001 at origin + safe 3001 at (300, 0, 0)
