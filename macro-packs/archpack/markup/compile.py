"""Canonical graph + layout + schedule -> a motion_arch block (port of mermaid_arch/compile.mjs).

The JS file also builds the film payload and the steps/messages tables around the block; the Python target (arch_motion)
takes the block itself, so those parts are not ported. The text alternative (`text_steps`, `text_messages`) is kept: it is
the same data the JS tables are made from.
"""
from __future__ import annotations

import math
import re

from ._js import js_round, to_fixed, uslice, ulen, trim_end
from .activity import activity
from .graph import LIMITS, PACES, ArchError, assign_steps
from .labels import plan_labels
from .layout import layout_graph
from .schedule import (CHIP_GAP, CHIP_START, CHIP_TAIL, RIDE_FLOOR, ScheduleError, build_schedule, chip_ride, pace_ride, words)


def r2(x):
    return js_round(x * 100) / 100


def r4(x):
    return js_round(x * 10000) / 10000


def pd(seconds, D):
    """the atom clamps every dur to 0.01-1 of the film"""
    return r4(max(0.011, seconds / D))


def clamp(x, a, b):
    return max(a, min(b, x))


def clip(s, max_):
    t = _trim(str(s))
    return t if ulen(t) <= max_ else trim_end(uslice(t, 0, max_ - 1)) + '…'


def _trim(s):
    from ._js import trim
    return trim(s)


def _fsum(xs):
    t = 0
    for x in xs:
        t = t + x
    return t


def compile_graph(graph, opts=None):
    """graph -> dict(block, layout, warnings, steps, textSteps, textMessages, schedule, durationSeconds, ...). The graph must be valid."""
    opts = opts or {}
    warnings = []
    numbered = bool(opts['numbered']) if opts.get('numbered') is not None else bool(graph.get('numbered'))
    pace = opts.get('pace') or graph.get('pace') or 'normal'
    duration = opts['duration'] if opts.get('duration') is not None else graph.get('duration')

    step_no = assign_steps(graph)[0] if numbered else None
    plan = plan_labels(graph, numbered, step_no)
    warnings.extend(plan['warnings'])
    drawn = [x['text'] for x in plan['edges']]
    edge_text = plan['edgeLabels']
    g2_nodes = []
    for n in graph['nodes']:
        p = plan['nodes'][n['id']]
        o = {**n, 'label': p['label']}
        if p['sub']:
            o['sub'] = p['sub']
        else:
            o.pop('sub', None)
        g2_nodes.append(o)
    g2 = {**graph, 'nodes': g2_nodes, 'edges': [{**e, 'label': drawn[i]} for i, e in enumerate(graph['edges'])]}

    lay = layout_graph(g2, opts)
    if not lay['fits']:
        raise ArchError(["the diagram does not fit in the atom's 2000 x 2000 frame even at the smallest text size; shorten the labels or split the diagram"])
    if lay['direction'] != graph['direction']:
        warnings.append('drawn %s instead of %s: that keeps the text about %s px on a 343 px phone column. %s' % (
            'top-to-bottom' if lay['direction'] == 'TB' else 'left-to-right', graph['direction'], to_fixed(lay['size'] * 343 / lay['W'], 0),
            'You can switch the Layout menu to the written direction.' if opts.get('hint') == 'web' else 'Pass --direction %s to force the written direction.' % graph['direction']))
    W, H, size = lay['W'], lay['H'], lay['size']
    horizontal = lay['direction'] in ('LR', 'RL')
    rev = lay['direction'] in ('RL', 'BT')
    by_id = {n['id']: n for n in lay['nodes']}
    gnode = {n['id']: n for n in graph['nodes']}

    def first_edge(f, t):
        return next((i for i, e in enumerate(graph['edges']) if e['from'] == f and e['to'] == t), -1)
    msg_edge = []
    for j, m in enumerate(graph['messages']):
        idx = first_edge(m['from'], m['to'])
        back = bool(m.get('back'))
        if idx < 0:
            idx = first_edge(m['to'], m['from'])
            back = not back
        if idx < 0:
            raise ArchError(['message %d: no edge between "%s" and "%s"' % (j + 1, m['from'], m['to'])])
        msg_edge.append((idx, back))

    def main(n):
        return n['x'] + n['w'] / 2 if horizontal else n['y'] + n['h'] / 2
    sorted_nodes = sorted(({'id': n['id'], 'm': main(n) * (-1 if rev else 1), 'i': i} for i, n in enumerate(lay['nodes'])), key=lambda o: (o['m'], o['i']))
    node_rank = {n['id']: k for k, n in enumerate(sorted_nodes)}
    n_edges = len(graph['edges'])
    if numbered:
        order = sorted(range(n_edges), key=lambda a: step_no[a])
    else:
        def kk(a):
            return max(node_rank[graph['edges'][a]['from']], node_rank[graph['edges'][a]['to']])
        order = sorted(range(n_edges), key=lambda a: (kk(a), a))

    def lab(id_):
        return gnode[id_]['label']

    def is_reply(i, e):
        return any(j != i and o['from'] == e['to'] and o['to'] == e['from'] for j, o in enumerate(graph['edges'])) and first_edge(e['to'], e['from']) < i
    sentence = [activity(lab(e['from']), lab(e['to']), edge_text[i], style=e.get('style'), both=e.get('both'), reply=is_reply(i, e)) for i, e in enumerate(graph['edges'])]
    long_side = max(W, H)

    def path_len(ei):
        rt = lay['routes'][ei] if lay.get('routes') else None
        if rt:
            t = 0
            pts = rt['points']
            for q in range(len(pts) - 1):
                t = t + math.hypot(pts[q + 1][0] - pts[q][0], pts[q + 1][1] - pts[q][1])
            return t
        a, b = by_id[graph['edges'][ei]['from']], by_id[graph['edges'][ei]['to']]
        return 1.2 * math.hypot(a['x'] + a['w'] / 2 - (b['x'] + b['w'] / 2), a['y'] + a['h'] / 2 - (b['y'] + b['h'] / 2))
    ride_of = [chip_ride(path_len(msg_edge[j][0]), long_side, ulen(clip(m['text'], LIMITS['msgText']))) for j, m in enumerate(graph['messages'])]
    info = []
    for ei in order:
        rides = [ride_of[j] for j, m in enumerate(graph['messages']) if msg_edge[j][0] == ei]
        info.append({'words': words(sentence[ei]), 'chips': len(rides), 'rides': rides})
    mult = PACES[pace]
    try:
        sched = build_schedule(info, pace, duration)
    except ScheduleError as e:
        raise ArchError([str(e)])
    warnings.extend(sched['warnings'])
    D = sched['durationSeconds']
    step_of = {ei: k for k, ei in enumerate(order)}

    NODE_DUR = 0.3
    node_at = {n['id']: 0.3 + ((k * 0.4) / (len(sorted_nodes) - 1) if len(sorted_nodes) > 1 else 0) for k, n in enumerate(sorted_nodes)}
    nodes = []
    for gn in graph['nodes']:
        b = by_id[gn['id']]
        pn = plan['nodes'][gn['id']]
        o = {'id': gn['id'], 'kind': gn.get('kind') or 'server', 'label': clip(pn['label'], LIMITS['label'])}
        if pn['sub']:
            o['sub'] = clip(pn['sub'], LIMITS['sub'])
        o['x'] = r2(((b['x'] + b['w'] / 2) / W) * 100)
        o['y'] = r2(((b['y'] + b['h'] / 2) / H) * 100)
        o['w'] = r2(clamp((b['w'] / W) * 100, 4, 100))
        o['h'] = r2(clamp((b['h'] / H) * 100, 4, 100))
        o['at'] = r4(node_at[gn['id']] / D)
        o['dur'] = pd(NODE_DUR, D)
        nodes.append(o)

    def edge_sec(st):
        return max(min(0.5, (st['end'] - st['start']) * 0.4), 0.011 * D)
    edges = []
    for i, e in enumerate(graph['edges']):
        st = sched['schedule'][step_of[i]]
        o = {'from': e['from'], 'to': e['to']}
        dl = plan['edges'][i]['lines']
        if dl:
            o['label'] = clip(dl[0], LIMITS['edgeLabel'])
        if len(dl) > 1:
            o['label2'] = clip(dl[1], LIMITS['edgeLabel'])
        o['style'] = 'solid' if (e.get('style') == 'sync' or e.get('style') is None) else 'dashed'
        if e.get('both'):
            o['both'] = True
        rt = lay['routes'][i] if lay.get('routes') else None
        if rt:
            o['points'] = [{'x': r2((q[0] / W) * 100), 'y': r2((q[1] / H) * 100)} for q in rt['points']]
            if rt['label']:
                o['label_at'] = {'x': r2(((rt['label']['x'] + rt['label']['w'] / 2) / W) * 100), 'y': r2(((rt['label']['y'] + rt['label']['h'] / 2) / H) * 100)}
        elif lay['curves'][i]:
            o['curve'] = lay['curves'][i]
        o['at'] = r4(st['start'] / D)
        o['dur'] = pd(edge_sec(st), D)
        edges.append(o)

    def worst_chip_fit(sch, Dt):
        worst, at = 1, -1
        for k, st in enumerate(info):
            if not st['chips']:
                continue
            dw = sch[k]['end'] - sch[k]['start']
            es = max(min(0.5, dw * 0.4), 0.011 * Dt)
            need = max(CHIP_START, es + 0.05) + _fsum(RIDE_FLOOR * c['min'] for c in st['rides']) + (st['chips'] - 1) * CHIP_GAP
            if need / dw > worst:
                worst, at = need / dw, k
        return worst, at
    if duration is not None:
        _w, at = worst_chip_fit(sched['schedule'], D)
        if at >= 0:
            text_min = build_schedule([{**st, 'chips': 0, 'rides': []} for st in info], pace)['minimumSeconds']
            hint = math.ceil(duration)

            def bad(h):
                try:
                    return worst_chip_fit(build_schedule(info, pace, h)['schedule'], h)[1] >= 0
                except ScheduleError:
                    return True
            while hint < 600 and bad(hint):
                hint += 1
            total_cause = duration < text_min - 1e-9 and hint == math.ceil(text_min)
            from ._js import num_str
            if total_cause:
                raise ArchError(["duration %s s is shorter than the film's minimum (%s s at the fast pace). Raise the duration to at least %d s, or remove steps or messages." % (num_str(duration), to_fixed(text_min, 1), hint)])
            raise ArchError(['duration %s s is too short for the %d message chips on step %d: each chip needs at least its minimum ride (1.35 s or more, longer for long text) inside its step. Raise the duration to at least %d s, or remove messages.'
                             % (num_str(duration), info[at]['chips'], sched['schedule'][at]['step'], hint)])
    seen = {}
    messages = []
    for j, m in enumerate(graph['messages']):
        idx, back = msg_edge[j]
        si = step_of[idx]
        st = sched['schedule'][si]
        jn = seen.get(idx, 0)
        seen[idx] = jn + 1
        dwell = st['end'] - st['start']
        off = max(CHIP_START, edge_sec(st) + 0.05)
        rides = [pace_ride(c, mult) for c in info[si]['rides']]
        k = len(rides)
        room = dwell - off - CHIP_TAIL - (k - 1) * CHIP_GAP
        total = _fsum(rides)
        sq = room / total if total > room else 1
        cs = [max(0.3, r * sq) for r in rides]
        c = cs[jn]
        o = {'edge': idx, 'text': clip(m['text'], LIMITS['msgText'])}
        if back:
            o['back'] = True
        acc = 0
        for x in cs[:jn]:
            acc = acc + x + CHIP_GAP
        o['at'] = r4((st['start'] + off + acc) / D)
        o['dur'] = pd(c, D)
        messages.append(o)

    groups = []
    for g in lay['groups']:
        gg = next(x for x in graph['groups'] if x['id'] == g['id'])
        groups.append({'label': clip(gg['label'], LIMITS['groupLabel']), 'x': r2((g['x'] / W) * 100), 'y': r2((g['y'] / H) * 100),
                       'w': r2((g['w'] / W) * 100), 'h': r2((g['h'] / H) * 100), 'at': 0, 'dur': pd(0.3, D)})

    block = {'type': 'motion_arch', 'label': clip(graph.get('title') or 'Architecture diagram', LIMITS['title']), 'w': W, 'h': H, 'size': size, 'nodes': nodes, 'edges': edges}
    if lay.get('routes'):
        block['radius'] = clamp(js_round(size * 0.55), 6, 14)
        warnings.extend(lay['routeWarnings'])
    if groups:
        block['groups'] = groups
    if messages:
        block['messages'] = messages

    steps = []
    if numbered:
        for k, ei in enumerate(order):
            e = graph['edges'][ei]
            o = {'step': step_no[ei], 'from': lab(e['from']), 'to': lab(e['to']), 'label': edge_text[ei] or '', 'style': e.get('style') or 'sync', 'activity': sentence[ei]}
            if e.get('relation'):
                o['relation'] = e['relation']
            steps.append(o)
    text_steps = []
    for k, ei in enumerate(order):
        e = graph['edges'][ei]
        o = {'step': step_no[ei] if numbered else k + 1, 'from': lab(e['from']), 'to': lab(e['to']), 'label': edge_text[ei] or '', 'style': e.get('style') or 'sync', 'activity': sentence[ei]}
        if e.get('relation'):
            o['relation'] = e['relation']
        text_steps.append(o)
    text_messages = []
    for j, m in enumerate(graph['messages']):
        idx, back = msg_edge[j]
        e = graph['edges'][idx]
        text_messages.append({'step': text_steps[step_of[idx]]['step'], 'text': m['text'], 'from': lab(e['to'] if back else e['from']), 'to': lab(e['from'] if back else e['to'])})
    text_messages.sort(key=lambda x: x['step'])
    relation_column = numbered and (bool(opts['relationColumn']) if opts.get('relationColumn') is not None else bool(graph.get('relationColumn')))
    relation_name = opts.get('relationName') or graph.get('relationName') or 'Relation'
    schedule = [{'step': step_no[order[k]] if numbered else s['step'], 'start': s['start'], 'end': s['end']} for k, s in enumerate(sched['schedule'])]
    return {'block': block, 'layout': lay, 'warnings': warnings, 'steps': steps, 'textSteps': text_steps, 'textMessages': text_messages, 'schedule': schedule,
            'durationSeconds': D, 'numbered': numbered, 'pace': pace, 'minimumSeconds': sched['minimumSeconds'], 'relationColumn': relation_column, 'relationName': relation_name}


def validate_block(b):
    """Validate the compiled block against the atom's own limits (JS validateBlock)."""
    errs = []
    if b.get('type') != 'motion_arch':
        errs.append('type must be motion_arch')
    from ._js import num_str
    if not (200 <= b['w'] <= 2000):
        errs.append('w %s outside 200-2000' % num_str(b['w']))
    if not (120 <= b['h'] <= 2000):
        errs.append('h %s outside 120-2000' % num_str(b['h']))
    if not (8 <= b['size'] <= 40):
        errs.append('size %s outside 8-40' % num_str(b['size']))
    if b.get('radius') is not None and not (0 <= b['radius'] <= 60):
        errs.append('radius %s outside 0-60' % num_str(b['radius']))
    nodes, edges, groups, msgs = b.get('nodes') or [], b.get('edges') or [], b.get('groups') or [], b.get('messages') or []
    if len(nodes) > LIMITS['nodes']:
        errs.append('too many nodes')
    if len(edges) > LIMITS['edges']:
        errs.append('too many edges')
    if len(groups) > LIMITS['groups']:
        errs.append('too many groups')
    if len(msgs) > LIMITS['messages']:
        errs.append('too many messages')
    ids = set()
    for n in nodes:
        if not re.fullmatch(r'[a-z][a-z0-9_-]{0,31}', n['id']):
            errs.append('node id %s invalid' % n['id'])
        ids.add(n['id'])
        if n['x'] < 0 or n['x'] > 100 or n['y'] < 0 or n['y'] > 100:
            errs.append('node %s centre outside 0-100' % n['id'])
        if n['w'] < 4 or n['h'] < 4:
            errs.append('node %s too small' % n['id'])
        if ulen(n['label']) > 40 or (n.get('sub') and ulen(n['sub']) > 40):
            errs.append('node %s text too long' % n['id'])
        if n['at'] < 0 or n['at'] > 1 or n['dur'] < 0.01 or n['dur'] > 1:
            errs.append('node %s timing outside 0-1' % n['id'])
    for i, e in enumerate(edges):
        if e['from'] not in ids or e['to'] not in ids:
            errs.append('edge %d dangling' % i)
        if e.get('curve') is not None and (e['curve'] < -100 or e['curve'] > 100):
            errs.append('edge %d curve' % i)
        if e.get('points') is not None:
            if not isinstance(e['points'], list) or len(e['points']) < 2 or len(e['points']) > 10:
                errs.append('edge %d points: 2 to 10 needed' % i)
            elif any(not (0 <= q['x'] <= 100 and 0 <= q['y'] <= 100) for q in e['points']):
                errs.append('edge %d points outside the frame' % i)
        if e.get('label_at') is not None and not (0 <= e['label_at']['x'] <= 100 and 0 <= e['label_at']['y'] <= 100):
            errs.append('edge %d label_at outside the frame' % i)
        if e.get('label') and ulen(e['label']) > 48:
            errs.append('edge %d label too long' % i)
        if e.get('label2') is not None and (not e.get('label') or len(e['label2']) > 48):
            errs.append('edge %d label2 too long or without a label' % i)
        if e['at'] < 0 or e['at'] > 1 or e['dur'] < 0.01 or e['dur'] > 1 or e['at'] + e['dur'] > 1.0001:
            errs.append('edge %d timing outside 0-1' % i)
    for i, m in enumerate(msgs):
        if not (0 <= m['edge'] < len(edges)):
            errs.append('message %d edge index' % i)
        if ulen(m['text']) > 40:
            errs.append('message %d text too long' % i)
        if m['at'] + m['dur'] > 1.0001 or m['dur'] < 0.01:
            errs.append('message %d timing outside the film' % i)
    for i, g in enumerate(groups):
        if g['x'] < 0 or g['y'] < 0 or g['w'] < 1 or g['h'] < 1 or g['x'] + g['w'] > 100.01 or g['y'] + g['h'] > 100.01:
            errs.append('group %d outside frame' % i)
    return errs
