"""availability: a booking-style slot grid, the pack's first scheduling macro. Input: days (ISO dates, at most 7), times (HH:MM, at most 12), busy ([date, time] pairs or {date, time} objects), selected (one pair or None), view ('week' or 'day') and day (for the day view).
Tolerant reader like the rest of the pack: what cannot be used is dropped and counted in a note (bad dates and times, busy pairs outside the grid, a selection outside the grid); a wrong `view` is drawn as the week. Returns BOTH views as variants,
{'week': Result, 'day': Result, '_default': view}, so a caller that builds a booking flow (pick a day, then a time) draws each step from one call. Colour is never the only signal: every cell says Open, Taken or Your pick."""
import datetime as dt, re
from .common import *
from .waterfall import safe_text
MAX_DAYS, MAX_TIMES = 7, 12
_DAY, _TIME = re.compile(r'\d{4}-\d{2}-\d{2}', re.ASCII), re.compile(r'(?:[01]\d|2[0-3]):[0-5]\d', re.ASCII)
WD, MON = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
OPEN, TAKEN, PICK, EDGE = '#e6f4ea', '#e3e5ee', '#4b4acf', '#b9c0d8'
def _date(v):
    if not (isinstance(v, str) and _DAY.fullmatch(v)): return None
    try: return dt.date.fromisoformat(v)
    except ValueError: return None
def _pair(v):
    if isinstance(v, dict): v = [v.get('date'), v.get('time')]
    if isinstance(v, (list, tuple)) and len(v) == 2 and _date(v[0]) and isinstance(v[1], str) and _TIME.fullmatch(v[1]): return (v[0], v[1])
    return None
def label_day(iso, long=False): d = _date(iso); return f'{WD[d.weekday()]} {d.day} {MON[d.month - 1]}' if long else f'{WD[d.weekday()]} {d.day}'
def availability(days, times, busy=None, selected=None, view='week', day=None, title='', version=1):
    notes = []; ttl = safe_text(title, 80, '') or ''
    if isinstance(version, int) and not isinstance(version, bool) and version > 1: notes.append(f'Contract version {min(version, 10**9)} is drawn as version 1.')
    if not isinstance(days, list) or not isinstance(times, list): raise ValueError('days and times must be lists')
    ds, bad = [], 0
    for v in days:
        if _date(v) and v not in ds: ds.append(v)
        else: bad += 1
    if bad: notes.append(f'{bad} days were left out (not a date like 2026-11-09, or repeated).')
    if len(ds) > MAX_DAYS: notes.append(f'{len(ds) - MAX_DAYS} days beyond the {MAX_DAYS}th were not drawn.'); ds = ds[:MAX_DAYS]
    ts, bad = [], 0
    for v in times:
        if isinstance(v, str) and _TIME.fullmatch(v) and v not in ts: ts.append(v)
        else: bad += 1
    if bad: notes.append(f'{bad} times were left out (not a time like 09:30, or repeated).')
    if len(ts) > MAX_TIMES: notes.append(f'{len(ts) - MAX_TIMES} times beyond the {MAX_TIMES}th were not drawn.'); ts = ts[:MAX_TIMES]
    if not ds or not ts: raise ValueError('there must be at least one valid day and one valid time')
    ts.sort(); grid = {(d, t) for d in ds for t in ts}; bs, off = set(), 0
    for v in (busy if isinstance(busy, list) else []):
        p = _pair(v)
        if p and p in grid: bs.add(p)
        else: off += 1
    if off: notes.append(f'{off} busy entries were left out (not a date and time on the grid).')
    sel = None
    if selected is not None:
        p = _pair(selected)
        if p and p in grid: sel = p
        else: notes.append('The selection is not a date and time on the grid, so none is shown.')
    if sel in bs: notes.append('The selected slot is also listed as busy; it is shown as taken.'); sel = None
    free = {d: [t for t in ts if (d, t) not in bs and (d, t) != sel] for d in ds}; nfree = sum(len(v) for v in free.values())      # the pick is shown as "Your pick", so it is not counted as open
    if view not in ('week', 'day'): notes.append('view must be week or day; the week is drawn.'); view = 'week'
    dd = day if day in ds else next((d for d in ds if free[d]), ds[0])
    if day is not None and day not in ds: notes.append('day is not one of the days; the first day with a free slot is drawn.')
    head = ttl or 'Availability'
    wk = _week(ds, ts, bs, sel, free, head, notes); dy = _day(dd, ts, bs, sel, free[dd], head, notes)
    summary = f'{len(ds)} days, {len(ts)} times a day; {nfree} of {len(ds) * len(ts)} slots are open.' + (f' Your pick: {label_day(sel[0], True)} at {sel[1]}.' if sel else '')
    table = '; '.join(f'{label_day(d, True)}: ' + (', '.join(free[d]) if free[d] else 'no open slot') for d in ds)
    r1 = finish('availability', head, wk, summary, table, notes); r2 = finish('availability', f'{head}: {label_day(dd, True)}', dy, f'{label_day(dd, True)}: ' + (f'{len(free[dd])} of {len(ts)} slots open.' if free[dd] else 'no open slot.') + (f' Your pick: {sel[1]}.' if sel and sel[0] == dd else ''), table, notes)
    r1['free'] = free; r2['free'] = free; r1['day'] = dd; r2['day'] = dd
    return {'week': r1, 'day': r2, '_default': view}
def _cell(x, y, w, h, st, text):
    fill, ink, edge = (PICK, '#ffffff', PICK) if st == 'pick' else (TAKEN, MUTED, TAKEN) if st == 'taken' else (OPEN, INK, '#5f8a1f')
    return f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" rx="6" fill="{fill}" stroke="{edge}" stroke-width="1"/>' + label(x + w / 2, y + h / 2 + 4.5, text, 13, 'middle', ink, 700 if st == 'pick' else 400)
def _legend(y):
    return ''.join(f'<rect x="{x}" y="{y}" width="14" height="14" rx="3" fill="{f}" stroke="{e}"/>' + label(x + 20, y + 12, t, 13, 'start', MUTED) for x, f, e, t in ((60, OPEN, '#5f8a1f', 'Open'), (150, TAKEN, TAKEN, 'Taken'), (250, PICK, PICK, 'Your pick')))
def _week(ds, ts, bs, sel, free, head, notes):
    w, h = 720, 120 + 38 * len(ts); L, T = 70, 74; cw = (w - L - 20) / len(ds); rh = 38
    b = label(w / 2, 32, head, 22, 'middle', INK, 700)
    for i, d in enumerate(ds): b += label(L + cw * (i + .5), T - 24, label_day(d), 15, 'middle', INK, 700) + label(L + cw * (i + .5), T - 8, f'{len(free[d])} open', 13, 'middle', MUTED)
    for j, t in enumerate(ts):
        b += label(L - 10, T + rh * j + rh / 2 + 5, t, 13, 'end', MUTED)
        for i, d in enumerate(ds): b += _cell(L + cw * i + 3, T + rh * j + 3, cw - 6, rh - 6, 'pick' if sel == (d, t) else 'taken' if (d, t) in bs else 'open', 'Your pick' if sel == (d, t) else 'Taken' if (d, t) in bs else 'Open')
    return svg(b + _legend(h - 26), f'Week availability: {len(ds)} days, {len(ts)} times'[:200], w, h)
def _day(d, ts, bs, sel, free, head, notes):
    w, h = 720, 110 + 44 * len(ts); T = 78
    b = label(w / 2, 32, head, 22, 'middle', INK, 700) + label(w / 2, 58, label_day(d, True), 16, 'middle', MUTED)
    for j, t in enumerate(ts):
        st = 'pick' if sel == (d, t) else 'taken' if (d, t) in bs else 'open'; y = T + 44 * j
        b += label(48, y + 27, t, 15, 'end', INK, 700) + _cell(60, y + 3, w - 80, 38, st, 'Your pick' if st == 'pick' else 'Taken' if st == 'taken' else 'Open')
    return svg(b + _legend(h - 26), f'Day availability for {label_day(d, True)}: {len(free)} of {len(ts)} times open'[:200], w, h)
