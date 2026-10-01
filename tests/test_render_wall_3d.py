"""Integration test for declaration_prealable/render_wall_3d.py -- skipped if bpy isn't installed, same
mechanism as tests/test_render_blender.py (that module's own requirements-blender.txt dependency).
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("bpy", reason="scripts/brick_models/requirements-blender.txt's own dependency, not the base repo's")

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "declaration_prealable" / "render_wall_3d.py"


def _write_project(tmp_path, **wall_kwargs):
    data = {
        "commune": "Exemple-sur-Seine", "address": "12 rue des Tilleuls",
        "wall": {
            "length_m": wall_kwargs.get("length_m", 3.0),
            "height_m": wall_kwargs.get("height_m", 1.5),
            "thickness_mm": wall_kwargs.get("thickness_mm", 200),
            "finish_label": wall_kwargs.get("finish_label", "Enduit lisse peint en blanc"),
            "finish_colour_hex": wall_kwargs.get("finish_colour_hex", "#e8e6df"),
        },
        "plot": {}, "date_iso": "2026-10-01",
    }
    path = tmp_path / "project.json"
    path.write_text(json.dumps(data))
    return path


def _load_rgb_array(path):
    from PIL import Image
    import numpy as np
    return np.asarray(Image.open(path).convert("RGB"))


def test_render_wall_3d_produces_a_real_image(tmp_path):
    project_path = _write_project(tmp_path, length_m=4.0, height_m=1.8)
    out_dir = tmp_path / "out"
    cmd = [sys.executable, str(SCRIPT), "--project", str(project_path), "--out-dir", str(out_dir),
           "--resolution", "160x120", "--samples", "8"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    assert result.returncode == 0, result.stdout + result.stderr

    out_path = out_dir / "wall_3d.png"
    assert out_path.exists()
    img = _load_rgb_array(out_path)
    assert img.shape[:2] == (120, 160)
    assert img.std() > 1.0  # not a flat/blank image


def test_build_wall_scene_box_matches_requested_dimensions():
    sys.path.insert(0, str(ROOT))
    import bpy
    from declaration_prealable import render_wall_3d as rw3d
    from declaration_prealable.project_schema import DPProject, PlotGeometry, WallSpec

    bpy.ops.wm.read_factory_settings(use_empty=True)
    wall = WallSpec(length_m=5.0, height_m=2.0, thickness_mm=200)
    project = DPProject(commune="X", address="Y", wall=wall, plot=PlotGeometry(), date_iso="2026-10-01")
    box_min, box_max = rw3d.build_wall_scene(project)

    assert box_min == (-2.5, 0.0, -0.1)
    assert box_max == (2.5, 2.0, 0.1)

    # The actual bpy object's real-world dimensions must match the box this function reports --
    # this is the exact regression test for the primitive_cube_add(size=1) half-extent bug found
    # live (the mesh was previously HALF the size fit_camera was told to frame for).
    wall_obj = bpy.data.objects["wall"]
    dims = wall_obj.dimensions
    assert abs(dims.x - 5.0) < 1e-6
    assert abs(dims.y - 2.0) < 1e-6
    assert abs(dims.z - 0.2) < 1e-6
