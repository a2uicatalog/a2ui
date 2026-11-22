"""glass_monitor (20 Nov 2026): the time rule behind the glass effect, kept in the DATA layer (owner: break when the value is at or under 5 percent for longer than 5 seconds; back to green when it is over 10 percent for longer than 5 seconds).
A debounce with a gap (hysteresis): a dip that does not last does not break anything, a recovery that does not last does not heal anything, and values between the two levels never change the state. Pure and deterministic: the same samples always give the same events. Standard library only.
States: 'ok' and 'red'. Events: 'pending_break' (the value reached the break level, the timer started), 'cancel_break' (it left the level before the dwell was over), 'break' (it stayed for MORE than the dwell), then the same three for recovery: 'pending_recover', 'cancel_recover', 'recover'.
The dwell is strict ('longer than 5 s'): with samples every second, a timer that starts at t = 8 fires at the first sample after t = 13, that is t = 14; `due` says the exact time the dwell ran out. Samples must be in time order; a repeated or earlier time is an error, never silently reordered.
Usage: m = GlassMonitor(break_at=5, recover_above=10, dwell=5); r = m.update(t, value) -> {'t','value','state','event','pending','elapsed','due'}. run(samples, ...) maps a list of (t, value). Not registered in the pack's PACK table."""
class GlassMonitor:
    def __init__(self, break_at=5.0, recover_above=10.0, dwell=5.0, state='ok'):
        if not break_at < recover_above: raise ValueError('break_at must be under recover_above (the gap between them is what stops flicker)')
        if dwell < 0: raise ValueError('dwell must not be negative')
        if state not in ('ok', 'red'): raise ValueError("state must be 'ok' or 'red'")
        self.break_at, self.recover_above, self.dwell, self.state = float(break_at), float(recover_above), float(dwell), state
        self.since = None; self.last_t = None
    def update(self, t, value):
        t = float(t); value = float(value)
        if self.last_t is not None and t <= self.last_t: raise ValueError(f'samples must be in time order (got t={t} after t={self.last_t})')
        self.last_t = t; event = None; ok = self.state == 'ok'
        cond = value <= self.break_at if ok else value > self.recover_above   # the condition that would flip the state
        if cond:
            if self.since is None: self.since = t; event = 'pending_break' if ok else 'pending_recover'
            if t - self.since > self.dwell:
                event = 'break' if ok else 'recover'; self.state = 'red' if ok else 'ok'; self.since = None
        elif self.since is not None:
            event = 'cancel_break' if ok else 'cancel_recover'; self.since = None
        pend = self.since is not None
        return {'t': t, 'value': value, 'state': self.state, 'event': event, 'pending': ('break' if self.state == 'ok' else 'recover') if pend else None,
                'elapsed': round(t - self.since, 6) if pend else 0.0, 'due': round(self.since + self.dwell, 6) if pend else None}
def run(samples, break_at=5.0, recover_above=10.0, dwell=5.0, state='ok'):
    m = GlassMonitor(break_at, recover_above, dwell, state); return [m.update(t, v) for t, v in samples]
class EscalationMonitor:
    """The three-tier time rule (20 Nov 2026, owner): ok -> red when the value is at or under break_at for MORE than break_dwell seconds; red (or ok) -> dead when it is at or under explode_at for MORE than explode_dwell seconds (0 percent for 10 s: the explosion);
    red or dead -> ok when it is OVER recover_above for MORE than recover_dwell seconds. Three independent timers; between the levels nothing changes. A timer that runs out acts at the first sample after it; 'due' is the exact time it ran out.
    Events: break, explode, recover (state changes) and pending_break, cancel_break, pending_explode, cancel_explode, pending_recover, cancel_recover (a timer started or was cancelled). If two timers run out on the same sample the worse state wins (explode over break). Pure and deterministic."""
    def __init__(self, break_at=5.0, break_dwell=5.0, explode_at=0.0, explode_dwell=10.0, recover_above=10.0, recover_dwell=5.0, state='ok'):
        if not (explode_at <= break_at < recover_above): raise ValueError('need explode_at <= break_at < recover_above')
        if state not in ('ok', 'red', 'dead'): raise ValueError("state must be 'ok', 'red' or 'dead'")
        self.p = dict(break_at=float(break_at), break_dwell=float(break_dwell), explode_at=float(explode_at), explode_dwell=float(explode_dwell), recover_above=float(recover_above), recover_dwell=float(recover_dwell))
        self.state = state; self.since = {'break': None, 'explode': None, 'recover': None}; self.last_t = None
    def update(self, t, value):
        t = float(t); value = float(value); p = self.p
        if self.last_t is not None and t <= self.last_t: raise ValueError(f'samples must be in time order (got t={t} after t={self.last_t})')
        self.last_t = t; events = []
        conds = {'break': value <= p['break_at'] and self.state == 'ok', 'explode': value <= p['explode_at'] and self.state != 'dead', 'recover': value > p['recover_above'] and self.state != 'ok'}
        for k, c in conds.items():
            if c and self.since[k] is None: self.since[k] = t; events.append('pending_' + k)
            if not c and self.since[k] is not None: self.since[k] = None; events.append('cancel_' + k)
        dwell = {'break': p['break_dwell'], 'explode': p['explode_dwell'], 'recover': p['recover_dwell']}
        due = {k: self.since[k] is not None and t - self.since[k] > dwell[k] for k in self.since}
        new = self.state
        if due['explode']: new = 'dead'
        elif due['break']: new = 'red'
        elif due['recover']: new = 'ok'
        if new != self.state:
            events = [e for e in events if not e.startswith('pending_')] + [{'dead': 'explode', 'red': 'break', 'ok': 'recover'}[new]]; self.state = new
            if new == 'red': self.since['break'] = None; self.since['recover'] = None   # the explosion timer keeps running: the value that broke the glass may also be at the explosion level
            else: self.since = {'break': None, 'explode': None, 'recover': None}
        pend = [(k, s) for k, s in self.since.items() if s is not None]; pk, ps = (min(pend, key=lambda x: x[1]) if pend else (None, None))
        return {'t': t, 'value': value, 'state': self.state, 'event': events[-1] if events else None, 'events': events, 'pending': pk, 'elapsed': round(t - ps, 6) if ps is not None else 0.0, 'due': round(ps + dwell[pk], 6) if ps is not None else None}
def run_escalation(samples, **kw):
    m = EscalationMonitor(**kw); return [m.update(t, v) for t, v in samples]
