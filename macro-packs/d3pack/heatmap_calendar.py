"""heatmap_calendar macro: same contract as the heatmap_calendar atom (data [{date 'YYYY-MM-DD', count}], months default 3 (1..12), color_scale, unit, title); `version` is accepted (a higher whole number is drawn as 1, noted).
Robust reading: at most 5000 entries are read (the rest noted), bad entries are counted in ONE note (not one per entry), counts must be finite and 0..1e12, dates are ASCII YYYY-MM-DD and real. The drawing degrades before the
output policy refuses it: first the per-day hover titles are left out, then the numbers inside the cells (the table keeps every day); each loss is noted."""
import calendar, datetime as dt, re
from .common import *
from .waterfall import safe_text, fit_svg
CARBON = ['#edf5ff', '#d0e2ff', '#a6c8ff', '#78a9ff', '#4589ff', '#0f62fe', '#0043ce']
MAX_ENTRIES = 5000
def heatmap_calendar(data, months=3, color_scale=None, unit='', title='', version=1):
    notes = []; u = safe_text(unit, 12, '') or ''; ttl = safe_text(title, 80, '') or ''
    if not isinstance(data, list): raise ValueError('data must be a list')
    if len(data) > MAX_ENTRIES: notes.append(f'{len(data) - MAX_ENTRIES} entries beyond the {MAX_ENTRIES}th were not read.'); data = data[:MAX_ENTRIES]
    cnt = {}; bad = 0
    for d in data:
        day = None
        if isinstance(d, dict) and isinstance(d.get('date'), str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', d['date'], re.ASCII):
            v = finite(d.get('count'), 0, 1e12)
            if v is not None:
                try: day = dt.date.fromisoformat(d['date'])
                except ValueError: day = None
        if day is None: bad += 1; continue
        cnt[day] = cnt.get(day, 0) + v
    if bad: notes.append(f'{bad} entries were left out (each needs a real date YYYY-MM-DD and a count from 0 to 1e12).')
    if isinstance(version, int) and not isinstance(version, bool) and version > 1: notes.append(f'Contract version {min(version, 10**9)} is drawn as version 1.')
    if not cnt: raise ValueError('no usable entries')
    mv = finite(months, -1e15, 1e15); m = int(mv) if mv is not None and mv == int(mv) else 3
    if mv is None or mv != int(mv): notes.append('months was not a whole number; 3 is used.')
    elif m < 1 or m > 12: notes.append(f'months {m} was clamped to {min(12, max(1, m))}.'); m = min(12, max(1, m))
    scale = [c for c in color_scale if isinstance(c, str) and re.fullmatch(r'#[0-9a-fA-F]{6}', c)] if isinstance(color_scale, list) else []
    if color_scale and len(scale) < 2: notes.append('color_scale needs at least 2 hex colours; the default scale is used.'); scale = []
    scale = scale or CARBON; last = max(cnt); ym = [(last.year, last.month)]
    for _ in range(m - 1): y, mo = ym[0]; ym.insert(0, (y - 1, 12) if mo == 1 else (y, mo - 1))
    shown = {d: v for d, v in cnt.items() if (d.year, d.month) in ym}; vmax = max(shown.values()) if shown else 0
    outside = sum(1 for d in cnt if (d.year, d.month) not in ym)
    if outside: notes.append(f'{outside} dates fall outside the {m} months shown.')
    def colour(v): return scale[0] if vmax <= 0 or v <= 0 else scale[min(len(scale) - 1, 1 + int((len(scale) - 1) * v / vmax - 1e-9))]
    per_row = 3 if m > 2 else m; rows = math.ceil(m / per_row); cell = 26; mw = 7 * cell; gap = 24; x0 = (W - (per_row * mw + (per_row - 1) * gap)) / 2; hh = 70 + (rows - 1) * 250 + 6 * cell + 60
    def draw(lvl):
        body = ''
        for i, (y, mo) in enumerate(ym):
            r, c = divmod(i, per_row); mx = x0 + c * (mw + gap); my = 70 + r * 250; first = dt.date(y, mo, 1); off = first.weekday()   # Monday = 0
            body += label(mx + mw / 2, my - 30, f'{calendar.month_name[mo]} {y}', 20, weight=700)
            for k, nm in enumerate('MTWTFSS'): body += label(mx + k * cell + cell / 2, my - 8, nm, 14, fill=MUTED)
            for day in range(1, calendar.monthrange(y, mo)[1] + 1):
                d = dt.date(y, mo, day); idx = off + day - 1; wk, wd = divmod(idx, 7); v = shown.get(d, 0); col = colour(v)
                body += f'<rect x="{mx + wd * cell + 1:.1f}" y="{my + wk * cell + 1:.1f}" width="{cell - 2}" height="{cell - 2}" rx="4" fill="{col}">' + (f'<title>{d.isoformat()}: {fmt(v)}{(" " + esc(u)) if u else ""}</title>' if lvl == 0 else '') + '</rect>'
                if v > 0 and lvl < 2: body += label(mx + wd * cell + cell / 2, my + wk * cell + cell / 2 + 5, fmt(v), 12, fill=text_on(col))
        body += label(W / 2, hh - 20, 'darker = more' + (f' ({u})' if u else ''), 15, fill=MUTED)
        return svg(body, f'Calendar heatmap, {calendar.month_name[ym[0][1]]} {ym[0][0]} to {calendar.month_name[ym[-1][1]]} {ym[-1][0]}', W, hh)
    tot = sum(shown.values()); busiest = max(shown, key=shown.get) if shown else None
    tab = '; '.join(f'{d.isoformat()} {fmt(v)}' for d, v in sorted(shown.items()))
    summary = f"{len(ym)} months ({calendar.month_name[ym[0][1]]} {ym[0][0]} to {calendar.month_name[ym[-1][1]]} {ym[-1][0]}): total {fmt(tot)}{(' ' + u) if u else ''} over {len(shown)} active days; busiest day {busiest.isoformat()} ({fmt(shown[busiest])})." if shown else f'{len(ym)} months, no active days in them.'
    r = finish('heatmap_calendar', ttl, fit_svg(draw, notes), summary, tab, notes, u); r['shown'] = shown; r['months'] = ym; return {'calendar': r, '_default': 'calendar'}
