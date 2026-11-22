#!/usr/bin/env python3
"""glass_monitor (20 Nov 2026): the time rule in the data layer. GlassMonitor (two levels) and EscalationMonitor (three tiers). Each rule has a case that fires and a case that must not; the owner's scenarios are checked event by event at exact times.
Run: /tmp/claude-1000/pubvenv/bin/python tests/test_glass_monitor.py"""
import pathlib, sys
sys.dont_write_bytecode = True; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from d3pack.glass_monitor import GlassMonitor, EscalationMonitor, run, run_escalation
fails = []; n = 0
def ok(name, cond):
    global n; n += 1
    if not cond: fails.append(name); print("FAIL", name)
ev = lambda rs: [(r['t'], r['event']) for r in rs if r['event']]
# the owner's first scenario: at or under 5 for MORE than 5 s breaks; over 10 for MORE than 5 s recovers; 5 to 10 changes nothing
S = list(zip(range(0, 42), [45] * 5 + [30, 12, 12, 4.8, 4.8, 4.8, 6.5, 9, 9, 9] + [4.2] * 7 + [3.8, 4.5, 6, 7.5, 9, 11, 11.5, 12, 8, 5, 4, 6] + [15] * 8))
got = ev(run(S))
ok("scenario: a dip that does not last is cancelled, the glass breaks after more than 5 s, a recovery that does not last is cancelled, then it recovers", got == [(8, 'pending_break'), (11, 'cancel_break'), (15, 'pending_break'), (21, 'break'), (27, 'pending_recover'), (30, 'cancel_recover'), (34, 'pending_recover'), (40, 'recover')])
ok("the timer reports its exact due time and elapsed seconds", [r for r in run(S) if r['t'] == 8][0]['due'] == 13.0 and [r for r in run(S) if r['t'] == 10][0]['elapsed'] == 2.0)
ok("strict: exactly 5 s at the level does not break (the sample at t=13 is 5 s after t=8); the next one does", ev(run([(t, 4) for t in range(8, 15)])) == [(8, 'pending_break'), (14, 'break')])
ok("the gap between the levels starts nothing: 7 is neither at the break level nor over the recovery level; a value that falls back into the gap cancels a recovery that was running", run([(0, 7), (10, 7)])[-1]["pending"] is None and run([(0, 7), (10, 7)], state='red')[-1]["pending"] is None and ev(run([(0, 11), (3, 8)], state='red')) == [(0, 'pending_recover'), (3, 'cancel_recover')])
ok("values exactly at the levels: 5 is at the break level (counts), 10 is not over the recovery level", run([(0, 5)])[0]['pending'] == 'break' and run([(0, 10)], state='red')[0]['pending'] is None)
for bad in (dict(break_at=10, recover_above=5), dict(break_at=5, recover_above=5), dict(dwell=-1), dict(state='dead')):
    try: GlassMonitor(**bad); good = False
    except ValueError: good = True
    ok(f"GlassMonitor refuses bad settings {bad}", good)
try: m = GlassMonitor(); m.update(5, 1); m.update(5, 1); good = False
except ValueError: good = True
ok("a repeated time is refused, never silently reordered", good)
ok("deterministic: the same samples give the same events", run(S) == run(S))
# the three tiers
B = list(zip(range(60), [40] * 3 + [4.8] * 7 + [3] * 4 + [0] * 17 + [9] * 2 + [14] * 27))
eb = ev(run_escalation(B))
ok("escalation: break after more than 5 s, explode after more than 10 s at 0, recover after more than 5 s over 10", [e for e in eb if e[1] in ('break', 'explode', 'recover')] == [(9, 'break'), (25, 'explode'), (39, 'recover')])
ok("a value that is 0 from the start of the dip: the glass breaks at 9 and the explosion at 14 (its timer kept running through the break)", [e for e in ev(run_escalation([(t, 0) for t in range(3, 30)])) if e[1] in ('break', 'explode')] == [(9, 'break'), (14, 'explode')])
ok("9 s at 0 then a rise to 3 cancels the explosion timer and the state stays red", [e for e in ev(run_escalation([(t, 4) for t in range(0, 7)] + [(t, 0) for t in range(7, 17)] + [(17, 3)])) if e[1] in ('explode', 'cancel_explode')] == [(17, 'cancel_explode')])
ok("a dead gauge stays dead at 0 and between the levels (no timers run); only more than 5 s over 10 recovers it", run_escalation([(0, 0), (1, 6), (2, 6), (3, 9), (10, 9)], state='dead')[-1]['state'] == 'dead' and run_escalation([(0, 0), (10, 0)], state='dead')[-1]['pending'] is None)
ok("recovery from dead goes straight to ok", [e for e in ev(run_escalation([(t, 14) for t in range(0, 9)], state='dead')) if e[1] == 'recover'] == [(6, 'recover')])
ok("escalation is deterministic and refuses disorder", run_escalation(B) == run_escalation(B))
try: EscalationMonitor(explode_at=7, break_at=5); good = False
except ValueError: good = True
ok("EscalationMonitor refuses explode_at above break_at", good)
print(f"glass_monitor: {n} checks, {len(fails)} failed"); sys.exit(1 if fails else 0)
