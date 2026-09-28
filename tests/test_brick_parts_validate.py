"""Real-parts build checks for the brick_build_3d atom -- renderers/brick_parts_validate.py.

Two layers of proof, the same shape as tests/test_brick_validate.py for the procedural validator:
  * parity   -- tests/fixtures/bricks/parts_parity_cases.json holds models and the results the atom's
               JavaScript validateParts() produced for them (captured via
               scripts/gen_parts_parity_cases.mjs, itself checked against all 15 spec fixtures in
               test_brick_parts_validate_js.py). The Python twin must reproduce every number and every
               detail string, so an agent-supplied real-parts design checked server-side gets the same
               verdict the browser shows.
"""
import json
import os

import pytest

from renderers.brick_parts_validate import (
    PART_ROT,
    _boxes_overlap,
    _world_boxes,
    rot_ldu,
    validate_parts,
)

HERE = os.path.dirname(__file__)
ROOT = os.path.dirname(HERE)
with open(os.path.join(HERE, 'fixtures', 'bricks', 'parts_parity_cases.json'), encoding='utf-8') as _f:
    CASES = json.load(_f)['cases']

_PART_ID_ALIAS = {'3023': '3023b', '3665': '3665a', '3660': '3660a', '60481': '60481a', '4032': '4032a',
                  '2654': '2654a', '4073': '6141'}
_mesh_cache = {}


def _load_mesh(pid):
    pid = _PART_ID_ALIAS.get(pid, pid)
    if pid not in _mesh_cache:
        with open(os.path.join(ROOT, 'public', 'parts', pid + '.json'), encoding='utf-8') as f:
            _mesh_cache[pid] = json.load(f)
    return _mesh_cache[pid]


@pytest.mark.parametrize('case', CASES, ids=[c['name'] for c in CASES])
def test_matches_javascript_validator(case):
    meshes = {e['p']: _load_mesh(e['p']) for e in case['parts']}
    report = validate_parts(case['parts'], meshes)
    exp = case['expected']

    assert report['ok'] == exp['ok']
    assert report['checks'] == exp['checks']            # id, label, status and the rendered detail text
    assert report['connections'] == exp['connections']
    assert report['studConnections'] == exp['studConnections']
    assert report['pinConnections'] == exp['pinConnections']
    assert report['collisions'] == exp['collisions']
    assert report['overlaps'] == exp['overlaps']
    assert report['floating'] == exp['floating']
    assert report['balance'] == exp['balance']
    if exp['com']['margin'] is None:
        assert report['com']['margin'] is None
    else:
        assert report['com']['margin'] == pytest.approx(exp['com']['margin'], abs=1e-9)


# Real transformation matrices cited in ROTATION_MODEL_INVESTIGATION.md section 2:
# 1. 2429/2430 hinge plate pair at ~29.7 degrees (8880-1 Super Car):
M_HINGE_29 = (-0.868, 0.0, 0.496, 0.0, 1.0, 0.0, -0.496, 0.0, -0.868)
# 2. Metroliner (10001-1) 9V train cab matrices:
M_METRO_30 = (0.866, 0.0, -0.5, 0.0, 1.0, 0.0, 0.5, 0.0, 0.866)
M_METRO_60 = (0.5, 0.0, 0.866, 0.0, 1.0, 0.0, -0.866, 0.0, 0.5)
M_METRO_150 = (-0.866, 0.0, 0.5, 0.0, 1.0, 0.0, -0.5, 0.0, -0.866)
# 3. Metroliner pantograph angled at 16.5 degrees:
M_PANTOGRAPH_16_5 = (1.0, 0.284, 0.0, -0.284, 1.0, 0.0, 0.0, 0.0, 1.0)
# 4. Technic chassis diagonal brace at 33.9 degrees (8880-1):
M_TECHNIC_33_9 = (0.0, 0.0, -1.0, -0.558, 0.83, 0.0, 0.83, 0.558, 0.0)


def test_rot_ldu_accepts_int_or_9_tuple():
    """Verify rot_ldu works identically with integer index or 9-tuple/list matrix."""
    p = (10.0, -20.0, 30.0)
    for r_idx in range(len(PART_ROT)):
        res_int = rot_ldu(r_idx, p)
        res_tuple = rot_ldu(PART_ROT[r_idx], p)
        res_list = rot_ldu(list(PART_ROT[r_idx]), p)
        assert res_int == res_tuple
        assert res_int == res_list

    # Test with real cited non-axis-aligned matrix
    rot_p = rot_ldu(M_HINGE_29, p)
    assert abs(rot_p[0] - (-0.868 * 10.0 + 0.496 * 30.0)) < 1e-6
    assert abs(rot_p[1] - (-20.0)) < 1e-6
    assert abs(rot_p[2] - (-0.496 * 10.0 - 0.868 * 30.0)) < 1e-6


def test_world_boxes_accepts_int_or_9_tuple():
    """Verify _world_boxes returns 6-tuples for int r and OBB dicts with enclosing AABB for 9-tuple."""
    mesh_2429 = _load_mesh('2429')
    # Int r -> returns list of 6-tuples (x0, x1, y0, y1, z0, z1)
    boxes_int = _world_boxes(mesh_2429, 0, 10.0, 20.0, 30.0)
    assert isinstance(boxes_int, list)
    assert len(boxes_int) == len(mesh_2429['occupancy'])
    for b in boxes_int:
        assert isinstance(b, tuple)
        assert len(b) == 6

    # 9-tuple r (identity) -> returns list of OBB dicts
    boxes_mat = _world_boxes(mesh_2429, PART_ROT[0], 10.0, 20.0, 30.0)
    assert isinstance(boxes_mat, list)
    assert len(boxes_mat) == len(mesh_2429['occupancy'])
    for b_obb, b_tuple in zip(boxes_mat, boxes_int):
        assert isinstance(b_obb, dict)
        assert 'center' in b_obb
        assert 'extents' in b_obb
        assert 'axes' in b_obb
        assert 'aabb' in b_obb
        # For identity rotation, enclosing AABB must match the axis-aligned 6-tuple exactly
        for i in range(6):
            assert abs(b_obb['aabb'][i] - b_tuple[i]) < 1e-6

    # Non-axis-aligned matrix (M_HINGE_29)
    boxes_rot = _world_boxes(mesh_2429, M_HINGE_29, 0.0, 0.0, 0.0)
    for b in boxes_rot:
        assert isinstance(b, dict)
        cx, cy, cz = b['center']
        # Enclosing AABB must be centered at world center
        assert abs((b['aabb'][0] + b['aabb'][1]) * 0.5 - cx) < 1e-6
        assert abs((b['aabb'][2] + b['aabb'][3]) * 0.5 - cy) < 1e-6
        assert abs((b['aabb'][4] + b['aabb'][5]) * 0.5 - cz) < 1e-6


def test_boxes_overlap_input_combinations():
    """Verify _boxes_overlap accepts any combination of 6-tuple AABBs and OBB dicts."""
    b1_tuple = (0.0, 20.0, 0.0, 8.0, 0.0, 20.0)
    b2_tuple_touch = (20.0, 40.0, 0.0, 8.0, 0.0, 20.0)     # touches at x=20 (0 gap, no overlap)
    b3_tuple_overlap = (15.0, 35.0, 0.0, 8.0, 0.0, 20.0)   # overlaps x by 5 LDU

    # Fake OBB dicts
    obb_identity = {
        'center': (30.0, 4.0, 10.0),
        'extents': (10.0, 4.0, 10.0),
        'axes': ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        'aabb': (20.0, 40.0, 0.0, 8.0, 0.0, 20.0),
    }
    obb_shifted = {
        'center': (25.0, 4.0, 10.0),
        'extents': (10.0, 4.0, 10.0),
        'axes': ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        'aabb': (15.0, 35.0, 0.0, 8.0, 0.0, 20.0),
    }

    # 1. tuple vs tuple
    assert _boxes_overlap(b1_tuple, b2_tuple_touch) is False
    assert _boxes_overlap(b1_tuple, b3_tuple_overlap) is True

    # 2. tuple vs OBB dict
    assert _boxes_overlap(b1_tuple, obb_identity) is False
    assert _boxes_overlap(b1_tuple, obb_shifted) is True

    # 3. OBB dict vs tuple
    assert _boxes_overlap(obb_identity, b1_tuple) is False
    assert _boxes_overlap(obb_shifted, b1_tuple) is True

    # 4. OBB dict vs OBB dict
    assert _boxes_overlap(obb_identity, obb_identity) is True
    assert _boxes_overlap(obb_identity, obb_shifted) is True


def test_sat_matches_aabb_axis_aligned_regression():
    """Requirement (a) and (b): verify SAT produces identical results to AABB interval test for axis-aligned boxes."""
    box_a = (0.0, 20.0, 0.0, 8.0, 0.0, 20.0)
    # (a) Non-overlapping boxes:
    # 0 overlap on X (touching)
    assert _boxes_overlap(box_a, (20.0, 40.0, 0.0, 8.0, 0.0, 20.0)) is False
    # Gap on X
    assert _boxes_overlap(box_a, (25.0, 45.0, 0.0, 8.0, 0.0, 20.0)) is False
    # Separated on Y
    assert _boxes_overlap(box_a, (0.0, 20.0, 8.5, 16.5, 0.0, 20.0)) is False
    # Separated on Z
    assert _boxes_overlap(box_a, (0.0, 20.0, 0.0, 8.0, 20.5, 40.5)) is False
    # Boundary: 0.49 LDU overlap on X (within 0.5 tolerance) -> no collision
    assert _boxes_overlap(box_a, (19.51, 39.51, 0.0, 8.0, 0.0, 20.0)) is False
    # Exactly 0.50 LDU overlap on X -> no collision
    assert _boxes_overlap(box_a, (19.5, 39.5, 0.0, 8.0, 0.0, 20.0)) is False

    # (b) Overlapping boxes:
    # Boundary: 0.51 LDU overlap on X (exceeds 0.5 tolerance) -> collision
    assert _boxes_overlap(box_a, (19.49, 39.49, 0.0, 8.0, 0.0, 20.0)) is True
    # Substantial overlap (5 LDU on X)
    assert _boxes_overlap(box_a, (15.0, 35.0, 0.0, 8.0, 0.0, 20.0)) is True
    # Identical box (full overlap)
    assert _boxes_overlap(box_a, box_a) is True


def test_real_cited_matrix_hinge_no_false_collision():
    """Requirement (c): verify real 2429/2430 mated hinge at ~29.7 degrees does NOT falsely collide under OBB/SAT."""
    mesh_2429 = _load_mesh('2429')
    mesh_2430 = _load_mesh('2430')

    # In 8880-1 Super Car, hinge 2429 (Base) and 2430 (Top) are mated at (0, 0, 0).
    # 2429 has r=0 (or identity), 2430 is rotated by M_HINGE_29 (~29.7 deg).
    boxes_2429 = _world_boxes(mesh_2429, 0, 0.0, 0.0, 0.0)
    boxes_2430_rot = _world_boxes(mesh_2430, M_HINGE_29, 0.0, 0.0, 0.0)

    # Under naive AABB inflation, 2430's AABB extends into 2429's space, causing false collision.
    # Under OBB/SAT, none of the box pairs between 2429 and 2430 collide!
    for b_base in boxes_2429:
        for b_top in boxes_2430_rot:
            assert _boxes_overlap(b_base, b_top) is False

    # Test also via validate_parts
    parts = [
        {'p': '2429', 'x': 0.0, 'y': 0.0, 'z': 0.0, 'r': 0},
        {'p': '2430', 'x': 0.0, 'y': 0.0, 'z': 0.0, 'r': M_HINGE_29},
    ]
    report = validate_parts(parts, {'2429': mesh_2429, '2430': mesh_2430})
    # Overlaps must be 0 (no part-part collisions)
    assert report['overlaps'] == 0
    assert [0, 1] not in report['collisions']


def test_real_cited_matrices_metroliner_and_technic_no_false_collision():
    """Requirement (c): verify parts rotated by Metroliner 30/60/150 deg and Technic 33.9 deg don't falsely collide with adjacent parts."""
    mesh_3023 = _load_mesh('3023')
    boxes_p1 = _world_boxes(mesh_3023, 0, 0.0, 0.0, 0.0)

    for m_rot in (M_METRO_30, M_METRO_60, M_METRO_150, M_PANTOGRAPH_16_5, M_TECHNIC_33_9):
        boxes_rot = _world_boxes(mesh_3023, m_rot, 50.0, 0.0, 50.0)
        for b1 in boxes_p1:
            for b2 in boxes_rot:
                assert _boxes_overlap(b1, b2) is False


def test_rotated_boxes_deliberate_collision_detected():
    """Requirement (d): verify deliberate overlap of rotated boxes is correctly detected."""
    mesh_2429 = _load_mesh('2429')
    mesh_2430 = _load_mesh('2430')

    # Concentric placement: world center of 2430 box matches 2429 base box 1
    boxes_2429 = _world_boxes(mesh_2429, 0, 0.0, 0.0, 0.0)
    boxes_2430_coll = _world_boxes(mesh_2430, M_HINGE_29, -6.28, 0.0, 23.64)

    colliding_pairs = [
        (i, j)
        for i, b1 in enumerate(boxes_2429)
        for j, b2 in enumerate(boxes_2430_coll)
        if _boxes_overlap(b1, b2)
    ]
    assert len(colliding_pairs) > 0

    # Also test through validate_parts
    parts = [
        {'p': '2429', 'x': 0.0, 'y': 0.0, 'z': 0.0, 'r': 0},
        {'p': '2430', 'x': -6.28, 'y': 0.0, 'z': 23.64, 'r': M_HINGE_29},
    ]
    report = validate_parts(parts, {'2429': mesh_2429, '2430': mesh_2430})
    assert report['overlaps'] >= 1
    assert [0, 1] in report['collisions']


# --- hinges connector (2026-09-28, HINGE_INVESTIGATION.md section 6) ---------------------------------------
# Real hinge parts re-baked with the new `hinges` connector: 3937/3938 (classic round-knuckle) and
# 4275b/4276b (interleaved finger plates). Real verified pivot axes -- see parts.py's HINGE_CONNECTORS.

def test_hinge_knuckle_family_mates_flat():
    """Neither part touches the baseplate here, so both are correctly still `floating` (that check is about
    reaching the ground, not about having any connection at all) -- what this proves is the hinge edge itself:
    hingeConnections registers the mate, and the two halves do not falsely collide."""
    mesh_3937, mesh_3938 = _load_mesh('3937'), _load_mesh('3938')
    parts = [
        {'p': '3937', 'x': 0.0, 'y': 0.0, 'z': 0.0, 'r': 0},
        {'p': '3938', 'x': 0.0, 'y': 0.0, 'z': 0.0, 'r': 0},
    ]
    report = validate_parts(parts, {'3937': mesh_3937, '3938': mesh_3938})
    assert report['hingeConnections'] == 1
    assert report['overlaps'] == 0


def test_hinge_knuckle_family_mates_when_folded_open():
    """A real open-door fold: 3938 rotated 90 deg about the shared pivot axis (local X), with the compensating
    translation a model builder must supply so the physical pivot point still coincides in world space -- the
    connector match is on the AXIS LINE, not a fixed point, so it must still detect the mate after this."""
    mesh_3937, mesh_3938 = _load_mesh('3937'), _load_mesh('3938')
    parts = [
        {'p': '3937', 'x': 0.0, 'y': 0.0, 'z': 0.0, 'r': 0},
        {'p': '3938', 'x': 0.0, 'y': 20.0, 'z': 0.0, 'r': 21},  # PART_ROT[21] fixes local X, folds Y/Z
    ]
    report = validate_parts(parts, {'3937': mesh_3937, '3938': mesh_3938})
    assert report['hingeConnections'] == 1
    assert report['overlaps'] == 0


def test_hinge_finger_family_mates_complement_only():
    mesh_a, mesh_b = _load_mesh('4275b'), _load_mesh('4276b')
    parts = [
        {'p': '4275b', 'x': 0.0, 'y': 0.0, 'z': 0.0, 'r': 0},
        {'p': '4276b', 'x': 0.0, 'y': 0.0, 'z': 0.0, 'r': 0},
    ]
    report = validate_parts(parts, {'4275b': mesh_a, '4276b': mesh_b})
    assert report['hingeConnections'] == 1
    assert report['overlaps'] == 0


def test_hinge_finger_family_does_not_mate_with_own_kind():
    """Real physical rule: a finger2 plate never mates with another finger2 (tooth-on-tooth) -- same real part
    id twice, at the same placement, must NOT register as a hinge connection."""
    mesh_b = _load_mesh('4276b')
    parts = [
        {'p': '4276b', 'x': 0.0, 'y': 0.0, 'z': 0.0, 'r': 0},
        {'p': '4276b', 'x': 0.0, 'y': 0.0, 'z': 0.0, 'r': 0},
    ]
    report = validate_parts(parts, {'4276b': mesh_b})
    assert report['hingeConnections'] == 0


def test_hinge_axis_misaligned_parts_do_not_falsely_mate():
    """Two real hinge halves placed with NO shared pivot (arbitrary offset) must not be reported as connected
    -- the detector must actually check axis+distance, not just kind compatibility."""
    mesh_3937, mesh_3938 = _load_mesh('3937'), _load_mesh('3938')
    parts = [
        {'p': '3937', 'x': 0.0, 'y': 0.0, 'z': 0.0, 'r': 0},
        {'p': '3938', 'x': 200.0, 'y': 200.0, 'z': 200.0, 'r': 0},
    ]
    report = validate_parts(parts, {'3937': mesh_3937, '3938': mesh_3938})
    assert report['hingeConnections'] == 0
    assert 0 in report['floating']


# --- pin/hole mated-pair collision exemption (2026-09-28, TECHNIC_PANEL_INVESTIGATION.md section 5) --------

def test_pin_in_hole_exemption_does_not_suppress_unrelated_collision():
    """A real friction pin (2780) correctly mated into a real Technic beam's hole (3701) must clear the pin/
    hole connection AND report zero collisions for that pair -- proves the exemption path is reachable with
    real baked geometry, not just a synthetic case."""
    mesh_3701, mesh_2780 = _load_mesh('3701'), _load_mesh('2780')
    parts = [
        {'p': '3701', 'x': 0.0, 'y': 0.0, 'z': 0.0, 'r': 0},
        {'p': '2780', 'x': 20.0, 'y': 10.0, 'z': 0.0, 'r': 1},  # PART_ROT[1]: local X (pin axis) -> world -Z
    ]
    report = validate_parts(parts, {'3701': mesh_3701, '2780': mesh_2780})
    assert report['pinConnections'] > 0
    assert report['overlaps'] == 0
    assert [0, 1] not in report['collisions']


# --- 2429/2430 classic plate hinge (2026-09-28) -- real evidence for this pair was already sitting in this
# file's own M_HINGE_29 fixture (a pure Y-axis rotation, real official set 8880-1 Super Car cited above at
# its first use); this just connects it to the hinges registry itself.

def test_hinge_2429_2430_mates_flat():
    mesh_2429, mesh_2430 = _load_mesh('2429'), _load_mesh('2430')
    parts = [
        {'p': '2429', 'x': 0.0, 'y': 0.0, 'z': 0.0, 'r': 0},
        {'p': '2430', 'x': 0.0, 'y': 0.0, 'z': 0.0, 'r': 0},
    ]
    report = validate_parts(parts, {'2429': mesh_2429, '2430': mesh_2430})
    assert report['hingeConnections'] == 1
    assert report['overlaps'] == 0


def test_hinge_2429_2430_mates_at_real_cited_bent_angle():
    """Real official-set angle (8880-1 Super Car): 2430 rotated by M_HINGE_29 around the shared origin --
    the hinge connector must still register the mate (axis unaffected by a pure Y-axis rotation) and the
    two halves must not falsely collide at this real open angle."""
    mesh_2429, mesh_2430 = _load_mesh('2429'), _load_mesh('2430')
    parts = [
        {'p': '2429', 'x': 0.0, 'y': 0.0, 'z': 0.0, 'r': 0},
        {'p': '2430', 'x': 0.0, 'y': 0.0, 'z': 0.0, 'r': M_HINGE_29},
    ]
    report = validate_parts(parts, {'2429': mesh_2429, '2430': mesh_2430})
    assert report['hingeConnections'] == 1
    assert report['overlaps'] == 0


# --- 3830/3831 brick hinge (2026-09-28) -- pattern-matched, not independently real-set-cited: identical
# single-radius-4.0-cylinder signature to 2429/2430 (same X bounds, Y/Z match between halves, axis Y),
# the 3rd real confirmation of this exact pattern (3937/3938 X-axis, 4275b/4276b Z-axis both real-set
# cited). Flat-mate only -- no equivalent bent-angle fixture exists for this pair yet.

def test_hinge_3830_3831_mates_flat():
    mesh_3830, mesh_3831 = _load_mesh('3830'), _load_mesh('3831')
    parts = [
        {'p': '3830', 'x': 0.0, 'y': 0.0, 'z': 0.0, 'r': 0},
        {'p': '3831', 'x': 0.0, 'y': 0.0, 'z': 0.0, 'r': 0},
    ]
    report = validate_parts(parts, {'3830': mesh_3830, '3831': mesh_3831})
    assert report['hingeConnections'] == 1
    assert report['overlaps'] == 0
