"""svg_repair: a small, honest normaliser for SVG that a MODEL wrote, placed in front of the fail-closed checker (common.verify_svg or rich.verify_rich).

Why: a first test (18 Nov 2026, one model, eight drawings) failed all eight under the checker, but only because of a handful of habits, not because anything was unsafe:
font-weight="bold" instead of a number, the smooth curve command T, stroke-opacity put on a group, text styling put on a group. Four mechanical repairs took 7 of 8 to a pass.

Rules this module keeps:
 - A repair is EXACT: the repaired drawing looks the same. Nothing is dropped to make it pass, nothing is sanitised, no unsafe construct is ever removed or rewritten.
 - Every repair is REPORTED in the notes, so a caller can show what was changed. Nothing is changed silently.
 - It never widens the policy and never replaces the checker: repair_and_verify() runs the real checker on the result. A script, an event handler, a link, an image, a foreignObject or
   a style element is not touched here; the checker still rejects it.
 - Anything it cannot repair exactly it leaves alone (and says so), so the checker rejects it with its own reason.
Repairs: font-weight keywords to numbers; the smooth curve commands S and T rewritten as C and Q (path made absolute); text styling on a group moved onto its text elements;
stroke-opacity on a group moved onto the lines and paths under it; ellipse and polyline rewritten as paths.
Hardened after the 18 Nov 2026 security review (an independent fuzz of 8 fixtures and 320 mutants): only elements in the SVG namespace are touched; an ellipse or polyline with a child element, a non-number
among its points or an out-of-bound number is left alone; a path is only rewritten if every number in it is within the checker's bound; a group value is only moved or dropped if the checker itself would
accept that value on a text element; repair never raises and skips a drawing that is too large or too deeply nested. Coordinates in rewritten paths are rounded to 0.001.
Pure Python, stdlib only, no model, no network."""
import math
import re
import xml.etree.ElementTree as ET
from . import common as C

NS = C.SVG_NS
_FONT_WEIGHTS = {'bold': '700', 'bolder': '700', 'normal': '400', 'lighter': '300'}
_TEXT_ATTRS = ('font-family', 'font-size', 'font-weight', 'text-anchor', 'paint-order')
_NUM = re.compile(r'[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?')
_SEP = re.compile(r'[\s,]*')
_ARGC = {'M': 2, 'L': 2, 'H': 1, 'V': 1, 'C': 6, 'S': 4, 'Q': 4, 'T': 2, 'A': 7, 'Z': 0}


def _f(x):
    s = ('%.3f' % x).rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


def _parse_path(d):
    """Path data to a list of (command, [numbers]) with the command letter kept as written (relative or absolute), or None if it cannot be read safely."""
    pos, n, out, cmd = 0, len(d), [], None
    while True:
        pos = _SEP.match(d, pos).end()
        if pos >= n: break
        ch = d[pos]
        if ch.isalpha():
            if ch.upper() not in _ARGC: return None
            cmd = ch; pos += 1
            if cmd in 'Zz': out.append((cmd, [])); continue
        elif cmd is None or cmd in 'Zz': return None
        want = _ARGC[cmd.upper()]; args = []
        for k in range(want):
            pos = _SEP.match(d, pos).end()
            if cmd.upper() == 'A' and k in (3, 4):   # arc flags are single characters and may touch the next number
                if pos >= n or d[pos] not in '01': return None
                args.append(float(d[pos])); pos += 1; continue
            m = _NUM.match(d, pos)
            if not m: return None
            args.append(float(m.group(0))); pos = m.end()
        out.append((cmd, args))
        if cmd == 'M': cmd = 'L'
        elif cmd == 'm': cmd = 'l'
    return out


def _absolute(segs):
    """The same path with every command absolute and only M, L, C, Q, A and Z used: S becomes C and T becomes Q with the reflected control point (the same curve)."""
    cx = cy = sx = sy = 0.0; lastc = lastq = None; out = []
    for cmd, a in segs:
        rel = cmd.islower(); c = cmd.upper(); ox, oy = (cx, cy) if rel else (0.0, 0.0)
        if c == 'M': cx, cy = ox + a[0], oy + a[1]; sx, sy = cx, cy; out.append('M %s %s' % (_f(cx), _f(cy))); lastc = lastq = None
        elif c == 'L': cx, cy = ox + a[0], oy + a[1]; out.append('L %s %s' % (_f(cx), _f(cy))); lastc = lastq = None
        elif c == 'H': cx = (cx if rel else 0.0) + a[0]; out.append('L %s %s' % (_f(cx), _f(cy))); lastc = lastq = None
        elif c == 'V': cy = (cy if rel else 0.0) + a[0]; out.append('L %s %s' % (_f(cx), _f(cy))); lastc = lastq = None
        elif c == 'C':
            x1, y1, x2, y2, x, y = ox + a[0], oy + a[1], ox + a[2], oy + a[3], ox + a[4], oy + a[5]
            out.append('C %s %s %s %s %s %s' % tuple(map(_f, (x1, y1, x2, y2, x, y)))); lastc = (x2, y2); lastq = None; cx, cy = x, y
        elif c == 'S':
            x1, y1 = (2 * cx - lastc[0], 2 * cy - lastc[1]) if lastc else (cx, cy); x2, y2, x, y = ox + a[0], oy + a[1], ox + a[2], oy + a[3]
            out.append('C %s %s %s %s %s %s' % tuple(map(_f, (x1, y1, x2, y2, x, y)))); lastc = (x2, y2); lastq = None; cx, cy = x, y
        elif c == 'Q':
            x1, y1, x, y = ox + a[0], oy + a[1], ox + a[2], oy + a[3]
            out.append('Q %s %s %s %s' % tuple(map(_f, (x1, y1, x, y)))); lastq = (x1, y1); lastc = None; cx, cy = x, y
        elif c == 'T':
            x1, y1 = (2 * cx - lastq[0], 2 * cy - lastq[1]) if lastq else (cx, cy); x, y = ox + a[0], oy + a[1]
            out.append('Q %s %s %s %s' % tuple(map(_f, (x1, y1, x, y)))); lastq = (x1, y1); lastc = None; cx, cy = x, y
        elif c == 'A':
            x, y = ox + a[5], oy + a[6]; out.append('A %s %s %s %d %d %s %s' % (_f(a[0]), _f(a[1]), _f(a[2]), int(a[3]), int(a[4]), _f(x), _f(y))); cx, cy = x, y; lastc = lastq = None
        elif c == 'Z': out.append('Z'); cx, cy = sx, sy; lastc = lastq = None
    return ' '.join(out)


def _tag(e):
    """The local name of an element in the SVG namespace, else '' so an element in any other namespace never matches a repair."""
    t = e.tag
    return t[len(NS) + 2:] if isinstance(t, str) and t.startswith('{' + NS + '}') else ''


def _within(values):
    return all(math.isfinite(x) and abs(x) <= C.MAX_COORD for x in values)


def _value_ok(attr, value):
    """Would the base checker accept this text attribute value? Asked of the checker itself on a one-text drawing, so a group value is only moved or dropped if the checker would have accepted it."""
    a = {'x': '0', 'y': '20', 'font-size': '12'}; a[attr] = value
    body = ' '.join('%s="%s"' % (k, v.replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;')) for k, v in a.items())
    try: C.verify_svg('<svg xmlns="%s" width="10" height="10"><text %s>a</text></svg>' % (NS, body)); return True
    except Exception: return False


def _shape_ok(root, max_depth=64):
    """At most the checker's element budget and a modest nesting depth (iterative, so a hostile document cannot make this recurse)."""
    stack = [(root, 1)]; count = 0
    while stack:
        e, d = stack.pop(); count += 1
        if d > max_depth or count > C.MAX_SVG_ELEMENTS: return False
        stack.extend((k, d + 1) for k in e)
    return True


def repair_svg(svg):
    """Never raises: on any internal error the drawing is returned as written, with a note, for the checker to decide."""
    try: return _repair_svg(svg)
    except Exception as e:   # RecursionError, UnicodeError, ValueError, OverflowError ...
        return svg, ['Repair skipped (%s): the drawing is left as written for the checker.' % type(e).__name__]


def _repair_svg(svg):
    """Returns (svg, notes). notes is a list of plain sentences, one per kind of repair, empty if nothing was changed. Text that is not well-formed SVG, or that carries a DOCTYPE,
    comment or processing instruction, is returned unchanged for the checker to reject."""
    if not isinstance(svg, str) or '<!' in svg or '<?' in svg or len(svg.encode()) > C.MAX_SVG_BYTES * 2: return svg, []
    try: root = ET.fromstring(svg)
    except ET.ParseError: return svg, []
    if root.tag != '{%s}svg' % NS: return svg, []
    if not _shape_ok(root): return svg, ['Repair skipped: too many elements or too deeply nested; the checker decides.']
    notes = []; changed = False
    # 1. font-weight keywords
    n = 0
    for e in root.iter():
        v = e.get('font-weight')
        if v is not None and v.strip().lower() in _FONT_WEIGHTS: e.set('font-weight', _FONT_WEIGHTS[v.strip().lower()]); n += 1
    if n: notes.append('Replaced a font-weight keyword (such as "bold") with its number (700) on %d element%s.' % (n, '' if n == 1 else 's')); changed = True
    # 2. smooth curve commands S and T
    n = 0
    for e in root.iter():
        if _tag(e) == 'path' and re.search(r'[STst]', e.get('d') or ''):
            segs = _parse_path(e.get('d'))
            if segs is not None and _within(float(x) for x in _NUM.findall(e.get('d'))): e.set('d', _absolute(segs)); n += 1
    if n: notes.append('Rewrote the smooth curve commands S and T as C and Q on %d path%s (the same curve).' % (n, '' if n == 1 else 's')); changed = True
    # 3. text styling on a group, innermost group first so the nearest setting wins
    groups = [e for e in root.iter() if _tag(e) == 'g']; n = 0
    for g in reversed(groups):
        texts = [t for t in g.iter() if _tag(t) == 'text']; moved = False
        for a in _TEXT_ATTRS:
            if a not in g.attrib or not texts or not _value_ok(a, g.get(a)): continue   # nothing to carry it, or a value the checker would refuse: leave it for the checker
            for t in texts:
                if a not in t.attrib: t.set(a, g.get(a))
            g.attrib.pop(a); moved = True
        if moved: n += 1
    if n: notes.append('Moved text styling from %d group%s onto the text elements inside %s.' % (n, '' if n == 1 else 's', 'it' if n == 1 else 'them')); changed = True
    # 4. stroke-opacity on a group, outermost group first; only if every child can carry it, else left for the checker
    n = skipped = 0
    for g in groups:
        v = g.get('stroke-opacity')
        if v is None: continue
        kids = list(g)
        try: one = float(v) == 1.0
        except ValueError: continue
        if one:
            if re.fullmatch(r'1(?:\.0*)?', v.strip()): g.attrib.pop('stroke-opacity'); n += 1   # the default, written plainly; any other spelling of 1 is left for the checker
            continue
        if all(_tag(k) in ('line', 'path', 'g') for k in kids):
            for k in kids:
                if 'stroke-opacity' not in k.attrib: k.set('stroke-opacity', v)
            g.attrib.pop('stroke-opacity'); n += 1
        else: skipped += 1
    if n: notes.append('Moved stroke-opacity from %d group%s onto the lines and paths inside %s.' % (n, '' if n == 1 else 's', 'it' if n == 1 else 'them')); changed = True
    if skipped: notes.append('Left stroke-opacity on %d group%s: some elements inside cannot carry it, so the checker decides.' % (skipped, '' if skipped == 1 else 's'))
    # 5. ellipse and polyline as paths
    ne = npl = 0
    for parent in list(root.iter()):
        for i, e in enumerate(list(parent)):
            t = _tag(e)
            if t == 'ellipse' and len(e) == 0 and all(k in e.attrib for k in ('cx', 'cy', 'rx', 'ry')):
                try: cx, cy, rx, ry = (float(e.get(k)) for k in ('cx', 'cy', 'rx', 'ry'))
                except ValueError: continue
                if not _within((cx, cy, rx, ry)) or rx <= 0 or ry <= 0: continue
                d = 'M %s %s A %s %s 0 1 0 %s %s A %s %s 0 1 0 %s %s Z' % (_f(cx - rx), _f(cy), _f(rx), _f(ry), _f(cx + rx), _f(cy), _f(rx), _f(ry), _f(cx - rx), _f(cy))
                p = ET.Element('{%s}path' % NS, {'d': d}); [p.set(k, v) for k, v in e.attrib.items() if k not in ('cx', 'cy', 'rx', 'ry')]; p.tail = e.tail; parent[i] = p; ne += 1
            elif t == 'polyline' and len(e) == 0 and e.get('points'):
                nums = _NUM.findall(e.get('points'))
                if len(nums) >= 4 and len(nums) % 2 == 0 and not _NUM.sub('', e.get('points')).strip(' \t\r\n,') and _within(float(x) for x in nums):
                    pts = [(float(nums[k]), float(nums[k + 1])) for k in range(0, len(nums), 2)]
                    d = 'M %s %s ' % (_f(pts[0][0]), _f(pts[0][1])) + ' '.join('L %s %s' % (_f(x), _f(y)) for x, y in pts[1:])
                    p = ET.Element('{%s}path' % NS, {'d': d}); [p.set(k, v) for k, v in e.attrib.items() if k != 'points']; p.tail = e.tail; parent[i] = p; npl += 1
    if ne: notes.append('Rewrote %d ellipse%s as a path (the same shape).' % (ne, '' if ne == 1 else 's')); changed = True
    if npl: notes.append('Rewrote %d polyline%s as a path (the same line).' % (npl, '' if npl == 1 else 's')); changed = True
    if not changed: return svg, notes
    ET.register_namespace('', NS)
    return ET.tostring(root, encoding='unicode'), notes


def repair_and_verify(svg, policy=None):
    """Repair, then run the real checker (policy None = the base policy, 'rich' = the rich policy). Returns (svg, notes). Raises SvgPolicyError, with the notes on the exception, if the checker
    still rejects the result: a repaired drawing is never trusted without the check."""
    fixed, notes = repair_svg(svg)
    try: C._verifier(policy)(fixed)
    except C.SvgPolicyError as e:
        e.notes = notes; raise
    return fixed, notes
