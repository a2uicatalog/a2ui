"""Phase 4: deterministic voxel -> real-parts builder (scripts/brick_models/parts_builder.py), gated by the
Python real-parts validator, plus the Rebrickable wanted-list export."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts' / 'brick_models'))
import parts_builder as pb  # noqa: E402


def _block():
    v = {(x, l, z) for x in range(6) for z in range(4) for l in range(3)}
    return v | {(x, 3, z) for x in range(1, 5) for z in range(1, 3)}


def test_block_builds_valid_and_covers_every_cell():
    parts, rep = pb.repair(_block())
    assert rep['ok'] and rep['collisions'] == [] and rep['floating'] == []
    assert all(c['status'] == 'pass' for c in rep['checks'])
    # 6*4*3 + 4*2 = 80 cells; 1xN bricks cover N cells each
    size = {'3010': 4, '3622': 3, '3004': 2, '3005': 1}
    assert sum(size[p['p']] for p in parts) == 80


def test_build_is_deterministic():
    assert pb.build_parts(_block()) == pb.build_parts(_block())


def test_layers_alternate_orientation_for_running_bond():
    parts = pb.build_parts(_block())
    rot = {}
    for p in parts:
        rot.setdefault(p['y'], set()).add(p['r'])
    assert rot[-24] == {0} and rot[-48] == {1} and rot[-72] == {0}


def test_unsupported_layer_is_reported_floating():
    parts = pb.build_parts({(0, 0, 0), (5, 2, 5)})   # second cell hovers over nothing
    assert pb.validate(parts)['ok'] is False


def test_wanted_list_csv_counts_parts_by_colour():
    parts = pb.build_parts({(x, 0, 0) for x in range(4)} | {(x, 0, 1) for x in range(2)}, {'*': 15})
    assert pb.rebrickable_wanted_csv(parts) == 'Part,Color,Quantity\n3004,15,1\n3010,15,1\n'
