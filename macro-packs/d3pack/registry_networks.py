"""Registry for the networks group of the d3 macro pack."""
from .decision_tree import decision_tree
from .spring_nodes import spring_nodes
from .voronoi import voronoi
PACK_NETWORKS = {'decision_tree': decision_tree, 'spring_nodes': spring_nodes, 'voronoi': voronoi}
