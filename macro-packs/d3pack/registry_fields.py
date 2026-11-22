"""Registry of the 'fields' group (merged into PACK by d3pack/__init__.py). The venn macro is registered under both its own name and the atom's name (venn_diagram), so a router
keyed by atom name finds it."""
from .contour import contour_plot
from .venn import venn
PACK_FIELDS = {'contour_plot': contour_plot, 'venn': venn, 'venn_diagram': venn}
