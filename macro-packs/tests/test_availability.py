"""The availability macro (booking-style slot grid): the picture read back cell by cell against the input, the tolerant reader (every bad input dropped and counted, never a crash), limits, determinism, the output policy, and escaping.
Run: python3 tests/test_availability.py   (stdlib only; no network, no model)."""
import sys, re, math, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent)); sys.dont_write_bytecode = True
import d3pack
from d3pack import common as C
from d3pack.demos_booking import DAYS, TIMES, BUSY
fails = []; n = 0
def ok(name, c):
    global n; n += 1
    if not c: fails.append(name); print('FAIL', name)
call = lambda **kw: d3pack.call('availability', kw, isolate=False)
def refused(**kw):
    try: call(**kw); return False
    except d3pack.MacroError: return True
texts = lambda svg: re.findall(r'<text [^>]*>([^<]*)</text>', svg)
r = call(days=DAYS, times=TIMES, busy=BUSY, selected=['2026-11-10', '11:00'], title='Platform office hours'); wk, dy = r['week'], r['day']
ok('both views come back, week by default, and both pass the default output policy', set(r) == {'week', 'day', '_default'} and r['_default'] == 'week' and C.verify_svg(wk['svg']) and C.verify_svg(dy['svg']))
t = texts(wk['svg']); nb = len({tuple(b) for b in BUSY})
ok(f'week read-back: {len(DAYS) * len(TIMES)} cells = {nb} Taken + 1 Your pick + {len(DAYS) * len(TIMES) - nb - 1} Open (each label also appears once in the legend)', t.count('Taken') == nb + 1 and t.count('Your pick') == 1 + 1 and t.count('Open') == len(DAYS) * len(TIMES) - nb - 1 + 1)
cells = [x for x in t if x in ('Open', 'Taken', 'Your pick')]
ok('week read-back: every grid cell says exactly one of Open, Taken or Your pick (colour is never the only signal), plus the legend', len(cells) == len(DAYS) * len(TIMES) + 3 and cells.count('Your pick') == 2)
free = wk['free']; ok('free slots per day are exactly the times not listed as busy and not the pick', all(free[d] == [x for x in TIMES if [d, x] not in BUSY and (d, x) != ('2026-11-10', '11:00')] for d in DAYS))
ok('the header of each day column states the open count that matches', all(f'{len(free[d])} open' in t for d in DAYS))
ok('the table and summary list every open slot and the pick', all(x in wk['table'] for x in free[DAYS[0]]) and 'Your pick: Tue 10 Nov at 11:00' in wk['summary'] and f'{sum(len(v) for v in free.values())} of {len(DAYS) * len(TIMES)} slots are open' in wk['summary'] and '22 of 40 slots are open' in wk['summary'])
td = texts(dy['svg']); ok('day read-back: one row per time, one status each, for the first day with a free slot', td.count('Taken') == len([1 for x in TIMES if [DAYS[0], x] in BUSY]) + 1 and td.count('Open') == len([1 for x in TIMES if [DAYS[0], x] not in BUSY]) + 1 and dy['day'] == DAYS[0])
d2 = call(days=DAYS, times=TIMES, busy=BUSY, selected=['2026-11-10', '11:00'], view='day', day='2026-11-10'); ok('view=day makes the day the default and day= picks the date, with the pick shown', d2['_default'] == 'day' and d2['day']['day'] == '2026-11-10' and texts(d2['day']['svg']).count('Your pick') == 2)
ok('deterministic: the same input gives byte-identical output', call(days=DAYS, times=TIMES, busy=BUSY)['week']['svg'] == call(days=DAYS, times=TIMES, busy=BUSY)['week']['svg'])
# tolerant reader
x = call(days=['2026-11-09', '2026-02-30', 'tomorrow', 5, None, '2026-11-09', '2026-11-10'], times=['09:00', '25:00', '9:00', '09:00', 7, '10:30'], busy=[['2026-11-09', '09:00'], ['2030-01-01', '09:00'], 'x', {'date': '2026-11-10', 'time': '10:30'}, {'date': '2026-11-10'}, None, 5])
ok('bad and repeated days and times are dropped and counted once each', x['week']['free'] == {'2026-11-09': ['10:30'], '2026-11-10': ['09:00']} and any('5 days were left out' in s for s in x['week']['notes']) and any('4 times were left out' in s for s in x['week']['notes']))
ok('busy pairs: dict form accepted, off-grid and malformed counted', any('5 busy entries were left out' in s for s in x['week']['notes']))
z = call(days=DAYS[:2], times=TIMES[:3], busy=[[DAYS[0], t] for t in TIMES[:3]]); ok('a fully booked day says so in the table, and the day view skips to the first day with a free slot', 'Mon 9 Nov: no open slot' in z['week']['table'] and z['day']['day'] == DAYS[1] and call(days=DAYS[:2], times=TIMES[:3], busy=[[DAYS[0], t] for t in TIMES[:3]], day=DAYS[0])['day']['summary'].startswith('Mon 9 Nov: no open slot'))
y = call(days=DAYS, times=TIMES, selected=['2030-01-01', '09:00']); ok('a selection off the grid is dropped with a note', 'Your pick' not in y['week']['summary'] and any('selection is not a date and time on the grid' in s for s in y['week']['notes']))
y = call(days=DAYS, times=TIMES, busy=[[DAYS[0], '09:00']], selected=[DAYS[0], '09:00']); ok('a selection that is also busy is shown as taken, with a note', texts(y['week']['svg']).count('Your pick') == 1 and any('also listed as busy' in s for s in y['week']['notes']))
y = call(days=DAYS, times=TIMES, view='sideways', day='1999-01-01'); ok('an unknown view is drawn as the week and a day outside the days falls back, both with notes', y['_default'] == 'week' and any('view must be' in s for s in y['week']['notes']) and any('day is not one of the days' in s for s in y['week']['notes']))
y = call(days=[f'2026-11-{d:02d}' for d in range(1, 15)], times=[f'{h:02d}:00' for h in range(0, 24)]); ok('more than 7 days and 12 times are capped with notes and still pass the policy', len(y['week']['free']) == 7 and all(len(v) == 12 for v in y['week']['free'].values()) and any('beyond the 7th' in s for s in y['week']['notes']) and any('beyond the 12th' in s for s in y['week']['notes']) and len(y['week']['svg']) < 80000)
for name, kw in (('days not a list', dict(days='2026-11-09', times=TIMES)), ('times not a list', dict(days=DAYS, times=None)), ('no valid day', dict(days=['x'], times=TIMES)), ('no valid time', dict(days=DAYS, times=['x'])), ('empty', dict(days=[], times=[]))): ok(f'refused: {name}', refused(**kw))
y = call(days=DAYS, times=TIMES, busy='x', selected=7, view=None, day=5, title=None); ok('wrong types for the optional inputs never crash', y['week']['svg'].startswith('<svg'))
y = call(days=DAYS, times=TIMES, title='<script>alert(1)</script>&"‮\x00x'); ok('a hostile title is escaped and stripped, and the SVG is still valid', '<script' not in y['week']['svg'] and C.verify_svg(y['week']['svg']) and '‮' not in y['week']['svg'])
y = call(days=DAYS, times=TIMES, version=99); ok('a newer contract version is drawn as version 1 with a note', any('Contract version 99' in s for s in y['week']['notes']))
y = call(days=DAYS, times=TIMES, busy=[[d, t] for d in DAYS for t in TIMES]); ok('everything busy: every cell Taken, summary says 0 open, no crash', texts(y['week']['svg']).count('Open') == 1 and '0 of 40 slots are open' in y['week']['summary'])
ok('the through-call path is isolated-safe: isolated and in-process results are identical', d3pack.call('availability', dict(days=DAYS, times=TIMES, busy=BUSY), isolate=True)['week']['svg'] == call(days=DAYS, times=TIMES, busy=BUSY)['week']['svg'])
print(f'availability tests: {n} checks, {len(fails)} failed'); sys.exit(1 if fails else 0)
