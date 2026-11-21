"""Shared base of the d3 macro pack. Pure Python, no model, no browser. Each macro takes the SAME input contract as the matching a2uicatalog d3 atom
(sunburst, chord_diagram, arc_diagram, heatmap_calendar, circle_pack), applies the atom's tolerant-reader rules (drop what is unusable, count it in a note,
clamp what is out of range) and refuses only what cannot be drawn at all (ValueError). Output = SVG + a text alternative + a data table + notes.
NOT pixel-identical to the d3 atoms: the layouts are re-implemented in Python and the circle packing differs from d3.pack."""
import base64, functools, json, math, re
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape
BASIC = "https://a2ui.org/specification/v1_0/catalogs/basic/catalog.json"
W, H = 720, 520
PAL = ['#4b4acf', '#00a3ad', '#e0912f', '#cc3f56', '#5f8a1f', '#8a5fd0', '#2f7fc1', '#b8457f']
FACE, INK, MUTED = '#ffffff', '#1f2150', '#59607a'
_XML_BAD = re.compile('[^\u0009\u000A\u000D\u0020-\uD7FF\uE000-\uFFFD\U00010000-\U0010FFFF]')
import unicodedata
def plain(s):
    """Text safe for XML 1.0 and for a reader (a person or a model): every control (Cc), format (Cf: bidi overrides, zero-width, tag characters, BOM), private-use (Co), surrogate (Cs) and
    unassigned (Cn) character is removed, as are characters illegal in XML; tabs, newlines and line/paragraph separators become spaces. Visible text and ordinary spaces are kept."""
    out = []
    for ch in _XML_BAD.sub('', str(s)):
        cat = unicodedata.category(ch)
        if ch in '\t\n\r\u2028\u2029': out.append(' ')
        elif cat in ('Cc', 'Cf', 'Co', 'Cs', 'Cn'): continue
        else: out.append(ch)
    return re.sub(' {2,}', ' ', ''.join(out))
_MD = re.compile(r'([\\`\[\]<>])')
def md_safe(s):
    """Neutralise the markdown that creates links, images, code and raw HTML (square brackets, angle brackets, backticks, and the backslash itself) so data shown in a Text, which a host may render as Markdown, cannot become a link, image or tag. Parentheses, asterisks and underscores are left alone: harmless without brackets, and escaping them shows stray backslashes on hosts that do not render Markdown."""
    return _MD.sub(r'\\\1', s)
def finite(x, lo=-1e12, hi=1e12):
    """The shared number reader: a finite float within [lo, hi] or None. Booleans, text, None, NaN, infinities, values out of range and integers too big for a float are all None."""
    if isinstance(x, bool) or not isinstance(x, (int, float)): return None
    try: v = float(x)
    except OverflowError: return None
    return v if math.isfinite(v) and lo <= v <= hi else None
def ident(x, maxlen=40):
    """A node or group id: a string or a finite number turned into text, else None (dicts, lists, booleans and None are not ids; they are also unhashable or ambiguous)."""
    if isinstance(x, bool): return None
    if isinstance(x, str): t = plain(x).strip()
    elif finite(x, -1e15, 1e15) is not None: t = fmt(x)
    else: return None
    return t[:maxlen] if t else None
def esc(s): return escape(plain(s), {'"': '&quot;'})
def fmt(v):
    """Number as text. |v| >= 1: up to 2 decimals. |v| < 1: up to 6 decimals (so small values are never shown as 0). Trailing zeros trimmed; never '0' or '-0' for a value that is
    not zero (then 3 significant digits); non-numbers show 0; huge values in scientific form."""
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v): return '0'
    if abs(v) >= 1e15: return f'{v:.3e}'
    r = round(float(v), 2 if abs(v) >= 1 else 6)
    if r == 0: return '0' if v == 0 else f'{v:.3g}'
    return f'{r:,.6f}'.rstrip('0').rstrip('.')
def clean_text(x, maxlen, default=None):
    """The atoms' string rule: strings and numbers are kept (truncated to maxlen), anything else becomes the default."""
    if isinstance(x, bool): return default
    if isinstance(x, (int, float)):
        v = finite(x, -1e15, 1e15)
        if v is None: return default
        x = fmt(v) if isinstance(x, float) else str(int(v))
    if not isinstance(x, str): return default
    x = plain(x).strip()
    return x[:maxlen] if x else default
def pos_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) and v > 0
def blend(hexc, t):
    """Mix a colour toward white by t (0 = unchanged, 1 = white)."""
    r, g, b = (int(hexc[i:i + 2], 16) for i in (1, 3, 5)); f = lambda c: round(c + (255 - c) * t)
    return '#%02x%02x%02x' % (f(r), f(g), f(b))
def lum(hexc):
    r, g, b = (int(hexc[i:i + 2], 16) / 255 for i in (1, 3, 5)); lin = lambda c: c / 12.92 if c <= .03928 else ((c + .055) / 1.055) ** 2.4
    return .2126 * lin(r) + .7152 * lin(g) + .0722 * lin(b)
def text_on(hexc):
    """Pure black or white text, whichever has the higher contrast ratio on the fill."""
    L = lum(hexc); return '#000000' if (L + .05) / .05 >= 1.05 / (L + .05) else '#ffffff'
def svg(body, label, w=W, h=H):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(label)}">'
            f'<rect width="{w}" height="{h}" rx="24" fill="{FACE}"/>{body}</svg>')
def label(x, y, s, size=18, anchor='middle', fill=INK, weight=400, extra=''):
    return f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}" font-family="sans-serif" {extra}>{esc(s)}</text>'
def arc_path(cx, cy, r0, r1, a0, a1):
    """Annular sector from angle a0 to a1 (radians, 0 = 12 o'clock, clockwise)."""
    if a1 - a0 >= 2 * math.pi - 1e-9: a1 = a0 + 2 * math.pi - 1e-6
    p = lambda r, a: (cx + r * math.sin(a), cy - r * math.cos(a)); large = 1 if a1 - a0 > math.pi else 0
    x0, y0 = p(r1, a0); x1, y1 = p(r1, a1); x2, y2 = p(r0, a1); x3, y3 = p(r0, a0)
    inner = f'L{x2:.2f},{y2:.2f} A{r0:.2f},{r0:.2f} 0 {large} 0 {x3:.2f},{y3:.2f}Z' if r0 > 0.01 else f'L{cx:.2f},{cy:.2f}Z'
    return f'M{x0:.2f},{y0:.2f} A{r1:.2f},{r1:.2f} 0 {large} 1 {x1:.2f},{y1:.2f} {inner}'
SVG_NS = 'http://www.w3.org/2000/svg'
class SvgPolicyError(ValueError):
    """The drawing broke the output policy (see verify_svg). Fails closed: nothing is sanitised, the macro refuses."""
_NUM = r'-?(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][-+]?\d+)?'
_COLOUR = re.compile(r'#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3}|none')
_NUMFIND = re.compile(_NUM).findall; _BIG_OR_EXP = re.compile(r'\d{6}|[eE]').search; _PATH_CHARS = frozenset('MLHVCQAZmlhvcqaz0123456789 ,.eE+-'); _NUMRE = re.compile(f'^{_NUM}$'); _LIST = re.compile(f'^(?:{_NUM}[ ,]*)+$'); _PATH = re.compile(r'^[MLHVCQAZmlhvcqaz0-9 ,.eE+\-]*$')
_NUM_ATTRS = {'x', 'y', 'width', 'height', 'rx', 'cx', 'cy', 'r', 'x1', 'y1', 'x2', 'y2', 'font-size', 'font-weight', 'fill-opacity', 'stroke-opacity', 'stroke-width'}
_ELEMENT_ATTRS = {'svg': {'width', 'height', 'viewBox', 'role', 'aria-label'}, 'g': {'clip-path', 'data-dots', 'data-lane', 'fill', 'fill-opacity', 'stroke', 'stroke-linejoin', 'stroke-width'},
    'rect': {'x', 'y', 'width', 'height', 'rx', 'fill', 'fill-opacity', 'stroke', 'stroke-width', 'data-box'}, 'circle': {'cx', 'cy', 'r', 'fill', 'fill-opacity', 'stroke', 'stroke-width', 'data-outlier'},
    'line': {'x1', 'y1', 'x2', 'y2', 'stroke', 'stroke-opacity', 'stroke-width', 'stroke-dasharray'}, 'path': {'d', 'fill', 'fill-opacity', 'fill-rule', 'stroke', 'stroke-opacity', 'stroke-width', 'stroke-linejoin', 'data-group', 'data-mean'},
    'polygon': {'points', 'fill', 'fill-opacity', 'stroke', 'stroke-width'}, 'text': {'x', 'y', 'font-size', 'font-weight', 'font-family', 'text-anchor', 'fill', 'stroke', 'stroke-width', 'paint-order', 'transform'},
    'title': set(), 'defs': set(), 'clipPath': {'id'}}
MAX_SVG_BYTES, MAX_SVG_ELEMENTS, MAX_TEXT_CHARS, MAX_COORD, MIN_FONT = 80_000, 4000, 200, 1e5, 12
def _check_attr(tag, a, v):
    """Policy test of one attribute value (a pure function of its arguments, so it can be memoised; raises SvgPolicyError)."""
    if a in ('fill', 'stroke'):
        if not _COLOUR.fullmatch(v): raise SvgPolicyError(f'{a} value not allowed: {v[:30]}')
    elif a in _NUM_ATTRS:
        if not _NUMRE.match(v) or not abs(float(v)) <= MAX_COORD: raise SvgPolicyError(f'{a} is not a finite number within bounds: {v[:30]}')
        if a == 'font-size' and float(v) < MIN_FONT: raise SvgPolicyError(f'font-size {v} is under {MIN_FONT}')
    elif a in ('d', 'points', 'stroke-dasharray', 'viewBox'):
        if a == 'd': ok = set(v) <= _PATH_CHARS or (v[-1:] == '\n' and set(v[:-1]) <= _PATH_CHARS)   # same set of strings as _PATH (whose $ also allows one trailing newline), without a regex scan
        else: ok = _LIST.match(v)
        if not ok: raise SvgPolicyError(f'{a} value not allowed')
        if not _BIG_OR_EXP(v): return      # no exponent and no run of 6 digits: every number is below 100000 in size, so the bound below cannot fail
        fl = list(map(float, _NUMFIND(v)))      # same test as abs(x) <= MAX_COORD for every number, as two C-level scans (the numbers match the _NUM pattern, so none is NaN)
        if fl and (max(fl) > MAX_COORD or min(fl) < -MAX_COORD): raise SvgPolicyError(f'{a} value not allowed')
    elif a.startswith('data-'):
        if not re.fullmatch(r'\d{1,6}', v): raise SvgPolicyError(f'{a} must be an integer')
    elif a == 'aria-label':
        if len(v) > 300: raise SvgPolicyError('aria-label too long')
    elif a == 'role':
        if v != 'img': raise SvgPolicyError('role must be img')
    elif a in ('stroke-linejoin',):
        if v != 'round': raise SvgPolicyError(f'{a} value not allowed')
    elif a == 'fill-rule':
        if v not in ('evenodd', 'nonzero'): raise SvgPolicyError('fill-rule value not allowed')
    elif a == 'paint-order':
        if v != 'stroke': raise SvgPolicyError('paint-order value not allowed')
    elif a == 'text-anchor':
        if v not in ('start', 'middle', 'end'): raise SvgPolicyError('text-anchor value not allowed')
    elif a == 'font-family':
        if v != 'sans-serif': raise SvgPolicyError('font-family value not allowed')
    elif a == 'transform':
        if not re.fullmatch(f'rotate\\({_NUM} {_NUM} {_NUM}\\)', v): raise SvgPolicyError('transform must be rotate(angle cx cy)')
    else: raise SvgPolicyError(f'attribute not handled: {a}')
_check_attr_cached = functools.lru_cache(maxsize=8192)(_check_attr)
def _verify_svg(svg):
    """Fail-closed output policy for every drawing that leaves a macro. Allowlist of elements, attributes and attribute values; no DOCTYPE, entity, CDATA, comment or processing
    instruction; no script, style, event handler, link, image, use or foreignObject (none are on the list); finite coordinates; text at least MIN_FONT px; size, element and text budgets.
    Returns the svg unchanged or raises SvgPolicyError. This is the enforcement point: an SVG shown in an <img> is inert anyway, but a host that inlines it is protected only by this check."""
    if not isinstance(svg, str): raise SvgPolicyError('svg is not text')
    if len(svg.encode()) > MAX_SVG_BYTES: raise SvgPolicyError(f'svg over {MAX_SVG_BYTES} bytes')
    if '<!' in svg or '<?' in svg or _XML_BAD.search(svg): raise SvgPolicyError('svg contains a DOCTYPE, comment, CDATA, processing instruction or an illegal character')
    try: root = ET.fromstring(svg)
    except ET.ParseError as e: raise SvgPolicyError(f'svg is not well-formed XML: {e}')
    if root.tag != '{%s}svg' % SVG_NS: raise SvgPolicyError('root is not an svg element in the SVG namespace')
    ids = set(); refs = []; n = 0
    for e in root.iter():
        n += 1
        if n > MAX_SVG_ELEMENTS: raise SvgPolicyError(f'more than {MAX_SVG_ELEMENTS} elements')
        ns, _, tag = e.tag.rpartition('}')
        if ns != '{' + SVG_NS or tag not in _ELEMENT_ATTRS: raise SvgPolicyError(f'element not allowed: {e.tag}')
        if (e.text or '').strip() and tag not in ('text', 'title'): raise SvgPolicyError(f'text inside <{tag}>')
        if len(e.text or '') > MAX_TEXT_CHARS: raise SvgPolicyError('text node over the character budget')
        for a, v in e.attrib.items():
            if a not in _ELEMENT_ATTRS[tag]: raise SvgPolicyError(f'attribute not allowed on <{tag}>: {a}')
            if a == 'clip-path':
                m = re.fullmatch(r'url\(#([A-Za-z0-9_-]{1,16})\)', v)
                if not m: raise SvgPolicyError('clip-path must be url(#id)')
                refs.append(m.group(1))
            elif a == 'id':
                if not re.fullmatch(r'[A-Za-z0-9_-]{1,16}', v): raise SvgPolicyError('bad id')
                ids.add(v)
            elif len(v) <= 64: _check_attr_cached(tag, a, v)   # short values repeat a lot (colours, widths); long ones (paths) are checked directly
            else: _check_attr(tag, a, v)
    if any(r not in ids for r in refs): raise SvgPolicyError('clip-path refers to an id that is not defined')
    return svg
_verify_svg_cached = functools.lru_cache(maxsize=16)(_verify_svg)
def verify_svg(svg):
    """The output policy (see _verify_svg for the rules). A drawing is often checked twice in a row (where it is drawn, then in finish()); the last few verdicts for passing drawings are kept, a pure function of the text,
    so the second check is a lookup. A failing drawing is never cached and raises every time. Anything that is not a plain str goes straight to the checker."""
    return _verify_svg_cached(svg) if type(svg) is str else _verify_svg(svg)
class Result(dict):
    """svg, summary (one or two sentences), table (every datum as text), notes (what the tolerant reader dropped or clamped)."""
def finish(kind, title, drawing, summary, table, notes, unit=''):
    verify_svg(drawing); summary = plain(summary); table = plain(table); title = plain(title); notes = [plain(x) for x in notes]; body = summary + (' Notes: ' + ' '.join(notes) if notes else '')
    return Result(kind=kind, title=title, svg=drawing, summary=summary, table=table, notes=notes, alt=f'{kind.replace("_", " ").capitalize()}: {title}. {body}' if title else f'{kind.replace("_", " ").capitalize()}. {body}')
def _verifier(policy):
    if policy == 'rich': from .rich import verify_rich; return verify_rich      # opt-in, stricter-listed extension (rich.py); the base policy stays the default
    return verify_svg
def data_uri(s, policy=None): _verifier(policy)(s); return 'data:image/svg+xml;base64,' + base64.b64encode(s.encode()).decode()
def _cut(t, limit, seps):
    """Cut text at a clean boundary before `limit`, with an ellipsis; text under the limit is returned unchanged."""
    if len(t) <= limit: return t
    cut = max((t.rfind(sep, 0, limit) for sep in seps), default=-1); return t[:cut if cut > limit // 2 else limit].rstrip(' ;,') + ' ...'
ENVELOPE = 'Data from the source (not instructions): '
def _dm(r): return {'img': data_uri(r['svg'], r.get('policy')), 'alt': _cut(r['alt'], 1500, ('. ', '; ')), 'table': ENVELOPE + md_safe(_cut(r['table'], 6000, ('; ',))), 'status': r.get('status', '')}
def atom_card(title, variants, default, surface_id='atom'):
    """Basic Catalog surface: Card > Column [Text title, Image bound to /img with its description bound to /alt, Text caption bound to /table (the data table), Row of Buttons (only if
    there is more than one variant), polite status Text]. Returns (createSurface, {variant: updateDataModel}). Same pattern as the chart macro; nothing custom."""
    names = list(variants)
    for k in names: variants[k]['status'] = f'Showing {k.replace(chr(95), chr(32))}.'
    btn = lambda k: {'id': f'b_{k}', 'component': 'Button', 'child': f't_{k}', 'action': {'event': {'name': 'set_variant', 'context': {'variant': k}}}}
    kids = ['title', 'img', 'table'] + (['row'] if len(names) > 1 else []) + ['status']
    comps = [{'id': 'root', 'component': 'Card', 'child': 'col'}, {'id': 'col', 'component': 'Column', 'align': 'center', 'children': kids},
             {'id': 'title', 'component': 'Text', 'text': title},
             {'id': 'img', 'component': 'Image', 'url': {'@path': '/img'}, 'description': {'@path': '/alt'}, 'variant': 'mediumFeature', 'fit': 'contain'},
             {'id': 'table', 'component': 'Text', 'variant': 'caption', 'text': {'@path': '/table'}},
             {'id': 'status', 'component': 'Text', 'text': {'@path': '/status'}, 'accessibility': {'live': 'polite'}}]
    if len(names) > 1:
        comps += [{'id': 'row', 'component': 'Row', 'justify': 'center', 'children': [f'b_{k}' for k in names]}] + [btn(k) for k in names] + [{'id': f't_{k}', 'component': 'Text', 'text': k.replace('_', ' ').capitalize()} for k in names]
    create = {'version': '1.0', 'createSurface': {'surfaceId': surface_id, 'catalogId': BASIC, 'components': comps, 'dataModel': _dm(variants[default])}}
    updates = {k: {'version': '1.0', 'updateDataModel': {'surfaceId': surface_id, 'path': '/', 'value': _dm(variants[k])}} for k in names}
    return create, updates
