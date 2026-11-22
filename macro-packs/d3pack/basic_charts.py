"""bar_chart and line_chart: the first two macros of the pack (formerly the chart-macro demo), re-built on the pack's helpers so they pass the same output policy.
Inputs: labels (list of text), values (list of numbers), unit, title, x_label. Returns {'chart': Result}. Not an atom contract (the atoms have no plain bar or line chart); own design."""
import math
from .common import *
def nice_ticks(vmax, n=5):
    """Axis maximum and step so ticks are 1, 2 or 5 times a power of ten."""
    if not vmax or vmax <= 0: return 1.0, [0.0, 1.0]
    raw = vmax / n; mag = 10 ** math.floor(math.log10(raw)); f = raw / mag
    step = (1 if f <= 1 else 2 if f <= 2 else 5 if f <= 5 else 10) * mag; top = math.ceil(vmax / step - 1e-12) * step
    return step, [round(i * step, 10) for i in range(int(round(top / step)) + 1)]
def _clean(labels, values, kind):
    if not isinstance(labels, list) or not isinstance(values, list) or not labels or len(labels) != len(values): raise ValueError('labels and values must be non-empty lists of the same length')
    notes = []; L = []; V = []
    for i, (l, v) in enumerate(zip(labels[:60], values[:60]), 1):
        x = finite(v)
        if x is None or x < 0: notes.append(f'Point {i} was left out (not a number of 0 or more).'); continue
        L.append(clean_text(l, 16, f'Point {i}')); V.append(x)
    if len(labels) > 60: notes.append(f'{len(labels) - 60} points beyond the 60th were not drawn.')
    if len(V) < (2 if kind == 'line' else 1): raise ValueError('not enough usable points')
    if max(V) <= 0: raise ValueError('at least one value must be above 0')
    return L, V, notes
def _frame(vmax):
    L, R, T, B = 78, 28, 36, 70; return L, R, T, B, W - L - R, H - T - B, *nice_ticks(vmax)
def _grid(ticks, top, L, R, T, ph, u):
    out = ''
    for t in ticks:
        y = T + ph - ph * t / top
        out += f'<line x1="{L}" y1="{y:.2f}" x2="{W - R}" y2="{y:.2f}" stroke="#e3e6f3" stroke-width="2"/>' + label(L - 10, y + 6, fmt(t), 16, 'end', MUTED)
    return out
def bar_chart(labels, values, unit='', title='', x_label='', version=1):
    L_, V, notes = _clean(labels, values, 'bar'); u = clean_text(unit, 12, '') or ''; ttl = clean_text(title, 80, '') or ''; n = len(V)
    L, R, T, B, pw, ph, step, ticks = _frame(max(V)); top = ticks[-1]; slot = pw / n; bw = slot * 0.62; body = _grid(ticks, top, L, R, T, ph, u)
    for i, (l, v) in enumerate(zip(L_, V)):
        h = ph * v / top; x = L + i * slot + (slot - bw) / 2; y = T + ph - h
        body += f'<rect x="{x:.2f}" y="{y:.2f}" width="{bw:.2f}" height="{h:.2f}" rx="6" fill="{PAL[0]}"/>'
        if n <= 14: body += label(x + bw / 2, y - 8, fmt(v), 15, 'middle', INK, 700)
        if n <= 20 or i % math.ceil(n / 20) == 0: body += label(x + bw / 2, H - B + 28, l[:10], 14, 'middle', MUTED)
    hi = max(range(n), key=V.__getitem__); lo = min(range(n), key=V.__getitem__)
    tab = '; '.join(f'{l} {fmt(v)}{(" " + u) if u else ""}' for l, v in zip(L_, V))
    summary = f'{n} bars; highest {L_[hi]} ({fmt(V[hi])}{(" " + u) if u else ""}), lowest {L_[lo]} ({fmt(V[lo])}{(" " + u) if u else ""}).'
    return {'chart': finish('bar_chart', ttl, svg(body, 'Bar chart'), summary, tab, notes, u), '_default': 'chart'}
def line_chart(labels, values, unit='', title='', x_label='', version=1):
    L_, V, notes = _clean(labels, values, 'line'); u = clean_text(unit, 12, '') or ''; ttl = clean_text(title, 80, '') or ''; n = len(V)
    L, R, T, B, pw, ph, step, ticks = _frame(max(V)); top = ticks[-1]; body = _grid(ticks, top, L, R, T, ph, u)
    px = lambda i: L + (pw * i / (n - 1) if n > 1 else pw / 2); py = lambda v: T + ph - ph * v / top
    path = 'M' + ' L'.join(f'{px(i):.2f},{py(v):.2f}' for i, v in enumerate(V)); area = path + f' L{px(n - 1):.2f},{py(0):.2f} L{px(0):.2f},{py(0):.2f}Z'
    body += f'<path d="{area}" fill="{PAL[0]}" fill-opacity=".12"/><path d="{path}" fill="none" stroke="{PAL[0]}" stroke-width="4" stroke-linejoin="round"/>'
    step_l = max(1, math.ceil(n / 12))
    for i, (l, v) in enumerate(zip(L_, V)):
        if n <= 40: body += f'<circle cx="{px(i):.2f}" cy="{py(v):.2f}" r="{5 if n <= 20 else 3}" fill="#ffffff" stroke="{PAL[0]}" stroke-width="3"/>'
        if i % step_l == 0 or i == n - 1: body += label(px(i), H - B + 28, l[-5:] if len(l) > 5 and l[4:5] == '-' else l[:8], 14, 'middle', MUTED)
    hi = max(range(n), key=V.__getitem__); lo = min(range(n), key=V.__getitem__)
    tab = '; '.join(f'{l} {fmt(v)}{(" " + u) if u else ""}' for l, v in zip(L_, V))
    summary = f'{n} points from {L_[0]} to {L_[-1]}; highest {L_[hi]} ({fmt(V[hi])}{(" " + u) if u else ""}), lowest {L_[lo]} ({fmt(V[lo])}{(" " + u) if u else ""}); last value {fmt(V[-1])}{(" " + u) if u else ""}.'
    return {'chart': finish('line_chart', ttl, svg(body, 'Line chart'), summary, tab, notes, u), '_default': 'chart'}
