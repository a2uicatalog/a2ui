"""chord_diagram macro: same contract as the chord_diagram atom (groups, matrix, unit, directed, title, version). Undirected = d3.chord semantics (group arc = row sum, subgroups sorted
largest first, one ribbon per pair coloured by its SOURCE group = the larger direction, ribbon width at each end = the flow from that group). Directed (approximation of chordDirected +
ribbonArrow): one arrow ribbon per non-zero off-diagonal flow, from an outgoing slot in the source group to an incoming slot in the target group; group arc = row sum + column sum.
A visible legend names every group; the table lists every non-zero flow and each group's total out and in. Cells are read with finite semantics: not a number, negative or non-finite counts
as 0 (noted); a finite value above 1e12 is clamped to 1e12 (noted). groups not a list, fewer than 2 groups, a matrix that is not square or does not match, or no flow at all gives a
note-only Result (the atom: a note replaces the chart). Returns {mode: Result, '_default': mode}."""
import math
from .common import *
from .waterfall import note_result
PAD = 0.05; CELL_MAX = 1e12; MAX_G = 12
def _note(ttl, why, notes, mode='undirected'):
    notes.append(why); return {mode: note_result('chord_diagram', ttl, why + ' Nothing was drawn.', notes), '_default': mode}
def _clean(groups, matrix, notes):
    """Returns (names, matrix) or a string: the reason the chart is replaced by a note."""
    if not isinstance(groups, list): return 'The groups were not a list.'
    ng = len(groups); g = [ident(x, 20) or f'Group {i + 1}' for i, x in enumerate(groups[:MAX_G])]
    if ng < 2: return 'A chord diagram needs at least 2 groups.'
    if ng > MAX_G: notes.append(f'{ng - MAX_G} groups beyond the {MAX_G}th were not drawn, with their rows and columns.')
    if not isinstance(matrix, list): return 'A chord diagram needs a square matrix with one row per group. The matrix was not a list of rows.'
    if len(matrix) != ng or any(not isinstance(r, list) or len(r) != ng for r in matrix[:ng + 1]):
        shape = ' x '.join(str(len(r)) if isinstance(r, list) else '?' for r in matrix[:1])
        return f'A chord diagram needs a square matrix with one row per group. There are {ng} groups but the matrix has {len(matrix)} rows' + (f' of {shape} columns' if shape else '') + '.'
    n = len(g); m = []; badc = []; clamped = 0
    for i in range(n):
        row = []
        for j in range(n):
            v = matrix[i][j]
            if isinstance(v, bool) or not isinstance(v, (int, float)): badc.append((i, j)); v = 0.0
            else:
                try: f = float(v)
                except OverflowError: f = math.inf if v > 0 else -math.inf; v = None
                if f != f or (math.isinf(f) and v is not None) or f < 0: badc.append((i, j)); v = 0.0
                elif f > CELL_MAX: clamped += 1; v = CELL_MAX
                else: v = f
            row.append(v)
        m.append(row)
    if badc: notes.append(f'{len(badc)} cells were not a number of 0 or more and are treated as 0 (first: ' + ', '.join(f'{g[i]} to {g[j]}' for i, j in badc[:3]) + ').')
    if clamped: notes.append(f'{clamped} cells above {fmt(CELL_MAX)} were clamped to {fmt(CELL_MAX)}.')
    if sum(map(sum, m)) <= 0: return 'Every flow is 0.'
    return g, m
def undirected_layout(m):
    """d3.chord with sortSubgroups(descending): returns groups [(a0, a1)] and chords [(src, tgt, (s0, s1), (t0, t1))] in radians; src is the group of the larger direction (ties: the
    lower index). Independent of any drawing."""
    n = len(m); tot = sum(map(sum, m)); k = (2 * math.pi - PAD * n) / tot; x = 0; groups = []; sub = [[None] * n for _ in range(n)]
    for i in range(n):
        x0 = x
        for j in sorted(range(n), key=lambda j: -m[i][j]): sub[i][j] = (x, x + m[i][j] * k); x += m[i][j] * k
        groups.append((x0, x)); x += PAD
    chords = []
    for i in range(n):
        for j in range(i, n):
            if m[i][j] > 0 or m[j][i] > 0:
                if m[i][j] >= m[j][i]: chords.append((i, j, sub[i][j], sub[j][i]))
                else: chords.append((j, i, sub[j][i], sub[i][j]))
    return groups, chords
def directed_layout(m):
    n = len(m); out_ = [sum(r) for r in m]; in_ = [sum(m[i][j] for i in range(n)) for j in range(n)]; tot = sum(out_) * 2; k = (2 * math.pi - PAD * n) / tot; x = 0; groups = []; arrows = []
    starts = []
    for i in range(n): starts.append(x); x += (out_[i] + in_[i]) * k + PAD
    cursor_out = list(starts); cursor_in = [starts[i] + out_[i] * k for i in range(n)]
    for i in range(n):
        groups.append((starts[i], starts[i] + (out_[i] + in_[i]) * k))
        for j in range(n):
            if i != j and m[i][j] > 0:
                s = (cursor_out[i], cursor_out[i] + m[i][j] * k); cursor_out[i] = s[1]; arrows.append((i, j, s, None))
    res = []
    for (i, j, s, _) in arrows:
        t = (cursor_in[j], cursor_in[j] + m[i][j] * k); cursor_in[j] = t[1]; res.append((i, j, s, t))
    for i in range(n):     # a flow from a group to itself is a loop inside the group's outgoing slot
        if m[i][i] > 0: s = (cursor_out[i], cursor_out[i] + m[i][i] * k); cursor_out[i] = s[1]; res.append((i, i, s, s))
    return groups, res
def _pt(r, a): return (r * math.sin(a), -r * math.cos(a))
def _ribbon(cx, cy, r, s, t, arrow=False):
    (sx0, sy0), (sx1, sy1) = _pt(r, s[0]), _pt(r, s[1]); (tx0, ty0), (tx1, ty1) = _pt(r, t[0]), _pt(r, t[1]); o = lambda x, y: (cx + x, cy + y)
    ls = 1 if s[1] - s[0] > math.pi else 0; lt = 1 if t[1] - t[0] > math.pi else 0
    P = lambda x, y: '%.2f,%.2f' % o(x, y)
    if arrow:
        mid = (t[0] + t[1]) / 2; ax, ay = _pt(r - 14, mid); return f'M{P(sx0, sy0)} A{r},{r} 0 {ls} 1 {P(sx1, sy1)} Q{cx:.2f},{cy:.2f} {P(tx0, ty0)} L{P(ax, ay)} L{P(tx1, ty1)} Q{cx:.2f},{cy:.2f} {P(sx0, sy0)}Z'
    return f'M{P(sx0, sy0)} A{r},{r} 0 {ls} 1 {P(sx1, sy1)} Q{cx:.2f},{cy:.2f} {P(tx0, ty0)} A{r},{r} 0 {lt} 1 {P(tx1, ty1)} Q{cx:.2f},{cy:.2f} {P(sx0, sy0)}Z'
def _legend(names, y0):
    """Rows of swatch + name; returns (markup, rows)."""
    x = 24; y = y0; out = ''; rows = 1
    for i, nm in enumerate(names):
        w = 30 + len(nm) * 8.4 + 14
        if x + w > W - 24 and x > 24: x = 24; y += 26; rows += 1
        out += f'<rect x="{x:.0f}" y="{y - 13}" width="16" height="16" rx="3" fill="{PAL[i % len(PAL)]}"/>' + label(x + 22, y, nm, 14, 'start'); x += w
    return out, rows
def chord_diagram(groups, matrix, unit='', directed=False, title='', version=1):
    notes = []; u = ident(unit, 12) or ''; ttl = ident(title, 80) or ''
    if isinstance(version, int) and not isinstance(version, bool) and version > 1: notes.append(f'Contract version {min(version, 10 ** 9)} is drawn as version 1.')
    got = _clean(groups, matrix, notes)
    if isinstance(got, str): return _note(ttl, got, notes, 'directed' if directed is True else 'undirected')
    g, m = got; n = len(g); un = (' ' + u) if u else ''; cx, cy, R = W / 2, 270, 190; out = {}
    row = [sum(r) for r in m]; col = [sum(m[i][j] for i in range(n)) for j in range(n)]; top = max(range(n), key=row.__getitem__)
    big = max(((m[i][j], i, j) for i in range(n) for j in range(n)), key=lambda x: (x[0], -x[1], -x[2]))
    tab = '; '.join(f'{g[i]} to {g[j]} {fmt(m[i][j])}{un}' for i in range(n) for j in range(n) if m[i][j] > 0) + '. Totals out and in: ' + '; '.join(f'{g[i]} out {fmt(row[i])}{un}, in {fmt(col[i])}{un}' for i in range(n))
    summary = f'{n} groups; total flow {fmt(sum(row))}{un}; the largest flow is {g[big[1]]} to {g[big[2]]} ({fmt(big[0])}{un}); the biggest sender is {g[top]} ({fmt(row[top])}).'
    leg, rows = _legend(g, 520 + 4); h = 520 + 26 * rows + 16
    for mode in ('undirected', 'directed'):
        body = label(W / 2, 32, ttl, 20, weight=700) if ttl else ''
        if mode == 'undirected': grp, ribs = undirected_layout(m)
        else: grp, ribs = directed_layout(m)
        for (i, j, s, t) in ribs:
            if mode == 'undirected': tip = f'{g[i]} to {g[j]}: {fmt(m[i][j])}{un}' + (f' ({g[j]} to {g[i]}: {fmt(m[j][i])}{un})' if i != j else '')
            else: tip = f'{g[i]} to {g[j]}: {fmt(m[i][j])}{un}'
            body += f'<path d="{_ribbon(cx, cy, R - 6, s, t, arrow=(mode == "directed" and i != j))}" fill="{PAL[i % len(PAL)]}" fill-opacity=".55" stroke="{PAL[i % len(PAL)]}" stroke-width="1"><title>{esc(tip)}</title></path>'
        for i, (a0, a1) in enumerate(grp):
            body += f'<path d="{arc_path(cx, cy, R, R + 18, a0, a1)}" fill="{PAL[i % len(PAL)]}"><title>{esc(g[i] + ": out " + fmt(row[i]) + un + ", in " + fmt(col[i]) + un)}</title></path>'; mid = (a0 + a1) / 2
            if (a1 - a0) * (R + 34) >= 18:
                lx, ly = cx + (R + 34) * math.sin(mid), cy - (R + 34) * math.cos(mid) + 6; body += label(lx, ly, g[i][:14], 16, 'start' if math.sin(mid) > .2 else 'end' if math.sin(mid) < -.2 else 'middle', weight=600)
        out[mode] = finish('chord_diagram', ttl, svg(body + leg, 'Chord diagram', W, h), summary + (' Arrows approximate d3.chordDirected.' if mode == 'directed' else ''), tab, notes, u)
        out[mode]['layout'] = (grp, ribs); out[mode]['center'] = (cx, cy); out[mode]['radius'] = R; out[mode]['size'] = (W, h)
    out['_default'] = 'directed' if directed is True else 'undirected'; return out
