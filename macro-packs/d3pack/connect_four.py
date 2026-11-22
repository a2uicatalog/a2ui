"""connect_four: a Connect Four position as a picture (own design, not a d3 atom). Inputs: cells (42 values, row-major from the TOP row, ' ' / 'R' / 'Y'; or six strings of seven characters with '.' or ' ' for empty), last (row, col) of the newest disc, win (four (row, col) pairs), title.
Tolerant reader: characters that are not R, Y, space or '.' count as empty and are noted; last and win are dropped with a note if they are not valid cells; a board that is not 42 cells is refused (a ValueError). Discs carry a letter as well as a colour. Colours are baked in."""
from .common import *
import math
ROWS, COLS, CELL, PAD, TOP = 6, 7, 80, 0, 44   # PAD 0: the column pitch is exactly 1/7 of the picture width, so seven equal-width buttons under it line up with the columns
W_, H_ = COLS * CELL + 2 * PAD, ROWS * CELL + 2 * PAD + TOP
RED, YEL, HOLE, BOARD = '#c2182b', '#f5c518', '#dfe6f5', '#2f4fb3'
NAME = {'R': 'Red', 'Y': 'Yellow'}
def _xy(r, c): return PAD + c * CELL + CELL / 2, TOP + PAD + r * CELL + CELL / 2
def _cells(cells, notes):
    if isinstance(cells, (list, tuple)) and len(cells) == ROWS and all(isinstance(x, str) and len(x) == COLS for x in cells): cells = [ch for row in cells for ch in row]
    if not isinstance(cells, (list, tuple)) or len(cells) != ROWS * COLS: raise ValueError('cells must be 42 values (six rows of seven), row-major from the top')
    out = []; bad = 0
    for v in cells:
        v = v if isinstance(v, str) else ' '
        if v in ('R', 'Y'): out.append(v)
        else: out.append(' '); bad += v not in (' ', '.', '')
    if bad: notes.append(f'{bad} cell values were not R, Y, space or . and were drawn as empty.')
    return out
def _cell(x, notes, what):
    try:
        r, c = int(x[0]), int(x[1])
        if isinstance(x[0], bool) or isinstance(x[1], bool) or not (0 <= r < ROWS and 0 <= c < COLS): raise ValueError
        return r, c
    except Exception: notes.append(f'{what} was not a valid cell and was left out.'); return None
def draw(cells, last=None, win=None):
    """The SVG alone, for a caller that already holds a clean 42-cell list (the game server). Same output policy as every macro."""
    notes = []; cells = _cells(cells, notes); win = {w for w in (_cell(x, notes, 'a winning cell') for x in (win or [])) if w}; last = _cell(last, notes, 'the last-move marker') if last else None
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W_}" height="{H_}" viewBox="0 0 {W_} {H_}" role="img" aria-label="Connect Four board">', f'<rect x="0" y="{TOP}" width="{W_}" height="{H_ - TOP}" rx="18" fill="{BOARD}"/>']
    for c in range(COLS): s.append(label(PAD + c * CELL + CELL / 2, 30, str(c + 1), 22, 'middle', INK, 700))
    for r in range(ROWS):
        for c in range(COLS):
            x, y = _xy(r, c); v = cells[r * COLS + c]
            s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="32" fill="{RED if v == "R" else YEL if v == "Y" else HOLE}"/>')
            if v != ' ': s.append(label(x, y + 9, v, 26, 'middle', '#ffffff' if v == 'R' else INK, 800))
            if (r, c) in win: s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="36" fill="none" stroke="#ffffff" stroke-width="6"/>')
            elif last == (r, c): s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="36" fill="none" stroke="{INK}" stroke-width="4"/>')
    s.append('</svg>'); return verify_svg(''.join(s))

# ---- 3D views. Geometry in grid units: x across (0..7), y up (0..6), w toward the viewer (0 back of the slab, T front face, T + DISC the front of a disc).
T, DISC, NPTS = 0.6, 0.32, 20
KX, KY = 0.22, 0.34                       # oblique recession: up and to the right, small enough that seven equal buttons under the picture still sit under their columns
_VIEWS = ('flat', 'oblique', 'iso')
def _proj3(mode, x, y, w, s):
    """Screen position (before the frame offset). iso: the true isometric view from the front-right-above, so columns slant. oblique: the board face stays a true rectangle and depth recedes up and to the right (cabinet projection)."""
    if mode == 'iso': return (x - w) * 0.8660254 * s, (x + w) * 0.5 * s - y * s
    d = T - w; return x * s + d * KX * s, -(y * s + d * KY * s)
def _frame(mode):
    pts = [_proj3(mode, x, y, w, 1.0) for x in (0, COLS) for y in (0, ROWS + 0.9) for w in (0, T + DISC)]
    x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts); y0, y1 = min(p[1] for p in pts), max(p[1] for p in pts)
    if mode == 'oblique': x0 = min(x0, COLS - x1)     # pad the left as far as the depth sticks out on the right, so the board face is centred in the picture
    s = min(640 / (x1 - x0), 520 / (y1 - y0)); return s, -x0 * s, -y0 * s + 20, round((x1 - x0) * s), round((y1 - y0) * s + 40)
def _ring(mode, cx, cy, w, r, f, s, ox, oy):
    pts = [_proj3(mode, cx + r * math.cos(2 * math.pi * k / NPTS), cy + r * math.sin(2 * math.pi * k / NPTS), w, s) for k in range(NPTS)]
    return ' '.join(f'{ox + px:.1f},{oy + py:.1f}' for px, py in pts)
def _hex2(c, f, mix=0.0):
    r, g, b = int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16); out = []
    for v in (r, g, b): v = v * f; out.append(max(0, min(255, int(round(v + (255 - v) * mix)))))
    return '#%02x%02x%02x' % tuple(out)
def draw3(cells, last=None, win=None, mode='oblique'):
    """The board as a 3D picture: a thick slab with 42 holes and discs standing out of its front face. Same output policy as every macro."""
    if mode not in ('oblique', 'iso'): raise ValueError('view must be flat, oblique or iso')
    notes = []; cells = _cells(cells, notes); win = {w for w in (_cell(x, notes, 'a winning cell') for x in (win or [])) if w}; last = _cell(last, notes, 'the last-move marker') if last else None
    s, ox, oy, W3, H3 = _frame(mode); P = lambda x, y, w: (ox + _proj3(mode, x, y, w, s)[0], oy + _proj3(mode, x, y, w, s)[1]); poly = lambda pts, fill, stroke='none', sw=1: '<polygon points="' + ' '.join(f'{a:.1f},{b:.1f}' for a, b in pts) + f'" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W3}" height="{H3}" viewBox="0 0 {W3} {H3}" role="img" aria-label="Connect Four board, 3D view">']
    out.append(poly([P(0, ROWS, T), P(COLS, ROWS, T), P(COLS, ROWS, 0), P(0, ROWS, 0)], _hex2(BOARD, 1.0, 0.28), INK, 1.2))      # top edge
    out.append(poly([P(COLS, 0, T), P(COLS, ROWS, T), P(COLS, ROWS, 0), P(COLS, 0, 0)], _hex2(BOARD, 0.62), INK, 1.2))           # right end
    out.append(poly([P(0, 0, T), P(COLS, 0, T), P(COLS, ROWS, T), P(0, ROWS, T)], BOARD, INK, 1.2))                                # front face
    for c in range(COLS):
        tx, ty = P(c + 0.5, ROWS, 0 if mode == 'oblique' else T); out.append(label(tx, ty - 12, str(c + 1), 22, 'middle', INK, 700))
    side, edge = {'R': _hex2(RED, 0.62), 'Y': _hex2(YEL, 0.62), ' ': HOLE}, _hex2(BOARD, 0.55)
    for r in range(ROWS):
        for c in range(COLS):
            cx, cy = c + 0.5, ROWS - r - 0.5; v = cells[r * COLS + c]
            out.append(poly(_pts(_ring(mode, cx, cy, T, 0.40, 0, s, ox, oy)), _hex2(HOLE, 0.9), edge, 1))
            if v == ' ': continue
            col = RED if v == 'R' else YEL
            out.append(poly(_pts(_ring(mode, cx, cy, T, 0.40, 0, s, ox, oy)), side[v], INK, 1)); out.append(poly(_pts(_ring(mode, cx, cy, T + DISC * 0.55, 0.40, 0, s, ox, oy)), side[v], INK, 1))
            out.append(poly(_pts(_ring(mode, cx, cy, T + DISC, 0.40, 0, s, ox, oy)), col, INK, 1.2)); tx, ty = P(cx, cy, T + DISC); out.append(label(tx, ty + 9, v, 24, 'middle', '#ffffff' if v == 'R' else INK, 800))
            if (r, c) in win: out.append(poly(_pts(_ring(mode, cx, cy, T + DISC, 0.52, 0, s, ox, oy)), 'none', '#ffffff', 5))
            elif last == (r, c): out.append(poly(_pts(_ring(mode, cx, cy, T + DISC, 0.52, 0, s, ox, oy)), 'none', INK, 3.5))
    out.append('</svg>'); return verify_svg(''.join(out))
def _pts(txt): return [tuple(float(v) for v in p.split(',')) for p in txt.split(' ')]
def alt_text(cells, last=None, win=None):
    n = {k: sum(1 for v in cells if v == k) for k in 'RY'}; parts = [f'Connect Four board, {ROWS} rows by {COLS} columns. Red {n["R"]} discs, Yellow {n["Y"]} discs.']
    if last and cells[last[0] * COLS + last[1]] in NAME: parts.append(f'Newest disc: {NAME[cells[last[0] * COLS + last[1]]]} in column {last[1] + 1}.')
    if win and cells[win[0][0] * COLS + win[0][1]] in NAME: parts.append(f'Four in a row for {NAME[cells[win[0][0] * COLS + win[0][1]]]}, from column {min(c for _, c in win) + 1} to column {max(c for _, c in win) + 1}.')
    return ' '.join(parts)
def table_text(cells): return 'Rows from the top (R red, Y yellow, . empty): ' + ' | '.join(f'row {r + 1}: ' + ' '.join('.' if cells[r * COLS + c] == ' ' else cells[r * COLS + c] for c in range(COLS)) for r in range(ROWS))
def connect_four(cells, last=None, win=None, title='', view='flat', version=1):
    """view: 'flat' (the front-on picture, default), 'oblique' (3D slab, board face stays a true rectangle) or 'iso' (true isometric). The result carries all three as variants; view picks the one shown first."""
    notes = []; cl = _cells(cells, notes)
    if version != 1: notes.append('Only version 1 exists; drawn as version 1.')
    lw = _cell(last, [], '') if last else None; ww = [w for w in (_cell(x, [], '') for x in (win or [])) if w] if win else None
    if win and (not ww or len(ww) != 4): notes.append('The winning line was not four valid cells and was left out.'); ww = None
    if last and not lw: notes.append('The last-move marker was not a valid cell and was left out.')
    if view not in _VIEWS: notes.append('view was not flat, oblique or iso; flat was used.'); view = 'flat'
    ttl = clean_text(title, 60, 'Connect Four'); res = {}
    for v in _VIEWS:
        svg = draw(cl, lw, ww) if v == 'flat' else draw3(cl, lw, ww, v); res[v] = finish('connect_four', ttl, svg, alt_text(cl, lw, ww) + ('' if v == 'flat' else f' Shown as a {"front-on 3D" if v == "oblique" else "isometric"} view.'), table_text(cl), notes)
    res['_default'] = view; return res
