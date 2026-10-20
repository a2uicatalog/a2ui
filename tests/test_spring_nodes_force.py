"""spring_nodes layout: Python and GAS ports against REAL d3-force 3.0.0 (with d3-quadtree 3.0.1, d3-dispatch and d3-timer as its deps).

GOLDEN holds what d3 produced (generated outside the repo by a node script):
    forceSimulation(nodes).force("link", forceLink(links).distance(D)).force("charge", forceManyBody().strength(-300))
        .force("center", forceCenter(0, 0)).stop().tick(300)
on nodes with no x/y (so d3's own phyllotaxis start) and its default LCG random source. `pos` is [x, y] per node.
The layout functions (_sn_layout / _snLayout) must match to 1e-9. The render is a settled static SVG: no script, no animation.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from test_motion_atoms import _gas_batch, _node, _py, core_js  # noqa: F401  (core_js is a fixture)
from test_motion_atoms import wa  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TOL = 1e-9
TICKS, CHARGE = 300, -300

GOLDEN = {"single": {"n": 1, "links": [], "distance": 110, "pos": [[0, 0]]}, "pair": {"n": 2, "links": [[0, 1]], "distance": 110, "pos": [[51.23683685789728, -26.325003388055986], [-51.23683685789728, 26.325003388055986]]}, "chain3": {"n": 3, "links": [[0, 1], [1, 2]], "distance": 110, "pos": [[72.76312635683023, 66.87040640281596], [-35.49001095271287, 24.68545273539636], [-37.27653637931344, -91.55296844564384]]}, "default6": {"n": 6, "links": [[0, 1], [1, 2], [1, 3], [1, 4], [0, 3], [1, 5]], "distance": 110, "pos": [[112.86682217976046, 37.59285462006423], [-10.658367574720248, 12.97671172557151], [-62.917933809592434, -95.65155246060183], [38.47693203337843, 127.35256348466703], [-130.27255159701056, 6.778920087036399], [52.507525649904, -89.0363175125355]]}, "ring8": {"n": 8, "links": [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 7], [7, 0]], "distance": 80, "pos": [[-190.62698512725584, 13.412723611981772], [-112.0225806005833, -72.5569358326122], [4.552708455394482, -109.18441079560816], [116.71523174758886, -72.4939405550763], [182.5578923438432, 15.511004698177238], [106.07626519784445, 90.63146038618719], [-5.30816198218151, 90.40870689524793], [-101.94445240854797, 44.27095043492761]]}, "star10": {"n": 10, "links": [[0, 1], [0, 2], [0, 3], [0, 4], [0, 5], [0, 6], [0, 7], [0, 8], [0, 9]], "distance": 110, "pos": [[0.793629030515582, -4.682759239015613], [-66.12826502706062, 99.95273097241802], [32.14333128731305, -124.18606941033892], [83.44594338538909, 87.25528226521031], [-115.88391364314519, -46.71755033540284], [107.89689318924181, -67.06940988922], [10.671983628736642, 118.6149835364139], [-57.81120460559006, -113.45411439078025], [122.22489516561912, 17.68288151345336], [-117.34938090283055, 32.59895408544231]]}, "islands": {"n": 7, "links": [[0, 1], [1, 2], [3, 4]], "distance": 90, "pos": [[-107.63019763387824, -108.93912898623941], [-203.77061763484573, -91.15319182757926], [-232.18021214122857, -184.41656267677533], [145.86557129431276, 140.55851816953685], [54.64018869591392, 110.18886271128727], [393.5208594513673, -302.7711671151969], [-50.44844156077575, 436.5371543763675]]}, "no_edges5": {"n": 5, "links": [], "distance": 110, "pos": [[225.41624544802505, -65.35464812319968], [-161.80326529738272, 223.6306153769126], [26.06409504407746, -315.2464740090149], [211.95321364968325, 260.0583830891243], [-301.6301789434949, -103.08776052921758]]}, "rand20": {"n": 20, "links": [[0, 1], [0, 2], [1, 3], [3, 4], [3, 5], [4, 6], [1, 7], [7, 8], [6, 9], [8, 10], [8, 11], [4, 12], [10, 13], [2, 14], [8, 15], [3, 16], [3, 17], [14, 18], [16, 19], [16, 2], [9, 14], [7, 5], [7, 18], [17, 8], [8, 16], [6, 7]], "distance": 110, "pos": [[-87.53944120910603, 199.4522896610443], [-97.05474340819069, 65.5315411258014], [-4.331821189632122, 263.32687633741045], [7.871112589961524, 8.639226759867121], [-165.797423320237, -67.94689936743764], [2.3727522154729486, -122.68626365327249], [-279.4763548766273, -14.862828248783407], [-100.62564624928405, -69.92413531999435], [140.23248503416605, -95.23428337236128], [-319.59967143278544, 135.01849850574985], [269.7394931299673, -196.26674756376457], [264.73886972685006, -98.05813141948323], [-264.98766266636926, -149.01539659323578], [377.17493845764255, -270.28849811228037], [-198.09733571560818, 226.89979304728334], [165.35826343888434, -218.38814545374004], [118.84162215343241, 116.31738524690807], [143.2861191113623, 17.773643391809653], [-188.64324623369524, 69.83178463300807], [216.52368272766904, 199.8909270524135]]}, "rand45": {"n": 45, "links": [[0, 1], [1, 2], [1, 3], [3, 4], [1, 5], [2, 6], [6, 7], [6, 8], [2, 9], [5, 10], [9, 11], [8, 12], [1, 13], [8, 14], [1, 15], [11, 16], [6, 17], [12, 18], [4, 19], [7, 20], [8, 21], [9, 22], [21, 23], [10, 24], [0, 25], [6, 26], [3, 27], [18, 28], [0, 29], [8, 30], [8, 31], [13, 32], [7, 33], [27, 34], [16, 35], [19, 36], [31, 37], [23, 38], [27, 39], [0, 40], [22, 41], [18, 42], [21, 43], [29, 44], [13, 21], [42, 9], [23, 40], [27, 0], [28, 29], [17, 36], [30, 12], [35, 44], [22, 8], [25, 30], [38, 25], [31, 3], [42, 3], [10, 20], [36, 13], [38, 10], [36, 18], [19, 0], [14, 31], [37, 35], [44, 26], [38, 13], [0, 11], [23, 29]], "distance": 60, "pos": [[97.66745862861787, 75.11130215883651], [-100.27451120086353, -80.85856520559489], [-193.4420725639139, 50.54808562939799], [-35.69435714787687, 204.55959849873344], [-93.6100648585213, 130.136091999322], [-160.27610710577724, -271.92804845511057], [-175.57132672771226, -63.02761618769626], [-326.52732924984923, -252.58432554991603], [-40.312322783808916, 99.25467335623495], [-98.34974023426865, 235.91621701515925], [-180.27669255099465, -422.84782409584545], [99.12203719401978, 274.20711929565107], [32.033659091025584, 45.56510644064805], [43.52707031498314, -267.76239714263994], [37.49936233245911, 206.72954534002164], [-179.03532547655772, -128.44251972768316], [249.9536069150424, 351.18054244267853], [-106.51208850399806, -163.48259164810804], [157.35245797277096, 3.4030160262696234], [-13.163815171222796, 6.134619752301806], [-299.3913318802099, -391.8193116519373], [109.38883977851204, -148.40166460366555], [-189.36821979750655, 228.4721613498621], [176.40110638503455, -208.29903412058937], [-204.380752822555, -511.7856311174672], [12.09167572495704, -104.55975959999674], [51.236984562067285, 0.21083410576020037], [13.904759060177604, 327.1049098858913], [308.2521552661969, -38.26799179221633], [257.0291234865278, -10.21985535644362], [-75.96206692172541, 8.258339224174478], [118.39367160439689, 239.39386247339417], [82.53090653238607, -357.2375470650324], [-409.5008506264222, -297.13058555266394], [-30.362340828089152, 414.3333545372087], [350.0469269028559, 282.19157684754197], [22.815642987493344, -155.42388912570485], [260.8888223697582, 298.08055809012313], [-2.933191876366296, -322.7586626785884], [19.380729511366763, 425.65498011967014], [172.852171295159, -70.06939221763928], [-267.5820504133262, 286.58372629126836], [37.99775613015928, 158.0232798709092], [203.20630941722104, -193.46339172781606], [268.97753218471934, 109.34208871999202]]}, "dup_edges": {"n": 4, "links": [[0, 1], [0, 1], [1, 2], [2, 3], [3, 0]], "distance": 140, "pos": [[65.03190382628225, -26.994193097494154], [-90.59085792581615, 8.49540386815981], [12.848035026012532, -75.59480149382132], [12.711227496034459, 94.09408996263117]]}}


def _close(a, b):
    assert len(a) == len(b)
    for p, q in zip(a, b):
        assert abs(p[0] - q[0]) <= TOL and abs(p[1] - q[1]) <= TOL, (p, q)


@pytest.mark.parametrize("name", list(GOLDEN))
def test_python_layout_matches_d3_force(name):
    g = GOLDEN[name]
    _close(wa._sn_layout(g["n"], g["links"], g["distance"], CHARGE, TICKS), g["pos"])


def test_gas_layout_matches_d3_force(core_js):
    names = list(GOLDEN)
    calls = [[GOLDEN[n]["n"], GOLDEN[n]["links"], GOLDEN[n]["distance"]] for n in names]
    res = _node(core_js, "var G = " + json.dumps(calls) + "; console.log(JSON.stringify(G.map(function(c){ return _snLayout(c[0], c[1], c[2], %d, %d); })));" % (CHARGE, TICKS))
    for n, pos in zip(names, res):
        _close(pos, GOLDEN[n]["pos"])


def _block(path):
    t = path.read_text()
    a = t.index("// ── spring_nodes")
    return t[a:t.index("// ── isometric_mesh", a)]


def test_every_maintained_gas_copy_carries_the_same_spring_nodes_code():
    wired = _block(ROOT / "apps-script-surface/gas-wired-renderer/atoms_canvas.gs")
    assert "_snLayout" in wired and "Math.random" not in wired and "<script" not in wired and "requestAnimationFrame" not in wired
    for f in ("gas-schema-renderer/atoms_canvas.gs", "gas-schema-renderer/atoms_canvas.js"):
        assert _block(ROOT / "apps-script-surface" / f) == wired, f


def test_frozen_copies_are_untouched():
    for d in ("gas-fakes-schema-renderer-private", "gas-wired-renderer-starter"):
        p = ROOT / "apps-script-surface" / d / "atoms_canvas.gs"
        if p.exists():
            assert "_snLayout" not in p.read_text()


# ─── render ───────────────────────────────────────────────────────────────────
NODES = [{"id": "web", "label": "Web"}, {"id": "api", "label": "API"}, {"id": "db", "label": "Database"}, {"id": "q", "label": "Queue"}]
CIRCLE = re.compile(r'<circle cx="(-?[\d.]+)" cy="(-?[\d.]+)" r="([\d.]+)" fill="[^"]*" stroke=')   # the outlined disc (a plain tint disc sits on top of it)
LINE = re.compile(r'<line x1="(-?[\d.]+)" y1="(-?[\d.]+)" x2="(-?[\d.]+)" y2="(-?[\d.]+)"')


def _fmt(v):
    import math
    return "%.2f" % (math.floor(v * 100 + 0.5) / 100)


def _expected_pos(n, links, dist, h, r=22):
    import math
    pos = wa._sn_layout(n, links, dist, CHARGE, TICKS)
    W, pad, lbl = 600, 24, 18
    xs = [p[0] for p in pos]; ys = [p[1] for p in pos]
    mx, Mx, my, My = min(xs), max(xs), min(ys), max(ys)
    aw = max(1, W - 2 * (pad + r)); ah = max(1, h - 2 * (pad + r) - lbl)
    s = 1.0
    if Mx - mx > 0: s = min(s, aw / (Mx - mx))
    if My - my > 0: s = min(s, ah / (My - my))
    cx, cy = (mx + Mx) / 2, (my + My) / 2
    return [((x - cx) * s + W / 2, (y - cy) * s + h / 2 - lbl / 2) for x, y in pos]


def _html_both(block, core_js):
    return [_py(block), _gas_batch(core_js, [block])[0]]


def test_render_follows_the_d3_layout_in_both_renderers(core_js):
    links = [[0, 1], [1, 2], [1, 3]]
    block = {"type": "spring_nodes", "nodes": NODES, "edges": [{"a": a, "b": b} for a, b in links], "height": 400, "rest_length": 90}
    exp = _expected_pos(4, links, 90, 400)
    for html in _html_both(block, core_js):
        cs = CIRCLE.findall(html)
        assert len(cs) == 4
        for (x, y, r), (ex, ey) in zip(cs, exp):
            assert x == _fmt(ex) and y == _fmt(ey), (x, y, ex, ey)
        ls = LINE.findall(html)
        assert len(ls) == 3
        for (x1, y1, x2, y2), (a, b) in zip(ls, links):
            assert (x1, y1, x2, y2) == (_fmt(exp[a][0]), _fmt(exp[a][1]), _fmt(exp[b][0]), _fmt(exp[b][1]))


def test_static_svg_has_no_script_no_motion_no_cdn(core_js):
    for html in _html_both({"type": "spring_nodes"}, core_js):
        low = html.lower()
        assert "<svg" in low and "<script" not in low and "<canvas" not in low
        for bad in ("animate", "transition", "requestanimationframe", "http://", "https://", "onmouse", "onclick"):
            assert bad not in low.replace("http://www.w3.org/2000/svg", ""), bad


def test_edge_shapes_index_pairs_ids_and_bad_edges_are_handled(core_js):
    cases = [
        ([{"a": 0, "b": 1}, {"a": 1, "b": 2}], 2),                       # the contract: {a, b} index pairs
        ([{"from": "web", "to": "api"}, {"from": "api", "to": "db"}], 2),  # ids (what the GAS twin took before)
        ([{"source": "web", "target": "db"}], 1),                          # what the Python renderer took before
        ([{"a": 0, "b": 9}, {"a": 2, "b": 2}, {"a": "nope", "b": 1}, {"a": 0, "b": 1}], 1),  # out of range, self loop, unknown id: skipped
    ]
    for edges, want in cases:
        for html in _html_both({"type": "spring_nodes", "nodes": NODES[:3], "edges": edges}, core_js):
            assert len(LINE.findall(html)) == want, (edges, len(LINE.findall(html)))


def test_defaults_are_six_labelled_nodes_with_links(core_js):
    for html in _html_both({"type": "spring_nodes"}, core_js):
        assert len(CIRCLE.findall(html)) == 6 and len(LINE.findall(html)) >= 5


def test_same_payload_renders_identically_every_time_and_python_matches_gas(core_js):
    b = {"type": "spring_nodes", "nodes": NODES, "edges": [{"a": 0, "b": 1}, {"a": 1, "b": 2}, {"a": 2, "b": 3}]}
    a1, g1 = _html_both(b, core_js)
    a2, g2 = _html_both(b, core_js)
    assert a1 == a2 and g1 == g2
    norm = lambda h: re.sub(r"\s+", " ", re.sub(r'(<svg\b[^>]*?) role="img" aria-label="[^"]*"', r"\1", h))
    assert norm(a1) == norm(g1)


def test_text_alternative_lists_every_node_and_link(core_js):
    b = {"type": "spring_nodes", "nodes": NODES, "edges": [{"a": 0, "b": 1}, {"a": 1, "b": 2}]}
    for html in _html_both(b, core_js):
        assert 'role="img"' in html and "aria-label=" in html
        assert "<ul" in html and html.count("<li>") == 4
        li = re.findall(r"<li>(.*?)</li>", html, re.S)
        assert any(t.startswith("Web") and "API" in t for t in li)
        assert any(t.startswith("Queue") for t in li)       # a node with no links is still listed
        for lab in ("Web", "API", "Database", "Queue"):
            assert lab in " ".join(li)


def _lum(h):
    h = h.lstrip("#")
    if len(h) == 3: h = "".join(c * 2 for c in h)
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def _ratio(a, b):
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def test_default_colours_pass_contrast_and_label_colour_follows_the_background(core_js):
    for html in _html_both({"type": "spring_nodes"}, core_js):
        stroke = re.search(r'<circle[^>]*stroke="(#[0-9a-fA-F]{6})"', html).group(1)
        text = re.search(r'<text[^>]*fill="(#[0-9a-fA-F]{6})"', html).group(1)
        bg = re.search(r"background:(#[0-9a-fA-F]{6})", html).group(1)
        assert _ratio(stroke, bg) >= 3 and _ratio(text, bg) >= 4.5, (stroke, text, bg)
    for html in _html_both({"type": "spring_nodes", "bg": "#ffffff", "colour": "#4f46e5"}, core_js):
        text = re.search(r'<text[^>]*fill="(#[0-9a-fA-F]{6})"', html).group(1)
        assert _ratio(text, "#ffffff") >= 4.5, text


def test_colour_values_cannot_break_out_of_the_attribute(core_js):
    for html in _html_both({"type": "spring_nodes", "colour": '"><script>x</script>', "bg": 'red;}</style><script>y</script>'}, core_js):
        assert "<script" not in html


def test_labels_are_escaped(core_js):
    for html in _html_both({"type": "spring_nodes", "nodes": [{"id": "a", "label": "<b>x</b>"}, {"id": "b", "label": "y"}]}, core_js):
        assert "<b>" not in html and "&lt;b&gt;" in html


def test_third_party_notice_names_d3_force_with_exact_version():
    t = (ROOT / "THIRD-PARTY-NOTICES.md").read_text()
    i = t.index("## d3-force")
    sec = t[i:t.index("\n---", i)]
    assert "3.0.0" in sec and "ISC" in sec and "d3-quadtree" in sec and "Mike Bostock" in sec
