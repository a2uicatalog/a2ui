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

from renderers.brick_parts_validate import validate_parts

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
