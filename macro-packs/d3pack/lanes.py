"""Contract source: atoms/schema.yaml (re-checked against it; limits and tolerant-reader rules match). swimlane macro (the catalogue has no atom named 'architecture lanes'; `swimlane` is the one that matches: 2-4 lanes, up to 12 numbered tasks, automatic grid layout).
Contract of the swimlane atom: title, roles (2-4 strings, max 24), phases (2-5 strings, max 24), tasks (up to 12) of {role, phase, task (max 60)}. Rows are roles, columns are phases, at most two tasks per cell.
Numbers follow the order of the usable tasks. Returns {'swimlane': Result}."""
from .common import *
from .waterfall import safe_text
def wrap(text, chars, maxlines):
    words = text.split(); lines = []; cur = ''
    for w in words:
        while len(w) > chars: 
            if cur: lines.append(cur); cur = ''
            lines.append(w[:chars]); w = w[chars:]
        if cur and len(cur) + 1 + len(w) > chars: lines.append(cur); cur = w
        else: cur = (cur + ' ' + w).strip()
    if cur: lines.append(cur)
    if len(lines) > maxlines: lines = lines[:maxlines]; lines[-1] = lines[-1][:max(1, chars - 1)].rstrip() + '…'
    return lines
def _list(x, lo, hi, maxlen, name, notes):
    if not isinstance(x, list): raise ValueError(f'{name} must be a list')
    if len(x) > hi: notes.append(f'{len(x) - hi} {name} beyond the {hi}th were not drawn.'); x = x[:hi]
    out = []; seen = set(); bad = 0
    for v in x:
        c = safe_text(v, maxlen)
        if c is None or c in seen: bad += 1; continue
        seen.add(c); out.append(c)
    if bad: notes.append(f'{bad} {name} were left out (empty or repeated).')
    if len(out) < lo: raise ValueError(f'a swimlane needs at least {lo} usable {name}')
    return out
def swimlane(roles, phases, tasks, title='', version=1):
    notes = []; ttl = safe_text(title, 80, '') or ''
    rs = _list(roles, 2, 4, 24, 'roles', notes); ps = _list(phases, 2, 5, 24, 'phases', notes)
    if not isinstance(tasks, list): raise ValueError('tasks must be a list')
    if len(tasks) > 12: notes.append(f'{len(tasks) - 12} tasks beyond the 12th were not drawn.'); tasks = tasks[:12]
    ts = []; bad = 0; full = 0; cell = {}
    for t in tasks:
        if not isinstance(t, dict): bad += 1; continue
        ro, ph, tx = safe_text(t.get('role'), 24), safe_text(t.get('phase'), 24), safe_text(t.get('task'), 60)
        if ro not in rs or ph not in ps or tx is None: bad += 1; continue
        if cell.get((ro, ph), 0) >= 2: full += 1; continue
        cell[(ro, ph)] = cell.get((ro, ph), 0) + 1; ts.append({'n': len(ts) + 1, 'role': ro, 'phase': ph, 'task': tx})
    if bad: notes.append(f'{bad} tasks were left out (not an object, a role or phase that is not listed, or no task text).')
    if full: notes.append(f'{full} tasks were left out because their cell already held two.')
    if isinstance(version, int) and not isinstance(version, bool) and version > 1: notes.append(f'Contract version {min(version, 10**9)} is drawn as version 1.')
    if not ts: raise ValueError('a swimlane needs at least 1 usable task')
    LW, T = 130, 56; gw = (W - LW - 12) / len(ps); gh = (H - T - 12) / len(rs); body = ''
    for j, p in enumerate(ps): body += label(LW + gw * (j + .5), 34, p[:max(4, int(gw / 8))], 14, 'middle', MUTED, 700)
    for i, ro in enumerate(rs):
        y = T + gh * i; body += f'<rect x="8" y="{y + 3:.2f}" width="{W - 16}" height="{gh - 6:.2f}" rx="12" fill="{blend(PAL[i % 8], .88)}"/><rect x="8" y="{y + 3:.2f}" width="{LW - 14}" height="{gh - 6:.2f}" rx="12" fill="{PAL[i % 8]}"/>'
        ls = wrap(ro, 12, 3)
        for k, l in enumerate(ls): body += label(8 + (LW - 14) / 2, y + gh / 2 + (k - (len(ls) - 1) / 2) * 18 + 5, l, 14, 'middle', text_on(PAL[i % 8]), 700)
    pos = {}; cut = 0
    for t in ts:
        i = rs.index(t['role']); j = ps.index(t['phase']); same = [u for u in ts if u['role'] == t['role'] and u['phase'] == t['phase']]; k = same.index(t); c = len(same)
        ch = (gh - 14 - (c - 1) * 6) / c; x = LW + gw * j + 4; y = T + gh * i + 7 + k * (ch + 6); cw = gw - 8; chars = max(4, int((cw - 36) / 7.4)); lines = wrap(t['task'], chars, max(1, int((ch - 8) / 17)))
        pos[t['n']] = (x, y, cw, ch); cut += 1 if ' '.join(lines) != ' '.join(t['task'].split()) else 0
        body += f'<rect x="{x:.2f}" y="{y:.2f}" width="{cw:.2f}" height="{ch:.2f}" rx="10" fill="{FACE}" stroke="{PAL[i % 8]}" stroke-width="2"><title>{t["n"]}. {esc(t["task"])}</title></rect><circle cx="{x + 16:.2f}" cy="{y + 16:.2f}" r="12" fill="{PAL[i % 8]}"/>'
        body += label(x + 16, y + 21, str(t['n']), 14, 'middle', text_on(PAL[i % 8]), 700)
        for q, l in enumerate(lines): body += label(x + 34, y + 21 + q * 17, l, 14, 'start')
    if cut: notes.append(f'{cut} task texts are shortened inside their cards; the table has them in full.')
    byrole = {ro: sum(1 for t in ts if t['role'] == ro) for ro in rs}; busy = max(rs, key=lambda ro: byrole[ro])
    summary = f'{len(rs)} roles, {len(ps)} phases, {len(ts)} numbered tasks; {busy} has the most ({byrole[busy]}).'
    tab = '; '.join(f'{t["n"]}. {t["role"]}, {t["phase"]}: {t["task"]}' for t in ts)
    r = finish('swimlane', ttl, svg(body, ('Swimlane' + (': ' + ttl if ttl else '') + ', roles ' + ', '.join(rs) + ', phases ' + ', '.join(ps))[:280]), summary, 'Roles: ' + ', '.join(rs) + '. Phases: ' + ', '.join(ps) + '. Tasks: ' + tab, notes); r['tasks'] = ts; r['roles'] = rs; r['phases'] = ps; r['cards'] = pos
    return {'swimlane': r, '_default': 'swimlane'}
