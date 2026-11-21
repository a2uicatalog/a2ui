"""D2 subset -> canonical graph (port of mermaid_arch/d2.mjs).

Supported: shapes, containers (one level), connections, `style.stroke-dash`, `shape:` names, `kind:`/`class:` hints,
`direction:`, and the comment directives `# title:`, `# msg:`, `# numbered:`, `# pace:`, `# duration:`, `# step:`,
`# rel:`, `# relation-column:`, `# relation-name:`. Operators must be surrounded by spaces.
"""
from __future__ import annotations

import re
import unicodedata

from ._js import rx, trim, ulen
from .graph import LIMITS, PACES, ArchError, did_you_mean, resolve_kind
from .mermaid import MAX_INPUT_CHARS, MAX_LINE_CHARS, make_id_mapper, strip_tags_deep, _js_number

MAX_DEPTH = 8
MAX_SEGMENTS = 8
MAX_ERRORS = 20

D2_SHAPE_KIND = {
    'cylinder': 'store', 'stored_data': 'store', 'queue': 'tool', 'person': 'user', 'circle': 'model', 'oval': 'model',
    'hexagon': 'app', 'rectangle': 'server', 'square': 'server', 'page': 'server', 'document': 'server', 'step': 'server',
    'cloud': 'surface', 'diamond': 'tool', 'package': 'server', 'parallelogram': 'server', 'callout': 'server',
}
RESERVED = {'shape', 'label', 'class', 'kind', 'style', 'direction', 'icon', 'tooltip', 'near', 'width', 'height', 'link', 'constraint',
            'source-arrowhead', 'target-arrowhead', 'top', 'left', 'grid-rows', 'grid-columns'}
UNSUPPORTED = {'classes', 'vars', 'd2-config', 'layers', 'scenarios', 'steps'}
DIRS = {'right': 'LR', 'left': 'RL', 'down': 'TB', 'up': 'BT'}
SEP = '\u0001'
OPS = ['<->', '->', '<-', '--']

_BR_G = rx(r'<br\s*/?>', re.I)
_WS1 = rx(r'\s')


def _disp(p):
    return '.'.join(p.split(SEP))


def _cat(t, c):
    """JS `t += c`: an undefined c (read past the end) appends the text "undefined"."""
    return t + ('undefined' if c is None else c)


class _Node:
    __slots__ = ('path', 'leaf', 'label', 'sub', 'shape', 'hints', 'order', 'line', 'children', 'parent')

    def __init__(self, path, leaf, order, line, parent):
        self.path = path
        self.leaf = leaf
        self.label = None
        self.sub = None
        self.shape = None
        self.hints = []
        self.order = order
        self.line = line
        self.children = 0
        self.parent = parent


class _EdgeOwner:
    def __init__(self, made):
        self.made = made

    @property
    def style(self):
        return self.made[0]['style']

    @style.setter
    def style(self, v):
        for e in self.made:
            e['style'] = v

    @property
    def label(self):
        return self.made[0]['label']

    @label.setter
    def label(self, v):
        for e in self.made:
            e['label'] = v or None


def parse_d2(text, opts=None):
    opts = opts or {}
    errors = []
    warnings = []
    if not isinstance(text, str):
        raise ArchError(['input must be D2 text (a string)'])
    if ulen(text) > MAX_INPUT_CHARS:
        raise ArchError(['input is %d characters; the most this converter reads is %d. A diagram this atom can show is far smaller.' % (ulen(text), MAX_INPUT_CHARS)])
    t0 = text[1:] if text.startswith('﻿') else text
    src = re.sub(r'\r\n?', '\n', unicodedata.normalize('NFC', t0))
    for idx, l in enumerate(src.split('\n')):
        if ulen(l) > MAX_LINE_CHARS:
            raise ArchError(['line %d: %d characters; the most one line may hold is %d. Split it over several lines.' % (idx + 1, ulen(l), MAX_LINE_CHARS)])
    st = {'i': 0, 'line': 1}
    nodes = {}
    edges = []
    msgs = []
    step_dirs = []
    flags = {'titleTagged': False, 'labelTagged': False, 'openWarned': False}
    meta = {'title': None, 'numbered': None, 'pace': None, 'duration': None, 'relationColumn': None, 'relationName': None, 'direction': 'LR'}
    rel_dirs = []
    ref_raw = ['']

    def add_err(m):
        errors.append(m)
        if len(errors) >= MAX_ERRORS:
            raise ArchError(errors[:MAX_ERRORS], warnings)

    def fail(m, ln=None):
        add_err('line %d: %s' % (st['line'] if ln is None else ln, m))

    def warn(m, ln=None):
        warnings.append('line %d: %s' % (st['line'] if ln is None else ln, m))

    n_src = len(src)

    def peek():
        i = st['i']
        return src[i] if 0 <= i < n_src else None

    def adv():
        i = st['i']
        c = src[i] if i < n_src else None
        st['i'] = i + 1
        if c == '\n':
            st['line'] += 1
        return c

    def mark_label():
        flags['labelTagged'] = True

    def mark_title():
        flags['titleTagged'] = True

    def skip_space(nl):
        while True:
            c = peek()
            if c == ' ' or c == '\t':
                adv()
            elif nl and (c == '\n' or c == ';'):
                adv()
            elif c == '#':
                start = st['i']
                e = src.find('\n', st['i'])
                if e < 0:
                    e = n_src
                directive(trim(src[start + 1:e]), st['line'])
                while st['i'] < e:
                    st['i'] += 1
            else:
                break

    DIR_RE = rx(r'^(title|msg|numbered|pace|duration|step|relation-column|relation-name|rel)\s*:\s*(.*)$', re.I)
    MSG_RE = rx(r'^(\S+?)\s*->\s*(\S+?)\s+"([^"]*)"(?:\s+(back))?\s*$')
    REL_RE = rx(r'^(\S+?)\s*->\s*(\S+?)\s+(.+?)\s*$')
    STEP_RE = rx(r'^(\S+?)\s*->\s*(\S+?)\s+(\d+)\s*$')

    def clean(t, mark):
        return trim(rx(r'\s+').sub(' ', strip_tags_deep(t, mark)))

    def directive(body, ln):
        m = DIR_RE.match(body)
        if not m:
            return
        k = m.group(1).lower()
        v = trim(m.group(2))
        if k == 'title':
            if v:
                tt = clean(v, mark_title)
                if tt:
                    meta['title'] = tt
        elif k == 'msg':
            mm = MSG_RE.match(v)
            if not mm:
                fail('bad "# msg:" directive; write it as  # msg: fromId->toId "payload text"', ln)
            else:
                msgs.append({'line': ln, 'from': mm.group(1), 'to': mm.group(2), 'text': clean(mm.group(3), mark_label), 'back': bool(mm.group(4))})
        elif k == 'numbered':
            b = v.lower()
            if b in ('on', 'true', 'yes'):
                meta['numbered'] = True
            elif b in ('off', 'false', 'no'):
                meta['numbered'] = False
            else:
                fail('"# numbered:" must be on or off', ln)
        elif k == 'pace':
            if v.lower() in PACES:
                meta['pace'] = v.lower()
            else:
                fail('"# pace:" must be one of ' + ', '.join(PACES), ln)
        elif k == 'duration':
            d = _js_number(rx(r'\s*s$', re.I).sub('', v, count=1))
            if d is not None and 2 <= d <= 120:
                meta['duration'] = d
            else:
                fail('"# duration:" must be a number of seconds from 2 to 120', ln)
        elif k == 'relation-column':
            b = v.lower()
            if b in ('on', 'true', 'yes'):
                meta['relationColumn'] = True
            elif b in ('off', 'false', 'no'):
                meta['relationColumn'] = False
            else:
                fail('"# relation-column:" must be on or off', ln)
        elif k == 'relation-name':
            v2 = clean(v, mark_label)
            if v2 and ulen(v2) <= LIMITS['relation']:
                meta['relationName'] = v2
            else:
                fail('"# relation-name:" must be 1 to %d characters' % LIMITS['relation'], ln)
        elif k == 'rel':
            mm = REL_RE.match(v)
            m3 = clean(mm.group(3), mark_label) if mm else None
            if not mm or not m3:
                fail('bad "# rel:" directive; write it as  # rel: fromId->toId calls', ln)
            elif ulen(m3) > LIMITS['relation']:
                fail('"# rel:" text is %d characters; the most is %d' % (ulen(m3), LIMITS['relation']), ln)
            else:
                rel_dirs.append({'line': ln, 'from': mm.group(1), 'to': mm.group(2), 'text': m3})
        elif k == 'step':
            mm = STEP_RE.match(v)
            if not mm:
                fail('bad "# step:" directive; write it as  # step: fromId->toId 3', ln)
            else:
                step_dirs.append({'line': ln, 'from': mm.group(1), 'to': mm.group(2), 'step': int(mm.group(3))})

    STOP_REF = rx(r'[\s:;{}#]')

    def read_ref():
        start0 = st['i']
        segs = []
        cur = ''
        quoted = False
        while True:
            c = peek()
            if c is None:
                break
            if c == '"':
                adv()
                t = ''
                while peek() is not None and peek() != '"':
                    if peek() == '\\':
                        adv()
                    t = _cat(t, adv())
                if peek() != '"':
                    fail('a quote is never closed; add a closing "')
                    break
                adv()
                cur += t
                quoted = True
                continue
            if c == '.':
                adv()
                segs.append(cur)
                cur = ''
                if len(segs) >= MAX_SEGMENTS:
                    raise ArchError(['line %d: a dotted path may have at most %d parts; shorten it' % (st['line'], MAX_SEGMENTS)])
                continue
            if STOP_REF.match(c):
                break
            cur = _cat(cur, adv())
        segs.append(cur)
        ref_raw[0] = src[start0:st['i']]
        return [s for s in segs if s != '' or quoted]

    def skip_line():
        while peek() is not None and peek() != '\n':
            adv()

    def bad_ref(ln):
        raw = ref_raw[0]
        bare = '"' not in raw
        if bare and re.search(r'->|<-|--', raw):
            fail('"%s": put spaces around the arrow, for example  a -> b  (without spaces D2 would read it as one shape name)' % raw, ln)
            return True
        if bare and '*' in raw:
            fail('"%s": globs (*) are not supported in this D2 subset; name the shapes one by one' % raw, ln)
            return True
        if raw.startswith('...') or raw.startswith('@'):
            fail('"%s": imports (...@file, @file) are not supported in this D2 subset; paste the content in' % raw, ln)
            return True
        return False

    def read_value():
        skip_space(False)
        t = ''
        if peek() == '"':
            adv()
            while peek() is not None and peek() != '"':
                if peek() == '\\':
                    adv()
                    n = adv()
                    t += '\n' if n == 'n' else ('undefined' if n is None else n)
                else:
                    t = _cat(t, adv())
            if peek() != '"':
                fail('a quote is never closed; add a closing "')
            else:
                adv()
            return t
        if peek() == '@':
            fail('imports (a: @file) are not supported in this D2 subset; paste the content in')
            while peek() is not None and peek() != '\n':
                adv()
            return ''
        if peek() == '|':
            fail('markdown/code blocks ("|md ... |") are not supported; use a plain label')
            while peek() is not None and peek() != '\n':
                adv()
            return ''
        while peek() is not None and peek() not in '\n;{}' and not (peek() == '#' and _WS1.match((src[st['i'] - 1] if st['i'] - 1 < n_src and st['i'] >= 1 else None) or ' ')):
            t = _cat(t, adv())
        return trim(t)

    def read_op():
        skip_space(False)
        for op in OPS:
            if src.startswith(op, st['i']):
                nx = src[st['i'] + len(op)] if st['i'] + len(op) < n_src else ' '
                if _WS1.match(nx):
                    st['i'] += len(op)
                    return op
        return None

    def key_of(scope, segs):
        return SEP.join([*scope['path'], *segs])

    def ensure_node(path, ln):
        n = nodes.get(path)
        if n is None:
            segs = path.split(SEP)
            parent = SEP.join(segs[:-1]) if len(segs) > 1 else None
            n = _Node(path, segs[-1], len(nodes), ln, parent)
            nodes[path] = n
            if parent:
                p = ensure_node(parent, ln)
                p.children += 1
        return n

    def strip_tags(t):
        return trim(re.sub(r'[ \t]+', ' ', strip_tags_deep(t, mark_label)))

    def edge_text(t):
        return strip_tags(_BR_G.sub(' ', str(t))) or None

    def set_label(n, v):
        parts = [x for x in (trim(strip_tags(p)) for p in _BR_G.sub('\n', v).split('\n')) if x]
        n.label = parts[0] if parts else n.leaf
        n.sub = ' '.join(parts[1:]) if len(parts) > 1 else None

    def skip_block():
        skip_space(False)
        if peek() != '{':
            return
        d = 0
        while True:
            c = adv()
            if c == '{':
                d += 1
            elif c == '}':
                d -= 1
            if not (d > 0 and peek() is not None):
                break

    def attribute(scope, segs, val, ln):
        key = '.'.join(segs).lower()
        owner = scope.get('owner')
        is_edge = scope.get('type') == 'edge'
        if key == 'direction':
            dk = (val or '').lower()
            d = DIRS.get(dk)
            if d:
                meta['direction'] = d
            else:
                fail('direction must be right, left, down or up', ln)
            return
        if owner is None:
            return
        if key == 'style' or key == 'style.stroke-dash' or scope.get('stylePrefix'):
            if key == 'style.stroke-dash' or (scope.get('stylePrefix') and key == 'stroke-dash'):
                if is_edge and val != '0':
                    owner.style = 'async'
            return
        if key.startswith('style.'):
            return
        if is_edge:
            if key == 'label' and val is not None:
                owner.label = edge_text(val)
            return
        if key == 'label':
            if val is not None:
                set_label(owner, val)
        elif key == 'shape':
            if val and trim(val).lower() in ('sql_table', 'class'):
                fail('shape: %s is not supported in this D2 subset (tables and classes have rows); draw it as a plain shape with a label' % trim(val), ln)
            elif val:
                owner.shape = val.lower()
        elif key == 'class' or key == 'kind':
            if val:
                owner.hints.append(trim(val).lower())

    def connection(scope, first_segs, op0, ln):
        refs = [first_segs]
        ops = [op0]
        while True:
            skip_space(False)
            segs = read_ref()
            if bad_ref(ln):
                skip_line()
                return
            if not segs:
                fail('a connection needs a shape on both sides of the arrow', ln)
                return
            refs.append(segs)
            op = read_op()
            if not op:
                break
            ops.append(op)
        skip_space(False)
        label = None
        if peek() == ':':
            adv()
            label = edge_text(read_value())
        skip_space(False)
        made = []
        for k in range(len(ops)):
            a = key_of(scope, refs[k])
            b = key_of(scope, refs[k + 1])
            op = ops[k]
            ensure_node(a, ln)
            ensure_node(b, ln)
            if op == '<-':
                a, b = b, a
                op = '->'
            if op == '--' and not flags['openWarned']:
                flags['openWarned'] = True
                warn('"--" lines have no arrowhead in D2, but motion_arch always draws one; the edge is drawn as an arrow.', ln)
            e = {'from': a, 'to': b, 'label': label or None, 'style': 'sync', 'both': True if op == '<->' else None, 'line': ln}
            edges.append(e)
            made.append(e)
        if peek() == '{':
            adv()
            sub = {'type': 'edge', 'path': scope['path'], 'owner': _EdgeOwner(made)}
            parse_block(sub, False, 1)

    def parse_block(scope, top, depth=0):
        if depth > MAX_DEPTH:
            raise ArchError(['line %d: braces are nested more than %d deep; flatten the diagram' % (st['line'], MAX_DEPTH)])
        while True:
            skip_space(True)
            c = peek()
            if c is None:
                if not top:
                    fail('a "{" is never closed; add a closing "}"')
                return
            if c == '}':
                if top:
                    fail('"}" without a matching "{"')
                    adv()
                    continue
                adv()
                return
            ln = st['line']
            if src.startswith('"""', st['i']):
                e = src.find('"""', st['i'] + 3)
                fail('block comments (""" ... """) are not supported in this D2 subset; use # line comments', ln)
                if e < 0:
                    st['i'] = n_src
                else:
                    while st['i'] < e + 3:
                        adv()
                continue
            if peek() == '(':
                fail('references to a connection, such as  (a -> b)[0].style...,  are not supported in this D2 subset', ln)
                skip_line()
                continue
            segs = read_ref()
            if bad_ref(ln):
                skip_line()
                continue
            if not segs:
                fail('cannot read "%s"; expected a shape name or a connection' % src[st['i']:st['i'] + 20].split('\n')[0], ln)
                while peek() is not None and peek() != '\n':
                    adv()
                continue
            op = read_op()
            if op:
                connection(scope, segs, op, ln)
                continue
            skip_space(False)
            val = None
            if peek() == ':':
                adv()
                val = read_value()
            skip_space(False)
            first = segs[0].lower()
            if first in UNSUPPORTED:
                fail('"%s" is not supported in this D2 subset' % segs[0], ln)
                skip_block()
                continue
            if scope.get('stylePrefix'):
                attribute(scope, segs, val, ln)
                continue
            cut = -1 if scope.get('type') == 'edge' else next((k for k, x in enumerate(segs) if k >= 1 and x.lower() in RESERVED), -1)
            if cut >= 1:
                opath = key_of(scope, segs[:cut])
                owner = ensure_node(opath, ln)
                prop = segs[cut:]
                sc = {'type': 'node', 'path': opath.split(SEP), 'owner': owner}
                attribute(sc, prop, val, ln)
                if peek() == '{':
                    adv()
                    parse_block({**sc, 'stylePrefix': prop[0].lower() == 'style'}, False, depth + 1)
                continue
            if first in RESERVED and (scope.get('type') != 'root' or first in ('direction', 'title') or len(segs) > 1 or scope.get('owner') is not None):
                attribute(scope, segs, val, ln)
                if peek() == '{':
                    adv()
                    parse_block({**scope, 'stylePrefix': first == 'style'}, False, depth + 1)
                continue
            if scope.get('type') == 'root' and first == 'direction':
                attribute(scope, segs, val, ln)
                continue
            path = key_of(scope, segs)
            n = ensure_node(path, ln)
            if val is not None and val != '':
                set_label(n, val)
            if peek() == '{':
                adv()
                parse_block({'type': 'node', 'path': path.split(SEP), 'owner': n}, False, depth + 1)

    parse_block({'type': 'root', 'path': []}, True)
    if not nodes and not errors:
        fail('no shapes found; write for example  a: Alpha  and  a -> b', 1)
    if errors:
        raise ArchError(errors[:20], warnings)

    # ---- canonical graph
    leaf_count = {}
    for n in nodes.values():
        if not n.children:
            leaf_count[n.leaf] = leaf_count.get(n.leaf, 0) + 1

    def orig_of(n):
        return _disp(n.path) if leaf_count.get(n.leaf, 0) > 1 else n.leaf
    map_node = make_id_mapper()
    map_group = make_id_mapper()

    def outer(n):
        p = n
        while p.parent:
            p = nodes[p.parent]
        return p
    group_nodes = [n for n in nodes.values() if n.children and not n.parent]
    for g in group_nodes:
        stack = [x for x in nodes.values() if x.parent and outer(x) is g and x.children]
        for sg in stack:
            warn('container "%s" is inside "%s"; nested groups are flattened, its shapes are drawn in the outer group "%s".' % (sg.leaf, g.leaf, g.leaf), sg.line)
    groups = [{'id': map_group(g.leaf), 'label': g.label or g.leaf, 'path': g.path} for g in group_nodes]
    leaves = sorted((n for n in nodes.values() if not n.children), key=lambda x: x.order)
    by_path = {n.path: n for n in leaves}
    n_out = []
    for n in leaves:
        kind = None
        for h in n.hints:
            k = resolve_kind(h)
            if k:
                kind = k
            else:
                warn('"%s" is not a known kind; ignored.' % h, n.line)
        if not kind:
            if n.shape and n.shape not in D2_SHAPE_KIND:
                warn('shape "%s" is not known; treated as a plain box.' % n.shape, n.line)
            kind = D2_SHAPE_KIND.get(n.shape or 'rectangle') or 'server'
        o = {'id': map_node(orig_of(n)), 'label': n.label if n.label is not None else n.leaf, 'kind': kind}
        if n.sub:
            o['sub'] = n.sub
        if n.parent:
            o['group'] = next(g for g in groups if g['path'] == outer(n).path)['id']
        n_out.append(o)

    def id_of(path):
        n = by_path.get(path)
        return map_node(orig_of(n)) if n else None
    e_out = []
    for e in edges:
        f, t = id_of(e['from']), id_of(e['to'])
        if not f or not t:
            add_err('line %d: "%s" is a container, not a shape. Edges to a whole container are not supported; connect to a shape inside it.' % (e['line'], _disp(e['from'] if not f else e['to'])))
            continue
        o = {'from': f, 'to': t, 'style': e['style']}
        if e['label']:
            o['label'] = e['label']
        if e['both']:
            o['both'] = True
        e_out.append(o)

    def find_id(ref, ln):
        cand = [n for n in by_path.values() if _disp(n.path) == ref or n.leaf == ref or orig_of(n) == ref or n.leaf.lower() == ref.lower()]
        if cand:
            return map_node(orig_of(cand[0]))
        names = [n.leaf for n in by_path.values()]
        dm = did_you_mean(ref, names)
        add_err('line %d: "%s" is not a shape' % (ln, ref) + (' (did you mean "%s"?)' % dm if dm else ''))
        return None
    m_out = []
    for d in msgs:
        f, t = find_id(d['from'], d['line']), find_id(d['to'], d['line'])
        if f and t:
            m = {'from': f, 'to': t, 'text': d['text']}
            if d['back']:
                m['back'] = True
            m_out.append(m)
    taken = set()
    for d in step_dirs:
        f, t = find_id(d['from'], d['line']), find_id(d['to'], d['line'])
        if not f or not t:
            continue
        idx = next((k for k, e in enumerate(e_out) if e['from'] == f and e['to'] == t and k not in taken), -1)
        if idx < 0:
            add_err('line %d: step directive: there is no (further) edge from "%s" to "%s"' % (d['line'], d['from'], d['to']))
            continue
        taken.add(idx)
        e_out[idx]['step'] = d['step']
    rel_taken = set()
    for d in rel_dirs:
        f, t = find_id(d['from'], d['line']), find_id(d['to'], d['line'])
        if not f or not t:
            continue
        idx = next((k for k, e in enumerate(e_out) if e['from'] == f and e['to'] == t and k not in rel_taken), -1)
        if idx < 0:
            add_err('line %d: rel directive: there is no (further) edge from "%s" to "%s"' % (d['line'], d['from'], d['to']))
            continue
        rel_taken.add(idx)
        e_out[idx]['relation'] = d['text']
    if errors:
        raise ArchError(errors[:20], warnings)
    graph = {'direction': opts.get('direction') or meta['direction'], 'groups': [{'id': g['id'], 'label': g['label']} for g in groups],
             'nodes': n_out, 'edges': e_out, 'messages': m_out}
    if meta['relationColumn'] is not None:
        graph['relationColumn'] = meta['relationColumn']
    if meta['relationName']:
        graph['relationName'] = meta['relationName']
    if meta['numbered'] is not None:
        graph['numbered'] = meta['numbered']
    if meta['pace']:
        graph['pace'] = meta['pace']
    if meta['duration'] is not None:
        graph['duration'] = meta['duration']
    if flags['labelTagged']:
        warnings.append('HTML tags were removed from a label.')
    if flags['titleTagged']:
        warnings.append('HTML tags were removed from the title.')
    ttl = opts.get('title') or meta['title']
    if ttl:
        graph['title'] = ttl
    return {'graph': graph, 'warnings': warnings}
