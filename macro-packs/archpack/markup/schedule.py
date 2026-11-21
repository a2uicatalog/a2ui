"""Pacing: how long each step of the film stays on screen (port of mermaid_arch/schedule.mjs). Timing only.

dwell(step) = max(1.8 s, words / 4 per second + 0.5 s), x 1.1 above 6 steps, x 1.1 again above 9, x pace (slow 1.4, normal 1,
fast 0.75); a step with several message chips is stretched so every chip rides inside it.
total = LEAD_IN (1 s) + sum of dwells + HOLD (2 s). `duration` overrides the total: the dwells are scaled to fit.
"""
from __future__ import annotations

import re

from ._js import js_round, num_str, to_fixed, trim
from .graph import PACES

LEAD_IN = 1
HOLD = 2
MIN_DWELL = 1.8
WORDS_PER_SECOND = 4
READ_PAD = 0.5
CHIP_GAP = 0.15
CHIP_START = 0.55
CHIP_TAIL = 0.3

CHIP_SPEED = 0.14
CHIP_MAX_RIDE = 5.0
RIDE_FLOOR = 0.75


class ScheduleError(Exception):
    """JS: an Error with archMessage = true; compile turns it into an ArchError."""


def chip_min_ride(chars):
    return max(1.8, 0.8 + 0.07 * chars)


def chip_ride(path_len, long_side, chars):
    mn = chip_min_ride(chars)
    mx = max(CHIP_MAX_RIDE, mn)
    return {'r': min(mx, max(mn, path_len / (CHIP_SPEED * max(1, long_side)))), 'min': mn}


def pace_ride(chip, m):
    return max(RIDE_FLOOR * chip['min'], chip['r'] * m)


def words(t):
    s = trim(str(t or ''))
    return len(re.split(r'[\s   -     　﻿]+', s)) if s else 0


def _round(x):
    return js_round(x * 1000) / 1000


def _fsum(xs):
    t = 0
    for x in xs:   # a plain left fold, like Array.reduce (Python 3.12+ sum() compensates and can differ in the last bit)
        t = t + x
    return t


def build_schedule(steps, pace='normal', duration=None):
    """steps: [{'words', 'chips', 'rides': [{r, min}]}] in playing order -> dict(schedule, durationSeconds, warnings, minimumSeconds)"""
    warnings = []
    if not (isinstance(pace, str) and pace in PACES):
        raise ScheduleError('pace "%s" is not one of %s' % (pace, ', '.join(PACES)))
    mult = PACES[pace]
    n = len(steps)
    crowd = 1.1 * 1.1 if n > 9 else (1.1 if n > 6 else 1)

    def base(st, m):
        d = max(MIN_DWELL, st['words'] / WORDS_PER_SECOND + READ_PAD) * crowd * m
        need = CHIP_START + _fsum(pace_ride(c, m) for c in (st.get('rides') or [])) + max(0, st['chips'] - 1) * CHIP_GAP + CHIP_TAIL
        return max(d, need)
    dwell = [base(st, mult) for st in steps]
    fast = LEAD_IN + HOLD + _fsum(base(st, PACES['fast']) for st in steps)
    if duration is not None:
        room = duration - LEAD_IN - HOLD
        total_dwell = _fsum(dwell)
        if room <= 0 or (n and room < 0.3 * n):
            raise ScheduleError('duration %s s leaves no time for %d steps after the %d s lead-in and %d s hold' % (num_str(duration), n, LEAD_IN, HOLD))
        if duration < fast - 1e-9:
            warnings.append('duration {} s is shorter than the {} s the steps need at the fast pace; readers will not have time to take each step in. Raise it or drop %% duration.'.format(num_str(duration), to_fixed(fast, 1)))
        k = room / total_dwell if n else 1
        dwell = [d * k for d in dwell]
    schedule = []
    t = LEAD_IN
    for i, d in enumerate(dwell):
        schedule.append({'step': i + 1, 'start': _round(t), 'end': _round(t + d)})
        t += d
    total = duration if duration is not None else _round(t + HOLD)
    return {'schedule': schedule, 'durationSeconds': _round(total), 'warnings': warnings, 'minimumSeconds': _round(fast)}
