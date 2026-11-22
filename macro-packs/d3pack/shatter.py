"""shatter (20 Nov 2026): a glass effect for ANY already-verified SVG drawing, deterministic, no model, inside the existing motion policy (verify_motion).
shatter_in: the drawing is cut into N (default 8, the motion policy's cap) glass shards by jagged cracks that radiate from an impact point; each shard is a clipped copy of the whole drawing that swings about a pivot out along its wedge and ends at rest on the intact picture
(opacity 1, rotate 0): the still picture, animations stripped, is the end frame. Each shard carries a faint sheen and its two crack edges; the cracks stay as seams at the end, a cue that is not colour (the gauge uses it for its red state).
seams_only: the same cracks, drawn once over the still drawing (no copies, no animation): the steady 'still in the red zone' picture, a few hundred bytes.
glass_state: the pure rule that decides WHICH of the two (or neither) applies, from the DATA: the value, the previous value and the level at which the glass breaks. The moment the value crosses the level the picture animates once; while it stays beyond it the picture shows the seams; otherwise nothing.
Deterministic: the same drawing and options give the same bytes (the seed defaults to a hash of the drawing; the cracks are the same in shatter_in and seams_only). Standard library only.
Guards, never silent: shatter_in needs a drawing that passes verify_rich with no animation and no filter and a viewBox 'W H' starting at 0; N copies must fit the rich budget (60 KB, 400 elements; the motion policy's 8 animations and 1.5 s); ids inside the drawing are renamed per copy.
If a guard stops it the ORIGINAL drawing comes back with applied=False and the reason in note; the caller says so. Returns {'svg', 'applied', 'note', 'shards', 'bytes', 'elements'}. Not registered in the pack's PACK table."""
import hashlib, math, random, re
import xml.etree.ElementTree as ET
from . import common as C
from .rich import verify_rich, MAX_RICH_BYTES, MAX_RICH_ELEMENTS
from .motion import verify_motion, MAX_MOTION_ANIMATIONS, MAX_MOTION_SECONDS
def _g(x): return f'{x:.1f}'.rstrip('0').rstrip('.') if abs(x - round(x)) > 1e-6 else str(int(round(x)))
def _seed(svg): return int(hashlib.sha256(svg.encode('utf-8')).hexdigest()[:8], 16)
def _refuse(svg, note): return {'svg': svg, 'applied': False, 'note': note, 'shards': 0, 'bytes': len(svg.encode('utf-8')), 'elements': 0}
def _rename_ids(body, p):
    ids = set(re.findall(r'\bid="([^"]+)"', body))
    for i in sorted(ids, key=len, reverse=True): body = body.replace(f'id="{i}"', f'id="{p}{i}"').replace(f'url(#{i})', f'url(#{p}{i})')
    return body
def glass_state(value, from_value=None, break_at=None, below=True):
    """The data-layer rule. 'break': the value has just crossed the level (or this is the first picture and it is already beyond it): play the effect once. 'seams': still beyond the level: the still picture with seams.
    'none': not beyond it. below=True means the glass breaks when the value falls to the level or under it; below=False when it rises to it or over. break_at None means the caller has no level: 'none'."""
    if break_at is None or value is None: return 'none'
    beyond = (lambda x: x is not None and x <= break_at) if below else (lambda x: x is not None and x >= break_at)
    if not beyond(value): return 'none'
    return 'seams' if beyond(from_value) else 'break'
def _cracks(svg, W, H, impact, n, seed):
    """The jagged cracks, shared by shatter_in and seams_only so they match exactly: returns (impact, rmax, angles, cracks) where cracks[i] is a list of points from the impact outwards and cracks[n] repeats cracks[0]."""
    rnd = random.Random(_seed(svg) if seed is None else int(seed)); cx, cy = (W / 2, H / 2) if impact is None else (float(impact[0]), float(impact[1]))
    rmax = max(math.hypot(x - cx, y - cy) for x in (0, W) for y in (0, H)) * 1.05
    base = rnd.uniform(0, 360 / n); angs = [math.radians(base + (360 / n) * i + rnd.uniform(-0.28, 0.28) * 360 / n) for i in range(n)]
    def crack(a):   # radius steps with a sideways wobble that grows with the distance
        pts = [(cx, cy)]; side = a + math.pi / 2
        for j in range(1, 7):
            r = rmax * j / 6; off = rnd.uniform(-1, 1) * min(0.035 * rmax, 4 + 0.05 * r) if j < 6 else rnd.uniform(-0.05, 0.05) * rmax
            pts.append((cx + r * math.cos(a) + off * math.cos(side), cy + r * math.sin(a) + off * math.sin(side)))
        return pts
    cr = [crack(a) for a in angs]; cr.append(cr[0]); return (cx, cy), rmax, angs, cr, rnd
def _path(pts, op): return f'<path d="M {" L ".join(f"{_g(x)},{_g(y)}" for x, y in pts)}" fill="none" stroke="#ffffff" stroke-opacity="{op}" stroke-width="1.2"/>'
def _parse(svg):
    if not re.search(r'<svg\b', svg): return None
    m = re.match(r'(<svg\b[^>]*viewBox="0 0 ([\d.]+) ([\d.]+)"[^>]*>)(.*)</svg>\s*\Z', svg, re.S)
    return (m.group(1), float(m.group(2)), float(m.group(3)), m.group(4)) if m else None
def seams_only(svg, impact=None, n=8, seed=None, seam_opacity=0.12):
    """The still drawing with the shared cracks drawn over it (one group of n paths). Returns the same dict as shatter_in."""
    try: verify_rich(svg)
    except C.SvgPolicyError as e: return _refuse(svg, f'the drawing does not pass the SVG policy ({str(e)[:80]})')
    p = _parse(svg)
    if not p: return _refuse(svg, 'no viewBox "0 0 W H" on the root element')
    head, W, H, inner = p; (cx, cy), rmax, angs, cr, _ = _cracks(svg, W, H, impact, int(n), seed)
    out = f'{head}{inner}<g>{"".join(_path(cr[i], seam_opacity) for i in range(int(n)))}</g></svg>'
    try: verify_rich(out)
    except C.SvgPolicyError as e: return _refuse(svg, f'the drawing with seams was refused ({str(e)[:100]})')
    return {'svg': out, 'applied': True, 'note': f'{int(n)} seams over the still drawing', 'shards': 0, 'bytes': len(out.encode('utf-8')), 'elements': len(ET.fromstring(out).findall('.//*'))}
def shatter_in(svg, impact=None, n=8, seed=None, dur_near=0.5, dur_far=0.85, max_angle=13.0, stagger=0.02, seam_opacity=0.12, sheen=False, static_text=True, clip_rect=None, backing=None):
    """See the module docstring. impact is (x, y) in viewBox units (default: the middle of the drawing). backing: a #rrggbb colour drawn under the shards, so the gaps between displaced pieces show something dark and the break can be SEEN on a light page (the shards tile the picture, so at rest it is covered)."""
    n = int(n); dur_near = float(dur_near); dur_far = float(dur_far)
    if n < 3 or n > MAX_MOTION_ANIMATIONS: return _refuse(svg, f'shards must be 3 to {MAX_MOTION_ANIMATIONS} (the motion policy allows {MAX_MOTION_ANIMATIONS} animations)')
    if max(dur_near, dur_far) + n * stagger > MAX_MOTION_SECONDS: return _refuse(svg, f'the longest shard would end after {MAX_MOTION_SECONDS} s (the motion policy)')
    try: verify_rich(svg)
    except C.SvgPolicyError as e: return _refuse(svg, f'the drawing does not pass the SVG policy ({str(e)[:80]})')
    if re.search(r'<(animate|animateTransform|filter)\b|\bfilter="', svg): return _refuse(svg, 'the drawing already animates or uses a filter; a shatter needs a still, filter-free drawing (a filtered picture is redrawn about every 380 ms while it animates)')
    p = _parse(svg)
    if not p: return _refuse(svg, 'no viewBox "0 0 W H" on the root element')
    head, W, H, inner = p; tm = re.match(r'\s*(<title>.*?</title>)', inner, re.S); ttl = tm.group(1) if tm else ''; body = inner[len(ttl):].strip()
    text_layer = ''
    if static_text: text_layer = ''.join(re.findall(r'<text\b[^>]*>.*?</text>', body, re.S)); body = re.sub(r'<text\b[^>]*>.*?</text>', '', body, flags=re.S)   # text stays whole on top: never cut by a crack, never tilted
    (cx, cy), rmax, angs, cr, rnd = _cracks(svg, W, H, impact, n, seed)
    order = sorted(range(n), key=lambda i: math.hypot((cr[i][2][0] + cr[i + 1][2][0]) / 2 - cx, (cr[i][2][1] + cr[i + 1][2][1]) / 2 - cy)); rank = {i: k for k, i in enumerate(order)}
    defs, shards = [], []
    if sheen:
        for k, (x1, y1, x2, y2) in enumerate(((0, 0, 1, 1), (1, 0, 0, 1), (0.2, 0, 0.8, 1))):
            defs.append(f'<linearGradient id="sg{k}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"><stop offset="0" stop-color="#ffffff" stop-opacity="0"/><stop offset="0.45" stop-color="#ffffff" stop-opacity="0.26"/><stop offset="1" stop-color="#ffffff" stop-opacity="0"/></linearGradient>')
    for i in range(n):
        a, b = cr[i], cr[i + 1]; span = ((angs[(i + 1) % n] - angs[i]) % (2 * math.pi)); mid = angs[i] + span / 2
        far = (cx + rmax * 1.35 * math.cos(mid), cy + rmax * 1.35 * math.sin(mid)); ring = a[1:] + [far] + b[1:][::-1]
        poly = ' '.join(f'{_g(x)},{_g(y)}' for x, y in [(cx, cy)] + ring)
        px, py = cx, cy   # the pivot is the impact: every shard swings in like a fan from the point that was hit
        k = rank[i] / max(1, n - 1); ang = rnd.choice((-1, 1)) * max_angle * (0.35 + 0.65 * k) * rnd.uniform(0.9, 1.1); begin = rank[i] * stagger; dur = dur_near + (dur_far - dur_near) * k   # the shards nearest the impact swing least and settle first
        defs.append(f'<clipPath id="sh{i}"><polygon points="{poly}"/></clipPath>')
        sh = f'<polygon points="{poly}" fill="url(#sg{i % 3})"/>' if sheen else ''
        shards.append(f'<g><g clip-path="url(#sh{i})">{_rename_ids(body, f"c{i}_")}{sh}</g>{_path(a, seam_opacity)}{_path(b, seam_opacity)}'
                      f'<animateTransform attributeName="transform" type="rotate" from="{_g(ang)} {_g(px)} {_g(py)}" to="0 {_g(px)} {_g(py)}" dur="{_g(dur)}s" begin="{_g(begin)}s" repeatCount="1" fill="freeze"/></g>')
    if clip_rect is not None: x_, y_, w_, h_, rx_ = clip_rect; defs.append(f'<clipPath id="shc"><rect x="{_g(x_)}" y="{_g(y_)}" width="{_g(w_)}" height="{_g(h_)}" rx="{_g(rx_)}"/></clipPath>'); stack = f'<g clip-path="url(#shc)">{"".join(shards)}</g>'   # the displaced edges never poke out of the card
    else: stack = ''.join(shards)
    if backing is not None:
        if not re.fullmatch(r'#[0-9a-fA-F]{6}', str(backing)): return _refuse(svg, 'backing must be a #rrggbb colour')
        stack = f'<rect width="{_g(W)}" height="{_g(H)}" fill="{backing}"/>' + stack   # under the shards, inside the same clip when there is one
    out = f'{head}{ttl}<defs>{"".join(defs)}</defs>{stack}' + (f'<g>{text_layer}</g>' if text_layer else '') + '</svg>'
    nb = len(out.encode('utf-8')); ne = len(ET.fromstring(out).findall('.//*'))
    if nb > MAX_RICH_BYTES or ne > MAX_RICH_ELEMENTS: return _refuse(svg, f'{n} copies are too big for the rich budget ({nb} bytes, {ne} elements against {MAX_RICH_BYTES} and {MAX_RICH_ELEMENTS}); a simpler drawing or fewer shards would fit')
    try: verify_motion(out)
    except C.SvgPolicyError as e: return _refuse(svg, f'the shattered drawing was refused by the motion policy ({str(e)[:100]})')
    return {'svg': out, 'applied': True, 'note': f'{n} glass shards, {_g(dur_far + (n - 1) * stagger)}s at most, ends on the intact picture', 'shards': n, 'bytes': nb, 'elements': ne}
