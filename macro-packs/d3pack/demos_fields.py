"""Small synthetic demo inputs for the 'fields' group."""
import math, random
_g = [round(math.exp(-((c - 12) ** 2 + (r - 8) ** 2) / 40) * 10 + math.exp(-((c - 4) ** 2 + (r - 14) ** 2) / 20) * 6, 3) for r in range(18) for c in range(24)]
_rng = random.Random(7)
_pts = [{'x': round(_rng.gauss(2, .6), 3), 'y': round(_rng.gauss(3, .5), 3)} for _ in range(150)] + [{'x': round(_rng.gauss(5, .8), 3), 'y': round(_rng.gauss(1, .7), 3)} for _ in range(100)]
DEMOS = {
    'contour_plot': dict(grid={'width': 24, 'height': 18, 'values': _g}, thresholds=8, value_label='Intensity', unit='mm', title='Two hills on a grid'),
    'contour_points': dict(points=_pts, bandwidth=24, x_label='Width', y_label='Height', title='Density of 250 points'),
    'venn': dict(sets=[{'name': 'Design', 'size': 40}, {'name': 'Build', 'size': 60}, {'name': 'Ship', 'size': 30}], overlaps=[{'sets': ['Design', 'Build'], 'size': 15}, {'sets': ['Build', 'Ship'], 'size': 12}, {'sets': ['Design', 'Ship'], 'size': 6}], triple=4, unit='people', title='Who works on what'),
    'venn_two': dict(sets=[{'name': 'Readers', 'size': 120}, {'name': 'Buyers', 'size': 45}], overlaps=[{'sets': ['Readers', 'Buyers'], 'size': 30}], title='Readers and buyers'),
}
