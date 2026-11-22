"""Contract source: atoms/schema.yaml (limits and tolerant-reader rules re-checked against it).
waterfall macro: steps [{label, value, kind total|delta}] (1 to 24), x_label, unit, title, version. Horizontal floating bars on one axis joined by dashed connectors.
A delta moves the level (green up, red down; the signed change is printed at the end of the row); a total without a value shows the running level as a bar from 0; a total with a value sets
the level to it (a note says when that differs from the steps before it). A delta needs a finite value up to 1e12; anything else is left out with a note. The default label is 'Step n' where n is the
position in the list. Numbers print with up to 6 decimals (the atom: 'the decimals the given values use, at most 6'), axis ticks with fmt(). Returns {'waterfall': Result}. A steps argument that is
not a list, or has no usable step, gives a note-only Result (nothing to draw) instead of an error. This module also holds three helpers the other flow macros share: safe_text, note_result, fit_svg."""
import math, re
from .common import *
def safe_text(x, maxlen, default=None):
    """clean_text that cannot raise: an integer too big for a float (10**400) or a non-finite number is not text."""
    if isinstance(x, (int, float)) and not isinstance(x, bool) and finite(x, -1e15, 1e15) is None: return default
    return clean_text(x, maxlen, default)
def fmt6(v):
    """Up to 6 decimals, thousands separators, trailing zeros trimmed, float noise rounded away; a non-zero value never shows as 0."""
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v): return '0'
    if abs(v) >= 1e15: return fmt(v)
    r = round(float(v), 6)
    if r == 0: return '0' if v == 0 else f'{v:.3g}'
    return f'{r:,.6f}'.rstrip('0').rstrip('.')
def note_result(kind, title, text, notes):
    """A Result that says why nothing was drawn: a small SVG carrying the sentence, the sentence as summary and table. Used instead of raising when the atom shows a message."""
    words = plain(text).split(); lines = []; cur = ''
    for w in words:
        if cur and len(cur) + 1 + len(w) > 52: lines.append(cur); cur = w
        else: cur = (cur + ' ' + w).strip()
    if cur: lines.append(cur)
    body = ''.join(label(W / 2, 200 + i * 26, l, 18, 'middle', INK) for i, l in enumerate(lines[:8]))
    r = finish(kind, title, svg(body, kind.replace('_', ' ').capitalize() + ': nothing to draw'), 'Nothing was drawn. ' + text, 'No data drawn.', notes); r['empty'] = True; return r
def fit_svg(draw, notes, limit=78_000, max_elements=3900):
    """Degrade before refusing: draw(level) returns the SVG at detail level 0 (everything), 1 (no hover titles) or 2 (no hover titles and no numbers inside the picture). The first level that fits
    the output policy (bytes, element count) is used and the loss is noted; if even level 2 is too big the policy check in finish() refuses it."""
    for lvl in range(3):
        s = draw(lvl)
        if len(s.encode()) <= limit and len(re.findall(r'<[A-Za-z]', s)) <= max_elements:
            if lvl == 1: notes.append('Hover titles were left out to keep the drawing small; the data table has every value.')
            if lvl == 2: notes.append('Hover titles and the numbers inside the drawing were left out to keep it small; the data table has every value.')
            return s
    notes.append('The drawing is still large after leaving out detail.'); return s
def nice_step(span, n=5):
    if not span > 0 or not math.isfinite(span): return 1
    raw = span / n; mag = 10 ** math.floor(math.log10(raw)); f = raw / mag
    return (1 if f <= 1 else 2 if f <= 2 else 5 if f <= 5 else 10) * mag
def waterfall(steps, x_label='', unit='', title='', version=1, reveal=None):
    notes = []; u = safe_text(unit, 12, '') or ''; ttl = safe_text(title, 80, '') or ''; xl = safe_text(x_label, 40, '') or ''
    if isinstance(version, int) and not isinstance(version, bool) and version > 1: notes.append(f'Contract version {min(version, 10**9)} is drawn as version 1.')
    if not isinstance(steps, list): notes.append('steps must be a list of {label, value, kind}.'); return {'waterfall': note_result('waterfall', ttl, 'The steps were not a list, so there is nothing to draw.', notes), '_default': 'waterfall'}
    if len(steps) > 24: notes.append(f'{len(steps) - 24} steps beyond the 24th were not drawn.'); steps = steps[:24]
    bars = []; level = 0.0; dropped = 0; reset = 0
    for i, s in enumerate(steps, 1):
        if not isinstance(s, dict): dropped += 1; continue
        kind = 'total' if s.get('kind') == 'total' else 'delta'; lab = safe_text(s.get('label'), 30, f'Step {i}'); v = finite(s.get('value'))
        if kind == 'delta':
            if v is None: dropped += 1; continue
            start = level; level = level + v; bars.append({'label': lab, 'kind': 'delta', 'value': v, 'start': start, 'end': level, 'level': level})
        else:
            if v is not None:
                if abs(v - level) > 1e-9 * max(1, abs(v)) and bars: reset += 1
                level = v
            bars.append({'label': lab, 'kind': 'total', 'value': level, 'start': 0.0, 'end': level, 'level': level})
    if dropped: notes.append(f'{dropped} steps were left out (not an object, or a change without a finite value up to 1e12 in size).')
    if reset: notes.append(f'{reset} totals gave a value different from the running total of the steps before and set it.')
    if not bars: notes.append('No step could be used.'); return {'waterfall': note_result('waterfall', ttl, 'No step could be used, so there is nothing to draw.', notes), '_default': 'waterfall'}
    m = reveal if isinstance(reveal, int) and not isinstance(reveal, bool) and 1 <= reveal <= len(bars) else len(bars)      # reveal: draw only the first m bars; the axis and row layout stay those of ALL bars, so successive frames line up
    lv = [0.0] + [b['start'] for b in bars] + [b['end'] for b in bars]; lo, hi = min(lv), max(lv)
    if hi - lo < 1e-12: hi = lo + 1
    step = nice_step(hi - lo); t0 = math.floor(lo / step + 1e-9) * step; t1 = math.ceil(hi / step - 1e-9) * step; ticks = [round(t0 + i * step, 10) for i in range(int(round((t1 - t0) / step)) + 1)]
    L, R, T, B = 180, 96, 40, 76; pw, ph = W - L - R, H - T - B; X = lambda v: L + pw * (v - ticks[0]) / (ticks[-1] - ticks[0]); n = len(bars); rh = ph / n; bh = max(4, rh * .68)
    col = {'increase': PAL[4], 'decrease': PAL[3], 'total': PAL[0]}
    for b in bars: b['text'] = (fmt6(b['value']) if b['kind'] == 'total' else ('+' if b['value'] >= 0 else '-') + fmt6(abs(b['value']))) + (f' {u}' if u else '')
    def draw(lvl):
        body = ''
        for i, c in enumerate(col): body += f'<rect x="{L + i * 150}" y="9" width="14" height="14" fill="{col[c]}"/>' + label(L + i * 150 + 20, 22, c.capitalize(), 14, 'start', MUTED)
        for t in ticks: body += f'<line x1="{X(t):.2f}" x2="{X(t):.2f}" y1="{T}" y2="{T + ph}" stroke="{INK if t == 0 else "#d5d9ea"}" stroke-width="{2 if t == 0 else 1}"/>' + label(X(t), T + ph + 20, fmt(t), 14, 'middle', MUTED)
        if xl or u: body += label(L + pw / 2, H - 14, xl + (f' ({u})' if u and xl else u), 14, 'middle', MUTED)
        for i, b in enumerate(bars[:m]):
            y = T + i * rh + (rh - bh) / 2; a, z = sorted((b['start'], b['end'])); x0, x1 = X(a), X(z); vt = b['text']
            c = col['total'] if b['kind'] == 'total' else col['increase'] if b['value'] >= 0 else col['decrease']
            body += f'<rect x="{x0:.2f}" y="{y:.2f}" width="{max(2, x1 - x0):.2f}" height="{bh:.2f}" rx="3" fill="{c}">' + (f'<title>{esc(b["label"])}: {esc(vt)}</title>' if lvl == 0 else '') + '</rect>'
            body += label(L - 10, y + bh / 2 + 5, b['label'][:22], 14, 'end', INK)
            if x1 + 8 + len(vt) * 8 < W - 4: body += label(x1 + 6, y + bh / 2 + 5, vt, 14, 'start', INK, 700)
            else: body += label(x0 - 6, y + bh / 2 + 5, vt, 14, 'end', INK, 700)
            if i + 1 < m:
                nx = bars[i + 1]; join = nx['start'] == b['end'] if nx['kind'] == 'delta' else abs(nx['end'] - b['end']) <= 1e-9 * max(1, abs(b['end']))   # a total bar ends at the level the step before it reached
                if join: xe = X(b['end']); body += f'<line x1="{xe:.2f}" x2="{xe:.2f}" y1="{y + bh:.2f}" y2="{y + rh:.2f}" stroke="{MUTED}" stroke-width="1.5" stroke-dasharray="3 2"/>'
        return svg(body, ('Waterfall chart' + (': ' + ttl if ttl else '') + (f', {n} steps' if m == n else f', {m} of {n} steps'))[:200])
    sh = bars[:m]; rows = [f'{b["label"]} {b["text"]}' + (f' (running total {fmt6(b["level"])}{(" " + u) if u else ""})' if b['kind'] == 'delta' else '') for b in sh]
    ups = [b for b in sh if b['kind'] == 'delta' and b['value'] > 0]; dns = [b for b in sh if b['kind'] == 'delta' and b['value'] < 0]
    summary = (f'{n} steps' if m == n else f'{m} of {n} steps shown') + f'; the running total ends at {fmt6(sh[-1]["level"])}{(" " + u) if u else ""}.' + (f' Largest increase: {max(ups, key=lambda b: b["value"])["label"]} {max(ups, key=lambda b: b["value"])["text"]}.' if ups else '') + (f' Largest decrease: {min(dns, key=lambda b: b["value"])["label"]} {min(dns, key=lambda b: b["value"])["text"]}.' if dns else '')
    r = finish('waterfall', ttl, fit_svg(draw, notes), summary, '; '.join(rows), notes, u); r['bars'] = bars; r['ticks'] = ticks
    return {'waterfall': r, '_default': 'waterfall'}
