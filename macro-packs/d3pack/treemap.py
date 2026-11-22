"""treemap macro: same contract as the treemap atom (items [{category (max 20), name (max 24), value > 0, path? (1 to 3 group names)}], max_items 12 to 60 (default 12), unit, title, version).
Without a usable path: at most four categories. With any usable path the chart nests by path (up to 3 group levels, group header with name and total); an item without a path goes into its category group or 'Other'.
Layout = d3.treemapSquarify (golden ratio) ported to pure Python, applied twice like the atom: categories in the box (sized by category total), then the items inside
each category rectangle. Variant 'columns' = the atom's description (one column per category, items stacked) for comparison. Returns {layout: Result}. Result['rects']
holds the exact rectangles (cat, name, value, x0, y0, x1, y1) and Result['cats'] the category rectangles."""
# Port of d3-hierarchy 3.1.2 treemapSquarify (ISC), Copyright 2010-2021 Mike Bostock. See THIRD-PARTY-NOTICES.md.
import math
from .common import *
PHI = (1 + math.sqrt(5)) / 2
BX0, BY0, BX1, BY1 = 20.0, 20.0, W - 20.0, H - 20.0
def squarify(values, x0, y0, x1, y1, ratio=PHI):
    """d3 treemapSquarify for a flat list of positive values (input order kept). Returns [(x0, y0, x1, y1)] in the same order. Values are used as shares of their total
    (the algorithm is scale free); a share is floored at 1e-12 so subnormal or absurdly small values cannot divide by zero."""
    n = len(values)
    if n == 0: return []
    tot = float(sum(values)); vals = [max(v / tot, 1e-12) for v in values] if tot > 0 else [1.0 / n] * n
    out = [None] * n; value = float(sum(vals)); i0 = 0
    while i0 < n:
        dx, dy = x1 - x0, y1 - y0; i1 = i0; s = 0.0; gx, gy = max(dx, 1e-300), max(dy, 1e-300)
        while True:
            s = vals[i1]; i1 += 1
            if s or i1 >= n: break
        mn = mx = s; alpha = max(gy / gx, gx / gy) / (value * ratio); beta = s * s * alpha; minr = max(mx / beta, beta / mn)
        while i1 < n:
            v = vals[i1]; s += v; mn = min(mn, v); mx = max(mx, v); beta = s * s * alpha; newr = max(mx / beta, beta / mn)
            if newr > minr: s -= v; break
            minr = newr; i1 += 1
        rowv = vals[i0:i1]
        if dx < dy:  # dice: the row runs left to right across the full width, its height is its share
            ye = y0 + dy * s / value if value else y1; cur = x0
            for k, v in enumerate(rowv): w = (x1 - x0) * v / s if s else 0; out[i0 + k] = (cur, y0, cur + w, ye); cur += w
            if rowv: out[i0 + len(rowv) - 1] = out[i0 + len(rowv) - 1][:2] + (x1, ye)
            y0 = ye
        else:  # slice: the row is a column top to bottom, its width is its share
            xe = x0 + dx * s / value if value else x1; cur = y0
            for k, v in enumerate(rowv): h = (y1 - y0) * v / s if s else 0; out[i0 + k] = (x0, cur, xe, cur + h); cur += h
            if rowv: out[i0 + len(rowv) - 1] = out[i0 + len(rowv) - 1][:3] + (y1,)
            x0 = xe
        value -= s; i0 = i1
    return out
def columns(values, x0, y0, x1, y1):
    s = sum(values); out = []; cur = x0
    for v in values: w = (x1 - x0) * v / s; out.append((cur, y0, cur + w, y1)); cur += w
    out[-1] = out[-1][:2] + (x1, y1); return out
def stack(values, x0, y0, x1, y1):
    s = sum(values); out = []; cur = y0
    for v in values: h = (y1 - y0) * v / s; out.append((x0, cur, x1, cur + h)); cur += h
    out[-1] = out[-1][:3] + (y1,); return out
HDR = 24.0
VMAX = 1e12
def txt(x, n):
    """Text field reader: strings are cut early (before the character cleaning, so a huge string costs little) then ident() rules apply (dict, list, bool, None -> None)."""
    if isinstance(x, str): x = x[:4 * n + 8]
    return ident(x, n)
def read_value(v, cnt):
    """A value above 0 that is a finite number, as a float; anything else None. A value above 1e12 (or an integer too big for a float) is drawn as 1e12 and counted."""
    if isinstance(v, bool) or not isinstance(v, (int, float)): return None
    try: f = float(v)
    except OverflowError:
        if v < 0: return None
        cnt['clamped'] += 1; return VMAX
    if not math.isfinite(f): return None
    if f > VMAX: cnt['clamped'] += 1; return VMAX
    return f if f > 0 else None
def usable_path(p, maxlen=3):
    if not isinstance(p, list) or not 1 <= len(p) <= maxlen: return None
    q = [txt(x, 20) for x in p]
    return None if any(x is None for x in q) else q
def common_notes(notes, cnt, version, what='items'):
    if cnt['dropped']: notes.append(f"{cnt['dropped']} {what} were left out (not an item, or no value above 0 that is a finite number).")
    if cnt['clamped']: notes.append(f"{cnt['clamped']} value{' was' if cnt['clamped'] == 1 else 's were'} above {fmt(VMAX)} and drawn as {fmt(VMAX)}.")
    if isinstance(version, int) and not isinstance(version, bool) and version > 1: notes.append(f'Contract version {version} is drawn as version 1.')
def note_result(kind, title, message, notes):
    """The atom's 'a note replaces the chart': a drawing that is only the message (and Result['note_only'] is True)."""
    words = message.split(); lines = []; cur = ''
    for w in words:
        if len(cur) + len(w) + 1 > 52: lines.append(cur); cur = w
        else: cur = (cur + ' ' + w).strip()
    lines.append(cur); body = ''.join(label(W / 2, 200 + 26 * i, ln, 18, 'middle', INK) for i, ln in enumerate(lines))
    r = finish(kind, title, svg(body, kind.replace('_', ' ').capitalize()), message, message, notes); r['note_only'] = True; return r
def render(kind, ttl, aria, draw, summary, tab, notes, u):
    """draw(titles) -> svg body. If the drawing would exceed the size budget the hover titles go first (with a note); finish() refuses only if it is still too big."""
    notes = list(notes); body = draw(True)
    if len(svg(body, aria).encode()) > 76_000: notes.append('Hover titles were left out to keep the drawing small; the table has every value.'); body = draw(False)
    return finish(kind, ttl, svg(body, aria), summary, tab, notes, u)
def tip(show, text): return f'<title>{esc(text)}</title>' if show else ''
def ell(t, cap):
    """Name that fits `cap` characters, with an ellipsis when cut; '' when fewer than 3 characters would fit."""
    if cap < 3: return ''
    return t if len(t) <= cap else t[:cap - 1].rstrip() + '…'
def fit_chars(w, size=14): return int((w - 12) / (0.6 * size))
def _nested(its, ttl, u, notes, total, tab, summary):
    root = {'name': '', 'kids': [], 'value': 0.0, 'idx': {}}
    for it in its:
        node = root
        for seg in it['gpath']:
            nxt = node['idx'].get(seg)
            if nxt is None: nxt = {'name': seg, 'kids': [], 'value': 0.0, 'idx': {}, 'group': True}; node['idx'][seg] = nxt; node['kids'].append(nxt)
            node = nxt
        node['kids'].append({'name': it['name'], 'value': it['value'], 'group': False, 'kids': [], 'idx': {}})
    def tot(nd): nd['value'] = nd['value'] if not nd['kids'] else sum(tot(k) for k in nd['kids']); return nd['value']
    tot(root); nodes = []; leaves = []; tops = []
    def lay(nd, box, depth, top, path):
        x0, y0, x1, y1 = box; rr = squarify([k['value'] for k in nd['kids']], x0, y0, x1, y1)
        for k, r in zip(nd['kids'], rr):
            t = len(tops) if depth == 0 else top
            if depth == 0: tops.append(k['name'])
            w, h = r[2] - r[0], r[3] - r[1]; hdr = HDR if k['group'] and h >= 52 and w >= 60 else 0.0
            rec = {'name': k['name'], 'value': k['value'], 'depth': depth, 'top': t, 'group': k['group'], 'path': list(path), 'x0': r[0], 'y0': r[1], 'x1': r[2], 'y1': r[3], 'hdr': hdr, 'parent': id(nd)}
            rec['cx0'], rec['cy0'], rec['cx1'], rec['cy1'] = r[0], r[1] + hdr, r[2], r[3]; rec['id'] = id(k); nodes.append(rec)
            if k['group']: lay(k, (r[0], r[1] + hdr, r[2], r[3]), depth + 1, t, path + [k['name']])
            else: leaves.append(rec)
    lay(root, (BX0, BY0, BX1, BY1), 0, 0, [])
    def draw(titles):
        body = ''
        for r in nodes:
            w, h = r['x1'] - r['x0'], r['y1'] - r['y0']; base = PAL[r['top'] % 4]; tt = tip(titles, f'{"/".join(r["path"] + [r["name"]])}: {fmt(r["value"])}')
            if r['group']:
                col = blend(base, .12 * r['depth']); body += f'<rect x="{r["x0"]:.2f}" y="{r["y0"]:.2f}" width="{w:.2f}" height="{h:.2f}" fill="{blend(base, .8 - .05 * r["depth"])}" stroke="#ffffff" stroke-width="2">{tt}</rect>'
                if r['hdr']:
                    body += f'<rect x="{r["x0"]:.2f}" y="{r["y0"]:.2f}" width="{w:.2f}" height="{r["hdr"]:.0f}" fill="{col}"/>'
                    t = ell(f'{r["name"]} {fmt(r["value"])}', fit_chars(w))
                    if t: body += label(r['x0'] + 6, r['y0'] + 17, t, 14, 'start', text_on(col), 700)
            else:
                col = blend(base, .35 + .08 * (r['depth'] % 3)); body += f'<rect x="{r["x0"]:.2f}" y="{r["y0"]:.2f}" width="{w:.2f}" height="{h:.2f}" fill="{col}" stroke="#ffffff" stroke-width="2">{tt}</rect>'
                if h >= 44:
                    t = ell(r['name'], fit_chars(w))
                    if t: body += label(r['x0'] + 6, r['y0'] + 20, t, 14, 'start', text_on(col), 600) + label(r['x0'] + 6, r['y0'] + 38, fmt(r['value']), 14, 'start', text_on(col))
        return body
    res = render('treemap', ttl, 'Treemap', draw, summary, tab, notes, u)
    res['nodes'] = nodes; res['rects'] = [{'category': '/'.join(r['path']), 'name': r['name'], 'value': r['value'], 'x0': r['x0'], 'y0': r['y0'], 'x1': r['x1'], 'y1': r['y1']} for r in leaves]
    res['depth'] = max(r['depth'] for r in nodes) + 1; return res
def treemap(items, unit='', title='', version=1, max_items=12):
    notes = []; cnt = {'dropped': 0, 'clamped': 0}; u = txt(unit, 12) or ''; ttl = txt(title, 80) or ''
    cap = max_items if isinstance(max_items, int) and not isinstance(max_items, bool) and 12 <= max_items <= 60 else 12
    if not isinstance(items, list): raise ValueError('items must be a list')
    if len(items) > cap: notes.append(f'{len(items) - cap} items beyond the {cap}th were not drawn.'); items = items[:cap]
    its = []
    for n_, it in enumerate(items, 1):
        v = read_value(it.get('value'), cnt) if isinstance(it, dict) else None
        if v is None: cnt['dropped'] += 1; continue
        its.append({'category': txt(it.get('category'), 20) or 'Other', 'name': txt(it.get('name'), 24) or f'Item {n_}', 'value': v, 'path': usable_path(it.get('path'))})
    if not its: raise ValueError('a treemap needs at least 1 usable item')
    nest = any(i['path'] for i in its); cats = []
    for it in its:
        it['gpath'] = it['path'] or [it['category']]; top = it['gpath'][0]
        if top not in cats: cats.append(top)
    if not nest and len(cats) > 4:
        keep = cats[:4]; n0 = len(its); its = [i for i in its if i['category'] in keep]; cats = keep
        notes.append(f'{n0 - len(its)} items in categories beyond the 4th were not drawn.')
    if len(its) < 4: notes.append(f'Only {len(its)} usable items (the atom expects 4 to 12).')
    common_notes(notes, cnt, version)
    total = sum(i['value'] for i in its); ctot = [sum(i['value'] for i in its if i['gpath'][0] == c) for c in cats]
    where = lambda i: '/'.join(i['gpath']) if nest else i['category']
    tab = '; '.join(f"{where(i)}/{i['name']} {fmt(i['value'])}{(' ' + u) if u else ''} ({100 * i['value'] / total:.1f}%)" for i in its)
    big = max(its, key=lambda i: i['value']); bc = cats[ctot.index(max(ctot))]
    summary = f"Total {fmt(total)}{(' ' + u) if u else ''} in {len(its)} items and {len(cats)} {'top-level groups' if nest else 'categories'}; the largest item is {big['name']} ({fmt(big['value'])}, {100 * big['value'] / total:.0f}%) and the largest {'group' if nest else 'category'} is {bc} ({100 * max(ctot) / total:.0f}%)."
    if nest: return {'squarified': _nested(its, ttl, u, notes, total, tab, summary), '_default': 'squarified'}
    out = {}
    for lay in ('squarified', 'columns'):
        crect = (squarify if lay == 'squarified' else columns)(ctot, BX0, BY0, BX1, BY1); rects = []; pills = []
        for ci, c in enumerate(cats):
            members = [i for i in its if i['category'] == c]; cx0, cy0, cx1, cy1 = crect[ci]
            rr = (squarify if lay == 'squarified' else stack)([m['value'] for m in members], cx0, cy0, cx1, cy1)
            for k, (m, r) in enumerate(zip(members, rr)): rects.append({'category': c, 'name': m['name'], 'value': m['value'], 'x0': r[0], 'y0': r[1], 'x1': r[2], 'y1': r[3], 'cat_index': ci, 'first': k == 0})
        def draw(titles):
            body = ''
            for r in rects:
                ci = r['cat_index']; k = sum(1 for q in rects[:rects.index(r)] if q['cat_index'] == ci); col = blend(PAL[ci % len(PAL)], min(.5, .12 * k)); w, h = r['x1'] - r['x0'], r['y1'] - r['y0']
                body += f'<rect x="{r["x0"]:.2f}" y="{r["y0"]:.2f}" width="{w:.2f}" height="{h:.2f}" fill="{col}" stroke="#ffffff" stroke-width="2">{tip(titles, r["category"] + " / " + r["name"] + ": " + fmt(r["value"]))}</rect>'
                dy = 26 if r['first'] else 0   # the category pill sits in the first item's top-left corner
                if w >= 84 and h >= 44 + dy: body += label(r['x0'] + 8, r['y0'] + 22 + dy, ell(r['name'], fit_chars(w)), 14, 'start', text_on(col), 600) + label(r['x0'] + 8, r['y0'] + 40 + dy, fmt(r['value']), 14, 'start', text_on(col))
            for ci, c in enumerate(cats):
                cx0, cy0, cx1, cy1 = crect[ci]; t = ell(f'{c} {fmt(ctot[ci])}', fit_chars(cx1 - cx0 - 8, 14))
                if t and cy1 - cy0 >= 40:
                    pw = min(cx1 - cx0 - 8, 0.6 * 14 * len(t) + 14)
                    body += f'<rect x="{cx0 + 4:.2f}" y="{cy0 + 4:.2f}" width="{pw:.2f}" height="22" rx="11" fill="#ffffff" stroke="{PAL[ci % len(PAL)]}" stroke-width="2"/>' + label(cx0 + 4 + pw / 2, cy0 + 20, t, 14, 'middle', INK, 700)
            return body
        out[lay] = render('treemap', ttl, 'Treemap', draw, summary, tab, notes, u); out[lay]['rects'] = rects; out[lay]['cats'] = dict(zip(cats, crect))
    out['_default'] = 'squarified'; return out
