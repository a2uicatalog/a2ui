"""gauge_modern factory (19 Nov 2026): the modern gauge designs that came out of three rounds of model drawing, blind review and measured checks, made parametric so ANY value draws exactly, with no model.
Two designs (design='semicircle' or 'bar') in two themes (theme='light' or 'dark'). Inputs: value, max_value, min, threshold (the target; higher is better), unit, label, title.
Status follows the gauge_sla atom: judged only when a threshold is given (healthy at or above it, warning at or above 90 percent of it, else breached), always stated in words in a pill, never by colour alone.
What the reviews fixed, now rules of the code: (1) the visible end of the fill, a rounded cap included, lands exactly on the value (the arc is shortened by the cap's angle; a value too small for a cap draws a flat-ended sector);
(2) the fill is at least 3 to 1 against the card and against the empty track, and every text colour is at least 4.5 to 1 against what it sits on (palettes below are checked in the tests); (3) no text is under 24 px on the 600 px canvas
(12 px on a phone card), except nothing: every text is 24 or more; (4) the margin to the target is written in points only when the unit is a percent, and carries an up or down triangle; (5) one scale form (the two ends only);
(6) the target label is placed by a clearance search, never touching the pill, the arc or the marker. Shapes only from the base policy: filled paths and circles for rounded ends (no stroke-linecap), rect rx for corners, fill-opacity for soft layers.
Returns {'gauge': Result, '_default': 'gauge'} like gauge_sla. Not yet registered in the pack's PACK table."""
import math
from .common import *
from .gauge_sla import _num, _status, _note
W_, H_ = 600, 384
CX, CY, RO, RI = 300.0, 286.0, 186.0, 148.0
RM, CAP = (RO + RI) / 2, (RO - RI) / 2
CAP_FRAC = (CAP / RM) / math.pi              # the rounded cap's tip lies this fraction of the half circle past the end line
TRACK_Y = 246                                 # the bar's track top
THEMES = {
    'light': {'bg': '#ffffff', 'rx': 0, 'ink': '#0f172a', 'ink2': '#334155', 'track': '#e2e8f0', 'hi': '#ffffff', 'outline': '#ffffff', 'shadow': '#0f172a', 'shadow_a': '0.10',
              'status': {'healthy': ('HEALTHY', '#059669', '#047857', '#e2f7f0'), 'warning': ('WARNING', '#b45309', '#92400e', '#fef3c7'), 'breached': ('BREACHED', '#dc2626', '#b91c1c', '#fee2e2'),
                         None: ('', '#4f46e5', '#4338ca', '#e0e7ff')}},
    'dark': {'bg': '#0f172a', 'rx': 28, 'ink': '#f8fafc', 'ink2': '#e2e8f0', 'track': '#3d4c66', 'hi': '#ffffff', 'outline': '#0f172a', 'shadow': '#000000', 'shadow_a': '0.22',
             'status': {'healthy': ('HEALTHY', '#34d399', '#6ee7b7', '#15353c'), 'warning': ('WARNING', '#fbbf24', '#fcd34d', '#3b2a0a'), 'breached': ('BREACHED', '#f87171', '#fca5a5', '#4a1d1d'),
                        None: ('', '#a5b4fc', '#c7d2fe', '#1e2a4a')}},
}
RICH = {'light': {'healthy': ('#059669', '#047857'), 'warning': ('#c2620a', '#b45309'), 'breached': ('#dc2626', '#b91c1c'), None: ('#4f46e5', '#4338ca')},
        'dark': {'healthy': ('#6ee7b7', '#34d399'), 'warning': ('#fcd34d', '#fbbf24'), 'breached': ('#fca5a5', '#f87171'), None: ('#c7d2fe', '#a5b4fc')}}
def _finish(kind, ttl, drawing, summ, tab, notes, u, rich, allow_fill=False):
    if not rich: return finish(kind, ttl, drawing, summ, tab, notes, u)
    from .rich import verify_rich
    verify_rich(drawing, allow_fill_animation=allow_fill)   # a gradient and a drop shadow are admitted only by the rich policy; the result says so
    s2, t2, ttl2, n2 = plain(summ), plain(tab), plain(ttl), [plain(x) for x in notes]; body_ = s2 + (' Notes: ' + ' '.join(n2) if n2 else '')
    res = Result(kind=kind, title=ttl2, svg=drawing, summary=s2, table=t2, notes=n2, alt=(f'{kind.replace(chr(95), chr(32)).capitalize()}: {ttl2}. {body_}' if ttl2 else f'{kind.replace(chr(95), chr(32)).capitalize()}. {body_}'))
    res['policy'] = 'rich'; return res
def _el(t, attrs, anim=''): return f'<{t} {attrs}/>' if not anim else f'<{t} {attrs}>{anim}</{t}>'   # a self-closing element, or one that holds an animation
def _fa(old, new): return f'<animate attributeName="fill" from="{old}" to="{new}" dur="0.8s" begin="0s" repeatCount="1" fill="freeze"/>'   # a status colour change; ends on the element's own fill
def _a_op(begin, dur): return f'<animate attributeName="opacity" from="0" to="1" dur="{dur}s" begin="{begin}s" repeatCount="1" fill="freeze"/>'
def _a_rot(a, cx, cy, begin, dur): return f'<animateTransform attributeName="transform" type="rotate" from="{a} {_g(cx)} {_g(cy)}" to="0 {_g(cx)} {_g(cy)}" dur="{dur}s" begin="{begin}s" repeatCount="1" fill="freeze"/>'
def _a_tr(x, y, begin, dur): return f'<animateTransform attributeName="transform" type="translate" from="{x} {y}" to="0 0" dur="{dur}s" begin="{begin}s" repeatCount="1" fill="freeze"/>'
def _g(x): return ('%.2f' % x).rstrip('0').rstrip('.')
def _pt(r, frac): a = math.pi * (1 - frac); return CX + r * math.cos(a), CY - r * math.sin(a)   # frac 0 = left end of the half circle, 1 = right end
def _w(text, size, weight=700): return len(text) * size * (0.58 if weight >= 700 else 0.52)   # an estimate of the text width in canvas px for layout only; the browser test checks it against real fonts   # an estimate of text width in canvas px, for layout only
def _wn(text, size):
    """A conservative width for the large numeral in any common bold sans-serif (digits are 0.70 em in the widest, the percent sign 1.0 em); used where text sits beside it."""
    return sum(1.0 if c == '%' else 0.70 if c.isdigit() else 0.40 if c in '.,' else 0.35 if c == ' ' else 0.78 for c in text) * size
def _wp(text, size):
    """A tighter width for where to START the margin text after the numeral (the browser test checks no overlap in three fonts)."""
    return sum(0.95 if c == '%' else 0.64 if c.isdigit() else 0.36 if c in '.,' else 0.30 if c == ' ' else 0.72 for c in text) * size
def _text(x, y, s, size, anchor, fill, weight=700): return label(x, y, s, size, anchor, fill, weight)
def _cut(s, n, notes, what):
    if len(s) > n: notes.append(f'The {what} was cut to {n} characters to fit.'); return s[:n - 1].rstrip() + '.'
    return s
def _delta_text(v, thr, u, short=False):
    d = v - thr; sign = '+' if d >= 0 else '-'
    unit = ' pts' if u.strip() == '%' else (u if u else '')
    return f'{sign}{fmt(abs(d))}{unit}' + ('' if short else ' vs target')
def _marker(P, tf):
    p1, p2 = _pt(140, tf), _pt(196, tf); o = P['outline']; k = P['ink']
    return (f'<line x1="{_g(p1[0])}" y1="{_g(p1[1])}" x2="{_g(p2[0])}" y2="{_g(p2[1])}" stroke="{o}" stroke-width="10"/><circle cx="{_g(p1[0])}" cy="{_g(p1[1])}" r="5" fill="{o}"/><circle cx="{_g(p2[0])}" cy="{_g(p2[1])}" r="5" fill="{o}"/>'
            f'<line x1="{_g(p1[0])}" y1="{_g(p1[1])}" x2="{_g(p2[0])}" y2="{_g(p2[1])}" stroke="{k}" stroke-width="4.5"/><circle cx="{_g(p1[0])}" cy="{_g(p1[1])}" r="2.25" fill="{k}"/><circle cx="{_g(p2[0])}" cy="{_g(p2[1])}" r="4.5" fill="{k}"/>'), p2
def _ring(y): return f'M {_g(CX - RO)},{y} A {_g(RO)},{_g(RO)} 0 0 1 {_g(CX + RO)},{y} A {_g(CAP)},{_g(CAP)} 0 0 1 {_g(CX + RI)},{y} A {_g(RI)},{_g(RI)} 0 0 0 {_g(CX - RI)},{y} A {_g(CAP)},{_g(CAP)} 0 0 1 {_g(CX - RO)},{y} Z'
def _fill_arc(frac, dy=0):
    """The value arc. Capped: it ends CAP_FRAC early so the cap's tip lands on `frac`. Too short for a cap: a flat sector, ending exactly at `frac`."""
    fe = frac - CAP_FRAC
    if fe >= 0.02:
        o, i = _pt(RO, fe), _pt(RI, fe); o = (o[0], o[1] + dy); i = (i[0], i[1] + dy); cy = CY + dy
        main = f'M {_g(CX - RO)},{_g(cy)} A {_g(RO)},{_g(RO)} 0 0 1 {_g(o[0])},{_g(o[1])} A {_g(CAP)},{_g(CAP)} 0 0 1 {_g(i[0])},{_g(i[1])} A {_g(RI)},{_g(RI)} 0 0 0 {_g(CX - RI)},{_g(cy)} A {_g(CAP)},{_g(CAP)} 0 0 1 {_g(CX - RO)},{_g(cy)} Z'
        if fe > 0.12:
            ho, hi_ = _pt(RO - 3, fe), _pt(RO - 7, fe)
            hl = f'M {_g(CX - RO + 3)},{_g(CY)} A {_g(RO - 3)},{_g(RO - 3)} 0 0 1 {_g(ho[0])},{_g(ho[1])} A 2,2 0 0 1 {_g(hi_[0])},{_g(hi_[1])} A {_g(RO - 7)},{_g(RO - 7)} 0 0 0 {_g(CX - RO + 7)},{_g(CY)} A 2,2 0 0 1 {_g(CX - RO + 3)},{_g(CY)} Z'
        else: hl = ''
        return main, hl
    if frac < 0.002: return '', ''
    o, i = _pt(RO, frac), _pt(RI, frac)
    return f'M {_g(CX - RO)},{_g(CY)} A {_g(RO)},{_g(RO)} 0 0 1 {_g(o[0])},{_g(o[1])} L {_g(i[0])},{_g(i[1])} A {_g(RI)},{_g(RI)} 0 0 0 {_g(CX - RI)},{_g(CY)} Z', ''
def _place_target_label(p2, tf, size, text, pill, header, notes):
    """Candidates around the marker's outer end; the first whose box keeps 12 px from the pill, the header, the arc band and the canvas edge wins."""
    w = _w(text, size) * 1.15; h = size   # 15 percent safety: the browser test runs wide fonts
    cands = [('start', p2[0] + 18, p2[1] - 2), ('end', p2[0] - 18, p2[1] - 2), ('middle', p2[0], p2[1] - 16), ('start', p2[0] + 18, p2[1] + 24), ('end', p2[0] - 18, p2[1] + 24)]
    for anchor, x, y in cands:
        x0 = x if anchor == 'start' else (x - w if anchor == 'end' else x - w / 2); box = (x0, y - h * 0.8, x0 + w, y + h * 0.25)
        if box[0] < 8 or box[2] > W_ - 8 or box[1] < 8: continue
        if box[3] > CY - 6: continue   # only above the arc's baseline: below it sit the status line and the scale ends
        if any(not (box[2] + 20 <= r[0] or box[0] >= r[2] + 20 or box[3] + 20 <= r[1] or box[1] >= r[3] + 20) for r in ([pill] if pill else []) + header): continue
        bad = False
        for k in range(13):
            for (px, py) in ((box[0] + (box[2] - box[0]) * k / 12, box[1]), (box[0] + (box[2] - box[0]) * k / 12, box[3]), (box[0], box[1] + (box[3] - box[1]) * k / 12), (box[2], box[1] + (box[3] - box[1]) * k / 12)):
                d = math.hypot(px - CX, py - CY)
                if py <= CY + 4 and RI - 12 < d < RO + 12: bad = True   # keep 12 px clear of the arc (the marker's own end is 28 px away by construction)
        if bad: continue
        return anchor, x, y
    return None   # no clear spot near the marker: the caller puts the label at the fixed spot below the arc
def gauge_modern(value=0, max_value=100, unit='', label='', title='', min=0, threshold=None, design='semicircle', theme='light', rich=False, shape_only=False, shape_tick=False, motion=False, from_status=None, glass=False, break_at=None, from_value=None, status=None):
    if glass is True or glass in ('break', 'seams'): return _glass(value, max_value, unit, label, title, min, threshold, design, theme, break_at, from_value, glass, status)   # glass=True: decided from the value, the previous value and break_at; 'break' or 'seams': decided by the caller (for example by glass_monitor, which holds the time rule)   # the glass effect: decided by the DATA (see _glass); every other argument means what it always meant
    notes = []; ttl = clean_text(title, 60, '') or ''; u = clean_text(unit, 8, '') or ''
    if u and isinstance(unit, str) and unit[:1] == ' ': u = ' ' + u[:7]
    lab = clean_text(label, 60, '') or ''
    if theme not in THEMES: notes.append(f'theme "{str(theme)[:12]}" is not light or dark, so light is used.'); theme = 'light'
    if design not in ('semicircle', 'bar'): notes.append(f'design "{str(design)[:12]}" is not semicircle or bar, so semicircle is used.'); design = 'semicircle'
    lo = _num(min, 0.0); hi = _num(max_value, None)
    if lo is None: lo = 0.0; notes.append('min is not a number, so 0 is used.')
    if hi is None: hi = 100.0; notes.append('max_value is not a number, so 100 is used.')
    if not hi > lo: return _note(ttl, 'The scale has no width (max_value is not above min).', notes)
    v = _num(value, None)
    if v is None: v = lo; notes.append('value is not a number, so the minimum is used.')
    shown = v
    if v < lo or v > hi: shown = lo if v < lo else hi; notes.append('The value is outside the scale; it is drawn at the nearest end and printed as given.')
    thr = _num(threshold, None) if threshold is not None else None
    if threshold is not None and thr is None: notes.append('threshold is not a number, so no target is drawn.')
    motion = motion is True; rich = rich is True or motion; mk_ = []   # motion: a ONE-TIME entrance (verify_motion: opacity, rotate, translate, each ending on the identity), no filter; it implies the rich gradient and flat shadow layers. mk_ = [(start, end, animations)] over `body`
    shape_only = shape_only is True; shape_tick = shape_tick is True; shape = []   # shape_only: the track, fill and marker alone, for use beside native text components (semicircle only)
    st = status if (status in ('healthy', 'warning', 'breached') and thr is not None) else _status(v, thr); P = THEMES[theme]; word, fill, stxt, pillbg = P['status'][st]   # status: the DATA layer may own it (a debounced monitor decides the colour, not the instant value); only with a target, because the words are judged against it
    trans = motion and from_status in ('healthy', 'warning', 'breached') and from_status != st; entr = motion and not trans   # trans: this picture is sent AT a status change: the colours fade from the old status to the new, nothing else moves; entr: the one-time entrance
    _old = P['status'][from_status] if trans else None; _pa = _fa(_old[3], pillbg) if trans else ''; _da = _fa(_old[2], stxt) if trans else ''; _fl = _fa(_old[1], fill) if trans else ''
    gid = f'g{theme[0]}{(st or "neutral")[0]}'; fid = f's{theme[0]}'   # ids unique per theme and status (gld, gdb, ...; the rich checker allows 16 characters), so several of these drawings inlined in one page never pick up each other's gradient
    frac = (shown - lo) / (hi - lo); tf = None if thr is None else _max(0.0, _min(1.0, (thr - lo) / (hi - lo)))
    if thr is not None and (thr < lo or thr > hi): notes.append('The target is outside the scale; it is drawn at the nearest end.')
    ttl_s = _cut(ttl, 20 if design == 'semicircle' else 22, notes, 'title'); lab_s = _cut(lab, 24, notes, 'label')
    vtxt = f'{fmt(v)}{u}'; lo_t, hi_t = f'{fmt(lo)}{u}', f'{fmt(hi)}{u}'
    body = [f'<rect width="{W_}" height="{H_}"' + (f' rx="{P["rx"]}"' if P['rx'] else '') + f' fill="{P["bg"]}"/>']
    pillw = (56 + 17 * len(word)) if word else 0
    if design == 'semicircle':
        x0 = 32; pill = (W_ - 24 - pillw, 18, W_ - 24, 58) if word else None
        body += [_text(x0, 44, ttl_s, 28, 'start', P['ink']), _text(x0, 74, lab_s, 24, 'start', P['ink2'], 400)] if ttl_s or lab_s else []
        _p0 = len(body)
        if word: body += [_el('rect', f'x="{pill[0]}" y="18" width="{pillw}" height="40" rx="20" fill="{pillbg}"', _pa) + _el('circle', f'cx="{pill[0] + 22}" cy="38" r="6" fill="{stxt}"', _da), _text(pill[0] + 38, 46, word, 24, 'start', stxt)]
        if entr and word: mk_.append((_p0, len(body), _a_tr(24, 0, 0.2, 0.5) + _a_op(0.2, 0.5)))
        _tr = [f'<path d="{_ring(_g(CY + 2))}" fill="#0f172a" fill-opacity="0.05"/>', f'<path d="{_ring(_g(CY + 4))}" fill="#0f172a" fill-opacity="0.05"/>', f'<path d="{_ring(_g(CY))}" fill="{P["track"]}"/>']
        body += _tr; shape += _tr; _n1 = len(body)
        main, hl = _fill_arc(frac)
        if main and trans:
            for dy_ in (2, 4): body.append(f'<path d="{_fill_arc(frac, dy_)[0]}" fill="{P["shadow"]}" fill-opacity="{P["shadow_a"]}"/>')
            body.append(_el('path', f'd="{main}" fill="{fill}"', _fl))
        elif main and motion:
            _f0 = len(body)
            for dy_ in (2, 4): body.append(f'<path d="{_fill_arc(frac, dy_)[0]}" fill="{P["shadow"]}" fill-opacity="{P["shadow_a"]}"/>')
            body.append(f'<path d="{main}" fill="url(#{gid})"/>'); mk_.append((_f0, len(body), _a_rot(-35, CX, CY, 0.1, 0.9) + _a_op(0.1, 0.5)))   # the arc swings into place about the gauge centre; flat shadow layers move with it, no filter
        elif main and rich: body.append(f'<g filter="url(#{fid})"><path d="{main}" fill="url(#{gid})"/></g>')
        elif main:
            for dy_ in (2, 4): body.append(f'<path d="{_fill_arc(frac, dy_)[0]}" fill="{P["shadow"]}" fill-opacity="{P["shadow_a"]}"/>')
            body.append(f'<path d="{main}" fill="{fill}"/>')
        # (the thin outer-edge highlight was removed after the loop 2 review: it read as gloss; the shadow and, in rich, the gradient give the depth)
        shape += body[_n1:]
        if tf is not None:
            mk, p2 = _marker(P, tf); body.append(mk); tl = f'Target {fmt(thr)}{u}'
            if shape_tick: a_, b_ = _pt(RI - 5, tf), _pt(RO + 5, tf); shape.append(f'<line x1="{_g(a_[0])}" y1="{_g(a_[1])}" x2="{_g(b_[0])}" y2="{_g(b_[1])}" stroke="{P["outline"]}" stroke-width="8"/><line x1="{_g(a_[0])}" y1="{_g(a_[1])}" x2="{_g(b_[0])}" y2="{_g(b_[1])}" stroke="{P["ink"]}" stroke-width="4"/>')   # a plain tick across the band: reads as a target, not a needle
            else: shape.append(mk)
            hdr = [(x0 - 4, 16, x0 + _w(ttl_s, 28), 52), (x0 - 4, 52, x0 + _w(lab_s, 24, 400), 82)]
            pos = _place_target_label(p2, tf, 24, tl, pill, hdr, notes)
            if pos: body.append(_text(pos[1], pos[2], tl, 24, pos[0], P['ink']))
            elif CX - _w(tl, 24) / 2 >= CX - RM + _w(lo_t, 24) / 2 + 12 and CX + _w(tl, 24) / 2 <= CX + RM - _w(hi_t, 24) / 2 - 12: body.append(_text(CX, 344, tl, 24, 'middle', P['ink2']))   # no clear spot near the marker: a fixed spot between the two scale ends
            else: notes.append('The target label does not fit clear of the arc or the scale ends, so it is left out; the marker and the status are drawn.')
        _v0 = len(body); size = 68 if len(vtxt) <= 5 else _max(24, int(68 * 5 / len(vtxt)))
        body.append(_text(CX, 250, vtxt, size, 'middle', P['ink']))
        if thr is not None:
            dt = _delta_text(v, thr, u); up = v >= thr
            if _w(dt, 24) > 272: dt = _delta_text(v, thr, u, True)   # the inner width of the arc is about 296, less 22 for the triangle: a margin like +26.3 pts vs target (19 characters) fits
            if _w(dt, 24) > 272: dt = ''; notes.append('The margin to the target is too long to print inside the arc, so it is left out.')
            if dt:
                tw = _w(dt, 24); startx = CX - (14 + 8 + tw) / 2
                tri = f'{_g(startx + 7)},{274 if up else 287} {_g(startx + 14)},{287 if up else 274} {_g(startx)},{287 if up else 274}'
                body += [_el('polygon', f'points="{tri}" fill="{stxt}"', _da), _text(startx + 22, 290, dt, 24, 'start', stxt)]
        if entr: mk_.append((_v0, len(body), _a_op(0.5, 0.5)))
        body += [_text(CX - RM, 344, lo_t, 24, 'middle', P['ink2']), _text(CX + RM, 344, hi_t, 24, 'middle', P['ink2'])]   # bold: the loop 3 panel found the bold scale ends easier to read on a phone
    else:
        x0, x1 = 40, 560; tw_ = x1 - x0; pill = (x1 - pillw, 24, x1, 70) if word else None
        body += [_text(x0, 48, ttl_s, 28, 'start', P['ink']), _text(x0, 78, lab_s, 24, 'start', P['ink2'], 400)] if ttl_s or lab_s else []
        _p0 = len(body)
        if word: body += [_el('rect', f'x="{pill[0]}" y="24" width="{pillw}" height="46" rx="23" fill="{pillbg}"', _pa) + _el('circle', f'cx="{pill[0] + 22}" cy="47" r="6" fill="{stxt}"', _da), _text(pill[0] + 38, 55, word, 24, 'start', stxt)]
        if entr and word: mk_.append((_p0, len(body), _a_tr(24, 0, 0.2, 0.5) + _a_op(0.2, 0.5)))
        _v0 = len(body); size = 72 if _wn(vtxt, 72) <= 300 else _max(24, int(300 / (_wn(vtxt, 1))))
        body.append(_text(x0, 172, vtxt, size, 'start', P['ink']))
        if thr is not None:
            up = v >= thr; dt = _delta_text(v, thr, u)
            # keep "vs target": shrink the large number (72 down to 48) until number, gap, triangle and the full margin text fit the 520 px row; only then shorten, and only if even that does not fit, leave the margin out
            fitted = next((sz for sz in range(size, 47, -4) if _wn(vtxt, sz) + 24 + 22 + _w(dt, 24) <= x1 - x0), None)
            if fitted is None:
                dt = _delta_text(v, thr, u, True); fitted = next((sz for sz in range(size, 47, -4) if _wn(vtxt, sz) + 24 + 22 + _w(dt, 24) <= x1 - x0), None)
            if fitted is None: dt = ''; notes.append('The margin to the target is too long to print beside the number, so it is left out.')
            else:
                if fitted != size: size = fitted; body[-1] = _text(x0, 172, vtxt, size, 'start', P['ink'])
            sx = x0 + _wp(vtxt, size) + 20
            if dt:
                tri = f'{_g(sx + 7)},{156 if up else 169} {_g(sx + 14)},{169 if up else 156} {_g(sx)},{169 if up else 156}'
                body += [_el('polygon', f'points="{tri}" fill="{stxt}"', _da), _text(sx + 22, 172, dt, 24, 'start', stxt)]
        if entr: mk_.append((_v0, len(body), _a_op(0.5, 0.5)))
        for dy in (2, 4): body.append(f'<rect x="{x0}" y="{TRACK_Y + dy}" width="{tw_}" height="44" rx="22" fill="#0f172a" fill-opacity="0.05"/>')
        body.append(f'<rect x="{x0}" y="{TRACK_Y}" width="{tw_}" height="44" rx="22" fill="{P["track"]}"/>')
        fw = tw_ * frac
        if fw >= 1 and trans:
            for dy_ in (2, 4): body.append(f'<rect x="{x0}" y="{TRACK_Y + dy_}" width="{_g(fw)}" height="44" rx="{_g(_min(22, fw / 2))}" fill="{P["shadow"]}" fill-opacity="{P["shadow_a"]}"/>')
            body.append(_el('rect', f'x="{x0}" y="{TRACK_Y}" width="{_g(fw)}" height="44" rx="{_g(_min(22, fw / 2))}" fill="{fill}"', _fl))
        elif fw >= 1 and motion:
            _f0 = len(body)
            for dy_ in (2, 4): body.append(f'<rect x="{x0}" y="{TRACK_Y + dy_}" width="{_g(fw)}" height="44" rx="{_g(_min(22, fw / 2))}" fill="{P["shadow"]}" fill-opacity="{P["shadow_a"]}"/>')
            body.append(f'<rect x="{x0}" y="{TRACK_Y}" width="{_g(fw)}" height="44" rx="{_g(_min(22, fw / 2))}" fill="url(#{gid})"/>'); mk_.append((_f0, len(body), _a_op(0.1, 0.7)))
        elif fw >= 1 and rich: body.append(f'<g filter="url(#{fid})"><rect x="{x0}" y="{TRACK_Y}" width="{_g(fw)}" height="44" rx="{_g(_min(22, fw / 2))}" fill="url(#{gid})"/></g>')
        elif fw >= 1:
            for dy_ in (2, 4): body.append(f'<rect x="{x0}" y="{TRACK_Y + dy_}" width="{_g(fw)}" height="44" rx="{_g(_min(22, fw / 2))}" fill="{P["shadow"]}" fill-opacity="{P["shadow_a"]}"/>')
            body.append(f'<rect x="{x0}" y="{TRACK_Y}" width="{_g(fw)}" height="44" rx="{_g(_min(22, fw / 2))}" fill="{fill}"/>')
        if fw >= 56: body.append(f'<rect x="{x0 + 14}" y="{TRACK_Y + 3}" width="{_g(fw - 28)}" height="4" rx="2" fill="{P["hi"]}" fill-opacity="0.12"/>')   # a faint highlight, almost to the fill's end (a 14 px inset on each side)
        if tf is not None:
            mx = x0 + tw_ * tf; o = P['outline']; k = P['ink']
            body += [f'<rect x="{_g(mx - 7)}" y="232" width="14" height="72" rx="7" fill="{o}"/><rect x="{_g(mx - 3.5)}" y="235.5" width="7" height="65" rx="3.5" fill="{k}"/>']
            tl = f'Target {fmt(thr)}{u}'; tlw = _w(tl, 24); cx_ = _max(x0 + tlw / 2, _min(x1 - tlw / 2, mx)); body.append(_text(cx_, 218, tl, 24, 'middle', P['ink']))
        body += [_text(x0, 340, lo_t, 24, 'start', P['ink2']), _text(x1, 340, hi_t, 24, 'end', P['ink2'])]
    for _s, _e, _an in sorted(mk_, reverse=True): body[_s:_e] = ['<g>' + ''.join(body[_s:_e]) + _an + '</g>']   # an animation must sit INSIDE a group, never in a text
    word_l = word.lower()
    aria = (f'{ttl}: ' if ttl else '') + f'{vtxt}' + (f', {word_l}, target {fmt(thr)}{u}' if st else '') + (f', {lab}' if lab else '')
    defs = (f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{RICH[theme][st][0]}"/><stop offset="1" stop-color="{RICH[theme][st][1]}"/></linearGradient>' +
            (f'<filter id="{fid}"><feDropShadow dx="0" dy="3" stdDeviation="3" flood-color="#000000" flood-opacity="{0.45 if theme == "dark" else 0.28}"/></filter>' if not motion else '') + '</defs>') if rich else ''
    if shape_only and design != 'semicircle': notes.append('shape_only is drawn for the semicircle only, so the full drawing is returned.'); shape_only = False
    if shape_only: drawing = (f'<svg xmlns="http://www.w3.org/2000/svg" width="460" height="226" viewBox="70 88 460 226" role="img" aria-label="{esc(aria)}"><title>{esc(aria)}</title>' + defs + ''.join(shape) + '</svg>')
    else: drawing = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W_}" height="{H_}" viewBox="0 0 {W_} {H_}" role="img" aria-label="{esc(aria)}"><title>{esc(aria)}</title>' + defs + ''.join(body) + '</svg>')
    summ = (f'{ttl}: ' if ttl else '') + f'{fmt(shown)}{u} on a scale of {fmt(lo)} to {fmt(hi)}.' + (f' Status {word_l} against a target of {fmt(thr)}{u}.' if st else ' No target was given, so no status is judged.') + (f' {lab}.' if lab else '')
    tab = f'Value {fmt(shown)}{u}; scale {fmt(lo)} to {fmt(hi)}' + (f'; target {fmt(thr)}{u} ({word_l})' if st else '')
    if motion:
        from .motion import verify_motion
        verify_motion(drawing)   # the stricter subset of the rich policy; a motion picture is refused here if it breaks a rule
    res_ = _finish('gauge_modern', ttl, drawing, summ, tab, notes, u, rich, trans)
    if motion: res_['motion'] = ('status change: the colours fade from ' + from_status + ' to ' + (st or 'none') + ', once, ends on the still picture') if trans else 'entrance, once, ends on the still picture'
    return {'gauge': res_, '_default': 'gauge'}
_min, _max = min, max

def _glass(value, max_value, unit, label, title, mn, threshold, design, theme, break_at, from_value, forced=True, status=None):
    """The glass effect (20 Nov 2026), decided by the DATA, not by the drawing: glass_state(value, from_value, break_at). break_at is the level at which the glass breaks (the value falling to it or under it); if it is None the level is the red zone
    itself (the value under 90 percent of the threshold, the same rule that makes the status BREACHED). 'break': the value has just crossed it (or this is the first picture and it is already beyond it): the picture plays once, 8 shards swing in from the point the value marks and end on the intact gauge.
    'seams': still beyond the level: the still picture with faint crack seams (a cue that is not colour). Otherwise the ordinary picture, no effect. Never silent: if the effect cannot be applied the still picture comes back with the reason in notes."""
    import re as _re, math as _math
    from .shatter import glass_state, shatter_in, seams_only
    v = _num(value, None); fv = _num(from_value, None) if from_value is not None else None; thr = _num(threshold, None) if threshold is not None else None
    br = _num(break_at, None) if break_at is not None else (None if thr is None else _math.nextafter(thr * 0.9, -_math.inf))
    state = forced if forced in ('break', 'seams') else glass_state(v, fv, br)   # the caller may have decided already (glass_monitor holds the time rule)
    kw = dict(max_value=max_value, unit=unit, label=label, title=title, min=mn, threshold=threshold, design=design, theme=theme, status=status)
    if state == 'none':
        res = gauge_modern(value, **kw)['gauge']; res['glass'] = {'state': 'none', 'break_at': br}; return {'gauge': res, '_default': 'gauge'}
    res = gauge_modern(value, motion=True, **kw)['gauge']   # the rich, filter-free drawing; its own entrance animation is stripped so the glass starts from the still picture, which IS the end of that entrance
    still = _re.sub(r'<animate(?:Transform)?\b[^>]*/>', '', res['svg']); lo = _num(mn, 0) if mn is not None else 0; hi = _num(max_value, 100)
    fr = _max(0.0, _min(1.0, ((v - lo) / (hi - lo)))) if hi != lo else 0.0; impact = _pt((RO + RI) / 2, fr) if design == 'semicircle' else None
    vb = _re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', still); card = (0, 0, float(vb.group(1)), float(vb.group(2)), THEMES[theme]['rx']) if vb else None
    out = shatter_in(still, impact=impact, clip_rect=card) if state == 'break' else seams_only(still, impact=impact)
    res['svg'] = out['svg'] if out['applied'] else still
    res['glass'] = {'state': state, 'break_at': br, 'applied': out['applied'], 'note': out['note']}
    if not out['applied']: res['notes'] = list(res.get('notes') or []) + ['The glass effect was not applied: ' + out['note']]
    lv = fmt(br) if br is not None else 'the level'; res['motion'] = ('glass: ' + out['note'] + ' (the value crossed ' + lv + ')') if out['applied'] and state == 'break' else ('seams over the still picture: still beyond ' + lv if out['applied'] else 'no motion')
    return {'gauge': res, '_default': 'gauge'}
