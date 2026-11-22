"""kpi_strip factory (19 Nov 2026): a list of KPI rows as ONE verified drawing, deterministic, no model. Each row: a status bar, the KPI name, its target, the status in WORDS, a sparkline of the recent history whose end dot lands exactly on the current value, the value, and the margin to the target.
Built on the gauge_modern rules: palettes and status words come from gauge_modern's THEMES (checked there for contrast), every text is 24 canvas px or more (12 px on a phone card), status is never colour alone, the margin is written in points only when the unit is a percent and carries a triangle, shapes come from the base policy
(rect, circle, path with fill or stroke, polygon, text; no linecap, no gradients). Direction: higher_is_better=True (uptime) or False (response time, backlog): the status is judged against the target in that direction, healthy at the target or better, warning within 10 percent of it, else breached.
Inputs: kpis = a list of up to 5 dicts {name, value, target, unit, history (up to 24 numbers), higher_is_better}; title; theme. Returns {'kpi_strip': Result, '_default': 'kpi_strip'}. Not registered in the pack's PACK table."""
import math
from .common import *
from .gauge_sla import _num, _note
from .gauge_modern import THEMES, _g, _w, _text, _cut, _delta_text, _finish
W_, ROW = 600, 108
HEAD = 52   # the title row, drawn only when a title is given
MAXK, MAXH = 5, 24
def _status2(v, thr, hib):
    if thr is None: return None
    if hib: return 'healthy' if v >= thr else 'warning' if v >= 0.9 * thr else 'breached'
    return 'healthy' if v <= thr else 'warning' if v <= 1.1 * thr else 'breached'
def _spark(hist, v, thr, x0, x1, y0, y1):
    """The sparkline path and the end point. The history is scaled to its own range (and the target's), padded 8 percent; the end point is the last history value, which is the current value."""
    pts = hist[-MAXH:] + ([] if hist and hist[-1] == v else [v]); lo = min(pts + ([thr] if thr is not None else [])); hi = max(pts + ([thr] if thr is not None else []))
    if hi - lo < 1e-9: lo, hi = lo - 1, hi + 1
    pad = (hi - lo) * 0.08; lo -= pad; hi += pad
    X = lambda i: x0 + (x1 - x0) * (i / max(1, len(pts) - 1)); Y = lambda q: y1 - (y1 - y0) * ((q - lo) / (hi - lo))
    d = 'M ' + ' L '.join(f'{_g(X(i))},{_g(Y(q))}' for i, q in enumerate(pts)); return d, (X(len(pts) - 1), Y(pts[-1])), (None if thr is None else Y(thr)), len(pts)
def kpi_strip(kpis=None, title='', theme='light'):
    notes = []; ttl = clean_text(title, 60, '') or ''
    if theme not in THEMES: notes.append(f'theme "{str(theme)[:12]}" is not light or dark, so light is used.'); theme = 'light'
    if not isinstance(kpis, (list, tuple)) or not kpis: return _note(ttl, 'There are no KPIs to draw.', notes)
    if len(kpis) > MAXK: notes.append(f'Only the first {MAXK} of {len(kpis)} KPIs are drawn.')
    P = THEMES[theme]; rows = []; body = []; summ_parts = []; tab_parts = []; used = 0; top = HEAD if ttl else 0
    if ttl: body.append(_text(24, 38, _cut(ttl, 34, notes, 'title'), 28, 'start', P['ink']))
    for k in list(kpis)[:MAXK]:
        if not isinstance(k, dict): notes.append('An entry that is not a KPI object was skipped.'); continue
        name = clean_text(k.get('name', ''), 40, '') or ''; v = _num(k.get('value'), None)
        if v is None: notes.append(f'KPI "{name[:16]}" has no numeric value, so it was skipped.'); continue
        thr = _num(k.get('target'), None) if k.get('target') is not None else None
        u = clean_text(k.get('unit', ''), 8, '') or ''
        if u and isinstance(k.get('unit'), str) and k['unit'][:1] == ' ': u = ' ' + u[:7]   # a unit written with a leading space (' min') keeps it, as in the gauge
        hib = k.get('higher_is_better', True) is not False
        hist = [x for x in (_num(h, None) for h in (k.get('history') or [])[-MAXH:]) if x is not None]
        st = _status2(v, thr, hib); word, fill, stxt, pillbg = P['status'][st]; y = top + used * ROW + 8; used += 1
        nm = _cut(name or 'KPI', 19, notes, 'name'); vtxt = f'{fmt(v)}{u}'; tgt = f'Target {fmt(thr)}{u}' if thr is not None else 'No target'
        body.append(f'<rect x="12" y="{y + 12}" width="8" height="{ROW - 24}" rx="4" fill="{fill}"/>')
        body += [_text(32, y + 38, nm, 24, 'start', P['ink']), _text(32, y + 68, _cut(tgt, 19, notes, 'target'), 24, 'start', P['ink2'], 400), _text(32, y + 96, word if st else '', 24, 'start', stxt)]
        sx0, sx1, sy0, sy1 = 292, 396, y + 20, y + ROW - 22
        d, (ex, ey), ty, n = _spark(hist, v, thr, sx0, sx1, sy0, sy1)
        if ty is not None: body.append(f'<rect x="{sx0}" y="{_g(ty - 1)}" width="{sx1 - sx0}" height="2" fill="{P["ink2"]}" fill-opacity="0.55"/>')   # the target, visible against the line
        if n >= 2: body.append(f'<path d="{d}" fill="none" stroke="{fill}" stroke-width="3"/>')
        body.append(f'<circle cx="{_g(ex)}" cy="{_g(ey)}" r="6" fill="{fill}"/>')
        if len(u.strip()) > 3 or len(vtxt) > 7:   # a long unit is set small (24) after a full-size number, so every row's number is the same size
            ut = u.strip(); uw = _w(ut, 24, 400) + 8
            body += [_text(W_ - 24, y + 52, ut, 24, 'end', P['ink2'], 400), _text(W_ - 24 - uw, y + 52, fmt(v), 40, 'end', P['ink'])]
        else: body.append(_text(W_ - 24, y + 52, vtxt, 40, 'end', P['ink']))
        if thr is not None:
            dt = _delta_text(v, thr, u if len(u.strip()) <= 3 else '', True); up = v >= thr   # a long unit is left out of the margin (the value line carries it), so the margin stays clear of the sparkline
            tw = _w(dt, 24); sx = W_ - 24 - tw - 22
            tri = f'{_g(sx + 7)},{y + (78 if up else 91)} {_g(sx + 14)},{y + (91 if up else 78)} {_g(sx)},{y + (91 if up else 78)}'
            body += [f'<polygon points="{tri}" fill="{stxt}"/>', _text(W_ - 24, y + 94, dt, 24, 'end', stxt)]
        if used < len(list(kpis)[:MAXK]): body.append(f'<rect x="12" y="{y + ROW - 1}" width="{W_ - 24}" height="1.5" fill="{P["track"]}" fill-opacity="0.7"/>')
        summ_parts.append(f'{name or "KPI"}: {vtxt}' + (f', {word.lower()}, target {fmt(thr)}{u}' if st else ''))
        tab_parts.append(f'{name or "KPI"} {vtxt}' + (f' target {fmt(thr)}{u} ({word.lower()}{"" if hib else ", lower is better"})' if st else ''))
    if not used: return _note(ttl, 'None of the KPIs had a numeric value.', notes)
    H_ = top + used * ROW + 16; aria = (f'{ttl}: ' if ttl else '') + '; '.join(summ_parts)
    if len(aria) > 190: aria = aria[:189].rstrip(' ;,') + '…'; notes.append('The picture\'s accessible name is shortened to fit the 200 character limit of a text node; the full reading is in the summary and the table.')
    bg = f'<rect width="{W_}" height="{H_}"' + (f' rx="{P["rx"]}"' if P['rx'] else '') + f' fill="{P["bg"]}"/>'
    drawing = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W_}" height="{H_}" viewBox="0 0 {W_} {H_}" role="img" aria-label="{esc(aria)}"><title>{esc(aria)}</title>' + bg + ''.join(body) + '</svg>'
    summ = (f'{ttl}: ' if ttl else '') + '; '.join(summ_parts) + '.'; tab = '; '.join(tab_parts)
    return {'kpi_strip': _finish('kpi_strip', ttl, drawing, summ, tab, notes, '', False), '_default': 'kpi_strip'}
