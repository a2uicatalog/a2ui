"""Mermaid, D2 and JSON graph -> arch_motion arguments.

A pure Python 3.11 port of the JS mermaid_arch compiler (scripts/mermaid_arch in the a2ui release repo): the same parsers,
the same validation messages, the same layered layout, orthogonal router and timing schedule. No subprocess, no network, no model.

    from archpack.markup import mermaid_to_arch, d2_to_arch, json_to_arch, ArchError
    res = mermaid_to_arch(text, numbered=True)
    out = arch_motion(**res)            # res holds exactly arch_motion's keyword arguments
    res.warnings                        # what the converter changed or could not draw
    res.text_steps                      # one plain sentence per edge, in playing order (the text alternative)

Options (all optional, checked, never silently clamped): size (8-40), fit ('balanced'|'wide'), aspect, routing
('orthogonal'|'curve'), pace ('slow'|'normal'|'fast'), duration (2-120 s), hint ('cli'|'web'), direction (LR RL TB TD BT),
title, numbered, relationColumn, relationName. `aspect`, `duration`, `pace`, `numbered` and the relation options shape the
JS film and its tables; here they shape the timing (`at`/`dur`) and the text alternative only.
"""
from __future__ import annotations

from ._js import UNDEF, is_finite_number, is_number, js_json
from .compile import compile_graph, validate_block
from .d2 import parse_d2
from .graph import DIRECTIONS, PACES, ArchError, fold_groups, norm_direction, validate_graph
from .mermaid import parse_mermaid, strip_tags_deep

__all__ = ['ArchError', 'ArchResult', 'mermaid_to_arch', 'd2_to_arch', 'json_to_arch', 'check_options', 'sanitize_graph',
           'parse_mermaid', 'parse_d2', 'validate_graph', 'fold_groups']

_OPTION_ALIASES = {'relation_column': 'relationColumn', 'relation_name': 'relationName'}


class ArchResult(dict):
    """The keyword arguments of arch_motion (label, w, h, size, radius, nodes, edges, groups, messages), plus the extras as attributes."""
    warnings: list
    graph: dict
    block: dict
    layout: dict
    text_steps: list
    text_messages: list
    schedule: list
    duration_seconds: float
    steps: list


def check_options(opts=None):
    """Option values are checked, never silently clamped or ignored."""
    e = []
    o = opts or {}

    def given(k):
        return o.get(k) is not None
    if given('size') and not (is_finite_number(o['size']) and 8 <= o['size'] <= 40):
        e.append('size %s must be a number from 8 to 40 (label text size in px)' % js_json(o['size']))
    if given('fit') and o['fit'] not in ('balanced', 'wide'):
        e.append('fit %s must be balanced or wide' % js_json(o['fit']))
    if given('aspect') and o['aspect'] not in ('16:9', '4:3', '1:1', '9:16'):
        e.append('aspect %s must be 16:9, 4:3, 1:1 or 9:16' % js_json(o['aspect']))
    if given('routing') and o['routing'] not in ('orthogonal', 'curve'):
        e.append('routing %s must be orthogonal or curve' % js_json(o['routing']))
    if given('pace') and not (isinstance(o['pace'], str) and o['pace'] in PACES):
        e.append('pace %s must be one of %s' % (js_json(o['pace']), ', '.join(PACES)))
    if given('duration') and not (is_number(o['duration']) and 2 <= o['duration'] <= 120):
        e.append('duration %s must be a number of seconds from 2 to 120' % js_json(o['duration']))
    if given('hint') and o['hint'] not in ('cli', 'web'):
        e.append('hint %s must be cli or web' % js_json(o['hint']))
    if given('direction') and norm_direction(o['direction']) not in DIRECTIONS:
        e.append('direction %s must be LR, RL, TB (or TD) or BT' % js_json(o['direction']))
    if e:
        raise ArchError(e)


def sanitize_graph(graph):
    """One gate for every input path: strings are literal text, so only tags are removed (no entity decoding). Returns (copy, changed)."""
    changed = [False]

    def mark():
        changed[0] = True

    def clean(t):
        return strip_tags_deep(t, mark) if isinstance(t, str) else t

    def each(a, keys):
        if not isinstance(a, list):
            return a
        out = []
        for o in a:
            if not isinstance(o, dict):
                out.append(o)
                continue
            c = dict(o)
            for k in keys:
                if k in c:
                    c[k] = clean(c[k])
            out.append(c)
        return out
    if not isinstance(graph, dict):
        return graph, False
    g = dict(graph)
    if 'title' in g:
        g['title'] = clean(g['title'])
    if 'relationName' in g:
        g['relationName'] = clean(g['relationName'])
    g['nodes'] = each(g.get('nodes'), ['label', 'sub'])
    g['groups'] = each(g.get('groups'), ['label'])
    g['edges'] = each(g.get('edges'), ['label', 'relation'])
    g['messages'] = each(g.get('messages'), ['text'])
    for k in ('groups', 'messages'):
        if g.get(k) is None:   # a graph without groups or messages used to crash the layout
            g[k] = []
    return g, changed[0]


def _norm_opts(opts):
    out = {}
    for k, v in (opts or {}).items():
        out[_OPTION_ALIASES.get(k, k)] = v
    return out


def graph_to_arch(graph, **opts):
    opts = _norm_opts(opts)
    check_options(opts)
    san, changed = sanitize_graph(graph)
    folded, fold_w = fold_groups(san)
    warnings0 = list(fold_w)
    if changed:
        warnings0.insert(0, 'HTML tags were removed from a label.')
    opts = dict(opts)
    for k in ('title', 'relationName'):
        if isinstance(opts.get(k), str):
            o, ch = sanitize_graph({'title': opts[k]})
            opts[k] = o['title']
            if ch and 'HTML tags were removed from a label.' not in warnings0:
                warnings0.insert(0, 'HTML tags were removed from a label.')
    g = dict(folded)
    if opts.get('direction'):
        g['direction'] = norm_direction(opts['direction'])
    if g.get('direction'):
        g['direction'] = norm_direction(g['direction'])
    if opts.get('title'):
        g['title'] = opts['title']
    if not g.get('direction'):
        g['direction'] = 'LR'
    errors, v_warnings = validate_graph(g)
    warnings = [*warnings0, *v_warnings]
    if errors:
        raise ArchError(errors, warnings)
    lopts = {**opts, 'forceDirection': bool(opts.get('direction')), 'direction': norm_direction(opts.get('direction'))}
    c = compile_graph(g, lopts)
    block = c['block']
    bad = validate_block(block)
    if bad:
        raise ArchError(['internal: compiled block breaks the atom limits: ' + '; '.join(bad)], warnings)
    res = ArchResult({k: v for k, v in block.items() if k != 'type'})
    res.warnings = [*warnings, *c['warnings']]
    res.graph = g
    res.block = block
    res.layout = c['layout']
    res.text_steps = c['textSteps']
    res.text_messages = c['textMessages']
    res.schedule = c['schedule']
    res.duration_seconds = c['durationSeconds']
    res.steps = c['steps']
    res.pace = c['pace']
    res.numbered = c['numbered']
    return res


def _merge_warnings(parsed, res):
    seen = []
    for w in [*parsed['warnings'], *res.warnings]:
        if w not in seen:
            seen.append(w)
    res.warnings = seen
    return res


def mermaid_to_arch(text, **opts):
    opts = _norm_opts(opts)
    check_options(opts)
    parsed = parse_mermaid(text, opts)
    return _merge_warnings(parsed, graph_to_arch(parsed['graph'], **opts))


def d2_to_arch(text, **opts):
    opts = _norm_opts(opts)
    check_options(opts)
    parsed = parse_d2(text, opts)
    return _merge_warnings(parsed, graph_to_arch(parsed['graph'], **opts))


def json_to_arch(graph, **opts):
    """A canonical graph (a dict, or JSON text) -> arch_motion arguments. Fold warnings come first, like the corpus runner."""
    import json as _json
    if isinstance(graph, (str, bytes)):
        graph = _json.loads(graph)
    res = graph_to_arch(graph, **opts)
    _f, fw = fold_groups(graph)
    res.warnings = [*[w for w in fw if w not in res.warnings], *res.warnings]
    return res
