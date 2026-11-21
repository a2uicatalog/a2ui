"""Opt-in 'rich' output policy: the smallest extension of verify_svg that the Opus SVG review (6 Nov 2026) judged safe for an SVG SHOWN AS AN <img> and still inert if a host inlines it.
Admitted, with limits: linear gradients (at most 8 stops, ids prefixed by nothing but [A-Za-z0-9_-]), SMIL animate (opacity) and animateTransform (translate, rotate) that END within 5 s
(begin + dur x repeatCount <= 5, finite, fill=freeze), at most 20 animated elements, never inside or around a filtered element, ONE filter primitive per filter (feDropShadow or feGaussianBlur,
stdDeviation <= 8, at most 2 filters, at most 50 filtered elements), and one <style> that must match a fixed dark-mode template (classes d3-xxxx, hex values only).
Not admitted, because nothing here lists them: @keyframes, @import, @font-face, url() other than a same-file gradient or filter id, animateMotion, set, feImage, feTurbulence, filter chains,
href, script, foreignObject, event handlers. Everything else is the base policy's rule: fail closed, nothing is sanitised. The base verify_svg is unchanged and stays the default.
Rich admits every drawing the base policy admits (within the tighter rich budgets: 60 KB and 400 elements), with one known exception: two clipPath elements sharing an id pass base and are refused here. The one <style> may have no child element: a browser builds the stylesheet from all its text, including text after a child, which the first version of this check never read (found by the 18 Nov 2026 security review). Until 18 Nov 2026 the rich attribute table was narrower than the
base one (no polygon, clipPath, stroke-linejoin, fill-rule, paint-order, text transform or data-*): 29 of the 51 drawings the pack makes, all passing the base policy, were rejected by rich. Now the table is the
base table plus the extras and the base checker decides the value of any base attribute rich does not treat specially."""
import re
import xml.etree.ElementTree as ET
from . import common as C
MAX_RICH_BYTES, MAX_RICH_ELEMENTS, MAX_STOPS, MAX_ANIMATED, MAX_FILTERS, MAX_FILTERED, MAX_BLUR, MAX_SECONDS = 60_000, 400, 8, 20, 2, 50, 8, 5.0
_HEX6 = re.compile(r'#[0-9a-fA-F]{6}')
_ID = re.compile(r'[A-Za-z0-9_-]{1,16}'); _CLASS = re.compile(r'd3-[a-z]{1,8}'); _URL = re.compile(r'url\(#([A-Za-z0-9_-]{1,16})\)'); _SEC = re.compile(r'(\d{1,2}(?:\.\d{1,3})?)s')
_STYLE = re.compile(r'@media \(prefers-color-scheme: dark\)\{(?:\.d3-[a-z]{1,8}\{(?:(?:fill|stroke|stop-color):#[0-9a-fA-F]{6};?){1,4}\}){1,12}\}')
_SHAPE = {'x', 'y', 'width', 'height', 'rx', 'cx', 'cy', 'r', 'x1', 'y1', 'x2', 'y2', 'font-size', 'font-weight', 'fill-opacity', 'stroke-opacity', 'stroke-width'}
_ATTRS = {'svg': {'width', 'height', 'viewBox', 'role', 'aria-label'}, 'g': {'fill', 'fill-opacity', 'stroke', 'stroke-width', 'class', 'filter'}, 'title': set(), 'defs': set(), 'style': set(),
    'rect': {'x', 'y', 'width', 'height', 'rx', 'fill', 'fill-opacity', 'stroke', 'stroke-width', 'class', 'filter'}, 'circle': {'cx', 'cy', 'r', 'fill', 'fill-opacity', 'stroke', 'stroke-width', 'class', 'filter'},
    'line': {'x1', 'y1', 'x2', 'y2', 'stroke', 'stroke-opacity', 'stroke-width', 'class'}, 'path': {'d', 'fill', 'fill-opacity', 'stroke', 'stroke-width', 'class'},
    'text': {'x', 'y', 'font-size', 'font-weight', 'font-family', 'text-anchor', 'fill', 'class'},
    'linearGradient': {'id', 'x1', 'y1', 'x2', 'y2'}, 'stop': {'offset', 'stop-color', 'stop-opacity'},
    'animate': {'attributeName', 'from', 'to', 'dur', 'begin', 'repeatCount', 'fill'}, 'animateTransform': {'attributeName', 'type', 'from', 'to', 'dur', 'begin', 'repeatCount', 'fill'},
    'filter': {'id'}, 'feDropShadow': {'dx', 'dy', 'stdDeviation', 'flood-color', 'flood-opacity'}, 'feGaussianBlur': {'stdDeviation'}}
_ATTRS['filter'].add('id')
for _t in ('rect', 'circle', 'g', 'text', 'path', 'line'): _ATTRS[_t].add('id')
for _t, _a in C._ELEMENT_ATTRS.items(): _ATTRS.setdefault(_t, set()).update(_a)   # rich = base + the extras: every element and attribute the base admits is admitted here too (18 Nov 2026; before, this table was narrower than the base)
def _seconds(v, what):
    m = _SEC.fullmatch(v)
    if not m: raise C.SvgPolicyError(f'{what} must be a number of seconds like 2s')
    return float(m.group(1))
def _begins(v, dur, max_seconds):
    """begin is one time, or (only with the explicit long opt-in max_seconds) a list of restart times 'b1;b2;...': the picture LOOPS at normal speed, and each restart must come after the previous run has finished. Returns the last begin."""
    parts = [x.strip() for x in v.split(';')]
    if len(parts) == 1: return _seconds(parts[0], 'begin')
    if max_seconds is None: raise C.SvgPolicyError('a list of begin times is the explicit long-loop opt-in (max_seconds); without it begin is one time')
    if len(parts) > 40: raise C.SvgPolicyError('at most 40 restart times')
    vals = [_seconds(p, 'begin') for p in parts]
    if any(y < x + dur - 1e-9 for x, y in zip(vals, vals[1:])): raise C.SvgPolicyError('each restart must begin after the previous run has finished')
    return vals[-1]
def _nums(v, count, what):
    parts = v.split()
    if len(parts) not in count or any(not C._NUMRE.match(p) or not abs(float(p)) <= C.MAX_COORD for p in parts): raise C.SvgPolicyError(f'{what} is not {"/".join(map(str, count))} finite numbers')
def verify_rich(svg, allow_fill_animation=False, max_seconds=None):   # max_seconds: an explicit opt-in for LONG motion (verify_motion passes it); None keeps the 5 s limit
    """Returns the svg unchanged or raises SvgPolicyError. See the module docstring for what is admitted."""
    if not isinstance(svg, str): raise C.SvgPolicyError('svg is not text')
    try: size = len(svg.encode())
    except UnicodeEncodeError: raise C.SvgPolicyError('svg contains a character that cannot be encoded (a lone surrogate)')   # review finding: this raised UnicodeEncodeError, not SvgPolicyError
    if size > MAX_RICH_BYTES: raise C.SvgPolicyError(f'svg over {MAX_RICH_BYTES} bytes')
    if '<!' in svg or '<?' in svg or C._XML_BAD.search(svg): raise C.SvgPolicyError('svg contains a DOCTYPE, comment, CDATA, processing instruction or an illegal character')
    try: root = ET.fromstring(svg)
    except ET.ParseError as e: raise C.SvgPolicyError(f'svg is not well-formed XML: {e}')
    if root.tag != '{%s}svg' % C.SVG_NS: raise C.SvgPolicyError('root is not an svg element in the SVG namespace')
    parent = {c: p for p in root.iter() for c in p}; tag = lambda e: e.tag.rpartition('}')[2]
    ids = {}; fill_refs = []; filter_refs = []; clip_refs = []; n = 0; styles = animated = filters = filtered = 0
    for e in root.iter():
        n += 1
        if n > MAX_RICH_ELEMENTS: raise C.SvgPolicyError(f'more than {MAX_RICH_ELEMENTS} elements')
        ns, _, t = e.tag.rpartition('}')
        if ns != '{' + C.SVG_NS or t not in _ATTRS: raise C.SvgPolicyError(f'element not allowed: {t or e.tag}')
        if (e.text or '').strip() and t not in ('text', 'title', 'style'): raise C.SvgPolicyError(f'text inside <{t}>')
        if len(e.text or '') > C.MAX_TEXT_CHARS and t != 'style': raise C.SvgPolicyError('text node over the character budget')
        for a, v in e.attrib.items():
            if a not in _ATTRS[t]: raise C.SvgPolicyError(f'attribute not allowed on <{t}>: {a}')
            if a == 'fill' and t in ('rect', 'circle', 'g', 'path', 'text', 'polygon'):
                m = _URL.fullmatch(v)
                if m: fill_refs.append(m.group(1))
                elif not C._COLOUR.fullmatch(v): raise C.SvgPolicyError(f'fill value not allowed: {v[:30]}')
            elif a == 'stroke':
                if not C._COLOUR.fullmatch(v): raise C.SvgPolicyError(f'stroke value not allowed: {v[:30]}')
            elif a == 'filter':
                m = _URL.fullmatch(v)
                if not m: raise C.SvgPolicyError('filter must be url(#id)')
                filter_refs.append(m.group(1)); filtered += 1
            elif a == 'id':
                if not _ID.fullmatch(v) or v in ids: raise C.SvgPolicyError('bad or repeated id')
                ids[v] = t
            elif a == 'class':
                if not all(_CLASS.fullmatch(c) for c in v.split()): raise C.SvgPolicyError('class must be d3-xxxx')
            elif a in ('stop-color', 'flood-color'):
                if not re.fullmatch(r'#[0-9a-fA-F]{6}', v): raise C.SvgPolicyError(f'{a} must be a 6-digit hex colour')
            elif a in ('stop-opacity', 'flood-opacity'):
                if not C._NUMRE.match(v) or not 0 <= float(v) <= 1: raise C.SvgPolicyError(f'{a} must be 0 to 1')
            elif a == 'offset':
                if not C._NUMRE.match(v) or not 0 <= float(v) <= 1: raise C.SvgPolicyError('offset must be 0 to 1')
            elif t == 'linearGradient' and a in ('x1', 'y1', 'x2', 'y2'):
                if not C._NUMRE.match(v) or not 0 <= float(v) <= 1: raise C.SvgPolicyError(f'gradient {a} must be 0 to 1')
            elif a in ('dx', 'dy'):
                if not C._NUMRE.match(v) or not abs(float(v)) <= 20: raise C.SvgPolicyError(f'{a} must be within 20')
            elif a == 'stdDeviation':
                if not C._NUMRE.match(v) or not 0 <= float(v) <= MAX_BLUR: raise C.SvgPolicyError(f'stdDeviation must be a single number up to {MAX_BLUR}')
            elif a in _SHAPE:
                if not C._NUMRE.match(v) or not abs(float(v)) <= C.MAX_COORD: raise C.SvgPolicyError(f'{a} is not a finite number within bounds: {v[:30]}')
                if a == 'font-size' and float(v) < C.MIN_FONT: raise C.SvgPolicyError(f'font-size {v} is under {C.MIN_FONT}')
            elif a in ('d', 'viewBox'):
                ok = C._PATH.match(v) if a == 'd' else C._LIST.match(v)
                if not ok or any(not abs(float(x)) <= C.MAX_COORD for x in re.findall(C._NUM, v)): raise C.SvgPolicyError(f'{a} value not allowed')
            elif a == 'aria-label':
                if len(v) > 300: raise C.SvgPolicyError('aria-label too long')
            elif a == 'role':
                if v != 'img': raise C.SvgPolicyError('role must be img')
            elif a == 'text-anchor':
                if v not in ('start', 'middle', 'end'): raise C.SvgPolicyError('text-anchor value not allowed')
            elif a == 'font-family':
                if v != 'sans-serif': raise C.SvgPolicyError('font-family value not allowed')
            elif a == 'clip-path':
                m = _URL.fullmatch(v)
                if not m: raise C.SvgPolicyError('clip-path must be url(#id)')
                clip_refs.append(m.group(1))
            elif a in C._ELEMENT_ATTRS.get(t, ()): C._check_attr(t, a, v)   # an attribute the base policy admits and rich does not treat specially: the base checker decides its value
            elif a in ('attributeName', 'type', 'from', 'to', 'dur', 'begin', 'repeatCount', 'fill'): pass          # animation attributes: checked together below
            else: raise C.SvgPolicyError(f'attribute not handled: {a}')
        if t == 'style':
            styles += 1
            if styles > 1 or len(e) or parent.get(e) is not root or not _STYLE.fullmatch(e.text or ''): raise C.SvgPolicyError('style must be one dark-mode block from the fixed template, directly under svg, with no child element')   # len(e): text after a child element is CSS to a browser and was never checked (review 18 Nov 2026)
        if t == 'linearGradient' and not 1 <= len(e) <= MAX_STOPS or t == 'linearGradient' and any(tag(c) != 'stop' for c in e): raise C.SvgPolicyError(f'a gradient has 1 to {MAX_STOPS} stops and nothing else')
        if t == 'stop' and tag(parent[e]) != 'linearGradient': raise C.SvgPolicyError('stop outside a gradient')
        if t == 'filter':
            filters += 1
            if filters > MAX_FILTERS: raise C.SvgPolicyError(f'more than {MAX_FILTERS} filters')
            if len(e) != 1 or tag(e[0]) not in ('feDropShadow', 'feGaussianBlur'): raise C.SvgPolicyError('a filter has exactly one primitive, feDropShadow or feGaussianBlur (filter chains can hang a tab)')
        if t in ('feDropShadow', 'feGaussianBlur') and tag(parent[e]) != 'filter': raise C.SvgPolicyError('filter primitive outside a filter')
        if t in ('animate', 'animateTransform'):
            animated += 1; p = parent[e]
            if tag(p) in ('svg', 'defs', 'linearGradient', 'filter', 'text', 'title', 'style'): raise C.SvgPolicyError('an animation must sit inside a shape or group')
            a = e.attrib; need = {'attributeName', 'from', 'to', 'dur', 'repeatCount', 'fill'} | ({'type'} if t == 'animateTransform' else set())
            if not need <= set(a): raise C.SvgPolicyError(f'<{t}> needs {sorted(need)}')
            dur = _seconds(a['dur'], 'dur'); begin = _begins(a.get('begin', '0s'), dur, max_seconds); rep = a['repeatCount']
            if not re.fullmatch(r'[1-9]', rep): raise C.SvgPolicyError('repeatCount must be a whole number 1 to 9 (indefinite is not admitted)')
            _lim = MAX_SECONDS if max_seconds is None else max_seconds
            if dur <= 0 or begin + dur * int(rep) > _lim + 1e-9: raise C.SvgPolicyError(f'an animation must end within {_lim:g} s (begin + dur x repeatCount)')
            if a['fill'] != 'freeze': raise C.SvgPolicyError('fill must be freeze')
            if t == 'animate':
                if allow_fill_animation and a['attributeName'] == 'fill':   # opt-in, used only by verify_motion: a colour fade between two literal hex colours (no gradients, no url, no names)
                    if tag(p) not in ('path', 'rect', 'circle', 'polygon'): raise C.SvgPolicyError('a fill animation sits inside a path, rect, circle or polygon')
                    if any(not _HEX6.fullmatch(a[k]) for k in ('from', 'to')): raise C.SvgPolicyError('a fill animation goes between two #rrggbb colours')
                    continue
                if a['attributeName'] != 'opacity': raise C.SvgPolicyError('animate may only change opacity')
                for k in ('from', 'to'):
                    if not C._NUMRE.match(a[k]) or not 0 <= float(a[k]) <= 1: raise C.SvgPolicyError('opacity must be 0 to 1')
            else:
                if a['attributeName'] != 'transform' or a['type'] not in ('translate', 'rotate'): raise C.SvgPolicyError('animateTransform may only be translate or rotate on transform')
                cnt = (2,) if a['type'] == 'translate' else (1, 3)
                _nums(a['from'], cnt, 'from'); _nums(a['to'], cnt, 'to')
    if animated > MAX_ANIMATED: raise C.SvgPolicyError(f'more than {MAX_ANIMATED} animated elements')
    if filtered > MAX_FILTERED: raise C.SvgPolicyError(f'more than {MAX_FILTERED} filtered elements')
    if any(ids.get(r) != 'linearGradient' for r in fill_refs): raise C.SvgPolicyError('fill url() must name a gradient in this file')
    if any(ids.get(r) != 'filter' for r in filter_refs): raise C.SvgPolicyError('filter url() must name a filter in this file')
    if any(ids.get(r) != 'clipPath' for r in clip_refs): raise C.SvgPolicyError('clip-path url() must name a clipPath in this file')
    for e in root.iter():
        if e.get('filter'):                                                              # nothing animates inside a filtered element, and a filtered element is never itself animated
            if any(tag(d) in ('animate', 'animateTransform') for d in e.iter()): raise C.SvgPolicyError('a filtered element must not be animated')
        if tag(e) in ('animate', 'animateTransform'):
            p = parent[e]
            while p is not None:
                if p.get('filter'): raise C.SvgPolicyError('an animation must not sit inside a filtered element')
                p = parent.get(p)
    return svg
