"""I143 travel story on the geo atoms: frame, categorical choropleth, region shading on geo_map, and a motion_transition pan/zoom between two frames.

* BYTE: payloads without the new fields render exactly the bytes origin/main rendered (hashes in fixtures/geo_travel_baseline.json, made on 515ae5e00).
* FRAME: validated and clamped, fixed 960 x 540 canvas, outlines cropped by the viewBox and not dropped, a long leg is not cut by the zoom.
* CATEGORIES: colour from theme tokens only, a pattern per slot, legend + hidden table + no-category details, hostile text and bad input.
* PARITY: Python and gas-wired-renderer emit the same bytes.
* BROWSER: motion_transition between two frames: every keyed region starts on its partner's box and ends where B alone puts it.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))

from test_motion_atoms import _node, _unkey, core_js  # noqa: F401  (core_js is a fixture)
from test_motion_build import browser  # noqa: E402
from renderers import web_article as wa
import test_geo_map as tg
import test_choropleth_map as tc

ATTACK = tg.ATTACK
LIS, MAD, PAR = (38.72, -9.14), (40.42, -3.70), (48.85, 2.35)
CATS = ["visited", "planned", "not yet"]


def _pt(n, c):
    return {"lat": c[0], "lon": c[1], "label": n, "id": n.lower()}


def _leg(i, a, b):
    return {"id": "leg%d" % i, "label": "Leg %d" % i, "path": [{"lat": a[0], "lon": a[1]}, {"lat": b[0], "lon": b[1]}]}


IBERIA = {"lon_min": -12, "lon_max": 4, "lat_min": 36, "lat_max": 44}
TRIP1 = {"type": "geo_map", "title": "Trip", "projection": "mercator", "frame": IBERIA, "points": [_pt("Lisbon", LIS), _pt("Madrid", MAD)], "lines": [_leg(1, LIS, MAD)],
         "regions": [{"id": "PRT", "category": "visited"}, {"id": "ESP", "category": "visited"}, {"id": "FRA", "category": "planned"}], "categories": CATS}
TRIP2 = {**TRIP1, "frame": {"lon_min": -12, "lon_max": 8, "lat_min": 36, "lat_max": 51}, "points": TRIP1["points"] + [_pt("Paris", PAR)], "lines": TRIP1["lines"] + [_leg(2, MAD, PAR)],
         "regions": [{"id": "PRT", "category": "visited"}, {"id": "ESP", "category": "visited"}, {"id": "FRA", "category": "visited"}]}
CAT = {"type": "choropleth_map", "title": "Visited", "region_set": "europe-countries", "categories": CATS, "category_colors": {"visited": "accent", "planned": "accent2"},
       "values": [{"id": "PRT", "value": "visited"}, {"id": "ESP", "value": "visited"}, {"id": "FRA", "value": "planned"}, {"id": "ITA", "value": "not yet"}]}
FRAMED_CH = {"type": "choropleth_map", "region_set": "world-countries", "projection": "mercator", "frame": IBERIA, "values": [{"id": "PRT", "value": 1}, {"id": "ESP", "value": 5}]}
GOOD = [TRIP1, TRIP2, CAT, FRAMED_CH,
        {**CAT, "categories": ["a", "b", "c", "d", "e", "f", "g"], "values": [{"id": "PRT", "value": "g"}, {"id": "ESP", "value": "a"}, {"id": "FRA", "value": "f"}, {"id": "ITA", "value": "c"}]},
        {**CAT, "values": [{"id": "prt", "value": " visited "}, {"id": "PRT", "value": "planned"}, {"id": "ZZZ", "value": "visited"}, {"id": "ESP", "value": "other"}, {"id": "FRA", "value": 3}, "x"]},
        {**CAT, "category_colors": {"visited": "#ff0000", "planned": "constructor", "not yet": "muted"}},
        {"type": "choropleth_map", "region_set": "us-states", "categories": ["x"], "values": [{"id": "TX", "value": "x"}], "frame": {"lon_min": -100, "lon_max": -90, "lat_min": 25, "lat_max": 35}},
        {"type": "choropleth_map", "region_set": "world-countries", "frame": {"lon_min": 10, "lon_max": 10.2, "lat_min": 45, "lat_max": 45.1}, "values": [{"id": "ITA", "value": 1}]},
        {"type": "choropleth_map", "region_set": "world-countries", "frame": {"lon_min": -999, "lon_max": 999, "lat_min": -999, "lat_max": 999}, "values": [{"id": "ITA", "value": 1}]},
        {"type": "choropleth_map", "region_set": "world-countries", "projection": "mercator", "frame": {"lon_min": 170, "lon_max": 180, "lat_min": -20, "lat_max": -10}, "values": [{"id": "FJI", "value": 1}]},
        {**tg.WORLD, "frame": {"lon_min": -80, "lon_max": 10, "lat_min": 30, "lat_max": 60}},
        {**tg.WORLD, "regions": [{"id": "FRA", "category": "A"}, {"id": "USA", "category": "B"}, {"id": "ZZZ", "category": "C"}, {"id": "FRA", "category": "B"}, "x", {"id": "JPN"}]},
        {**tg.US, "frame": IBERIA, "regions": [{"id": "TX", "category": "visited"}]},
        {**tg.EU, "frame": {"lon_min": "a", "lon_max": 2, "lat_min": 1, "lat_max": 2}, "regions": {"id": "FRA"}},
        {**tg.EU, "frame": {"lon_min": 5, "lon_max": 4, "lat_min": 1, "lat_max": 2}, "regions": [{"id": "FRA", "category": "x"}], "categories": "x"},
        {**tg.EU, "frame": [1, 2, 3, 4], "regions": [{"id": "FRA", "category": ATTACK}], "category_colors": {ATTACK: "accent"}},
        {**tg.EU, "regions": [{"id": "FRA", "category": "x"}], "categories": [1, 2]},
        {"type": "geo_map", "frame": {"lon_min": -180, "lon_max": 180, "lat_min": -85, "lat_max": 85}, "lines": [{"path": [{"lat": 0, "lon": 170}, {"lat": 0, "lon": -170}]}]}]
BAD = [{**CAT, "categories": []}, {**CAT, "categories": "visited"}, {**CAT, "categories": [""]}, {**CAT, "categories": [1]}, {**CAT, "values": [{"id": "PRT", "value": "zzz"}]},
       {**CAT, "values": [{"id": "PRT", "value": 5}]}, {**CAT, "values": []}, {**CAT, "values": "x"}]


def _py(b):
    return _unkey(wa._RENDERERS[b["type"]](copy.deepcopy(b)))


def _pyk(b):
    return wa._RENDERERS[b["type"]](copy.deepcopy(b))


def _gas(core_js, blocks):
    return _node(core_js, "_a11yFix = function(h) { return h; }; var B = " + json.dumps(blocks) + "; console.log(JSON.stringify(B.map(function(b){ return renderAtoms([b], {}); })));")


def _notes(h):
    return re.findall(r'<p role="note"[^>]*>(.*?)</p>', h)


def _viewbox(h):
    return re.search(r'viewBox="0 0 (\d+) (\d+)"', h).groups()


# ── byte identity without the new fields ──
def test_payloads_without_the_new_fields_render_the_bytes_of_origin_main():
    base = json.loads((Path(__file__).parent / "fixtures" / "geo_travel_baseline.json").read_text())
    got = {}
    for i, b in enumerate(tg.GOOD + [x for x in tg.BAD if isinstance(x, dict)]):
        got["g%d" % i] = hashlib.sha256(wa._RENDERERS["geo_map"](copy.deepcopy(b)).encode()).hexdigest()
    for i, b in enumerate(tc.GOOD + tc.BAD):
        got["c%d" % i] = hashlib.sha256(wa._RENDERERS["choropleth_map"](copy.deepcopy(b)).encode()).hexdigest()
    assert got == base


# ── frame ──
def test_frame_gives_a_fixed_960_by_540_canvas_and_keeps_every_outline():
    h = _py(FRAMED_CH)
    assert _viewbox(h) == ("960", "540")
    assert h.count('data-cb="tile"') == len(wa._ch_regions("world-countries"))   # cropped by the viewBox, never dropped
    assert _viewbox(_py({**FRAMED_CH, "frame": {"lon_min": 0, "lon_max": 60, "lat_min": 0, "lat_max": 5}})) == ("960", "540")
    assert _viewbox(_py({**FRAMED_CH, "frame": None})) != ("960", "540")


def test_frame_centres_the_zone_and_markers_land_inside_the_canvas():
    for b in (TRIP1, TRIP2, {**TRIP1, "projection": "equal-earth"}):
        h = _py(b)
        xy = [tuple(map(float, m)) for m in re.findall(r'data-xy="([-\d.]+),([-\d.]+)"', h)]
        assert len(xy) == len(b["points"])
        assert all(0 < x < 960 and 0 < y < 540 for x, y in xy), xy
    xy = {m[0]: (float(m[1]), float(m[2])) for m in re.findall(r'data-key="(\w+)"[^>]*data-xy="([-\d.]+),([-\d.]+)"', _pyk(TRIP1))}
    assert xy["lisbon"][0] < xy["madrid"][0]   # west of Madrid, left of it


def test_a_zoomed_frame_keeps_a_long_leg_whole_where_the_old_rule_would_cut_it():
    z = {"type": "geo_map", "projection": "mercator", "frame": {"lon_min": -9.2, "lon_max": -6.8, "lat_min": 38.4, "lat_max": 39.4},
         "lines": [{"id": "l", "path": [{"lat": 38.7, "lon": -9.1}, {"lat": 39.0, "lon": -6.9}]}]}
    d = re.search(r'data-key="l"[^>]* d="([^"]*)"', _pyk(z)).group(1)
    assert d.count("M") == 1 and len(d.split()) == 4   # one step is wider than half the canvas: the old rule would have broken the path and drawn nothing


def test_antimeridian_legs_still_break_in_a_frame():
    d = re.search(r'data-cb="link"[^>]* d="([^"]*)"', _py(GOOD[-1])).group(1)
    assert d.count("M") >= 2


@pytest.mark.parametrize("fr,word", [("x", "four finite numbers"), ({"lon_min": 1}, "four finite numbers"), ({"lon_min": 5, "lon_max": 4, "lat_min": 1, "lat_max": 2}, "lon_min below"),
                                     ({"lon_min": "1", "lon_max": 2, "lat_min": 1, "lat_max": 2}, "four finite numbers"), ({"lon_min": float("nan"), "lon_max": 2, "lat_min": 1, "lat_max": 2}, "four finite")])
def test_a_bad_frame_draws_the_whole_map_with_a_note(fr, word):
    h = _pyk({**FRAMED_CH, "frame": fr})
    assert any(word in n for n in _notes(h)), _notes(h)
    assert _viewbox(h) != ("960", "540") and 'data-cb="tile"' in h


def test_frame_is_clamped_and_a_tiny_span_widened():
    assert _viewbox(_py({**FRAMED_CH, "frame": {"lon_min": -999, "lon_max": 999, "lat_min": -999, "lat_max": 999}})) == ("960", "540")
    assert wa._ch_frame_read({"lon_min": -999, "lon_max": 999, "lat_min": -999, "lat_max": 999}, "mercator", []) == (-180.0, 180.0, -85.0, 85.0)
    lo0, lo1, la0, la1 = wa._ch_frame_read({"lon_min": 10, "lon_max": 10.2, "lat_min": 45, "lat_max": 45.1}, "mercator", [])
    assert lo1 - lo0 == pytest.approx(1) and la1 - la0 == pytest.approx(1)
    assert wa._ch_frame_read({"lon_min": 5, "lon_max": 4, "lat_min": 1, "lat_max": 2}, "mercator", []) is None


def test_frame_is_ignored_with_a_note_on_albers_usa():
    h = _pyk({**tg.US, "frame": IBERIA})
    assert any("albers-usa" in n for n in _notes(h)) and _viewbox(h) == ("960", "500")


def test_every_outline_of_a_framed_geo_map_is_keyed_by_its_code_and_unframed_ones_stay_unkeyed():
    h = _pyk(TRIP1)
    codes = re.findall(r'data-base="1" data-cb="tile" data-key="(\w+)"', h)
    assert len(codes) == len(wa._ch_regions("world-countries")) and "PRT" in codes and "ESP" in codes
    assert 'data-base="1" data-cb' not in _pyk(tg.WORLD)


# ── categories ──
def test_categorical_choropleth_legend_table_and_patterns():
    h = _pyk(CAT)
    assert [re.sub("<[^>]+>", "", x) for x in re.findall(r"<li [^>]*>.*?</li>", h)] == ["visited", "planned", "not yet", "No category"]
    assert re.findall(r'data-key="class-(\d)"', h) == ["1", "2", "3"]
    t = re.search(r"<table.*?</table>", h, re.S).group(0)
    assert "<th scope=\"col\">Category</th>" in t and re.findall(r"<td>([^<]*)</td>", t) == ["ESP", "visited", "PRT", "visited", "FRA", "planned", "ITA", "not yet"]
    pats = re.findall(r'<pattern id="(ch\w+c\d)"', h)
    assert len(pats) == 2   # slot 0 is a plain colour, slots 1 and 2 carry a pattern: colour is never the only cue
    assert len(set(re.findall(r"url\(#(ch\w+c\d)\)", h))) == 2
    assert "no category (hatched)" in h and "<details" in h
    assert 'aria-label="Visited: 4 of ' in h and "in 3 categories" in h


def test_category_colours_are_theme_tokens_only():
    h = _py(CAT)
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b", re.sub(r"var\([^()]*#[0-9a-fA-F]{3,8}[^()]*\)", "", h.split("<table")[0]))
    assert "var(--a2ui-accent2" in h
    n = _notes(_pyk({**CAT, "category_colors": {"visited": "#ff0000", "planned": "constructor", "not yet": "muted"}}))
    assert any("2 category colours are not" in x for x in n), n
    assert "ff0000" not in _py({**CAT, "category_colors": {"visited": "#ff0000"}})


def test_six_categories_at_most_and_unlisted_categories_are_counted():
    n = _notes(_pyk(GOOD[4]))
    assert any("first 6 categories" in x for x in n)
    n = _notes(_pyk(GOOD[5]))
    assert any("Repeated ids" in x for x in n) and any("Not in the map: ZZZ" in x for x in n) and any("not in categories" in x for x in n) and any("skipped" in x for x in n)
    h = _pyk(GOOD[5])
    assert "PRT</td><td>visited" in h   # trimmed, first wins


@pytest.mark.parametrize("i", range(len(BAD)))
def test_bad_category_payloads_show_a_note_not_a_map(i):
    h = _pyk(BAD[i])
    assert "not drawn" in h and "<svg" not in h and "Traceback" not in h


def test_numeric_choropleth_is_untouched_by_the_category_mode_when_categories_is_absent():
    assert "<th scope=\"col\">Class</th>" in _py(tc.WORLD) and "Category" not in _py(tc.WORLD)


# ── geo_map region shading ──
def test_shaded_regions_are_keyed_listed_and_tinted():
    h = _pyk(TRIP1)
    assert 'data-key="PRT" style="fill:color-mix(in srgb,var(--a2ui-accent,#4f46e5) 38%,var(--a2ui-surface,#ffffff))' in h   # slot 0 solid tint
    assert re.search(r'data-key="FRA" style="fill:url\(#gc\w+c1\)', h)
    assert [re.sub("<[^>]+>", "", x) for x in re.findall(r"<li [^>]*>.*?</li>", h)][:3] == ["visited", "planned", "not yet"]
    t = h[h.index("shaded regions</caption>"):]
    assert re.findall(r"<td>([^<]*)</td>", t.split("</table>")[0]) == ["ESP", "visited", "PRT", "visited", "FRA", "planned"]
    assert "2 regions shaded in 3 categories" not in h and "3 regions shaded in 3 categories" in h


def test_shading_without_categories_takes_the_first_seen_names_and_bad_entries_are_noted():
    h = _pyk(GOOD[12])
    assert [re.sub("<[^>]+>", "", x) for x in re.findall(r"<li [^>]*>.*?</li>", h)][3:5] == ["A", "B"]
    n = _notes(h)
    assert any("Not in the map: ZZZ" in x for x in n) and any("Repeated region ids" in x for x in n)


def test_a_bad_regions_field_changes_nothing_but_a_note():
    assert _py({**tg.EU, "regions": {"id": "FRA"}}) == _py(tg.EU)
    assert "list of 1 to 6" in "".join(_notes(_pyk({**tg.EU, "regions": [{"id": "FRA", "category": "x"}], "categories": [1, 2]})))


def test_hostile_text_is_escaped_everywhere():
    for b in (GOOD[14], {**CAT, "categories": [ATTACK, "b"], "values": [{"id": "PRT", "value": ATTACK}], "title": ATTACK},
              {**TRIP1, "regions": [{"id": "PRT", "category": ATTACK}], "categories": [ATTACK], "title": ATTACK}):
        h = _py(b)
        assert "<img src" not in h and "<svg onload" not in h and "<script>alert" not in h and "&lt;img src" in h or "<img" not in h


def test_every_element_keeps_one_style_attribute():
    for b in (TRIP1, CAT):
        for el in re.findall(r"<(?:path|rect|g|circle)\b[^>]*>", _py(b)):
            assert el.count(" style=") <= 1, el[:120]


# ── parity ──
def test_python_and_gas_emit_the_same_bytes(core_js):
    blocks = GOOD + BAD
    out = _gas(core_js, blocks)
    for b, g in zip(blocks, out):
        assert _py(b) == g, json.dumps(b)[:160]


# ── schema ──
def test_schema_documents_the_new_fields():
    by = {x["type"]: x for x in yaml.safe_load((ROOT / "atoms/schema.yaml").read_text())["blocks"]}
    assert {"frame", "categories", "category_colors"} <= set(by["choropleth_map"]["fields"])
    assert {"frame", "regions", "categories", "category_colors"} <= set(by["geo_map"]["fields"])


# ── the pan and zoom, in headless Chromium ──
@browser
@pytest.mark.parametrize("width", [480, 1100])
def test_motion_transition_between_two_frames_pans_every_keyed_region(width):
    from test_motion_transition import _page, _expected_start, _close
    blk = {"type": "motion_transition", "from": TRIP1, "to": TRIP2}
    p0 = _page(blk, 0, width)
    keys = [k for k in p0["b"] if k in p0["a"]]
    assert {"PRT", "ESP", "FRA", "lisbon", "madrid", "leg1"} <= set(keys)
    assert len([k for k in keys if k.isupper()]) > 100   # the whole map travels, not only the shaded countries
    for k in keys:
        r, s = p0["b"][k], p0["a"][k]
        assert abs(r[0] + r[2] / 2 - s[0] - s[2] / 2) <= 3 and abs(r[1] + r[3] / 2 - s[1] - s[3] / 2) <= 3, (k, r[:4], s[:4])
    assert p0["b"]["paris"][4] == pytest.approx(0, abs=0.01)   # B only: hidden until late
    p1 = _page(blk, 1, width)
    alone = _page(TRIP2, None, width)["b"]
    for k, r in p1["b"].items():
        assert _close(r, alone[k], 2.5), (k, r[:4], alone[k][:4])
    moved = [k for k in keys if any(abs(x - y) > 2 for x, y in zip(p0["b"][k][:4], p1["b"][k][:4]))]
    assert len(moved) > 100, len(moved)   # a pan and a zoom: the whole map moves between the two frames
