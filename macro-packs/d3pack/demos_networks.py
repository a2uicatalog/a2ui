"""Small synthetic demos for the networks group: {macro_name: params}."""
DEMOS = {
    'decision_tree': dict(title='Which support route?', nodes=[
        {'text': 'Is the service down?', 'children': [
            {'text': 'Yes: page on-call', 'children': [{'text': 'Declare incident'}, {'text': 'Open status page'}]},
            {'text': 'No: is it slow?', 'children': [{'text': 'Yes: check queue depth'}, {'text': 'No: file a ticket'}]}]}]),
    'spring_nodes': dict(nodes=[{'id': c, 'label': l} for c, l in (('w', 'Web'), ('a', 'API'), ('d', 'Database'), ('u', 'Auth'), ('c', 'Cache'), ('q', 'Queue'), ('m', 'Mail'))],
                         edges=[{'a': 'w', 'b': 'a'}, {'a': 'a', 'b': 'd'}, {'a': 'a', 'b': 'u'}, {'a': 'a', 'b': 'c'}, {'a': 'a', 'b': 'q'}, {'a': 'q', 'b': 'm'}], height=420, rest_length=110),
    'voronoi': dict(title='Nearest depot', unit='km', x_label='East (km)', y_label='North (km)', sites=[
        {'x': 10, 'y': 80, 'label': 'North', 'group': 'Hub', 'value': 120}, {'x': 55, 'y': 70, 'label': 'Centre', 'group': 'Hub', 'value': 200}, {'x': 90, 'y': 85, 'label': 'East', 'group': 'Depot', 'value': 90},
        {'x': 20, 'y': 25, 'label': 'West', 'group': 'Depot', 'value': 75}, {'x': 60, 'y': 20, 'label': 'South', 'group': 'Depot', 'value': 110}, {'x': 95, 'y': 35, 'label': 'Port', 'group': 'Hub', 'value': 160}]),
}
