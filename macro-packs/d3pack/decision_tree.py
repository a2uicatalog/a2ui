"""decision_tree macro: same contract as the decision_tree atom (nodes [{text, children:[{text, children}]}], title, layout, version). The atom is an interactive
collapsible outline (plus a static 'tree' layout); this macro always draws the FULLY EXPANDED tree, left to right: depth maps to the horizontal axis, every leaf gets its own
row, every parent is centred (vertically) over its first and last child. Atom limits: 31 nodes, 6 levels, labels of 32 characters; where the atom falls back to its outline with a note,
this macro draws what fits, says so in a note and keeps the full text in the table. The parser never recurses deeper than the 6 level limit, and everything it has to count beyond
the limits is counted iteratively with a visit budget, so a very deep or very wide or shared-subtree input cannot exhaust the stack or the clock. Returns {'tree': Result, '_default': 'tree'}.
layout='flow' (optional node fields edge, detail, outcome; options theme and ids) draws the top-down decision diagram instead: see decision_flow.py. layout='flow-v' takes the same fields and options and stacks the tree as an indented list about 340 px wide (for phones). Every other call is unchanged."""
from .common import *
from .waterfall import note_result
MAX_NODES, MAX_LEVELS, MAX_DRAW, MAX_TEXT = 31, 6, 32, 120
BOX_H, PITCH, GAP, CHAR_W, PADX, MX = 22, 28, 28, 7.8, 8, 20
VISIT_BUDGET, MAX_TOP = 100_000, 10_000
MAX_EDGE = 24
def _text_of(item):
    if isinstance(item, str): return ident(item, MAX_TEXT)
    return ident(item.get('text'), MAX_TEXT) if isinstance(item, dict) else None
def _children(item): ch = item.get('children') if isinstance(item, dict) else None; return ch if isinstance(ch, list) else []
def _count(item, budget, seen):
    """Number of usable nodes under and including item, counted with an explicit stack; every object is visited at most once (shared or cyclic input is safe) and budget[0] bounds the work."""
    n = 0; stack = [item]
    while stack and budget[0] > 0:
        it = stack.pop()
        if id(it) in seen: continue
        seen.add(id(it)); budget[0] -= 1
        if _text_of(it) is None: continue
        n += 1; stack.extend(_children(it))
    return n
def decision_tree(nodes, title='', layout='tree', version=1, theme='light', ids='dt'):
    flow = layout in ('flow', 'flow-v'); notes = []; ttl = ident(title, 80) or ''
    if isinstance(version, int) and not isinstance(version, bool) and version > 1: notes.append(f'Contract version {min(version, 10 ** 9)} is drawn as version 1.')
    if not isinstance(nodes, list): notes.append('nodes must be a list.'); return {'tree': note_result('decision_tree', ttl, 'The nodes were not a list, so there is nothing to draw.', notes), '_default': 'tree'}
    st = {'dropped': 0, 'deep': 0, 'cut': 0, 'count': 0, 'long': 0}; flat = []; budget = [VISIT_BUDGET]; seen = set()
    if len(nodes) > MAX_TOP: notes.append(f'{len(nodes) - MAX_TOP} top-level entries beyond the {MAX_TOP}th were not looked at.'); nodes = nodes[:MAX_TOP]
    def parse(item, depth, parent):
        """depth <= MAX_LEVELS here, so the recursion is at most MAX_LEVELS deep."""
        txt = _text_of(item)
        if txt is None: st['dropped'] += 1; return
        if st['count'] >= MAX_NODES: st['cut'] += _count(item, budget, seen); return
        st['count'] += 1; me = {'text': txt, 'depth': depth - 1, 'parent': parent, 'kids': [], 'i': len(flat)}; flat.append(me)
        if flow and isinstance(item, dict): me.update(edge=ident(item.get('edge'), MAX_EDGE), detail=ident(item.get('detail'), MAX_TEXT), outcome=item.get('outcome') if isinstance(item.get('outcome'), bool) else None)
        elif flow: me.update(edge=None, detail=None, outcome=None)
        if len(txt) > MAX_DRAW and not flow: st['long'] += 1
        for c in _children(item):
            if depth >= MAX_LEVELS:
                if _text_of(c) is None: st['dropped'] += 1
                else: st['deep'] += _count(c, budget, seen)
                continue
            k = len(flat); parse(c, depth + 1, me['i'])
            if len(flat) > k: me['kids'].append(k)
    for it in nodes: parse(it, 1, None)
    if not flat:
        why = 'A decision tree needs at least one node with text.'; notes.append(why)
        return {'tree': note_result('decision_tree', ttl, why + ' Nothing was drawn.', notes), '_default': 'tree'}
    if st['dropped']: notes.append(f'{st["dropped"]} nodes were left out (no text, or not an object or string).')
    if st['deep']: notes.append(f'{st["deep"]} nodes below level {MAX_LEVELS} were not drawn (the atom shows its outline instead of the tree beyond {MAX_LEVELS} levels).')
    if st['cut']: notes.append(f'{st["cut"]} nodes beyond the {MAX_NODES}th were not drawn (the atom shows its outline instead of the tree beyond {MAX_NODES} nodes).')
    if st['long']: notes.append(f'{st["long"]} labels longer than {MAX_DRAW} characters are drawn shortened with an ellipsis; the table and the hover title keep the full text (the atom shows its outline for labels over {MAX_DRAW} characters).')
    if isinstance(layout, str) and layout not in ('tree', 'flow', 'flow-v'): notes.append(f'layout {ident(layout, 20)} is the collapsible outline; this is the static tree.')
    if flow: return _flow(flat, ttl, notes, theme, ids, layout == 'flow-v')
    notes.append('Drawn fully expanded: the atom is collapsible, a static picture cannot be.')
    roots = [n['i'] for n in flat if n['parent'] is None]
    slot = [0]
    def place(i):
        n = flat[i]
        if not n['kids']: n['row'] = float(slot[0]); slot[0] += 1
        else:
            for k in n['kids']: place(k)
            n['row'] = (flat[n['kids'][0]]['row'] + flat[n['kids'][-1]]['row']) / 2
    for r in roots: place(r)
    for n in flat: n['drawn'] = n['text'] if len(n['text']) <= MAX_DRAW else n['text'][:MAX_DRAW - 1] + '…'
    leaves = slot[0]; levels = max(n['depth'] for n in flat) + 1
    need = [max(len(n['drawn']) * CHAR_W + 2 * PADX for n in flat if n['depth'] == d) for d in range(levels)]
    avail = W - 2 * MX - (levels - 1) * GAP
    if sum(need) > avail:
        cap = avail / levels
        for _ in range(8):
            small = [x for x in need if x <= cap]; big = sum(1 for x in need if x > cap)
            if not big: break
            cap = (avail - sum(small)) / big
        cw = [min(x, cap) for x in need]
    else: cw = list(need)
    xs = []; x = MX
    for d in range(levels): xs.append(x); x += cw[d] + GAP
    top = 56 if ttl else 24; h = max(H, int(top + leaves * PITCH + 16)); body = ''
    if ttl: body += label(W / 2, 32, ttl, 20, weight=700)
    for n in flat:
        d = n['depth']; n['x'] = xs[d]; n['w'] = cw[d]; n['y'] = top + n['row'] * PITCH + PITCH / 2; n['h'] = BOX_H
        fit = int((n['w'] - 2 * PADX) / CHAR_W); n['shown'] = n['drawn'] if len(n['drawn']) <= fit else n['drawn'][:max(1, fit - 1)] + '…'
    for n in flat:
        if n['parent'] is not None:
            p = flat[n['parent']]; mx = p['x'] + p['w'] + GAP / 2
            body += f'<path d="M{p["x"]+p["w"]:.2f},{p["y"]:.2f} H{mx:.2f} V{n["y"]:.2f} H{n["x"]:.2f}" fill="none" stroke="#c9cde0" stroke-width="2"/>'
    for n in flat:
        c = PAL[n['depth'] % len(PAL)]
        body += (f'<g><title>{esc(n["text"])}</title><rect x="{n["x"]:.2f}" y="{n["y"]-n["h"]/2:.2f}" width="{n["w"]:.2f}" height="{n["h"]}" rx="6" fill="{c}"/>'
                 + label(n['x'] + n['w'] / 2, n['y'] + 5, n['shown'], 14, fill=text_on(c)) + '</g>')
    def num(i):
        n = flat[i]; sibs = roots if n['parent'] is None else flat[n['parent']]['kids']; k = sibs.index(i) + 1
        return str(k) if n['parent'] is None else num(n['parent']) + '.' + str(k)
    for n in flat: n['path'] = num(n['i'])
    table = '; '.join(f'{n["path"]} {n["text"]}' + ('' if n['kids'] else ' (end)') for n in flat)
    per = [sum(1 for n in flat if n['depth'] == d) for d in range(levels)]; wid = max(range(levels), key=lambda d: (per[d], -d))
    summary = f'{len(flat)} nodes in {levels} levels, {leaves} end points; the widest level is level {wid + 1} with {per[wid]} nodes.'
    res = finish('decision_tree', ttl, svg(body, 'Decision tree', W, h), summary, table, notes)
    res['nodes'] = flat; res['levels'] = levels; res['leaves'] = leaves; res['size'] = (W, h)
    return {'tree': res, '_default': 'tree'}
def _flow(flat, ttl, notes, theme, ids, vertical=False):
    """layout='flow' (see decision_flow.py): numbering, table, summary and the ordered-list text are made here from the parsed nodes; the drawing there. Iterative except for the numbering, which is at most MAX_LEVELS deep."""
    from .decision_flow import draw_flow, draw_flow_v
    from .common import esc, plain
    if theme not in ('light', 'css-vars'): notes.append('theme ' + (ident(theme, 20) or 'unknown') + ' is not known; drawn with theme light (the other is css-vars).'); theme = 'light'
    roots = [n['i'] for n in flat if n['parent'] is None]; levels = max(n['depth'] for n in flat) + 1; leaves = sum(1 for n in flat if not n['kids'])
    def num(i):
        n = flat[i]; sibs = roots if n['parent'] is None else flat[n['parent']]['kids']; k = sibs.index(i) + 1
        return str(k) if n['parent'] is None else num(n['parent']) + '.' + str(k)
    for n in flat: n['path'] = num(n['i'])
    full = lambda n: (f'If {n["edge"]}: ' if n.get('edge') else '') + n['text'] + (f' - {n["detail"]}' if n.get('detail') else '')
    table = '; '.join(f'{n["path"]} {full(n)}' + ('' if n['kids'] else ' (end)') for n in flat)
    per = [sum(1 for n in flat if n['depth'] == d) for d in range(levels)]; wid = max(range(levels), key=lambda d: (per[d], -d))
    summary = f'{len(flat)} nodes in {levels} levels, {leaves} end points; the widest level is level {wid + 1} with {per[wid]} nodes.'
    def li(i):
        n = flat[i]; inner = ''.join(f'<li>{li(k)}</li>' for k in n['kids'])
        return esc(full(n)) + (f'<ol>{inner}</ol>' if inner else '')
    html = '<ol>' + ''.join(f'<li>{li(r)}</li>' for r in roots) + '</ol>'
    plain_text = '\n'.join('  ' * n['depth'] + f'{n["path"]}. {full(n)}' for n in flat)
    desc = f'{len(flat)} boxes. ' + ' '.join(full(n) + ('.' if not full(n).endswith(('.', '?')) else '') for n in flat)
    return (draw_flow_v if vertical else draw_flow)(flat, ttl, notes, theme, ids, leaves, levels, summary, table, {'plain': plain_text, 'html': html, 'desc': plain(desc)[:600]})
