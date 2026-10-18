"""Build catalogue blocks from a grounded graph. Each builder returns (block, elements): the block for the renderer
and, for the provenance check, every element it drew with the slot ids it rests on. Builders never add a node,
edge, zone, label or title that the graph does not carry.

Graph: chain [node], path [{id, a, b, label}] (chain order), deps [{id, a, b, label}], zones [{id, label, members,
grounds}], messages [{edge, text, grounds}], names {node: display name}, kinds {node: glyph}, title.
"""
import re

# Measured from the motion_arch render (17 px labels, glyph + padding), so boxes fit their labels.
NODE_PX, CHAR_PX, EDGE_CHAR_PX, ARROW_PX, MARGIN_PX = 80, 10.2, 7.6, 36, 30
GROUP_CHAR_PX = 8.4   # group labels: mono, uppercase, letter-spaced
GROUP_LABEL_MAX = 40  # motion_arch cuts group labels past this; never hand it one it would clip
UNLINKED = 'Not linked to the main flow'


def _id(name):
    return re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')[:32] or 'n'


def node_grounds(graph, node):
    return sorted({e['id'] for e in graph['path'] + graph['deps'] if node in (e['a'], e['b'])})


def arch_width(graph):
    """Canvas width a one-row layout needs, so the clarity rule can be judged before building."""
    names = graph['names']
    return int(2 * MARGIN_PX + sum(NODE_PX + CHAR_PX * len(names[c]) for c in graph['chain'])
               + sum(ARROW_PX + EDGE_CHAR_PX * len(e['label']) for e in graph['path'])) + 1


def motion_arch(graph, colours=None):
    names, W = graph['names'], max(arch_width(graph), 200)
    pos, wid, x = {}, {}, MARGIN_PX
    for i, c in enumerate(graph['chain']):
        npx = NODE_PX + CHAR_PX * len(names[c])
        pos[c], wid[c] = (round(100 * (x + npx / 2) / W, 1), 34), round(100 * npx / W, 1)
        x += npx + (ARROW_PX + EDGE_CHAR_PX * len(graph['path'][i]['label']) if i < len(graph['path']) else 0)
    for d in graph['deps']:                                    # a dependency sits below its source
        if d['b'] not in pos:
            pos[d['b']], wid[d['b']] = (pos[d['a']][0], 80), max(wid[d['a']], round(100 * (NODE_PX + CHAR_PX * len(names[d['b']])) / W, 1))
    nodes = list(graph['chain']) + [d['b'] for d in graph['deps'] if d['b'] not in graph['chain']]
    block = dict(type='motion_arch', label=graph['title'],
                 nodes=[dict(id=_id(c), kind=graph['kinds'][c], label=names[c], x=pos[c][0], y=pos[c][1], w=wid[c], h=16) for c in nodes],
                 edges=[dict(**{'from': _id(e['a']), 'to': _id(e['b'])}, label=e['label'], style='solid') for e in graph['path']]
                       + [dict(**{'from': _id(d['a']), 'to': _id(d['b'])}, label=d['label'], style='dashed') for d in graph['deps']],
                 messages=[dict(edge=m['edge'], text=m['text']) for m in graph['messages']],
                 groups=[], w=W, h=520, **(colours or {}))
    for z in graph['zones']:
        lo = min(pos[m][0] - wid[m] / 2 for m in z['members']) - 1.5
        hi = max(pos[m][0] + wid[m] / 2 for m in z['members']) + 1.5
        block['groups'].append(dict(label=z['label'], x=round(lo, 1), y=18, w=round(hi - lo, 1), h=34))
    elements = ([dict(what='node', label=names[c], grounds=node_grounds(graph, c)) for c in nodes]
                + [dict(what='edge', label=f"{e['a']} -> {e['b']}", grounds=[e['id']]) for e in graph['path'] + graph['deps']]
                + [dict(what='zone', label=z['label'], grounds=z['grounds']) for z in graph['zones']]
                + [dict(what='message', label=m['text'], grounds=m['grounds']) for m in graph['messages']])
    return block, elements


def layer_stack(graph):
    names, deps = graph['names'], {d['a']: d for d in graph['deps']}
    layers, elements = [], []
    for c in graph['chain']:
        g = node_grounds(graph, c)
        layer = dict(name=names[c], status='present', field='path slot ' + ', '.join(g))
        if c in deps:
            layer['note'] = f"{deps[c]['label']} the {names[deps[c]['b']]} (dependency, not a layer)"
        layers.append(layer)
        elements.append(dict(what='layer', label=names[c], grounds=g))
    return dict(type='layer_stack', title=graph['title'] + ', bottom up', order='bottom_up', layers=layers), elements


def bullet_list(names_in_order, display):
    """The names-only fallback: components the article names. Grounded in the lexicon match, not in a slot."""
    return dict(type='bullet_list', items=[dict(text=display[n]) for n in names_in_order]), []


def pieces_of(edges):
    """Connected groups of interactions (undirected), largest first: an HLD draws each sourced piece."""
    groups = []
    for e in edges:
        hit = [g for g in groups if {e['a'], e['b']} & g['nodes']]
        merged = dict(nodes={e['a'], e['b']}, edges=[e])
        for g in hit:
            merged['nodes'] |= g['nodes']; merged['edges'] += g['edges']; groups.remove(g)
        groups.append(merged)
    return sorted(groups, key=lambda g: (-len(g['nodes']), sorted(g['nodes'])))


def hld(graph, edges, colours=None):
    """A high-level design: columns by flow depth within each piece, pieces on their own bands, path steps numbered,
    dependencies dashed below their source, boxes and gaps sized to their labels. Draws only the edges given."""
    names = graph['names']
    npx = lambda c: NODE_PX + CHAR_PX * len(names[c])
    pieces = pieces_of(edges)
    rows = []                                                 # band height per piece: 1 row, +1 if dependencies hang below
    for p in pieces:
        rows.append(2 if any(e['role'] != 'path' for e in p['edges']) else 1)
    tops, y0 = [], 40
    for n in rows:
        tops.append(y0); y0 += 70 + 110 * n
    H = y0
    pos, wid, W = {}, {}, 0
    step, steps = 0, {}
    for pi, p in enumerate(pieces):
        path = [e for e in p['edges'] if e['role'] == 'path']
        deps = [e for e in p['edges'] if e['role'] != 'path']
        depth = {n: 0 for n in p['nodes']}
        for _ in range(len(p['nodes'])):                      # longest-path depth along path edges
            for e in path:
                depth[e['b']] = max(depth[e['b']], depth[e['a']] + 1)
        for e in deps:                                        # a dependency target sits with its source, one row down
            if not any(x['b'] == e['b'] for x in path):
                depth[e['b']] = depth[e['a']]
        cols = {}
        for n in sorted(p['nodes'], key=lambda n: (depth[n], n)):
            cols.setdefault(depth[n], []).append(n)
        x = MARGIN_PX
        for d in sorted(cols):
            cw = max(npx(n) for n in cols[d])
            top = [n for n in cols[d] if not any(e['b'] == n for e in deps) or any(x2['b'] == n for x2 in path)]
            low = [n for n in cols[d] if n not in top]
            for k, n in enumerate(top):
                pos[n] = (x + cw / 2, tops[pi] + 60 + k * 70)
            for k, n in enumerate(low):
                pos[n] = (x + cw / 2, tops[pi] + 60 + (len(top) + k) * 70 + 40)
            gap = max([ARROW_PX + EDGE_CHAR_PX * len(e['label']) + 24 for e in path if depth[e['a']] == d] or [0])
            x += cw + gap
        W = max(W, x + MARGIN_PX)
        for e in sorted(path, key=lambda e: (depth[e['a']], e['a'], e['b'])):
            step += 1; steps[e['id']] = step
    W = int(max(W, 400))
    H = int(max(y for _, y in pos.values()) + 27 + 22 + 30)    # tight: last box, its frame padding, a margin
    nodes = sorted({n for p in pieces for n in p['nodes']}, key=lambda n: (pos[n][1], pos[n][0]))
    for n in nodes:
        wid[n] = round(100 * npx(n) / W, 1)
    block = dict(type='motion_arch', label=graph['title'],
                 nodes=[dict(id=_id(n), kind=graph['kinds'][n], label=names[n], x=round(100 * pos[n][0] / W, 1),
                             y=round(100 * pos[n][1] / H, 1), w=wid[n], h=round(100 * 54 / H, 1)) for n in nodes],
                 edges=[dict(**{'from': _id(e['a']), 'to': _id(e['b'])},
                             label=(f"{steps[e['id']]} · " if e['id'] in steps else '') + e['label'],
                             style='solid' if e['role'] == 'path' else 'dashed') for e in edges],
                 messages=[], groups=[], w=W, h=H, **(colours or {}))
    def frame(members, label, pad_top=30, pad=14):
        # in px, so the label row (pad_top) always clears the boxes it surrounds
        lo = min(pos[m][0] - npx(m) / 2 for m in members) - pad; hi = max(pos[m][0] + npx(m) / 2 for m in members) + pad
        if len(label) > GROUP_LABEL_MAX:
            raise ValueError(f'group label {label!r} would be clipped by the renderer ({GROUP_LABEL_MAX} chars)')
        hi = max(hi, lo + GROUP_CHAR_PX * len(label) + 2 * pad)  # the frame is never narrower than its label
        top = min(pos[m][1] for m in members) - 27 - pad_top; bot = max(pos[m][1] for m in members) + 27 + pad
        return dict(label=label, x=round(100 * lo / W, 1), y=round(100 * top / H, 1), w=round(100 * (hi - lo) / W, 1),
                    h=round(100 * (bot - top) / H, 1))
    for z in graph['zones']:
        if all(m in pos for m in z['members']):
            block['groups'].append(frame(z['members'], z['label']))
    for p in pieces[1:]:
        block['groups'].append(frame(sorted(p['nodes']), UNLINKED, pad_top=34, pad=22))
    elements = ([dict(what='component', label=names[n], grounds=sorted({e['id'] for e in edges if n in (e['a'], e['b'])})) for n in nodes]
                + [dict(what='interaction', label=f"{e['a']} -> {e['b']}", grounds=[e['id']]) for e in edges]
                + [dict(what='zone', label=z['label'], grounds=z['grounds']) for z in graph['zones'] if all(m in pos for m in z['members'])]
                + [dict(what='boundary', label=UNLINKED, grounds=sorted(e['id'] for e in p['edges'])) for p in pieces[1:]])
    return block, elements, steps, pieces, W
