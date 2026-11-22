"""stat_card factory (19 Nov 2026): ONE statistic as one verified drawing, deterministic, no model. A big number, a direction line (an arrow and the change since the last release, in words), a sparkline of the last releases whose end dot lands on the current value, the period labels, and a source line.
Direction is the point, not health: the palette is NEUTRAL (gauge_modern's neutral indigo), no healthy or breached colours, no status words, because up is not good or bad for a statistic. A threshold, if wanted, is a different card.
Motion (motion=True, opt-in, only for a NEW RELEASE, never for a re-send): the end dot travels along the final segment of the line from the previous release to the new one, the arrow slides in the direction of the change (up arrows rise, down arrows fall) and the number fades in; every animation ends on the identity, so the still picture is the end frame (verify_motion). Text cannot be animated, so the number does not count up.
Inputs: title, value, previous (the previous release, default: the second last of the series), series (up to 24 numbers, ends at the value; default [previous, value]), unit, period ('month'), labels (first and last period labels), source (default says the figures are illustrative), theme, motion. Returns {'stat': Result, '_default': 'stat'}. Not registered in the pack's PACK table."""
from .common import *
from .gauge_sla import _num, _note
from .gauge_modern import THEMES, _g, _w, _text, _cut, _finish, _a_op, _a_tr
W_, H_ = 600, 392
MAXN = 24
def _pts(series, v):
    s = [x for x in (_num(q, None) for q in (series or [])[-MAXN:]) if x is not None]
    if not s or s[-1] != v: s.append(v)
    return s[-MAXN:]
def stat_card(title='', value=None, previous=None, series=None, unit='', period='month', labels=None, source='Illustrative figures, not real data', theme='light', motion=False):
    notes = []; ttl = clean_text(title, 60, '') or ''; u = clean_text(unit, 8, '') or ''; per = clean_text(period, 12, 'month') or 'month'
    if u and isinstance(unit, str) and unit[:1] == ' ': u = ' ' + u[:7]   # a unit written with a leading space (' ms') keeps it
    src = clean_text(source, 60, '') or ''
    if theme not in THEMES: notes.append(f'theme "{str(theme)[:12]}" is not light or dark, so light is used.'); theme = 'light'
    v = _num(value, None)
    if v is None: return _note(ttl, 'The statistic needs a numeric value.', notes)
    pts = _pts(series, v); prev = _num(previous, None) if previous is not None else (pts[-2] if len(pts) >= 2 else None)
    if previous is not None and prev is None: notes.append('previous is not a number, so the one before the value in the series is used.'); prev = pts[-2] if len(pts) >= 2 else None
    if prev is not None and (len(pts) < 2 or pts[-2] != prev): pts = pts[:-1] + [prev, v] if len(pts) >= 1 and pts[-1] == v else pts + [prev, v]; pts = pts[-MAXN:]
    P = THEMES[theme]; _w0, fill, ntxt, _pb = P['status'][None]; motion = motion is True
    d = None if prev is None else v - prev; kind = 'unchanged' if d is None or d == 0 else ('up' if d > 0 else 'down')
    unit_w = ' points' if u.strip() == '%' else (u if u else '')
    chg = {'up': f'up {fmt(abs(d))}{unit_w} from last {per}', 'down': f'down {fmt(abs(d))}{unit_w} from last {per}', 'unchanged': f'unchanged from last {per}'}[kind] if prev is not None else f'first {per} shown'
    vtxt = f'{fmt(v)}{u}'; size = 96 if len(vtxt) <= 5 else max(40, int(96 * 5 / len(vtxt)))
    x0, x1, y0, y1 = 32, 568, 214, 292; lo, hi = min(pts), max(pts)
    if hi - lo < 1e-9: lo, hi = lo - 1, hi + 1
    pad = (hi - lo) * 0.1; lo -= pad; hi += pad
    X = lambda i: x0 + (x1 - x0) * (i / max(1, len(pts) - 1)); Y = lambda q: y1 - (y1 - y0) * ((q - lo) / (hi - lo))
    path = 'M ' + ' L '.join(f'{_g(X(i))},{_g(Y(q))}' for i, q in enumerate(pts)); ex, ey = X(len(pts) - 1), Y(pts[-1])
    body = [f'<rect width="{W_}" height="{H_}"' + (f' rx="{P["rx"]}"' if P['rx'] else '') + f' fill="{P["bg"]}"/>']
    body.append(_text(32, 44, _cut(ttl, 30, notes, 'title'), 28, 'start', P['ink'])) if ttl else None
    vt = _text(32, 150, vtxt, size, 'start', P['ink']); body.append('<g>' + vt + _a_op(0.3, 0.5) + '</g>' if motion else vt)
    if prev is not None:
        ax = 32; ay = 192   # the arrow sits at the start of the direction line, so it never depends on the width of the big number or the font
        if kind == 'up': tri = f'{_g(ax + 11)},{ay - 26} {_g(ax + 22)},{ay} {_g(ax)},{ay}'
        elif kind == 'down': tri = f'{_g(ax + 11)},{ay} {_g(ax + 22)},{ay - 26} {_g(ax)},{ay - 26}'
        else: tri = f'{_g(ax)},{ay - 16} {_g(ax + 22)},{ay - 16} {_g(ax + 22)},{ay - 10} {_g(ax)},{ay - 10}'   # unchanged: a flat bar, not an arrow
        arrow = f'<polygon points="{tri}" fill="{ntxt}"/>'
        if motion and kind != 'unchanged': arrow = '<g>' + arrow + _a_tr(0, 24 if kind == 'up' else -24, 0.2, 0.6) + _a_op(0.2, 0.6) + '</g>'
        body.append(arrow)
    body.append(_text(66 if prev is not None else 32, 188, _cut(chg, 38 if prev is not None else 44, notes, 'change'), 24, 'start', ntxt))
    body.append(f'<path d="{path}" fill="none" stroke="{fill}" stroke-width="3"/>')
    dot = f'<circle cx="{_g(ex)}" cy="{_g(ey)}" r="7" fill="{fill}"/>'
    if motion and len(pts) >= 2:
        px, py = X(len(pts) - 2), Y(pts[-2])
        if max(abs(px - ex), abs(py - ey)) <= 60: body.append('<g>' + dot + _a_tr(_g(px - ex), _g(py - ey), 0.1, 0.9) + '</g>')   # the dot travels along the final segment, from the previous release to the new one
        else: body.append('<g>' + dot + _a_op(0.1, 0.6) + '</g>'); notes.append('The previous release is too far from the new one for the dot to travel (the motion policy allows 60 px), so the dot fades in instead.')
    else: body.append(dot)
    lab = [clean_text(x, 16, '') for x in (labels or [])[:2]] if isinstance(labels, (list, tuple)) else []
    if len(lab) == 2 and all(lab): body += [_text(32, 330, lab[0], 24, 'start', P['ink2'], 400), _text(568, 330, lab[1], 24, 'end', P['ink2'], 400)]
    if src: body.append(_text(32, 372, _cut(src, 44, notes, 'source'), 24, 'start', P['ink2'], 400))
    aria = (f'{ttl}: ' if ttl else '') + f'{vtxt}, {chg}'
    drawing = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W_}" height="{H_}" viewBox="0 0 {W_} {H_}" role="img" aria-label="{esc(aria)}"><title>{esc(aria)}</title>' + ''.join(body) + '</svg>'
    if motion:
        from .motion import verify_motion
        verify_motion(drawing)
    summ = (f'{ttl}: ' if ttl else '') + f'{vtxt}, {chg}.' + (f' {src}.' if src else ''); tab = f'Value {vtxt}; {chg}' + (f'; previous {fmt(prev)}{u}' if prev is not None else '') + f'; {len(pts)} points' + (f'; {src}' if src else '')
    res = _finish('stat_card', ttl, drawing, summ, tab, notes, u, motion)
    if motion: res['motion'] = 'new release: the end dot travels along the last segment, the arrow slides, the number fades in, once, ends on the still picture'
    return {'stat': res, '_default': 'stat'}
