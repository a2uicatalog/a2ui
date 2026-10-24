"""Existing-style payloads for histogram, box_plot and treemap; their output must not change when the d3-variants options are absent."""
import json
from pathlib import Path

_F = Path(__file__).parent


def payloads():
    out = {}
    vals = [3, 4, 4, 5, 6, 7, 7, 7, 8, 9, 12, 15, 21, 22, 40]
    out['hist_basic'] = {'type': 'histogram', 'values': vals}
    out['hist_bins'] = {'type': 'histogram', 'values': vals, 'bins': 6, 'unit': 'ms', 'x_label': 'Latency', 'title': 'T'}
    out['hist_few'] = {'type': 'histogram', 'values': [1, 2, 3]}
    out['hist_junk'] = {'type': 'histogram', 'values': vals + ['x', None, True], 'version': 3}
    out['hist_ridge'] = {'type': 'histogram', 'layout': 'ridge', 'series': [{'label': 'A', 'values': vals}, {'label': 'B', 'values': [x * 2 for x in vals]}]}
    for k, c in json.loads((_F / 'box_plot_d3_golden.json').read_text())['golden'].items():
        out['box_' + k] = {'type': 'box_plot', 'groups': [{'label': 'G%d' % i, 'values': g} for i, g in enumerate(c['groups'])]}
    out['box_points'] = {'type': 'box_plot', 'show_points': True, 'unit': 'ms', 'groups': [{'label': 'A', 'values': vals}, {'label': 'B', 'values': vals[::-1][:9]}]}
    out['box_empty'] = {'type': 'box_plot', 'groups': [{'label': 'A', 'values': [1, 2]}]}
    for k, c in json.loads((_F / 'treemap_d3_golden.json').read_text()).items():
        out['tm_nest_' + k] = {'type': 'treemap', 'items': [{'path': ['Root'] if False else [], 'name': 'x', 'value': 1}] if False else []}
    out['tm_flat'] = {'type': 'treemap', 'items': [{'category': 'A' if i % 2 else 'B', 'name': 'n%d' % i, 'value': 10 + i} for i in range(16)]}
    out['tm_path'] = {'type': 'treemap', 'items': [{'path': ['Home', 'x'] if i % 2 else ['Work'], 'name': 'n%d' % i, 'value': 5 + i} for i in range(14)]}
    out['tm_small'] = {'type': 'treemap', 'items': [{'category': 'A', 'name': 'a', 'value': 3}, {'category': 'B', 'name': 'b', 'value': 4}], 'version': 2}
    return {k: v for k, v in out.items() if not k.startswith('tm_nest_')}
