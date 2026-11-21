"""Label wrapping and label hygiene (port of mermaid_arch/labels.mjs).

A node label (max 40) may have a second line (`sub`, max 40), an edge label (max 48) a second line (`label2`, max 48).
A longer text is wrapped at a word boundary near the middle; only a text that cannot fit on two lines is cut (with an
ellipsis, and one merged warning). Lengths are counted in UTF-16 units, like JS .length.
"""
from __future__ import annotations

from ._js import rx, squash, trim, trim_end, trim_start, ulen
from .graph import LIMITS

MIN_SIDE = 4


def wrap_label(text, max_):
    """text -> (lines, cut); every line is at most `max_` units"""
    raw = trim(str(text))
    if ulen(raw) <= max_:
        return [raw], False
    t = squash(raw)
    if ulen(t) <= max_:
        return [t], False
    cps = list(t)
    pre = [0]
    for i, c in enumerate(cps):
        pre.append(pre[i] + ulen(c))
    total = pre[len(cps)]
    if total <= 2 * max_:
        best, best_gap = -1, float('inf')
        for i in range(1, len(cps) - 1):
            if cps[i] != ' ':
                continue
            l, r = pre[i], total - pre[i + 1]
            if l < MIN_SIDE or r < MIN_SIDE:
                continue
            if l <= max_ and r <= max_ and abs(l - r) < best_gap:
                best, best_gap = i, abs(l - r)
        if best >= 0:
            return [''.join(cps[:best]), ''.join(cps[best + 1:])], False
        at, gap = -1, float('inf')
        for i in range(1, len(cps)):
            l, r = pre[i], total - pre[i]
            if l <= max_ and r <= max_ and abs(l - r) < gap:
                at, gap = i, abs(l - r)
        if at > 0:
            return [trim_end(''.join(cps[:at])), trim_start(''.join(cps[at:]))], False
    at = -1
    for i in range(1, len(cps)):
        if cps[i] == ' ' and pre[i] <= max_:
            at = i
    if at < 0:
        at = 0
        while at + 1 < len(cps) and pre[at + 1] <= max_:
            at += 1
    l1 = trim_end(''.join(cps[:at]))
    rest = trim_start(''.join(cps[at:]))
    return [l1, clip_text(rest, max_)], True


def clip_text(s, max_):
    t = squash(s)
    if ulen(t) <= max_:
        return t
    cps = list(t)
    n = 0
    i = 0
    while i < len(cps) and n + ulen(cps[i]) <= max_ - 1:
        n += ulen(cps[i])
        i += 1
    return trim_end(''.join(cps[:i])) + '…'


_OWN_NUMBER = rx(r'^\(?\d{1,3}\s*(?:[.):]|-(?=\s))\s+(?=\S)')


def strip_own_number(label):
    s = '' if label is None else str(label)
    ts = trim_start(s)
    return _OWN_NUMBER.sub('', ts, count=1) if _OWN_NUMBER.match(ts) else s


_DANGLING = rx(r'[\s,;:&\-–—]+$')


def strip_dangling(s):
    return _DANGLING.sub('', str(s))


def _name_list(xs):
    return ''.join(xs) if len(xs) < 2 else ', '.join(xs[:-1]) + ' and ' + xs[-1]


def plan_labels(graph, numbered=False, step_no=None):
    """-> {'nodes': {id: {label, sub}}, 'edges': [{text, lines}], 'edgeLabels': [...], 'warnings': [...]}"""
    node_cut, sub_cut, edge_cut, group_cut = [], [], [], []
    nodes = {}
    for n in graph['nodes']:
        label = squash(n['label'])
        sub = squash(n['sub']) if n.get('sub') else ''
        if ulen(label) > LIMITS['label']:
            if not sub:
                lines, cut = wrap_label(label, LIMITS['label'])
                label = lines[0]
                sub = lines[1] if len(lines) > 1 else ''
                if cut:
                    node_cut.append(n['id'])
            else:
                label = clip_text(label, LIMITS['label'])
                node_cut.append(n['id'])
        if ulen(sub) > LIMITS['sub']:
            sub = clip_text(sub, LIMITS['sub'])
            if n['id'] not in node_cut:
                sub_cut.append(n['id'])
        nodes[n['id']] = {'label': label, 'sub': sub}
    edge_labels = [(strip_own_number(e.get('label')) if (numbered and e.get('label')) else e.get('label')) for e in graph['edges']]
    edges = []
    for i, e in enumerate(graph['edges']):
        base = edge_labels[i]
        full = (str(step_no[i]) + (' ' + base if base else '')) if numbered else base
        if not full:
            edges.append({'text': base, 'lines': []})
            continue
        lines, cut = wrap_label(full, LIMITS['edgeLabel'])
        if cut:
            edge_cut.append(i + 1)
        edges.append({'text': '\n'.join(lines), 'lines': lines})
    for gr in graph.get('groups') or []:
        if ulen(str(gr['label'])) > LIMITS['groupLabel']:
            group_cut.append(gr['id'])

    warnings = []
    if node_cut:
        one = len(node_cut) == 1
        warnings.append('%s %s %s longer than the atom can show (%d characters, or %d on two lines when there is no sub-label); %s cut (the Steps table has the full text).'
                        % ('Node' if one else 'Nodes', _name_list(['"%s"' % x for x in node_cut]), 'has a label' if one else 'have labels', LIMITS['label'], LIMITS['label'] * 2, 'it was' if one else 'they were'))
    if sub_cut:
        one = len(sub_cut) == 1
        warnings.append('%s %s %s longer than %d characters; %s cut.'
                        % ('Node' if one else 'Nodes', _name_list(['"%s"' % x for x in sub_cut]), 'has a sub-label' if one else 'have sub-labels', LIMITS['sub'], 'it was' if one else 'they were'))
    if edge_cut:
        one = len(edge_cut) == 1
        warnings.append('%s %s %s longer than the atom can show on two lines; %s cut (the Steps table has the full text).'
                        % ('Edge' if one else 'Edges', _name_list([str(x) for x in edge_cut]), 'has a label' if one else 'have labels', 'it was' if one else 'they were'))
    if group_cut:
        one = len(group_cut) == 1
        warnings.append('%s %s %s longer than %d characters; %s cut.'
                        % ('Group' if one else 'Groups', _name_list(['"%s"' % x for x in group_cut]), 'has a title' if one else 'have titles', LIMITS['groupLabel'], 'it was' if one else 'they were'))
    return {'nodes': nodes, 'edges': edges, 'edgeLabels': edge_labels, 'warnings': warnings}
