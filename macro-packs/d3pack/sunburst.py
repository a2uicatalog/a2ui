"""sunburst macro: same contract as the sunburst atom (items [{path (0 to 3 strings), name, value}], layout radial|icicle, unit, title, version). Returns {layout: Result}.
Layout re-implemented like d3 partition(): at every level the children divide their parent's span in proportion to value, largest first (ties keep input order).
With fewer than 2 usable items a note replaces the chart (Result['note_only'])."""
import math
from .common import *
from .treemap import txt, read_value, usable_path, common_notes, note_result, render, tip, ell
def _items(items, notes, cnt):
    if not isinstance(items, list): raise ValueError('items must be a list')
    if len(items) > 40: notes.append(f'{len(items) - 40} items beyond the 40th were not drawn.'); items = items[:40]
    out = []
    for n, it in enumerate(items, 1):
        v = read_value(it.get('value'), cnt) if isinstance(it, dict) else None
        if v is None: cnt['dropped'] += 1; continue
        out.append({'path': usable_path(it.get('path')) or [], 'name': txt(it.get('name'), 24) or f'Item {n}', 'value': v})
    return out
def build_tree(items):
    root = {'name': '', 'children': {}, 'leaves': [], 'value': 0.0}
    for it in items:
        node = root
        for seg in it['path']: node = node['children'].setdefault(seg, {'name': seg, 'children': {}, 'leaves': [], 'value': 0.0})
        node['leaves'].append(it)
    def total(nd): nd['value'] = sum(l['value'] for l in nd['leaves']) + sum(total(c) for c in nd['children'].values()); return nd['value']
    total(root); return root
def layout_tree(nd):
    """Returns records (in drawing order) with start/end fractions of the whole (0..1). Children of a node divide its span in proportion to value, largest first."""
    recs = []
    def rec(node, depth, f0, f1, top):
        span = f1 - f0; cur = f0
        kids = sorted([('g', c) for c in node['children'].values()] + [('l', l) for l in node['leaves']], key=lambda kc: -kc[1]['value'])
        for kind, c in kids:
            v = c['value']; frac = span * v / node['value']
            r = {'name': c['name'], 'value': v, 'depth': depth, 'f0': cur, 'f1': cur + frac, 'leaf': kind == 'l', 'path': list(node.get('_path', []))}
            r['top'] = top if depth else sum(1 for x in recs if x['depth'] == 0); recs.append(r)
            if kind == 'g': c['_path'] = r['path'] + [c['name']]; rec(c, depth + 1, cur, cur + frac, r['top'])
            cur += frac
    rec(nd, 0, 0.0, 1.0, None); return recs
def sunburst(items, layout='radial', unit='', title='', version=1):
    notes = []; cnt = {'dropped': 0, 'clamped': 0}; u = txt(unit, 12) or ''; ttl = txt(title, 80) or ''
    if layout not in ('radial', 'icicle'): layout = 'radial'
    items = _items(items, notes, cnt); common_notes(notes, cnt, version)
    if len(items) < 2: return {layout: note_result('sunburst', ttl, 'A sunburst needs at least 2 usable items, so no chart is drawn.', notes), '_default': layout}
    root = build_tree(items); recs = layout_tree(root); total = root['value']; maxd = max(r['depth'] for r in recs) + 1; us = (' ' + u) if u else ''
    tab = '; '.join(('/'.join(it['path']) + '/' if it['path'] else '') + f"{it['name']} {fmt(it['value'])}{us} ({100 * it['value'] / total:.1f}%)" for it in items)
    tops = [r for r in recs if r['depth'] == 0]; big = max(tops, key=lambda r: r['value'])
    summary = f"Total {fmt(total)}{us} in {len(items)} items and {len(tops)} top-level groups; the largest group is {big['name']} ({fmt(big['value'])}, {100 * big['value'] / total:.0f}%)."
    out = {}
    for lay in ('radial', 'icicle'):
        def draw(titles):
            body = ''
            if lay == 'radial':
                cx, cy, R0, R = W / 2, H / 2, 70, 235; rw = (R - R0) / maxd
                for r in recs:
                    a0, a1 = r['f0'] * 2 * math.pi, r['f1'] * 2 * math.pi; col = blend(PAL[r['top'] % len(PAL)], .22 * r['depth'])
                    body += f'<path d="{arc_path(cx, cy, R0 + r["depth"] * rw, R0 + (r["depth"] + 1) * rw - 2, a0, a1)}" fill="{col}" stroke="#ffffff" stroke-width="2">{tip(titles, "/".join(r["path"] + [r["name"]]) + ": " + fmt(r["value"]) + us + " (" + format(100 * r["value"] / total, ".1f") + "%)")}</path>'
                    mid = (a0 + a1) / 2; rm = R0 + (r['depth'] + .5) * rw
                    if (a1 - a0) * rm >= 62: body += label(cx + rm * math.sin(mid), cy - rm * math.cos(mid) + 6, ell(r['name'], max(3, int(rw / 8.6))), 16, fill=text_on(col), weight=600)
                body += label(cx, cy - 4, fmt(total), 28, weight=700) + label(cx, cy + 22, u or 'total', 16, fill=MUTED)
            else:
                x0, y0, w, h = 30, 40, W - 60, H - 80; cw = w / maxd
                for r in recs:
                    col = blend(PAL[r['top'] % len(PAL)], .22 * r['depth']); y = y0 + r['f0'] * h; hh = (r['f1'] - r['f0']) * h - 2
                    body += f'<rect x="{x0 + r["depth"] * cw:.2f}" y="{y:.2f}" width="{cw - 2:.2f}" height="{max(hh, 0):.2f}" fill="{col}">{tip(titles, "/".join(r["path"] + [r["name"]]) + ": " + fmt(r["value"]) + us)}</rect>'
                    if hh >= 22: body += label(x0 + r['depth'] * cw + 10, y + hh / 2 + 6, f"{ell(r['name'], 14)} {fmt(r['value'])}", 16, 'start', text_on(col), 600)
            return body
        out[lay] = render('sunburst', ttl, 'Sunburst', draw, summary, tab, notes, u); out[lay]['records'] = recs
    out['_default'] = layout; return out
