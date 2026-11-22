"""ridgeline: kept as a thin wrapper. The ridge drawing now lives in histogram.py (histogram(layout='ridge'), contract = the histogram atom, atoms/schema.yaml),
because the atom's ridge layout replaces a separate ridgeline. This wrapper only maps our older input {groups:[{name|label, values}] or values} to series and adds an `overlap` option
(0.5..3, default 1.6) that the atom does not have. Series rules are the atom's (5 to 2000 numbers, up to 8, shared bins, height = share of the series). Returns {'ridgeline': Result}."""
import math
from .common import *
from .histogram import ridge_result, read_series, note_card, ctext
def ridgeline(groups=None, values=None, bins=None, overlap=1.6, unit='', title='', x_label='', version=1, **extra):
    notes = []; u = ctext(unit, 12, '') or ''; ttl = ctext(title, 80, '') or ''; xl = ctext(x_label, 40, '') or ''
    if isinstance(overlap, (int, float)) and not isinstance(overlap, bool) and math.isfinite(overlap): ov = min(3.0, max(.5, float(overlap))); notes += [f'overlap {overlap} was clamped to {fmt(ov)}.'] if ov != overlap else []
    else: ov = 1.6; notes.append('overlap was not a number, 1.6 was used.')
    if isinstance(version, int) and not isinstance(version, bool) and version > 1: notes.append(f'Contract version {version} is drawn as version 1.')
    raw = [dict(g, label=g.get('label', g.get('name'))) if isinstance(g, dict) else g for g in groups] if isinstance(groups, list) else ([{'label': 'Values', 'values': values}] if values is not None else [])
    ss = read_series(raw, notes, 'Series', 8, 'groups')
    if not ss: m = 'A ridgeline needs 1 to 8 groups, each with at least 5 usable numbers.'; return {'ridgeline': note_card('ridgeline', ttl, m, notes + [m]), '_default': 'ridgeline'}
    if isinstance(bins, int) and not isinstance(bins, bool) or bins is None: pass
    return {'ridgeline': ridge_result('ridgeline', ttl, ss, bins, xl, u, notes, ov), '_default': 'ridgeline'}
