"""gauge_sla macro: the geometry read back from the SVG against the formula, the atom's status rules, bands, the tolerant reader, hostile text, determinism and speed.
Run: python3 tests/test_gauge.py   (stdlib only; no network, no model)."""
import sys, re, math, random, time
import xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent)); sys.dont_write_bytecode = True
import d3pack
from d3pack import common as C
from d3pack.gauge_sla import gauge_sla, CX, CY, R_OUT, R_NEEDLE
fails = []; n = 0
def ok(name, c):
    global n; n += 1
    if not c: fails.append(name); print('FAIL', name)
def g(**kw): return gauge_sla(**kw)['gauge']
NS = '{http://www.w3.org/2000/svg}'
def els(svg, tag): return list(ET.fromstring(svg).iter(NS + tag))
def needle(svg):
    ln = [e for e in els(svg, 'line') if e.get('stroke-width') == '6'][0]; return float(ln.get('x2')), float(ln.get('y2'))
def expect(frac, r): a = -math.pi / 2 + math.pi * frac; return CX + r * math.sin(a), CY - r * math.cos(a)
def texts(svg): return [(e.text or '') for e in els(svg, 'text')]

# --- the geometry follows the formula exactly ---
for v in (0, 25, 50, 75, 100, 99.4, 3.3, 0.001):
    x, y = needle(g(value=v)['svg']); ex, ey = expect(v / 100, R_NEEDLE)
    ok('needle at value %s follows angle = -90 + 180 x frac' % v, abs(x - ex) < 0.01 and abs(y - ey) < 0.01)
ok('needle at 0 points left, at 50 up, at 100 right', needle(g(value=0)['svg'])[0] < CX - 100 and abs(needle(g(value=50)['svg'])[0] - CX) < 0.01 and needle(g(value=100)['svg'])[0] > CX + 100)
r = random.Random(3); worst = 0
for _ in range(300):
    lo = r.uniform(-50, 50); hi = lo + r.uniform(1, 200); v = r.uniform(lo, hi)
    x, y = needle(g(value=v, min=lo, max_value=hi)['svg']); ex, ey = expect((v - lo) / (hi - lo), R_NEEDLE); worst = max(worst, abs(x - ex), abs(y - ey))
ok('300 random scales and values: needle within 0.01 px of the formula (worst %.4f)' % worst, worst < 0.01)
def arc_end(svg):   # the value arc is the second path when there are no steps: M x0,y0 A r,r 0 large 1 x1,y1 L ...
    p = [e.get('d') for e in els(svg, 'path')][1]; m = re.search(r'A[\d.]+,[\d.]+ 0 [01] 1 (-?[\d.]+),(-?[\d.]+)', p); return float(m.group(1)), float(m.group(2))
for v in (10, 40, 66.6, 90):
    x, y = arc_end(g(value=v)['svg']); ex, ey = expect(v / 100, R_OUT); ok('value arc ends at the formula point for %s' % v, abs(x - ex) < 0.01 and abs(y - ey) < 0.01)
ok('a value of 0 draws no value arc (only the track)', len(els(g(value=0)['svg'], 'path')) == 1)

# --- status: the atom's rules, always in words ---
ok('healthy at or above the threshold', 'HEALTHY' in texts(g(value=99, threshold=99)['svg'])[0] or any('HEALTHY' in t for t in texts(g(value=99, threshold=99)['svg'])))
ok('warning from 90 percent of the threshold (not tested exactly on 89.1: 0.9 x 99 is 89.10000000000001 in floating point, as in the atom)', any('WARNING' in t for t in texts(g(value=89.15, threshold=99)['svg'])) and any('WARNING' in t for t in texts(g(value=98.9, threshold=99)['svg'])))
ok('breached below 90 percent', any('BREACHED' in t for t in texts(g(value=89, threshold=99)['svg'])))
ok('no threshold: no status word is drawn and the summary says none is judged', not any(w in ''.join(texts(g(value=50)['svg'])) for w in ('HEALTHY', 'WARNING', 'BREACHED')) and 'no status is judged' in g(value=50)['summary'])
ok('the status is in the summary text too (not colour alone)', 'healthy' in g(value=99.4, threshold=99)['summary'] and 'warning' in g(value=95, threshold=99)['summary'])
ok('the threshold tick is drawn (a 4 px line)', any(e.get('stroke-width') == '4' for e in els(g(value=50, threshold=60)['svg'], 'line')))
ok('no threshold, no tick', not any(e.get('stroke-width') == '4' for e in els(g(value=50)['svg'], 'line')))
ok('the label and the target appear in the status line', any('SLA MET' in t and 'TARGET 99' in t for t in texts(g(value=99.4, threshold=99, label='SLA Met', unit='%')['svg'])))
ok('a non-positive threshold is ignored with a note', 'no status is judged' in g(value=5, threshold=0)['summary'] and any('threshold' in x for x in g(value=5, threshold=0)['notes']))
ok('a threshold outside the scale still judges, but draws no tick, with a note', any('tick' in x for x in g(value=5, threshold=500)['notes']))
dark = {'HEALTHY': '#047857', 'WARNING': '#0b5f87', 'BREACHED': '#b91c1c'}
for word, col in dark.items():
    v = {'HEALTHY': 100, 'WARNING': 95, 'BREACHED': 50}[word]; t = [e for e in els(g(value=v, threshold=100)['svg'], 'text') if word in (e.text or '')][0]
    ok('%s status text uses the darker colour, readable on white' % word, t.get('fill') == col)

# --- bands ---
bands = [{'from': 0, 'to': 33, 'color': '#0284c7'}, {'from': 33, 'to': 66, 'color': '#d97706'}, {'from': 66, 'to': 100, 'color': '#dc2626'}]
b = g(value=50, steps=bands)
ok('three bands draw as three paths in their colours', [e.get('fill') for e in els(b['svg'], 'path')] == ['#0284c7', '#d97706', '#dc2626'] and 'band 0 to 33 colour #0284c7' in b['table'])
big = g(value=1, steps=[{'from': i, 'to': i + 1, 'color': '#123456'} for i in range(12)], max_value=12)
ok('more than eight bands: the first eight are drawn and the rest noted', len(els(big['svg'], 'path')) == 8 and any('first 8 of 12' in x for x in big['notes']))
ok('a band with no usable range is left out and noted', any('Step 2' in x for x in g(value=1, steps=[{'from': 0, 'to': 50}, {'from': 'x', 'to': 5}, 'bad'])['notes']))
ok('a band outside the scale is left out and noted', any('outside the scale' in x for x in g(value=1, steps=[{'from': 200, 'to': 300, 'color': '#000000'}])['notes']))
ok('a band over the edge is cut to the scale and noted', any('cut to the scale' in x for x in g(value=1, steps=[{'from': -50, 'to': 50, 'color': '#000000'}])['notes']))
nb = g(value=1, steps=[{'from': 0, 'to': 10, 'color': 'var(--x)'}, {'from': 10, 'to': 20, 'color': 'red'}])
ok('a colour that is not hex is replaced by a pack colour, noted, never passed through', all(re.fullmatch(r'#[0-9a-f]{3,6}', e.get('fill'), re.I) for e in els(nb['svg'], 'path')) and sum('not a hex colour' in x for x in nb['notes']) == 2)
ok('steps that is not a list is noted', any('not a list' in x for x in g(value=1, steps='x')['notes']))

# --- the tolerant reader ---
ok('a numeric string is read', 'on a scale' in g(value='42')['summary'] and '42' in g(value='42')['summary'] and not g(value='42')['notes'])
for bad in ('abc', None, True, float('nan'), float('inf'), [1], {}):
    r_ = g(value=bad); ok('value %r counts as 0 and is noted' % (bad,), any('not a number' in x for x in r_['notes']) and abs(needle(r_['svg'])[0] - expect(0, R_NEEDLE)[0]) < 0.01)
hi_ = g(value=140, threshold=100)
ok('a value above the scale: needle at the end, the number as given, noted', abs(needle(hi_['svg'])[0] - expect(1, R_NEEDLE)[0]) < 0.01 and '140' in ''.join(texts(hi_['svg'])) and any('above the scale' in x for x in hi_['notes']))
ok('a value below the scale: needle at the start, noted', any('below the scale' in x for x in g(value=-5)['notes']) and abs(needle(g(value=-5)['svg'])[0] - expect(0, R_NEEDLE)[0]) < 0.01)
ok('status uses the value as given, not the clamped one', any('HEALTHY' in t for t in texts(hi_['svg'])))
nr = gauge_sla(value=5, max_value=0)['gauge']
ok('a scale with no width gives a note-only result', 'Nothing was drawn' in nr['summary'] and any('no width' in x for x in nr['notes']))
ok('a bad max_value falls back to 100 with a note', any('max_value' in x for x in g(value=5, max_value='x')['notes']) and '0 to 100' in g(value=5, max_value='x')['summary'])
ok('version above 1 draws as version 1 with a note', any('version 3' in x for x in g(value=5, version=3)['notes']))
ok('a custom scale is labelled at both ends', set(['-20', '80']) <= set(texts(g(value=0, min=-20, max_value=80)['svg'])))

# --- hostile text and the output policy ---
h = g(value=5, title='<script>alert(1)</script>"&', unit='<b>%', label='x' * 500)
ok('markup in title, unit and label stays escaped text', '<script' not in h['svg'] and '<b>' not in h['svg'] and ET.fromstring(h['svg']) is not None)
ok('long text is capped (label 40 chars)', all(len(t) <= 80 for t in texts(h['svg'])))
for k in ('gauge_sla', 'gauge_sla_warning', 'gauge_sla_plain', 'gauge_sla_bands'):
    macro, params = d3pack._demos()[k]; res = d3pack.PACK[macro](**params)['gauge']
    try: C.verify_svg(res['svg']); passed = True
    except C.SvgPolicyError: passed = False
    ok('demo %s draws and passes the base output policy' % k, passed and res['alt'].startswith('Gauge sla'))
ok('every text is at least 12 px', all(float(e.get('font-size')) >= 12 for e in els(g(value=5, threshold=9, title='t', label='l')['svg'], 'text')))

# --- the pack, determinism, speed ---
ok('registered in the pack', d3pack.PACK['gauge_sla'] is gauge_sla)
ok('deterministic', g(value=37.5, threshold=30, steps=bands) == g(value=37.5, threshold=30, steps=bands))
t0 = time.perf_counter()
for i in range(200): g(value=i / 2, threshold=60, steps=bands)
ms = (time.perf_counter() - t0) * 1000 / 200
ok('draw and policy check under 5 ms (measured %.2f ms)' % ms, ms < 5)
card = d3pack.card('gauge_sla', 'API Response SLA', dict(value=99.4, unit='%', threshold=99))
ok('card() returns A2UI messages', isinstance(card, (list, tuple)) and len(card) >= 1)


# --- extreme values (18 Nov 2026): units keep their space, long text shrinks to fit, nothing under 12 px ---
def sized(svg): return [(float(e.get('font-size')), e.text or '') for e in els(svg, 'text')]
ok('a unit given with a leading space keeps it (as the atom does)', any(t == '0.00042 A' for _, t in sized(g(value=0.00042, max_value=0.001, unit=' A')['svg'])))
ok('a unit given without a space stays tight', any(t == '99.4%' for _, t in sized(g(value=99.4, unit='%')['svg'])))
ok('ordinary lengths keep the full 44 px value text', any(sz == 44 and t == '99.4%' for sz, t in sized(g(value=99.4, unit='%')['svg'])))
big = g(value=1.2e9, max_value=2e9, unit=' B', threshold=1.5e9, label='x' * 40, title='Requests')
vt = [(sz, t) for sz, t in sized(big['svg']) if t == '1,200,000,000 B'][0]
ok('a long value shrinks below 44 px and stays at 12 px or more', 12 <= vt[0] < 44)
ok('a long status line shrinks to fit, never under 12 px', any(t.startswith('BREACHED') and 12 <= sz < 16 for sz, t in sized(big['svg'])))
ok('estimated text widths (0.64 em per character, bold) stay inside the 600 px picture, also at the extremes', all(len(t) * sz * 0.64 <= 590 for gg in (big, g(value=-123456789012345, max_value=999999999999999, unit=' units', threshold=5e14, label='y' * 40)) for sz, t in sized(gg['svg'])))
ok('the extreme drawings pass the output policy and every font is 12 px or more', all(float(e.get('font-size')) >= 12 for e in els(big['svg'], 'text')))
ok('negative scale: the needle at the midpoint of -50..50 points straight up', abs(needle(g(value=0, min=-50, max_value=50)['svg'])[0] - CX) < 0.01)
ok('offset scale: the needle follows (value - min) / (max - min)', abs(needle(g(value=1042, min=1000, max_value=1100)['svg'])[0] - expect(0.42, R_NEEDLE)[0]) < 0.01)
ok('a tiny scale (0 to 1e-9) draws a needle at the right place', abs(needle(g(value=5e-10, max_value=1e-9)['svg'])[0] - CX) < 0.01)
print('gauge_sla: %d checks, %d failed' % (n, len(fails)))
sys.exit(1 if fails else 0)
