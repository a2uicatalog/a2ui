"""atom_convert (20 Nov 2026): the deterministic conversion from a catalogue MOTION ATOM to a MACRO result (an animated SVG that fits a Basic Catalog `Image`).
Vocabulary agreed with the owner: atom = our catalogue entry; macro = draws a picture from parameters; transition = animates one picture into the next; converter = turns a spec into a picture. This module is the converter for transitions.
First slice: motion_shatter. The atom's fields (shards, origin, cracks, fall, spin, seed) map to shatter_in by a TABLE, never by guesswork, and every place the picture cannot match the atom is returned in `gaps` (nothing is dropped or clamped silently).
The atom's semantics are an EXIT (p = 1 is gone); the motion policy requires every animation to end at rest on the intact picture (so a viewer that ignores animation shows the same picture the animation ends on). So the output is the ENTRANCE form: the glass breaks at the impact and the shards settle back into the intact picture. The exit needs the terminal mode that the policy does not allow yet; that is recorded as a gap, not hidden.
Children: the atom wraps up to 3 child atoms; this slice takes ONE still SVG, handed in directly or resolved from a `motion_image` child whose url is an inline svg data URL (the same rule the renderer accepts). Anything else is refused with a reason. Standard library only; pure and deterministic.
convert(atom, child_svg=None) -> {'svg', 'applied', 'mapping', 'gaps', 'params'}
Converters (20 Nov 2026): motion_shatter, motion_shake, motion_group, motion_assemble. Every other motion atom is refused with a reason from REFUSALS (classified from the schema description; see atom_coverage.py for the run over all of them)."""
import base64, re
from . import shatter as SH
from .shatter import shatter_in
MAX_SHARDS = SH.MAX_MOTION_ANIMATIONS
SPIN_SCALE = 20.0 / 40.0   # the atom's default spin (40) maps to 20 degrees: 13 read as a flash and 26 as a bit flashy on a light page (20 Nov, owner); the policy caps a rotation at 90
BACKING = '#7b8798'        # the atom reveals 'what is behind it'; an Image has nothing behind it, so the converter supplies a dark backing the gaps show (a light page made the break invisible)
DUR_NEAR, DUR_FAR = 0.8, 1.3   # slower than the first tuning: the shards stay apart long enough to be seen (the policy allows 1.5 s)
_EDGES = {'top': (50, 0), 'bottom': (50, 100), 'left': (0, 50), 'right': (100, 50), 'center': (50, 50)}
_DATA = re.compile(r'^data:image/svg\+xml;base64,([A-Za-z0-9+/=]{1,40000})$')
def _refuse(svg, why, gaps=None): return {'svg': svg, 'applied': False, 'mapping': [], 'gaps': (gaps or []) + [why], 'params': {}}
def _num(v, lo, hi, dflt, name, gaps, integer=True):
    ok = isinstance(v, (int, float)) and not isinstance(v, bool)
    if v is None: return dflt
    if not ok: gaps.append(f'{name} {v!r} is not a number: used the default {dflt}'); return dflt
    x = int(v) if integer else float(v)
    if x < lo or x > hi: gaps.append(f'{name} {v} is outside {lo} to {hi}: clamped to {min(max(x, lo), hi)}')
    return min(max(x, lo), hi)
def _child_svg(atom, child_svg):
    if child_svg is not None: return child_svg, None
    blocks = atom.get('blocks')
    if not isinstance(blocks, list) or not blocks: return None, 'no child: this slice converts a wrapped picture; a plain panel is not converted yet'
    if len(blocks) > 1: return None, f'{len(blocks)} children: this slice converts one still SVG'
    b = blocks[0]
    if not isinstance(b, dict) or b.get('type') != 'motion_image': return None, f"child type {b.get('type') if isinstance(b, dict) else b!r} is not convertible yet (only motion_image with an inline svg url)"
    m = _DATA.match(str(b.get('url', '')).strip())
    if not m: return None, 'the child motion_image url is not an inline base64 svg data URL'
    try: return base64.b64decode(m.group(1), validate=True).decode('utf-8'), None
    except Exception: return None, 'the child svg data URL does not decode'
def _viewbox(svg):
    m = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg); return (float(m.group(1)), float(m.group(2))) if m else None
def _shatter(atom, child_svg=None):
    gaps = []
    svg, why = _child_svg(atom, child_svg)
    if why: return _refuse('', why)
    vb = _viewbox(svg)
    if not vb: return _refuse(svg, 'the child svg has no viewBox "0 0 W H"')
    W, H = vb; mapping = []
    shards = _num(atom.get('shards'), 4, 24, 12, 'shards', gaps)
    n = min(shards, MAX_SHARDS)
    if n != shards: gaps.append(f'shards {shards} became {n}: the motion policy allows {MAX_SHARDS} animations, one per shard')
    mapping.append(f'shards {shards} -> n {n}')
    o = atom.get('origin', 'top')
    if isinstance(o, str):
        if o not in _EDGES: gaps.append(f'origin {o!r} is not a known edge: used top'); o = 'top'
        ox, oy = _EDGES[o]
    elif isinstance(o, dict):
        ox, oy = _num(o.get('x'), 0, 100, 50, 'origin.x', gaps, False), _num(o.get('y'), 0, 100, 50, 'origin.y', gaps, False)
    else: gaps.append(f'origin {o!r} is not a name or an {{x, y}}: used top'); ox, oy = _EDGES['top']
    impact = (round(W * ox / 100, 2), round(H * oy / 100, 2)); mapping.append(f'origin ({ox:g}%, {oy:g}%) -> impact {impact} in viewBox units')
    cracks = atom.get('cracks', True); seam = 0.12 if cracks is not False else 0.0; mapping.append(f'cracks {cracks!r} -> seam_opacity {seam}')
    spin = _num(atom.get('spin'), 0, 180, 40, 'spin', gaps); ang = round(min(spin * SPIN_SCALE, 90.0), 2)
    mapping.append(f'spin {spin} -> max_angle {ang}')
    seed = _num(atom.get('seed'), 0, 9999, 7, 'seed', gaps); mapping.append(f'seed {seed} -> seed {seed}')
    fall = atom.get('fall', 'down')
    if fall not in ('down', 'out'): gaps.append(f'fall {fall!r} is not down or out: used down'); fall = 'down'
    gaps.append(f"fall {fall!r}: the shards rotate about the impact and settle back (no fall or flight is allowed by the motion policy)")
    gaps.append('exit semantics: the atom ends GONE at p = 1; this picture is the entrance form (it ends on the intact picture, as the policy requires). The exit needs the terminal mode.')
    if atom.get('version', 1) not in (1, None): gaps.append('version above 1 draws as version 1 (as the atom says)')
    mapping.append(f'converter choice: backing {BACKING} under the shards, durations {DUR_NEAR} to {DUR_FAR} s, clipped to the picture')
    params = dict(impact=impact, n=n, seed=seed, max_angle=ang, seam_opacity=seam, dur_near=DUR_NEAR, dur_far=DUR_FAR, backing=BACKING, clip_rect=(0, 0, W, H, 0))
    out = shatter_in(svg, **params)
    if not out['applied']: return {'svg': svg, 'applied': False, 'mapping': mapping, 'gaps': gaps + [f"shatter_in refused: {out['note']}"], 'params': params}
    return {'svg': out['svg'], 'applied': True, 'mapping': mapping, 'gaps': gaps, 'params': params, 'bytes': out['bytes'], 'elements': out['elements']}

import hashlib, math
from . import motion as _MO
MAX_OFFSET = _MO.MAX_OFFSET; MAX_SECONDS = SH.MAX_MOTION_SECONDS; MAX_ANIMS = SH.MAX_MOTION_ANIMATIONS
def _wrap(svg, anims_open, anims_close_inner=None):
    """Put the whole drawing (text included: the atom moves what it wraps) inside nested groups that carry the animations. anims_open is a list of (animation xml) for ONE outer group; returns (svg, ok, why)."""
    p = SH._parse(svg)
    if not p: return None, 'the child svg has no viewBox "0 0 W H"'
    head, W, H, inner = p; tm = re.match(r'\s*(<title>.*?</title>)', inner, re.S); ttl = tm.group(1) if tm else ''; body = inner[len(ttl):].strip()
    return head, ttl, body, W, H
def _tr(vals, dur, begin):  # a translate that ENDS at rest
    return f'<animateTransform attributeName="transform" type="translate" from="{vals[0]:g} {vals[1]:g}" to="0 0" dur="{dur:g}s" begin="{begin:g}s" repeatCount="1" fill="freeze"/>'
def _rot(deg, cx, cy, dur, begin): return f'<animateTransform attributeName="transform" type="rotate" from="{deg:g} {cx:g} {cy:g}" to="0 {cx:g} {cy:g}" dur="{dur:g}s" begin="{begin:g}s" repeatCount="1" fill="freeze"/>'
def _op(dur, begin): return f'<animate attributeName="opacity" from="0" to="1" dur="{dur:g}s" begin="{begin:g}s" repeatCount="1" fill="freeze"/>'
def _finish(svg, layers, mapping, gaps, extra=None):
    """layers: a list of animation-xml lists, one per nested group, outermost first."""
    head, ttl, body, W, H = svg
    out = body
    for anims in reversed(layers): out = f'<g>{out}{"".join(anims)}</g>'
    out = f'{head}{ttl}{out}</svg>'
    try: _MO.verify_motion(out)
    except Exception as e: return {'svg': '', 'applied': False, 'mapping': mapping, 'gaps': gaps + [f'the converted drawing was refused by the motion policy ({str(e)[:100]})'], 'params': extra or {}}
    return {'svg': out, 'applied': True, 'mapping': mapping, 'gaps': gaps, 'params': extra or {}, 'bytes': len(out.encode()), 'elements': len(re.findall(r'<[a-zA-Z]', out))}
def _seeded(k, tag):  # deterministic pseudo-random in 0..1 (never a random call)
    return int(hashlib.sha256(f'{tag}:{k}'.encode()).hexdigest()[:8], 16) / 0xffffffff
def _shake(atom, child_svg=None):
    gaps = []; mapping = []
    svg, why = _child_svg(atom, child_svg)
    if why: return _refuse('', why)
    w = _wrap(svg, None)
    if isinstance(w[0], type(None)): return _refuse(svg, w[1])
    head, ttl, body, W, H = w
    amount = _num(atom.get('amount'), 1, 80, 12, 'amount', gaps); amp = min(amount, MAX_OFFSET)
    if amp != amount: gaps.append(f'amount {amount} px became {amp:g}: the motion policy allows a travel of {MAX_OFFSET:g} px')
    freq = _num(atom.get('frequency'), 1, 40, 9, 'frequency', gaps); jolts = min(freq, MAX_ANIMS - 1)
    if jolts != freq: gaps.append(f'frequency {freq} became {jolts} jolts: the policy allows {MAX_ANIMS} animations and one is kept for the tilt')
    tilt = _num(atom.get('tilt'), 0, 10, 1.5, 'tilt', gaps, False)
    total = 1.0; step = total / jolts; trs = []
    for k in range(jolts):
        a = 2 * math.pi * _seeded(k, 'shake'); r = amp * (1 - k / jolts) ** 1.5; trs.append(_tr((round(r * math.cos(a), 2), round(r * math.sin(a), 2)), round(step * 0.9, 3), round(k * step, 3)))
    mapping += [f'amount {amount} -> peak travel {amp:g} px, decaying over {jolts} jolts', f'frequency {freq} -> {jolts} jolts in {total:g} s', f'tilt {tilt:g} -> one rotation settling over {total:g} s']
    gaps.append("sin() and cos() motion over the whole of p becomes a chain of decaying jolts, each one a straight move back to rest (the policy allows only from/to animations)")
    gaps.append('exit semantics: the atom is strongest at p = 0 and gone at p = 1, which already ends at rest: this one is a true match in direction')
    layers = [trs] + ([[_rot(round(tilt, 2), W / 2, H / 2, total, 0)]] if tilt > 0 else [])
    return _finish(w, layers, mapping, gaps, dict(jolts=jolts, amp=amp, tilt=tilt))
_GROUP_EFFECT = {'fade': ((0, 0), 'opacity'), 'rise': ((0, 24), 'opacity'), 'drop': ((0, -24), 'opacity'), 'slide-left': ((40, 0), 'opacity'), 'slide-right': ((-40, 0), 'opacity')}
def _duration(v):
    tok = {'instant': 0.0, 'quick': 0.24, 'base': 0.56, 'slow': 0.9, 'cinematic': 1.4}
    return tok[v] if isinstance(v, str) and v in tok else (float(v) / 1000.0 if isinstance(v, (int, float)) and not isinstance(v, bool) else None)
def _group(atom, child_svg=None):
    gaps = []; mapping = []
    svg, why = _child_svg(atom, child_svg)
    if why: return _refuse('', why)
    w = _wrap(svg, None)
    if isinstance(w[0], type(None)): return _refuse(svg, w[1])
    effect = atom.get('effect', 'rise')
    if effect not in _GROUP_EFFECT:
        gaps.append(f'effect {effect!r} cannot be drawn: the policy has no scale, blur or wipe; used rise'); effect = 'rise'
    off, _ = _GROUP_EFFECT[effect]; d = _duration(atom.get('duration', 560)); d = 0.56 if d is None else d
    if d > MAX_SECONDS: gaps.append(f'duration {d:g} s became {MAX_SECONDS:g} s: the policy ends every animation within {MAX_SECONDS:g} s'); d = MAX_SECONDS
    delay = _num(atom.get('delay'), 0, 20000, 0, 'delay', gaps) / 1000.0
    if delay + d > MAX_SECONDS: nd = round(max(0.0, MAX_SECONDS - d), 3); gaps.append(f'delay {delay:g} s became {nd:g} s so that the whole picture ends within {MAX_SECONDS:g} s'); delay = nd
    if len(atom.get('blocks') or []) <= 1 and atom.get('stagger') not in (None, 0): gaps.append('stagger needs several children: with one picture it has no effect')
    if atom.get('on', 'load') == 'view': gaps.append("on 'view' needs the page to know when the image is scrolled into view; the picture plays when it loads")
    anims = [_op(round(d, 3), round(delay, 3))] + ([_tr(off, round(d, 3), round(delay, 3))] if off != (0, 0) else [])
    mapping += [f'effect {effect} -> opacity 0 to 1' + (f' and a move of {off[0]:g} {off[1]:g} px to rest' if off != (0, 0) else ''), f'duration {d:g} s, delay {delay:g} s']
    return _finish(w, [[anims[0]], anims[1:]] if len(anims) > 1 else [anims], mapping, gaps, dict(effect=effect, dur=d, delay=delay))
def _assemble(atom, child_svg=None):
    gaps = []; mapping = []
    svg, why = _child_svg(atom, child_svg)
    if why: return _refuse('', why)
    w = _wrap(svg, None)
    if isinstance(w[0], type(None)): return _refuse(svg, w[1])
    head, ttl, body, W, H = w
    n = len(atom.get('blocks') or [1])
    gaps.append(f"the bento grid (columns {atom.get('columns', 3)}, gap {atom.get('gap', 14)}) lays out several children: this picture is ONE child, so there is no layout, only the fly-in")
    a = 2 * math.pi * _seeded(0, 'assemble'); off = (round(MAX_OFFSET * math.cos(a), 2), round(MAX_OFFSET * math.sin(a), 2)); tilt = round(-8 + 16 * _seeded(1, 'assemble'), 2); dur = 0.9
    mapping += [f'scattered start -> a move of {off[0]:g} {off[1]:g} px (the policy limit is {MAX_OFFSET:g}) to rest', f'tilted start -> {tilt:g} degrees to 0', f'fly-in over {dur:g} s with a fade 0 to 1']
    gaps.append('the atom starts the children far outside the box; the policy allows a move of at most 60 px, so the fly-in is shorter than the atom')
    return _finish(w, [[_tr(off, dur, 0)], [_rot(tilt, W / 2, H / 2, dur, 0)], [_op(dur * 0.7, 0)]], mapping, gaps, dict(offset=off, tilt=tilt))

# ─── generative converters (20 Nov 2026): atoms that DRAW their own content (no child picture). The end state is the atom's finished picture (the atom's own standalone render is p = 1); the animation is an entrance that ends on it. ───
import html as _html
_HEX = re.compile(r'#[0-9a-fA-F]{6}')
def _hex(v, dflt, name, gaps):
    if v is None: return dflt
    if isinstance(v, str) and _HEX.fullmatch(v): return v
    gaps.append(f'{name} {v!r} is not a #rrggbb colour: used {dflt}'); return dflt
def _enum(v, allowed, dflt, name, gaps):
    if v is None: return dflt
    if isinstance(v, str) and v in allowed: return v
    gaps.append(f'{name} {v!r} is not one of {", ".join(allowed)}: used {dflt}'); return dflt
def _g(x): return f'{x:.2f}'.rstrip('0').rstrip('.') if isinstance(x, float) else str(x)
def _lab(t): return _html.escape(re.sub(r'\s+', ' ', str(t)).strip()[:80] or 'Picture', quote=True)
def _gdoc(W, H, label, body): l = _lab(label); return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{l}"><title>{l}</title>{body}</svg>'
def _gfinish(svg, mapping, gaps, params=None):
    try: _MO.verify_motion(svg)
    except Exception as e: return {'svg': '', 'applied': False, 'mapping': mapping, 'gaps': gaps + [f'the generated drawing was refused by the motion policy ({str(e)[:110]})'], 'params': params or {}}
    return {'svg': svg, 'applied': True, 'mapping': mapping, 'gaps': gaps, 'params': params or {}, 'bytes': len(svg.encode()), 'elements': len(re.findall(r'<[a-zA-Z]', svg))}
def _grp(inner, *anims): return f'<g>{inner}{"".join(anims)}</g>'
def _capoff(x, y, gaps, what):
    m = max(abs(x), abs(y))
    if m > MAX_OFFSET: f = MAX_OFFSET / m; gaps.append(f'{what} starts {m:.0f} px away; the motion policy allows {MAX_OFFSET:g} px, so it starts {MAX_OFFSET:g} px away'); return round(x * f, 2), round(y * f, 2)
    return round(x, 2), round(y, 2)
def _angle_pt(cx, cy, r, deg): a = math.radians(deg); return cx + r * math.cos(a), cy + r * math.sin(a)
def _annulus(cx, cy, ro, ri): return (f'M {_g(cx - ro)},{_g(cy)} A {_g(ro)},{_g(ro)} 0 1 1 {_g(cx + ro)},{_g(cy)} A {_g(ro)},{_g(ro)} 0 1 1 {_g(cx - ro)},{_g(cy)} Z '
                                        f'M {_g(cx - ri)},{_g(cy)} A {_g(ri)},{_g(ri)} 0 1 0 {_g(cx + ri)},{_g(cy)} A {_g(ri)},{_g(ri)} 0 1 0 {_g(cx - ri)},{_g(cy)} Z')
def _fill_def(c1, c2, angle, W, H, gid):
    if not c2: return '', c1
    a = math.radians(angle); x1, y1, x2, y2 = (0.5 - 0.5 * math.cos(a), 0.5 - 0.5 * math.sin(a), 0.5 + 0.5 * math.cos(a), 0.5 + 0.5 * math.sin(a))
    return f'<defs><linearGradient id="{gid}" x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}"><stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient></defs>', f'url(#{gid})'
def _shape(atom, child_svg=None):
    gaps, mapping = [], []
    sh = _enum(atom.get('shape'), ('rect', 'circle', 'ring', 'line'), 'rect', 'shape', gaps)
    dflt = {'rect': 'grow-x', 'line': 'grow-x', 'circle': 'scale', 'ring': 'sweep'}[sh]; draw = atom.get('draw', dflt)
    c1 = _hex(atom.get('fill'), '#38bdf8', 'fill', gaps); c2 = atom.get('fill2'); c2 = _hex(c2, '#a78bfa', 'fill2', gaps) if c2 is not None else None
    ang = _num(atom.get('angle'), 0, 360, 90, 'angle', gaps); thick = _num(atom.get('thickness'), 1, 200, 6, 'thickness', gaps); rad = _num(atom.get('radius'), 0, 500, 0, 'radius', gaps)
    W = _num(atom.get('w'), 1, 3000, 600 if sh in ('rect', 'line') else 360, 'w', gaps); H = _num(atom.get('h'), 1, 3000, 200 if sh in ('rect', 'line') else 360, 'h', gaps)
    if max(W, H) > 1200: f = 1200 / max(W, H); W, H = int(W * f), int(H * f); gaps.append('the box is larger than 1200 px: scaled down to fit the picture')
    if atom.get('blur'): gaps.append(f"blur {atom.get('blur')} px is dropped: the motion policy allows no filter on an animated picture")
    defs, f = _fill_def(c1, c2, ang, W, H, 'sg')
    if sh == 'rect': el = f'<rect width="{W}" height="{H}" rx="{min(rad, W / 2, H / 2)}" fill="{f}"/>'
    elif sh == 'line': t = min(thick, H); el = f'<rect y="{_g((H - t) / 2)}" width="{W}" height="{t}" rx="{_g(min(rad, t / 2))}" fill="{f}"/>'
    elif sh == 'circle': r = min(W, H) / 2; el = f'<circle cx="{_g(W / 2)}" cy="{_g(H / 2)}" r="{_g(r)}" fill="{f}"/>'
    else: ro = min(W, H) / 2; el = f'<path d="{_annulus(W / 2, H / 2, ro, max(1, ro - min(thick, ro - 1)))}" fill="{f}"/>'
    D = 0.8; a = _op(D, 0); mv = {'grow-x': (-40, 0), 'grow-y': (0, 40)}.get(draw)
    if draw not in ('grow-x', 'grow-y', 'scale', 'sweep', 'fade', 'none'): gaps.append(f'draw {draw!r} is not known: used fade'); draw = 'fade'
    if draw == 'none': inner = el; mapping.append('draw none -> no animation')
    elif mv: inner = _grp(_grp(el, _tr(mv, D, 0)), a); mapping.append(f'draw {draw} -> a slide of {mv[0]:g} {mv[1]:g} px to rest with a fade')
    elif draw == 'sweep': inner = _grp(_grp(el, _rot(-90, W / 2, H / 2, D, 0)), a); mapping.append('draw sweep -> the ring turns in from -90 degrees with a fade')
    else: inner = _grp(el, a); mapping.append(f'draw {draw} -> a fade')
    if draw in ('grow-x', 'grow-y', 'scale', 'sweep'): gaps.append(f'draw {draw} grows or sweeps the shape; the policy has no scale, clip or dash animation, so it is approximated as noted in the mapping')
    return _gfinish(_gdoc(W, H, f'{sh} shape', defs + inner), mapping, gaps, dict(shape=sh, draw=draw))
def _ellipse_path(cx, cy, rx, ry, rot):
    a = math.radians(rot); dx, dy = rx * math.cos(a), rx * math.sin(a)
    return f'M {_g(cx - dx)},{_g(cy - dy)} A {_g(rx)},{_g(ry)} {_g(float(rot))} 1 0 {_g(cx + dx)},{_g(cy + dy)} A {_g(rx)},{_g(ry)} {_g(float(rot))} 1 0 {_g(cx - dx)},{_g(cy - dy)} Z'
def _mark(atom, child_svg=None):
    gaps, mapping = [], []
    size = _num(atom.get('size'), 24, 600, 120, 'size', gaps); a1 = _hex(atom.get('accent'), '#38bdf8', 'accent', gaps); a2 = _hex(atom.get('accent2'), '#00b7c3', 'accent2', gaps)
    ew = max(4, size * 5 // 48); ang = math.radians(197)
    ex, ey = 12 + 8.48 * math.cos(ang) + 2.33 * math.sin(ang), 12 - 5.30 * math.cos(ang) + 3.73 * math.sin(ang)
    st = lambda rot, w, col, op=None: f'<path d="{_ellipse_path(12, 12, 10, 4.4, rot)}" fill="none" stroke="{col}" stroke-width="{w}"' + (f' stroke-opacity="{op}"' if op else '') + '/>'
    e1, e2, e3 = st(-32, 1.5, a1), st(32, 1.5, a2), st(90, 1.1, a1, 0.35)
    body = (_grp(_grp(e1, _rot(-60, 12, 12, 0.9, 0)) + _grp(e2, _rot(60, 12, 12, 0.9, 0.1)) + _grp(e3, _rot(60, 12, 12, 0.9, 0.2)), _op(0.9, 0)) + _grp(f'<circle cx="12" cy="12" r="2.7" fill="{a1}"/>', _op(0.5, 0.4))
            + _grp(f'<circle cx="{ex:.2f}" cy="{ey:.2f}" r="{ew / size * 24 / 2:.2f}" fill="{a2}"/>', _op(0.4, 0.8)))
    mapping += ['the three ellipses turn in from 60 degrees with a fade, one after another', 'nucleus and electron fade in; the electron rests at 197 degrees (step 0)']
    gaps.append("the atom's draw-on (stroke-dashoffset) and the electron's orbit on the step dial cannot be drawn: the policy has no dash animation, and the orbit needs a second clock")
    return _gfinish(_gdoc(size, size, 'A2UI Catalog mark', '').replace(f'viewBox="0 0 {size} {size}"', 'viewBox="0 0 24 24"').replace('</svg>', body + '</svg>'), mapping, gaps, dict(size=size))
def _rays(atom, child_svg=None):
    gaps, mapping = [], []
    kind = _enum(atom.get('kind'), ('burst', 'speed'), 'burst', 'kind', gaps); cnt = _num(atom.get('count'), 4, 64, 24, 'count', gaps); thk = _num(atom.get('thickness'), 0.1, 0.9, 0.5, 'thickness', gaps, False)
    spin = _num(atom.get('spin'), -360, 360, 45, 'spin', gaps); st = _num(atom.get('strength'), 0.05, 1, 0.35, 'strength', gaps, False); acc = _hex(atom.get('accent'), '#38bdf8', 'accent', gaps); W = H = 600; cx = cy = 300.0
    if kind == 'burst':
        step = 360.0 / cnt; wedge = step * thk; polys = []
        for k in range(cnt): a0 = k * step; pts = [(cx, cy), _angle_pt(cx, cy, 460, a0), _angle_pt(cx, cy, 460, a0 + wedge)]; polys.append('<polygon points="' + ' '.join(f'{_g(x)},{_g(y)}' for x, y in pts) + f'" fill="{acc}" fill-opacity="{st}"/>')
        sp = max(-90, min(90, spin))
        if sp != spin: gaps.append(f'spin {spin} became {sp}: the motion policy allows a rotation of at most 90 degrees')
        body = _grp(_grp(''.join(polys), _rot(-sp, cx, cy, 1.0, 0)), _op(0.8, 0)); mapping.append(f'burst of {cnt} rays -> turns in from {-sp} degrees with a fade')
    else:
        ang = _num(atom.get('angle'), -180, 180, 0, 'angle', gaps); a = math.radians(ang); d = (math.cos(a), math.sin(a)); nrm = (-d[1], d[0]); lines = []
        for k in range(cnt):
            off = (k + 0.5) / cnt * 720 - 360; px, py = cx + nrm[0] * off, cy + nrm[1] * off
            lines.append(f'<line x1="{_g(px - d[0] * 700)}" y1="{_g(py - d[1] * 700)}" x2="{_g(px + d[0] * 700)}" y2="{_g(py + d[1] * 700)}" stroke="{acc}" stroke-opacity="{st}" stroke-width="{_g(720 / cnt * thk)}"/>')
        body = _grp(_grp(''.join(lines), _tr((-40 * d[0], -40 * d[1]), 0.9, 0)), _op(0.8, 0)); mapping.append(f'{cnt} speed lines at {ang} degrees -> slide in 40 px with a fade')
    gaps.append("the atom's --s dial (turn or slide continuously) has no second clock here: only the entrance on p is drawn")
    return _gfinish(_gdoc(W, H, f'{kind} rays', body), mapping, gaps, dict(kind=kind, count=cnt))
def _cells(atom, child_svg=None):
    gaps, mapping = [], []
    cols = _num(atom.get('columns'), 2, 12, 6, 'columns', gaps); rows = _num(atom.get('rows'), 1, 8, 4, 'rows', gaps); mode = _enum(atom.get('mode'), ('pop', 'flip', 'fill'), 'pop', 'mode', gaps)
    gap = _num(atom.get('gap'), 0, 24, 4, 'gap', gaps); rad = _num(atom.get('radius'), 0, 40, 6, 'radius', gaps); fs = _num(atom.get('size'), 8, 80, 18, 'size', gaps); fs = max(fs, 12)
    chess = atom.get('chess', True) is not False; nums = atom.get('numbers') is True; acc = _hex(atom.get('accent'), '#38bdf8', 'accent', gaps); acc2 = _hex(atom.get('accent2'), '#94a3b8', 'accent2', gaps)
    cw = (600 - gap * (cols - 1)) / cols; ch = (400 - gap * (rows - 1)) / rows; c = min(cw, ch); W = int(cols * c + gap * (cols - 1)); H = int(rows * c + gap * (rows - 1)); bands = {}
    for r in range(rows):
        for q in range(cols):
            col = acc if (not chess or (q + r) % 2 == 0) else acc2; n = r * cols + q
            cell = f'<rect x="{_g(q * (c + gap))}" y="{_g(r * (c + gap))}" width="{_g(c)}" height="{_g(c)}" rx="{min(rad, c / 2)}" fill="{col}"' + ('' if (not chess or (q + r) % 2 == 0) else ' fill-opacity="0.35"') + '/>'
            if nums and n < 13: cell += f'<text x="{_g(q * (c + gap) + c / 2)}" y="{_g(r * (c + gap) + c / 2 + fs / 3)}" font-size="{fs}" font-weight="700" fill="#0f172a" text-anchor="middle" font-family="sans-serif">{2 ** n}</text>'
            bands.setdefault(min(q + r, 6), []).append(cell)
    body = ''.join(_grp(''.join(v), _op(0.4, 0.1 * b)) for b, v in sorted(bands.items())); mapping.append(f'{cols} by {rows} cells -> a diagonal wave of {len(bands)} fading bands')
    if mode != 'fill': gaps.append(f"mode {mode!r} pops or flips each cell (scale); the policy has no scale, so every mode is a fade in a diagonal wave")
    if len(bands) < cols + rows - 1: gaps.append(f'the wave has {len(bands)} steps: the policy allows 8 animations, so diagonals beyond the 7th fade with the 7th')
    return _gfinish(_gdoc(W, H, f'Grid of {cols} by {rows} cells', body), mapping, gaps, dict(cols=cols, rows=rows))
def _scatter(atom, child_svg=None):
    gaps, mapping = [], []
    items = atom.get('items') if isinstance(atom.get('items'), list) else ['Ticket', 'Label', 'Note']; cards = []
    for it in items:
        t = (it.get('title') if isinstance(it, dict) else it); x = it.get('text') if isinstance(it, dict) else ''
        if isinstance(t, str) and t.strip(): cards.append((t.strip()[:30], (x or '')[:50] if isinstance(x, str) else ''))
    if len(cards) > MAX_ANIMS: gaps.append(f'{len(cards)} cards: the policy allows {MAX_ANIMS} animations, one per card, so only the first {MAX_ANIMS} are drawn'); cards = cards[:MAX_ANIMS]
    if not cards: return _refuse('', 'no usable items')
    cwp = _num(atom.get('card_w'), 10, 50, 24, 'card_w', gaps); fs = max(_num(atom.get('size'), 8, 60, 18, 'size', gaps), 12); fill = _hex(atom.get('fill'), '#ffffff', 'fill', gaps); col = _hex(atom.get('color'), '#0f172a', 'color', gaps); acc = _hex(atom.get('accent'), '#38bdf8', 'accent', gaps)
    W, H = 640, 420; cw = W * cwp / 100; chh = cw * 0.62; body = [f'<rect width="{W}" height="{H}" fill="#f1f5f9"/>']; n = len(cards); per = 4
    for k, (t, x) in enumerate(cards):
        r, q = divmod(k, per); jx, jy = (_seeded(k, 'sx') - 0.5) * 30, (_seeded(k, 'sy') - 0.5) * 30
        px = 20 + q * ((W - 40 - cw) / max(1, min(per, n) - 1 if n > 1 else 1)) + jx if n > 1 else (W - cw) / 2; py = 30 + r * (H - 60 - chh) / max(1, (n - 1) // per) + jy if n > per else (H - chh) / 2 + jy
        px = min(max(px, 4), W - cw - 4); py = min(max(py, 4), H - chh - 4)
        card = f'<rect x="{_g(px)}" y="{_g(py)}" width="{_g(cw)}" height="{_g(chh)}" rx="6" fill="{fill}" stroke="#cbd5e1" stroke-width="1"/><rect x="{_g(px)}" y="{_g(py)}" width="{_g(cw)}" height="6" fill="{acc}"/><text x="{_g(px + 10)}" y="{_g(py + 6 + fs + 6)}" font-size="{fs}" font-weight="700" fill="{col}" font-family="sans-serif">{_html.escape(t)}</text>'
        if x: card += f'<text x="{_g(px + 10)}" y="{_g(py + 6 + 2 * fs + 12)}" font-size="{max(12, fs - 4)}" fill="{col}" font-family="sans-serif">{_html.escape(x)}</text>'
        off = _capoff((_seeded(k, 'ox') - 0.5) * 240, -80 - _seeded(k, 'oy') * 60, [], 'a card')
        body.append(_grp(card, _tr(off, 0.7, round(k * 0.08, 2))))
    mapping += [f'{n} cards -> each slides in up to {MAX_OFFSET:g} px to its resting spot, one after another']
    gaps += ['the atom flies cards in from outside the frame; the policy allows a move of at most 60 px, so the fly-in is much shorter', 'resting tilts need a static transform on each card, which the policy does not allow: the cards rest level', 'a fade as well as the slide would need a second animation per card (the limit is 8): slide only']
    return _gfinish(_gdoc(W, H, 'Pile of cards: ' + ', '.join(c[0] for c in cards[:4]), ''.join(body)), mapping, gaps, dict(cards=n))
def _shape_points(shape, n, cx, cy, R, seed):
    pts = []
    for k in range(n):
        t = k / n
        if shape == 'circle': pts.append(_angle_pt(cx, cy, R, 360 * t))
        elif shape == 'blob': pts.append(_angle_pt(cx, cy, R * (0.8 + 0.2 * math.sin(3 * 2 * math.pi * t + _seeded(seed, 'blob') * 6)), 360 * t))
        elif shape == 'heart': a = 2 * math.pi * t; pts.append((cx + R * 16 * math.sin(a) ** 3 / 17, cy - R * (13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a)) / 17))
        elif shape == 'star': a = 360 * t; r = R if int(t * 10) % 2 == 0 else R * 0.45; pts.append(_angle_pt(cx, cy, R * (0.45 + 0.55 * abs(math.cos(math.radians(a * 5 / 2)))), a - 90))
        else:
            poly = {'square': [(-1, -1), (1, -1), (1, 1), (-1, 1)], 'triangle': [(0, -1), (0.9, 0.8), (-0.9, 0.8)], 'diamond': [(0, -1), (1, 0), (0, 1), (-1, 0)], 'hexagon': [_angle_pt(0, 0, 1, 60 * j) for j in range(6)],
                    'plus': [(-0.3, -1), (0.3, -1), (0.3, -0.3), (1, -0.3), (1, 0.3), (0.3, 0.3), (0.3, 1), (-0.3, 1), (-0.3, 0.3), (-1, 0.3), (-1, -0.3), (-0.3, -0.3)], 'arrow': [(-1, -0.25), (0.2, -0.25), (0.2, -0.8), (1, 0), (0.2, 0.8), (0.2, 0.25), (-1, 0.25)]}[shape]
            per = t * len(poly); i0 = int(per) % len(poly); f = per - int(per); a, b = poly[i0], poly[(i0 + 1) % len(poly)]; pts.append((cx + R * (a[0] + (b[0] - a[0]) * f), cy + R * (a[1] + (b[1] - a[1]) * f)))
    return pts
def _particles(atom, child_svg=None):
    gaps, mapping = [], []
    if isinstance(atom.get('text'), str) and atom['text'].strip(): return _refuse('', "dot-matrix text needs the 5 by 7 dot font, which is not built yet; a shape converts")
    shape = _enum(atom.get('shape'), ('circle', 'square', 'triangle', 'diamond', 'hexagon', 'star', 'heart', 'blob', 'plus', 'arrow'), 'heart', 'shape', gaps); seed = _num(atom.get('seed'), 1, 2147483646, 7, 'seed', gaps)
    dot = _num(atom.get('dot'), 0.1, 10, 1.6, 'dot', gaps, False); col = _hex(atom.get('color'), '#38bdf8', 'color', gaps); col2 = atom.get('accent2'); col2 = _hex(col2, '#f472b6', 'accent2', gaps) if col2 is not None else None
    vary = atom.get('vary') is True; W = H = 600; pts = _shape_points(shape, 72, 300, 300, 230, seed); groups = [[] for _ in range(MAX_ANIMS)]
    for k, (x, y) in enumerate(pts):
        r = dot * 6 * ((0.6 + 0.8 * _seeded(k + seed, 'v')) if vary else 1); c = col2 if (col2 and k % 3 == 2) else col; groups[k % MAX_ANIMS].append(f'<circle cx="{_g(x)}" cy="{_g(y)}" r="{_g(r)}" fill="{c}"/>')
    body = ''
    for gi, dots in enumerate(groups):
        a = 2 * math.pi * _seeded(gi, f'pg{seed}'); off = (round(MAX_OFFSET * math.cos(a), 2), round(MAX_OFFSET * math.sin(a), 2)); body += _grp(''.join(dots), _tr(off, 0.9, round(gi * 0.05, 2)))
    mapping += [f'{len(pts)} dots in the {shape} outline, in {MAX_ANIMS} groups, each group slides in from {MAX_OFFSET:g} px away (seeded direction)']
    gaps += [f'each dot starts scattered in the atom; the policy allows {MAX_ANIMS} animations, so dots move in {MAX_ANIMS} groups and only {MAX_OFFSET:g} px', "the atom's scatter on the second dial (--s) and the glow are not drawn"]
    if atom.get('glow'): gaps.append('glow is dropped: the policy allows no filter on an animated picture')
    return _gfinish(_gdoc(W, H, f'Dots forming a {shape}', body), mapping, gaps, dict(shape=shape, dots=len(pts)))
def _lit(atom, child_svg=None):
    gaps, mapping = [], []
    blocks = atom.get('blocks')
    if isinstance(blocks, list) and len(blocks) > 1 and child_svg is None: return _refuse('', f'{len(blocks)} cards: placing several drawings side by side needs a static transform on each, which the policy does not allow; one card converts')
    svg, why = _child_svg(atom, child_svg)
    if why: return _refuse('', why)
    w = _wrap(svg, None)
    if isinstance(w[0], type(None)): return _refuse(svg, w[1])
    ghost = _num(atom.get('ghost'), 0, 1, 0.3, 'ghost', gaps, False); head, ttl, body, W, H = w
    anim = f'<animate attributeName="opacity" from="{ghost:g}" to="1" dur="0.9s" begin="0s" repeatCount="1" fill="freeze"/>'
    mapping.append(f'ghost {ghost:g} -> the card lights from {ghost:g} to full opacity over 0.9 s')
    gaps += ["the travelling border highlight and the one-after-another lighting of several cards are not drawn: one card, one fade", "the step dial (--s) that lights each card in turn has no second clock here"]
    return _gfinish(f'{head}{ttl}{_grp(body, anim)}</svg>', mapping, gaps, dict(ghost=ghost))
def _arcs(atom, child_svg=None):
    gaps, mapping = [], []
    arcs = atom.get('arcs') if isinstance(atom.get('arcs'), list) else [{'color': '#38bdf8', 'r': 36, 'from': 200, 'sweep': 240, 'width': 10}, {'color': '#a78bfa', 'r': 24, 'from': 20, 'sweep': 240, 'width': 10}]
    arcs = [a for a in arcs if isinstance(a, dict)][:4]
    if not arcs: return _refuse('', 'no usable arcs')
    body = ''; W = H = 400; S = 4.0
    for k, a in enumerate(arcs):
        col = _hex(a.get('color'), '#38bdf8', f'arcs[{k}].color', gaps); r = _num(a.get('r'), 8, 48, 36, f'arcs[{k}].r', gaps); frm = _num(a.get('from'), 0, 359, 0, f'arcs[{k}].from', gaps); sw = _num(a.get('sweep'), 20, 340, 240, f'arcs[{k}].sweep', gaps)
        wd = _num(a.get('width'), 3, 24, 8, f'arcs[{k}].width', gaps); dx = _num(a.get('dx'), -30, 30, 0, f'arcs[{k}].dx', gaps); dy = _num(a.get('dy'), -30, 30, 0, f'arcs[{k}].dy', gaps); spin = _num(a.get('spin'), -720, 720, 90, f'arcs[{k}].spin', gaps)
        cx, cy = (50 + dx) * S, (50 + dy) * S; R = r * S; p0 = _angle_pt(cx, cy, R, frm); p1 = _angle_pt(cx, cy, R, frm + sw); big = 1 if sw > 180 else 0
        sp = max(-90, min(90, spin))
        if sp != spin: gaps.append(f'arcs[{k}].spin {spin} became {sp}: the policy allows a rotation of at most 90 degrees')
        if a.get('color2'): gaps.append(f'arcs[{k}].color2 (a gradient along the arc) is drawn as the single colour {col}')
        if a.get('blur'): gaps.append(f'arcs[{k}].blur is dropped: no filter on an animated picture')
        path = f'<path d="M {_g(p0[0])},{_g(p0[1])} A {_g(R)},{_g(R)} 0 {big} 1 {_g(p1[0])},{_g(p1[1])}" fill="none" stroke="{col}" stroke-width="{_g(wd * S)}"/>'
        body += _grp(_grp(path, _rot(-sp, cx, cy, 0.7, round(k * 0.1, 2))), _op(0.7, round(k * 0.1, 2)))
    mapping.append(f'{len(arcs)} arcs -> each turns in from its spin (at most 90 degrees) with a fade, one after another')
    gaps.append('arc ends are flat: round caps need stroke-linecap, which the SVG policy does not allow')
    return _gfinish(_gdoc(W, H, atom.get('label') if isinstance(atom.get('label'), str) else 'Mark', body), mapping, gaps, dict(arcs=len(arcs)))
def _wrap_text(t, width_px, fs):
    per = max(8, int(width_px / (fs * 0.55))); words, lines, cur = str(t).split(), [], ''
    for w in words:
        if len(cur) + len(w) + (1 if cur else 0) <= per: cur = (cur + ' ' + w).strip()
        else: lines.append(cur); cur = w
    return (lines + [cur])[:5] if cur else lines[:5]
def _dialog(atom, child_svg=None):
    gaps, mapping = [], []
    title = atom.get('title')
    if not isinstance(title, str) or not title.strip(): return _refuse('', 'a dialog needs a title (it is also its accessible name)')
    title = title.strip()[:60]; body_t = atom.get('body') if isinstance(atom.get('body'), str) else ''; acts = [x for x in (atom.get('actions') or []) if isinstance(x, dict) and isinstance(x.get('label'), str)][:3]
    enter = _enum(atom.get('enter'), ('fade', 'rise', 'scale'), 'scale', 'enter', gaps); dim = _num(atom.get('dim'), 0.2, 0.8, 0.45, 'dim', gaps, False); scrim = _hex(atom.get('scrim'), '#000000', 'scrim', gaps); asp = _num(atom.get('aspect'), 0.8, 3, 1.6, 'aspect', gaps, False)
    W = 640; H = int(W / asp); dw, dh = W * 0.66, H * 0.62; dx0, dy0 = (W - dw) / 2, (H - dh) / 2; fs = 22; lines = _wrap_text(body_t, dw - 48, 16) if body_t else []
    d = f'<rect x="{_g(dx0)}" y="{_g(dy0)}" width="{_g(dw)}" height="{_g(dh)}" rx="16" fill="#ffffff"/><text x="{_g(dx0 + 24)}" y="{_g(dy0 + 24 + fs)}" font-size="{fs}" font-weight="700" fill="#0f172a" font-family="sans-serif">{_html.escape(title)}</text>'
    for i, ln in enumerate(lines): d += f'<text x="{_g(dx0 + 24)}" y="{_g(dy0 + 24 + fs + 14 + 20 * (i + 1))}" font-size="16" fill="#334155" font-family="sans-serif">{_html.escape(ln)}</text>'
    bx = dx0 + dw - 24
    for a in reversed(acts):
        lab = a['label'][:20]; bw = max(70, len(lab) * 9 + 28); bx -= bw; pri = a.get('primary') is True
        d += f'<rect x="{_g(bx)}" y="{_g(dy0 + dh - 24 - 36)}" width="{_g(bw)}" height="36" rx="8" fill="{"#4f46e5" if pri else "#e2e8f0"}"/><text x="{_g(bx + bw / 2)}" y="{_g(dy0 + dh - 24 - 12)}" font-size="16" font-weight="700" fill="{"#ffffff" if pri else "#0f172a"}" text-anchor="middle" font-family="sans-serif">{_html.escape(lab)}</text>'; bx -= 10
    rise = 24 if enter in ('rise', 'scale') else 0
    out = _grp(f'<rect width="{W}" height="{H}" fill="{scrim}" fill-opacity="{dim:g}"/>', _op(0.3, 0)) + _grp(_grp(d, _tr((0, rise), 0.7, 0.2)) if rise else d, _op(0.7, 0.2))
    mapping += [f'the scrim ({scrim}, strength {dim:g}) fades in first, then the dialog fades in and ' + (f'rises {rise} px' if rise else 'rests')]
    if enter == 'scale': gaps.append("enter 'scale' grows the dialog; the policy has no scale, so it rises 24 px as for 'rise'")
    gaps += ['the text is wrapped by an estimate (the picture cannot measure text): long bodies may wrap differently from the HTML', 'actions are drawn as buttons in a picture: not focusable, as in the atom']
    return _gfinish(_gdoc(W, H, f'Dialog: {title}', out), mapping, gaps, dict(enter=enter))
def _discs(atom, child_svg=None):
    gaps, mapping = [], []
    ds = atom.get('discs') if isinstance(atom.get('discs'), list) else [{'color': '#38bdf8', 'r': 30}, {'color': '#f472b6', 'r': 30}]; ds = [x for x in ds if isinstance(x, dict)][:4]
    if len(ds) < 2: return _refuse('', 'discs needs 2 to 4 discs')
    ov = _num(atom.get('overlap'), 2, 30, 12, 'overlap', gaps, False); asp = _num(atom.get('aspect'), 0.5, 3, 1.78, 'aspect', gaps, False); H = 360; W = int(H * asp); n = len(ds); body = ''
    for k, d in enumerate(ds):
        col = _hex(d.get('color'), '#38bdf8', f'discs[{k}].color', gaps); r = _num(d.get('r'), 8, 50, 30, f'discs[{k}].r', gaps, False) / 100 * H
        tx = W / 2 + (k - (n - 1) / 2) * ov / 100 * W; ax = W * (0.2 + 0.6 * k / (n - 1)); off = _capoff(ax - tx, 0, gaps, f'disc {k + 1}')
        body += _grp(_grp(f'<circle cx="{_g(tx)}" cy="{_g(H / 2)}" r="{_g(r)}" fill="{col}" fill-opacity="0.78"/>', _tr(off, 0.9, round(k * 0.1, 2))), _op(0.6, round(k * 0.1, 2)))
    mapping.append(f'{n} discs -> each slides together from up to {MAX_OFFSET:g} px apart with a fade, one after another')
    gaps.append('blend (multiply where discs meet) needs a blend mode: discs are drawn at 78 percent opacity instead'); gaps.append('the atom slides the discs from far apart on the step dial; the policy allows 60 px')
    return _gfinish(_gdoc(W, H, atom.get('label') if isinstance(atom.get('label'), str) and atom['label'].strip() else 'Overlapping discs', body), mapping, gaps, dict(discs=n))
def _dotgrid(atom, child_svg=None):
    gaps, mapping = [], []
    cols = _num(atom.get('cols'), 2, 12, 5, 'cols', gaps); rows = _num(atom.get('rows'), 2, 10, 4, 'rows', gaps); seed = _num(atom.get('seed'), 0, 999, 4, 'seed', gaps); dotp = _num(atom.get('dot'), 30, 95, 70, 'dot', gaps)
    col = _hex(atom.get('color'), '#f4ead0', 'color', gaps); acc = _hex(atom.get('accent'), '#e11d48', 'accent', gaps); asp = _num(atom.get('aspect'), 0.5, 3, 1.25, 'aspect', gaps, False)
    H = 400; W = int(H * asp); cw, ch = W / cols, H / rows; r = min(cw, ch) * dotp / 100 / 2; hops = atom.get('hops')
    if not (isinstance(hops, list) and 2 <= len(hops) <= 8 and all(isinstance(h, list) and len(h) == 2 and all(isinstance(v, int) for v in h) for h in hops)):
        if hops is not None: gaps.append('hops is not 2 to 8 [col, row] cells: the seeded path was used')
        hops = [[int(_seeded(k, f'hx{seed}') * cols), int(_seeded(k, f'hy{seed}') * rows)] for k in range(5)]
    hops = [[min(max(c, 0), cols - 1), min(max(rr, 0), rows - 1)] for c, rr in hops]; cen = lambda c, rr: ((c + 0.5) * cw, (rr + 0.5) * ch)
    dots = ''.join(f'<circle cx="{_g(cen(c, rr)[0])}" cy="{_g(cen(c, rr)[1])}" r="{_g(r)}" fill="{col}"/>' for rr in range(rows) for c in range(cols)); lx, ly = cen(*hops[-1]); fx, fy = cen(*hops[0]); off = _capoff(fx - lx, fy - ly, gaps, 'the token')
    body = f'<rect width="{W}" height="{H}" fill="#1f2937"/>' + _grp(dots, _op(0.6, 0)) + _grp(f'<circle cx="{_g(lx)}" cy="{_g(ly)}" r="{_g(r * 1.05)}" fill="{acc}"/>', _tr(off, 0.9, 0.3))
    mapping += [f'{cols} by {rows} dots fade in; the token ends on the last hop cell {tuple(hops[-1])} and slides in from the first']
    gaps += [f'the token hops along {len(hops)} cells on a parabola; only a straight slide that ends at rest is allowed, so the path is reduced to its first and last cell', 'the dark backing is the atom\'s stage colour, added because the picture has no stage behind it']
    return _gfinish(_gdoc(W, H, atom.get('label') if isinstance(atom.get('label'), str) and atom['label'].strip() else 'Grid of dots with a token', body), mapping, gaps, dict(hops=len(hops)))
CONVERTERS = {'motion_shatter': _shatter, 'motion_shake': _shake, 'motion_group': _group, 'motion_assemble': _assemble, 'motion_shape': _shape, 'motion_mark': _mark, 'motion_rays': _rays, 'motion_cells': _cells, 'motion_scatter': _scatter,
              'motion_particles': _particles, 'motion_lit': _lit, 'motion_arcs': _arcs, 'motion_dialog': _dialog, 'motion_discs': _discs, 'motion_dotgrid': _dotgrid}
REFUSALS = {}   # filled by atom_coverage.classify(); an unknown atom is refused with 'no converter yet'
_TIME = re.compile(r'\b(begin|dur)="([0-9.]+)s"')
def _stretch(res, duration):
    """Scale EVERY begin and dur of a converted picture so the whole sequence spans `duration` seconds (an explicit long opt-in: the motion policy is checked with max_seconds, never above LONG_MOTION_SECONDS). Same order, same proportions, same end state."""
    svg = res['svg']
    anims = re.findall(r'<animate(?:Transform)?\b[^>]*>', svg); natural = 0.0
    for a in anims:
        b = re.search(r'begin="([0-9.]+)s"', a); d = re.search(r'dur="([0-9.]+)s"', a); natural = max(natural, (float(b.group(1)) if b else 0.0) + float(d.group(1)))
    if natural <= 0: return dict(res, gaps=res['gaps'] + ['duration: there is no animation to stretch'])
    f = duration / natural
    for _ in range(3):
        out = _TIME.sub(lambda m: f'{m.group(1)}="{float(m.group(2)) * f:.3f}s"', svg); worst = 0.0
        for a in re.findall(r'<animate(?:Transform)?\b[^>]*>', out):
            b = re.search(r'begin="([0-9.]+)s"', a); d = re.search(r'dur="([0-9.]+)s"', a); worst = max(worst, (float(b.group(1)) if b else 0.0) + float(d.group(1)))
        if worst <= duration + 1e-9: break
        f *= 0.9995
    try: _MO.verify_motion(out, max_seconds=duration)
    except Exception as e: return dict(res, applied=False, svg='', gaps=res['gaps'] + [f'the stretched picture was refused by the motion policy ({str(e)[:110]})'])
    return dict(res, svg=out, bytes=len(out.encode()), mapping=res['mapping'] + [f'duration: the whole motion is stretched from {natural:g} s to {duration:g} s (every begin and dur x {f:.2f}; order and proportions unchanged)'],
                gaps=res['gaps'] + [f'long motion ({duration:g} s): WCAG 2.2.2 asks for a way to pause, stop or hide any movement that starts by itself and lasts more than 5 s; a picture in an Image has no such control, so the host page must provide one (or show the still picture), and reduced motion cannot be honoured inside an Image'], params=dict(res.get('params') or {}, duration=duration))
def _loop(res, seconds, rest=None):
    """Repeat the motion at its NORMAL speed for `seconds` (an explicit long opt-in, ceiling 15 s): every animation restarts at begin + k x cycle, where cycle = the motion's natural length + a rest. Speeds, order and stagger are unchanged; the picture is at rest between runs and after the last one."""
    svg = res['svg']; natural = 0.0
    for a in re.findall(r'<animate(?:Transform)?\b[^>]*>', svg):
        b = re.search(r'begin="([0-9.]+)s"', a); d = re.search(r'dur="([0-9.]+)s"', a); natural = max(natural, (float(b.group(1)) if b else 0.0) + float(d.group(1)))
    if natural <= 0: return dict(res, gaps=res['gaps'] + ['loop: there is no animation to repeat'])
    rest = max(0.6, 0.4 * natural) if rest is None else rest; cycle = natural + rest
    if seconds < natural: return dict(res, applied=False, svg='', gaps=res['gaps'] + [f'loop: one run takes {natural:g} s, which is longer than the {seconds:g} s asked for'])
    runs = int((seconds - natural + 1e-9) // cycle) + 1
    def restart(m):
        b0 = float(m.group(1)); return 'begin="' + ';'.join(f'{b0 + k * cycle:.3f}s' for k in range(runs)) + '"'
    out = re.sub(r'(?<=<animateTransform )([^>]*)|(?<=<animate )([^>]*)', lambda m: re.sub(r'begin="([0-9.]+)s"', restart, m.group(0)), svg)
    try: _MO.verify_motion(out, max_seconds=seconds)
    except Exception as e: return dict(res, applied=False, svg='', gaps=res['gaps'] + [f'the looped picture was refused by the motion policy ({str(e)[:110]})'])
    return dict(res, svg=out, bytes=len(out.encode()), mapping=res['mapping'] + [f'loop: the motion ({natural:g} s) runs {runs} times over {seconds:g} s with a {rest:g} s rest between runs (each animation restarts at its own begin + k x {cycle:.2f} s)'],
                gaps=res['gaps'] + [f'loop ({seconds:g} s): WCAG 2.2.2 asks for a way to pause, stop or hide movement that starts by itself and lasts more than 5 s; a picture in an Image has no such control, so the host page must provide one (or show the still picture); the loop is finite (the policy admits no indefinite repeat) and ends at rest'], params=dict(res.get('params') or {}, loop=seconds, runs=runs))
def convert(atom, child_svg=None, duration=None, loop=None):
    t = atom.get('type') if isinstance(atom, dict) else None
    if loop is not None:
        if duration is not None: return _refuse('', 'give duration (slow down) or loop (repeat), not both')
        if isinstance(loop, bool) or not isinstance(loop, (int, float)) or not (0.2 <= loop <= _MO.LONG_MOTION_SECONDS): return _refuse('', f'loop must be a number of seconds from 0.2 to {_MO.LONG_MOTION_SECONDS:g}')
        res = convert(atom, child_svg)
        return _loop(res, float(loop)) if res['applied'] else res
    if duration is not None:
        if isinstance(duration, bool) or not isinstance(duration, (int, float)) or not (0.2 <= duration <= _MO.LONG_MOTION_SECONDS): return _refuse('', f'duration must be a number of seconds from 0.2 to {_MO.LONG_MOTION_SECONDS:g}')
        res = convert(atom, child_svg)
        return _stretch(res, float(duration)) if res['applied'] else res
    if t in CONVERTERS: return CONVERTERS[t](atom, child_svg)
    return _refuse(child_svg or '', REFUSALS.get(t) or f'atom type {t!r} has no converter yet (converters: ' + ', '.join(sorted(CONVERTERS)) + ')')
