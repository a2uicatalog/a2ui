"""Locks in scripts/brick_models/blender_view_math.py's rotation/placement/camera-fit math directly, mirroring
scripts/test_threejs_view_math.mjs's own hand-computed-assertion style (not "didn't throw") for the JS twin
this module ports. No bpy import anywhere in this file or the module it tests -- runs in the plain
`pytest tests/ -q` suite with zero new runtime dependency.
"""
import json
import math
from pathlib import Path

import pytest

from scripts.brick_models import blender_view_math as bvm

ROOT = Path(__file__).resolve().parent.parent


def close(a, b, eps=1e-9):
    return abs(a - b) <= eps


def close_vec(a, b, eps=1e-9):
    return len(a) == len(b) and all(close(x, y, eps) for x, y in zip(a, b))


def test_rot_identity_leaves_point_unchanged():
    # twin of test_threejs_view_math.mjs's "tjsRot index 0 (identity) leaves a point unchanged"
    assert close_vec(bvm.rot(0, (3, -2, 7)), (3, -2, 7))


def test_rot_index_1_matches_hand_computed():
    # twin of "tjsRot index 1 matches its own matrix, hand-computed"
    assert close_vec(bvm.rot(1, (1, 0, 0)), (0, 0, -1))


def test_to_world_ldraw_y_down_becomes_y_up():
    # twin of "tjsToWorld: LDraw Y-down floored offset becomes three.js Y-up correctly"
    out = bvm.to_world((16, 0, 0), 16, 0, (0, -24, 0))
    assert close_vec(out, (0.05, 1.2, 0), 1e-6)


def test_fit_camera_target_is_box_centre():
    fit = bvm.fit_camera((-1, -1, -1), (1, 1, 1), (0, 0, 1), 90, 1, 1.15)
    assert close_vec(fit["target"], (0, 0, 0))


def test_fit_camera_distance_matches_hand_computed():
    # margin * halfExtent / tan(45deg) = 1.15 * 1 / 1
    fit = bvm.fit_camera((-1, -1, -1), (1, 1, 1), (0, 0, 1), 90, 1, 1.15)
    assert close(fit["distance"], 1.15, 1e-9)


def test_fit_camera_position_along_dir():
    fit = bvm.fit_camera((-1, -1, -1), (1, 1, 1), (0, 0, 1), 90, 1, 1.15)
    assert close_vec(fit["position"], (0, 0, 1.15), 1e-9)


def test_fit_camera_near_far_bracket_object():
    fit = bvm.fit_camera((-1, -1, -1), (1, 1, 1), (0, 0, 1), 90, 1, 1.15)
    assert fit["near"] < fit["distance"] - 1
    assert fit["far"] > fit["distance"] + 1


def test_fit_camera_wide_box_needs_more_distance_than_square():
    # the real bug tjsFitCamera was written to fix: a scalar heuristic gave the same, too-small distance
    # regardless of the box's actual proportions
    wide = bvm.fit_camera((-5, -1, -1), (5, 1, 1), (0, 0, 1), 90, 1, 1.15)
    square = bvm.fit_camera((-1, -1, -1), (1, 1, 1), (0, 0, 1), 90, 1, 1.15)
    assert wide["distance"] > square["distance"]


def test_fit_camera_ortho_half_extents_cube():
    # FOV/aspect-independent -- the 2x2x2 cube (half-extent 1 on every axis) reports margin*1 on both axes
    # regardless of the 90-degree FOV the perspective checks above used
    fit = bvm.fit_camera((-1, -1, -1), (1, 1, 1), (0, 0, 1), 90, 1, 1.15)
    assert close(fit["ortho"]["half_w"], 1.15, 1e-9)
    assert close(fit["ortho"]["half_h"], 1.15, 1e-9)


def test_fit_camera_ortho_half_extents_track_non_square_box():
    wide = bvm.fit_camera((-5, -1, -1), (5, 1, 1), (0, 0, 1), 90, 1, 1.15)
    assert close(wide["ortho"]["half_w"], 5.75, 1e-9)
    assert close(wide["ortho"]["half_h"], 1.15, 1e-9)


def test_part_rot_has_24_entries():
    assert len(bvm.PART_ROT) == 24


def test_every_part_rot_is_proper_rotation():
    def det3(m):
        return (m[0] * (m[4] * m[8] - m[5] * m[7])
                - m[1] * (m[3] * m[8] - m[5] * m[6])
                + m[2] * (m[3] * m[7] - m[4] * m[6]))
    bad = [m for m in bvm.PART_ROT if not close(det3(m), 1, 1e-9)]
    assert not bad, bad


def _apply_matrix_row_major(els, p):
    return (
        els[0][0] * p[0] + els[0][1] * p[1] + els[0][2] * p[2] + els[0][3],
        els[1][0] * p[0] + els[1][1] * p[1] + els[1][2] * p[2] + els[1][3],
        els[2][0] * p[0] + els[2][1] * p[1] + els[2][2] * p[2] + els[2][3],
    )


def _apply_d(p):
    return (p[0] / 20, -p[1] / 20, p[2] / 20)


INSTANCE_CASES = [
    # same 5 numeric cases test_threejs_view_math.mjs hard-codes -- if both ports agree on the same inputs,
    # both are correct constructions on top of the same PART_ROT/to_world design, independent of whether
    # Blender itself runs for this class of test
    {"r": 0, "inst_pos": (0, -24, 0), "q": 16, "p": (16, 0, 0)},
    {"r": 1, "inst_pos": (40, -24, -40), "q": 16, "p": (8, -12, 4)},
    {"r": 5, "inst_pos": (-80, 0, 120), "q": 20, "p": (-3, 7, 11)},
    {"r": 13, "inst_pos": (0, 0, 0), "q": 1, "p": (1, 2, 3)},
    {"r": 23, "inst_pos": (200, -48, -200), "q": 8, "p": (-5, 0, 17)},
]


@pytest.mark.parametrize("case", INSTANCE_CASES, ids=lambda c: f"r={c['r']}")
def test_instance_matrix_composed_with_d_matches_to_world(case):
    via_matrix = _apply_d(_apply_matrix_row_major(
        bvm.instance_matrix(case["r"], case["inst_pos"], case["q"]), case["p"]))
    via_to_world = bvm.to_world(case["p"], case["q"], case["r"], case["inst_pos"])
    assert close_vec(via_matrix, via_to_world, 1e-9), (via_matrix, via_to_world)


def test_part_rot_matches_fixture_rotations():
    # parity check against this repo's own canonical fixture -- catches drift against the real, existing
    # fixture, not just against the JS test file's own hard-coded expectations
    fixture = json.loads((ROOT / "tests/fixtures/bricks/parts_fixtures-v0.1.json").read_text())
    fixture_rotations = fixture["rotations"]
    assert len(fixture_rotations) == len(bvm.PART_ROT)
    for i, (fixture_m, ours_m) in enumerate(zip(fixture_rotations, bvm.PART_ROT)):
        flat = tuple(v for row in fixture_m for v in row)
        assert close_vec(flat, ours_m), f"rotation index {i}: fixture={flat} ours={ours_m}"


def test_material_params_default():
    params = bvm.material_params_for_code(0, {"0": {"hex": "#1b2a34", "finish": None, "alpha": 255}})
    assert params["base_color_hex"] == "#1b2a34"
    assert close(params["metallic"], 0.05)
    assert close(params["roughness"], 0.85)
    assert "transmission_weight" not in params


def test_material_params_chrome():
    params = bvm.material_params_for_code(383, {"383": {"hex": "#aeafb0", "finish": "chrome", "alpha": 255}})
    assert close(params["metallic"], 1.0)
    assert close(params["coat_weight"], 1.0)


def test_material_params_trans():
    params = bvm.material_params_for_code(47, {"47": {"hex": "#fcfcfc", "finish": None, "alpha": 200}})
    assert close(params["transmission_weight"], 1.0)
    assert close(params["ior"], 1.5)


def test_material_params_missing_code_falls_back_to_default():
    params = bvm.material_params_for_code(9999, {})
    assert params["base_color_hex"] == "#c91a09"
    assert close(params["roughness"], 0.85)


def test_generated_part_rot_block_matches_a_fresh_run():
    # Drift gate for the 5th rotation-table twin (see gen_part_rot_table.py's own comment): an edit to
    # renderers/brick_parts_validate.py's PART_ROT that isn't followed by re-running the generator must fail
    # here, rather than silently becoming a hand-kept copy that can diverge unnoticed.
    import subprocess
    import sys
    module_path = ROOT / "scripts" / "brick_models" / "blender_view_math.py"
    before = module_path.read_text(encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "brick_models" / "gen_part_rot_table.py")],
        cwd=ROOT, capture_output=True, text=True,
    )
    after = module_path.read_text(encoding="utf-8")
    assert result.returncode == 0, result.stderr
    assert after == before, "blender_view_math.py's PART_ROT is stale -- run gen_part_rot_table.py and commit the result"
