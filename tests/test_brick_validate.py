"""Build checks for the brick_build_3d atom — renderers/brick_validate.py.

Two layers of proof:
  * parity   — tests/fixtures/bricks/parity_cases.json holds models and the results the atom's JavaScript
               validator produced for them (six stock shapes plus a faulted heart). The Python twin must
               reproduce every number and every detail string, so an agent-supplied design checked
               server-side gets the same verdict the browser shows.
  * designs  — small hand-built models that each break exactly one rule, so a check that stops firing fails
               a test by name instead of hiding inside a large fixture.
"""
import json
import os

import pytest

from renderers.brick_validate import normalise, validate

HERE = os.path.dirname(__file__)
with open(os.path.join(HERE, 'fixtures', 'bricks', 'parity_cases.json'), encoding='utf-8') as _f:
    CASES = json.load(_f)['cases']


def _status(report):
    return {c['id']: c['status'] for c in report['checks']}


def B(x, y, z, w=1, d=1, h=1, c='#c91a09'):
    return {'x': x, 'y': y, 'z': z, 'w': w, 'd': d, 'h': h, 'c': c}


# ---------------------------------------------------------------- parity with the JavaScript validator

@pytest.mark.parametrize('case', CASES, ids=[c['name'] for c in CASES])
def test_matches_javascript_validator(case):
    exp = case['expected']
    model = normalise(case['bricks'])
    report = validate(model['bricks'])

    assert report['ok'] == exp['ok']
    assert report['checks'] == exp['checks']            # id, label, status and the rendered detail text
    assert report['connections'] == exp['connections']
    assert report['overlaps'] == exp['overlaps']
    assert report['floating'] == exp['floating']
    assert report['com']['x'] == pytest.approx(exp['com']['x'], abs=1e-9)
    assert report['com']['z'] == pytest.approx(exp['com']['z'], abs=1e-9)
    assert report['com']['margin'] == pytest.approx(exp['com']['margin'], abs=1e-9)
    assert report['cost'] == pytest.approx(exp['cost'], abs=1e-9)
    assert [{'size': p['size'], 'colour': p['colour'], 'count': p['count']} for p in report['parts']] == exp['parts']
    assert model['steps'] == exp['steps']
    per_step = {}
    for b in model['bricks']:
        per_step[b['step']] = per_step.get(b['step'], 0) + 1
    assert [per_step[k] for k in sorted(per_step)] == exp['per_step']


def test_fixture_covers_pass_and_fail():
    verdicts = {c['name']: c['expected']['ok'] for c in CASES}
    assert verdicts['heart'] is True
    assert verdicts['heart_faulted'] is False


# ---------------------------------------------------------------- hand-built designs

def test_valid_tower_passes_and_counts_connections():
    tower = [B(0, 0, 0, 2, 2), B(0, 1, 0, 2, 2), B(0, 2, 0, 2, 2)]
    r = validate(tower)
    assert r['ok'] and set(_status(r).values()) == {'pass'}
    assert r['connections'] == 12                      # 4 studs on the baseplate + 4 + 4 between layers
    assert r['floating'] == 0 and r['overlaps'] == 0


def test_duplicate_brick_is_a_collision():
    r = validate([B(0, 0, 0, 2, 2), B(0, 1, 0, 2, 2), B(0, 1, 0, 2, 2)])
    assert _status(r)['collisions'] == 'fail'
    assert r['overlaps'] == 1 and not r['ok']


def test_partial_overlap_reports_shared_cells():
    r = validate([B(0, 0, 0, 4, 1), B(3, 0, 0, 2, 1)])
    assert r['overlaps'] == 1
    assert '1 brick pair share 1 stud cell' in r['checks'][0]['detail']


def test_brick_with_a_gap_beneath_is_floating():
    r = validate([B(0, 0, 0, 2, 2), B(0, 2, 0, 2, 2)])   # nothing on layer 1
    assert _status(r)['anchored'] == 'fail'
    assert r['floating'] == 1


def test_brick_hanging_from_one_above_is_anchored():
    # A overhangs with nothing under it, but the brick above rests on both A and the pillar: still one part.
    r = validate([B(0, 0, 0, 1, 1), B(0, 1, 0, 1, 1), B(1, 1, 0, 1, 1), B(0, 2, 0, 2, 1)])
    assert _status(r)['anchored'] == 'pass'


def test_side_by_side_bricks_are_not_connected():
    # touching on a face is not a stud connection
    r = validate([B(0, 0, 0, 1, 1), B(0, 1, 0, 1, 1), B(1, 1, 0, 1, 1)])
    assert r['floating'] == 1


def test_cantilever_fails_balance():
    lean = [B(0, 0, 0, 2, 2), B(1, 1, 0, 4, 2), B(1, 2, 0, 4, 2)]
    r = validate(lean)
    assert _status(r)['balance'] == 'fail'
    assert r['com']['margin'] < 0
    assert 'outside by' in r['checks'][3]['detail']


def test_tight_balance_warns():
    # 1x1 foot with 2x1 bricks stacked toward +x: centre of mass at x=0.9, 0.1 stud inside the foot's edge
    r = validate([B(0, 0, 0, 1, 1), B(0, 1, 0, 2, 1), B(0, 2, 0, 2, 1)])
    assert _status(r)['balance'] == 'warn'
    assert r['com']['margin'] == pytest.approx(0.1)
    assert r['ok']                                    # a warning does not fail the build


def test_centred_tower_on_a_single_stud_has_exactly_half_a_stud_of_margin():
    r = validate([B(0, 0, 0, 1, 1), B(0, 1, 0, 1, 1), B(0, 2, 0, 1, 1)])
    assert r['com']['margin'] == pytest.approx(0.5)
    assert _status(r)['balance'] == 'pass'


def test_no_ground_level_bricks_cannot_balance():
    r = validate([B(0, 1, 0, 2, 2)])
    assert _status(r)['balance'] == 'fail' and _status(r)['anchored'] == 'fail'


def test_parts_list_groups_by_size_and_colour():
    r = validate([B(0, 0, 0, 2, 2, c='#c91a09'), B(2, 0, 0, 2, 2, c='#C91A09'), B(0, 1, 0, 2, 2, c='#0055bf')])
    parts = {(p['size'], p['colour']): p['count'] for p in r['parts']}
    assert parts == {('2×2', 'red'): 2, ('2×2', 'blue'): 1}
    assert r['cost'] == pytest.approx(3 * (0.03 + 0.04 * 4))


def test_unknown_colour_is_listed_by_hex():
    r = validate([B(0, 0, 0, c='#123456')])
    assert r['parts'][0]['colour'] == '#123456'


# ---------------------------------------------------------------- normalise / steps

def test_normalise_shifts_to_origin_and_numbers_steps():
    bricks = [B(5, 3, 7, 1, 1) for _ in range(1)] + [B(5 + i, 4, 7) for i in range(7)]
    m = normalise(bricks)
    assert min(b['x'] for b in m['bricks']) == 0 and min(b['y'] for b in m['bricks']) == 0
    assert m['L'] == 2 and m['steps'] == 3            # layer 0: 1 brick; layer 1: 7 bricks -> 6 + 1
    assert [b['step'] for b in m['bricks']] == [1, 2, 2, 2, 2, 2, 2, 3]


def test_multi_layer_brick_height_counts_towards_L():
    m = normalise([B(0, 0, 0, 2, 2, h=3)])
    assert m['L'] == 3


# ---------------------------------------------------------------- bad input

@pytest.mark.parametrize('bad', [
    [], [B(0, 0, 0, w=0)], [B(0, 0, 0, d=-1)], [B(0, 0, 0, h=0)], [B(-1, 0, 0)],
    [{'x': 0.5, 'y': 0, 'z': 0}], [{'x': True, 'y': 0, 'z': 0}],
])
def test_bad_input_is_rejected_not_guessed(bad):
    with pytest.raises(ValueError):
        validate(bad)
