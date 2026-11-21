"""Tests for the Python port of the mermaid_arch compiler.

The oracle is the JS compiler itself: ref_dump.mjs runs it over the JS repo's corpus (tests/mermaid_corpus) once per
session and the Python results are compared with that. Set A2UI_JS_ROOT to the JS repo root and A2UI_NODE to the node
binary when they are not in the default places. Without them the oracle tests are skipped.
"""
from __future__ import annotations

import functools
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))   # macro-packs/ (the import root: archpack, d3pack)

from archpack.markup import d2_to_arch, json_to_arch, mermaid_to_arch   # noqa: E402
from archpack.markup.d2 import parse_d2   # noqa: E402
from archpack.markup.graph import ArchError, fold_groups   # noqa: E402
from archpack.markup.mermaid import parse_mermaid   # noqa: E402

JS_ROOT = Path(os.environ.get('A2UI_JS_ROOT', HERE.parents[2]))   # default: this repository's root (scripts/mermaid_arch and tests/mermaid_corpus are the JS reference)
NODE = os.environ.get('A2UI_NODE') or shutil.which('node') or 'node'
CORPUS = JS_ROOT / 'tests' / 'mermaid_corpus'
HAVE_ORACLE = Path(NODE).exists() and CORPUS.is_dir()
oracle = pytest.mark.skipif(not HAVE_ORACLE, reason='node or the JS corpus is not available')

FILES = sorted(p.name for p in CORPUS.iterdir() if p.suffix in ('.mmd', '.d2', '.json') and p.name != 'expected.json') if CORPUS.is_dir() else []
OPTSETS = {   # the same option sets ref_dump.mjs runs; A is the one tests/mermaid_corpus_runner.mjs uses
    'A': {'numbered': True, 'hint': 'web'},
    'B': {},
    'C': {'routing': 'curve', 'hint': 'cli'},
    'D': {'numbered': True, 'pace': 'slow', 'duration': 60, 'direction': 'TD', 'title': 'T <b>x</b>'},
    'E': {'size': 14, 'fit': 'wide', 'direction': 'RL'},
    'F': {'direction': 'BT', 'pace': 'fast', 'numbered': True, 'relationColumn': True, 'relationName': 'Rel'},
    'G': {'duration': 5, 'numbered': True},
    'H': {'duration': 14, 'size': 22, 'direction': 'LR', 'hint': 'web'},
}


@pytest.fixture(scope='session')
def ref(tmp_path_factory):
    out = tmp_path_factory.mktemp('ref') / 'ref.json'
    proc = subprocess.run([NODE, str(HERE / 'ref_dump.mjs'), str(out), str(JS_ROOT)], capture_output=True, text=True, timeout=300, check=False)
    assert proc.returncode == 0, proc.stderr[-2000:]
    return json.loads(out.read_text(encoding='utf-8'))


def text_of(name):
    return (CORPUS / name).read_text(encoding='utf-8')


def norm(x):
    return json.loads(json.dumps(x))


# ---------------------------------------------------------------- slice 1: parsers and validation
def parse_py(name):
    text = text_of(name)
    try:
        if name.endswith('.json'):
            raw = json.loads(text)
            g, w = fold_groups(raw)
            return {'ok': True, 'graph': raw, 'fold': {'graph': g, 'warnings': w}}
        r = (parse_d2 if name.endswith('.d2') else parse_mermaid)(text, {})
        return {'ok': True, 'graph': r['graph'], 'warnings': r['warnings']}
    except json.JSONDecodeError:
        return {'ok': False, 'syntax': True}
    except ArchError as e:
        return {'ok': False, 'known': True, 'errors': e.errors, 'warnings': e.warnings}


@oracle
@pytest.mark.parametrize('name', FILES)
def test_parse_equals_js(ref, name):
    want, got = ref[name]['parse'], parse_py(name)
    assert got['ok'] == want['ok']
    if want['ok']:
        assert norm(got) == norm(want)
    elif want.get('syntax'):
        assert got.get('syntax')   # JSON.parse vs json.loads: the wording of the message differs, the failure does not
    else:
        assert got['errors'] == want['errors'] and got['warnings'] == want['warnings']


# ---------------------------------------------------------------- slice 2: layout, routing, schedule
def convert_py(name, opts):
    text = text_of(name)
    if name.endswith('.json'):
        return json_to_arch(text, **opts)
    return (d2_to_arch if name.endswith('.d2') else mermaid_to_arch)(text, **opts)


@functools.lru_cache(maxsize=None)
def run_py(name, k):
    """-> ('ok', ArchResult) | ('error', ArchError) | ('syntax', None)"""
    try:
        return 'ok', convert_py(name, OPTSETS[k])
    except ArchError as e:
        return 'error', e
    except json.JSONDecodeError:
        return 'syntax', None


CASES = [(n, k) for n in FILES for k in OPTSETS]
IDS = [f'{n}-{k}' for n, k in CASES]
TOL = 0.5   # percentage points


def close(a, b, path=''):
    """Structure equal, numbers within TOL (positions and sizes are percent of the frame, timings are fractions of 1)."""
    if isinstance(a, dict) and isinstance(b, dict):
        assert sorted(a) == sorted(b), f'{path}: keys {sorted(a)} != {sorted(b)}'
        for k in a:
            close(a[k], b[k], f'{path}/{k}')
    elif isinstance(a, list) and isinstance(b, list):
        assert len(a) == len(b), f'{path}: {len(a)} != {len(b)}'
        for i, (x, y) in enumerate(zip(a, b)):
            close(x, y, f'{path}/{i}')
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        assert abs(a - b) <= TOL, f'{path}: {a} vs {b}'
    else:
        assert a == b, f'{path}: {a!r} != {b!r}'


@oracle
@pytest.mark.parametrize('name,k', CASES, ids=IDS)
def test_arch_equals_js_within_tolerance(ref, name, k):
    want = ref[name]['full'][k]
    kind, got = run_py(name, k)
    if kind == 'syntax':
        assert want['ok'] is False and want.get('syntax')
        return
    assert (kind == 'ok') == want['ok']
    if kind == 'error':
        assert got.errors == want['errors'] and got.warnings == want['warnings']
        return
    assert got.warnings == want['warnings']
    close(norm(got.block), want['block'], 'block')
    assert norm(got.text_steps) == want['textSteps'] and norm(got.text_messages) == want['textMessages']


@oracle
@pytest.mark.parametrize('name,k', CASES, ids=IDS)
def test_arch_exact_like_js(ref, name, k):
    """The port does the same arithmetic in the same order, so nothing differs, not even in the last digit."""
    want = ref[name]['full'][k]
    kind, got = run_py(name, k)
    if kind != 'ok':
        pytest.skip('error case, covered by the tolerance test')
    assert norm(got.block) == want['block']
    assert norm(got.schedule) == want['schedule'] and got.duration_seconds == want['durationSeconds']
    assert got.layout['direction'] == want['direction']


# ---------------------------------------------------------------- slice 3: the result goes into arch_motion
from archpack.arch_motion import arch_motion   # noqa: E402


@oracle
@pytest.mark.parametrize('name,k', CASES, ids=IDS)
def test_error_message_is_js_message(ref, name, k):
    want = ref[name]['full'][k]
    kind, got = run_py(name, k)
    if want['ok']:
        pytest.skip('renders, covered by test_renders')
    if want.get('syntax'):
        assert kind == 'syntax'
        return
    assert kind == 'error'
    assert str(got) == '\n'.join(want['errors'])


@oracle
@pytest.mark.parametrize('name,k', CASES, ids=IDS)
def test_renders_in_arch_motion(ref, name, k):
    if not ref[name]['full'][k]['ok']:
        pytest.skip('JS does not render this one either')
    kind, res = run_py(name, k)
    assert kind == 'ok'
    out = arch_motion(**res)   # verify_rich runs inside, and raises when the svg is not admitted
    for variant in ('wide', 'narrow'):
        assert out[variant]['svg'].startswith('<svg')
        # the contract has no mismatch: nothing was clamped, dropped or ignored on the way in
        bad = [n for n in out[variant]['notes'] if any(w in n for w in ('clamped', 'were left out', 'were not drawn', 'Unknown option', 'invalid', 'defaulted', 'ignored'))]
        assert not bad, bad
    assert len(res['nodes']) == len(ref[name]['full'][k]['block']['nodes'])


# ---------------------------------------------------------------- the API
def test_result_is_arch_motion_kwargs():
    res = mermaid_to_arch('flowchart LR\n  a[Client] -->|hi| b[Server]\n')
    assert 'type' not in res and 'warnings' not in res
    assert {'label', 'w', 'h', 'size', 'nodes', 'edges'} <= set(res)
    assert isinstance(res.warnings, list) and res.text_steps[0]['step'] == 1
    assert arch_motion(**res)['wide']['svg']


def test_d2_and_json_entry_points():
    r1 = d2_to_arch('a: A\nb: B\na -> b: go\n')
    r2 = json_to_arch({'direction': 'LR', 'nodes': [{'id': 'a', 'label': 'A'}, {'id': 'b', 'label': 'B'}], 'edges': [{'from': 'a', 'to': 'b', 'label': 'go'}]})
    assert [n['id'] for n in r1['nodes']] == [n['id'] for n in r2['nodes']] == ['a', 'b']
    assert arch_motion(**r1)['wide']['svg'] and arch_motion(**r2)['wide']['svg']


@pytest.mark.parametrize('opts,msg', [
    ({'size': 3}, 'size 3 must be a number from 8 to 40 (label text size in px)'),
    ({'fit': 'x'}, 'fit "x" must be balanced or wide'),
    ({'duration': 1}, 'duration 1 must be a number of seconds from 2 to 120'),
    ({'pace': 'warp'}, 'pace "warp" must be one of slow, normal, fast'),
    ({'direction': 'UP'}, 'direction "UP" must be LR, RL, TB (or TD) or BT'),
])
def test_bad_options_are_refused_not_clamped(opts, msg):
    with pytest.raises(ArchError) as e:
        mermaid_to_arch('flowchart LR\n a --> b\n', **opts)
    assert str(e.value) == msg


def test_html_tags_are_removed_and_warned():
    res = json_to_arch({'direction': 'LR', 'nodes': [{'id': 'a', 'label': 'A<script>x</script>'}, {'id': 'b', 'label': 'B'}], 'edges': [{'from': 'a', 'to': 'b'}]})
    assert 'script' not in json.dumps(res)
    assert res.warnings[0] == 'HTML tags were removed from a label.'
