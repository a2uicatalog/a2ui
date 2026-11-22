"""decision_tree, layout='flow': the top-down decision diagram (questions as grey boxes, outcomes as purple-outlined boxes, arrows, Yes/No words on the lines, a bold title of up to two lines and
a grey detail line under it). Built for the post figure that was first drawn by hand; the nested node contract is unchanged and three OPTIONAL node fields are added: edge (the word on the line from the
parent), detail (the grey second text) and outcome (true draws the purple box; default: a node without children). Called by decision_tree(); never used by the default layout.
Two themes. theme='light' (default): self-contained, fixed light colours plus ONE @media (prefers-color-scheme: dark) block inside the SVG (works in an <img>, so it is usable as an A2UI Image data URL) and it
passes the 'rich' output policy (res['policy'] == 'rich'). theme='css-vars': for INLINE embedding in a page whose CSS defines --surface, --surface-2, --border, --text and --muted: the same drawing with
fill and stroke values written var(--name, light fallback), the accessible title and description ids, and no background. The css-vars text is produced by replacing constants in a drawing that already
passed the rich policy; it is NOT admitted by any output policy (data_uri() refuses it), so it can never become an Image by accident. res['svg_img'] is always the self-contained one."""
import re
from . import common as C
from .rich import verify_rich
from .waterfall import note_result
PAD, CW_B, CW_D, TITLE_LINES, DETAIL_LINES, WRAP_T, WRAP_D, MINW, HGAP, VGAP, MX, TOP, ARROW = 24, 9.2, 7.6, 2, 4, 26, 26, 160, 20, 84, 20, 20, 9
ACCENT = '#6b5cff'
LIGHT = dict(bg='#ffffff', q='#f2f4f8', out='#ffffff', border='#d8dde6', text='#1c2230', muted='#5b6475')
DARK = dict(bg='#262d39', q='#2f3744', out='#373f4e', border='#4c5565', text='#eef1f5', muted='#a3acba', accent='#8f84ff')
VARS = {LIGHT['q']: ('--surface-2', LIGHT['q']), LIGHT['out']: ('--surface', LIGHT['out']), LIGHT['border']: ('--border', LIGHT['border']), LIGHT['text']: ('--text', LIGHT['text']), LIGHT['muted']: ('--muted', LIGHT['muted']), ACCENT: ('--accent', ACCENT)}
def wrap(s, width, max_lines):
    """Greedy word wrap on character counts; a word longer than width is split. Returns (lines, cut) where cut says text was dropped (the last line then ends with an ellipsis)."""
    lines = []; cur = ''
    for w in s.split():
        while len(w) > width:
            if cur: lines.append(cur); cur = ''
            lines.append(w[:width]); w = w[width:]
        if cur and len(cur) + 1 + len(w) > width: lines.append(cur); cur = w
        else: cur = (cur + ' ' + w).strip()
    if cur: lines.append(cur)
    if len(lines) <= max_lines: return lines, False
    keep = lines[:max_lines]; keep[-1] = keep[-1][:max(1, width - 1)].rstrip() + '…'; return keep, True
def _style():
    d = DARK
    rules = [('bg', f'fill:{d["bg"]}'), ('q', f'fill:{d["q"]};stroke:{d["border"]}'), ('out', f'fill:{d["out"]};stroke:{d["accent"]}'), ('tx', f'fill:{d["text"]}'), ('mu', f'fill:{d["muted"]}'), ('ln', f'stroke:{d["text"]}'), ('ar', f'fill:{d["text"]}')]
    return '<style>@media (prefers-color-scheme: dark){' + ''.join(f'.d3-{k}{{{v}}}' for k, v in rules) + '}</style>'
def draw_flow(flat, ttl, notes, theme, ids, leaves, levels, summary, table_of, text_of):
    """flat: parsed nodes (preorder, with text, depth, parent, kids, edge, detail, outcome). Returns {'tree': Result, '_default': 'tree'}. Never raises: a drawing the policy refuses becomes a note result."""
    cut = 0
    for n in flat:
        n['tl'], c1 = wrap(n['text'], WRAP_T, TITLE_LINES); n['dl'], c2 = wrap(n['detail'], WRAP_D, DETAIL_LINES) if n.get('detail') else ([], False); cut += c1 or c2
        n['isout'] = n['outcome'] if n['outcome'] is not None else not n['kids']
        n['w'] = max(MINW, max(len(x) for x in n['tl']) * CW_B + 2 * PAD, (max(len(x) for x in n['dl']) * CW_D + 2 * PAD) if n['dl'] else 0)
        n['h'] = 32 + 24 * (len(n['tl']) - 1) + (26 + 22 * (len(n['dl']) - 1) if n['dl'] else 0) + 22
    if cut: notes.append(f'{cut} labels or details were longer than the box holds ({TITLE_LINES} lines of {WRAP_T} and {DETAIL_LINES} lines of {WRAP_D} characters) and are drawn shortened with an ellipsis; the table keeps the full text.')
    roots = [n['i'] for n in flat if n['parent'] is None]; cur = [0.0]
    def place(i):
        n = flat[i]
        if not n['kids']: n['cx'] = cur[0] + n['w'] / 2; cur[0] += n['w'] + HGAP
        else:
            for k in n['kids']: place(k)
            n['cx'] = (flat[n['kids'][0]]['cx'] + flat[n['kids'][-1]]['cx']) / 2
    for r in roots: place(r)
    for d in range(levels):                                   # keep boxes of one level apart: push right whatever overlaps
        row = sorted((n for n in flat if n['depth'] == d), key=lambda n: n['cx']); edge = None
        for n in row:
            if edge is not None and n['cx'] - n['w'] / 2 < edge + HGAP: n['cx'] = edge + HGAP + n['w'] / 2
            edge = n['cx'] + n['w'] / 2
    rowh = [max(n['h'] for n in flat if n['depth'] == d) for d in range(levels)]; ytop = [TOP]
    for d in range(1, levels): ytop.append(ytop[-1] + rowh[d - 1] + VGAP)
    for n in flat: n['x'] = n['cx'] - n['w'] / 2; n['y'] = ytop[n['depth']]
    edges = []
    for n in flat:
        if n['parent'] is None: continue
        p = flat[n['parent']]; sx = min(max(p['cx'] + (n['cx'] - p['cx']) * .45, p['x'] + 24), p['x'] + p['w'] - 24); ex = min(max(n['cx'] + (p['cx'] - n['cx']) * .3, n['x'] + 24), n['x'] + n['w'] - 24)
        edges.append({'from': p['i'], 'to': n['i'], 'x1': sx, 'y1': p['y'] + p['h'], 'x2': ex, 'y2': n['y'], 'label': n.get('edge'), 'left': n['cx'] < p['cx']})
    for e in edges:
        e['lx'] = (e['x1'] + e['x2']) / 2 + (-10 if e['left'] else 10); e['ly'] = (e['y1'] + e['y2']) / 2 + 5; e['lw'] = len(e['label']) * CW_D if e['label'] else 0
    lo = min([n['x'] for n in flat] + [e['lx'] - e['lw'] if e['left'] else e['lx'] for e in edges if e['label']]); hi = max([n['x'] + n['w'] for n in flat] + [e['lx'] + (0 if e['left'] else e['lw']) for e in edges if e['label']])
    dx = MX - lo; Wd = int(hi - lo + 2 * MX + .999); Hd = int(ytop[-1] + rowh[-1] + MX + .999)
    for n in flat: n['x'] += dx; n['cx'] += dx
    for e in edges: e['x1'] += dx; e['x2'] += dx; e['lx'] += dx
    L = LIGHT; f = lambda v: f'{v:.1f}'
    body = '<g fill="none" stroke-width="2">'
    for n in flat:
        if n['isout']: body += f'<rect class="d3-out" x="{f(n["x"])}" y="{f(n["y"])}" width="{f(n["w"])}" height="{f(n["h"])}" rx="12" fill="{L["out"]}" stroke="{ACCENT}" stroke-width="3"/>'
        else: body += f'<rect class="d3-q" x="{f(n["x"])}" y="{f(n["y"])}" width="{f(n["w"])}" height="{f(n["h"])}" rx="12" fill="{L["q"]}" stroke="{L["border"]}"/>'
    for e in edges:
        x1, y1, x2, y2 = e['x1'], e['y1'], e['x2'], e['y2']; ln = max(1e-9, ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** .5); ux, uy = (x2 - x1) / ln, (y2 - y1) / ln; bx, by = x2 - ARROW * ux, y2 - ARROW * uy; nx, ny = -uy * ARROW * .5, ux * ARROW * .5
        body += f'<path class="d3-ln" d="M{f(x1)} {f(y1)}L{f(bx)} {f(by)}" stroke="{L["text"]}"/>' + f'<path class="d3-ar" d="M{f(x2)} {f(y2)}L{f(bx + nx)} {f(by + ny)}L{f(bx - nx)} {f(by - ny)}Z" fill="{L["text"]}" stroke="none"/>'
    body += '</g><g>'
    for n in flat:
        y = n['y'] + 32
        for k, s in enumerate(n['tl']): body += f'<text class="d3-tx" x="{f(n["cx"])}" y="{f(y + 24 * k)}" font-size="17" font-weight="700" text-anchor="middle" font-family="sans-serif" fill="{L["text"]}">{C.esc(s)}</text>'
        y += 24 * (len(n['tl']) - 1) + 26
        for k, s in enumerate(n['dl']): body += f'<text class="d3-mu" x="{f(n["cx"])}" y="{f(y + 22 * k)}" font-size="15" text-anchor="middle" font-family="sans-serif" fill="{L["muted"]}">{C.esc(s)}</text>'
    for e in edges:
        if e['label']: body += f'<text class="d3-mu" x="{f(e["lx"])}" y="{f(e["ly"])}" font-size="15" font-family="sans-serif" fill="{L["muted"]}" text-anchor="{"end" if e["left"] else "start"}">{C.esc(e["label"])}</text>'
    body += '</g>'
    label_ = C.esc(ttl or 'Decision tree')
    head = f'<svg xmlns="http://www.w3.org/2000/svg" width="{Wd}" height="{Hd}" viewBox="0 0 {Wd} {Hd}" role="img" aria-label="{label_}">' + _style() + f'<rect class="d3-bg" width="{Wd}" height="{Hd}" rx="24" fill="{L["bg"]}"/>'
    kind = 'decision_tree'; alt_body = summary + (' Notes: ' + ' '.join(notes) if notes else ''); title = C.plain(ttl or '')
    try: img = verify_rich(head + body + '</svg>')
    except C.SvgPolicyError as e:
        notes.append(f'The flow drawing was refused by the output policy ({C.plain(str(e))[:80]}).'); return {'tree': note_result(kind, ttl, 'The flow drawing could not be produced for this input.', notes), '_default': 'tree'}
    inline = None
    if theme == 'css-vars':
        s = re.sub(r'<style>.*?</style>', '', head + body + '</svg>'); s = re.sub(r'<rect class="d3-bg"[^>]*/>', '', s); s = re.sub(r' class="d3-[a-z]{1,8}"', '', s)
        for hexc, (name, fb) in VARS.items(): s = s.replace(f'="{hexc}"', f'="var({name}, {fb})"')
        iid = re.sub(r'[^A-Za-z0-9_-]', '', str(ids))[:12] or 'dt'
        s = re.sub(r'^<svg [^>]*>', f'<svg viewBox="0 0 {Wd} {Hd}" role="img" aria-labelledby="{iid}-t {iid}-d" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;max-width:{min(Wd, 1040)}px;font-family:sans-serif">'
                   f'<title id="{iid}-t">{C.esc(ttl or "Decision tree")}</title><desc id="{iid}-d">{C.esc(text_of["desc"])}</desc>', s)
        inline = s
    res = C.Result(kind=kind, title=title, svg=inline or img, summary=C.plain(summary), table=C.plain(table_of), notes=[C.plain(x) for x in notes],
                   alt=(f'Decision tree: {title}. {alt_body}' if title else f'Decision tree. {alt_body}'), policy='css-vars' if inline else 'rich')
    res['svg_img'] = img; res['edges'] = edges; res['nodes'] = flat; res['levels'] = levels; res['leaves'] = leaves; res['size'] = (Wd, Hd); res['theme'] = 'css-vars' if inline else 'light'
    res['text'] = text_of['plain']; res['text_html'] = text_of['html']
    return {'tree': res, '_default': 'tree'}
VW, VMX, VIND, VRAIL, VLABEL, VGAP2, VTOP, VTITLE_LINES, VDETAIL_LINES = 320, 10, 26, 14, 26, 22, 12, 3, 5
def draw_flow_v(flat, ttl, notes, theme, ids, leaves, levels, summary, table_of, text_of):
    """layout='flow-v': the same nodes, fields and themes as draw_flow, stacked top to bottom as an indented tree about VW (320) px wide, for phones. Each node is a box that starts one indent step to the right of its parent
    and ends at the same right edge; an elbow runs from the parent's left rail down to the child and into it with an arrowhead; the edge word sits on its own row above the child. Height grows with the number of nodes.
    Never raises: a drawing the policy refuses becomes a note result."""
    cut = 0
    for n in flat:
        n['x'] = VMX + n['depth'] * VIND; n['w'] = VW - VMX - n['x']; cw_t = max(8, int((n['w'] - 28) / CW_B)); cw_d = max(8, int((n['w'] - 28) / CW_D))
        n['tl'], c1 = wrap(n['text'], cw_t, VTITLE_LINES); n['dl'], c2 = wrap(n['detail'], cw_d, VDETAIL_LINES) if n.get('detail') else ([], False); cut += c1 or c2
        n['isout'] = n['outcome'] if n['outcome'] is not None else not n['kids']
        n['h'] = 32 + 24 * (len(n['tl']) - 1) + (26 + 22 * (len(n['dl']) - 1) if n['dl'] else 0) + 22; n['cx'] = n['x'] + n['w'] / 2
    if cut: notes.append(f'{cut} labels or details were longer than the box holds ({VTITLE_LINES} lines of about 24 and {VDETAIL_LINES} lines of about 30 characters) and are drawn shortened with an ellipsis; the table keeps the full text.')
    y = VTOP
    for n in flat:
        if n.get('edge') and n['parent'] is not None: y += VLABEL
        n['y'] = y; y += n['h'] + VGAP2
    Wd, Hd = VW, int(y - VGAP2 + VMX + .999)
    edges = []
    for n in flat:
        if n['parent'] is None: continue
        p = flat[n['parent']]; rx = p['x'] + VRAIL
        edges.append({'from': p['i'], 'to': n['i'], 'x1': rx, 'y1': p['y'] + p['h'], 'x2': n['x'], 'y2': n['y'] + n['h'] / 2, 'label': n.get('edge'), 'lx': n['x'] + 4, 'ly': n['y'] - 8, 'left': False, 'lw': len(n['edge']) * CW_D if n.get('edge') else 0})
    L = LIGHT; f = lambda v: f'{v:.1f}'
    body = '<g fill="none" stroke-width="2">'
    for n in flat:
        if n['isout']: body += f'<rect class="d3-out" x="{f(n["x"])}" y="{f(n["y"])}" width="{f(n["w"])}" height="{f(n["h"])}" rx="12" fill="{L["out"]}" stroke="{ACCENT}" stroke-width="3"/>'
        else: body += f'<rect class="d3-q" x="{f(n["x"])}" y="{f(n["y"])}" width="{f(n["w"])}" height="{f(n["h"])}" rx="12" fill="{L["q"]}" stroke="{L["border"]}"/>'
    for e in edges:
        x1, y1, x2, y2 = e['x1'], e['y1'], e['x2'], e['y2']
        body += f'<path class="d3-ln" d="M{f(x1)} {f(y1)}V{f(y2)}H{f(x2 - ARROW)}" stroke="{L["text"]}"/>' + f'<path class="d3-ar" d="M{f(x2)} {f(y2)}L{f(x2 - ARROW)} {f(y2 - ARROW * .5)}L{f(x2 - ARROW)} {f(y2 + ARROW * .5)}Z" fill="{L["text"]}" stroke="none"/>'
    body += '</g><g>'
    for n in flat:
        y = n['y'] + 32
        for k, s in enumerate(n['tl']): body += f'<text class="d3-tx" x="{f(n["cx"])}" y="{f(y + 24 * k)}" font-size="17" font-weight="700" text-anchor="middle" font-family="sans-serif" fill="{L["text"]}">{C.esc(s)}</text>'
        y += 24 * (len(n['tl']) - 1) + 26
        for k, s in enumerate(n['dl']): body += f'<text class="d3-mu" x="{f(n["cx"])}" y="{f(y + 22 * k)}" font-size="15" text-anchor="middle" font-family="sans-serif" fill="{L["muted"]}">{C.esc(s)}</text>'
    for e in edges:
        if e['label']: body += f'<text class="d3-mu" x="{f(e["lx"])}" y="{f(e["ly"])}" font-size="15" font-family="sans-serif" fill="{L["muted"]}" text-anchor="start">{C.esc(e["label"])}</text>'
    body += '</g>'
    label_ = C.esc(ttl or 'Decision tree')
    head = f'<svg xmlns="http://www.w3.org/2000/svg" width="{Wd}" height="{Hd}" viewBox="0 0 {Wd} {Hd}" role="img" aria-label="{label_}">' + _style() + f'<rect class="d3-bg" width="{Wd}" height="{Hd}" rx="24" fill="{L["bg"]}"/>'
    kind = 'decision_tree'; alt_body = summary + (' Notes: ' + ' '.join(notes) if notes else ''); title = C.plain(ttl or '')
    try: img = verify_rich(head + body + '</svg>')
    except C.SvgPolicyError as e:
        notes.append(f'The flow-v drawing was refused by the output policy ({C.plain(str(e))[:80]}).'); return {'tree': note_result(kind, ttl, 'The flow-v drawing could not be produced for this input.', notes), '_default': 'tree'}
    inline = None
    if theme == 'css-vars':
        s = re.sub(r'<style>.*?</style>', '', head + body + '</svg>'); s = re.sub(r'<rect class="d3-bg"[^>]*/>', '', s); s = re.sub(r' class="d3-[a-z]{1,8}"', '', s)
        for hexc, (name, fb) in VARS.items(): s = s.replace(f'="{hexc}"', f'="var({name}, {fb})"')
        iid = re.sub(r'[^A-Za-z0-9_-]', '', str(ids))[:12] or 'dt'
        s = re.sub(r'^<svg [^>]*>', f'<svg viewBox="0 0 {Wd} {Hd}" role="img" aria-labelledby="{iid}-t {iid}-d" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;max-width:{Wd}px;font-family:sans-serif">'
                   f'<title id="{iid}-t">{C.esc(ttl or "Decision tree")}</title><desc id="{iid}-d">{C.esc(text_of["desc"])}</desc>', s)
        inline = s
    res = C.Result(kind=kind, title=title, svg=inline or img, summary=C.plain(summary), table=C.plain(table_of), notes=[C.plain(x) for x in notes],
                   alt=(f'Decision tree: {title}. {alt_body}' if title else f'Decision tree. {alt_body}'), policy='css-vars' if inline else 'rich')
    res['svg_img'] = img; res['edges'] = edges; res['nodes'] = flat; res['levels'] = levels; res['leaves'] = leaves; res['size'] = (Wd, Hd); res['theme'] = 'css-vars' if inline else 'light'
    res['text'] = text_of['plain']; res['text_html'] = text_of['html']
    return {'tree': res, '_default': 'tree'}
