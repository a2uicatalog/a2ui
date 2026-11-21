"""Canonical architecture graph and its validator (port of mermaid_arch/graph.mjs).

graph = {
  'title'?: str, 'direction': 'LR'|'RL'|'TB'|'BT',
  'groups': [{id, label}],
  'nodes':  [{id, label, kind?, sub?, group?, line?}],     (line = source line, set by the Mermaid parser)
  'edges':  [{from, to, label?, style: 'sync'|'async'|'optional', both?, step?, relation?, line?}],
  'messages': [{from, to, text, back?}],
  numbered?, pace?, duration?, relationColumn?, relationName?
}
The limits are the motion_arch atom's own.
"""
from __future__ import annotations

import re

from ._js import UNDEF, is_number, js_str, jsget, to_fixed, trim, ulen

LIMITS = {
    'nodes': 12, 'edges': 16, 'groups': 4, 'messages': 12,
    'label': 40, 'sub': 40, 'groupLabel': 40, 'edgeLabel': 48, 'msgText': 40, 'title': 80, 'relation': 20,
}
KINDS = ('device', 'app', 'server', 'tool', 'model', 'store', 'surface', 'user')
STYLES = ('sync', 'async', 'optional')
PACES = {'slow': 1.4, 'normal': 1.0, 'fast': 0.75}
DIRECTIONS = ('LR', 'RL', 'TB', 'BT')
ID_RE = re.compile(r'[a-z][a-z0-9_-]{0,31}\Z')


def norm_direction(d):
    return 'TB' if d == 'TD' else d


KIND_ALIASES = {
    'client': 'device', 'browser': 'device', 'phone': 'device', 'mobile': 'device', 'laptop': 'device', 'device': 'device',
    'db': 'store', 'database': 'store', 'cache': 'store', 'bucket': 'store', 'storage': 'store', 'datastore': 'store', 'store': 'store',
    'queue': 'tool', 'mcp': 'tool', 'auth': 'tool', 'tool': 'tool',
    'gateway': 'server', 'cdn': 'server', 'proxy': 'server', 'backend': 'server', 'server': 'server', 'worker': 'server',
    'service': 'app', 'agent': 'app', 'app': 'app', 'application': 'app', 'frontend': 'app',
    'llm': 'model', 'ai': 'model', 'model': 'model',
    'external': 'surface', 'ui': 'surface', 'screen': 'surface', 'renderer': 'surface', 'surface': 'surface',
    'person': 'user', 'actor': 'user', 'human': 'user', 'user': 'user',
}


class ArchError(Exception):
    """Same messages as the JS ArchError: str(e) is the errors joined by newlines."""

    def __init__(self, errors, warnings=None):
        lst = list(errors) if isinstance(errors, (list, tuple)) else [errors]
        super().__init__('\n'.join(lst))
        self.errors = lst
        self.warnings = list(warnings) if warnings else []


def _has(d, k):
    return isinstance(d, dict) and k in d


def fold_groups(graph):
    """When a graph has more groups than the atom draws, the smallest are shown without their boxes. -> (graph, warnings)"""
    groups = graph.get('groups') if isinstance(graph, dict) else None
    groups = groups if isinstance(groups, list) else []
    nodes = graph.get('nodes') if isinstance(graph, dict) else None
    if len(groups) <= LIMITS['groups'] or not isinstance(nodes, list):
        return graph, []

    def size(gr):
        return sum(1 for n in nodes if n and n.get('group') == gr.get('id'))

    order = sorted(((gr, i, size(gr)) for i, gr in enumerate(groups)), key=lambda o: (o[2], -o[1]))
    fold = {o[0].get('id'): o[0] for o in order[:len(groups) - LIMITS['groups']]}
    new_nodes = []
    for n in nodes:
        if not n or n.get('group') not in fold:
            new_nodes.append(n)
            continue
        rest = {k: v for k, v in n.items() if k != 'group'}
        gl = fold[n['group']].get('label')
        t = trim(js_str(gl if gl is not None else n['group']))
        if (rest.get('sub') is None or rest.get('sub') == '') and t and ulen(t) <= LIMITS['sub']:
            rest['sub'] = t
        new_nodes.append(rest)
    kept = [gr for gr in groups if gr.get('id') not in fold]
    names = ['"%s"' % (gr.get('label') or gr.get('id')) for gr in groups if gr.get('id') in fold]
    lst = names[0] if len(names) == 1 else ', '.join(names[:-1]) + ' and ' + names[-1]
    warning = ('Drew %d of %d groups: %s %s shown without %s (the diagram can draw at most %d).'
               % (len(kept), len(groups), lst, 'was' if len(names) == 1 else 'were', 'its box' if len(names) == 1 else 'their boxes', LIMITS['groups']))
    g2 = dict(graph)
    g2['groups'] = kept
    g2['nodes'] = new_nodes
    return g2, [warning]


def _at(x):
    ln = x.get('line') if isinstance(x, dict) else None
    return 'line %d: ' % ln if isinstance(ln, int) and not isinstance(ln, bool) else ''


def resolve_kind(name):
    if not isinstance(name, str):
        return None
    k = trim(name).lower()
    return KIND_ALIASES.get(k)


def levenshtein(a: str, b: str) -> int:
    m, n = len(a), len(b)
    if not m:
        return n
    if not n:
        return m
    prev = list(range(n + 1))
    for i in range(1, m + 1):
        cur = [i]
        for j in range(1, n + 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (0 if a[i - 1] == b[j - 1] else 1)))
        prev = cur
    return prev[n]


def did_you_mean(word, candidates):
    """Closest candidate, or None when nothing is plausibly a typo."""
    w = js_str(word).lower()
    best = None
    best_d = float('inf')
    for c in candidates:
        d = levenshtein(w, js_str(c).lower())
        if d < best_d:
            best_d = d
            best = c
    limit = max(1, min(3, max(ulen(w), 3) // 3))
    return best if best_d <= limit else None


def _hint(word, candidates):
    s = did_you_mean(word, candidates)
    return ' (did you mean "%s"?)' % s if s is not None else ''


def _plural(n, one, many):
    return '%d %s' % (n, one if n == 1 else many)


def assign_steps(graph):
    """Step numbers for the edges (source order, or a `step` override). -> (steps, errors)"""
    edges = graph.get('edges') if isinstance(graph.get('edges'), list) else []
    n = len(edges)
    errors = []
    steps = [0] * n
    owner = {}
    for i, e in enumerate(edges):
        if not _has(e, 'step') or e['step'] is None:
            continue
        d = 'edge %d (%s -> %s)' % (i + 1, js_str(jsget(e, 'from')), js_str(jsget(e, 'to')))
        st = e['step']
        if not (isinstance(st, int) and not isinstance(st, bool)) or st < 1:
            errors.append('%s: step must be a whole number from 1 to %d' % (d, n))
            continue
        if st > n:
            errors.append('%s: step %d is larger than the number of edges (%d); steps must run 1 to %d with no gaps' % (d, st, n, n))
            continue
        if st in owner:
            errors.append('step %d is given to both edge %d and edge %d; each step number can be used once' % (st, owner[st] + 1, i + 1))
            continue
        owner[st] = i
        steps[i] = st
    nxt = 1
    for i, e in enumerate(edges):
        if steps[i]:
            continue
        if _has(e, 'step') and e['step'] is not None:
            continue
        while nxt in owner:
            nxt += 1
        owner[nxt] = i
        steps[i] = nxt
    if not errors:
        for k in range(1, n + 1):
            if k not in owner:
                errors.append('step %d is missing; steps must run 1 to %d with no gaps' % (k, n))
    return steps, errors


def _is_str(x):
    return isinstance(x, str)


def validate_graph(g):
    """-> (errors, warnings). Numbering in messages is 1-based."""
    errors = []
    warnings = []
    if not isinstance(g, dict):
        return ['graph must be an object with nodes and edges'], warnings
    nodes = g['nodes'] if isinstance(g.get('nodes'), list) else []
    edges = g['edges'] if isinstance(g.get('edges'), list) else []
    groups = g['groups'] if isinstance(g.get('groups'), list) else []
    messages = g['messages'] if isinstance(g.get('messages'), list) else []

    if 'direction' in g and g['direction'] is not UNDEF and norm_direction(g['direction']) not in DIRECTIONS:
        errors.append('direction "%s" is not one of %s' % (js_str(g['direction']), ', '.join(DIRECTIONS)))
    if not nodes:
        errors.append('the graph has no nodes; add at least one node')

    group_ids = set()
    for i, gr in enumerate(groups):
        if not isinstance(gr, dict) or not _is_str(gr.get('id')) or not gr.get('id'):
            errors.append('group %d: needs an id' % (i + 1))
            continue
        if gr['id'] in group_ids:
            errors.append('group %d: id "%s" is used twice; group ids must be unique' % (i + 1, gr['id']))
        group_ids.add(gr['id'])
        if not _is_str(gr.get('label')) or not trim(gr['label']):
            errors.append('group %d ("%s"): needs a label' % (i + 1, gr['id']))

    ids = []
    idset = set()
    for i, n in enumerate(nodes):
        where, nm = _at(n), 'node %d' % (i + 1)
        if not isinstance(n, dict) or not _is_str(n.get('id')) or not n.get('id'):
            errors.append('%s%s: needs an id' % (where, nm))
            continue
        if not ID_RE.match(n['id']):
            errors.append('%s%s: id "%s" is not valid; use a lowercase letter first, then lowercase letters, digits, "_" or "-", up to 32 characters' % (where, nm, n['id']))
        if n['id'] in idset:
            errors.append('%s%s: id "%s" is used twice; node ids must be unique' % (where, nm, n['id']))
        if n['id'] not in idset:
            ids.append(n['id'])
        idset.add(n['id'])
        if not _is_str(n.get('label')) or not trim(n['label']):
            errors.append('%s%s ("%s"): needs a label' % (where, nm, n['id']))
        if 'kind' in n and n['kind'] is not UNDEF and n['kind'] not in KINDS:
            rk = resolve_kind(n['kind'])
            errors.append('%snode "%s": kind "%s" is not one of %s' % (where, n['id'], js_str(n['kind']), ', '.join(KINDS))
                          + (' (did you mean "%s"?)' % rk if rk else _hint(n['kind'], KINDS)))
        if 'group' in n and n['group'] is not UNDEF and n['group'] not in group_ids:
            errors.append('%snode "%s": group "%s" is not a group id' % (where, n['id'], js_str(n['group'])) + _hint(n['group'], list(group_ids)))

    nd_list = list(ids)
    touched = set()
    for i, e in enumerate(edges):
        where, nm = _at(e), 'edge %d' % (i + 1)
        if not isinstance(e, dict):
            errors.append('%s%s: must be an object with from and to' % (where, nm))
            continue
        bad = False
        for end in ('from', 'to'):
            v = jsget(e, end)
            if not _is_str(v) or v not in idset:
                hv = v if (v is not UNDEF and v is not None) else ''
                errors.append('%s%s: "%s" is not a node id%s' % (where, nm, js_str(v), _hint(hv, nd_list)))
                bad = True
        if bad:
            continue
        if e['from'] == e['to']:
            errors.append('%s%s: %s points at itself; the atom cannot draw self-loops. Remove the edge or add a second node.' % (where, nm, _shown(nodes, e['from'])))
            continue
        if 'style' in e and e['style'] is not UNDEF and e['style'] not in STYLES:
            errors.append('%s%s: style "%s" is not one of %s' % (where, nm, js_str(e['style']), ', '.join(STYLES)))
        touched.add(e['from'])
        touched.add(e['to'])
    seen = {}
    for i, e in enumerate(edges):
        if not e or e.get('from') == e.get('to'):
            continue
        k = '%s>%s|%s|%s' % (js_str(e.get('from', UNDEF)), js_str(e.get('to', UNDEF)), e.get('style') or 'sync', e.get('label') or '')
        if k in seen:
            warnings.append('edge %d: duplicates edge %d (%s -> %s); consider merging them into one labelled edge.' % (i + 1, seen[k], js_str(e.get('from', UNDEF)), js_str(e.get('to', UNDEF))))
        else:
            seen[k] = i + 1
    for n in nodes:
        if n and n.get('id') in idset and n.get('id') not in touched and len(nodes) > 1:
            warnings.append('node "%s" has no edges; it will sit on its own in the layout. Connect it or remove it.' % n['id'])

    for i, m in enumerate(messages):
        at = 'message %d' % (i + 1)
        if not isinstance(m, dict):
            errors.append('%s: must be an object with from, to and text' % at)
            continue
        bad = False
        for end in ('from', 'to'):
            v = jsget(m, end)
            if not _is_str(v) or v not in idset:
                hv = v if (v is not UNDEF and v is not None) else ''
                errors.append('%s: "%s" is not a node id%s' % (at, js_str(v), _hint(hv, nd_list)))
                bad = True
        if bad:
            continue
        if not _is_str(m.get('text')) or not trim(m['text']):
            errors.append('%s: needs text (the payload chip)' % at)
            continue
        if ulen(m['text']) > LIMITS['msgText']:
            warnings.append('%s: text is %d characters; the atom shows at most %d.' % (at, ulen(m['text']), LIMITS['msgText']))
        fwd = any(e and e.get('from') == m['from'] and e.get('to') == m['to'] for e in edges)
        rev = any(e and e.get('from') == m['to'] and e.get('to') == m['from'] for e in edges)
        if not fwd and not rev:
            errors.append('%s: there is no edge between "%s" and "%s" for the chip to ride; add that edge or fix the ids' % (at, m['from'], m['to']))
        elif not fwd and rev:
            warnings.append('%s: only the edge %s -> %s exists, so the chip "%s" rides it backwards (reply direction).' % (at, m['to'], m['from'], m['text']))

    for i, e in enumerate(edges):
        if e and 'relation' in e and e['relation'] is not UNDEF and (not _is_str(e['relation']) or ulen(e['relation']) > LIMITS['relation']):
            errors.append('edge %d: relation must be text of at most %d characters (for example "calls" or "reports back")' % (i + 1, LIMITS['relation']))
    if 'relationName' in g and (not _is_str(g['relationName']) or not trim(g['relationName']) or ulen(g['relationName']) > LIMITS['relation']):
        errors.append('relationName must be 1 to %d characters' % LIMITS['relation'])
    if 'relationColumn' in g and not isinstance(g['relationColumn'], bool):
        errors.append('relationColumn must be true or false')
    if 'pace' in g and not (_is_str(g['pace']) and g['pace'] in PACES):
        errors.append('pace "%s" is not one of %s' % (js_str(g['pace']), ', '.join(PACES)))
    if 'duration' in g and not (is_number(g['duration']) and 2 <= g['duration'] <= 120):
        errors.append('duration "%s" must be a number of seconds from 2 to 120' % js_str(g['duration']))
    if g.get('numbered') or any(e and 'step' in e for e in edges):
        if not any(re.match(r'edge \d+: "', x) for x in errors):
            errors.extend(assign_steps(g)[1])

    group_sizes = [(gr.get('label') or gr.get('id'), sum(1 for n in nodes if n and n.get('group') == gr.get('id'))) for gr in groups]
    group_sizes.sort(key=lambda t: -t[1])
    if len(nodes) > LIMITS['nodes']:
        over = len(nodes) - LIMITS['nodes']
        how = 'Split it into two diagrams (one per subsystem), or merge small nodes into one.'
        if len(group_sizes) > 1:
            how = 'Split it by group: %s; draw one diagram per group, or collapse a group into a single node.' % ', '.join(
                '"%s" has %s' % (lb, _plural(c, 'node', 'nodes')) for lb, c in group_sizes[:4])
        errors.append('the graph has %d nodes; the atom draws at most %d (%d over). %s' % (len(nodes), LIMITS['nodes'], over, how))
    if len(edges) > LIMITS['edges']:
        errors.append('the graph has %d edges; the atom draws at most %d. Remove the %d least important, merge duplicate calls into one labelled edge, or split into two diagrams.'
                      % (len(edges), LIMITS['edges'], len(edges) - LIMITS['edges']))
    if len(groups) > LIMITS['groups']:
        errors.append('the graph has %d groups; the atom draws at most %d. Merge related groups, or turn the smallest into plain nodes.' % (len(groups), LIMITS['groups']))
    if len(messages) > LIMITS['messages']:
        errors.append('the graph has %d messages; the atom animates at most %d. Keep the %d that tell the story.' % (len(messages), LIMITS['messages'], LIMITS['messages']))
    if 'title' in g and g['title'] is not UNDEF and ulen(js_str(g['title'])) > LIMITS['title']:
        warnings.append('title is %d characters; the atom keeps at most %d for the accessible name.' % (ulen(js_str(g['title'])), LIMITS['title']))
    return errors, warnings


def _shown(nodes, id_):
    n = next((x for x in nodes if x and x.get('id') == id_), None)
    if n and _is_str(n.get('label')) and trim(n['label']) and n['label'] != id_:
        return '"%s" (id %s)' % (n['label'], id_)
    return '"%s"' % id_
