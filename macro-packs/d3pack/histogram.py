"""histogram macro. Contract: the a2uicatalog `histogram` atom, atoms/schema.yaml (`- type: histogram`, stage stable).
Implemented: title (max 80), values (5 to 2000 numbers; non-finite, non-number or above 1e12 skipped and counted; fewer than 5 left -> a NOTE REPLACES THE CHART, as the atom says),
bins (3..40, default Sturges ceil(log2 n)+1; edges rounded to 1/2/5 x 10^k so the drawn count can differ), x_label (max 40), unit (max 12, appended to the axis caption and to the
edge values in the table), layout 'bars' | 'ridge' (anything else draws bars), series (ridge only: 1 to 8 of {label max 30 default 'Series n', values 5..2000}, shared bins from the pooled
values, each ridge's height = its share of its own values per bin, no y axis, the table gives each bin's count per series), version (higher -> drawn as 1 with a note).
NOT implemented (named in the notes if given): bin_size/bin_start/bin_end, norm, cumulative, func, weights, and the motion variable --p.
Where this differs from d3.bin(): d3 keeps x0 = the smallest value and thresholds = d3.ticks(x0, x1, count), so its first and last bins can be narrower and a tick equal to the maximum adds a zero-width bin; here the extent is widened outward to whole tick steps, so every bin has one width and the last bin is closed. Constant data (span under 1e-9 x max(|lo|,|hi|,1)) is one bin of width 1.
Bins include the lower edge and exclude the upper, except the last, which includes both. The y axis starts at 0. Returns {layout: Result}; the ridge drawing is also used by ridgeline.py."""
# Port of d3-array 3.2.4 tickSpec/ticks (ISC), Copyright 2010-2023 Mike Bostock. See THIRD-PARTY-NOTICES.md.
import math
from bisect import bisect_right
from .common import *
def ctext(x, maxlen, default=None):
    """common.clean_text, but a huge int (10**400) or a non-finite float gives the default instead of raising OverflowError inside math.isfinite."""
    if isinstance(x, bool): return default
    if isinstance(x, int) and finite(x, -1e15, 1e15) is None: return default
    if isinstance(x, float) and not math.isfinite(x): return default
    return clean_text(x, maxlen, default)
MAXV = 2000; UNSUPPORTED = ('bin_size', 'bin_start', 'bin_end', 'norm', 'cumulative', 'func', 'weights')
def _spec(a, b, count):
    """d3-array tickSpec: (i1, i2, inc); inc < 0 means the step is 1/-inc."""
    step = (b - a) / max(0, count); power = math.floor(math.log10(step)); err = step / 10 ** power
    factor = 10 if err >= math.sqrt(50) else 5 if err >= math.sqrt(10) else 2 if err >= math.sqrt(2) else 1
    rnd = lambda x: math.floor(x + .5)
    if power < 0:
        inc = 10 ** -power / factor; i1 = rnd(a * inc); i2 = rnd(b * inc)
        if i1 / inc < a: i1 += 1
        if i2 / inc > b: i2 -= 1
        inc = -inc
    else:
        inc = 10 ** power * factor; i1 = rnd(a / inc); i2 = rnd(b / inc)
        if i1 * inc < a: i1 += 1
        if i2 * inc > b: i2 -= 1
    if i2 < i1 and .5 <= count < 2: return _spec(a, b, 2 * count)
    return i1, i2, inc
def d3_ticks(a, b, count):
    """d3.ticks for a < b: the nice values inside [a, b]."""
    if not count > 0: return []
    if a == b: return [a]
    i1, i2, inc = _spec(a, b, count)
    if i2 < i1: return []
    return [round((i1 + k) / -inc, 12) if inc < 0 else round((i1 + k) * inc, 12) for k in range(i2 - i1 + 1)]
def _r(x): return float(f'{x:.12g}')
def nice_edges(lo, hi, count):
    """Equal-width edges of whole tick steps covering [lo, hi]. A span below 1e-9 x max(|lo|, |hi|, 1) counts as zero: one bin of width 1 centred on the data."""
    if not hi - lo > 1e-9 * max(abs(lo), abs(hi), 1.0): m = (lo + hi) / 2; return [_r(m - .5), _r(m + .5)]
    _, _, inc = _spec(lo, hi, max(1, count))
    f, g = ((lambda i: i / -inc), (lambda x: x * -inc)) if inc < 0 else ((lambda i: i * inc), (lambda x: x / inc))
    a = math.floor(g(lo) + 1e-9); b = math.ceil(g(hi) - 1e-9)
    if b <= a: b = a + 1
    e = [_r(f(i)) for i in range(a, b + 1)]
    if any(e[i + 1] <= e[i] for i in range(len(e) - 1)): m = (lo + hi) / 2; return [_r(m - .5), _r(m + .5)]
    st = e[1] - e[0]
    while e[0] > lo and len(e) < 400: e.insert(0, _r(e[0] - st))
    while e[-1] < hi and len(e) < 400: e.append(_r(e[-1] + st))
    return e
def bin_counts(values, edges):
    """Counts per bin: [e_i, e_i+1), last bin closed. Values outside the edges are not counted."""
    c = [0] * (len(edges) - 1)
    for v in values:
        if edges[0] <= v <= edges[-1]: c[min(bisect_right(edges, v) - 1, len(c) - 1)] += 1
    return c
def numbers(seq, notes, what, cap=MAXV):
    """Tolerant reader for a list of numbers: only the first `cap` entries are read; finite numbers within +-1e12 are kept (common.finite), the rest counted."""
    if not isinstance(seq, list): notes.append(f'{what}: values is not a list, ignored.'); return []
    if len(seq) > cap: notes.append(f'{what}: {len(seq) - cap} entries beyond the {cap:,}th were not read.'); seq = seq[:cap]
    ok = [v for v in map(finite, seq) if v is not None]
    if len(ok) < len(seq): notes.append(f'{what}: {len(seq) - len(ok)} values were left out (not finite numbers, or above 1e12).')
    return ok
def groups_in(groups, values, notes, cap_groups, default_name='Values'):
    """[{name, values}] with the atoms' rules: unusable entries dropped and counted, names cleaned. `values` alone makes one group."""
    if isinstance(groups, list) and groups:
        out = []; bad = 0
        if len(groups) > cap_groups: notes.append(f'{len(groups) - cap_groups} groups beyond the {cap_groups}th were not drawn.'); groups = groups[:cap_groups]
        for i, g in enumerate(groups, 1):
            if not isinstance(g, dict) or not isinstance(g.get('values'), list): bad += 1; continue
            nm = ctext(g.get('name'), 24, f'Group {i}'); out.append({'name': nm, 'values': numbers(g['values'], notes, nm)})
        if bad: notes.append(f'{bad} groups were left out (not an object with a values list).')
        if len(out) > cap_groups: notes.append(f'{len(out) - cap_groups} groups beyond the {cap_groups}th were not drawn.'); out = out[:cap_groups]
        return [g for g in out if g['values']]
    v = numbers(values, notes, default_name) if values is not None else []
    return [{'name': default_name, 'values': v}] if v else []
def nice_ticks(vmax, n=5):
    if vmax <= 0: return 1, [0, 1]
    raw = vmax / n; mag = 10 ** math.floor(math.log10(raw)); f = raw / mag
    step = (1 if f <= 1 else 2 if f <= 2 else 5 if f <= 5 else 10) * mag
    top = math.ceil(vmax / step) * step
    return step, [round(i * step, 10) for i in range(int(round(top / step)) + 1)]
def rng_text(a, b, last): return f'[{fmt(a)}, {fmt(b)}{"]" if last else ")"}'
def note_card(kind, title, message, notes):
    """The atom's 'a note replaces the chart': a drawing that is only the message."""
    words = message.split(); lines = []; cur = ''
    for w in words:
        if len(cur) + len(w) + 1 > 52: lines.append(cur); cur = w
        else: cur = (cur + ' ' + w).strip()
    lines.append(cur); body = ''.join(label(W / 2, 200 + 26 * i, ln, 18, 'middle', INK) for i, ln in enumerate(lines))
    r = finish(kind, title, svg(body, kind.replace('_', ' ').capitalize()), message, message, notes); r['note_only'] = True; return r
def read_series(raw, notes, default, cap_n, what):
    """[{label max 30 default '<default> n', values}] with the atom's rules: entries that are not objects, or with fewer than 5 usable numbers, left out with a note."""
    if not isinstance(raw, list): return []
    if len(raw) > cap_n: notes.append(f'{len(raw) - cap_n} {what} beyond the first {cap_n} were not drawn.'); raw = raw[:cap_n]
    out = []; bad = 0
    for i, g in enumerate(raw, 1):
        if not isinstance(g, dict) or not isinstance(g.get('values'), list): bad += 1; continue
        lab = ctext(g.get('label'), 30, f'{default} {i}'); v = numbers(g['values'], notes, lab)
        if len(v) < 5: notes.append(f'{lab} was left out: fewer than 5 usable numbers.'); continue
        out.append({'label': lab, 'values': v})
    if bad: notes.append(f'{bad} {what} were left out (not an object with a values list).')
    return out
def bins_target(bins, n, notes):
    if bins is None: return math.ceil(math.log2(n)) + 1
    if isinstance(bins, int) and not isinstance(bins, bool):
        k = min(40, max(3, bins))
        if k != bins: notes.append(f'bins {bins} was clamped to {k}.')
        return k
    notes.append('bins is not an integer, the Sturges rule was used.'); return math.ceil(math.log2(n)) + 1
def caption(xl, u): return f'{xl} ({u})' if xl and u else (xl or u)
def ridge_result(kind, title, series, bins, xl, u, notes, overlap=1.6):
    """Shared ridge drawing. series = [{label, values}] already read."""
    allv = [v for s in series for v in s['values']]; edges = nice_edges(min(allv), max(allv), bins_target(bins, len(allv), notes)); nb = len(edges) - 1
    for s in series: s['counts'] = bin_counts(s['values'], edges); s['shares'] = [c / len(s['values']) for c in s['counts']]
    smax = max(max(s['shares']) for s in series); un = (' ' + u) if u else ''
    tab = f'Count per bin and series; bin width {fmt(edges[1] - edges[0])}{un}, each bin includes its lower edge, the last also its upper edge. ' + ' '.join(
        f'{s["label"]} ({len(s["values"]):,} values): ' + '; '.join(f'{fmt(edges[i])}{un} to {fmt(edges[i + 1])}{un}: {s["counts"][i]}' for i in range(nb)) + '.' for s in series)
    pk = max(series, key=lambda s: max(s['shares'])); pi = pk['shares'].index(max(pk['shares']))
    summary = f'{len(series)} series, {len(allv):,} values in {nb} bins from {fmt(edges[0])} to {fmt(edges[-1])}{un}; the highest ridge is {pk["label"]} at {fmt(edges[pi])} to {fmt(edges[pi + 1])} ({pk["counts"][pi]} of its {len(pk["values"]):,} values).'
    L, R, T = 120, 24, 24; B = 62 if caption(xl, u) else 46; pw, ph = W - L - R, H - T - B; px = lambda e: L + (e - edges[0]) / (edges[-1] - edges[0]) * pw
    s_ = ph / (len(series) - 1 + overlap); scale = overlap * s_ / smax; body = ''
    for e in edges[::max(1, math.ceil(len(edges) / 9))]: body += f'<line x1="{px(e):.2f}" x2="{px(e):.2f}" y1="{T}" y2="{T + ph}" stroke="#e3e6f2" stroke-width="1.5"/>' + label(px(e), T + ph + 22, fmt(e), 14, 'middle', MUTED)
    bases = []
    for i, g in enumerate(series):
        base = T + overlap * s_ + i * s_; bases.append(base); col = PAL[i % len(PAL)]
        pts = [(edges[0], 0)] + [((edges[k] + edges[k + 1]) / 2, c) for k, c in enumerate(g['shares'])] + [(edges[-1], 0)]
        d = 'M' + ' L'.join(f'{px(x):.2f},{base - c * scale:.2f}' for x, c in pts) + 'Z'
        body += f'<path d="{d}" fill="{blend(col, .25)}" fill-opacity=".88" stroke="{col}" stroke-width="2.5" data-group="{i}"><title>{esc(g["label"])}: {len(g["values"]):,} values, tallest bin {max(g["counts"])}</title></path>' + label(L - 10, base + 5, g['label'][:14], 14, 'end')
    body += f'<line x1="{L}" x2="{W - R}" y1="{T + ph}" y2="{T + ph}" stroke="{INK}" stroke-width="2"/>'
    if caption(xl, u): body += label(L + pw / 2, H - 12, caption(xl, u), 14, 'middle', INK)
    r = finish(kind, title, svg(body, 'Ridge histogram'), summary, tab, notes, u)
    r['edges'] = edges; r['counts'] = [g['counts'] for g in series]; r['shares'] = [g['shares'] for g in series]; r['names'] = [g['label'] for g in series]; r['bases'] = bases; r['scale'] = scale; return r
def histogram(title='', values=None, bins=None, x_label='', unit='', layout='bars', series=None, version=1, **extra):
    notes = []; u = ctext(unit, 12, '') or ''; ttl = ctext(title, 80, '') or ''; xl = ctext(x_label, 40, '') or ''
    for k in UNSUPPORTED:
        if k in extra: notes.append(f'{k} is not drawn by this macro.')
    if isinstance(version, int) and not isinstance(version, bool) and version > 1: notes.append(f'Contract version {version} is drawn as version 1.')
    if layout == 'ridge':
        ss = read_series(series, notes, 'Series', 8, 'series')
        if not ss: m = 'The ridge layout needs 1 to 8 series, each with at least 5 usable numbers.'; return {'ridge': note_card('histogram', ttl, m, notes + [m]), '_default': 'ridge'}
        return {'ridge': ridge_result('histogram', ttl, ss, bins, xl, u, notes), '_default': 'ridge'}
    if layout != 'bars': notes.append('layout was not bars or ridge, drawn as bars.')
    vals = numbers(values, notes, 'Values', MAXV) if values is not None else []
    if len(vals) < 5: m = f'Fewer than 5 usable numbers ({len(vals)}), so there is no histogram.'; return {'bars': note_card('histogram', ttl, m, notes + [m]), '_default': 'bars'}
    n_all = len(vals); edges = nice_edges(min(vals), max(vals), bins_target(bins, n_all, notes)); nb = len(edges) - 1; counts = bin_counts(vals, edges); tmax = max(counts); un = (' ' + u) if u else ''
    tab = f'{n_all:,} values in {nb} bins of width {fmt(edges[1] - edges[0])}{un}, each bin includes its lower edge, the last also its upper edge. Bins from, to, count: ' + '; '.join(f'{fmt(edges[i])}{un} to {fmt(edges[i + 1])}{un}: {counts[i]}' for i in range(nb)) + '.'
    ti = counts.index(tmax); summary = f'{n_all:,} values in {nb} bins from {fmt(edges[0])} to {fmt(edges[-1])}{un}; the tallest bin is {rng_text(edges[ti], edges[ti + 1], ti == nb - 1)} with {tmax}.'
    L, R, T = 64, 20, 24; B = 78 if caption(xl, u) else 60; pw, ph = W - L - R, H - T - B; px = lambda e: L + (e - edges[0]) / (edges[-1] - edges[0]) * pw
    step, tk = nice_ticks(tmax); top = tk[-1]; py = lambda c: T + ph - ph * c / top; body = ''
    for t in tk: body += f'<line x1="{L}" x2="{W - R}" y1="{py(t):.2f}" y2="{py(t):.2f}" stroke="#c9cde0" stroke-width="1.5"/>' + label(L - 8, py(t) + 5, fmt(t), 14, 'end', MUTED)
    for i in range(nb):
        if counts[i]: body += f'<rect x="{px(edges[i]) + 1:.2f}" y="{py(counts[i]):.2f}" width="{px(edges[i + 1]) - px(edges[i]) - 2:.2f}" height="{T + ph - py(counts[i]):.2f}" fill="{PAL[0]}"><title>{esc(rng_text(edges[i], edges[i + 1], i == nb - 1))}: {counts[i]}</title></rect>'
    body += f'<line x1="{L}" x2="{W - R}" y1="{T + ph}" y2="{T + ph}" stroke="{INK}" stroke-width="2"/>'
    for i in range(0, len(edges), math.ceil(len(edges) / 9)): body += label(px(edges[i]), T + ph + 22, fmt(edges[i]), 14, 'middle', MUTED)
    if caption(xl, u): body += label(L + pw / 2, H - 14, caption(xl, u), 14, 'middle', INK)
    r = finish('histogram', ttl, svg(body, 'Histogram'), summary, tab, notes, u); r['edges'] = edges; r['counts'] = [counts]; r['names'] = ['Values']; r['mode'] = 'bars'
    return {'bars': r, '_default': 'bars'}
