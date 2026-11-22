"""PACK_STATS: macro name (= atom name) -> function. 'ridgeline' is a thin wrapper over histogram's ridge layout, kept for callers that use it; 'beeswarm' has no atom (own contract).
DEMO_FN maps a DEMOS key to the macro it runs (histogram_ridge is histogram with layout='ridge')."""
from .histogram import histogram
from .box_plot import box_plot
from .ridgeline import ridgeline
from .beeswarm import beeswarm
PACK_STATS = {'histogram': histogram, 'box_plot': box_plot, 'ridgeline': ridgeline, 'beeswarm': beeswarm}
DEMO_FN = {'histogram': 'histogram', 'histogram_ridge': 'histogram', 'box_plot': 'box_plot', 'ridgeline': 'ridgeline', 'beeswarm': 'beeswarm'}
