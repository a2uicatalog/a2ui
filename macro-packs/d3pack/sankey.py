"""sankey_flow macro. Contract source: atoms/schema.yaml: nodes [{id, label, column?, color?}] (column hint 0..15), links [{source, target, value, color?}],
title, keyed. Flows that close a cycle or would run backwards between columns are not drawn and are named in the notes. The chart is wider by 220 px per column beyond two (capped at 1600 px wide; text
grows with the width so it stays about 14 px when the picture is shown at 720 px). `keyed` is accepted but NOT implemented: the pack's output policy (common.verify_svg) allows only integer data-* attributes, and the
atom's data-cb / data-key values are text; a note says so and the drawing is the unkeyed one.
Layout rule (documented, not d3-sankey's iterative relaxation, so it is NOT pixel-identical): (1) links that close a cycle are dropped, taking links in input order; (2) a node's column is its `column`
hint (0..15), else its longest-path distance from the sources, and an unhinted node with no outgoing flow goes to the last column; (3) links that do not run strictly left to right are dropped and noted;
(4) nodes without any remaining link are dropped; used columns are renumbered 0..n-1; (5) node height = max(inflow, outflow) x k, one k for the whole chart, the largest that fits every column
(vertical padding max(18, text size + 4) px between nodes); (6) nodes keep input order inside a column, centred vertically; (7) on each node the outgoing ribbons are stacked in order of target y and the incoming
ones in order of source y (ties: input order); each ribbon is a cubic Bezier band of height value x k. Colours come from PAL by node order. Values must be finite, 1e-9 to 1e12 (others are dropped and counted).
Ids are strings or numbers (a dict, list or boolean id is not an id). Returns {'sankey_flow': Result}."""
from .common import *
from .waterfall import safe_text, fit_svg, fmt6
NW, TOP, BOT = 16, 16, 16
def _names(items, limit=5):
    t = ', '.join(items[:limit]); return t + (f' and {len(items) - limit} more' if len(items) > limit else '')
def sankey_flow(nodes, links, title='', version=1, keyed=False):
    notes = []; ttl = safe_text(title, 80, '') or ''
    if not isinstance(nodes, list) or not isinstance(links, list): raise ValueError('nodes and links must be lists')
    if len(nodes) > 30: notes.append(f'{len(nodes) - 30} nodes beyond the 30th were not drawn.'); nodes = nodes[:30]
    ns = []; seen = set(); bad = 0; custom = 0
    for nd in nodes:
        nid = ident(nd.get('id'), 40) if isinstance(nd, dict) else None
        if nid is None or nid in seen: bad += 1; continue
        seen.add(nid); c = finite(nd.get('column'), 0, 15); hint = int(c) if c is not None and c == int(c) else None
        custom += 1 if nd.get('color') else 0; ns.append({'id': nid, 'label': safe_text(nd.get('label'), 24, nid[:24]), 'hint': hint})
    if bad: notes.append(f'{bad} nodes were left out (no id, or a repeated id).')
    if len(links) > 80: notes.append(f'{len(links) - 80} links beyond the 80th were not drawn.'); links = links[:80]
    ls = []; bad = 0
    for l in links:
        s_, t_, v = (ident(l.get('source'), 40), ident(l.get('target'), 40), finite(l.get('value'), 1e-9, 1e12)) if isinstance(l, dict) else (None, None, None)
        if s_ not in seen or t_ not in seen or s_ == t_ or v is None: bad += 1; continue
        custom += 1 if l.get('color') else 0; ls.append({'source': s_, 'target': t_, 'value': v})
    if bad: notes.append(f'{bad} links were dropped (not an object, a self link, an id that is not a node, or a value outside 1e-9 to 1e12).')
    if custom: notes.append('Custom colours are not used; node colours come from the pack palette.')
    if keyed: notes.append('keyed is not supported by this macro (the output policy allows only numeric data attributes); the unkeyed drawing is shown.')
    if isinstance(version, int) and not isinstance(version, bool) and version > 1: notes.append(f'Contract version {min(version, 10**9)} is drawn as version 1.')
    lab = {n['id']: n['label'] for n in ns}
    # (1) cycles
    kept = []; adj = {}
    def reach(a, b):
        st = [a]; vis = {a}
        while st:
            x = st.pop()
            if x == b: return True
            for y in adj.get(x, ()):
                if y not in vis: vis.add(y); st.append(y)
        return False
    cyc = []
    for l in ls:
        if reach(l['target'], l['source']): cyc.append(f'{lab[l["source"]]} to {lab[l["target"]]}'); continue
        adj.setdefault(l['source'], []).append(l['target']); kept.append(l)
    if cyc: notes.append(f'{len(cyc)} flows that close a cycle were not drawn: {_names(cyc)}.')
    # (2) columns, in topological order
    preds = {n['id']: [] for n in ns}; outs = {n['id']: 0 for n in ns}
    for l in kept: preds[l['target']].append(l['source']); outs[l['source']] += 1
    col = {}; byid = {n['id']: n for n in ns}
    def colof(i):
        if i in col: return col[i]
        n = byid[i]; col[i] = n['hint'] if n['hint'] is not None else (max(colof(p) for p in preds[i]) + 1 if preds[i] else 0); return col[i]
    for n in ns: colof(n['id'])
    mx = max(col.values()) if col else 0
    for n in ns:
        if n['hint'] is None and outs[n['id']] == 0 and preds[n['id']]: col[n['id']] = mx
    back = [f'{lab[l["source"]]} to {lab[l["target"]]}' for l in kept if col[l['source']] >= col[l['target']]]; kept = [l for l in kept if col[l['source']] < col[l['target']]]
    if back: notes.append(f'{len(back)} flows that would not run left to right between columns were not drawn: {_names(back)}.')
    used = {x for l in kept for x in (l['source'], l['target'])}; unused = len([n for n in ns if n['id'] not in used])
    if unused: notes.append(f'{unused} nodes with no drawn flow were left out.')
    ns = [n for n in ns if n['id'] in used]
    if not kept: raise ValueError('a sankey needs at least 1 drawable flow')
    cs = sorted({col[n['id']] for n in ns}); ci = {c: i for i, c in enumerate(cs)}; nc = len(cs)
    for n in ns:
        n['col'] = ci[col[n['id']]]; n['in'] = sum(l['value'] for l in kept if l['target'] == n['id']); n['out'] = sum(l['value'] for l in kept if l['source'] == n['id']); n['value'] = max(n['in'], n['out'])
    Wd = min(1600, 720 + 220 * max(0, nc - 2)); fs = max(14, round(14 * Wd / 720)); PADY = max(18, fs + 4)
    avail = H - TOP - BOT; cols = [[n for n in ns if n['col'] == c] for c in range(nc)]
    k = min((avail - PADY * (len(c) - 1)) / sum(n['value'] for n in c) for c in cols)
    if not k > 0: raise ValueError('too many nodes in one column to fit')
    gap = (Wd - 2 * 20 - NW) / max(1, nc - 1)
    for c, cn in enumerate(cols):
        used_h = sum(n['value'] * k for n in cn) + PADY * (len(cn) - 1); y = TOP + (avail - used_h) / 2
        for n in cn: n['h'] = n['value'] * k; n['x'] = 20 + c * gap; n['y'] = y; y += n['h'] + PADY
    for i, n in enumerate(ns): n['color'] = PAL[i % 8]
    for l in kept: l['w'] = l['value'] * k
    pos = {n['id']: n for n in ns}; order = {id(l): i for i, l in enumerate(kept)}
    for n in ns:
        cy = n['y']
        for l in sorted([l for l in kept if l['source'] == n['id']], key=lambda l: (pos[l['target']]['y'], order[id(l)])): l['sy0'] = cy; l['sy1'] = cy + l['w']; cy += l['w']
        cy = n['y']
        for l in sorted([l for l in kept if l['target'] == n['id']], key=lambda l: (pos[l['source']]['y'], order[id(l)])): l['ty0'] = cy; l['ty1'] = cy + l['w']; cy += l['w']
    def draw(lvl):
        body = ''
        for l in kept:
            s, t = pos[l['source']], pos[l['target']]; x0, x1 = s['x'] + NW, t['x']; xm = (x0 + x1) / 2
            body += (f'<path d="M{x0:.2f},{l["sy0"]:.2f} C{xm:.2f},{l["sy0"]:.2f} {xm:.2f},{l["ty0"]:.2f} {x1:.2f},{l["ty0"]:.2f} L{x1:.2f},{l["ty1"]:.2f} C{xm:.2f},{l["ty1"]:.2f} {xm:.2f},{l["sy1"]:.2f} {x0:.2f},{l["sy1"]:.2f}Z" '
                     f'fill="{s["color"]}" fill-opacity=".45">' + (f'<title>{esc(s["label"])} to {esc(t["label"])}: {fmt6(l["value"])}</title>' if lvl == 0 else '') + '</path>')
        for n in ns:
            body += f'<rect x="{n["x"]:.2f}" y="{n["y"]:.2f}" width="{NW}" height="{max(n["h"], .5):.2f}" fill="{n["color"]}">' + (f'<title>{esc(n["label"])}: {fmt6(n["value"])}</title>' if lvl == 0 else '') + '</rect>'
            chars = 24 if nc == 2 else max(0, int((gap - NW - 10) / (fs * .55))); lb = n['label'][:chars]
            if lb and lvl < 2:
                last = n['col'] == nc - 1; body += label(n['x'] - 6 if last else n['x'] + NW + 6, n['y'] + n['h'] / 2 + fs / 3, lb, fs, 'end' if last else 'start', INK, 700, 'stroke="#ffffff" stroke-width="3" paint-order="stroke"')
        return svg(body, ('Sankey flow' + (': ' + ttl if ttl else '') + f', {len(ns)} nodes, {len(kept)} flows')[:280], Wd, H)
    big = max(kept, key=lambda l: l['value'])
    summary = f'{len(ns)} nodes in {nc} columns, {len(kept)} flows; the largest flow is {lab[big["source"]]} to {lab[big["target"]]} ({fmt6(big["value"])}).'
    tab = 'Nodes: ' + '; '.join(f'{n["label"]} (column {n["col"] + 1}, in {fmt6(n["in"])}, out {fmt6(n["out"])})' for n in ns) + '. Flows: ' + '; '.join(f'{lab[l["source"]]} to {lab[l["target"]]} {fmt6(l["value"])}' for l in kept)
    r = finish('sankey_flow', ttl, fit_svg(draw, notes), summary, tab, notes); r['nodes'] = ns; r['links'] = kept; r['k'] = k; r['columns'] = nc; r['width'] = Wd
    return {'sankey_flow': r, '_default': 'sankey_flow'}
