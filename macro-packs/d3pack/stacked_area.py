"""stacked_area macro. Contract source: atoms/schema.yaml: title, labels, series [{label, data, color}],
layout 'area'|'bars' (default area), offset (expand|silhouette|wiggle, else none), up to 12 series and 60 labels, negative or non-numeric cells drawn as 0 and counted in a note.
d3.stack semantics: none/silhouette/expand keep input order; wiggle uses d3.stackOffsetWiggle with d3.stackOrderInsideOut (the atom: 'layers ordered inside-out'). Series colours are not used (PAL only;
with more than 8 series PAL repeats, noted). Values must be finite and 0..1e12 (else drawn as 0 and counted). Fewer than 2 labels, no usable series or all-zero data give a note-only Result (the atom shows a
message) instead of an error. Labels and series names are kept in full in the table and shortened only in the drawing (counted in a note). The 'bars' layout is a simplified horizontal stacked-bar list
(first 24 labels drawn, all in the table). Returns {offset: Result x4 | 'bars': Result, '_default': ...}."""
# Port of d3-shape 3.2.0 stackOrderInsideOut and stackOffsetWiggle (ISC), Copyright 2010-2022 Mike Bostock. See THIRD-PARTY-NOTICES.md.
import math
from .common import *
from .waterfall import nice_step, safe_text, note_result, fit_svg, fmt6
def inside_out(cols):
    """d3.stackOrderInsideOut: series sorted by the index of their peak, then dealt alternately to the lighter side; returns series indices bottom to top."""
    n = len(cols[0]); ser = [[c[i] for c in cols] for i in range(n)]; peaks = [ser[i].index(max(ser[i])) for i in range(n)]; sums = [sum(x) for x in ser]
    ords = sorted(range(n), key=lambda i: peaks[i]); top = bottom = 0.0; tops = []; bottoms = []
    for j in ords:
        if top < bottom: top += sums[j]; tops.append(j)
        else: bottom += sums[j]; bottoms.append(j)
    return bottoms[::-1] + tops
def stack(cols, offset):
    """cols[j][i] = value of layer i at x j (all >= 0). Returns lay[i] = (y0 list, y1 list), d3.stack / stackOffset* semantics."""
    n = len(cols[0]); m = len(cols); y0 = [[0.0] * m for _ in range(n)]; y1 = [[0.0] * m for _ in range(n)]
    base = [0.0] * m; order = inside_out(cols) if offset == 'wiggle' else list(range(n)); cols = [[c[i] for i in order] for c in cols]
    if offset == 'silhouette': base = [-sum(c) / 2 for c in cols]
    elif offset == 'wiggle':
        y = 0.0; base = [0.0] * m
        for j in range(1, m):
            s1 = s2 = 0.0
            for i in range(n):
                s3 = (cols[j][i] - cols[j - 1][i]) / 2 + sum(cols[j][k] - cols[j - 1][k] for k in range(i)); s1 += cols[j][i]; s2 += s3 * cols[j][i]
            base[j - 1] = y
            if s1: y -= s2 / s1
        base[m - 1] = y
    for j in range(m):
        tot = sum(cols[j]); k = (1 / tot if tot else 0) if offset == 'expand' else 1; acc = base[j]
        for i in range(n): y0[i][j] = acc; acc += cols[j][i] * k; y1[i][j] = acc
    inv = {o: i for i, o in enumerate(order)}; return [(y0[inv[i]], y1[inv[i]]) for i in range(n)]
OFFSETS = ('none', 'silhouette', 'wiggle', 'expand')
def stacked_area(labels, series, title='', offset='none', layout='area', version=1):
    notes = []; ttl = safe_text(title, 80, '') or ''
    if isinstance(version, int) and not isinstance(version, bool) and version > 1: notes.append(f'Contract version {min(version, 10**9)} is drawn as version 1.')
    def empty(why):
        notes.append(why); return {'none': note_result('stacked_area', ttl, why + ' There is nothing to draw.', notes), '_default': 'none'}
    if not isinstance(labels, list) or not isinstance(series, list): return empty('labels and series must both be lists.')
    if len(labels) > 60: notes.append(f'{len(labels) - 60} labels beyond the 60th were not drawn.'); labels = labels[:60]
    full = [safe_text(x, 40, f'#{i + 1}') for i, x in enumerate(labels)]; m = len(full)
    if m < 2: return empty('A stacked area needs at least 2 labels.')
    if len(series) > 12: notes.append(f'{len(series) - 12} series beyond the 12th were not drawn.'); series = series[:12]
    ss = []; dropped = 0; fixed = 0; fit = 0
    for s in series:
        if not isinstance(s, dict) or not isinstance(s.get('data'), list): dropped += 1; continue
        d = s['data']
        if len(d) != m: fit += 1
        vals = []
        for j in range(m):
            v = finite(d[j], 0, 1e12) if j < len(d) else None
            if v is None: vals.append(0.0); fixed += 1 if j < len(d) else 0
            else: vals.append(v)
        ss.append({'label': safe_text(s.get('label'), 40, f'Series {len(ss) + 1}'), 'data': vals})
    if dropped: notes.append(f'{dropped} series were left out (not an object, or no data list).')
    if fixed: notes.append(f'{fixed} values that were negative, not numbers or over 1e12 are drawn as 0.')
    if fit: notes.append(f'{fit} series had a data list of a different length from the labels; it was cut or padded with 0.')
    if len(ss) > 8: notes.append('More than 8 series: the pack palette repeats colours.')
    if not ss: return empty('No series could be used.')
    cols = [[s['data'][j] for s in ss] for j in range(m)]; totals = [sum(c) for c in cols]
    if max(totals) <= 0: return empty('Every value is 0.')
    lab = [x[:10] for x in full]; short = sum(1 for x in full if len(x) > 10) + sum(1 for s in ss if len(s['label']) > 16)
    if short: notes.append(f'{short} labels or series names are shortened in the drawing; the table has them in full.')
    lay_req = 'bars' if layout == 'bars' else 'area'
    off_req = offset if isinstance(offset, str) else None
    if offset is not None and off_req not in OFFSETS and lay_req == 'area': notes.append(f'Offset {plain(offset)[:20] if isinstance(offset, str) else "(not text)"!r} is drawn as none.')
    tab = '; '.join(f'{s["label"]}: ' + ', '.join(f'{full[j]} {fmt6(s["data"][j])}' for j in range(m)) for s in ss) + '. Column totals: ' + ', '.join(f'{full[j]} {fmt6(totals[j])}' for j in range(m))
    peak = max(range(m), key=lambda j: totals[j]); top = max(ss, key=lambda s: sum(s['data'])); names = ', '.join(s['label'] for s in ss)
    head = f'{len(ss)} series ({names}) over {m} points from {full[0]} to {full[-1]}; the total peaks at {full[peak]} ({fmt6(totals[peak])}); the biggest series is {top["label"]} ({fmt6(sum(top["data"]))} in all).'
    aria = f'Stacked area chart{": " + ttl if ttl else ""}: {names}, {full[0]} to {full[-1]}'[:280]
    if lay_req == 'bars':
        if off_req not in (None, 'none') or (offset is not None and off_req is None): notes.append('The bar layout ignores offset.')
        rows = min(m, 24)
        if m > rows: notes.append(f'Only the first {rows} labels are drawn as bars; the table lists all {m}.')
        L, T = 110, 16; rh = (H - T - 100) / rows; vmax = max(totals[:rows]); step = nice_step(vmax); top_ = math.ceil(vmax / step - 1e-9) * step
        if vmax <= 0: return empty('Every value in the first 24 labels is 0.')
        X = lambda v: L + (W - L - 20) * v / top_
        def drawb(lvl):
            body = ''
            for j in range(rows):
                y = T + j * rh; acc = 0.0; body += label(L - 8, y + rh / 2 + 5, lab[j], 14, 'end', MUTED)
                for i, sr in enumerate(ss):
                    v = sr['data'][j]; body += f'<rect x="{X(acc):.2f}" y="{y + 1:.2f}" width="{X(acc + v) - X(acc):.2f}" height="{rh - 2:.2f}" fill="{PAL[i % 8]}">' + (f'<title>{esc(sr["label"])} {fmt6(v)}</title>' if lvl == 0 else '') + '</rect>'; acc += v
            for t in range(int(round(top_ / step)) + 1): body += label(X(t * step), T + rows * rh + 20, fmt(t * step), 14, 'middle', MUTED)
            for i, sr in enumerate(ss): body += f'<rect x="{20 + (i % 4) * 170}" y="{H - 62 + (i // 4) * 24}" width="14" height="14" fill="{PAL[i % 8]}"/>' + label(20 + (i % 4) * 170 + 20, H - 50 + (i // 4) * 24, sr['label'][:16], 14, 'start')
            return svg(body, aria.replace('area chart', 'bars'))
        bn = list(notes); r = finish('stacked_area', ttl, fit_svg(drawb, bn), head + ' Drawn as stacked bars.', tab, bn); r['totals'] = totals; r['layout'] = 'bars'; return {'bars': r, '_default': 'bars'}
    desc = {'none': 'Layers stack up from a zero baseline.', 'silhouette': 'Layers are centred on a middle line, so the total thickness is the column total.', 'wiggle': 'Layers sit on a wiggling baseline that minimises slope changes; thickness is still the value.', 'expand': 'Each column is scaled to 100 percent, so thickness is the share.'}
    L, R, T, B = 70, 24, 24, 118; pw, ph = W - L - R, H - T - B; X = lambda j: L + pw * j / (m - 1); out = {}
    for off in OFFSETS:
        lay = stack(cols, off); lo = min(min(y0) for y0, _ in lay); hi = max(max(y1) for _, y1 in lay)
        if off == 'expand': lo, hi, ticks = 0.0, 1.0, [0, .25, .5, .75, 1]
        elif off == 'none': step = nice_step(hi); hi = math.ceil(hi / step - 1e-9) * step; lo = 0.0; ticks = [round(i * step, 10) for i in range(int(round(hi / step)) + 1)]
        else: ticks = []; pad = (hi - lo) * .04; lo -= pad; hi += pad
        Y = lambda v, lo=lo, hi=hi: T + ph - ph * (v - lo) / (hi - lo)
        def draw(lvl, lay=lay, ticks=ticks, off=off, Y=Y):
            body = ''
            for t in ticks: body += f'<line x1="{L}" x2="{W - R}" y1="{Y(t):.2f}" y2="{Y(t):.2f}" stroke="#d5d9ea"/>' + label(L - 8, Y(t) + 5, (f'{round(t * 100)}%' if off == 'expand' else fmt(t)), 14, 'end', MUTED)
            if not ticks: body += label(L - 8, T + 14, 'Thickness = value', 14, 'start', MUTED)
            for i, (y0, y1) in enumerate(lay):
                pts = [f'{X(j):.2f},{Y(y1[j]):.2f}' for j in range(m)] + [f'{X(j):.2f},{Y(y0[j]):.2f}' for j in range(m - 1, -1, -1)]
                body += f'<polygon points="{" ".join(pts)}" fill="{PAL[i % 8]}" fill-opacity=".85" stroke="{FACE}" stroke-width="1.5">' + (f'<title>{esc(ss[i]["label"])}</title>' if lvl == 0 else '') + '</polygon>'
            every = max(1, math.ceil(m * 56 / pw))
            for j in range(0, m, every): body += label(X(j), T + ph + 22, lab[j], 14, 'middle', MUTED)
            for i, s in enumerate(ss): body += f'<rect x="{L + (i % 4) * 160}" y="{T + ph + 44 + (i // 4) * 28}" width="14" height="14" fill="{PAL[i % 8]}"/>' + label(L + (i % 4) * 160 + 20, T + ph + 57 + (i // 4) * 28, s['label'][:16], 14, 'start')
            return svg(body, aria)
        vn = list(notes); r = finish('stacked_area', ttl, fit_svg(draw, vn), head + ' ' + desc[off], tab, vn)
        r['layers'] = [{'label': ss[i]['label'], 'y0': lay[i][0], 'y1': lay[i][1]} for i in range(len(ss))]; r['offset'] = off; r['totals'] = totals; out[off] = r
    out['_default'] = off_req if off_req in OFFSETS else 'none'; return out
