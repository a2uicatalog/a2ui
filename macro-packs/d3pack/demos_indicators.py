"""Demo inputs for the gauge_sla macro (same input contract as the gauge_sla atom): an SLA that is met, a value in the warning band, a value with no target (no status is judged) and a value on a banded scale, built in code (no random)."""
DEMOS = {
    'gauge_sla': dict(title='API Response SLA', value=99.4, max_value=100, unit='%', label='SLA Met', threshold=99),
    'gauge_sla_warning': dict(title='Uptime this month', value=95.2, max_value=100, unit='%', label='Below target', threshold=99),
    'gauge_sla_plain': dict(title='Tickets closed today', value=37, max_value=60, label='No target set'),
    'gauge_sla_bands': dict(title='Disk used', value=72, max_value=100, unit='%', threshold=90, steps=[dict(**{'from': 0, 'to': 60, 'color': '#2f8a3f'}), dict(**{'from': 60, 'to': 85, 'color': '#e0912f'}), dict(**{'from': 85, 'to': 100, 'color': '#cc3f56'})]),
}
