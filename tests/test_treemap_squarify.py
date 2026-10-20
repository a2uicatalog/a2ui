"""Squarified treemap layout: Python and GAS ports against REAL d3-hierarchy 3.1.2 treemapSquarify.

GOLDEN holds the rectangles d3 produced (generated outside the repo by a node script running
`treemap().tile(treemapSquarify).size([900, 300])` with no padding and no rounding on the same payloads).
The layout functions must match to 1e-9; the rendered boxes (percentages, 3 decimals) must match to the rounding.
"""
from __future__ import annotations

import re

import pytest

from test_motion_atoms import _gas_batch, _node, _py, core_js  # noqa: F401  (core_js is a fixture)
from test_motion_atoms import wa  # noqa: E402

# d3-hierarchy 3.1.2, size [900, 300], paddings 0, round off. Each case: payload items, per-category value lists,
# category rectangles and item rectangles [x0, y0, x1, y1].
GOLDEN = {
    'one_category': {
        'items': [{"category": "A", "name": "n0", "value": 5}, {"category": "A", "name": "n1", "value": 3}, {"category": "A", "name": "n2", "value": 2}],
        'groups': [[5, 3, 2]],
        'cats': [[0, 0, 900, 300]],
        'rects': [[[0, 0, 450, 300], [450, 0, 720, 300], [720, 0, 900, 300]]],
    },
    'four_categories': {
        'items': [{"category": "A", "name": "n0", "value": 40}, {"category": "A", "name": "n1", "value": 25}, {"category": "B", "name": "n2", "value": 30}, {"category": "B", "name": "n3", "value": 10}, {"category": "C", "name": "n4", "value": 22}, {"category": "D", "name": "n5", "value": 18}, {"category": "D", "name": "n6", "value": 9}, {"category": "D", "name": "n7", "value": 4}],
        'groups': [[40, 25], [30, 10], [22], [18, 9, 4]],
        'cats': [[0, 0, 370.253164556962, 300], [370.253164556962, 0, 723.4177215189873, 193.5483870967742], [370.253164556962, 193.5483870967742, 723.4177215189873, 300], [723.4177215189873, 0, 900, 300]],
        'rects': [[[0, 0, 370.253164556962, 184.61538461538458], [0, 184.61538461538458, 370.253164556962, 299.99999999999994]], [[370.253164556962, 0, 635.126582278481, 193.5483870967742], [635.126582278481, 0, 723.4177215189873, 193.5483870967742]], [[370.253164556962, 193.5483870967742, 723.4177215189873, 300]], [[723.4177215189873, 0, 900, 174.19354838709677], [723.4177215189873, 174.19354838709677, 845.6669912366115, 300], [845.6669912366115, 174.19354838709677, 900, 300]]],
    },
    'twelve_items': {
        'items': [{"category": "A", "name": "n0", "value": 9}, {"category": "B", "name": "n1", "value": 8}, {"category": "C", "name": "n2", "value": 7}, {"category": "D", "name": "n3", "value": 6}, {"category": "A", "name": "n4", "value": 5}, {"category": "B", "name": "n5", "value": 4}, {"category": "C", "name": "n6", "value": 3}, {"category": "D", "name": "n7", "value": 2}, {"category": "A", "name": "n8", "value": 1.5}, {"category": "B", "name": "n9", "value": 1.25}, {"category": "C", "name": "n10", "value": 1}, {"category": "D", "name": "n11", "value": 0.5}],
        'groups': [[9, 5, 1.5], [8, 4, 1.25], [7, 3, 1], [6, 2, 0.5]],
        'cats': [[0, 0, 289.11917098445593, 300], [289.11917098445593, 0, 536.2694300518135, 300], [536.2694300518135, 0, 900, 169.23076923076923], [536.2694300518135, 169.23076923076923, 900, 300]],
        'rects': [[[0, 0, 185.86232420429312, 270.96774193548384], [185.86232420429312, 0, 289.119170984456, 270.96774193548384], [0, 270.96774193548384, 289.11917098445593, 300]], [[289.11917098445593, 0, 453.8860103626943, 271.6981132075472], [453.8860103626943, 0, 536.2694300518135, 271.6981132075472], [289.11917098445593, 271.6981132075472, 536.2694300518135, 300]], [[536.2694300518135, 0, 767.7343382006594, 169.23076923076923], [767.7343382006594, 0, 900, 126.92307692307692], [767.7343382006594, 126.92307692307692, 900, 169.23076923076923]], [[536.2694300518135, 169.23076923076923, 793.0204206034746, 300], [793.0204206034746, 169.23076923076923, 900, 273.8461538461538], [793.0204206034746, 273.8461538461538, 900, 300]]],
    },
    'very_unequal': {
        'items': [{"category": "A", "name": "n0", "value": 1000000}, {"category": "A", "name": "n1", "value": 1}, {"category": "B", "name": "n2", "value": 0.001}, {"category": "B", "name": "n3", "value": 250000}, {"category": "C", "name": "n4", "value": 3}, {"category": "C", "name": "n5", "value": 0.001}, {"category": "D", "name": "n6", "value": 999999}],
        'groups': [[1000000, 1], [0.001, 250000], [3, 0.001], [999999]],
        'cats': [[0, 0, 399.9998663112894, 300], [399.9998663112894, 0, 499.99973328924466, 300], [499.99973328924466, 0, 899.9999999999998, 0.0009002981985033047], [499.99973328924466, 0.0009002981985033047, 899.9999999999998, 300]],
        'rects': [[[0, 0, 399.9994663118231, 300], [399.9994663118231, 0, 399.9998663112894, 300]], [[399.9998663112894, 0, 499.9997343602642, 1.1999999823477486e-06], [399.9998663112894, 1.1999999823477486e-06, 499.99973328924466, 300]], [[499.99973328924466, 0, 899.866711007427, 0.0009002981985033048], [899.866711007427, 0, 899.9999999999998, 0.0009002981985033047]], [[499.99973328924466, 0.0009002981985033047, 899.9999999999998, 300]]],
    },
    'equal_values': {
        'items': [{"category": "A", "name": "n0", "value": 1}, {"category": "A", "name": "n1", "value": 1}, {"category": "A", "name": "n2", "value": 1}, {"category": "B", "name": "n3", "value": 1}, {"category": "B", "name": "n4", "value": 1}, {"category": "C", "name": "n5", "value": 1}, {"category": "D", "name": "n6", "value": 1}, {"category": "D", "name": "n7", "value": 1}, {"category": "D", "name": "n8", "value": 1}],
        'groups': [[1, 1, 1], [1, 1], [1], [1, 1, 1]],
        'cats': [[0, 0, 300, 300], [300, 0, 600, 200], [300, 200, 600, 300], [600, 0, 900, 300]],
        'rects': [[[0, 0, 200, 150], [0, 150, 200, 300], [200, 0, 300, 300]], [[300, 0, 600, 100], [300, 100, 600, 200]], [[300, 200, 600, 300]], [[600, 0, 800, 150], [600, 150, 800, 300], [800, 0, 900, 300]]],
    },
    'truncated_fifth': {
        'items': [{"category": "A", "name": "n0", "value": 10}, {"category": "B", "name": "n1", "value": 20}, {"category": "C", "name": "n2", "value": 30}, {"category": "D", "name": "n3", "value": 40}, {"category": "E", "name": "n4", "value": 50}, {"category": "A", "name": "n5", "value": 5}],
        'groups': [[10, 5], [20], [30], [40]],
        'cats': [[0, 0, 300, 128.57142857142856], [0, 128.57142857142856, 300, 300], [300, 0, 557.1428571428571, 300], [557.1428571428571, 0, 900, 300]],
        'rects': [[[0, 0, 200, 128.57142857142856], [200, 0, 300, 128.57142857142856]], [[0, 128.57142857142856, 300, 300]], [[300, 0, 557.1428571428571, 300]], [[557.1428571428571, 0, 900, 300]]],
    },
    'single_item': {
        'items': [{"category": "Only", "name": "n0", "value": 7}],
        'groups': [[7]],
        'cats': [[0, 0, 900, 300]],
        'rects': [[[0, 0, 900, 300]]],
    },
    'mixed_decimals': {
        'items': [{"category": "Cloud", "name": "n0", "value": 1234.56}, {"category": "Cloud", "name": "n1", "value": 78.9}, {"category": "Edge", "name": "n2", "value": 456.789}, {"category": "Edge", "name": "n3", "value": 0.37}, {"category": "Edge", "name": "n4", "value": 12}, {"category": "Core", "name": "n5", "value": 3333.3}, {"category": "Ops", "name": "n6", "value": 101.1}, {"category": "Ops", "name": "n7", "value": 202.2}],
        'groups': [[1234.56, 78.9], [456.789, 0.37, 12], [3333.3], [101.1, 202.2]],
        'cats': [[0, 0, 218.13364619514363, 300], [218.13364619514363, 0, 296.04950455037897, 299.99999999999994], [296.04950455037897, 0, 849.6292731480312, 300], [849.6292731480312, 0, 900, 300.0000000000002]],
        'rects': [[[0, 0, 218.13364619514363, 281.97889543648074], [0, 281.97889543648074, 218.1336461951434, 300]], [[218.13364619514363, 0, 296.04950455037897, 292.09010164997363], [218.13364619514363, 292.09010164997363, 220.46419329226867, 299.99999999999994], [220.46419329226867, 292.09010164997363, 296.04950455037897, 299.99999999999994]], [[296.04950455037897, 0, 849.6292731480312, 300]], [[849.6292731480312, 0, 900, 100.00000000000006], [849.6292731480312, 100.00000000000006, 900, 300.0000000000002]]],
    },
}

TOL = 1e-9
CELL = re.compile(r'<div style="position:absolute;left:([\d.]+)%;top:([\d.]+)%;width:([\d.]+)%;height:([\d.]+)%;box-sizing:border-box;border:1px solid transparent;')


def _close(a, b, tol=TOL):
    assert len(a) == len(b)
    for x, y in zip(a, b):
        assert abs(x - y) <= tol, (a, b)


def _cells(html):
    return [[float(x) for x in m] for m in CELL.findall(html)]


def _expected_cells(g):
    return [[r[0] / 9, r[1] / 3, (r[2] - r[0]) / 9, (r[3] - r[1]) / 3] for cat in g["rects"] for r in cat]


@pytest.mark.parametrize("name", list(GOLDEN))
def test_python_layout_matches_d3(name):
    g = GOLDEN[name]
    cats, items = wa._tm_layout(g["groups"])
    for a, b in zip(cats, g["cats"]):
        _close(a, b)
    assert len(items) == len(g["rects"])
    for ia, ib in zip(items, g["rects"]):
        assert len(ia) == len(ib)
        for a, b in zip(ia, ib):
            _close(a, b)


def test_gas_layout_matches_d3(core_js):
    names = list(GOLDEN)
    res = _node(core_js, "var G = " + __import__("json").dumps([GOLDEN[n]["groups"] for n in names]) + "; console.log(JSON.stringify(G.map(function(g){ return _tmLayout(g); })));")
    for n, (cats, items) in zip(names, res):
        g = GOLDEN[n]
        for a, b in zip(cats, g["cats"]):
            _close(a, b)
        for ia, ib in zip(items, g["rects"]):
            for a, b in zip(ia, ib):
                _close(a, b)


@pytest.mark.parametrize("name", list(GOLDEN))
def test_rendered_boxes_follow_the_d3_layout_in_both_renderers(name, core_js):
    g = GOLDEN[name]
    block = {"type": "treemap", "items": g["items"]}
    exp = _expected_cells(g)
    for html in (_py(block), _gas_batch(core_js, [block])[0]):
        got = _cells(html)
        assert len(got) == len(exp), (len(got), len(exp))
        for a, b in zip(got, exp):
            _close(a, b, 6e-4)          # the boxes carry 3 decimals of a percent
        assert "<script" not in html


def test_fifth_category_is_still_dropped():
    html = _py({"type": "treemap", "items": GOLDEN["truncated_fifth"]["items"]})
    assert ">E " not in html and "n4" not in html


def test_every_item_is_fully_visible_in_a_static_render_with_four_categories(core_js):
    # The motion index was ci*4+k, so the 3rd and 4th categories' later items overshot the 12-step clamp and
    # rendered at opacity 0 when --p is 1 (static pages, PDF). Every item must reach --k = 1 at p = 1.
    import re
    items = [{"category": c, "name": f"{c}{i}", "value": v}
             for c, n in [("A", 2), ("B", 2), ("C", 3), ("D", 3)] for i, v in zip(range(n), [5, 3, 2])]
    block = {"type": "treemap", "items": items}
    for html in (_py(block), _gas_batch(core_js, [block])[0]):
        ks = re.findall(r'var\(--p,1\)\*(\d+)\s*-\s*(\d+)\)', html)
        assert len(ks) == len(items)
        assert all(int(m) - int(i) >= 1 for m, i in ks), ks
