"""arc_diagram (I61): nodes on one horizontal line, each link a semicircle above it (d3 gallery "arc diagram"). No d3 layout module computes it; the node
positions are d3-scale 4.0.2 scalePoint().range([0, 800]).padding(0.5), ported by hand into BOTH renderers.

GOLDEN (tests/fixtures/arc_diagram_d3_golden.json, from arc_diagram_d3_golden_gen.mjs) holds what the REAL scalePoint gives for 0 to 40 nodes in four
ranges. Every position is compared with ==: the scale is step = (r1 - r0) / max(1, n), start = r0 + (r1 - r0 - step * (n - 1)) * 0.5, start + step * i,
all correctly rounded IEEE operations in Python and V8 alike.
Also held here: Python/GAS HTML parity, the node orders (input, group, degree), the hidden tables, the aria label, the legend, the thinned labels, the
motion index, malformed input, caps with notes, the `version` field, escaping and registration.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

import pytest
import yaml

from test_histogram import ATTACK
from test_motion_atoms import _gas_batch, _node, _py, core_js  # noqa: F401  (core_js is a fixture)
from test_motion_atoms import wa  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
D = json.loads((ROOT / "tests/fixtures/arc_diagram_d3_golden.json").read_text())


# ─── the point scale against real d3 ───────────────────────────────────────────────────────────────────────────
def test_python_point_scale_matches_d3_exactly():
    assert len(D["cases"]) == 41 * 4
    for c in D["cases"]:
        assert wa._ad_point(c["n"], c["range"][0], c["range"][1]) == c["values"], (c["n"], c["range"])


def test_gas_point_scale_matches_d3_exactly(core_js):
    got = _node(core_js, "var C = " + json.dumps([[c["n"], c["range"]] for c in D["cases"]]) + "; console.log(JSON.stringify(C.map(function(c){ return _adPoint(c[0], c[1][0], c[1][1]); })));")
    assert got == [c["values"] for c in D["cases"]]


# ─── rendering ─────────────────────────────────────────────────────────────────────────────────────────────────
def _n(i, label=None, group=None):
    return {"id": i, "label": label or i} | ({"group": group} if group else {})


def _l(s, t, v=None):
    return {"source": s, "target": t} | ({"value": v} if v is not None else {})


AUTHORS = {"type": "arc_diagram", "title": "Who writes with whom", "unit": "papers", "nodes": [
    _n("ada", "Ada Okafor", "Systems"), _n("ben", "Ben Haas", "Systems"), _n("chi", "Chidi Eze", "Systems"), _n("dia", "Diana Rossi", "Vision"),
    _n("eli", "Elif Demir", "Vision"), _n("fay", "Fay Chen", "Vision"), _n("gus", "Gus Lindqvist", "Theory"), _n("hal", "Hal Brandt", "Theory"),
    _n("ivy", "Ivy Moreau", "Theory"), _n("jon", "Jon Park")], "links": [
    _l("ada", "ben", 6), _l("ada", "chi", 3), _l("ben", "chi", 4), _l("ada", "dia", 1), _l("dia", "eli", 5), _l("dia", "fay", 2), _l("eli", "fay", 3),
    _l("fay", "gus", 1), _l("gus", "hal", 7), _l("gus", "ivy", 2), _l("hal", "ivy", 3), _l("ben", "gus", 1), _l("chi", "jon", 1), _l("jon", "ada", 2), _l("eli", "ivy", 1)]}
MODULES = {"type": "arc_diagram", "title": "Module imports", "nodes": [_n(m) for m in ("app", "router", "auth", "db", "cache", "log", "config", "utils")], "links": [
    _l("app", "router"), _l("app", "config"), _l("router", "auth"), _l("router", "log"), _l("auth", "db"), _l("auth", "cache"), _l("db", "config"), _l("db", "log"),
    _l("cache", "config"), _l("auth", "utils"), _l("db", "utils"), _l("app", "log")]}


def _forty(nn=40, nl=120):
    nodes = [_n("n%d" % k, "Node %d" % k, "G%d" % (k % 5) if k % 7 else None) for k in range(nn)]
    links, s = [], 7
    while len(links) < nl:
        s = (s * 1103515245 + 12345) % 2147483648
        a = s % nn
        s = (s * 1103515245 + 12345) % 2147483648
        t = s % nn
        if a != t:
            links.append(_l("n%d" % a, "n%d" % t, 1 + (s >> 8) % 9))
    return {"type": "arc_diagram", "nodes": nodes, "links": links}


PAYLOADS = {
    "authors": AUTHORS,
    "authors_group": dict(AUTHORS, order="group"),
    "authors_degree": dict(AUTHORS, order="degree"),
    "modules": MODULES,
    "forty": _forty(),
    "forty_degree": dict(_forty(), order="degree"),
    "two": {"type": "arc_diagram", "nodes": [_n("a"), _n("b")], "links": [_l("a", "b", 2.5)]},
    "no_links": {"type": "arc_diagram", "nodes": [_n("a"), _n("b"), _n("c")], "links": []},
    "no_links_key": {"type": "arc_diagram", "nodes": [_n("a"), _n("b"), _n("c")]},
    "long_labels": {"type": "arc_diagram", "nodes": [_n("a", "A label of exactly twenty-four chars", "A very long group name indeed"), _n("b", "Short"), _n("c", "ccc")], "links": [_l("a", "c"), _l("a", "b", 3)]},
    "twelve_groups": {"type": "arc_diagram", "nodes": [_n("n%d" % k, "N%d" % k, "G%d" % k) for k in range(12)], "links": [_l("n%d" % k, "n%d" % ((k + 3) % 12)) for k in range(12)]},
    "dirty": {"type": "arc_diagram", "nodes": [_n("a", "Alpha", "X"), _n("b", "Beta", "X"), _n("a", "Again"), {"label": "no id"}, "text", None, 7, {"id": "", "label": "empty"}, {"id": 5},
                                                  {"id": "c", "group": 4}, {"id": "d", "label": 9, "group": "  "}],
              "links": [_l("a", "b", 2), _l("a", "a", 3), _l("a", "zzz", 1), _l("zzz", "b"), {"source": "a"}, "text", None, _l("a", "c", 0), _l("a", "c", -2), _l("a", "c", "5"), _l("b", "c", float("inf")),
                        _l("c", "d", 1.5), _l("d", "a", None), {"source": 1, "target": "a"}]},
    "forty_one_nodes": {"type": "arc_diagram", "nodes": [_n("n%d" % k) for k in range(41)], "links": [_l("n0", "n40"), _l("n0", "n39")]},
    "links_121": {"type": "arc_diagram", "nodes": [_n("a"), _n("b"), _n("c")], "links": [_l("a", "b", 1 + k % 3) for k in range(121)]},
    "too_few": {"type": "arc_diagram", "title": "T", "nodes": [_n("a")], "links": []},
    "no_nodes": {"type": "arc_diagram"},
    "nodes_not_list": {"type": "arc_diagram", "nodes": {"id": "a"}, "links": 5},
    "bad_order": {"type": "arc_diagram", "order": "spiral", "nodes": AUTHORS["nodes"], "links": AUTHORS["links"]},
    "order_junk": {"type": "arc_diagram", "order": ["group"], "nodes": AUTHORS["nodes"], "links": AUTHORS["links"]},
    "version_2": {"type": "arc_diagram", "version": 2, "nodes": MODULES["nodes"], "links": MODULES["links"]},
    "version_junk": {"type": "arc_diagram", "version": True, "nodes": MODULES["nodes"], "links": MODULES["links"]},
}


@pytest.mark.parametrize("name", list(PAYLOADS))
def test_python_and_gas_emit_identical_html(name, core_js):
    assert _py(PAYLOADS[name]) == _gas_batch(core_js, [PAYLOADS[name]])[0]


def test_hostile_text_python_and_gas_agree_and_are_escaped(core_js):
    b = {"type": "arc_diagram", "title": ATTACK, "unit": ATTACK, "nodes": [_n(ATTACK, ATTACK, ATTACK), _n("b", ATTACK, ATTACK + "2")], "links": [_l(ATTACK, "b", 3)]}
    outs = [_py(b), _gas_batch(core_js, [b])[0]]
    assert outs[0] == outs[1]
    for h in outs:
        assert "<img" not in h and "<svg onload" not in h and "<script" not in h.replace("<style", "") and 'onerror=alert(1)>' not in h.replace("&gt;", "")
        assert "&lt;img" in h


def _tables(html):
    out = []
    for m in re.finditer(r'<table style="position:absolute[^"]*"><thead><tr>(.*?)</tr></thead><tbody>(.*?)</tbody></table>', html, re.S):
        out.append((re.findall(r'<th scope="col">(.*?)</th>', m.group(1)), [re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', r) for r in re.findall(r'<tr>(.*?)</tr>', m.group(2), re.S)]))
    return out


def _dots(html):
    return re.findall(r'<circle class="adn" cx="([\d.]+)" cy="([\d.]+)" r="([\d.]+)" fill="([^"]+)"><title>(.*?)</title></circle>', html)


def _nm(title):
    """The node name at the start of a dot title ("Name (Group): 3 links" or "Name: 3 links")."""
    return re.split(r" \(|: ", title)[0]


def _arcs(html):
    return re.findall(r'<path class="ada" d="M([\d.]+),([\d.]+)A([\d.]+),([\d.]+),0,0,1,([\d.]+),([\d.]+)" fill="none" stroke="([^"]+)" stroke-width="([\d.]+)" stroke-opacity="0\.6" stroke-linecap="round" '
                      r'vector-effect="non-scaling-stroke"><title>(.*?)</title></path>', html)


def test_draws_one_arc_per_link_one_dot_per_node_and_two_hidden_tables(core_js):
    for html in (_py(AUTHORS), _gas_batch(core_js, [AUTHORS])[0]):
        assert "<script" not in html and "<svg " in html and "NaN" not in html and "undefined" not in html and "[object Object]" not in html
        assert len(_arcs(html)) == 15 and len(_dots(html)) == 10
        ts = _tables(html)
        assert [t[0] for t in ts] == [["Node", "Group", "Links"], ["From", "To", "Value"]]
        t = html.index("<table")
        assert 'role="img"' in html[:t] and 'role="img"' not in html[t:]
        assert ts[0][1][0] == ["Ada Okafor", "Systems", "4"] and ts[0][1][-1] == ["Jon Park", "No group", "2"]
        assert len(ts[0][1]) == 10 and len(ts[1][1]) == 15
        assert ts[1][1][0] == ["Ada Okafor", "Ben Haas", "6 papers"]
        assert sum(int(r[2]) for r in ts[0][1]) == 30                          # every link counts at both ends


def test_arcs_are_semicircles_above_one_line_between_their_nodes():
    h = _py(AUTHORS)
    xs = {_nm(t): float(cx) for cx, cy, r, f, t in _dots(h)}
    ys = {cy for _, cy, *_ in _dots(h)}
    assert len(ys) == 1
    base = float(ys.pop())
    pts = [xs[n["label"]] for n in AUTHORS["nodes"]]
    assert all(abs(a - b) < 0.006 for a, b in zip(pts, wa._ad_point(10, 0, 800)))
    for x0, y0, rx, ry, x1, y1, col, sw, title in _arcs(h):
        assert float(y0) == float(y1) == base and rx == ry and abs(float(rx) - (float(x1) - float(x0)) / 2) < 0.011 and float(x0) < float(x1)
    # the heaviest link (value 7) is the thickest, the lightest (1) the thinnest, and the width never passes 6
    by = {t: float(sw) for *_, sw, t in _arcs(h)}
    assert by["Gus Lindqvist to Hal Brandt: 7 papers"] == 6 and by["Ada Okafor to Diana Rossi: 1 papers"] == 1 and all(1 <= v <= 6 for v in by.values())


def test_equal_values_draw_every_arc_at_the_same_modest_width():
    ws = {sw for *_, sw, _ in _arcs(_py(MODULES))}
    assert ws == {"2.00"}


def test_aria_label_gives_counts_and_the_most_connected_node(core_js):
    for html in (_py(AUTHORS), _gas_batch(core_js, [AUTHORS])[0]):
        a = re.search(r'role="img" aria-label="([^"]*)"', html).group(1)
        assert a == "Arc diagram of 10 nodes and 15 links. Most connected: Ada Okafor, 4 links."
    assert re.search(r'aria-label="([^"]*)"', _py(PAYLOADS["two"])).group(1) == "Arc diagram of 2 nodes and 1 link. Most connected: a, 1 link."
    assert re.search(r'aria-label="([^"]*)"', _py(PAYLOADS["no_links"])).group(1) == "Arc diagram of 3 nodes and 0 links."


def test_order_input_group_degree():
    def labels(name):
        return [_nm(t) for *_, t in _dots(_py(PAYLOADS[name]))]
    assert labels("authors") == [n["label"] for n in AUTHORS["nodes"]]
    assert labels("authors_group") == ["Jon Park", "Ada Okafor", "Ben Haas", "Chidi Eze", "Gus Lindqvist", "Hal Brandt", "Ivy Moreau", "Diana Rossi", "Elif Demir", "Fay Chen"]
    deg = labels("authors_degree")
    assert deg[:2] == ["Ada Okafor", "Gus Lindqvist"] and len(deg) == 10
    degs = {r[0]: int(r[2]) for r in _tables(_py(PAYLOADS["authors_degree"]))[0][1]}
    assert [degs[x] for x in deg] == sorted(degs.values(), reverse=True)
    for a, b in zip(deg, deg[1:]):                                             # ties in degree keep input order
        if degs[a] == degs[b]:
            assert labels("authors").index(a) < labels("authors").index(b)


def test_group_order_sorts_by_group_then_label_and_is_stable():
    b = {"type": "arc_diagram", "order": "group", "nodes": [_n("1", "b", "Y"), _n("2", "a", "Y"), _n("3", "z", "X"), _n("4", "a", "Y"), _n("5", "m"), _n("6", "B", "X")], "links": []}
    assert [_nm(t) for *_, t in _dots(_py(b))] == ["m", "B", "z", "a", "a", "b"]
    assert [r[0] for r in _tables(_py(b))[0][1]] == ["m", "B", "z", "a", "a", "b"]


def test_group_colours_follow_first_seen_input_order_whatever_the_display_order(core_js):
    by = lambda h: {_nm(t): f for _, _, _, f, t in _dots(h)}
    a, g = by(_py(AUTHORS)), by(_py(PAYLOADS["authors_group"]))
    assert a == g
    assert a["Ada Okafor"] == a["Ben Haas"] != a["Diana Rossi"] != a["Gus Lindqvist"] and a["Ada Okafor"] == wa._SB_PALETTE[0] and a["Diana Rossi"] == wa._SB_PALETTE[1]
    assert a["Jon Park"] == wa._AD_NONE


def test_legend_names_every_group_and_never_leaves_colour_alone():
    h = _py(AUTHORS)
    legend = re.search(r'<div class="adleg"[^>]*>(.*?)</div>', h, re.S)
    txt = re.sub(r"<[^>]+>", "|", legend.group(1))
    for name in ("Systems", "Vision", "Theory", "No group"):
        assert name in txt
    assert "adleg" not in _py(MODULES)                                         # no groups, no legend
    # every dot title names its node and group, so colour is never the only cue
    assert "Ada Okafor (Systems): 4 links" in [t for *_, t in _dots(h)]


def test_text_is_never_below_12px_and_nothing_has_a_script():
    for n, b in PAYLOADS.items():
        h = _py(b)
        assert all(int(x) >= 12 for x in re.findall(r"font-size:(\d+)px", h)), n
        assert "<script" not in h and "NaN" not in h and "Infinity" not in h and "undefined" not in h and "[object Object]" not in h, n


def test_motion_index_stays_inside_its_clamp(core_js):
    for html in (_py(AUTHORS), _gas_batch(core_js, [AUTHORS])[0]):
        ks = re.findall(r'<g class="adr" style="--k:clamp\(0,calc\(var\(--p,1\)\*(\d+) - (\d+)\),1\);', html)
        assert [(int(n), int(i)) for n, i in ks] == [(3, 0), (3, 1)]


def test_malformed_input_is_dropped_and_explained(core_js):
    for h in (_py(PAYLOADS["dirty"]), _gas_batch(core_js, [PAYLOADS["dirty"]])[0]):
        nodes, links = _tables(h)[0][1], _tables(h)[1][1]
        assert [r[0] for r in nodes] == ["Alpha", "Beta", "c", "d"] and [r[1] for r in nodes] == ["X", "X", "No group", "No group"]
        assert [(r[0], r[1], r[2]) for r in links] == [("Alpha", "Beta", "2"), ("c", "d", "1.5"), ("d", "Alpha", "1")]
        assert "7 node entries were left out (not a node, no id, or an id already used)." in h
        assert "11 links were dropped (not a link, a self-link, an unknown node id or a value not above 0)." in h
        assert "NaN" not in h and "undefined" not in h and "[object Object]" not in h


def test_label_and_group_are_cut_to_24_and_20_characters():
    h = _py(PAYLOADS["long_labels"])
    nodes = _tables(h)[0][1]
    assert nodes[0][0] == "A label of exactly twent" and nodes[0][1] == "A very long group na"


def test_caps_are_noted():
    h = _py(PAYLOADS["forty_one_nodes"])
    assert len(_dots(h)) == 40 and "1 node beyond the first 40 was not drawn." in h
    assert "1 link was dropped (not a link, a self-link, an unknown node id or a value not above 0)." in h      # the link to the 41st node
    h = _py(PAYLOADS["links_121"])
    assert len(_arcs(h)) == 120 and "1 link beyond the first 120 was not drawn." in h


def test_too_few_or_no_nodes_gives_a_note_and_no_chart():
    for k in ("too_few", "no_nodes", "nodes_not_list"):
        h = _py(PAYLOADS[k])
        assert "An arc diagram needs at least 2 nodes." in h
        assert 'role="img"' not in h and "<table" not in h and "NaN" not in h
    assert ">T</div>" in _py(PAYLOADS["too_few"])


def test_unknown_or_malformed_order_is_input_order():
    plain = {k: v for k, v in PAYLOADS["bad_order"].items() if k != "order"}
    assert _py(PAYLOADS["bad_order"]) == _py(dict(plain, order="input")) == _py(plain) == _py(PAYLOADS["order_junk"])


def test_no_links_draws_the_nodes_alone():
    h = _py(PAYLOADS["no_links"])
    assert len(_dots(h)) == 3 and _arcs(h) == [] and h == _py(PAYLOADS["no_links_key"])


def test_version_above_one_is_noted_and_otherwise_silent(core_js):
    for h in (_py(PAYLOADS["version_2"]), _gas_batch(core_js, [PAYLOADS["version_2"]])[0]):
        assert "Written for arc_diagram version 2; drawn as version 1." in h
    assert "version" not in _py(PAYLOADS["version_junk"]).lower()
    assert _py(dict(MODULES, version=1)) == _py(MODULES)


# ─── the label rule ────────────────────────────────────────────────────────────────────────────────────────────
def _labels(html):
    return [(int(m.group(1) or 0), float(m.group(2)), m.group(3)) for m in re.finditer(r'<div class="adl(?: tmw(\d+))?" style="position:absolute;left:([\d.]+)%;top:0;[^"]*">(.*?)</div>', html)]


def test_every_node_has_a_label_and_the_gate_thins_them_by_halves():
    h = _py(PAYLOADS["forty"])
    labs = _labels(h)
    assert len(labs) == 40
    n = 40
    for i, (g, left, text) in enumerate(labs):
        lvl = 99 if i == 0 else min((i & -i).bit_length() - 1, 6)
        want = 0 if i == 0 else int(math.ceil((16 * n / 2 ** lvl + 16) / 10)) * 10
        assert g == (want if want > 160 else 0), (i, g, want)
    ws = sorted({g for g, *_ in labs if g})
    css = re.search(r"<style>(.*?)</style>", h).group(1)
    assert ws and all("@container (width<%dpx){.tmw%d{display:none}}" % (w, w) in css for w in ws) and max(ws) == 660
    assert len(_labels(_py(MODULES))) == 8 and all(g == 0 for g, *_ in _labels(_py(MODULES)))     # 8 nodes: 16 * 8 + 16 = 144 px, always drawn


def test_registered_as_a_stable_charts_atom_with_an_example_and_every_field_documented():
    blocks = {a["type"]: a for a in yaml.safe_load((ROOT / "atoms/schema.yaml").read_text())["blocks"]}
    a = blocks["arc_diagram"]
    assert a["stage"] == "stable" and set(a["fields"]) == {"title", "nodes", "links", "order", "unit", "version"}
    assert a["surfaces"] == blocks["treemap"]["surfaces"] and a["source"] == blocks["treemap"]["source"]
    assert "chord" in a["routing_text"] and "sankey" in a["routing_text"] and len(a["intent_phrases"]) == 3
    assert re.search(r"^a2ui-charts-v1:\n(?:- .*\n)*- arc_diagram$", (ROOT / "atoms/atom-packs.yaml").read_text(), re.M)
    assert '"arc_diagram":"a2ui-charts-v1"' in (ROOT / "apps-script-surface/gas-wired-renderer/PackMap.gs").read_text()
    import generate_atom_pages as g
    ex = g._EXAMPLE_BLOCKS["arc_diagram"]
    assert ex["type"] == "arc_diagram" and "<table" in _py(ex) and "<circle" in _py(ex) and "<path" in _py(ex)
    txt = (ROOT / "atoms/schema.yaml").read_text()
    assert txt.index("- type: arc_diagram") < txt.index("# ── Motion candidates (2026-10-10, preview) ──")


def test_d3_credit_names_scale_point():
    t = (ROOT / "THIRD-PARTY-NOTICES.md").read_text()
    assert "scalePoint" in t and "tests/test_arc_diagram.py" in t
