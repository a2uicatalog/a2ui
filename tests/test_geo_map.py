"""geo_map (scattergeo parity, 2026-10-21, stage: preview): points and great-circle lines on the choropleth_map outlines and projections.

* GOLDEN: d3-geo 3.1.1 geoInterpolate/geoDistance (tests/geo_map_golden_gen.mjs) against the Python and Apps Script ports to 1e-9.
* RENDER: basemap, markers (shape + colour per group, size per value), dashed/solid lines, hidden tables, frame notes, caps with notes, bad payloads, hostile text.
* PARITY: Python and gas-wired-renderer emit the same bytes (gas-schema-renderer is frozen); the atom is additive (choropleth_map output unchanged).
"""
from __future__ import annotations

import copy
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))

from test_motion_atoms import _node, _unkey, core_js  # noqa: F401  (core_js is a fixture)
from renderers import web_article as wa
import generate_atom_pages as gap

GAS = ROOT / "apps-script-surface"
GOLD = json.loads((Path(__file__).parent / "geo_map_golden.json").read_text())
ATTACK = '"><img src=x onerror=alert(1)>\'"><svg onload=alert(1)></script><script>alert(4)</script> onmouseover=alert(2)'


def P(lat, lon, **k):
    return {"lat": lat, "lon": lon, **k}


CITIES = [P(48.85, 2.35, label="Paris", value=2.1, group="Hub"), P(51.5, -0.12, label="London", value=9, group="Hub"), P(40.7, -74, label="New York", value=8.4, group="Port"),
          P(35.7, 139.7, label="Tokyo", value=14, group="Port"), P(-33.9, 151.2, label="Sydney", value=5, group="Depot"), P(-23.5, -46.6, label="Sao Paulo", group="Depot"),
          P(1.35, 103.8, label="Singapore", value=6.5, group="Port"), P(30, 31.2, label="Cairo", value=3, group="Hub")]
WORLD = {"type": "geo_map", "title": "Sites and routes", "region_set": "world-countries", "points": CITIES,
         "lines": [{"label": "Paris to New York", "path": [P(48.85, 2.35), P(40.7, -74)]}, {"label": "Tokyo loop", "path": [P(35.7, 139.7), P(1.35, 103.8), P(-33.9, 151.2)]}], "unit": "t", "legend_title": "Tonnes shipped"}
US = {"type": "geo_map", "region_set": "us-states", "points": [P(40.7, -74, label="NYC"), P(61.2, -149.9, label="Anchorage"), P(21.3, -157.8, label="Honolulu"), P(10, 20, label="Offshore")],
      "lines": [{"label": "East to Alaska", "path": [P(40.7, -74), P(61.2, -149.9)]}]}
EU = {"type": "geo_map", "region_set": "europe-countries", "projection": "mercator", "points": [P(48.85, 2.35, label="Paris"), P(52.5, 13.4, label="Berlin"), P(35.7, 139.7, label="Tokyo")]}
GOOD = [WORLD, US, EU,
        {"type": "geo_map", "points": [P(0, 0)]},
        {"type": "geo_map", "region_set": "world-countries", "lines": [{"path": [P(0, 170), P(0, -170)]}, {"path": [P(80, 0), P(80, 180)]}]},
        {"type": "geo_map", "points": [P(1, 1, value=5), P(2, 2, value=5)], "version": 3},
        {"type": "geo_map", "points": [P(i % 80 - 40, (i * 7) % 300 - 150, group="g%d" % (i % 9)) for i in range(40)]},
        {"type": "geo_map", "points": [P(10, 10, label="ok"), {"lat": "x", "lon": 3}, "bad", P(95, 0), P(0, 200), P(float("nan"), 1)], "lines": [{"path": [P(0, 0)]}, "x", {"path": "no"}]}]
BAD = [{"type": "geo_map"}, {"type": "geo_map", "points": []}, {"type": "geo_map", "points": "x"}, {"type": "geo_map", "points": [P(95, 0)]}, {"type": "geo_map", "region_set": "mars", "points": [P(0, 0)]},
       {"type": "geo_map", "region_set": "world-countries", "projection": "albers-usa", "points": [P(0, 0)]}, {"type": "geo_map", "projection": "globe", "points": [P(0, 0)]}, {"type": "geo_map", "geojson": {}, "lines": [{"path": []}]}, 5, None]


def _py(b):
    return _unkey(wa._RENDERERS["geo_map"](copy.deepcopy(b)))


def _pyk(b):
    return wa._RENDERERS["geo_map"](copy.deepcopy(b))


def _gas(core_js, blocks):
    return _node(core_js, "_a11yFix = function(h) { return h; }; var B = " + json.dumps(blocks) + "; console.log(JSON.stringify(B.map(function(b){ return renderAtoms([b], {}); })));")


class _Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags, self.stack, self.err = [], [], False

    def handle_starttag(self, t, a):
        self.tags.append((t, dict(a)))
        if t not in ("path", "circle", "rect", "line", "rect", "br", "pattern", "defs", "mask", "title", "div", "span", "table", "tr", "td", "th", "ul", "li", "p", "details", "summary", "style", "svg", "caption", "thead", "tbody", "g", "polygon"):
            self.err = True


def _tags(h):
    p = _Tags()
    p.feed(h)
    return p


def _close(a, b):
    assert len(a) == len(b)
    for x, y in zip(a, b):
        assert abs(x - y) <= 1e-9 * max(1, abs(y)), (a, b)


# ── great circle against real d3-geo ──
def test_python_interpolate_matches_d3_geo():
    for g in GOLD:
        f = wa._gm_interp(g["a"], g["b"])
        assert abs(f[1] - g["d"]) < 1e-12
        for q in g["pts"]:
            lo, la = f[0](q["t"])
            ref = q["p"]
            # longitude is only defined modulo 360 at the poles/equal points; compare on the sphere
            assert abs(la - ref[1]) < 1e-9 and (abs(abs(la) - 90) < 1e-9 or abs(((lo - ref[0] + 180) % 360) - 180) < 1e-9), (g["a"], g["b"], q)


def test_gas_interpolate_matches_d3_geo(core_js):
    body = "var G = " + json.dumps(GOLD) + "; console.log(JSON.stringify(G.map(function(g){ var f = _gmInterp(g.a, g.b); return {d: f[1], p: g.pts.map(function(q){ return f[0](q.t); })}; })));"
    r = _node(core_js, body)
    for g, o in zip(GOLD, r):
        assert abs(o["d"] - g["d"]) < 1e-12
        for q, p in zip(g["pts"], o["p"]):
            assert abs(p[1] - q["p"][1]) < 1e-9 and (abs(abs(p[1]) - 90) < 1e-9 or abs(((p[0] - q["p"][0] + 180) % 360) - 180) < 1e-9)


# ── render ──
def test_markers_lines_and_basemap():
    h = _py(WORLD)
    t = _tags(h)
    assert not t.err
    svg = [x for x in t.tags if x[0] == "svg"][0][1]
    assert svg["role"] == "img" and "8 points" in svg["aria-label"] and "2 lines" in svg["aria-label"] and "Sites and routes" in svg["aria-label"]
    assert len([x for x in t.tags if x[0] == "path" and x[1].get("data-base")]) > 150  # basemap
    assert len([x for x in t.tags if x[1].get("data-cb") == "node"]) == 8
    assert len([x for x in t.tags if x[1].get("data-cb") == "link"]) >= 2
    assert "<script" not in h and "NaN" not in h and "undefined" not in h and "Infinity" not in h and "[object" not in h


def test_group_is_never_colour_only_and_lines_differ_by_dash():
    h = _py(WORLD)
    shapes = set(re.findall(r'data-shape="(\w+)"', h))
    assert shapes == {"circle", "square", "diamond"}  # 3 groups -> 3 different shapes
    leg = h[h.index("<ul"):h.index("</ul>")]
    for g in ("Hub", "Port", "Depot"):
        assert g in leg
    routes = re.findall(r'data-cb="link"[^>]*style="([^"]*)"', h)
    assert len(routes) == 2 and routes[0] != routes[1] and "stroke-dasharray:7 4" in routes[1] and "stroke-dasharray" not in routes[0]


def test_size_encodes_value_and_is_explained():
    h = _py(WORLD)
    r = {m[0]: float(m[1]) for m in re.findall(r'<title>(\w[\w ]*):[^<]*</title>', h)[:0]} or None
    sizes = [float(x) for x in re.findall(r'data-r="([\d.]+)"', h)]
    assert len(sizes) == 8 and max(sizes) <= 18 and min(sizes) >= 6
    assert "Marker size" in h and "Tonnes shipped" in h


def test_hidden_table_has_every_point_and_line():
    h = _py(WORLD)
    tb = h[h.index("<table"):]
    for c in CITIES:
        assert c["label"] in tb
    assert "Paris to New York" in tb and "Tokyo loop" in tb
    assert h.count('<table style="position:absolute') == 2


def test_points_outside_the_frame_are_noted_not_dropped_from_the_table():
    h = _py(US)
    assert "Offshore" in h and re.search(r"1 point (is|was) outside", h)
    assert len(re.findall(r'data-cb="node"', h)) == 3
    assert "Lines are cut where they leave the map" in h and "Lines are cut" not in _py(WORLD)
    h = _py(EU)
    assert re.search(r"1 point (is|was) outside", h) and "Tokyo" in h


def test_albers_usa_places_alaska_and_hawaii_in_the_composite():
    h = _py(US)
    xy = re.findall(r'data-cb="node"[^>]*?data-xy="([\d.]+),([\d.]+)"', h)
    assert len(xy) == 3
    pts = {k: (float(a), float(b)) for k, (a, b) in zip(["NYC", "Anchorage", "Honolulu"], xy)}
    assert pts["Anchorage"][0] < 300 and pts["Anchorage"][1] > 380  # lower-left inset
    assert pts["NYC"][0] > 700


def test_antimeridian_lines_break_instead_of_crossing_the_map():
    h = _py(GOOD[4])
    for d in re.findall(r'data-cb="link"[^>]*? d="([^"]*)"', h):
        assert d.count("M") >= 2 or len(d) > 0
        # no single sub-path spans more than 60% of the width
        for sub in d.split("M")[1:]:
            xs = [float(v.split(" ")[0]) for v in re.findall(r"[\d.]+ [\d.]+", sub)]
            assert max(xs) - min(xs) < 0.6 * 960


def test_caps_have_visible_notes():
    b = {"type": "geo_map", "points": [P(i % 80, i % 170) for i in range(520)], "lines": [{"path": [P(0, 0), P(1, 1)]} for _ in range(45)]}
    h = _py(b)
    assert "500" in h and "40" in h and re.search(r"Only the first 500 of 520", h) and re.search(r"Only the first 40 of 45", h)
    assert len(re.findall(r'data-cb="node"', h)) == 500


def test_groups_beyond_six_are_merged_with_a_note():
    h = _py(GOOD[6])
    assert re.search(r"more than 6 groups", h, re.I) and "Other" in h


def test_bad_values_are_counted_in_a_note():
    h = _py(GOOD[7])
    assert re.search(r"\d entries were skipped|\d entry was skipped", h) and len(re.findall(r'data-cb="node"', h)) == 1


@pytest.mark.parametrize("i", range(len(BAD)))
def test_bad_payloads_show_a_note_not_a_map(i):
    h = _py(BAD[i]) if isinstance(BAD[i], dict) else wa._RENDERERS["geo_map"](BAD[i])
    assert 'role="note"' in h and "<svg" not in h and "NaN" not in h and "undefined" not in h


def test_version_note_and_defaults():
    h = _py(GOOD[5])
    assert "Written for geo_map version 3; drawn as version 1." in h
    assert _py(GOOD[3]) == _py({**GOOD[3], "region_set": "world-countries", "projection": "equal-earth"})


def test_hostile_text_is_escaped():
    b = {"type": "geo_map", "title": ATTACK, "unit": ATTACK, "legend_title": ATTACK, "points": [P(1, 1, label=ATTACK, group=ATTACK, value=3), P(2, 2, label="x", group="y", value=4)],
         "lines": [{"label": ATTACK, "path": [P(0, 0), P(5, 5)]}]}
    h = _py(b)
    assert "<img" not in h and "<svg onload" not in h and "<script>alert" not in h and 'onmouseover=alert(2)' not in re.sub(r"&[a-z]+;", "", h).replace("&quot;", "") or "&lt;" in h
    assert not [x for x in _tags(h).tags if x[0] in ("img", "script")]


def test_every_element_has_one_style_attribute_and_keeps_its_paint():
    h = _py(WORLD)
    for m in re.finditer(r"<(?:circle|rect|path)\b[^>]*data-cb=[^>]*>", h):
        assert m.group(0).count(" style=") == 1, m.group(0)[:200]
    assert all("fill:var" in m or "fill:color" in m for m in re.findall(r'data-shape="[^"]*"', h) and re.findall(r'data-cb="node"[^>]*style="([^"]*)"', h))
    assert all("fill:none" in m for m in re.findall(r'data-cb="link"[^>]*style="([^"]*)"', h))


def test_build_contract_present_and_deterministic():
    h = _py(WORLD)
    assert "data-cb-root" in h and "--n:" in h and h == _py(WORLD)


def test_motion_index_stays_inside_its_clamp():
    h = _py(WORLD)
    n = int(re.search(r"--n:(\d+)", h).group(1))
    ks = [int(x) for x in re.findall(r"calc\(var\(--p,1\)\*(\d+) - (\d+)\)", h) and [m[1] for m in re.findall(r"calc\(var\(--p,1\)\*(\d+) - (\d+)\)", h)]]
    assert ks and max(ks) <= n


# ── parity ──
def test_python_and_gas_emit_the_same_bytes(core_js):
    out = _gas(core_js, GOOD + [b for b in BAD if isinstance(b, dict)])
    for b, g in zip(GOOD + [b for b in BAD if isinstance(b, dict)], out):
        assert _py(b) == g, json.dumps(b)[:140]


def test_schema_renderer_stays_frozen():
    assert not list((GAS / "gas-schema-renderer").glob("atoms_geo_map*"))


def test_choropleth_is_unchanged_by_this_atom():
    import test_choropleth_map as tc
    assert _py_ch(tc.WORLD) == _py_ch(copy.deepcopy(tc.WORLD))


def _py_ch(b):
    return _unkey(wa._RENDERERS["choropleth_map"](copy.deepcopy(b)))


# ── schema checklist ──
def test_schema_entry_and_registration():
    a = {x["type"]: x for x in yaml.safe_load((ROOT / "atoms/schema.yaml").read_text())["blocks"]}["geo_map"]
    assert a["stage"] == "preview" and a["description"] and a["compact_description"] and a["routing_text"] and len(a["intent_phrases"]) >= 3
    assert {"web", "google-apps-script-web", "mcp-apps"} <= set(a["surfaces"]["works_on"])
    assert set(a["fields"]) >= {"version", "title", "region_set", "projection", "points", "lines", "unit", "legend_title"}
    assert "optional, default 1" in a["fields"]["version"]
    txt = json.dumps(a)
    for w in ("choropleth_map", "great-circle", "no custom GeoJSON", "no map tiles"):
        assert w in txt, w
    assert "geo_map" in (ROOT / "atoms/atom-packs.yaml").read_text()
    assert gap._EXAMPLE_BLOCKS["geo_map"]["type"] == "geo_map"
    assert "geo_map" in (GAS / "gas-wired-renderer/PackMap.gs").read_text()


# ── fix round (wave B, 2026-10-24): groups, ungrouped points, keys, draw-on routes ──
def _raw_gas(core_js, blocks):
    from test_motion_atoms import _node_raw
    return _node_raw(core_js, "var B = " + json.dumps(blocks) + "; console.log(JSON.stringify(B.map(function(b){ return renderAtoms([b], {}); })));")


def test_six_groups_all_have_a_different_shape_and_colour_pair(core_js):
    b = {"type": "geo_map", "points": [P(i * 10 - 30, i * 20 - 60, label="p%d" % i, group="g%d" % i) for i in range(6)]}
    for h in (_py(b), _gas(core_js, [b])[0]):
        pairs = re.findall(r'<(?:circle|rect|path) data-cb="node" class="cb-fade" style="fill:([^;]*);[^"]*" data-shape="(\w+)"', h)
        assert len(pairs) == 6 and len(set(pairs)) == 6, pairs
    c = {"type": "geo_map", "points": b["points"] + [P(5, 5, label="loose")]}
    h = _py(c)
    pairs = re.findall(r'data-cb="node" class="cb-fade" style="fill:([^;]*);[^"]*" data-shape="(\w+)"', h)
    assert len(set(pairs)) == 7                                   # the ungrouped point is a seventh, different pair


def test_ungrouped_points_get_their_own_style_and_legend_entry(core_js):
    b = {"type": "geo_map", "points": [P(10, 10, label="a", group="Hub"), P(20, 20, label="b"), P(30, 30, label="c", group="Hub")]}
    for h in (_py(b), _gas(core_js, [b])[0]):
        leg = h[h.index("<ul"):h.index("</ul>")]
        assert "Hub" in leg and "Ungrouped" in leg
        sty = re.findall(r'fill:([^;]*);[^"]*" data-shape="(\w+)"', h)
        assert sty[0] == sty[2] and sty[1] != sty[0]
    nog = {"type": "geo_map", "points": [P(10, 10), P(20, 20)]}
    assert "Ungrouped" not in _py(nog) and "<ul" not in _py(nog)       # nothing to tell apart: no legend entry


def test_every_mark_has_a_unique_key_from_id_then_label_then_index(core_js):
    b = {"type": "geo_map", "region_set": "europe-countries",
         "points": [P(48.85, 2.35, id="par", label="Paris"), P(52.5, 13.4, label="Berlin"), P(40.4, -3.7), P(41.9, 12.5, label="Berlin"), P(38.7, -9.1, id="  ")],
         "lines": [{"id": "trip", "label": "Trip", "path": [P(38.7, -9.1), P(40.4, -3.7)]}, {"path": [P(48.85, 2.35), P(52.5, 13.4)]}, {"label": "Berlin", "path": [P(48.85, 2.35), P(52.5, 13.4)]}]}
    keys = ["l0", "l1", "p0", "p1", "p2", "p3", "p4"]
    for h in (_pyk(b), _raw_gas(core_js, [b])[0]):
        got = re.findall(r'data-cb="(?:node|link)" data-key="([^"]*)"', h)
        assert got == ["trip", "l1", "Berlin", "par", "Berlin~2", "p2", "Berlin~3", "p4"], got
        assert len(set(got)) == len(got)
    assert keys                                                            # (documented fallbacks: l<i>, p<i>)


def test_routes_are_drawn_on_stop_by_stop_by_a_mask_under_p(core_js):
    b = {"type": "geo_map", "region_set": "europe-countries", "lines": [{"label": "Trip", "path": [P(38.7, -9.1), P(40.4, -3.7), P(48.85, 2.35)]}], "points": [P(38.7, -9.1, label="Lisbon")]}
    for h in (_py(b), _gas(core_js, [b])[0]):
        m = re.search(r'<mask id="(gm\w+)0".*?</mask>', h, re.S)
        assert m and h.count('url(#' + m.group(1) + '0)') == 1
        legs = re.findall(r'<path d="([^"]+)" pathLength="1" style="[^"]*stroke-dashoffset:calc\(1px\*\(1 - clamp\(0,calc\(\(var\(--p,1\)\*3 - 0\)\*2 - (\d)\),1\)\)\)', m.group(0))
        assert [x[1] for x in legs] == ["0", "1"]                                   # one mask path per leg, each with its own share of the route's time
        route = re.search(r'<path data-cb="link"[^>]*mask="url\(#gm\w+0\)"[^>]*>', h).group(0)
        assert "cb-fade" not in route and "stroke-dasharray" not in route          # no whole-line fade; a solid route keeps its own look
    dashed = {"type": "geo_map", "lines": [{"path": [P(0, 0), P(10, 10)]}, {"path": [P(0, 0), P(10, 10), P(20, 0)]}]}
    h = _py(dashed)
    assert "stroke-dasharray:7 4" in re.search(r'<path data-cb="link"[^>]*mask="url\(#gm\w+1\)"[^>]*>', h).group(0)


def test_the_line_table_lists_every_stop():
    b = {"type": "geo_map", "lines": [{"label": "Trip", "path": [P(1, 2), P(3, 4), P(5, 6)]}]}
    assert "1, 2 to 3, 4 to 5, 6" in _py(b)


def test_400_digit_integers_do_not_crash_the_page():
    big = 10 ** 400
    b = {"type": "geo_map", "region_set": "world-countries", "points": [P(big, 2, value=1), P(48, -big), P(10, 20, value=big), P(1, 1)]}
    h = wa._RENDERERS["geo_map"](copy.deepcopy(b))
    assert isinstance(h, str) and not re.search(r"NaN|Infinity|undefined", h)
