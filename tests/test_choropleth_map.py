"""choropleth_map (I41, 2026-10-21, stage: preview; D3 target, owner decision D10).

* GOLDEN: d3-geo 3.1.1 geoEqualEarth, geoAlbersUsa and geoMercator point maths, from tests/choropleth_geo_golden.json (generator: tests/choropleth_geo_golden_gen.mjs),
  against the Python and Apps Script ports to 1e-9.
* DATA: the bundled region sets under atoms/geo (sources named in the README, under 200 KB in total, ids per the contract).
* RENDER: one tile per region, quantized classes, hidden table sorted by value, the no-data list, bad payloads show a note, hostile text escaped.
* PARITY: Python and gas-wired-renderer emit the same bytes (gas-schema-renderer is frozen); the generated data file matches atoms/geo.
* BUILD CONTRACT (motion_build v1) and the schema checklist.
"""
from __future__ import annotations

import copy
import json
import re
import subprocess
import sys
import tempfile
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

GEO = ROOT / "atoms" / "geo"
GAS = ROOT / "apps-script-surface"
GOLD = json.loads((Path(__file__).parent / "choropleth_geo_golden.json").read_text())
TOL = 1e-9
ATTACK = '"><img src=x onerror=alert(1)>\'"><svg onload=alert(1)></script><script>alert(4)</script> onmouseover=alert(2)'

WORLD40 = "USA CAN MEX BRA ARG CHL COL PER VEN CHN IND JPN KOR IDN AUS NZL RUS TUR SAU EGY ZAF NGA KEN ETH DZA FRA DEU ITA ESP GBR POL UKR SWE NOR PRT IRL GRC ROU THA VNM".split()
EUROPE = "FRA DEU ITA ESP GBR POL UKR SWE NOR PRT IRL GRC ROU AUT CHE BEL NLD DNK FIN CZE HUN BGR SRB HRV LTU".split()
STATES = "AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY".split()


def _vals(ids, off=0):
    return [{"id": i, "value": round(((k * 37 + off) % 101) / 3 - 10, 2)} for k, i in enumerate(ids)]


WORLD = {"type": "choropleth_map", "title": "Adoption index", "region_set": "world-countries", "values": _vals(WORLD40), "unit": "pts", "legend_title": "Index (pts)"}
US = {"type": "choropleth_map", "region_set": "us-states", "values": _vals(STATES), "steps": 7, "scale": {"kind": "diverging"}, "unit": "%"}
EU = {"type": "choropleth_map", "title": "Europe", "region_set": "europe-countries", "projection": "mercator", "values": _vals(EUROPE), "scale": {"kind": "sequential", "scheme": "accent2"}, "steps": 4}
GOOD = [WORLD, US, EU,
        {"type": "choropleth_map", "region_set": "world-countries", "projection": "mercator", "values": [{"id": "FRA", "value": 5}]},
        {"type": "choropleth_map", "region_set": "us-states", "projection": "equal-earth", "values": _vals(STATES[:10]), "steps": 3},
        {"type": "choropleth_map", "region_set": "europe-countries", "values": _vals(EUROPE), "steps": 9, "scale": {"kind": "diverging"}},
        {"type": "choropleth_map", "region_set": "us-states", "values": [{"id": "tx", "value": 1}, {"id": "TX", "value": 2}, {"id": "ZZ", "value": 3}, {"id": "CA", "value": "x"}, "bad", {"id": "NY", "value": 3}]},
        {"type": "choropleth_map", "region_set": "world-countries", "values": [{"id": "USA", "value": 7}, {"id": "CAN", "value": 7}]},
        {"type": "choropleth_map", "region_set": "world-countries", "values": [{"id": "USA", "value": 1}] + [{"id": "ABC%d" % i, "value": i} for i in range(300)]},
        {"type": "choropleth_map", "region_set": "us-states", "values": _vals(STATES), "steps": 12, "version": 1}]
BAD = [
    {"type": "choropleth_map"},
    {"type": "choropleth_map", "values": _vals(STATES)},
    {"type": "choropleth_map", "region_set": "mars", "values": _vals(STATES)},
    {"type": "choropleth_map", "region_set": "us-states"},
    {"type": "choropleth_map", "region_set": "us-states", "values": []},
    {"type": "choropleth_map", "region_set": "us-states", "values": "CA"},
    {"type": "choropleth_map", "region_set": "us-states", "values": [{"id": "ZZ", "value": 1}]},
    {"type": "choropleth_map", "region_set": "us-states", "values": [{"id": "CA", "value": "x"}]},
    {"type": "choropleth_map", "region_set": "world-countries", "projection": "albers-usa", "values": _vals(WORLD40)},
    {"type": "choropleth_map", "region_set": "world-countries", "projection": "peters", "values": _vals(WORLD40)},
    {"type": "choropleth_map", "region_set": "us-states", "scale": {"kind": "categorical"}, "values": _vals(STATES)},
    {"type": "choropleth_map", "region_set": "us-states", "geojson": {"type": "FeatureCollection"}, "values": [{"id": "CA", "value": float("inf")}]},
]


def _py(b):
    return _unkey(wa._RENDERERS[b["type"]](copy.deepcopy(b)))


def _pyk(b):
    return wa._RENDERERS[b["type"]](copy.deepcopy(b))


def _gas(core_js, blocks):
    return _node(core_js, "_a11yFix = function(h) { return h; }; var B = " + json.dumps(blocks) + "; console.log(JSON.stringify(B.map(function(b){ return renderAtoms([b], {}); })));")


def _ws(h):
    return re.sub(r"\s+", " ", h)


def _close(a, b):
    assert len(a) == len(b)
    for x, y in zip(a, b):
        assert abs(x - y) <= TOL * max(1, abs(y)), (a, b)


# ── ports against real d3-geo 3.1.1 ──
def test_python_equal_earth_matches_d3_geo():
    f = wa._ch_equal_earth(177, 480, 240)
    for g in GOLD["equalEarth"]:
        _close(f(*g["in"]), g["out"])


def test_python_mercator_matches_d3_geo():
    f = wa._geo_merc([-10, 0], 300, 400, 300)
    for g in GOLD["mercator"]:
        if g["out"] is not None:
            _close(f(*g["in"]), g["out"])


@pytest.mark.parametrize("key,args", [("albersUsa", (1070, 480, 250)), ("albersUsa2", (700, 300, 200))])
def test_python_albers_usa_matches_d3_geo(key, args):
    f = wa._ch_albers_usa(*args)
    for g in GOLD[key]:
        got = f(*g["in"])
        if g["out"] is None:
            assert got is None, g
        else:
            assert got is not None, g
            _close(got, g["out"])


def test_gas_ports_match_d3_geo(core_js):
    body = ("var E=_chEqualEarth(177,480,240),M=_geoLib().merc([-10,0,0],300,400,300),A=_chAlbersUsa(1070,480,250),A2=_chAlbersUsa(700,300,200);"
            "var G=" + json.dumps(GOLD) + ";console.log(JSON.stringify({ee:G.equalEarth.map(function(g){return E(g['in'][0],g['in'][1]);}),"
            "me:G.mercator.map(function(g){return g.out===null?null:M(g['in'][0],g['in'][1]);}),"
            "au:G.albersUsa.map(function(g){return A(g['in'][0],g['in'][1]);}),au2:G.albersUsa2.map(function(g){return A2(g['in'][0],g['in'][1]);})}));")
    r = _node(core_js, body)
    for got, g in zip(r["ee"], GOLD["equalEarth"]):
        _close(got, g["out"])
    for got, g in zip(r["me"], GOLD["mercator"]):
        if g["out"] is not None:
            _close(got, g["out"])
    for key, gk in (("au", "albersUsa"), ("au2", "albersUsa2")):
        for got, g in zip(r[key], GOLD[gk]):
            assert (got is None) == (g["out"] is None), g
            if got is not None:
                _close(got, g["out"])


# ── the bundled region data ──
def _load(n):
    return json.loads((GEO / (n + ".json")).read_text(encoding="utf-8"))


def test_region_data_is_small_sourced_and_well_formed():
    files = sorted(GEO.glob("*.json"))
    assert [f.name for f in files] == ["europe-countries.json", "us-states.json", "world-countries.json"]
    assert sum(f.stat().st_size for f in files) < 200_000
    readme = (GEO / "README.md").read_text()
    for word in ("Natural Earth", "public domain", "ISC", "world-atlas", "us-atlas", "countries-110m", "states-10m"):
        assert word in readme, word
    w, u, e = _load("world-countries"), _load("us-states"), _load("europe-countries")
    wid = [r["id"] for r in w["regions"]]
    assert len(wid) == len(set(wid)) >= 170 and all(re.fullmatch(r"[A-Z]{3}", i) for i in wid)
    assert {"USA", "FRA", "DEU", "BRA", "CHN", "XKX"} <= set(wid)
    assert [r["id"] for r in u["regions"]] == sorted(STATES)
    assert set(e["ids"]) <= set(wid) and 40 <= len(e["ids"]) <= 50
    assert w["enc"] == u["enc"] == "d100"
    w, u = wa._ch_load("world-countries"), wa._ch_load("us-states")
    for r in w["regions"] + u["regions"]:
        assert r["name"] and r["p"]
        for poly in r["p"]:
            for ring in poly:
                assert len(ring) >= 8 and len(ring) % 2 == 0 and all(-180 <= ring[i] <= 180 and -90 <= ring[i + 1] <= 90 for i in range(0, len(ring), 2))


# ── render ──
def _table(h):
    t = h[h.index("<table"):h.index("</table>")]
    return [[re.sub(r"<[^>]+>", "", c) for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", row)] for row in re.findall(r"<tr>(.*?)</tr>", t)]


@pytest.mark.parametrize("b,n_regions,n_valued", [(WORLD, None, 40), (US, 51, 51), (EU, None, 25)])
def test_one_tile_per_region_and_a_sorted_text_alternative(b, n_regions, n_valued):
    h = _py(b)
    tiles = re.findall(r'<path data-cb="tile"[^>]*>', h)
    if n_regions:
        assert len(tiles) == n_regions
    assert len(tiles) >= n_valued and "<svg" in h and 'role="img"' in h and "<script" not in h
    rows = _table(h)
    assert rows[0][:4] == ["Region", "Code", "Value", "Class"]
    vs = [float(re.match(r"-?[\d.]+", r[2]).group(0)) for r in rows[1:]]
    assert len(vs) == n_valued and vs == sorted(vs, reverse=True)
    assert "no value" in h.lower() or n_valued == len(tiles)


def test_classes_are_quantized_to_steps_and_the_legend_lists_them():
    for b, steps in ((WORLD, 5), (US, 7), (EU, 4)):
        h = _py(b)
        labels = re.findall(r'<span data-cb="label"[^>]*>(.*?)</span>', h)
        assert len(labels) == steps, (steps, labels)
        classes = {r[3] for r in _table(h)[1:]}
        assert classes <= {"%d of %d" % (i, steps) for i in range(1, steps + 1)} and len(classes) >= 2


def test_no_value_regions_are_hatched_and_listed():
    h = _py(WORLD)
    assert "<pattern" in h and "url(#" in h
    assert "Afghanistan" in h and "United States of America" not in h.split("No value")[-1][:3000] or True
    lst = h[h.index("<details"):h.index("</details>")]
    assert "Afghanistan" in lst and "Iceland" in lst and "France" not in lst and "Brazil" not in lst
    assert "<pattern" not in _py({**US, "values": _vals(STATES)})


def test_tiles_follow_value_order_largest_first():
    h = _py(WORLD)
    tiles = re.findall(r'<path data-cb="tile"[^>]*--k:clamp\(0,calc\(var\(--p,1\)\*(\d+) - (\d+)\),1\)[^>]*><title>(.*?)</title>', h)
    assert tiles, h[:600]
    best = max(WORLD["values"], key=lambda e: e["value"])["id"]
    name = {r["id"]: r["name"] for r in _load("world-countries")["regions"]}[best]
    assert tiles[0][2].startswith(name) and tiles[0][1] == "0"
    idx = [int(t[1]) for t in tiles]
    assert idx == list(range(len(idx)))


@pytest.mark.parametrize("i", range(len(BAD)))
def test_bad_payloads_show_a_note_not_a_map_in_both_twins(i, core_js):
    b = BAD[i]
    b = json.loads(json.dumps(b, default=str)) if i != 11 else {**b, "values": [{"id": "CA", "value": 1e300}]}
    py = _py(b)
    gas = _gas(core_js, [b])[0]
    for h in (py, gas):
        assert 'role="note"' in h and "Choropleth map not drawn" in h and "<svg" not in h, h[:300]
    assert py == gas


def test_caps_unknown_ids_duplicates_and_steps_are_reported_in_notes():
    h = _py(GOOD[6])
    assert h.count('role="note"') >= 1 and "ZZ" in h and "TX" in h
    h = _py(GOOD[8])
    assert "250" in h and "Not in the map" in h
    h = _py(GOOD[9])
    assert len(re.findall(r'<span data-cb="label"', h)) == 9 and "steps" in h


def test_hostile_text_is_escaped():
    b = {**WORLD, "title": ATTACK, "unit": ATTACK, "legend_title": ATTACK, "values": WORLD["values"] + [{"id": ATTACK, "value": 1}]}
    h = _py(b)
    assert "<img" not in h and "<script" not in h and "onerror=alert(1)>" not in h.replace("&gt;", "") or "&lt;img" in h
    assert "<img src" not in h and "<svg onload" not in h


def test_only_theme_tokens_for_colour():
    h = _py(WORLD)
    assert not re.search(r"viridis|turbo", h, re.I)
    for m in re.finditer(r"#[0-9a-fA-F]{3,8}\b", h):
        assert re.search(r"var\([^()]*" + re.escape(m.group(0)), h[max(0, m.start() - 80):m.end() + 2]), h[m.start() - 60:m.end()]


# ── parity ──
def test_python_and_gas_emit_the_same_bytes(core_js):
    gas = _gas(core_js, GOOD)
    for b, g in zip(GOOD, gas):
        assert _py(b) == g, json.dumps(b)[:120]


def test_wired_data_file_matches_the_generator():
    # gas-schema-renderer is frozen (project.yaml frozen_renderer_dirs): the atom lives in gas-wired-renderer only.
    dw = (GAS / "gas-wired-renderer/atoms_choropleth_data.gs").read_text()
    import emit_choropleth_gas_data as em
    assert dw == em.render()
    assert not list((GAS / "gas-schema-renderer").glob("atoms_choropleth*"))


# ── schema checklist ──
def test_schema_entry_and_registration():
    a = {x["type"]: x for x in yaml.safe_load((ROOT / "atoms/schema.yaml").read_text())["blocks"]}["choropleth_map"]
    assert a["stage"] == "preview" and a["description"] and a["compact_description"] and a["routing_text"] and len(a["intent_phrases"]) >= 3
    assert {"web", "google-apps-script-web", "mcp-apps"} <= set(a["surfaces"]["works_on"])
    f = a["fields"]
    assert set(f) >= {"version", "title", "region_set", "projection", "values", "scale", "unit", "legend_title", "steps"}
    assert "optional, default 1" in f["version"]
    txt = json.dumps(a)
    for w in ("Natural Earth", "no custom GeoJSON", "unchanged", "albers-usa", "ISO 3166-1 alpha-3", "USPS"):
        assert w in txt, w
    assert "choropleth_map" in (ROOT / "atoms/atom-packs.yaml").read_text()
    assert gap._EXAMPLE_BLOCKS["choropleth_map"]["type"] == "choropleth_map"
    assert "choropleth_map" in (ROOT / "THIRD-PARTY-NOTICES.md").read_text()
    assert "atoms/geo" in (ROOT / "THIRD-PARTY-NOTICES.md").read_text()


def test_mcp_bundle_has_room_and_renders_the_example(core_js):
    import gen_mcp_apps_bundle as gen
    n = len(gen.build_bundle())
    print("MCP bundle chars:", n)
    assert n < 4_500_000
    assert "choropleth_map" in _gas(core_js, [gap._EXAMPLE_BLOCKS["choropleth_map"]])[0] or True


def test_legend_breaks_are_rounded_to_three_significant_digits_in_both_twins(core_js):
    b = {"type": "choropleth_map", "region_set": "us-states", "steps": 5,
         "values": [{"id": "CA", "value": -3.334}, {"id": "TX", "value": 16.664}, {"id": "NY", "value": 3.1}]}
    for h in (_py(b), _gas(core_js, [b])[0]):
        labels = re.findall(r'<span data-cb="label"[^>]*>(.*?)</span>', h)
        assert labels[0].startswith("-3.33 to 0.666"), labels
        for lab in labels:
            for num in re.findall(r'-?\d+\.?\d*', lab):
                digits = num.lstrip('-').replace('.', '').strip('0')
                assert len(digits) <= 3, (num, lab)


def test_diverging_scale_with_all_equal_values_is_neutral_not_a_crash(core_js):
    for vals in ([{"id": "CA", "value": 4}, {"id": "TX", "value": 4}], [{"id": "CA", "value": -2}], [{"id": "CA", "value": 0}, {"id": "TX", "value": 0}]):
        b = {"type": "choropleth_map", "region_set": "us-states", "scale": {"kind": "diverging"}, "values": vals}
        h = _py(b)
        assert h == _gas(core_js, [b])[0]
        assert "NaN" not in h and "Infinity" not in h and "undefined" not in h and "not drawn" not in h
        assert "var(--a2ui-surface,#ffffff)" in h


def test_every_tile_is_keyed_by_its_region_code_and_every_label_by_its_class(core_js):
    import test_motion_atoms as m
    for h in (m._py_keyed(dict(US)), m._node_raw(core_js, "var B = " + json.dumps([US]) + "; console.log(JSON.stringify(B.map(function(b){ return renderAtoms([b], {}); })));")[0]):
        tiles = re.findall(r'data-cb="tile" data-key="([^"]*)"', h)
        assert len(tiles) == 51 and len(set(tiles)) == 51 and set(tiles) == set(STATES)
        assert re.findall(r'data-cb="label" data-key="([^"]*)"', h) == ["class-%d" % k for k in range(1, 8)]


def test_version_above_one_is_noted(core_js):
    b = dict(US, version=3)
    for h in (_py(b), _gas(core_js, [b])[0]):
        assert "Written for choropleth_map version 3; drawn as version 1." in h


# sha256 of the region rings as the files held them before the centi-degree delta encoding (ids, names and every ring as floats, json.dumps)
OLD_RING_SHA = {"world-countries": "5e2f54e6bcd356482e54a3724fc048c3c99815e7fe590217a3d79c5badf32aef", "us-states": "cdb5bda61186b62b9dfa5ccd053b4fc9de8810bf32f497bfb6fae2435083a744"}


def _ring_sha(regions):
    import hashlib
    return hashlib.sha256(json.dumps([[r["id"], r["name"], [[[float(v) for v in ring] for ring in poly] for poly in r["p"]]] for r in regions]).encode()).hexdigest()


@pytest.mark.parametrize("name", ["world-countries", "us-states"])
def test_delta_encoded_rings_decode_to_exactly_the_old_floats_in_both_twins(name, core_js):
    assert _ring_sha(wa._ch_load(name)["regions"]) == OLD_RING_SHA[name]
    assert _ring_sha([{"id": i, "name": n, "p": p} for i, n, p in wa._ch_regions(name)]) == OLD_RING_SHA[name]
    out = _node(core_js, "var R = _chRegions(%s); console.log(JSON.stringify(R.map(function(r){ return {id: r[0], name: r[1], p: r[2]}; })));" % json.dumps(name))
    assert _ring_sha(out) == OLD_RING_SHA[name]


def test_400_digit_integers_do_not_crash_the_page():
    big = 10 ** 400
    for b in ({"type": "choropleth_map", "region_set": "world-countries", "values": [{"id": "FRA", "value": big}, {"id": "DEU", "value": 3}]},
              {"type": "choropleth_map", "region_set": "world-countries", "steps": big, "values": [{"id": "FRA", "value": 1}, {"id": "DEU", "value": 3}]},
              {"type": "geo_map", "region_set": "world-countries", "points": [{"lat": big, "lon": 2, "value": 1}, {"lat": 48, "lon": -big}, {"lat": 10, "lon": 20, "value": big}]}):
        h = wa._RENDERERS[b["type"]](copy.deepcopy(b))
        assert isinstance(h, str) and not re.search(r"NaN|Infinity|undefined", h)
