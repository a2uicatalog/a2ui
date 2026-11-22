"""Small synthetic demo inputs for the stats macros (fixed seed). histogram/box_plot/ridgeline use the atoms' own input names; beeswarm is our own design."""
import random
_r = random.Random(7)
_a = [round(_r.gauss(50, 10), 1) for _ in range(60)]; _b = [round(_r.gauss(62, 7), 1) for _ in range(60)]; _c = [round(_r.gauss(40, 14), 1) for _ in range(60)] + [95, 99]
DEMOS = {
    'histogram': dict(title='Task time', values=_a + _b, x_label='Task time', unit='min'),
    'histogram_ridge': dict(title='Task time by team', layout='ridge', series=[{'label': 'Team A', 'values': _a}, {'label': 'Team B', 'values': _b}, {'label': 'Team C', 'values': _c}], x_label='Task time', unit='min'),
    'box_plot': dict(title='Task time by team', groups=[{'label': 'Team A', 'values': _a}, {'label': 'Team B', 'values': _b}, {'label': 'Team C', 'values': _c}], x_label='Task time', unit='min', show_points=True),
    'ridgeline': dict(groups=[{'name': 'Team A', 'values': _a}, {'name': 'Team B', 'values': _b}, {'name': 'Team C', 'values': _c}], unit='min', title='Task time by team'),
    'beeswarm': dict(groups=[{'name': 'Team A', 'values': _a[:40]}, {'name': 'Team B', 'values': _b[:40]}, {'name': 'Team C', 'values': _c[:40]}], unit='min', title='Task time by team'),
}
