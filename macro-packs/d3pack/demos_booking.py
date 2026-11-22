"""Demo inputs for the availability macro: one invented team's office hours, the week of Monday 9 November 2026, built in code (no random)."""
DAYS = ['2026-11-09', '2026-11-10', '2026-11-11', '2026-11-12', '2026-11-13']
TIMES = ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00']
BUSY = [[d, t] for d, ts in (('2026-11-09', ('09:00', '11:00', '14:00')), ('2026-11-10', ('10:00', '13:00', '14:00', '15:00')), ('2026-11-11', ('09:00', '10:00', '12:00', '16:00')),
                              ('2026-11-12', ('11:00', '12:00', '13:00')), ('2026-11-13', ('09:00', '15:00', '16:00'))) for t in ts]
DEMOS = {'availability_week': dict(days=DAYS, times=TIMES, busy=BUSY, selected=['2026-11-10', '11:00'], title='Platform office hours'),
         'availability_day': dict(days=DAYS, times=TIMES, busy=BUSY, selected=['2026-11-10', '11:00'], view='day', day='2026-11-10', title='Platform office hours')}
