"""Deterministic part checks (scripts/ldraw/part_checks.py) and the catalogue queue's pure logic
(scripts/ldraw/pipeline.py). The first test is a standing gate over every committed mesh in public/parts/: it is what
would have caught 4274's occupancy box sitting 10 LDU away from its pin."""
import copy
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "ldraw"))
import part_checks as pc  # noqa: E402
import pipeline as pl  # noqa: E402


def _cube_mesh(w=20, h=24, d=20, title="Brick  1 x  1", occ=None, studs=1):
    """A closed 12-triangle box, LDU, quantised x16, origin at the top-centre like a real brick (y down)."""
    q = 16
    x0, x1, y0, y1, z0, z1 = -w / 2, w / 2, 0, h, -d / 2, d / 2
    v = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    idx = {p: i for i, p in enumerate(v)}
    quads = [((x0, y0, z0), (x0, y1, z0), (x0, y1, z1), (x0, y0, z1)), ((x1, y0, z0), (x1, y0, z1), (x1, y1, z1), (x1, y1, z0)),
             ((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)), ((x0, y0, z1), (x0, y1, z1), (x1, y1, z1), (x1, y0, z1)),
             ((x0, y0, z0), (x0, y0, z1), (x1, y0, z1), (x1, y0, z0)), ((x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1))]
    pos = []
    for a, b, c, dd in quads:
        for tri in ((a, b, c), (a, c, dd)):
            pos += [[int(round(p[i] * q)) for i in range(3)] for p in tri]
    lo = [int(x0 * q), int(y0 * q), int(z0 * q)]
    hi = [int(x1 * q), int(y1 * q), int(z1 * q)]
    return {"id": "t", "title": title, "quant": q, "bounds": {"min": lo, "max": hi},
            "triangles": [{"colour": "main", "pos": pos}],
            "connectors": {"studs": [{"pos": [0, 0, 0], "dir": [0, -1, 0]}] * studs, "sockets": [], "holes": [], "pins": []},
            "occupancy": occ if occ is not None else [[x0, x1, y0, y1, z0, z1]]}


def test_every_committed_part_passes_the_error_level_checks():
    idx = __import__("json").loads((pl.PARTS / "index.json").read_text())["parts"]
    bad = {}
    for pid in idx:
        errs = [f for f in pc.check_id(pid)[0] if f["level"] == "error"]
        if errs:
            bad[pid] = [f["msg"] for f in errs]
    assert not bad, bad


def test_clean_synthetic_part_has_no_findings():
    f, m = pc.check_part(_cube_mesh())
    assert f == [] and m["open_edges"] == 0 and m["nonmanifold"] == 0 and m["signed_volume"] != 0


def test_occupancy_box_outside_bounds_is_an_error():
    f, _ = pc.check_part(_cube_mesh(occ=[[0, 20, 0, 24, -10, 10]]))          # shifted 10 LDU: the 4274 bug class
    assert any(x["check"] == "occupancy" and x["level"] == "error" for x in f)


def test_stale_bounds_are_an_error():
    m = _cube_mesh()
    m["bounds"]["max"][0] += 16
    assert any(x["check"] == "bounds" for x in pc.check_part(m)[0])


def test_title_footprint_mismatch_is_an_error():
    m = _cube_mesh(w=40, d=20, title="Brick  1 x  1")
    assert any(x["check"] == "footprint" for x in pc.check_part(m)[0])


def test_plain_part_stud_count_must_match_footprint():
    f, _ = pc.check_part(_cube_mesh(w=40, d=20, title="Brick  1 x  2", studs=1))
    assert any(x["check"] == "connectors" and "expected 2" in x["msg"] for x in f)


def test_open_surface_is_measured():
    m = copy.deepcopy(_cube_mesh())
    m["triangles"][0]["pos"] = m["triangles"][0]["pos"][:-6]                 # drop the bottom face
    _, met = pc.check_part(m)
    assert met["open_edges"] == 4 and met["open_frac"] > 0


def test_ray_parity_inside_test_on_a_cube():
    T, q = pc.triangles(_cube_mesh())
    ins = pc.inside_points(T.astype(float) / q, np.array([[0.0, 12.0, 0.0], [0.0, 30.0, 0.0], [15.0, 12.0, 0.0]]))
    assert list(ins) == [True, False, False]


def test_queue_results_are_keyed_to_the_mesh_hash_and_stage_version():
    rec = {"stages": {"checks": {"sha": "abc", "v": pl.VERSIONS["checks"], "findings": []}}}
    assert pl.valid(rec, "checks", "abc") and not pl.valid(rec, "checks", "different")
    rec["stages"]["checks"]["v"] = pl.VERSIONS["checks"] - 1
    assert not pl.valid(rec, "checks", "abc")
    qa = {"stages": {"qa": {"sha": "abc", "v": pl.VERSIONS["qa"], "model": "m1"}}}
    assert pl.valid(qa, "qa", "abc", "m1") and not pl.valid(qa, "qa", "abc", "m2")


def test_classification_and_hints():
    err = {"stages": {"checks": {"findings": [{"level": "error"}]}, "qa": {"verdict": "pass"}}}
    assert pl.classify(err) == "failed"
    flag = {"stages": {"checks": {"findings": []}, "qa": {"verdict": "fail", "issues": ["top stud is solid instead of hollow"]}}}
    assert pl.classify(flag) == "needs_review" and pl.hint(flag) == "render-limitation?"
    flag["stages"]["qa"]["issues"].append("clip orientation is wrong")
    assert pl.hint(flag) == "review"
    ok = {"stages": {"checks": {"findings": []}, "qa": {"verdict": "pass"}}}
    assert pl.classify(ok) == "clean" and pl.classify({}) == "pending"


@pytest.mark.parametrize("mut", ["bounds", "occupancy"])
def test_gate_is_not_vacuous_on_a_real_part(mut):
    m = pc.load("3001")
    if mut == "bounds":
        m["bounds"]["max"][0] += 16
    else:
        m["occupancy"] = [[b + 20 if i < 2 else b for i, b in enumerate(m["occupancy"][0])]]
    assert any(f["level"] == "error" for f in pc.check_part(m)[0])
