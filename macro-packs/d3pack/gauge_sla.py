"""gauge_sla macro: same contract as the gauge_sla atom (title, value, max_value, unit, label, min, steps [{from, to, color}] up to 8, threshold, version). A semi-circular gauge:
a track, an optional set of colour bands, a needle at the value, a tick at the threshold, the value in large type and a status line. Parametric: the whole drawing follows from a few numbers
(angle = -90 degrees + 180 degrees x (value - min) / (max - min), measured from 12 o'clock), so any value draws from the same layout, exactly, with no model.
Status follows the atom: it is judged only when a threshold is given (healthy at or above it, warning at or above 90 percent of it, else breached) and is always stated in WORDS next to the
colour, never by colour alone; the status text uses darker colours than the arcs so it stays readable on white. Colours in steps must be #rgb or #rrggbb (the pack's output policy has no
var(--token)); anything else is replaced by a pack colour and noted. Cells are read with finite semantics: a value that is not a number counts as 0 (noted), a value outside the scale is
drawn at the nearest end (noted). A scale with no width (max not above min) gives a note-only Result (the atom: a note replaces the chart). `version` above 1 draws as version 1 with a note.
Returns {'gauge': Result, '_default': 'gauge'}."""
import math
from .common import *
from .waterfall import note_result
CX, CY, R_OUT, R_IN, R_NEEDLE = 300.0, 290.0, 210.0, 156.0, 150.0
GW, GH = 600, 384
MAX_STEPS = 8
HEX = re.compile(r'#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})')
TRACK = '#e6e8f0'
STATUS = {'healthy': ('HEALTHY', '#10b981', '#047857'), 'warning': ('WARNING', '#38bdf8', '#0b5f87'), 'breached': ('BREACHED', '#ef4444', '#b91c1c')}
def _note(ttl, why, notes): notes.append(why); return {'gauge': note_result('gauge_sla', ttl, why + ' Nothing was drawn.', notes), '_default': 'gauge'}
def _num(x, default=None):
    if isinstance(x, bool): return default
    if isinstance(x, str):
        try: x = float(x.strip())
        except ValueError: return default
    return finite(x, -1e15, 1e15) if isinstance(x, (int, float)) else default
_min, _max = min, max   # the contract's field is called min, which shadows the builtin inside the macro
def _angle(frac): return -math.pi / 2 + math.pi * _min(1.0, _max(0.0, frac))
def _pt(r, a): return CX + r * math.sin(a), CY - r * math.cos(a)
def _status(val, thr):
    if thr is None: return None
    return 'healthy' if val >= thr else ('warning' if val >= thr * 0.9 else 'breached')
def _fs(base, f):   # a font size: the reference size times f, never under 12 px, written as an integer when it is one (so f = 1 gives the macro's original sizes)
    v = _max(12, base * f); return int(v) if v == int(v) else round(v, 2)
def _g(x): return ('%.2f' % x).rstrip('0').rstrip('.')   # 4 stays 4, 2.1 stays 2.1
def _pt_at(cx, cy, r, a): return cx + r * math.sin(a), cy - r * math.cos(a)
def parts_body(cx, cy, f, lo, hi, v, shown, thr, sinfo, bands, u, lab, ttl, notes, text='full'):
    """The gauge's elements for a centre (cx, cy) and a scale factor f (1 = the macro's own layout, outer radius 210). Single source of truth for the geometry: gauge_sla() calls it with f = 1 and the
    sketch vocabulary calls it scaled. text: 'full' (title, scale ends, value and status lines), 'value' (the value only: for small gauges where the other text would fall under 12 px) or 'none'.
    Text sizes never go below the output policy's 12 px; a caller that draws at a size where that would overlap should use text='value'."""
    r_out, r_in, r_nd = R_OUT * f, R_IN * f, R_NEEDLE * f; frac = (v - lo) / (hi - lo); body = ''
    if ttl and text == 'full': body += label_(cx, cy - 246 * f, ttl, _fs(24, f), 'middle', INK, 700)
    if bands:
        for a2, b2, col in bands: body += f'<path d="{arc_path(cx, cy, r_in, r_out, _angle((a2 - lo) / (hi - lo)), _angle((b2 - lo) / (hi - lo)))}" fill="{col}"/>'
    else:
        body += f'<path d="{arc_path(cx, cy, r_in, r_out, -math.pi / 2, math.pi / 2)}" fill="{TRACK}"/>'
        if frac > 0: body += f'<path d="{arc_path(cx, cy, r_in, r_out, -math.pi / 2, _angle(frac))}" fill="{sinfo[1] if sinfo else PAL[0]}"/>'
    if thr is not None and lo <= thr <= hi:
        a = _angle((thr - lo) / (hi - lo)); x0, y0 = _pt_at(cx, cy, r_in - 10 * f, a); x1, y1 = _pt_at(cx, cy, r_out + 10 * f, a)
        body += f'<line x1="{x0:.2f}" y1="{y0:.2f}" x2="{x1:.2f}" y2="{y1:.2f}" stroke="{INK}" stroke-width="{_g(4 * f)}"/>'
    elif thr is not None: notes.append(f'threshold {fmt(thr)} is outside the scale, so its tick is not drawn.')
    nx, ny = _pt_at(cx, cy, r_nd, _angle(frac))
    body += f'<line x1="{cx:.2f}" y1="{cy:.2f}" x2="{nx:.2f}" y2="{ny:.2f}" stroke="{INK}" stroke-width="{_g(6 * f)}"/><circle cx="{cx:.2f}" cy="{cy:.2f}" r="{_g(14 * f)}" fill="{INK}"/>'
    if text == 'full':
        body += label_(cx - (r_out + r_in) / 2, cy + 24 * f, fmt(lo), _fs(14, f), 'middle', MUTED) + label_(cx + (r_out + r_in) / 2, cy + 24 * f, fmt(hi), _fs(14, f), 'middle', MUTED)
    if text in ('full', 'value'):
        vt = fmt(shown) + u; body += label_(cx, cy + 52 * f, vt, _fs(44 * _min(1.0, 13 / len(vt)), f), 'middle', INK, 700)   # more than 13 characters shrinks so it stays inside the picture
    head = sinfo[0] if sinfo else ''; tgt = f'TARGET {fmt(thr)}{u}' if thr is not None else ''; labu = lab.upper()
    room = 74 - len(' · '.join(x for x in (head, tgt) if x)) - (3 if (head or tgt) else 0)   # 74 characters is what fits at the 12 px floor; past that the label is cut
    if text == 'full' and len(labu) > room:
        if room >= 4: labu = labu[:room - 1] + '\u2026'; notes.append('The label is shortened to fit the status line.')
        else: labu = ''; notes.append('The label is left out: the status line has no room for it.')
    line = ' · '.join(x for x in (head, labu, tgt) if x)
    if line and text == 'full': body += label_(cx, cy + 82 * f, line, _fs(16 * _min(1.0, 52 / len(line)), f), 'middle', sinfo[2] if sinfo else MUTED, 700)   # likewise past 52 characters
    return body
def gauge_sla(value=0, max_value=100, unit='', label='', title='', min=0, steps=None, threshold=None, version=1):
    notes = []; ttl = clean_text(title, 60, '') or ''; u = clean_text(unit, 8, '') or ''
    if u and isinstance(unit, str) and unit[:1] == ' ': u = ' ' + u[:7]   # the atom keeps whatever space the payload gave the unit (' hPa'); clean_text strips it
    lab = clean_text(label, 40, '') or ''
    lo = _num(min, 0.0); hi = _num(max_value, None)
    if lo is None: lo = 0.0; notes.append('min is not a number, so 0 is used.')
    if hi is None: hi = 100.0; notes.append('max_value is not a number, so 100 is used.')
    if not hi > lo: return _note(ttl, 'The scale has no width (max_value is not above min).', notes)
    v = _num(value, None)
    if v is None: v = 0.0; notes.append('value is not a number, so 0 is drawn.')
    shown = v
    if v < lo: v = lo; notes.append(f'value {fmt(shown)} is below the scale and is drawn at {fmt(lo)}.')
    elif v > hi: v = hi; notes.append(f'value {fmt(shown)} is above the scale and is drawn at {fmt(hi)}.')
    thr = _num(threshold, None)
    if threshold is not None and (thr is None or thr <= 0): notes.append('threshold is not a positive number, so no status is judged.'); thr = None
    ver = _num(version, 1)
    if ver is not None and ver > 1: notes.append(f'version {int(ver)} draws as version 1.')
    frac = (v - lo) / (hi - lo); sinfo = STATUS.get(_status(shown, thr))   # the status is judged on the value as given (as the atom does); the needle is drawn at the nearest end of the scale
    bands = []
    if steps is not None:
        if not isinstance(steps, list): notes.append('steps is not a list, so no bands are drawn.')
        else:
            if len(steps) > MAX_STEPS: notes.append(f'Only the first {MAX_STEPS} of {len(steps)} steps are drawn.')
            for i, s in enumerate(steps[:MAX_STEPS]):
                a, b = (_num(s.get('from')), _num(s.get('to'))) if isinstance(s, dict) else (None, None)
                if a is None or b is None or not b > a: notes.append(f'Step {i + 1} has no usable from and to, so it is left out.'); continue
                a2, b2 = _max(a, lo), _min(b, hi)
                if not b2 > a2: notes.append(f'Step {i + 1} lies outside the scale, so it is left out.'); continue
                if (a2, b2) != (a, b): notes.append(f'Step {i + 1} is cut to the scale ({fmt(a2)} to {fmt(b2)}).')
                col = s.get('color') if isinstance(s.get('color'), str) else None
                if col is None or not HEX.fullmatch(col.strip()):
                    if col is not None: notes.append(f'Step {i + 1} colour {plain(col)[:20]!r} is not a hex colour, so a pack colour is used.')
                    col = PAL[len(bands) % len(PAL)]
                else: col = col.strip()
                bands.append((a2, b2, col))
    body = parts_body(CX, CY, 1.0, lo, hi, v, shown, thr, sinfo, bands, u, lab, ttl, notes)
    summ = (f'{ttl}: ' if ttl else '') + f'{fmt(shown)}{u} on a scale of {fmt(lo)} to {fmt(hi)}.' + (f' Status {sinfo[0].lower()} against a target of {fmt(thr)}{u}.' if sinfo else ' No target was given, so no status is judged.') + (f' {lab}.' if lab else '')
    tab = f'Value {fmt(shown)}{u}; scale {fmt(lo)} to {fmt(hi)}' + (f'; target {fmt(thr)}{u} ({sinfo[0].lower()})' if sinfo else '') + ''.join(f'; band {fmt(a)} to {fmt(b)} colour {c}' for a, b, c in bands)
    return {'gauge': finish('gauge_sla', ttl, svg(body, 'Gauge', GW, GH), summ, tab, notes, u), '_default': 'gauge'}
def label_(x, y, s, size, anchor, fill, weight=400): return label(x, y, s, size, anchor, fill, weight)
