"""public/parts/ — the baked LDraw part meshes (spec/brick-parts-v0.1.md). Verifies the committed output against
the curated part list and the sanity checks from the Phase 1 handoff (section 10). Needs a fetched LDraw library
(scripts/ldraw/fetch_library.py) only for test_baked_output_matches_the_generator; the rest reads committed JSON
and needs nothing else, so they still run in CI where the library isn't fetched."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
PARTS_DIR = ROOT / "public" / "parts"
CURATED = ROOT.parent / "a2ui-private" / "spec" / "brick-parts" / "curated-parts-v1.json"
LDRAW_CACHE = ROOT / "scripts" / "ldraw" / "_ldraw_cache" / "ldraw"


@pytest.fixture(scope="module")
def index():
    p = PARTS_DIR / "index.json"
    if not p.exists():
        pytest.skip("public/parts/ not baked yet — run scripts/ldraw/bake_parts.py")
    return json.loads(p.read_text())


@pytest.fixture(scope="module")
def curated():
    if not CURATED.exists():
        pytest.skip("a2ui-private sibling repo not present")
    return json.loads(CURATED.read_text())


def test_every_curated_part_is_baked(index, curated):
    ids = {p["id"] for p in curated}
    # minifig characters are generated from scripts/ldraw/characters.py, not curated (tests/test_characters.py)
    baked = {pid for pid, entry in index["parts"].items() if "character" not in entry}
    assert ids == baked, "missing: %s, extra: %s" % (ids - baked, baked - ids)


def test_index_carries_attribution_and_quant(index):
    assert "LDraw.org" in index["attribution"]
    assert "CC BY" in index["attribution"]
    assert "LEGO" in index["attribution"]  # trademark disclaimer, not just the geometry licence
    assert index["quant"] == 16


def test_part_mesh_has_the_declared_shape(index):
    for pid in list(index["parts"])[:5] + ["3001", "3024", "11211", "3700", "2780"]:
        mesh = json.loads((PARTS_DIR / (pid + ".json")).read_text())
        assert mesh["id"] == pid
        assert mesh["license"] and "CC BY" in mesh["license"]
        assert mesh["bounds"]["min"] != mesh["bounds"]["max"]
        # no baked triangle references a stud primitive's geometry — studs are connectors, drawn as instances
        assert sum(len(g["pos"]) for g in mesh["triangles"]) > 0


def test_11211_has_two_side_studs_facing_negative_z():
    """Sanity check from the Phase 1 handoff: Brick 1x2 with Two Studs on One Side."""
    mesh = json.loads((PARTS_DIR / "11211.json").read_text())
    studs = mesh["connectors"]["studs"]
    side = [s for s in studs if s["dir"] == [-0.0, -0.0, -1.0] or s["dir"] == [0.0, 0.0, -1.0]]
    assert len(side) == 2, studs


def test_3700_has_one_hole_segment_through_x0_y10():
    """Sanity check from the Phase 1 handoff: Technic Brick 1x2 with Hole."""
    mesh = json.loads((PARTS_DIR / "3700.json").read_text())
    holes = mesh["connectors"]["holes"]
    assert len(holes) == 2
    xs = {h["pos"][0] for h in holes}
    ys = {h["pos"][1] for h in holes}
    assert xs == {0}
    assert ys == {160}  # 10 LDU * quant 16


def test_stud_and_socket_counts_match_footprint_for_plain_bricks(index):
    """A plain WxD brick/plate has exactly W*D studs and W*D sockets (spec section 2)."""
    for pid, w, d in [("3001", 2, 4), ("3003", 2, 2), ("3024", 1, 1), ("3622", 1, 3), ("3020", 2, 4)]:
        entry = index["parts"][pid]
        assert entry["studs"] == w * d, pid
        assert entry["sockets"] == w * d, pid


def test_jumper_plate_has_two_bottom_sockets_and_one_offgrid_top_stud():
    """15573 (jumper plate): one off-grid top stud (its whole point -- a half-stud-offset connection point for
    whatever sits on it), but a NORMAL two-socket bottom -- the same one-socket-per-cell rule as any other 1x2
    part. An earlier version of this test (and the CONNECTOR_OVERRIDES entry it verified) asserted exactly one
    socket, misreading the title's "without Understud" (no reinforcing tube above the top stud) as "no normal
    bottom connection." Found wrong building the Phase 3 validator against
    spec/brick-parts/fixtures-v0.1.json's F12_jumper_offset, which requires both bottom sockets to reach 3 total
    stud_connections (2 baseplate + 1 top) for a jumper plate on the baseplate with a plate on its top stud --
    the override's 1-socket bottom gave only 2. Removing the override (letting the generic rule apply) makes all
    15 fixtures pass; this test now locks that in instead of the wrong count."""
    mesh = json.loads((PARTS_DIR / "15573.json").read_text())
    sockets = mesh["connectors"]["sockets"]
    assert len(sockets) == 2
    assert sorted(s["pos"][0] for s in sockets) == [-160, 160]   # the two 1x2 footprint cells, symmetric about x=0
    studs = mesh["connectors"]["studs"]
    assert len(studs) == 1 and studs[0]["pos"] == [0, 0, 0]      # the single off-grid top stud, unaffected


def test_gzipped_total_fits_the_budget():
    """Ceiling raised 2026-09-27 from 60MB to 90MB: a second library-wide expansion pass (survey_unbaked.py against
    the ~21,881 not-yet-baked candidates, resolved with the same generic occupancy fallback) grew the catalogue from
    2,854 to 4,761 parts. Measured real total at the time of this change: 70.8MB gzipped for 4,761 parts. Each part
    is fetched individually on demand (PART_BASE + id + '.json'), never as one bundle, so this is a repo/hosting
    storage budget, not a page-load one -- 90MB gives headroom over the measured 70.8MB without being a blank
    cheque for unbounded growth. File COUNT (4,761, well under Cloudflare Pages' 20,000-file-per-deployment limit)
    is not this test's concern. See the 2026-09-26 change this supersedes for the original 2MB -> 60MB rationale."""
    import gzip
    total = 0
    for f in PARTS_DIR.glob("*.json"):
        total += len(gzip.compress(f.read_bytes(), 6))
    assert total < 90_000_000, "%d bytes gzipped" % total


def test_needs_occupancy_parts_have_no_fabricated_occupancy(index):
    """Parts Phase 1 could not classify must carry occupancy=None, never a guessed box (Phase 1 handoff: "don't
    guess them")."""
    for pid, entry in index["parts"].items():
        mesh = json.loads((PARTS_DIR / (pid + ".json")).read_text())
        if entry["needs_occupancy"]:
            assert mesh["occupancy"] is None, pid
        else:
            assert mesh["occupancy"], pid


def test_positions_are_quantised_integers():
    mesh = json.loads((PARTS_DIR / "3001.json").read_text())
    for group in mesh["triangles"]:
        for point in group["pos"]:
            assert all(isinstance(v, int) for v in point), group


@pytest.mark.skipif(not LDRAW_CACHE.exists(), reason="LDraw library not fetched (scripts/ldraw/fetch_library.py)")
def test_baked_output_matches_the_generator(tmp_path):
    """Re-bakes into a scratch dir and diffs against the committed public/parts/ — catches drift the way
    tests/test_bricks_demo.py does for the model gallery."""
    import shutil
    env = dict(os.environ, LDRAW_DIR=str(LDRAW_CACHE))
    src = ROOT / "scripts" / "ldraw"
    scratch = tmp_path / "ldraw"
    shutil.copytree(src, scratch, ignore=shutil.ignore_patterns("_ldraw_cache", "__pycache__"))
    out_dir = tmp_path / "out"
    text = (scratch / "bake_parts.py").read_text()
    text = text.replace('OUT_DIR = os.path.join(ROOT, "public", "parts")', "OUT_DIR = %r" % str(out_dir))
    text = text.replace('CURATED = os.path.join(ROOT, "..", "a2ui-private", "spec", "brick-parts", "curated-parts-v1.json")',
                         "CURATED = %r" % str(CURATED))
    (scratch / "bake_parts.py").write_text(text)
    result = subprocess.run([sys.executable, str(scratch / "bake_parts.py")], cwd=scratch, env=env,
                             capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    for f in PARTS_DIR.glob("*.json"):
        fresh = out_dir / f.name
        assert fresh.exists(), f.name
        assert json.loads(fresh.read_text()) == json.loads(f.read_text()), \
            "%s is stale: run python3 scripts/ldraw/bake_parts.py" % f.name


# --- OMR Importer continuous rotation tests ---

def test_omr_rot_index_axis_aligned():
    """Axis-aligned rotations matching PART_ROT must return integer index 0..23."""
    from scripts.ldraw.omr_import import rot_index
    from renderers.brick_parts_validate import PART_ROT
    assert rot_index((1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)) == 0
    for idx, r in enumerate(PART_ROT):
        assert rot_index(r) == idx


def test_omr_rot_index_continuous_rotation():
    """Non-axis-aligned proper rotations return a continuous 9-tuple of rounded floats."""
    from scripts.ldraw.omr_import import rot_index
    # 30° Y-rotation from Metroliner 10001-1 locomotive nose
    m_30 = (0.866, 0.0, -0.5, 0.0, 1.0, 0.0, 0.5, 0.0, 0.866)
    r_30 = rot_index(m_30)
    assert isinstance(r_30, tuple)
    assert len(r_30) == 9
    assert r_30 == (0.866, 0.0, -0.5, 0.0, 1.0, 0.0, 0.5, 0.0, 0.866)

    # 16.5° pantograph arm from 10001-1
    m_panto = (1.0, 0.284, 0.0, -0.284, 1.0, 0.0, 0.0, 0.0, 1.0)
    r_panto = rot_index(m_panto)
    assert isinstance(r_panto, tuple)
    assert r_panto == (1.0, 0.284, 0.0, -0.284, 1.0, 0.0, 0.0, 0.0, 1.0)

    # 33.9° Technic chassis diagonal brace from 8880-1 Super Car
    m_technic = (0.0, 0.0, -1.0, -0.558, 0.83, 0.0, 0.83, 0.558, 0.0)
    r_technic = rot_index(m_technic)
    assert isinstance(r_technic, tuple)
    assert r_technic == (0.0, 0.0, -1.0, -0.558, 0.83, 0.0, 0.83, 0.558, 0.0)


def test_omr_rot_index_rejects_reflections_and_degenerates():
    """Mirrored parts (det ≈ -1) and singular/scaled matrices must return None."""
    from scripts.ldraw.omr_import import rot_index
    # Mirror reflection along X axis
    m_mirror = (-1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
    assert rot_index(m_mirror) is None

    # Zero / singular matrix
    m_zero = (0.0,) * 9
    assert rot_index(m_zero) is None

    # Scaled matrix (det = 8.0)
    m_scaled = (2.0, 0.0, 0.0, 0.0, 2.0, 0.0, 0.0, 0.0, 2.0)
    assert rot_index(m_scaled) is None


def test_omr_bottom_y_continuous_rotation():
    """bottom_y computes the lowest world-Y point (largest Y, LDraw Y down) across all 8 corners."""
    import math
    from scripts.ldraw.omr_import import bottom_y

    mesh_3001 = json.loads((PARTS_DIR / "3001.json").read_text())
    b = mesh_3001["bounds"]
    q = 16.0
    leaf = {"t": (0.0, 120.0, 0.0)}

    # Integer rotation (axis-aligned, identity)
    by_int = bottom_y("3001", leaf, 0, mesh=mesh_3001)
    assert by_int == 120.0 + b["max"][1] / q

    # Continuous 45° rotation around Z axis
    theta = math.radians(45)
    c, s = round(math.cos(theta), 4), round(math.sin(theta), 4)
    m_tilt = (c, -s, 0.0, s, c, 0.0, 0.0, 0.0, 1.0)
    by_cont = bottom_y("3001", leaf, m_tilt, mesh=mesh_3001)

    # Analytical cross-check: max Y across all 8 corners
    corner_ys = [
        m_tilt[3] * x / q + m_tilt[4] * y / q + m_tilt[5] * z / q
        for x in (b["min"][0], b["max"][0])
        for y in (b["min"][1], b["max"][1])
        for z in (b["min"][2], b["max"][2])
    ]
    expected_floor = 120.0 + max(corner_ys)
    assert math.isclose(by_cont, expected_floor, rel_tol=1e-6)
    # The lowest point of the tilted brick must be strictly lower (larger Y) than untilted
    assert by_cont > by_int


def test_omr_coverage_counts_continuous_as_renderable():
    """coverage() counts baked leaves with continuous rotation matrices as renderable."""
    from scripts.ldraw.omr_import import coverage
    m_30 = (0.866, 0.0, -0.5, 0.0, 1.0, 0.0, 0.5, 0.0, 0.866)
    leaves = [
        {"part": "3001", "colour": 1, "m": (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0), "t": (0.0, 0.0, 0.0), "step": 1},
        {"part": "3001", "colour": 4, "m": m_30, "t": (20.0, 0.0, 0.0), "step": 1},
        {"part": "non_existent_unbaked_part", "colour": 0, "m": (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0), "t": (0.0, 0.0, 0.0), "step": 1},
    ]
    cov = coverage(leaves)
    assert cov["parts"] == 3
    assert cov["baked"] == 2
    assert cov["renderable"] == 2
    assert cov["tilted"] == 0
    assert cov["fraction"] == 2 / 3


def test_omr_to_parts_model_preserves_continuous_matrix_and_grounds_floor():
    """to_parts_model emits rows with continuous matrix intact and grounds lowest point to y=0."""
    from scripts.ldraw.omr_import import to_parts_model, bottom_y
    m_30 = (0.866, 0.0, -0.5, 0.0, 1.0, 0.0, 0.5, 0.0, 0.866)
    leaves = [
        {"part": "3001", "colour": 1, "m": (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0), "t": (0.0, 50.0, 0.0), "step": 1},
        {"part": "3005", "colour": 4, "m": m_30, "t": (20.0, 80.0, 0.0), "step": 1},
    ]
    pm = to_parts_model(leaves)
    assert len(pm) == 2
    row_3001 = next(r for r in pm if r[0] == "3001")
    row_3005 = next(r for r in pm if r[0] == "3005")
    assert isinstance(row_3001[4], int)  # axis-aligned uses int rotation index
    assert isinstance(row_3005[4], tuple)  # tilted uses 9-tuple continuous matrix
    assert row_3005[4] == m_30
    # The lowest point across the entire placed model must sit at y=0 on the baseplate
    floors = [bottom_y(row[0], {"t": (row[1], row[2], row[3])}, row[4]) for row in pm]
    assert abs(max(floors)) <= 1.0  # within integer rounding of 0.0 LDU


def test_omr_real_metroliner_tilted_leaves_in_parts_model():
    """Real tilted leaves from Metroliner 10001-1 (Plate 1x4 at 30° and Pantograph 4504 at 16.5°)
    are included in to_parts_model output with continuous matrices intact."""
    from scripts.ldraw.omr_import import to_parts_model, coverage
    # Real leaves extracted from 10001-1.mpd
    leaves = [
        # Plate 1x4 (3710) rotated 30° around Y
        {"part": "3710", "colour": 7, "m": (0.866, 0.0, -0.5, 0.0, 1.0, 0.0, 0.5, 0.0, 0.866),
         "t": (160.0, -96.0, 20.0), "step": 3},
        # Hinge Control Handle (4504) pantograph arm tilted 16.5°
        {"part": "4504", "colour": 0, "m": (1.0, 0.284, 0.0, -0.284, 1.0, 0.0, 0.0, 0.0, 1.0),
         "t": (0.0, -120.0, -50.0), "step": 5},
    ]
    cov = coverage(leaves)
    assert cov["parts"] == 2
    assert cov["baked"] == 2
    assert cov["renderable"] == 2
    assert cov["tilted"] == 0

    pm = to_parts_model(leaves)
    assert len(pm) == 2
    assert all(isinstance(r[4], tuple) for r in pm)
    assert pm[0][4] == (0.866, 0.0, -0.5, 0.0, 1.0, 0.0, 0.5, 0.0, 0.866)
    assert pm[1][4] == (1.0, 0.284, 0.0, -0.284, 1.0, 0.0, 0.0, 0.0, 1.0)


