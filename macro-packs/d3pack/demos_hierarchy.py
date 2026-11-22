"""Small synthetic examples for the hierarchy group. Only macros whose atom contract exists in atoms/schema.yaml (treemap; dendrogram and radial_tree have no atom)."""
DEMOS = {'treemap': dict(items=[{'category': 'Compute', 'name': 'VMs', 'value': 40}, {'category': 'Compute', 'name': 'Batch', 'value': 25}, {'category': 'Storage', 'name': 'Archive', 'value': 30},
                                {'category': 'Storage', 'name': 'Hot', 'value': 10}, {'category': 'Network', 'name': 'Egress', 'value': 22}, {'category': 'Data', 'name': 'Warehouse', 'value': 18},
                                {'category': 'Data', 'name': 'Streams', 'value': 9}, {'category': 'Data', 'name': 'Catalog', 'value': 4}], unit='k USD', title='Cloud spend')}
