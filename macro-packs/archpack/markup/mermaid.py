"""Mermaid flowchart subset -> canonical graph (port of mermaid_arch/mermaid.mjs).

Unsupported input gives a plain error naming the line; the parser never raises anything but ArchError.
"""
from __future__ import annotations

import re
import unicodedata

from ._js import is_letter_mark_number, rx, strip_marks, trim, trim_end, ulen, uslice
from .graph import KINDS, LIMITS, PACES, ArchError, did_you_mean, resolve_kind

OTHER_DIAGRAMS = {
    'sequencediagram': 'Draw each participant as a node and each message as an edge in a flowchart.',
    'classdiagram': 'Draw each class as a node and each relation as an edge in a flowchart.',
    'statediagram': 'Draw each state as a node and each transition as an edge in a flowchart.',
    'statediagram-v2': 'Draw each state as a node and each transition as an edge in a flowchart.',
    'erdiagram': 'Draw each entity as a node and each relation as an edge in a flowchart.',
    'gantt': 'Gantt charts are timelines, not architecture; use a flowchart of the components instead.',
    'pie': 'Pie charts are not architecture diagrams.',
    'journey': 'User journeys are not supported; use a flowchart.',
    'gitgraph': 'Git graphs are not supported; use a flowchart.',
    'mindmap': 'Mind maps are not supported; use a flowchart.',
    'timeline': 'Timelines are not supported; use a flowchart.',
    'c4context': 'C4 diagrams are not supported; use a flowchart with subgraphs for the boundaries.',
    'c4container': 'C4 diagrams are not supported; use a flowchart with subgraphs for the boundaries.',
    'c4component': 'C4 diagrams are not supported; use a flowchart with subgraphs for the boundaries.',
    'architecture-beta': 'architecture-beta is not supported; use a flowchart with subgraphs for the groups.',
    'block-beta': 'block-beta is not supported; use a flowchart.',
    'sankey-beta': 'Sankey diagrams are not supported; use a flowchart.',
    'xychart-beta': 'Charts are not supported; use a flowchart.',
    'quadrantchart': 'Quadrant charts are not supported; use a flowchart.',
    'requirementdiagram': 'Requirement diagrams are not supported; use a flowchart.',
    'kanban': 'Kanban boards are not supported; use a flowchart.',
    'packet': 'Packet diagrams are not supported; use a flowchart.',
}

# shape delimiters, longest opener first: (open, closes, shape, degraded-name)
SHAPES = [
    ('(((', [')))'], 'circle', 'double circle'), ('[/', ['/]', '\\]'], 'rect', None), ('[\\', ['\\]', '/]'], 'rect', None),
    ('>', [']'], 'rect', 'asymmetric'),
    ('((', ['))'], 'circle', None), ('([', ['])'], 'stadium', None), ('[(', [')]'], 'cylinder', None), ('[[', [']]'], 'subroutine', None),
    ('{{', ['}}'], 'hexagon', None), ('(', [')'], 'round', None), ('[', [']'], 'rect', None), ('{', ['}'], 'diamond', None),
]
SHAPE_KIND = {
    'cylinder': 'store', 'subroutine': 'tool', 'stadium': 'device', 'circle': 'model', 'hexagon': 'app',
    'round': 'app', 'diamond': 'tool', 'rect': 'server', 'plain': 'server',
}
AT_SHAPES = {
    'cyl': 'cylinder', 'cylinder': 'cylinder', 'lin-cyl': 'cylinder', 'h-cyl': 'cylinder', 'das': 'cylinder', 'database': 'cylinder', 'db': 'cylinder',
    'circle': 'circle', 'circ': 'circle', 'sm-circ': 'circle', 'dbl-circ': 'circle',
    'stadium': 'stadium', 'terminal': 'stadium', 'pill': 'stadium',
    'subproc': 'subroutine', 'subroutine': 'subroutine', 'fr-rect': 'subroutine',
    'hex': 'hexagon', 'hexagon': 'hexagon', 'prepare': 'hexagon',
    'rounded': 'round', 'event': 'round',
    'rect': 'rect', 'rectangle': 'rect', 'proc': 'rect', 'process': 'rect', 'square': 'rect',
    'diamond': 'diamond', 'decision': 'diamond', 'question': 'diamond',
}
SLASH_NAME = {'//': 'parallelogram', '\\\\': 'parallelogram (alt)', '/\\': 'trapezoid', '\\/': 'trapezoid (alt)'}

MAX_INPUT_CHARS = 20000
MAX_LINE_CHARS = 500

_BR = rx(r'<br\s*/?>', re.I)
_TAG = rx(r'</?[A-Za-z!][^>]*(?:>|$)')
_ENT = rx(r'(?:#|&)(amp|lt|gt|quot|apos|nbsp);|(?:#|&#)(\d{1,7});|&#x([0-9a-f]{1,6});', re.I)
_NAMED = {'amp': '&', 'lt': '<', 'gt': '>', 'quot': '"', 'apos': "'", 'nbsp': ' '}
_MD_ITALIC_US = re.compile(r'(^|[^\w])_(.+?)_(?!\w)')   # \w without the ASCII flag = letters, digits, "_" (JS: \p{L}\p{N}_)


def _strip_markdown(t):
    t = re.sub(r'\*\*(.+?)\*\*', r'\1', t)
    t = re.sub(r'__(.+?)__', r'\1', t)
    t = re.sub(r'\*(.+?)\*', r'\1', t)
    return _MD_ITALIC_US.sub(r'\1\2', t)


def _strip_quotes(s):
    t = trim(s)
    if len(t) >= 2 and t[0] == '"' and t[-1] == '"':
        t = trim(t[1:-1])
    if len(t) >= 2 and t[0] == '`' and t[-1] == '`':
        t = _strip_markdown(t[1:-1])
    return t


def decode_entities(s):
    def rep(m):
        name, dec, hx = m.group(1), m.group(2), m.group(3)
        if name:
            return _NAMED[name.lower()]
        cp = int(dec) if dec is not None else int(hx, 16)
        ok = 32 <= cp <= 0x10ffff and not (0xd800 <= cp <= 0xdfff) and not (0x7f <= cp < 0xa0)
        return chr(cp) if ok else ''
    return _ENT.sub(rep, s)


_state = {'tags': False, 'title': False}


def strip_tags_deep(t, on_change=None, pattern=None):
    """Repeats until nothing changes (capped), so "<<script>script>" cannot leave a tag behind."""
    pat = pattern or _TAG
    cur = str(t)
    for _ in range(8):
        def rep(_m):
            if on_change:
                on_change()
            return ''
        nxt = pat.sub(rep, cur)
        if nxt == cur:
            break
        cur = nxt
    return cur


def _strip_tags(t):
    def mark():
        _state['tags'] = True
    return strip_tags_deep(t, mark)


def _tidy(p, is_title=False):
    if is_title:
        def mark():
            _state['title'] = True
        st = lambda t: strip_tags_deep(t, mark)
    else:
        st = _strip_tags
    return _collapse(st(decode_entities(st(p))))


def _collapse(s):
    return trim(rx(r'\s+').sub(' ', s))


def split_label(raw):
    parts = [x for x in (_tidy(p) for p in _BR.split(_strip_quotes(raw))) if x]
    if not parts:
        return {'label': ''}
    if len(parts) == 1:
        return {'label': parts[0]}
    first = rx(r'[\s,;:&\-–—]+$').sub('', parts[0]) or parts[0]
    return {'label': first, 'sub': ' '.join(parts[1:])}


def clean_text(raw):
    return ' '.join(x for x in (_tidy(p) for p in _BR.split(_strip_quotes(raw))) if x != '')


def _split_statements(line):
    out = []
    cur = []
    q = False
    for ch in line:
        if ch == '"':
            q = not q
        if ch == ';' and not q:
            out.append(''.join(cur))
            cur = []
        else:
            cur.append(ch)
    out.append(''.join(cur))
    return [x for x in (trim(s) for s in out) if x]


_WSC = rx(r'\s')


def _strip_trailing_comment(s):
    q = False
    for i in range(len(s) - 1):
        if s[i] == '"':
            q = not q
        if not q and s[i] == '%' and s[i + 1] == '%' and (i == 0 or _WSC.match(s[i - 1])):
            return trim_end(s[:i])
    return s


def _slug(s):
    t = re.sub(r'[^a-z0-9_-]+', '_', s.lower())
    t = re.sub(r'^_+|_+$', '', t)
    return t or 'x'


def make_id_mapper():
    """Deterministic, collision-safe map to the atom id rule ^[a-z][a-z0-9_-]{0,31}$"""
    used = set()
    by_orig = {}

    def mapper(orig):
        if orig in by_orig:
            return by_orig[orig]
        t = strip_marks(unicodedata.normalize('NFD', orig)).lower()
        base = ''.join(c if (c in '_-' or 'a' <= c <= 'z' or '0' <= c <= '9') else ('__' if ord(c) > 0xFFFF else '_') for c in t)
        if not re.match(r'[a-z]', base):
            base = 'n' + base
        base = base[:32]
        id_, k = base, 2
        while id_ in used:
            suf = '_%d' % k
            k += 1
            id_ = base[:32 - len(suf)] + suf
        used.add(id_)
        by_orig[orig] = id_
        return id_
    return mapper


def _at(s, i):
    return s[i] if 0 <= i < len(s) else ''


_CLS_NAME = re.compile(r':::([A-Za-z0-9_-]+)')
_ATSHAPE = rx(r'shape\s*:\s*([\w-]+)')
_ATLABEL = rx(r'label\s*:\s*("([^"]*)"|[^,]+)')


class _Ref(dict):
    pass


def parse_mermaid(text, opts=None):
    """-> {'graph': ..., 'warnings': [...]}; raises ArchError."""
    opts = opts or {}
    _state['tags'] = False
    _state['title'] = False
    style_line = 0
    click_line = 0
    errors = []
    warnings = []

    def fail(line, msg):
        errors.append('line %d: %s' % (line, msg))

    def warn(line, msg):
        warnings.append('line %d: %s' % (line, msg))

    if not isinstance(text, str):
        raise ArchError(['input must be Mermaid text (a string)'])
    if ulen(text) > MAX_INPUT_CHARS:
        raise ArchError(['input is %d characters; the most this converter reads is %d. A diagram this atom can show is far smaller.' % (ulen(text), MAX_INPUT_CHARS)])
    t0 = text[1:] if text.startswith('﻿') else text
    t0 = unicodedata.normalize('NFC', t0)
    lines = re.sub(r'\r\n?', '\n', t0).split('\n')
    for idx, l in enumerate(lines):
        if ulen(l) > MAX_LINE_CHARS:
            raise ArchError(['line %d: %d characters; the most one line may hold is %d. Split it over several lines.' % (idx + 1, ulen(l), MAX_LINE_CHARS)])

    nodes = {}          # orig -> node dict
    edges = []
    groups_by_key = {}
    group_stack = []
    class_stmts = []
    msg_directives = []
    step_directives = []
    title = None
    numbered = pace = duration = relation_column = relation_name = None
    direction = 'TB'
    header_seen = False
    open_link_warned = False
    rel_directives = []

    def touch_node(orig, line):
        n = nodes.get(orig)
        if n is None:
            n = {'orig': orig, 'label': None, 'sub': None, 'shape': None, 'hints': [], 'group': None, 'order': len(nodes), 'line': line}
            nodes[orig] = n
        if group_stack:
            outer = group_stack[0]['key']
            if n['group'] is None:
                n['group'] = outer
            elif n['group'] != outer:
                warn(line, 'node "%s" is listed in more than one subgraph; keeping it in "%s".' % (orig, groups_by_key[n['group']]['label']))
        return n

    def parse_node_ref(s, i0, line):
        i = i0
        while _at(s, i) in (' ', '\t'):
            i += 1
        start = i
        while i < len(s):
            cp = s[i]
            if is_letter_mark_number(cp):
                i += 1
            elif cp == '-' and i + 1 < len(s) and is_letter_mark_number(s[i + 1]) and i > start:
                i += 1
            else:
                break
        if i == start:
            fail(line, 'expected a node id at "%s"; node ids are letters, digits and underscores (write A[Label] or A --> B)' % uslice(trim(s[i0:]), 0, 20))
            return None
        orig = s[start:i]
        ref = _Ref(orig=orig, hints=[])
        for open_, closes, shape, degraded in SHAPES:
            if not s.startswith(open_, i):
                continue
            close = closes[0]
            j = i + len(open_)
            while _at(s, j) == ' ':
                j += 1
            if _at(s, j) == '"':
                e = s.find('"', j + 1)
                if e < 0:
                    fail(line, 'node "%s": the quote opened here is never closed; add a closing "' % orig)
                    return None
                txt = s[j + 1:e]
                k = e + 1
                while _at(s, k) == ' ':
                    k += 1
                close = next((c for c in closes if s.startswith(c, k)), close)
                if not s.startswith(close, k):
                    fail(line, 'node "%s": expected "%s" after the quoted text' % (orig, close))
                    return None
                i = k + len(close)
            else:
                e = -1
                for c in closes:
                    x = s.find(c, j)
                    if x >= 0 and (e < 0 or x < e):
                        e = x
                        close = c
                if e < 0 and open_[0] == '[' and len(open_) == 2 and open_[1] in '/\\':
                    continue   # "[/path]" is a plain box
                if e < 0:
                    fail(line, 'node "%s": missing closing "%s"; if the text contains brackets or parentheses, wrap it in quotes: %s["text (like this)"]' % (orig, close, orig))
                    return None
                txt = s[j:e]
                i = e + len(close)
            ref['shape'] = shape
            name = degraded or (SLASH_NAME.get(open_[1] + close[0]) if (len(open_) == 2 and open_[0] == '[' and open_[1] in '/\\') else None)
            if name:
                warn(line, 'Node "%s" uses a shape the atom cannot draw (%s); drawn as a %s.' % (orig, name, 'circle' if shape == 'circle' else 'rectangle'))
            ref.update(split_label(txt))
            break
        if s.startswith('@{', i):
            e = s.find('}', i)
            if e < 0:
                fail(line, 'node "%s": "@{" is never closed with "}"' % orig)
                return None
            body = s[i + 2:e]
            sm = _ATSHAPE.search(body)
            lm = _ATLABEL.search(body)
            if sm:
                shk = sm.group(1).lower()
                sh = AT_SHAPES.get(shk)
                if sh:
                    ref['shape'] = sh
                else:
                    ref['shape'] = 'rect'
                    warn(line, 'node "%s": shape "%s" is not known; treated as a plain box.' % (orig, sm.group(1)))
            if lm:
                ref.update(split_label(lm.group(2) if lm.group(2) is not None else lm.group(1)))
            i = e + 1
        while s.startswith(':::', i):
            m = _CLS_NAME.match(s, i)
            if not m:
                fail(line, 'node "%s": ":::" must be followed by a class name, for example %s:::server' % (orig, orig))
                return None
            ref['hints'].append(m.group(1))
            i += len(m.group(0))
        ref['end'] = i
        return ref

    def apply_ref(ref, line):
        n = touch_node(ref['orig'], line)
        if ref.get('label') is not None and ref.get('label') != '':
            n['label'] = ref['label']
            n['sub'] = ref.get('sub')
        if ref.get('shape'):
            n['shape'] = ref['shape']
        n['hints'].extend(ref['hints'])
        return n

    L1 = rx(r'^(<?)--\s+(.+?)\s+(-{2,}>|-{3,})(?=\s|$|[A-Za-z0-9_])')
    L1b = rx(r'^(<?)--\s*>')
    L2 = rx(r'^(<?)-\.\s+(.+?)\s+(\.-+>?)(?=\s|$|[A-Za-z0-9_])')
    L3 = rx(r'^(<?)==\s+(.+?)\s+(={2,}>|={3,})(?=\s|$|[A-Za-z0-9_])')
    L4 = rx(r'^(<?)(-\.+-+>?)')
    L5 = rx(r'^(<?)(-{2,}>|-{3,})')
    L6 = rx(r'^(<?)(={2,}>|={3,})')

    def match_link(rest):
        m = L1.match(rest)
        if m and not L1b.match(rest):
            return {'len': len(m.group(0)), 'both': bool(m.group(1)) and m.group(3).endswith('>'), 'style': 'sync', 'open': not m.group(3).endswith('>'), 'label': m.group(2)}
        m = L2.match(rest)
        if m:
            return {'len': len(m.group(0)), 'both': bool(m.group(1)) and m.group(3).endswith('>'), 'style': 'async', 'open': not m.group(3).endswith('>'), 'label': m.group(2)}
        m = L3.match(rest)
        if m:
            return {'len': len(m.group(0)), 'both': bool(m.group(1)) and m.group(3).endswith('>'), 'style': 'sync', 'open': not m.group(3).endswith('>'), 'label': m.group(2)}
        m = L4.match(rest)
        if m:
            return {'len': len(m.group(0)), 'both': bool(m.group(1)) and m.group(2).endswith('>'), 'style': 'async', 'open': not m.group(2).endswith('>')}
        m = L5.match(rest)
        if m:
            return {'len': len(m.group(0)), 'both': bool(m.group(1)) and m.group(2).endswith('>'), 'style': 'sync', 'open': not m.group(2).endswith('>')}
        m = L6.match(rest)
        if m:
            return {'len': len(m.group(0)), 'both': bool(m.group(1)) and m.group(2).endswith('>'), 'style': 'sync', 'open': not m.group(2).endswith('>')}
        return None

    EDGE_ID = rx(r'^[A-Za-z0-9_-]+@(-|=|<)')
    INVIS = rx(r'^~{3,}')
    CROSS1 = rx(r'^(<?)(-{2,}|={2,}|-\.+-*)[xo](\s|$)')
    CROSS2 = rx(r'^[xo](-{2,}|={2,}|-\.+-*)[xo]?(\s|$)')
    PIPE = rx(r'^\s*\|([^|]*)\|')

    def parse_chain(s, line):
        nonlocal open_link_warned
        pos = [0]

        def read_group():
            refs = []
            while True:
                ref = parse_node_ref(s, pos[0], line)
                if not ref:
                    return None
                refs.append(ref)
                pos[0] = ref['end']
                while _at(s, pos[0]) in (' ', '\t'):
                    pos[0] += 1
                if _at(s, pos[0]) == '&':
                    pos[0] += 1
                    continue
                break
            return refs
        prev = read_group()
        if not prev:
            return
        for r in prev:
            apply_ref(r, line)
        while True:
            while _at(s, pos[0]) in (' ', '\t'):
                pos[0] += 1
            if pos[0] >= len(s):
                return
            rest = s[pos[0]:]
            if EDGE_ID.match(rest):
                fail(line, 'edge ids ("e1@-->") are not supported; remove the "e1@" part')
                return
            if INVIS.match(rest):
                fail(line, 'invisible links (~~~) are not supported; remove the line or use a normal arrow.')
                return
            if CROSS1.match(rest) or CROSS2.match(rest):
                fail(line, 'arrows with a cross or circle end ("--x", "--o", "x--x", "o--o") are not supported; use --> or <-->.')
                return
            lk = match_link(rest)
            if not lk:
                fail(line, 'cannot read "%s"; expected an arrow such as -->, -.->, ==> or --- between nodes' % uslice(rest, 0, 24))
                return
            pos[0] += lk['len']
            label = lk.get('label')
            pm = PIPE.match(s[pos[0]:])
            if pm:
                if label is not None:
                    fail(line, 'an edge has its label written twice (in the line and in |bars|); keep one')
                    return
                label = pm.group(1)
                pos[0] += len(pm.group(0))
            if lk['open'] and not open_link_warned:
                open_link_warned = True
                warn(line, '"---" lines have no arrowhead in Mermaid, but motion_arch always draws one; the edge is drawn as an arrow.')
            nxt = read_group()
            if not nxt:
                return
            for r in nxt:
                apply_ref(r, line)
            lab = clean_text(label) if label is not None else ''
            for a in prev:
                for b in nxt:
                    e = {'from': a['orig'], 'to': b['orig'], 'label': lab or None, 'style': lk['style'], 'both': True if lk['both'] else None, 'line': line}
                    edges.append(e)
            prev = nxt

    # ---- header
    li = 0

    def Ln():
        return li + 1
    first_real = next((k for k, l in enumerate(lines) if trim(l) != ''), -1)
    if first_real >= 0 and trim(lines[first_real]) == '---':
        e = -1
        for k in range(first_real + 1, len(lines)):
            if trim(lines[k]) == '---':
                e = k
                break
        if e < 0:
            fail(first_real + 1, 'front matter starts with "---" but is never closed; add a closing "---" line')
        else:
            for k in range(first_real + 1, e):
                m = rx(r'^\s*title\s*:\s*(.+?)\s*$').match(lines[k])
                if m:
                    title = _tidy(_strip_quotes(m.group(1)), True)
            li = e + 1

    DIRECTIVE = rx(r'^%%\s*(title|msg|numbered|pace|duration|step|relation-column|relation-name|rel)\s*:\s*(.*)$', re.I)
    MSG = rx(r'^(\S+?)\s*->\s*(\S+?)\s+"([^"]*)"(?:\s+(back))?\s*$')
    REL = rx(r'^(\S+?)\s*->\s*(\S+?)\s+(.+?)\s*$')
    STEP = rx(r'^(\S+?)\s*->\s*(\S+?)\s+(\d+)\s*$')
    HEADER = rx(r'^(flowchart|graph)(?:-elk)?(?:\s+(LR|RL|TB|TD|BT))?\s*;?$', re.I)
    HEADER_WORD = rx(r'^([A-Za-z][\w-]*)')
    HEADER_ANY = rx(r'^(flowchart|graph)', re.I)
    DIRECTIVE_LINE = rx(r'^%%\{.*\}%%$')
    SUBGRAPH = rx(r'^subgraph\b\s*(.*)$')
    SG1 = rx(r'^([A-Za-z0-9_-]+)\s*\[\s*(.*?)\s*\]$')
    SG2 = rx(r'^"(.*)"$')
    END = rx(r'^end$', re.I)
    DIRN = rx(r'^direction\b', re.I)
    STYLE_ST = rx(r'^(classDef|style|linkStyle)\b')
    ACC = rx(r'^(accTitle|accDescr)\b')
    CLASS_ST = rx(r'^class\s+([^\s]+)\s+([A-Za-z0-9_-]+)$')
    CLASS_ANY = rx(r'^class\b')
    CLICK = rx(r'^click\b')

    def on_off(v):
        v = v.lower()
        if v in ('on', 'true', 'yes'):
            return True
        if v in ('off', 'false', 'no'):
            return False
        return None

    while li < len(lines):
        line = trim(lines[li])
        if not line:
            li += 1
            continue
        if line.startswith('%%'):
            d = DIRECTIVE.match(line)
            key = d.group(1).lower() if d else None
            if key == 'title':
                if trim(d.group(2)):
                    title = _tidy(trim(d.group(2)), True)
            elif key == 'msg':
                m = MSG.match(trim(d.group(2)))
                if not m:
                    fail(Ln(), 'bad "%% msg:" directive; write it as  %% msg: fromId->toId "payload text"  (add the word back at the end for a reply)')
                else:
                    msg_directives.append({'line': Ln(), 'from': m.group(1), 'to': m.group(2), 'text': clean_text(m.group(3)), 'back': bool(m.group(4))})
            elif key == 'numbered':
                v = on_off(trim(d.group(2)))
                if v is None:
                    fail(Ln(), '"%% numbered:" must be on or off')
                else:
                    numbered = v
            elif key == 'pace':
                v = trim(d.group(2)).lower()
                if v in PACES:
                    pace = v
                else:
                    fail(Ln(), '"%% pace:" must be one of ' + ', '.join(PACES))
            elif key == 'duration':
                v = _js_number(rx(r'\s*s$', re.I).sub('', trim(d.group(2)), count=1))
                if v is not None and 2 <= v <= 120:
                    duration = v
                else:
                    fail(Ln(), '"%% duration:" must be a number of seconds from 2 to 120, for example %% duration: 40')
            elif key == 'relation-column':
                v = on_off(trim(d.group(2)))
                if v is None:
                    fail(Ln(), '"%% relation-column:" must be on or off')
                else:
                    relation_column = v
            elif key == 'relation-name':
                v2 = _strip_tags(trim(d.group(2)))
                if v2 and ulen(v2) <= LIMITS['relation']:
                    relation_name = v2
                else:
                    fail(Ln(), '"%% relation-name:" must be 1 to {} characters, for example %% relation-name: Interaction'.format(LIMITS['relation']))
            elif key == 'rel':
                m = REL.match(trim(d.group(2)))
                m3 = _collapse(_strip_tags(m.group(3))) if m else None
                if not m or not m3:
                    fail(Ln(), 'bad "%% rel:" directive; write it as  %% rel: fromId->toId calls  (free text, at most 20 characters)')
                elif ulen(m3) > LIMITS['relation']:
                    fail(Ln(), '"%% rel:" text "{}" is {} characters; the most is {}'.format(m3, ulen(m3), LIMITS['relation']))
                else:
                    rel_directives.append({'line': Ln(), 'from': m.group(1), 'to': m.group(2), 'text': m3})
            elif key == 'step':
                m = STEP.match(trim(d.group(2)))
                if not m:
                    fail(Ln(), 'bad "%% step:" directive; write it as  %% step: fromId->toId 3')
                else:
                    step_directives.append({'line': Ln(), 'from': m.group(1), 'to': m.group(2), 'step': int(m.group(3))})
            li += 1
            continue
        line = _strip_trailing_comment(line)
        if not header_seen:
            hm = HEADER.match(line)
            if hm:
                header_seen = True
                d = (hm.group(2) or 'TB').upper()
                direction = 'TB' if d == 'TD' else d
                li += 1
                continue
            wm = HEADER_WORD.match(line)
            word = wm.group(1) if wm else uslice(line, 0, 20)
            k = word.lower()
            if HEADER_ANY.match(line):
                fail(Ln(), 'cannot read the header "%s"; write "flowchart LR" (or TD, TB, RL, BT)' % line)
            elif k in OTHER_DIAGRAMS:
                fail(Ln(), '"%s" diagrams are not supported; only flowcharts are. %s' % (word, OTHER_DIAGRAMS[k]))
            elif line.startswith('%%{'):
                li += 1
                continue
            else:
                fail(Ln(), 'expected "flowchart LR" (or "graph TD") on the first line, found "%s"' % uslice(line, 0, 30))
            break
        for stmt in _split_statements(line):
            if DIRECTIVE_LINE.match(stmt):
                continue
            m = SUBGRAPH.match(stmt)
            if m:
                rest = trim(m.group(1))
                mm = SG1.match(rest)
                if mm:
                    key, label = mm.group(1), clean_text(mm.group(2))
                else:
                    mm = SG2.match(rest)
                    if mm:
                        label = clean_text(mm.group(1))
                        key = _slug(label)
                    elif rest:
                        label = clean_text(rest)
                        key = _slug(rest) if ' ' in rest else rest
                    else:
                        fail(Ln(), 'a subgraph needs a name; write: subgraph id[Title]')
                        key = 'sg%d' % len(groups_by_key)
                        label = key
                nested = len(group_stack) > 0
                if nested:
                    warn(Ln(), 'subgraph "%s" is inside "%s"; nested groups are flattened, its nodes are drawn in the outer group "%s".' % (label, group_stack[0]['label'], group_stack[0]['label']))
                elif key not in groups_by_key:
                    groups_by_key[key] = {'key': key, 'label': label, 'order': len(groups_by_key), 'line': Ln()}
                else:
                    warn(Ln(), 'subgraph "%s" is declared twice; the second block adds to the first.' % key)
                group_stack.append({'key': group_stack[0]['key'] if nested else key, 'label': group_stack[0]['label'] if nested else label, 'nested': nested})
                continue
            if END.match(stmt):
                if not group_stack:
                    fail(Ln(), '"end" without a matching "subgraph"; remove it or add the subgraph line above')
                else:
                    group_stack.pop()
                continue
            if DIRN.match(stmt):
                warn(Ln(), '"%s" inside a subgraph is ignored; the whole diagram uses the direction on the first line.' % stmt)
                continue
            if STYLE_ST.match(stmt):
                style_line = style_line or Ln()
                continue
            if ACC.match(stmt):
                continue
            m = CLASS_ST.match(stmt)
            if m:
                if not resolve_kind(m.group(2)):
                    style_line = style_line or Ln()
                class_stmts.append({'line': Ln(), 'ids': [x for x in m.group(1).split(',') if x], 'cls': m.group(2)})
                continue
            if CLASS_ANY.match(stmt):
                fail(Ln(), 'write class statements as: class nodeId kind  (for example: class db store)')
                continue
            if CLICK.match(stmt):
                click_line = click_line or Ln()
                continue
            parse_chain(stmt, Ln())
        li += 1
    if not header_seen and not errors:
        fail(1, 'empty input; start with "flowchart LR" and add nodes and arrows')
    if group_stack:
        fail(len(lines), '%d "subgraph" block(s) are never closed; add an "end" line for each' % len(group_stack))

    if style_line:
        warnings.append('Colours and styles (classDef, style, linkStyle) are not drawn; the diagram uses its own colours by node kind.' + (' click/link statements are ignored too.' if click_line else ''))
    elif click_line:
        warn(click_line, 'click/link statements are ignored.')
    if _state['tags']:
        warnings.append('HTML tags were removed from a label.')
    if _state['title']:
        warnings.append('HTML tags were removed from the title.')

    for cs in class_stmts:
        for id_ in cs['ids']:
            n = nodes.get(id_)
            if n:
                n['hints'].append(cs['cls'])
            else:
                dm = did_you_mean(id_, list(nodes.keys()))
                warn(cs['line'], 'class statement names "%s", which is not a node' % id_ + (' (did you mean "%s"?)' % dm if dm else '') + '; ignored.')

    if errors:
        raise ArchError(errors[:20], warnings)

    # ---- build canonical graph
    map_node = make_id_mapper()
    map_group = make_id_mapper()
    groups = sorted(groups_by_key.values(), key=lambda g: g['order'])
    used_groups = {n['group'] for n in nodes.values() if n['group'] is not None}
    g_out = []
    for g in groups:
        if g['key'] not in used_groups:
            warn(g['line'], 'subgraph "%s" has no nodes; it is dropped.' % g['label'])
            continue
        g_out.append({'id': map_group(g['key']), 'label': g['label']})
    n_out = []
    for n in sorted(nodes.values(), key=lambda x: x['order']):
        kind = None
        for h in n['hints']:
            k = resolve_kind(h)
            if k:
                kind = k
        if not kind:
            kind = SHAPE_KIND[(n['shape'] or 'plain') if (n['shape'] or 'plain') in SHAPE_KIND else 'plain']
        label = n['label'] if n['label'] is not None else n['orig']
        o = {'id': map_node(n['orig']), 'label': label, 'kind': kind}
        if n['sub']:
            o['sub'] = n['sub']
        if n['group'] is not None and n['group'] in groups_by_key:
            o['group'] = map_group(n['group'])
        o['line'] = n['line']
        n_out.append(o)

    def lookup(k):
        if k in nodes:
            return k
        kl = k.lower()
        return next((x for x in nodes if x.lower() == kl), None)

    e_out = []
    for e in edges:
        o = {'from': map_node(e['from']), 'to': map_node(e['to']), 'style': e['style']}
        if e['label']:
            o['label'] = e['label']
        if e['both']:
            o['both'] = True
        o['line'] = e['line']
        e_out.append(o)
    for e in edges:
        if e['from'] in groups_by_key or e['to'] in groups_by_key:
            which = e['from'] if e['from'] in groups_by_key else e['to']
            n = nodes.get(which)
            if n and n['group'] is None and n['label'] is None:
                errors.append('line %d: "%s" is a subgraph, not a node. Edges to a whole subgraph are not supported; connect to a node inside it.' % (e['line'], which))
    m_out = []
    names = list(nodes.keys())

    def _dym(w):
        s = did_you_mean(w, names)
        return ' (did you mean "%s"?)' % s if s else ''
    for d in msg_directives:
        f, t = lookup(d['from']), lookup(d['to'])
        if not f:
            errors.append('line %d: message endpoint "%s" is not a node' % (d['line'], d['from']) + _dym(d['from']))
            continue
        if not t:
            errors.append('line %d: message endpoint "%s" is not a node' % (d['line'], d['to']) + _dym(d['to']))
            continue
        m = {'from': map_node(f), 'to': map_node(t), 'text': d['text']}
        if d['back']:
            m['back'] = True
        m_out.append(m)
    if errors:
        raise ArchError(errors[:20], warnings)

    taken = set()
    for d in step_directives:
        f, t = lookup(d['from']), lookup(d['to'])
        if not f or not t:
            w = d['from'] if not f else d['to']
            errors.append('line %d: step directive names "%s", which is not a node' % (d['line'], w) + _dym(w))
            continue
        idx = next((i for i, e in enumerate(e_out) if e['from'] == map_node(f) and e['to'] == map_node(t) and i not in taken), -1)
        if idx < 0:
            errors.append('line %d: step directive: there is no (further) edge from "%s" to "%s"' % (d['line'], d['from'], d['to']))
            continue
        taken.add(idx)
        e_out[idx]['step'] = d['step']
    rel_taken = set()
    for d in rel_directives:
        f, t = lookup(d['from']), lookup(d['to'])
        if not f or not t:
            w = d['from'] if not f else d['to']
            errors.append('line %d: rel directive names "%s", which is not a node' % (d['line'], w) + _dym(w))
            continue
        idx = next((i for i, e in enumerate(e_out) if e['from'] == map_node(f) and e['to'] == map_node(t) and i not in rel_taken), -1)
        if idx < 0:
            errors.append('line %d: rel directive: there is no (further) edge from "%s" to "%s"' % (d['line'], d['from'], d['to']))
            continue
        rel_taken.add(idx)
        e_out[idx]['relation'] = d['text']
    if errors:
        raise ArchError(errors[:20], warnings)
    graph = {'direction': opts.get('direction') or direction, 'groups': g_out, 'nodes': n_out, 'edges': e_out, 'messages': m_out}
    if relation_column is not None:
        graph['relationColumn'] = relation_column
    if relation_name:
        graph['relationName'] = relation_name
    if numbered is not None:
        graph['numbered'] = numbered
    if pace:
        graph['pace'] = pace
    if duration is not None:
        graph['duration'] = duration
    ttl = opts.get('title') or title
    if ttl:
        graph['title'] = ttl
    return {'graph': graph, 'warnings': warnings}


def _js_number(s):
    """Number(s) for the shapes that matter here; None for NaN/Infinity."""
    s = trim(s)
    if s == '':
        return 0
    try:
        if re.fullmatch(r'[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?', s):
            v = float(s)
            return int(v) if v == int(v) else v
        if re.fullmatch(r'0[xX][0-9a-fA-F]+', s):
            return int(s, 16)
        if re.fullmatch(r'0[bB][01]+', s):
            return int(s, 2)
        if re.fullmatch(r'0[oO][0-7]+', s):
            return int(s, 8)
    except (ValueError, OverflowError):
        return None
    return None
