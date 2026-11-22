"""Flow group tests (waterfall, stacked_area, swimlane, sankey_flow): independent arithmetic on each layout, tolerant-reader rules, guard rails, and every message validated against the upstream
A2UI 1.0 schemas (with negative controls). Run: A2UI_UPSTREAM=<upstream checkout> python3 -B tests/test_flow.py"""
import glob, json, math, random, re, sys, copy
from pathlib import Path
import os
_UP = os.environ.get('A2UI_UPSTREAM')
try:
    import jsonschema  # noqa: F401
except ImportError:
    _UP = None
if not _UP or not (Path(_UP) / 'specification/v1_0/json').is_dir():
    print('SKIPPED: set A2UI_UPSTREAM to a checkout of the upstream A2UI repository (and install jsonschema) to run the schema validation')
    sys.exit(0)
import xml.etree.ElementTree as ET
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE.parent)); sys.dont_write_bytecode = True
from d3pack import common as CM
from d3pack.common import atom_card
from d3pack.waterfall import waterfall
from d3pack.stacked_area import stacked_area, stack
from d3pack.lanes import swimlane
from d3pack.sankey import sankey_flow
from d3pack.registry_flow import PACK_FLOW
from d3pack.demos_flow import DEMOS
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
SPEC = (Path(_UP) / 'specification/v1_0/json'); CATF = (Path(_UP) / 'catalogs/basic/v1/catalog.json')
docs = {p: json.loads(Path(p).read_text()) for p in glob.glob(str(SPEC / '*.json'))}; cat = json.loads(CATF.read_text())
res = [(d.get('$id', 'file://' + p), Resource.from_contents(d)) for p, d in docs.items()] + [(cat['$id'], Resource.from_contents(cat)), ('https://a2ui.org/specification/v1_0/catalog.json', Resource.from_contents(cat))]
A2R = Draft202012Validator(docs[str(SPEC / 'agent_to_renderer.json')], registry=Registry().with_resources(res))
n = 0; bad = 0
def ok(name, c):
    global n, bad; n += 1
    if not c: bad += 1; print('FAIL', name)
def raises(fn):
    try: fn(); return False
    except ValueError: return True
def wf(r): ET.fromstring(r['svg']); return True
NSV = '{http://www.w3.org/2000/svg}'
close = lambda a, b, t=1e-9: abs(a - b) <= t * max(1, abs(a), abs(b))
# ---------- waterfall
ST = [{'label': 'Start', 'kind': 'total', 'value': 100}, {'label': 'a', 'value': 40}, {'label': 'b', 'value': -25.5}, {'label': 'sub', 'kind': 'total'}, {'label': 'c', 'value': -10}, {'label': 'End', 'kind': 'total'}]
r = waterfall(ST, unit='k', x_label='Bridge', title='T')['waterfall']; B = r['bars']
cum = 0; exp = []
for s in ST:
    if s.get('kind') == 'total': cum = s.get('value', cum); exp.append(cum)
    else: cum += s['value']; exp.append(cum)
ok('waterfall: running level equals a plain cumulative sum', all(close(b['level'], e) for b, e in zip(B, exp)))
ok('waterfall: each delta bar starts at the previous level and ends at the new one', all(close(B[i]['start'], B[i - 1]['level']) and close(B[i]['end'], B[i]['level']) for i in range(1, len(B)) if B[i]['kind'] == 'delta'))
ok('waterfall: consecutive delta bars end where the next begins', close(B[1]['end'], B[2]['start']))
ok('waterfall: a total without a value shows the running total from 0', B[3]['start'] == 0 and close(B[3]['end'], 114.5) and close(B[3]['value'], 114.5))
ok('waterfall: a total with a value sets the level', B[0]['end'] == 100 and B[0]['start'] == 0)
r2 = waterfall([{'value': 50}, {'kind': 'total', 'value': 10}, {'value': 5}])['waterfall']; ok('waterfall: a total with a different value sets the level and says so', r2['bars'][2]['level'] == 15 and any('set it' in x for x in r2['notes']))
ok('waterfall: default label is Step n', 'Step 2' in waterfall([{'value': 1}, {'value': 2}])['waterfall']['table'])
rn = waterfall(ST + ['junk', {'label': 'x'}, {'label': 'big', 'value': 1e13}, {'label': 'nan', 'value': float('nan')}, {'label': 'bool', 'value': True}])['waterfall']; ok('waterfall: unusable steps dropped and counted', any('5 steps were left out' in x for x in rn['notes']) and len(rn['bars']) == 6)
ok('waterfall: more than 24 steps cut and noted', any('beyond the 24th' in x for x in waterfall([{'value': 1}] * 27)['waterfall']['notes']))
ok('waterfall: version 2 drawn as 1 with a note', any('version 1' in x for x in waterfall(ST, version=3)['waterfall']['notes']))
ok('waterfall: nothing usable gives a note-only result, not an error', waterfall([{'label': 'x'}, 3])['waterfall'].get('empty') is True and 'nothing to draw' in waterfall([{'label': 'x'}, 3])['waterfall']['alt'])
ok('waterfall: steps that are not a list give a note-only result', waterfall('x')['waterfall'].get('empty') is True and waterfall(None)['waterfall'].get('empty') is True)
ok('waterfall: table lists every label and signed value', all(s in r['table'] for s in ('Start 100 k', 'a +40 k', 'b -25.5 k', 'sub 114.5 k', 'c -10 k', 'End 104.5 k')))
ok('waterfall: alt text carries the final total and the largest change', '104.5 k' in r['alt'] and 'Largest increase: a' in r['alt'] and 'Largest decrease: b' in r['alt'])
ok('waterfall: negative running levels are drawn (axis reaches below 0)', min(waterfall([{'value': -30}, {'value': 10}])['waterfall']['ticks']) <= -30)
ok('waterfall: ticks cover every level', min(r['ticks']) <= 0 and max(r['ticks']) >= max(b['end'] for b in B))
xe = ET.fromstring(waterfall([{'label': '<b>&"', 'value': 1}])['waterfall']['svg']); ok('waterfall: markup in a label is escaped and read back as the same text', '<b>&"' in [e.text for e in xe.iter(NSV + 'text')] and '<b>' not in waterfall([{'label': '<b>', 'value': 1}])['waterfall']['svg'])
ok('waterfall: well-formed and deterministic', wf(r) and waterfall(ST, unit='k', x_label='Bridge', title='T')['waterfall']['svg'] == r['svg'])
ok('waterfall: default label is Step n by list position (a dropped step still counts)', 'Step 3' in waterfall([{'value': 1}, 'junk', {'value': 2}])['waterfall']['table'] and 'Step 2' not in waterfall([{'value': 1}, 'junk', {'value': 2}])['waterfall']['table'])
# ---------- stacked_area
LB = ['a', 'b', 'c', 'd']; SE = [{'label': 'x', 'data': [1, 4, 2, 6]}, {'label': 'y', 'data': [3, 1, 5, 2]}, {'label': 'z', 'data': [2, 2, 2, 2]}]; sa = stacked_area(LB, SE)
tot = [sum(s['data'][j] for s in SE) for j in range(4)]
ok('stacked_area: all four offsets drawn, default none', set(sa) == {'none', 'silhouette', 'wiggle', 'expand', '_default'} and sa['_default'] == 'none')
L0 = sa['none']['layers']; ok('stacked_area none: baseline is zero', all(v == 0 for v in L0[0]['y0']))
ok('stacked_area none: layers sum to the column totals', all(close(L0[-1]['y1'][j], tot[j]) for j in range(4)))
ok('stacked_area none: each layer thickness equals its data', all(close(L0[i]['y1'][j] - L0[i]['y0'][j], SE[i]['data'][j]) for i in range(3) for j in range(4)))
ok('stacked_area: layers are contiguous (top of one = bottom of the next)', all(close(L0[i]['y1'][j], L0[i + 1]['y0'][j]) for i in range(2) for j in range(4)))
Lx = sa['expand']['layers']; ok('stacked_area expand: every column sums to 1', all(close(Lx[-1]['y1'][j] - Lx[0]['y0'][j], 1) for j in range(4)) and all(v == 0 for v in Lx[0]['y0']))
ok('stacked_area expand: thickness is the share', all(close(Lx[i]['y1'][j] - Lx[i]['y0'][j], SE[i]['data'][j] / tot[j]) for i in range(3) for j in range(4)))
Ls = sa['silhouette']['layers']; ok('stacked_area silhouette: symmetric about zero', all(close(Ls[0]['y0'][j], -tot[j] / 2) and close(Ls[-1]['y1'][j], tot[j] / 2) for j in range(4)))
ok('stacked_area silhouette: thickness is the value', all(close(Ls[i]['y1'][j] - Ls[i]['y0'][j], SE[i]['data'][j]) for i in range(3) for j in range(4)))
Lw = sa['wiggle']['layers']; srt = lambda j: sorted(Lw, key=lambda q: q['y0'][j]); ok('stacked_area wiggle: thickness is the value and layers contiguous', all(close(Lw[i]['y1'][j] - Lw[i]['y0'][j], SE[i]['data'][j]) for i in range(3) for j in range(4)) and all(close(srt(j)[a]['y1'][j], srt(j)[a + 1]['y0'][j]) for a in range(2) for j in range(4)))
ok('stacked_area wiggle: layers stacked inside-out, hand-dealt order bottom to top is x, z, y', all(Lw[0]['y0'][j] < Lw[2]['y0'][j] < Lw[1]['y0'][j] for j in range(4)))
one = stacked_area(['a', 'b', 'c'], [{'label': 's', 'data': [2, 6, 3]}])['wiggle']['layers'][0]; ok('stacked_area wiggle: for one series the baseline is -(v - v0)/2 (hand derivation of d3)', all(close(one['y0'][j], -(v - 2) / 2) for j, v in enumerate([2, 6, 3])))
two = stack([[1, 1], [3, 1]], 'wiggle'); ok('stacked_area wiggle: two-series hand calculation with inside-out order (series 1 at the bottom)', two[1][0] == [0, -0.75] and two[0][0] == [1, 0.25])
ok('stacked_area: wiggle differs from silhouette', any(not close(a, b) for a, b in zip(Lw[0]['y0'], Ls[0]['y0'])))
rn = stacked_area(LB, SE + [{'label': 'bad', 'data': 'x'}, 'junk', {'label': 'neg', 'data': [1, -2, 'q', 4, 99]}])['none']; ok('stacked_area: bad series dropped, bad values 0, long data cut, all noted', len(rn['layers']) == 4 and any('2 series were left out' in x for x in rn['notes']) and any('drawn as 0' in x for x in rn['notes']) and any('different length' in x for x in rn['notes']) and rn['layers'][3]['y1'][1] - rn['layers'][3]['y0'][1] == 0)
ok('stacked_area: more than 12 series cut and noted, 12 drawn', any('beyond the 12th' in x for x in stacked_area(LB, [{'label': str(i), 'data': [1, 1, 1, 1]} for i in range(14)])['none']['notes']) and len(stacked_area(LB, [{'label': str(i), 'data': [1, 1, 1, 1]} for i in range(14)])['none']['layers']) == 12)
ok('stacked_area: colours come from PAL only', set(re.findall(r'fill="(#[0-9a-f]{6})"', sa['none']['svg'])) <= set(CM.PAL) | {CM.FACE, CM.INK, CM.MUTED})
ok('stacked_area: table lists every value and total', all(f'{LB[j]} {SE[i]["data"][j]}' in sa['none']['table'] for i in range(3) for j in range(4)) and all(f'{LB[j]} {tot[j]}' in sa['none']['table'] for j in range(4)))
ok('stacked_area: fewer than 2 labels gives a note-only result', stacked_area(['a'], SE)['none'].get('empty') is True); ok('stacked_area: no series gives a note-only result', stacked_area(LB, [])['none'].get('empty') is True); ok('stacked_area: all zero gives a note-only result', stacked_area(LB, [{'data': [0, 0, 0, 0]}])['none'].get('empty') is True)
ok('stacked_area: unknown offset drawn as none with a note', stacked_area(LB, SE, offset='zigzag')['_default'] == 'none' and any('drawn as none' in x for x in stacked_area(LB, SE, offset='zigzag')['none']['notes']))
ok('stacked_area: well-formed, deterministic', all(wf(v) for k_, v in sa.items() if k_ != '_default') and stacked_area(LB, SE)['wiggle']['svg'] == sa['wiggle']['svg'])
rng = random.Random(3); good = True
for _ in range(30):
    m = rng.randint(2, 7); k_ = rng.randint(1, 5); S = [{'label': f's{i}', 'data': [rng.choice([0, 1, 2.5, 7]) for _ in range(m)]} for i in range(k_)]
    if sum(sum(s['data']) for s in S) == 0: continue
    t_ = [sum(s['data'][j] for s in S) for j in range(m)]; o = stacked_area([str(j) for j in range(m)], S)
    good = good and all(close(o['none']['layers'][-1]['y1'][j], t_[j]) for j in range(m)) and all(close(o['silhouette']['layers'][0]['y0'][j], -t_[j] / 2) for j in range(m)) and all(close(o['expand']['layers'][-1]['y1'][j], 1 if t_[j] else 0) for j in range(m))
ok('stacked_area: invariants hold on 30 random datasets', good)
from d3pack.stacked_area import inside_out
ok('stacked_area: inside-out order matches a hand deal ([1,3,2],[5,1,2] peaks 1,0)', inside_out([[1, 5], [3, 1]]) == [1, 0] and sorted(inside_out([[1, 5, 2], [3, 1, 2], [2, 2, 9]])) == [0, 1, 2])
bs = stacked_area(LB, SE, layout='bars', offset='wiggle'); ok('stacked_area: bars layout drawn, ignores offset with a note', bs['_default'] == 'bars' and wf(bs['bars']) and any('ignores offset' in x for x in bs['bars']['notes']) and all(f'{LB[j]} {SE[0]["data"][j]}' in bs['bars']['table'] for j in range(4)))
ok('stacked_area: 60 labels and 12 series accepted', len(stacked_area([str(i) for i in range(60)], [{'data': [1] * 60} for _ in range(12)])['none']['layers']) == 12 and any('61 labels' not in x and '60th' in x for x in stacked_area([str(i) for i in range(62)], [{'data': [1] * 62}])['none']['notes']))
# ---------- swimlane
RO = ['Sec', 'Eng', 'QA']; PH = ['One', 'Two', 'Three']; TK = [{'role': 'Sec', 'phase': 'One', 'task': 'first'}, {'role': 'Eng', 'phase': 'One', 'task': 'second'}, {'role': 'Eng', 'phase': 'Two', 'task': 'third'}, {'role': 'QA', 'phase': 'Three', 'task': 'fourth'}, {'role': 'Eng', 'phase': 'Two', 'task': 'fifth'}]
sw = swimlane(RO, PH, TK, title='T')['swimlane']
ok('swimlane: tasks are numbered in list order', [t['n'] for t in sw['tasks']] == [1, 2, 3, 4, 5] and [t['task'] for t in sw['tasks']] == ['first', 'second', 'third', 'fourth', 'fifth'])
ok('swimlane: placeholder removed (positions are checked by the SVG read-back oracle below)', True)
gh = (520 - 56 - 12) / 3; ok('swimlane: card y is within the role row', all(56 + gh * RO.index(t['role']) <= sw['cards'][t['n']][1] and sw['cards'][t['n']][1] + sw['cards'][t['n']][3] <= 56 + gh * (RO.index(t['role']) + 1) for t in sw['tasks']))
ok('swimlane: cards do not overlap', all(not (a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]) for i, a in sw['cards'].items() for j, b in sw['cards'].items() if i < j))
ok('swimlane: two tasks in one cell stack vertically', sw['cards'][3][1] < sw['cards'][5][1] and sw['cards'][3][0] == sw['cards'][5][0])
rn = swimlane(RO, PH, TK + [{'role': 'Eng', 'phase': 'Two', 'task': 'sixth'}, {'role': 'Nobody', 'phase': 'One', 'task': 'x'}, {'role': 'Sec', 'phase': 'Nowhere', 'task': 'x'}, 'junk', {'role': 'Sec', 'phase': 'One'}])['swimlane']
ok('swimlane: third task in a cell dropped and noted', any('already held two' in x for x in rn['notes']) and len(rn['tasks']) == 5)
ok('swimlane: unlisted role or phase, non-object, no text dropped and counted', any('4 tasks were left out' in x for x in rn['notes']))
ok('swimlane: more than 12 tasks cut and noted', any('beyond the 12th' in x for x in swimlane(['a', 'b'], ['c', 'd'], [{'role': 'a', 'phase': 'c', 'task': str(i)} if i % 2 else {'role': 'b', 'phase': 'd', 'task': str(i)} for i in range(14)])['swimlane']['notes']))
ok('swimlane: more than 4 roles cut, more than 5 phases cut', any('beyond the 4th' in x for x in swimlane(['a', 'b', 'c', 'd', 'e'], PH, TK[:0] + [{'role': 'a', 'phase': 'One', 'task': 't'}])['swimlane']['notes']) and any('beyond the 5th' in x for x in swimlane(RO, list('abcdefg'), [{'role': 'Sec', 'phase': 'a', 'task': 't'}])['swimlane']['notes']))
ok('swimlane: fewer than 2 roles or phases refused', raises(lambda: swimlane(['a'], PH, TK)) and raises(lambda: swimlane(RO, ['a', 'a'], TK)) and raises(lambda: swimlane(RO, PH, [])))
ok('swimlane: placeholder removed (task text is checked by the SVG read-back oracle below)', True)
ok('swimlane: table lists role, phase, number and full task', all(f'{t["n"]}. {t["role"]}, {t["phase"]}: {t["task"]}' in sw['table'] for t in sw['tasks']))
ok('swimlane: alt names the busiest role', 'Eng has the most (3)' in sw['alt'])
ok('swimlane: non-string role names become text', swimlane([1, 2.5], PH, [{'role': '1', 'phase': 'One', 'task': 't'}])['swimlane']['roles'] == ['1', '2.5'])
ok('swimlane: markup stays well-formed', wf(swimlane(['<a>', 'b&'], ['"p"', 'q'], [{'role': '<a>', 'phase': '"p"', 'task': '<x>&'}])['swimlane']))
ok('swimlane: text is at least 14px', all(int(x) >= 14 for x in re.findall(r'font-size="(\d+)"', sw['svg'])))
ok('swimlane: well-formed, deterministic', wf(sw) and swimlane(RO, PH, TK, title='T')['swimlane']['svg'] == sw['svg'])
# ---------- sankey
ND = [{'id': i, 'label': i.upper()} for i in 'abcdef']; LK = [{'source': 'a', 'target': 'b', 'value': 10}, {'source': 'a', 'target': 'c', 'value': 5}, {'source': 'b', 'target': 'd', 'value': 6}, {'source': 'b', 'target': 'e', 'value': 4}, {'source': 'c', 'target': 'e', 'value': 5}, {'source': 'e', 'target': 'f', 'value': 9}]
sk = sankey_flow(ND, LK, title='T')['sankey_flow']; NN = {x['id']: x for x in sk['nodes']}; k_ = sk['k']
ok('sankey: node height is proportional to max(in, out)', all(close(x['h'], max(x['in'], x['out']) * k_) for x in sk['nodes']))
ok('sankey: node flows are the sums of its links', all(close(x['in'], sum(l['value'] for l in sk['links'] if l['target'] == x['id'])) and close(x['out'], sum(l['value'] for l in sk['links'] if l['source'] == x['id'])) for x in sk['nodes']))
ok('sankey: the same k for every node (one scale)', len({round(x['h'] / x['value'], 9) for x in sk['nodes']}) == 1)
ok('sankey: columns follow longest path, a sink goes to the last column (a0 b1 c1 e2 d3 f3)', [NN[i]['col'] for i in 'abcdef'] == [0, 1, 1, 3, 2, 3])
ok('sankey: every link runs to a strictly later column', all(NN[l['source']]['col'] < NN[l['target']]['col'] for l in sk['links']))
ok('sankey: a link ribbon is as tall as its value on both ends', all(close(l['sy1'] - l['sy0'], l['value'] * k_) and close(l['ty1'] - l['ty0'], l['value'] * k_) for l in sk['links']))
ok('sankey: no link leaves its node (outgoing inside source, incoming inside target)', all(NN[l['source']]['y'] - 1e-6 <= l['sy0'] and l['sy1'] <= NN[l['source']]['y'] + NN[l['source']]['h'] + 1e-6 and NN[l['target']]['y'] - 1e-6 <= l['ty0'] and l['ty1'] <= NN[l['target']]['y'] + NN[l['target']]['h'] + 1e-6 for l in sk['links']))
ok('sankey: links on a node do not overlap each other', all(not (a['sy0'] < b['sy1'] - 1e-6 and b['sy0'] < a['sy1'] - 1e-6) for a in sk['links'] for b in sk['links'] if a is not b and a['source'] == b['source']) and all(not (a['ty0'] < b['ty1'] - 1e-6 and b['ty0'] < a['ty1'] - 1e-6) for a in sk['links'] for b in sk['links'] if a is not b and a['target'] == b['target']))
ok('sankey: flow is conserved through pass-through nodes (b, c, e have in = out)', all(close(NN[i]['in'], NN[i]['out']) for i in 'bce'))
ok('sankey: nodes in a column do not overlap and stay inside the drawing', all(0 <= x['y'] and x['y'] + x['h'] <= CM.H for x in sk['nodes']) and all(not (a['y'] < b['y'] + b['h'] and b['y'] < a['y'] + a['h']) for a in sk['nodes'] for b in sk['nodes'] if a is not b and a['col'] == b['col']))
ok('sankey: columns are drawn left to right in order', all(a['x'] < b['x'] for a in sk['nodes'] for b in sk['nodes'] if a['col'] < b['col']))
ok('sankey: ribbon order on a source follows the target position (no needless crossing)', all((a['sy0'] < b['sy0']) == (NN[a['target']]['y'] <= NN[b['target']]['y']) for a in sk['links'] for b in sk['links'] if a is not b and a['source'] == b['source'] and NN[a['target']]['y'] != NN[b['target']]['y']))
sinkcol = sankey_flow([{'id': 'a'}, {'id': 'b'}, {'id': 'c'}, {'id': 'd'}], [{'source': 'a', 'target': 'b', 'value': 1}, {'source': 'b', 'target': 'c', 'value': 1}, {'source': 'a', 'target': 'd', 'value': 1}])['sankey_flow']; ok('sankey: an unhinted node with no outflow goes to the last column', {x['id']: x['col'] for x in sinkcol['nodes']} == {'a': 0, 'b': 1, 'c': 2, 'd': 2})
cyc = sankey_flow(ND, LK + [{'source': 'f', 'target': 'a', 'value': 3}])['sankey_flow']; ok('sankey: a link closing a cycle is dropped and noted', len(cyc['links']) == 6 and any('cycle' in x for x in cyc['notes']))
hint = sankey_flow([{'id': 'a', 'column': 0}, {'id': 'b', 'column': 2}, {'id': 'c', 'column': 1}], [{'source': 'a', 'target': 'b', 'value': 1}, {'source': 'b', 'target': 'c', 'value': 1}, {'source': 'a', 'target': 'c', 'value': 2}])['sankey_flow']
ok('sankey: a link running backwards between hinted columns is dropped and noted', len(hint['links']) == 2 and any('left to right' in x for x in hint['notes']))
hn = {x['id']: x['col'] for x in hint['nodes']}; ok('sankey: column hints respected and gaps renumbered', hn == {'a': 0, 'b': 2, 'c': 1})
same = sankey_flow([{'id': 'a', 'column': 0}, {'id': 'b', 'column': 0}, {'id': 'c', 'column': 1}], [{'source': 'a', 'target': 'b', 'value': 1}, {'source': 'a', 'target': 'c', 'value': 1}])['sankey_flow']; ok('sankey: a link between two nodes in the same column is dropped and noted', len(same['links']) == 1 and any('left to right' in x for x in same['notes']))
gap = sankey_flow([{'id': 'a', 'column': 0}, {'id': 'b', 'column': 9}], [{'source': 'a', 'target': 'b', 'value': 1}])['sankey_flow']; ok('sankey: empty columns are collapsed (hints 0 and 9 give 2 columns)', gap['columns'] == 2)
rn = sankey_flow(ND + [{'id': 'a'}, {'label': 'x'}, 'junk', {'id': 'orphan'}], LK + [{'source': 'a', 'target': 'zz', 'value': 1}, {'source': 'a', 'target': 'a', 'value': 1}, {'source': 'a', 'target': 'b', 'value': 0}, {'source': 'a', 'target': 'b', 'value': -2}, 'x'])['sankey_flow']
ok('sankey: bad nodes and links dropped and counted; orphan left out', any('3 nodes were left out' in x for x in rn['notes']) and any('5 links were dropped' in x for x in rn['notes']) and any('1 nodes with no drawn flow' in x for x in rn['notes']) and len(rn['nodes']) == 6)
ok('sankey: custom colours noted, PAL colours used', any('Custom colours' in x for x in sankey_flow([{'id': 'a', 'color': '#ff0000'}, {'id': 'b'}], [{'source': 'a', 'target': 'b', 'value': 1}])['sankey_flow']['notes']) and set(re.findall(r'fill="(#[0-9a-f]{6})"', sk['svg'])) <= set(CM.PAL) | {CM.FACE, CM.INK, CM.MUTED})
ok('sankey: nothing drawable refused', raises(lambda: sankey_flow(ND, [])) and raises(lambda: sankey_flow([], LK)) and raises(lambda: sankey_flow('x', LK)))
ok('sankey: table lists every node and flow with values', all(s in sk['table'] for s in ('A (column 1, in 0, out 15)', 'F (column 4, in 9, out 0)', 'A to B 10', 'E to F 9')))
ok('sankey: more than 30 nodes cut and noted', any('beyond the 30th' in x for x in sankey_flow([{'id': str(i)} for i in range(32)], [{'source': '0', 'target': '1', 'value': 1}])['sankey_flow']['notes']))
ok('sankey: markup in labels stays well-formed', wf(sankey_flow([{'id': 'a', 'label': '<x>&"'}, {'id': 'b'}], [{'source': 'a', 'target': 'b', 'value': 1}])['sankey_flow']))
ok('sankey: well-formed, deterministic, small', wf(sk) and sankey_flow(ND, LK, title='T')['sankey_flow']['svg'] == sk['svg'] and len(sk['svg']) < 60_000)
rng = random.Random(9); good = True
for _ in range(25):
    cn = rng.randint(2, 5); nd = [{'id': f'n{i}'} for i in range(rng.randint(4, 12))]; lk = [{'source': f'n{rng.randrange(len(nd))}', 'target': f'n{rng.randrange(len(nd))}', 'value': rng.choice([1, 2, 3.5, 8])} for _ in range(rng.randint(3, 25))]
    try: z = sankey_flow(nd, lk)['sankey_flow']
    except ValueError: continue
    P = {x['id']: x for x in z['nodes']}
    good = good and all(close(x['h'], max(x['in'], x['out']) * z['k']) for x in z['nodes']) and all(P[l['source']]['col'] < P[l['target']]['col'] for l in z['links']) and all(P[l['source']]['y'] - 1e-6 <= l['sy0'] and l['sy1'] <= P[l['source']]['y'] + P[l['source']]['h'] + 1e-6 for l in z['links']) and all(0 <= x['y'] and x['y'] + x['h'] <= CM.H + 1e-6 for x in z['nodes'])
ok('sankey: invariants hold on 25 random graphs', good)
# ---------- INVERSE-READ ORACLES: parse the drawn SVG back into data and compare with values computed here, from the input alone
def root_of(r): return ET.fromstring(r['svg'])
def fnum(s): return float(s.replace(',', '').replace('%', ''))
def tick_map(pairs):
    """pairs = [(pixel, value)] from axis ticks -> function pixel -> value (needs two distinct ticks); also returns the max residual of the fit."""
    (p0, v0), (p1, v1) = pairs[0], pairs[-1]; f = lambda p: v0 + (p - p0) * (v1 - v0) / (p1 - p0); return f, max(abs(f(p) - v) for p, v in pairs)
def wf_read(r):
    rt = root_of(r); rects = [e for e in rt.iter(NSV + 'rect')]; bars = [e for e in rects if e.get('y') != '9' and e.get('rx') != '24']
    vlines = [(float(e.get('x1'))) for e in rt.iter(NSV + 'line') if e.get('x1') == e.get('x2') and e.get('stroke-dasharray') is None]; tx = [(float(e.get('x')), e.text) for e in rt.iter(NSV + 'text') if e.get('text-anchor') == 'middle']
    pairs = sorted((x, fnum(t)) for x in vlines for xx, t in tx if abs(xx - x) < .01 and re.fullmatch(r'-?[\d,.]+', t)); f, resid = tick_map(pairs)
    rows = [(f(float(b.get('x'))), f(float(b.get('x')) + float(b.get('width'))), b.get('fill')) for b in bars]
    vals = [e.text for e in rt.iter(NSV + 'text') if e.get('font-weight') == '700']; conn = [float(e.get('x1')) for e in rt.iter(NSV + 'line') if e.get('stroke-dasharray')]
    return rows, vals, resid, [f(c) for c in conn]
def wf_expect(steps):
    out = []; lvl = 0
    for s in steps:
        if s.get('kind') == 'total':
            if 'value' in s: lvl = s['value']
            out.append((0, lvl, 'total', lvl))
        else: out.append((lvl, lvl + s['value'], 'inc' if s['value'] >= 0 else 'dec', s['value'])); lvl += s['value']
    return out
WCOL = {'inc': CM.PAL[4], 'dec': CM.PAL[3], 'total': CM.PAL[0]}
def wf_check(steps, unit=''):
    r = waterfall(steps, unit=unit)['waterfall']; rows, vals, resid, conn = wf_read(r); ex = wf_expect(steps); tol = max(1e-6, 1e-4 * max(abs(b) + abs(a) for a, b, _, _ in ex))
    good = len(rows) == len(ex) and resid <= tol and all((a == b or (abs(min(a, b) - min(ra, rb)) <= tol * 3 and abs(max(a, b) - max(ra, rb)) <= tol * 3)) and col == WCOL[k] for (a, b, k, _), (ra, rb, col) in zip(ex, rows))
    txt = [(('+' if v >= 0 else '-') + f'{abs(v):,.6f}'.rstrip('0').rstrip('.') if k != 'total' else f'{v:,.6f}'.rstrip('0').rstrip('.')) + (f' {unit}' if unit else '') for a, b, k, v in ex]
    return good, vals == txt
g, t_ = wf_check([{'label': 'Start', 'kind': 'total', 'value': 100}, {'label': 'a', 'value': 40}, {'label': 'b', 'value': -25.5}, {'kind': 'total'}, {'value': -10}, {'kind': 'total'}], 'k')
ok('waterfall read-back: every bar starts and ends where the cumulative sum says, in the right colour (inverse of the drawn axis)', g); ok('waterfall read-back: the printed signed values are exactly the steps', t_)
g, t_ = wf_check([{'value': -30}, {'value': 10}, {'value': 45.25}, {'kind': 'total', 'value': 5}, {'value': 0.5}]); ok('waterfall read-back: negative running levels and a reset total are drawn where they belong', g); ok('waterfall read-back: printed values with decimals', t_)
rng = random.Random(11); good = True
for _ in range(20):
    st = [{'value': rng.choice([-40, -7.5, 3, 12, 60, 100])} if rng.random() < .75 else {'kind': 'total'} for _ in range(rng.randint(2, 9))]; g, t_ = wf_check(st); good = good and g and t_
ok('waterfall read-back: 20 random step lists (colour, position, scale, printed values)', good)
_r, _v, _res, cn = wf_read(waterfall([{'value': 10}, {'value': 5}, {'kind': 'total'}])['waterfall']); ok('waterfall read-back: dashed connectors sit at the running level, including the one into a total', len(cn) == 2 and abs(cn[0] - 10) < 1e-4 and abs(cn[1] - 15) < 1e-4)
_r, _v, _res, cn = wf_read(waterfall([{'value': 10}, {'kind': 'total', 'value': 50}])['waterfall']); ok('waterfall read-back: no connector into a total that resets the level', cn == [])
def nice_top(t):
    raw = t / 5; mag = 10 ** math.floor(math.log10(raw)); step = next(c * mag for c in (1, 2, 5, 10) if c * mag >= raw - 1e-12); return step, math.ceil(t / step - 1e-9) * step
def sa_read(r):
    rt = root_of(r); polys = [(e.get('fill'), [tuple(map(float, p.split(','))) for p in e.get('points').split()]) for e in rt.iter(NSV + 'polygon')]
    grid = sorted(float(e.get('y1')) for e in rt.iter(NSV + 'line') if e.get('y1') == e.get('y2')); lab = [(float(e.get('y')) - 5, e.text) for e in rt.iter(NSV + 'text') if e.get('text-anchor') == 'end' and re.fullmatch(r'-?[\d,.]+%?', e.text or '')]
    pairs = sorted((y, fnum(t)) for y in grid for ly, t in lab if abs(ly - y) < .01); return polys, pairs
SA_D = [[1, 4, 2, 6], [3, 1, 5, 2], [2, 2, 2, 2]]; SA_S = [{'label': n_, 'data': d_} for n_, d_ in zip('xyz', SA_D)]; saR = stacked_area(LB, SA_S); tot_ = [sum(c) for c in zip(*SA_D)]
polys, pairs = sa_read(saR['none']); f, resid = tick_map(pairs); m_ = 4; cum = [[0] * 4]
for d_ in SA_D: cum.append([a + b for a, b in zip(cum[-1], d_)])
ok('stacked_area read-back (none): every polygon top and bottom edge, mapped through the drawn axis, is the cumulative sum', len(polys) == 3 and resid < 1e-6 and all(abs(f(polys[i][1][j][1]) - cum[i + 1][j]) < 1e-6 and abs(f(polys[i][1][2 * m_ - 1 - j][1]) - cum[i][j]) < 1e-6 for i in range(3) for j in range(m_)))
ok('stacked_area read-back (none): the top tick is the nice ceiling of the largest total (axis and data agree)', abs(max(p_[1] for p_ in pairs) - nice_top(max(tot_))[1]) < 1e-9 and min(p_[1] for p_ in pairs) == 0 and abs(f(polys[2][1][1][1]) - tot_[1]) < 1e-6)
ok('stacked_area read-back: layer colours are PAL in input order, x spacing is even', [p[0] for p in polys] == CM.PAL[:3] and all(abs((polys[0][1][j + 1][0] - polys[0][1][j][0]) - (polys[0][1][1][0] - polys[0][1][0][0])) < .02 for j in range(3)))
polys, pairs = sa_read(saR['expand']); f, resid = tick_map(pairs); ok('stacked_area read-back (expand): axis 0 to 1, every layer edge is the cumulative share', sorted(p[1] for p in pairs) == [0, 25, 50, 75, 100] and all(abs(f(polys[i][1][j][1]) / 100 - cum[i + 1][j] / tot_[j]) < 1e-6 for i in range(3) for j in range(m_)))
for off in ('silhouette', 'wiggle'):
    polys, _ = sa_read(saR[off]); lay = stack([[SA_D[i][j] for i in range(3)] for j in range(4)], off); top0 = [polys[i][1][j][1] for i in range(3) for j in range(m_)]
    pix = lambda i, j, e: polys[i][1][j][1] if e == 1 else polys[i][1][2 * m_ - 1 - j][1]; s_ = (pix(0, 0, 0) - pix(2, 0, 1)) / tot_[0] if off == 'silhouette' else None
    thick = [[pix(i, j, 0) - pix(i, j, 1) for i in range(3)] for j in range(m_)]; unit_px = sum(thick[0]) / tot_[0]
    ok(f'stacked_area read-back ({off}): drawn thickness of every layer is its value (one pixel scale)', all(abs(thick[j][i] - SA_D[i][j] * unit_px) < .05 for i in range(3) for j in range(m_)))
    ok(f'stacked_area read-back ({off}): drawn baseline follows the {off} offset (hand-checked stack())', all(abs((pix(i, 0, 0) - pix(i, j, 0)) - (lay[i][0][j] - lay[i][0][0]) * unit_px) < .05 for i in range(3) for j in range(m_)))
polys, _ = sa_read(saR['silhouette']); mids = [(polys[2][1][j][1] + polys[0][1][2 * m_ - 1 - j][1]) / 2 for j in range(m_)]; ok('stacked_area read-back (silhouette): the stack is centred on one horizontal line', max(mids) - min(mids) < .02)
rt = root_of(saR['none']); ok('stacked_area read-back: legend names every series and the x labels are the labels', {e.text for e in rt.iter(NSV + 'text')} >= {'x', 'y', 'z', 'a', 'b', 'c', 'd'})
rt = root_of(stacked_area(['a' * 30, 'b'], [{'label': 'S' * 30, 'data': [1, 2]}])['none']); ok('stacked_area: long labels are shortened in the drawing and counted in a note, the table keeps them in full', stacked_area(['a' * 30, 'b'], [{'label': 'S' * 30, 'data': [1, 2]}])['none']['notes'] and 'a' * 30 in stacked_area(['a' * 30, 'b'], [{'label': 'S' * 30, 'data': [1, 2]}])['none']['table'] and all(len(e.text or '') <= 16 for e in rt.iter(NSV + 'text')))
ok('stacked_area: alt text and aria-label name the series and the range', 'x, y, z' in saR['none']['alt'] and 'a to d' in saR['none']['alt'] and 'x, y, z' in root_of(saR['none']).get('aria-label') and 'a to d' in root_of(saR['none']).get('aria-label'))
# swimlane oracle
def sw_read(r):
    rt = root_of(r); rects = list(rt.iter(NSV + 'rect')); heads = [(float(e.get('y')), float(e.get('height'))) for e in rects if e.get('x') == '8' and e.get('width') == '116']; cards = [e for e in rects if e.get('rx') == '10']
    texts = [(float(e.get('x')), float(e.get('y')), e.text, e.get('text-anchor'), e.get('font-weight')) for e in rt.iter(NSV + 'text')]
    phases = [(x, t) for x, y, t, a, w in texts if y == 34 and w == '700']; roles = [(y, t) for x, y, t, a, w in texts if x == 66 and a == 'middle']
    out = []
    for c in cards:
        cx, cy, cw, ch = (float(c.get(k)) for k in ('x', 'y', 'width', 'height')); inside = [(y, x, t, a, w) for x, y, t, a, w in texts if cx <= x <= cx + cw and cy <= y <= cy + ch]; inside.sort()
        num = [t for y, x, t, a, w in inside if a == 'middle' and w == '700'][0]; body = ' '.join(t for y, x, t, a, w in inside if a == 'start')
        ph = min(phases, key=lambda p: abs(p[0] - (cx + cw / 2)))[1]; hi = next(i for i, (hy, hh) in enumerate(heads) if hy <= cy + ch / 2 <= hy + hh); ro = ' '.join(t for y, t in roles if heads[hi][0] <= y <= heads[hi][0] + heads[hi][1])
        out.append((int(num), ro, ph, body))
    return sorted(out)
SWT = [{'role': 'Sec', 'phase': 'One', 'task': 'Rate the severity of the report'}, {'role': 'Eng', 'phase': 'One', 'task': 'second'}, {'role': 'Eng', 'phase': 'Two', 'task': 'third one here'}, {'role': 'QA', 'phase': 'Three', 'task': 'x ' * 29 + 'y'}, {'role': 'Eng', 'phase': 'Two', 'task': 'fifth'}]
exp = sorted((i + 1, t['role'], t['phase'], t['task'][:60].strip()) for i, t in enumerate(SWT)); got = sw_read(swimlane(RO, PH, SWT)['swimlane'])
ok('swimlane read-back: each card carries its number, sits in its role row and phase column, and shows its full task text (60 chars)', got == exp)
ok('swimlane read-back: a 100 character task is read back as exactly its first 60 characters', sw_read(swimlane(RO, PH, [{'role': 'Sec', 'phase': 'One', 'task': ('word ' * 20)}])['swimlane'])[0][3] == ('word ' * 20)[:60].strip())
ok('swimlane read-back: numbers follow the usable-task order after a drop', [g[0] for g in sw_read(swimlane(RO, PH, [{'role': 'Nobody', 'phase': 'One', 'task': 'a'}, {'role': 'Sec', 'phase': 'One', 'task': 'b'}, {'role': 'QA', 'phase': 'Two', 'task': 'c'}])['swimlane'])] == [1, 2])
ok('swimlane: a long task is shortened inside its card and the note says so', any('shortened' in x for x in swimlane(RO, PH, [{'role': 'Sec', 'phase': 'One', 'task': 'supercalifragilisticexpialidocious ' * 2}])['swimlane']['notes']))
# sankey oracle
def sk_read(r):
    rt = root_of(r); rects = [e for e in rt.iter(NSV + 'rect') if e.get('width') == '16']; nodes = {}
    for e in rects: t = e.find(NSV + 'title').text; nm, v = t.rsplit(': ', 1); nodes[nm] = (float(e.get('x')), float(e.get('y')), float(e.get('height')), fnum(v))
    links = []
    for e in rt.iter(NSV + 'path'):
        t = e.find(NSV + 'title').text; nm, v = t.rsplit(': ', 1); a, b = nm.split(' to '); nums = [float(x) for x in re.findall(r'-?\d+\.?\d*', e.get('d'))]; links.append((a, b, fnum(v), nums))
    return nodes, links
nodes_, links_ = sk_read(sk); kk = [ (n_[2] - n_[1]) / n_[3] for l in links_ for n_ in [(0, l[3][1], l[3][1] + (l[3][15] - l[3][1]), l[2])]]
ok('sankey read-back: every ribbon has the same thickness at both ends and one scale k = thickness / value', all(abs((l[3][15] - l[3][1]) - (l[3][9] - l[3][5])) < .02 for l in links_) and len({round((l[3][15] - l[3][1]) / l[2], 2) for l in links_}) == 1)
KS = (links_[0][3][15] - links_[0][3][1]) / links_[0][2]; EXP_V = {'A': 15, 'B': 10, 'C': 5, 'D': 6, 'E': 9, 'F': 9}
ok('sankey read-back: node height = max(in, out) x k for every node (values computed here from the input)', all(abs(nodes_[nm][2] - EXP_V[nm] * KS) < .02 and abs(nodes_[nm][3] - EXP_V[nm]) < 1e-9 for nm in EXP_V))
ok('sankey read-back: the tightest column fills the drawing height (488 px) with 27 px gaps (text 23 px + 4, four columns)', abs(max(sum(nodes_[nm][2] for nm in col_) + 27 * (len(col_) - 1) for col_ in (['A'], ['B', 'C'], ['E'], ['D', 'F'])) - 488) < .1)
ok('sankey read-back: each ribbon starts at the right edge of its source node and ends at the left edge of its target, inside both', all(abs(l[3][0] - (nodes_[l[0]][0] + 16)) < .01 and abs(l[3][6] - nodes_[l[1]][0]) < .01 and nodes_[l[0]][1] - .01 <= l[3][1] and l[3][15] <= nodes_[l[0]][1] + nodes_[l[0]][2] + .01 and nodes_[l[1]][1] - .01 <= l[3][5] and l[3][9] <= nodes_[l[1]][1] + nodes_[l[1]][2] + .01 for l in links_))
ok('sankey read-back: printed flow values are the input values', sorted((l[0], l[1], l[2]) for l in links_) == sorted((a.upper(), b.upper(), float(v)) for a, b, v in (('a', 'b', 10), ('a', 'c', 5), ('b', 'd', 6), ('b', 'e', 4), ('c', 'e', 5), ('e', 'f', 9))))
ok('sankey read-back: columns by x: A | B,C | E | D,F', nodes_['B'][0] == nodes_['C'][0] and nodes_['D'][0] == nodes_['F'][0] and nodes_['A'][0] < nodes_['B'][0] < nodes_['E'][0] < nodes_['D'][0])
wide = sankey_flow(ND, LK)['sankey_flow']; ok('sankey: four columns are 220 px per column wider than two (720 + 2 x 220 = 1160)', wide['width'] == 1160 and root_of(wide).get('width') == '1160' and sankey_flow([{'id': 'a'}, {'id': 'b'}], [{'source': 'a', 'target': 'b', 'value': 1}])['sankey_flow']['width'] == 720)
ok('sankey: dropped cyclic and backward flows are named in the notes', any('cycle' in x and 'F to A' in x for x in cyc['notes']) and any('left to right' in x and 'b to c' in x for x in hint['notes']))
ok('sankey: keyed is accepted and noted as not supported', any('keyed' in x for x in sankey_flow(ND, LK, keyed=True)['sankey_flow']['notes']) and not any('keyed' in x for x in sk['notes']))
# calendar oracle is in tests/test_pack.py (heatmap_calendar section)
# ---------- negative controls: hostile numbers and types must give a drawing with a note or a clean ValueError, never another exception
BIG = 10 ** 400; NAN = float('nan'); INF = float('inf')
def survives(fn, **kw):
    try: res_ = fn(**kw)
    except ValueError: return True
    except Exception as e_: print('   crash:', fn.__name__, type(e_).__name__, str(e_)[:80]); return False
    return all(wf(v) for k_, v in res_.items() if k_ != '_default')
HOST = [(waterfall, dict(steps=[{'label': BIG, 'value': BIG}, {'value': NAN}, {'value': INF}, {'value': 1e308}, {'value': 5}], title=BIG, unit=BIG, x_label=BIG, version=BIG)), (waterfall, dict(steps=[{'label': ['a'], 'value': {'x': 1}, 'kind': ['total']}, None, 3])),
        (stacked_area, dict(labels=['a', 'b'], series=[{'data': [1e308, 1]}, {'data': [BIG, NAN]}], title=BIG)), (stacked_area, dict(labels=['a', 'b'], series=[{'data': [1, 2]}], offset=[1])), (stacked_area, dict(labels=['a', 'b'], series=[{'data': [1, 2]}], offset={})),
        (stacked_area, dict(labels=['a', 'b'], series=[{'data': [1, 2]}], layout=[1], offset=BIG)), (stacked_area, dict(labels=[BIG, {'x': 1}, ['b']], series=[{'label': BIG, 'data': [1, 2, 3]}])),
        (swimlane, dict(roles=[BIG, {'a': 1}, ['x'], 'Q'], phases=['p', 'q'], tasks=[{'role': BIG, 'phase': 'p', 'task': BIG}, {'role': ['x'], 'phase': {}, 'task': 1}])), (swimlane, dict(roles=['a', 'b'], phases=['p', 'q'], tasks=[{'role': 'a', 'phase': 'p', 'task': 'x'}], title=BIG)),
        (sankey_flow, dict(nodes=[{'id': 'a'}, {'id': 'b'}], links=[{'source': {'x': 1}, 'target': 'b', 'value': 1}])), (sankey_flow, dict(nodes=[{'id': ['a']}, {'id': 'b'}, {'id': 'c'}], links=[{'source': 'b', 'target': ['c'], 'value': 1}, {'source': 'b', 'target': 'c', 'value': 1}])),
        (sankey_flow, dict(nodes=[{'id': 'a'}, {'id': 'b'}, {'id': 'c'}], links=[{'source': 'a', 'target': 'b', 'value': 1e308}, {'source': 'b', 'target': 'c', 'value': 1e308}, {'source': 'a', 'target': 'c', 'value': BIG}, {'source': 'a', 'target': 'c', 'value': NAN}])),
        (sankey_flow, dict(nodes=[{'id': 'a', 'column': BIG}, {'id': 'b', 'column': NAN}, {'id': BIG}], links=[{'source': 'a', 'target': 'b', 'value': 5e-324}, {'source': 'a', 'target': 'b', 'value': 1e12}, {'source': BIG, 'target': 'b', 'value': 1}], title=BIG, keyed=BIG, version=BIG)),
        (sankey_flow, dict(nodes=[{'id': i} for i in 'abc'], links=[{'source': 'a', 'target': 'b', 'value': 1e12}, {'source': 'b', 'target': 'c', 'value': 1e12}, {'source': 'a', 'target': 'c', 'value': 1e12}]))]
ok('negative controls: 10**400, NaN, inf, 1e308, dict and list ids, offset=[1] never raise anything but ValueError (and drawings stay well-formed)', all(survives(fn, **kw) for fn, kw in HOST))
ok('negative control: sankey with a dict link source drops it and notes it', any('dropped' in x for x in sankey_flow([{'id': 'a'}, {'id': 'b'}, {'id': 'c'}], [{'source': {'x': 1}, 'target': 'b', 'value': 1}, {'source': 'a', 'target': 'b', 'value': 1}])['sankey_flow']['notes']))
ok('negative control: sankey with 1e308 values drops them and refuses only when nothing is left', any('1e12' in x for x in sankey_flow([{'id': 'a'}, {'id': 'b'}, {'id': 'c'}], [{'source': 'a', 'target': 'b', 'value': 1e308}, {'source': 'b', 'target': 'c', 'value': 1}])['sankey_flow']['notes']) and raises(lambda: sankey_flow([{'id': 'a'}, {'id': 'b'}], [{'source': 'a', 'target': 'b', 'value': 1e308}])))
ok('negative control: stacked_area offset=[1] is noted and drawn as none', stacked_area(LB, SE, offset=[1])['_default'] == 'none' and any('not text' in x for x in stacked_area(LB, SE, offset=[1])['none']['notes']))
ok('negative control: stacked_area 1e308 and 10**400 cells are drawn as 0 and counted; all-invalid data gives a note-only result', any('drawn as 0' in x for x in stacked_area(LB, [{'data': [1e308, BIG, NAN, 4]}, {'data': [1, 1, 1, 1]}])['none']['notes']) and stacked_area(LB, [{'data': [1e308, BIG, NAN, 1e13]}])['none'].get('empty') is True)
ok('negative control: waterfall 10**400, NaN, inf and 1e13 steps are left out and counted', len(waterfall([{'value': BIG}, {'value': NAN}, {'value': INF}, {'value': 1e13}, {'value': 7}])['waterfall']['bars']) == 1 and any('4 steps' in x for x in waterfall([{'value': BIG}, {'value': NAN}, {'value': INF}, {'value': 1e13}, {'value': 7}])['waterfall']['notes']))
ok('negative control: a title of 10**400 becomes empty instead of raising in every flow macro', all(survives(fn, **kw) for fn, kw in ((waterfall, dict(steps=[{'value': 1}], title=BIG)), (stacked_area, dict(labels=['a', 'b'], series=[{'data': [1, 2]}], title=BIG)), (swimlane, dict(roles=['a', 'b'], phases=['c', 'd'], tasks=[{'role': 'a', 'phase': 'c', 'task': 'x'}], title=BIG)), (sankey_flow, dict(nodes=[{'id': 'a'}, {'id': 'b'}], links=[{'source': 'a', 'target': 'b', 'value': 1}], title=BIG)))))
big12 = stacked_area([str(i) for i in range(60)], [{'label': f's{i}', 'data': [1 + (i * j) % 7 for j in range(60)]} for i in range(12)]); ok('stacked_area: 60 labels x 12 series draws within the output policy for all four offsets', all(len(v['svg']) < 80_000 for k_, v in big12.items() if k_ != '_default'))
manyw = waterfall([{'label': f'Step {i}', 'value': i - 12.5} for i in range(30)])['waterfall']; ok('waterfall: 24 rows draw inside the policy and the cut is noted', len(manyw['bars']) == 24 and any('24th' in x for x in manyw['notes']))
# ---------- shared: text size, XML escape, A2UI validation
for name, params in DEMOS.items():
    r_ = PACK_FLOW[name](**params); first = r_[r_['_default']]
    ok(f'{name}: text is at least 14px', all(int(x) >= 14 for x in re.findall(r'font-size="(\d+)"', first['svg'])))
    ok(f'{name}: alt text is the summary, the demo draws without notes', not first['notes'] and first['summary'] in first['alt'] and first['alt'].startswith(name.replace('_', ' ').capitalize()))
    strs = []
    def walk(o, k=None):
        if isinstance(o, dict): [walk(v, kk) for kk, v in o.items()]
        elif isinstance(o, list): [walk(v, k) for v in o]
        elif isinstance(o, str) and k in ('label', 'task', 'role', 'phase'): strs.append(o)
    walk(params); ok(f'{name}: every label of the demo is in the table text', all(s in first['table'] for s in strs))
    ok(f'{name}: SVG under 60 KB', all(len(v['svg']) < 60_000 for k_, v in r_.items() if k_ != '_default'))
    default = r_.pop('_default'); create, updates = atom_card('T', r_, default)
    ok(f'{name}: createSurface validates', not list(A2R.iter_errors(create))); ok(f'{name}: every update validates', all(not list(A2R.iter_errors(u)) for u in updates.values()))
    ok(f'{name}: only Basic components', {c['component'] for c in create['createSurface']['components']} <= {'Card', 'Column', 'Row', 'Text', 'Image', 'Button'})
    ok(f'{name}: payload under 200 KB', len(json.dumps(create)) < 200_000)
    b1 = copy.deepcopy(create); b1['version'] = 'v1.0'; ok(f'{name}: negative: bad version rejected', bool(list(A2R.iter_errors(b1))))
    b2 = copy.deepcopy(create); b2['createSurface']['components'][2]['component'] = 'Chart'; ok(f'{name}: negative: unknown component rejected', bool(list(A2R.iter_errors(b2))))
print(f'flow tests: {n} checks, {bad} failed'); sys.exit(1 if bad else 0)
