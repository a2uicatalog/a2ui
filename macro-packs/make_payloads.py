"""Demo inputs for the d3pack macros (synthetic, no model). Run `python3 make_payloads.py` to write payloads.json and sizes.json next to this file."""
import json, sys; sys.dont_write_bytecode = True
import d3pack as D
DEMOS = {
 'sunburst': dict(items=[{'path': ['EU'], 'name': 'France', 'value': 40}, {'path': ['EU'], 'name': 'Germany', 'value': 30}, {'path': ['EU'], 'name': 'Spain', 'value': 14}, {'path': ['Asia', 'East'], 'name': 'Japan', 'value': 22}, {'path': ['Asia', 'East'], 'name': 'Korea', 'value': 11}, {'path': ['Asia', 'South'], 'name': 'India', 'value': 26}, {'path': ['Americas'], 'name': 'Brazil', 'value': 18}, {'path': ['Americas'], 'name': 'Canada', 'value': 9}, {'name': 'Other', 'value': 8}], unit='M'),
 'chord_diagram': dict(groups=['Compute', 'Storage', 'Network', 'AI'], matrix=[[0, 12, 6, 20], [4, 0, 8, 3], [2, 5, 0, 1], [18, 2, 0, 0]], unit='TB'),
 'arc_diagram': dict(nodes=[{'id': n, 'label': n, 'group': g} for n, g in (('api', 'core'), ('auth', 'core'), ('db', 'data'), ('cache', 'data'), ('web', 'edge'), ('cdn', 'edge'), ('queue', 'data'), ('worker', 'core'))], links=[{'source': 'web', 'target': 'api', 'value': 5}, {'source': 'api', 'target': 'auth', 'value': 3}, {'source': 'api', 'target': 'db', 'value': 8}, {'source': 'api', 'target': 'cache', 'value': 4}, {'source': 'cdn', 'target': 'web', 'value': 6}, {'source': 'api', 'target': 'queue', 'value': 2}, {'source': 'queue', 'target': 'worker', 'value': 2}, {'source': 'worker', 'target': 'db', 'value': 3}], unit='calls/s'),
 'heatmap_calendar': dict(data=[{'date': f'2026-{m:02d}-{d:02d}', 'count': (d * 7 + m * 3) % 11} for m in (9, 10, 11) for d in range(1, 29) if (d + m) % 3], months=3, unit='commits'),
 'circle_pack': dict(items=[{'path': ['Eng'], 'name': f'Team {c}', 'value': v} for c, v in zip('ABCDE', (34, 21, 13, 8, 5))] + [{'path': ['Sales'], 'name': f'Region {c}', 'value': v} for c, v in zip('XYZ', (28, 17, 9))] + [{'name': 'Ops', 'value': 12}], unit='people')}
ALL = {k: (k, p) for k, p in DEMOS.items()}
ALL.update(D._demos())
out = {}; sizes = {}
for k, (macro, p) in sorted(ALL.items()):
    c, u, r = D.card(macro, k.replace('_', ' ').title() + ' (synthetic data)', p); out[k] = {'create': c, 'updates': u}
    big = max(len(json.dumps(x)) for x in [c] + list(u.values())); sizes[k] = big
    print(f'{k:18} macro {macro:17} largest message {big:7} B   variants {list(u)}')
HERE = __import__('pathlib').Path(__file__).resolve().parent
json.dump(out, open(HERE / 'payloads.json', 'w'), separators=(',', ':')); json.dump(sizes, open(HERE / 'sizes.json', 'w'))
