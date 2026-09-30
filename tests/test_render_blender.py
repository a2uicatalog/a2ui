"""Integration test for scripts/brick_models/render_blender.py -- skipped if bpy isn't installed (it's an
optional, heavy dependency, see scripts/brick_models/requirements-blender.txt, deliberately not part of the
base repo's requirements.txt/CI). Install it to run this locally:
    .venv/bin/pip install -r scripts/brick_models/requirements-blender.txt
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("bpy", reason="scripts/brick_models/requirements-blender.txt's own dependency, not the base repo's")
pytest.importorskip("imageio_ffmpeg", reason="scripts/brick_models/requirements-blender.txt's own dependency, not the base repo's")

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "brick_models" / "render_blender.py"
PARTS_DIR = ROOT / "public" / "parts"
COLOURS = ROOT / "public" / "bricksdemo" / "ldraw_colours_full.json"


def _write_bom(tmp_path, rows):
    # Same small-fixture spirit as tests/fixtures/bricks/parts_fixtures-v0.1.json's F01_single_brick (a
    # single 2x4 brick on the baseplate) -- that fixture's own rows omit colour (c), needed here for
    # rendering, so these are new minimal rows rather than a literal reuse of that fixture's array.
    path = tmp_path / "bom.json"
    path.write_text(json.dumps({"partsModel": rows}))
    return path


def _run_render(bom_path, out_dir, *, direction=None, no_video=False, resolution="160x120",
                 still_samples=8):
    cmd = [
        sys.executable, str(SCRIPT),
        "--parts-model", str(bom_path),
        "--parts-dir", str(PARTS_DIR),
        "--colours", str(COLOURS),
        "--out-dir", str(out_dir),
        "--resolution", resolution,
        "--frames", "6", "--fps", "6",
        "--still-samples", str(still_samples), "--turntable-samples", "4",
    ]
    if direction:
        cmd += ["--direction", direction]
    if no_video:
        cmd.append("--no-video")
    return subprocess.run(cmd, capture_output=True, text=True, timeout=180)


def _load_rgb_array(path):
    from PIL import Image
    import numpy as np
    return np.asarray(Image.open(path).convert("RGB"))


def test_render_still_and_video(tmp_path):
    bom_path = _write_bom(tmp_path, [["3001", 20, -24, 20, 0, 4]])
    out_dir = tmp_path / "out"
    result = _run_render(bom_path, out_dir)
    assert result.returncode == 0, result.stdout + result.stderr

    still = out_dir / "hero.png"
    assert still.exists()
    img = _load_rgb_array(still)
    assert img.shape[:2] == (120, 160)  # numpy array is (height, width, channels)
    assert img.std() > 1.0  # a truly blank/solid-colour image has zero std deviation

    video = out_dir / "turntable.mp4"
    assert video.exists()
    assert video.stat().st_size > 0
    assert not (out_dir / "_frames").exists()  # intermediate frame sequence cleaned up after encoding


def test_render_still_only(tmp_path):
    bom_path = _write_bom(tmp_path, [["3001", 20, -24, 20, 0, 4]])
    out_dir = tmp_path / "out"
    result = _run_render(bom_path, out_dir, no_video=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert (out_dir / "hero.png").exists()
    assert not (out_dir / "turntable.mp4").exists()


def test_render_two_colours_of_same_part_stay_distinct(tmp_path):
    # Regression test for a real bug found 2026-09-30 while building a demo scene: Blender's
    # obj.data.materials is a MESH-DATA property, shared by every object using that mesh datablock.
    # build_scene deliberately shares one mesh datablock across every instance of the same part id (for the
    # same memory-reuse reason build_design_page.py's InstancedMesh buckets share geometry) -- naively
    # appending to obj.data.materials meant the LAST-processed instance's colour silently overwrote every
    # OTHER instance of that same part id sharing the mesh. Confirmed live: a yellow (14) and a green (2)
    # instance of the same part (3003) both rendered green. Fixed via Blender's real per-instance override
    # mechanism (material_slots[i].link='OBJECT'). This test renders exactly that scenario and checks BOTH
    # colours are actually present, not just "renders fine" (which the bug also did -- it rendered without
    # error, just with the wrong colour).
    bom_path = _write_bom(tmp_path, [
        ["3003", -150, -24, 0, 0, 14],  # yellow
        ["3003", 150, -24, 0, 0, 2],    # green
    ])
    out_dir = tmp_path / "out"
    result = _run_render(bom_path, out_dir, no_video=True, resolution="400x300", still_samples=32)
    assert result.returncode == 0, result.stdout + result.stderr

    img = _load_rgb_array(out_dir / "hero.png").astype(int)
    r, g, b = img[..., 0], img[..., 1], img[..., 2]
    # Yellow (#fac80a): R and G both clearly above B, R roughly >= G. Green (#00852b): G clearly above both
    # R and B. Thresholds calibrated against a real render of this exact scene, 2026-09-30 (not guessed).
    yellowish = (r > 120) & (g > 100) & (r > b + 40) & (g > b + 30)
    greenish = (g > 100) & (g > r + 50) & (g > b + 20)
    assert yellowish.sum() > 20, f"expected yellow-ish pixels somewhere in frame, found {yellowish.sum()}"
    assert greenish.sum() > 20, f"expected green-ish pixels somewhere in frame, found {greenish.sum()}"


def test_render_printed_part_decal_visible(tmp_path):
    # Regression test for the real decal-z-fighting bug found 2026-09-30 (see render_blender.py's own
    # top-of-file comment): renders the SAME real printed part (4744p0m) the empirical winding/decal-offset
    # verification used, and asserts the render shows real colour variation specifically from the print's own
    # white dots, not just a lighting gradient on the base red -- a plain non-blank check alone wouldn't
    # catch "renders fine but the decal itself silently vanished again".
    bom_path = _write_bom(tmp_path, [["4744p0m", 0, -24, 0, 0, 4]])
    out_dir = tmp_path / "out"
    result = _run_render(bom_path, out_dir, direction="0.5,0.8,-1", no_video=True,
                          resolution="200x150", still_samples=16)
    assert result.returncode == 0, result.stdout + result.stderr

    img = _load_rgb_array(out_dir / "hero.png")
    # Cycles' default view transform compresses highlights -- a pure-white (1,1,1) material under this
    # scene's moderate studio lighting renders around ~170-180, NOT near raw 255, confirmed by direct
    # inspection of a real render (public/parts/4744p0m.json's own white-dot print, 2026-09-30). So this
    # checks for "brighter AND more neutral (R/G/B close together) than the saturated red base", the real
    # signature of the white print against the red brick, rather than an absolute brightness threshold that
    # assumed unrealistic exposure.
    brightness = img.mean(axis=2)
    neutrality = img.max(axis=2).astype(int) - img.min(axis=2).astype(int)  # low = grey/white, high = saturated colour
    white_dot_pixels = (brightness > 120) & (neutrality < 25)
    assert white_dot_pixels.sum() > 20, \
        f"expected a cluster of bright, colour-neutral (white dot) pixels; found {white_dot_pixels.sum()}"
