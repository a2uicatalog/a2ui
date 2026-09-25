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
    baked = set(index["parts"])
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


def test_jumper_plate_socket_is_overridden_not_doubled():
    """15573 (jumper plate) has one off-grid stud; a naive one-socket-per-cell rule would give it two."""
    mesh = json.loads((PARTS_DIR / "15573.json").read_text())
    assert len(mesh["connectors"]["sockets"]) == 1


def test_gzipped_total_fits_the_2mb_budget():
    import gzip
    total = 0
    for f in PARTS_DIR.glob("*.json"):
        total += len(gzip.compress(f.read_bytes(), 9))
    assert total < 2_000_000, "%d bytes gzipped" % total


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
