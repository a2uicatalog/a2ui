"""box_plot macro. Contract: the a2uicatalog `box_plot` atom, atoms/schema.yaml (`- type: box_plot`, stage stable).
Implemented: title (max 80), groups (1 to 12 of {label max 30 default 'Group n', values 5 to 2000}; non-finite or above 1e12 skipped and counted; a group with fewer than 5 usable numbers, or an
entry that is not a group, left out with a note; groups beyond the 12th noted), x_label (max 40), unit (max 12), show_points (only True; every usable number as a dot at its exact place, deterministic
dodge, at most 300 dots shared across groups in proportion to size and evenly spaced through each group's sorted numbers; dots that cannot be placed stay on the row edge and are counted),
quartile_method 'linear' (default, R-7 = d3 quantileSorted) | 'exclusive' | 'inclusive' (median of the lower and upper half, the odd sample's middle value left out or kept in both),
show_mean (diamond + Mean column), orientation 'h' | 'v' (both variants are returned), version. Box = Q1..Q3, median line, whiskers to the furthest numbers within 1.5 x box length (Tukey),
dots for outliers; past 100 distinct outliers in a group the 100 furthest from the median are drawn and a note says so, the table counts all. As in the atom, dots are not drawn together with
a non-default quartile_method, show_mean, or the vertical orientation (a note says so).
NOT implemented (named in the notes if given): stats, notches, shape/violin, bandwidth, the motion variable --p. Vertical layout: group names that would not fit are replaced by numbers with a key under the axis. If the drawing would exceed the size budget it is degraded step by step (tooltips dropped, coordinates to 0.1 px, fewer outlier circles and dots) with a note, and refused only if still too big. Returns {'horizontal': Result, 'vertical': Result}."""
import math
from .common import *
from .histogram import read_series, nice_edges, note_card, ctext
from .beeswarm import place
def _median(s): n = len(s); return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2
def quantile(s, p):
    """R-7 quantile of a sorted list (d3 quantileSorted)."""
    i = (len(s) - 1) * p; lo = math.floor(i); hi = min(lo + 1, len(s) - 1); return s[lo] + (s[hi] - s[lo]) * (i - lo)
def quartiles(s, method='linear'):
    if method == 'linear': return quantile(s, .25), quantile(s, .5), quantile(s, .75)
    h = len(s) // 2; lower = s[:h]; upper = s[h + 1:] if len(s) % 2 and method == 'exclusive' else s[h:] if len(s) % 2 else s[h:]
    if len(s) % 2 and method == 'inclusive': lower = s[:h + 1]
    return _median(lower), _median(s), _median(upper)
def five(vals, method='linear', k=1.5):
    s = sorted(vals); q1, med, q3 = quartiles(s, method); iqr = q3 - q1; lf, hf = q1 - k * iqr, q3 + k * iqr; inside = [v for v in s if lf <= v <= hf]
    return dict(n=len(s), min=s[0], q1=q1, med=med, q3=q3, max=s[-1], wlo=inside[0], whi=inside[-1], out=[v for v in s if v < lf or v > hf], mean=sum(s) / len(s))
def pick_dots(groups, cap=300):
    """Dots per group: all if the total fits, else shares in proportion to size (largest remainder), evenly spaced through each sorted group."""
    tot = sum(len(g['values']) for g in groups)
    if tot <= cap: return [sorted(g['values']) for g in groups]
    q = [len(g['values']) * cap / tot for g in groups]; k = [int(x) for x in q]
    for i in sorted(range(len(q)), key=lambda i: (-(q[i] - k[i]), i))[:cap - sum(k)]: k[i] += 1
    out = []
    for g, m in zip(groups, k):
        s = sorted(g['values']); out.append([s[round(j * (len(s) - 1) / (m - 1))] for j in range(m)] if m > 1 else s[:m])
    return out
BUDGET = 72_000
def box_plot(title='', groups=None, x_label='', unit='', show_points=False, version=1, quartile_method='linear', show_mean=False, orientation='h', **extra):
    notes = []; u = ctext(unit, 12, '') or ''; ttl = ctext(title, 80, '') or ''; xl = ctext(x_label, 40, '') or ''
    for k_ in ('stats', 'notches', 'shape', 'bandwidth'):
        if k_ in extra: notes.append(f'{k_} is not drawn by this macro.')
    gs = read_series(groups, notes, 'Group', 12, 'groups')
    if isinstance(version, int) and not isinstance(version, bool) and version > 1: notes.append(f'Contract version {version} is drawn as version 1.')
    if not gs: m = 'A box plot needs 1 to 12 groups, each with at least 5 usable numbers.'; return {'horizontal': note_card('box_plot', ttl, m, notes + [m]), '_default': 'horizontal'}
    qm = quartile_method if quartile_method in ('linear', 'exclusive', 'inclusive') else 'linear'
    if qm != quartile_method and quartile_method is not None: notes.append('quartile_method was not linear, exclusive or inclusive, linear was used.')
    sm = show_mean is True; ori = 'vertical' if orientation == 'v' else 'horizontal'
    if orientation not in ('h', 'v') and orientation is not None: notes.append('orientation was not h or v, drawn h.')
    pts = show_points is True
    if pts and (qm != 'linear' or sm or ori == 'vertical'): notes.append('show_points dots are not drawn together with quartile_method, show_mean or the vertical orientation.'); pts_h = False
    else: pts_h = pts
    for g in gs: g.update(five(g['values'], qm))
    lo = min(g['min'] for g in gs); hi = max(g['max'] for g in gs); ed = nice_edges(lo, hi, 6); dlo, dhi = ed[0], ed[-1]; un = (' ' + u) if u else ''
    def row(g):
        o = g['out']; od = sorted(set(o)); extra_ = f', Mean {fmt(g["mean"])}{un}' if sm else ''
        return (f'{g["label"]}: n {g["n"]}, min {fmt(g["min"])}{un}, Q1 {fmt(g["q1"])}{un}, median {fmt(g["med"])}{un}, Q3 {fmt(g["q3"])}{un}, max {fmt(g["max"])}{un}{extra_}, whiskers {fmt(g["wlo"])} to {fmt(g["whi"])}{un}, '
                + (f'{len(o)} outliers: ' + ', '.join(fmt(v) + un for v in od[:12]) + (f' and {len(od) - 12} more distinct' if len(od) > 12 else '') if o else 'no outliers') + '.')
    tab = f'Quartiles by {"linear interpolation (R-7)" if qm == "linear" else qm + " halves"}; whiskers reach the furthest number within 1.5 x the box length. ' + ' '.join(row(g) for g in gs)
    tot = sum(g['n'] for g in gs); nout = sum(len(g['out']) for g in gs); widest = max(gs, key=lambda g: g['q3'] - g['q1'])
    summary = f'{len(gs)} groups, {tot:,} values, {nout} outliers; widest middle half: {widest["label"]} ({fmt(widest["q1"])} to {fmt(widest["q3"])}{un}).'
    dots_all = pick_dots(gs) if pts_h else None
    if pts_h and sum(len(d) for d in dots_all) < tot: notes.append(f'Dots: {sum(len(d) for d in dots_all)} of {tot:,} numbers are drawn (limit 300 per chart); the table counts them all.')
    for g in gs:
        dist = sorted(set(g['out']), key=lambda v: (-abs(v - g['med']), v))
        if len(dist) > 100: notes.append(f'{g["label"]}: 100 of {len(dist)} distinct outliers are drawn (the furthest from the median); the table counts all.')
    cap = f'{xl} ({u})' if xl and u else (xl or u)
    def draw(o, level):
        """level 0 full; 1 no tooltips; 2 + coordinates to 0.1 px; 3 at most 30 outliers per group and every other dot; 4 at most 10 outliers, no dots."""
        hz = o == 'horizontal'; n_ = len(gs); dn = 2 if level < 2 else 1; N = lambda x: f'{x:.{dn}f}'; cap_o = 100 if level < 3 else 30 if level == 3 else 10
        extra_notes = []; slot_ = None
        L, R, T = (120, 24, 24) if hz else (64, 24, 24); B = (62 if cap else 46) if hz else (78 if cap else 62)
        chars = None
        if not hz:
            slot_ = (W - L - R) / n_; chars = max(3, int(slot_ / 8.5)); keyed = any(len(g['label']) > chars for g in gs)
            if keyed: kr = math.ceil(n_ / 2); B += 18 * kr + 6
        pw, ph = W - L - R, H - T - B; slot = (ph if hz else pw) / n_; bw = min(44, slot * .6)
        sc = (lambda v: L + (v - dlo) / (dhi - dlo) * pw) if hz else (lambda v: T + ph - (v - dlo) / (dhi - dlo) * ph)
        P = (lambda v, c: (sc(v), c)) if hz else (lambda v, c: (c, sc(v)))
        body = ''; unplaced = 0
        for e in ed:
            a = sc(e); body += (f'<line x1="{a:.2f}" x2="{a:.2f}" y1="{T}" y2="{T + ph}"' if hz else f'<line x1="{L}" x2="{W - R}" y1="{a:.2f}" y2="{a:.2f}"') + ' stroke="#c9cde0" stroke-width="1.5"/>'
            body += label(a, T + ph + 22, fmt(e), 14, 'middle', MUTED) if hz else label(L - 8, a + 5, fmt(e), 14, 'end', MUTED)
        for i, g in enumerate(gs):
            c = (T if hz else L) + slot * (i + .5); col = PAL[i % len(PAL)]
            dts = dots_all[i] if dots_all and level < 4 else None
            if dts and level == 3: dts = dts[::2]
            if hz and dts:
                xs = [sc(v) for v in dts]; half = slot / 2 - 4; ys = place(xs, 3.5, half); body += f'<g fill="{col}" fill-opacity=".5" data-dots="{i}">'
                for j, x in enumerate(xs):
                    y = ys[j]
                    if y is None: y = half if j % 2 else -half; unplaced += 1
                    body += f'<circle cx="{N(x)}" cy="{N(c + y)}" r="3.5"/>'
                body += '</g>'
            (x0, y0), (x1, y1) = P(g['q1'], c - bw / 2), P(g['q3'], c + bw / 2); bx, by = min(x0, x1), min(y0, y1)
            (a0, b0), (a1, b1) = P(g['wlo'], c), P(g['whi'], c); (m0, n0), (m1, n1) = P(g['med'], c - bw / 2), P(g['med'], c + bw / 2)
            body += '<g>' + (f'<title>{esc(g["label"])}: Q1 {fmt(g["q1"])}{esc(un)}, median {fmt(g["med"])}{esc(un)}, Q3 {fmt(g["q3"])}{esc(un)}</title>' if level == 0 else '')
            body += f'<line x1="{N(a0)}" y1="{N(b0)}" x2="{N(a1)}" y2="{N(b1)}" stroke="{INK}" stroke-width="2"/>'
            for v in (g['wlo'], g['whi']):
                (e0, f0), (e1, f1) = P(v, c - bw / 4), P(v, c + bw / 4); body += f'<line x1="{N(e0)}" y1="{N(f0)}" x2="{N(e1)}" y2="{N(f1)}" stroke="{INK}" stroke-width="2"/>'
            body += f'<rect x="{N(bx)}" y="{N(by)}" width="{N(abs(x1 - x0))}" height="{N(abs(y1 - y0))}" fill="{blend(col, .45)}" fill-opacity=".9" stroke="{col}" stroke-width="2.5" data-box="{i}"/>'
            body += f'<line x1="{N(m0)}" y1="{N(n0)}" x2="{N(m1)}" y2="{N(n1)}" stroke="{INK}" stroke-width="3.5"/></g>'
            if sm:
                mx, my = P(g['mean'], c); body += f'<path d="M{mx - 6:.2f},{my:.2f} L{mx:.2f},{my - 6:.2f} L{mx + 6:.2f},{my:.2f} L{mx:.2f},{my + 6:.2f}Z" fill="{FACE}" stroke="{INK}" stroke-width="2" data-mean="{i}"/>'
            od = sorted(set(g['out']), key=lambda v: (-abs(v - g['med']), v))
            if len(od) > cap_o and cap_o < 100 and not any(f'{g["label"]}: outlier circles' in x for x in extra_notes): extra_notes.append(f'{g["label"]}: outlier circles limited to {cap_o} to keep the drawing small; the table counts all.')
            od = od[:cap_o]
            if od:
                body += f'<g fill="none" stroke="{col}" stroke-width="2" data-lane="{i}">'
                for v in od:
                    cx, cy = P(v, c); body += (f'<circle cx="{N(cx)}" cy="{N(cy)}" r="4"><title>{esc(g["label"])} outlier {fmt(v)}{esc(un)}</title></circle>' if level == 0 else f'<circle cx="{N(cx)}" cy="{N(cy)}" r="4"/>')
                body += '</g>'
            if hz: body += label(L - 10, c + 5, g['label'][:14], 14, 'end')
            elif keyed: body += label(c, T + ph + 20, str(i + 1), 14, 'middle')
            else: body += label(c, T + ph + 20, g['label'][:chars], 14, 'middle')
        if unplaced and hz: extra_notes.append(f'{unplaced} dots could not be placed without touching and stay on the edge of their row.')
        body += f'<line x1="{L}" x2="{L}" y1="{T}" y2="{T + ph}" stroke="{INK}" stroke-width="2"/>' if hz else f'<line x1="{L}" x2="{W - R}" y1="{T + ph}" y2="{T + ph}" stroke="{INK}" stroke-width="2"/>'
        if not hz and keyed:
            for i, g in enumerate(gs): body += label(L + (i % 2) * (pw / 2), T + ph + 44 + 18 * (i // 2), f'{i + 1} = {g["label"]}', 14, 'start', MUTED)
        if cap: body += label(L + pw / 2, H - 12, cap, 14, 'middle', INK)
        return svg(body, 'Box plot'), extra_notes
    out = {}
    for o in ('horizontal', 'vertical'):
        for level in range(5):
            drawing, en = draw(o, level)
            if len(drawing) <= BUDGET and drawing.count('<') <= 3600: break
        onotes = list(notes) + en
        if level == 1: onotes.append('Tooltips were left out to keep the drawing small.')
        elif level >= 2: onotes.append('Tooltips were left out and coordinates rounded to 0.1 px to keep the drawing small.')
        if level == 4: onotes.append('Dots were left out to keep the drawing small.')
        elif level == 3 and dots_all: onotes.append('Every other dot was left out to keep the drawing small.')
        r = finish('box_plot', ttl, drawing, summary, tab, onotes, u); r['stats'] = [{k_: g[k_] for k_ in ('label', 'n', 'min', 'q1', 'med', 'q3', 'max', 'wlo', 'whi', 'out', 'mean')} for g in gs]; r['domain'] = (dlo, dhi); r['dots'] = dots_all; r['level'] = level; out[o] = r
    out['_default'] = ori; return out
