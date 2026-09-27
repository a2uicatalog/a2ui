"""Minifig character templates (scripts/ldraw/characters.py), baked by bake_parts.py into public/parts/mf-<id>.json
and picked from the Brick Design Lab. Reads the committed bake; the template-to-library check needs the fetched
LDraw library and is skipped without it, like tests/test_ldraw_parts.py."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
PARTS_DIR = ROOT / "public" / "parts"
LDRAW_CACHE = ROOT / "scripts" / "ldraw" / "_ldraw_cache" / "ldraw"
sys.path.insert(0, str(ROOT / "scripts" / "ldraw"))

import characters as ch  # noqa: E402


@pytest.fixture(scope="module")
def index():
    p = PARTS_DIR / "index.json"
    if not p.exists():
        pytest.skip("public/parts/ not baked yet -- run scripts/ldraw/bake_parts.py")
    return json.loads(p.read_text())["parts"]


def test_template_ids_are_unique_and_part_id_safe():
    ids = [ch.character_id(t) for t in ch.TEMPLATES]
    assert len(ids) == len(set(ids))
    for pid in ids:   # the Design Lab page and the Worker accept part ids matching /^[0-9a-z-]{1,24}$/
        assert pid.startswith("mf-") and len(pid) <= 24 and all(c.isdigit() or c.islower() or c == "-" for c in pid), pid


def test_every_template_fills_the_body_slots():
    for t in ch.TEMPLATES:
        slots = ch.template_slots(t)
        for slot in ("torso", "hips", "leg_r", "leg_l", "arm_r", "arm_l", "hand_r", "hand_l", "head"):
            assert slot in slots, (t["id"], slot)
        assert set(slots) <= set(ch.OFFSETS), t["id"]


def test_generated_model_turns_the_figure_to_face_plus_z():
    lines = [l for l in ch.template_dat(ch.TEMPLATES[0]).splitlines() if l.startswith("1 ")]
    torso = lines[0].split()
    assert torso[2:5] == ["0", "0", "0"] and torso[5:14] == ["-1", "0", "0", "0", "1", "0", "0", "0", "-1"]
    assert all("-0 " not in l for l in lines)
    # the right arm (3818) sits on the +x side once the figure faces +Z
    arm_r = next(l.split() for l in lines if l.endswith(" 3818.dat"))
    assert float(arm_r[2]) > 0


@pytest.mark.skipif(not LDRAW_CACHE.exists(), reason="LDraw library not fetched (scripts/ldraw/fetch_library.py)")
def test_every_template_part_exists_in_the_library():
    for t in ch.TEMPLATES:
        for slot, (part, colour) in ch.template_slots(t).items():
            assert (LDRAW_CACHE / "parts" / (part + ".dat")).exists(), (t["id"], slot, part)
            assert isinstance(colour, int), (t["id"], slot)


def test_search_matches_every_word_across_name_id_and_tags():
    names = lambda q: [t["name"] for t in ch.search(q)]  # noqa: E731
    assert names("space") == ["Classic space astronaut"]
    assert names("") == [t["name"] for t in ch.TEMPLATES]
    assert names("dragon") == []
    assert set(names("castle knight")) == {"Castle knight", "Lion knight"}   # AND across words, any field
    assert set(names("CASTLE Knight")) == {"Castle knight", "Lion knight"}   # case-insensitive


def test_every_template_is_baked_with_character_metadata(index):
    for t in ch.TEMPLATES:
        pid = ch.character_id(t)
        assert pid in index, pid
        assert index[pid]["character"] == {"name": t["name"], "tags": t["tags"]}
        assert index[pid]["needs_occupancy"] is False


def test_baked_character_stands_on_a_1x2_stud_pair(index):
    for pid in (p for p in index if p.startswith("mf-")):
        mesh = json.loads((PARTS_DIR / (pid + ".json")).read_text())
        q = mesh["quant"]
        assert mesh["bounds"]["max"][1] == ch.FEET_Y * q, pid                     # feet exactly at y=+72
        assert mesh["connectors"]["studs"] == [], pid                             # studs baked into the mesh
        socks = sorted(tuple(s["pos"]) for s in mesh["connectors"]["sockets"])
        assert socks == [(-10 * q, ch.FEET_Y * q, 0), (10 * q, ch.FEET_Y * q, 0)], pid
        assert all(s["dir"] == [0, 1, 0] for s in mesh["connectors"]["sockets"]), pid
        lo = [v / q - 0.5 for v in mesh["bounds"]["min"]]
        hi = [v / q + 0.5 for v in mesh["bounds"]["max"]]
        for x0, x1, y0, y1, z0, z1 in mesh["occupancy"]:
            assert lo[0] <= x0 < x1 <= hi[0] and lo[1] <= y0 < y1 <= hi[1] and lo[2] <= z0 < z1 <= hi[2], pid


def test_baked_character_keeps_its_own_colours(index):
    """Printed torsos and multi-colour figures must not be tinted by the instance colour: every triangle group
    carries a baked #rrggbb (the WebGL renderer's per-vertex colour path), none is 'main'."""
    for pid in (p for p in index if p.startswith("mf-")):
        mesh = json.loads((PARTS_DIR / (pid + ".json")).read_text())
        colours = [g["colour"] for g in mesh["triangles"]]
        assert colours and all(c.startswith("#") for c in colours), (pid, colours)
        assert set(mesh["character"]["slots"]) == set(ch.template_slots(
            next(t for t in ch.TEMPLATES if ch.character_id(t) == pid)))
