"""arc_diagram macro: same contract as the arc_diagram atom (nodes [{id,label,group}], links [{source,target,value}], order input|group|degree, unit, title, version).
Nodes sit at even steps along one line (d3 scalePoint, padding 0.5); every link is a semicircle above the line; thickness 1 to 6 px by value (min to max; all links at 2 px when every value is
equal); an arc and its dot take the source node's group colour (ungrouped: slate); a legend names every group; node names hang below the line rotated 90 degrees (with 40 nodes at most the spacing is 16 px, enough for 14 px text, so every name is drawn; the atom thins names only in containers narrower than 720 px). The tables list every node (id, label, group, link count) and every link by label. Ids and groups are read with ident() (a
dict, list or boolean is not an id); link values with finite() (above 0). Fewer than 2 usable nodes gives a note-only Result. Returns {order: Result, '_default': order}."""
import math
from .common import *
from .waterfall import note_result
MARGIN, BASE, MAXN, MAXL = 40.0, 370, 40, 120
def arc_diagram(nodes, links=None, order='input', unit='', title='', version=1):
    notes = []; u = ident(unit, 12) or ''; ttl = ident(title, 80) or ''
    if isinstance(version, int) and not isinstance(version, bool) and version > 1: notes.append(f'Contract version {min(version, 10 ** 9)} is drawn as version 1.')
    def refuse(why): notes.append(why); return {'input': note_result('arc_diagram', ttl, why + ' Nothing was drawn.', notes), '_default': 'input'}
    if not isinstance(nodes, list): return refuse('The nodes were not a list.')
    if len(nodes) > MAXN: notes.append(f'{len(nodes) - MAXN} nodes beyond the {MAXN}th were not drawn.'); nodes = nodes[:MAXN]
    ns = []; seen = set(); dropped = 0
    for nd in nodes:
        nid = ident(nd.get('id'), 40) if isinstance(nd, dict) else None
        if nid is None or nid in seen: dropped += 1; continue
        seen.add(nid); ns.append({'id': nid, 'label': ident(nd.get('label'), 24) or nid[:24], 'group': ident(nd.get('group'), 20)})
    if dropped: notes.append(f'{dropped} nodes were left out (no id, or a repeated id).')
    if len(ns) < 2: return refuse('An arc diagram needs at least 2 usable nodes.')
    links = links if isinstance(links, list) else []
    if len(links) > MAXL: notes.append(f'{len(links) - MAXL} links beyond the {MAXL}th were not drawn.'); links = links[:MAXL]
    byid = {n['id']: n for n in ns}; ls = []; bad = 0
    for l in links:
        s = ident(l.get('source'), 40) if isinstance(l, dict) else None; t = ident(l.get('target'), 40) if isinstance(l, dict) else None
        if s not in byid or t not in byid or s == t: bad += 1; continue
        v = finite(l.get('value', 1), 0, 1.7e308)
        if v is None or v <= 0: bad += 1; continue
        ls.append((s, t, v))
    if bad: notes.append(f'{bad} links were dropped (not an object, a self link, an id that is not a node, or a value that is not a finite number above 0).')
    deg = {n['id']: 0 for n in ns}
    for s, t, v in ls: deg[s] += 1; deg[t] += 1
    groups = sorted({n['group'] for n in ns if n['group']}); gcol = {g: PAL[i % len(PAL)] for i, g in enumerate(groups)}
    col = lambda n: gcol.get(n['group'], MUTED)
    orders = {'input': list(ns), 'group': sorted(ns, key=lambda n: (n['group'] is not None, n['group'] or '', n['label'])), 'degree': sorted(ns, key=lambda n: -deg[n['id']])}
    un = (' ' + u) if u else ''; lab = lambda i: byid[i]['label']
    tab = ('Nodes: ' + '; '.join(f'{n["id"]} ({n["label"]}' + (f', group {n["group"]}' if n['group'] else '') + f', {deg[n["id"]]} links)' for n in ns) + '. Links: '
           + ('; '.join(f'{lab(s)} to {lab(t)} {fmt(v)}{un}' for s, t, v in ls) or 'no links'))
    top = max(ns, key=lambda n: deg[n['id']]); summary = f'{len(ns)} nodes, {len(ls)} links; the most connected node is {top["label"]} ({deg[top["id"]]} links).'
    vals = [v for _, _, v in ls]; vmin, vmax = (min(vals), max(vals)) if vals else (1, 1)
    width = lambda v: 2.0 if vmax == vmin else 1.0 + 5.0 * ((v - vmin) / (vmax - vmin))
    legend_items = [(g, gcol[g]) for g in groups] + ([('no group', MUTED)] if groups and any(n['group'] is None for n in ns) else [])
    out = {}; step = (W - 2 * MARGIN) / len(ns)
    for o, seq in orders.items():
        pos = {n['id']: MARGIN + step * (0.5 + i) for i, n in enumerate(seq)}; body = label(W / 2, 32, ttl, 20, weight=700) if ttl else ''
        body += f'<line x1="30" x2="{W-30}" y1="{BASE}" y2="{BASE}" stroke="#c9cde0" stroke-width="2"/>'
        for s, t, v in sorted(ls, key=lambda x: -abs(pos[x[0]] - pos[x[1]])):
            x0, x1 = sorted((pos[s], pos[t])); r = (x1 - x0) / 2
            body += (f'<path d="M{x0:.2f},{BASE} A{r:.2f},{r:.2f} 0 0 1 {x1:.2f},{BASE}" fill="none" stroke="{col(byid[s])}" stroke-opacity=".55" stroke-width="{width(v):.2f}">'
                     f'<title>{esc(lab(s))} to {esc(lab(t))}: {fmt(v)}{esc(un)}</title></path>')
        for i, n in enumerate(seq):
            x = pos[n['id']]; body += f'<circle cx="{x:.2f}" cy="{BASE}" r="6" fill="{col(n)}"><title>{esc(n["label"])}' + (f', group {esc(n["group"])}' if n['group'] else '') + f', {deg[n["id"]]} links</title></circle>'
            body += label(x + 5, BASE + 16, n['label'], 14, 'start', extra=f'transform="rotate(90 {x+5:.2f} {BASE+16})"')
        maxlab = max(len(n['label']) for n in seq); h = int(BASE + 16 + maxlab * 8.4 + 20 + (34 if legend_items else 0))
        if legend_items:
            x = 24
            for g, c in legend_items: body += f'<rect x="{x:.0f}" y="{h-30}" width="16" height="16" rx="3" fill="{c}"/>' + label(x + 22, h - 17, g, 14, 'start'); x += 40 + len(g) * 8.4
        out[o] = finish('arc_diagram', ttl, svg(body, 'Arc diagram', W, h), summary, tab, notes, u); out[o]['order'] = [n['id'] for n in seq]; out[o]['pos'] = pos; out[o]['size'] = (W, h); out[o]['base'] = BASE
    out['_default'] = order if isinstance(order, str) and order in orders else 'input'; return out
