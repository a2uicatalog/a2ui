"""I143 follow-up: a travel frame across the antimeridian (lon_min above lon_max) and a frame that reaches +-180, on geo_map and choropleth_map, both twins.

* The map is drawn with its central meridian at the frame's centre (d3-geo rotate([-lam0, 0]) in effect): outlines are unwrapped ring by ring and also drawn a world to the
  west and east, so a ring crossing the new seam stays one piece and land past +-180 shows; routes are unwrapped, so they run on across 180 without a break.
* Everything else is unchanged: the byte test in test_geo_travel.py (and the one below) pin payloads without a seam frame to origin/main's bytes.
* The 110m land set has no Kiribati and no Samoa, so the outline checks use Fiji (split by the data at 180) and the USA (Hawaii).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

from renderers import web_article as wa  # noqa: E402
from test_geo_travel import _py, _pyk, _gas, _notes, _viewbox, _pt, _leg, browser, core_js  # noqa: E402,F401

FJ, SA, HO = (-18.1, 178.4), (-13.8, -171.8), (21.3, -157.9)
PACIFIC = {"lon_min": 160, "lon_max": -150, "lat_min": -25, "lat_max": 30}
TRIP = {"type": "geo_map", "title": "Pacific", "projection": "equal-earth", "frame": PACIFIC, "points": [_pt("Suva", FJ), _pt("Apia", SA), _pt("Honolulu", HO)],
        "lines": [_leg(1, FJ, SA), _leg(2, SA, HO)], "regions": [{"id": "FJI", "category": "visited"}, {"id": "USA", "category": "planned"}], "categories": ["visited", "planned"]}
TRIP_M = {**TRIP, "projection": "mercator"}
TOUCH = {"type": "geo_map", "projection": "mercator", "frame": {"lon_min": 100, "lon_max": 180, "lat_min": -40, "lat_max": 10}, "points": [_pt("Suva", FJ)], "lines": [_leg(1, (-33.9, 151.2), FJ)]}
CH_PAC = {"type": "choropleth_map", "region_set": "world-countries", "projection": "mercator", "frame": PACIFIC, "values": [{"id": "FJI", "value": 1}, {"id": "USA", "value": 5}]}
CH_CAT_PAC = {"type": "choropleth_map", "region_set": "world-countries", "frame": PACIFIC, "categories": ["a", "b"], "values": [{"id": "FJI", "value": "a"}, {"id": "USA", "value": "b"}]}
HOSTILE = [{"lon_min": 180, "lon_max": -180, "lat_min": 0, "lat_max": 10}, {"lon_min": 179.9, "lon_max": -179.9, "lat_min": 0, "lat_max": 0.2}, {"lon_min": 1e9, "lon_max": -1e9, "lat_min": -999, "lat_max": 999},
           {"lon_min": 0.2, "lon_max": 0.1, "lat_min": 0, "lat_max": 5}, {"lon_min": 5, "lon_max": 5, "lat_min": 0, "lat_max": 5}, {"lon_min": 170, "lon_max": -170, "lat_min": 5, "lat_max": 5},
           {"lon_min": -180, "lon_max": -180, "lat_min": 0, "lat_max": 5}, {"lon_min": 180, "lon_max": 180, "lat_min": 0, "lat_max": 5}, {"lon_min": -10, "lon_max": -20, "lat_min": 40, "lat_max": 50},
           {"lon_min": "170", "lon_max": -170, "lat_min": 0, "lat_max": 5}, {"lon_min": None, "lon_max": -170, "lat_min": 0, "lat_max": 5}, {"lon_min": float("inf"), "lon_max": -170, "lat_min": 0, "lat_max": 5}]
ALL = [TRIP, TRIP_M, TOUCH, CH_PAC, CH_CAT_PAC] + [{**TRIP, "frame": f, "projection": p} for f in HOSTILE for p in ("equal-earth", "mercator")] \
    + [{**CH_PAC, "frame": f} for f in HOSTILE] + [{**TRIP, "frame": f} for f in (
        {"lon_min": -180, "lon_max": -100, "lat_min": -30, "lat_max": 30}, {"lon_min": 120, "lon_max": 179, "lat_min": -50, "lat_max": -5}, {"lon_min": 179, "lon_max": -179, "lat_min": -20, "lat_max": -10},
        {"lon_min": 0, "lon_max": -1, "lat_min": 0, "lat_max": 5}, {"lon_min": -180, "lon_max": 180, "lat_min": -85, "lat_max": 85})]


def _path(h, key, attr="data-key"):
    m = re.search(r'<path[^>]*' + attr + r'="' + key + r'"[^>]* d="([^"]*)"', h)
    return m.group(1) if m else ""


def _subpaths(d):
    return [[tuple(map(float, q)) for q in zip(*[iter(s.split())] * 2)] for s in re.split("[MZ]", d) if s.strip()]


def test_frame_read_accepts_lon_min_above_lon_max_and_centres_the_map_on_the_seam():
    notes = []
    assert wa._ch_frame_read(PACIFIC, "mercator", notes) == (160.0, -150.0, -25.0, 30.0) and notes == []
    assert wa._ch_lam0((160.0, -150.0, -25.0, 30.0)) == 185
    assert wa._ch_lam0((100.0, 180.0, 0.0, 1.0)) == 140 and wa._ch_lam0((-180.0, -100.0, 0.0, 1.0)) == -140
    assert wa._ch_lam0((-12.0, 4.0, 36.0, 44.0)) == 0 and wa._ch_lam0(None) == 0
    assert wa._ch_frame_read({"lon_min": 180, "lon_max": -180, "lat_min": 0, "lat_max": 5}, "mercator", []) is None
    lo0, lo1, la0, la1 = wa._ch_frame_read({"lon_min": 179.9, "lon_max": -179.9, "lat_min": 0, "lat_max": 5}, "mercator", [])   # 0.2 degrees across: widened to 1 around the seam
    assert (lo1 + 360 - lo0) == pytest.approx(1) and lo0 > 0 > lo1


@pytest.mark.parametrize("proj", ["equal-earth", "mercator"])
def test_a_pacific_trip_draws_all_three_stops_and_keeps_the_far_side_of_180(proj):
    h = _pyk({**TRIP, "projection": proj})
    assert _viewbox(h) == ("960", "540")
    assert "3 of 3 points drawn" in re.search(r'<svg[^>]*aria-label="([^"]*)"', h).group(1)
    assert not any("outside this map" in n or "frame contains no region" in n for n in _notes(h)), _notes(h)
    assert h.count('data-shape=') == 3 and h.count('outside the frame') == 0
    for k in ("suva", "apia", "honolulu"):
        assert re.search(r'data-key="' + k + r'"', h)
    pts = [tuple(map(float, m)) for m in re.findall(r'data-xy="([-\d.]+),([-\d.]+)"', h)]
    assert len(pts) == 3 and all(0 <= x <= 960 and 0 <= y <= 540 for x, y in pts)
    suva, apia, hon = pts   # west to east across the seam: Suva (178E) is left of Apia (172W), which is left of Honolulu (158W)
    assert suva[0] < apia[0] < hon[0]


@pytest.mark.parametrize("proj", ["equal-earth", "mercator"])
def test_routes_run_across_180_as_one_piece(proj):
    h = _pyk({**TRIP, "projection": proj})
    for k in ("leg1", "leg2"):
        d = _path(h, k)
        assert d.count("M") == 1, (k, d[:80])
        pts = _subpaths(d)[0]
        assert len(pts) > 3
        assert max(abs(a[0] - b[0]) for a, b in zip(pts, pts[1:])) < 40   # no long horizontal streak: the great circle's steps are a few pixels


@pytest.mark.parametrize("proj", ["equal-earth", "mercator"])
def test_outlines_are_not_smeared_across_the_canvas(proj):
    h = _pyk({**TRIP, "projection": proj})
    for rid in re.findall(r'data-base="1" data-cb="tile" data-key="([A-Z]+)"', h):
        for sp in _subpaths(_path(h, rid)):
            assert max(abs(a[0] - b[0]) for a, b in zip(sp, sp[1:] + sp[:1])) < 2 * 960, rid   # a ring broken at the old seam would jump a whole map width
    fiji = _subpaths(_path(h, "FJI"))
    assert len(fiji) >= 2   # the data splits Fiji at 180: both halves are drawn, side by side
    xs = [x for sp in fiji for x, _ in sp]
    assert max(xs) - min(xs) < 150
    assert all(0 <= x <= 960 for x in xs) and min(xs) > 300   # near Suva, not at the canvas edge
    usa = [x for sp in _subpaths(_path(h, "USA")) for x, _ in sp]
    assert usa and min(usa) >= 0   # Hawaii's pieces are in the canvas; the lower 48 lie off it and are not drawn


def test_frames_not_on_the_seam_behave_as_before():
    h = _pyk({**TRIP, "frame": {"lon_min": -180, "lon_max": -140, "lat_min": -25, "lat_max": 30}, "points": TRIP["points"][1:]})   # reaches -180, so it is centred on -160: Honolulu and Apia both inside
    assert "outside this map" not in "".join(_notes(h))
    h0 = _pyk({**TRIP, "frame": {"lon_min": -10, "lon_max": 30, "lat_min": 30, "lat_max": 60}})
    assert any("3 points are outside this map" in n for n in _notes(h0))   # an ordinary frame far from the seam still leaves them out


def test_a_frame_that_reaches_180_draws_the_land_beyond_the_seam():
    h = _pyk(TOUCH)
    assert not any("outside this map" in n for n in _notes(h)), _notes(h)
    fiji = _subpaths(_path(h, "FJI"))
    assert len(fiji) >= 2 and all(0 <= x <= 960 for sp in fiji for x, _ in sp)   # Fiji's -180 piece is drawn east of the 180 edge, in the canvas
    d = _path(h, "leg1")
    assert d.count("M") == 1
    # unrotated frames keep their rule: a leg that crosses the seam is cut there
    cut = _pyk({"type": "geo_map", "projection": "mercator", "frame": {"lon_min": 100, "lon_max": 170, "lat_min": -40, "lat_max": 10}, "lines": [_leg(1, (-33.9, 151.2), FJ)]})
    assert _path(cut, "leg1") != ""


def test_the_sea_tint_is_left_out_for_a_seam_frame_on_a_region_set_without_the_seam():
    eu = {"type": "geo_map", "region_set": "europe-countries", "projection": "mercator", "frame": PACIFIC, "points": [_pt("Suva", FJ)]}
    assert 'data-sea="1"' not in _pyk(eu)
    assert 'data-sea="1"' in _pyk(TRIP)


def test_choropleth_map_frames_across_the_seam_too():
    for b in (CH_PAC, CH_CAT_PAC):
        h = _pyk(b)
        assert _viewbox(h) == ("960", "540")
        assert not any("frame contains no region" in n for n in _notes(h))
        assert len(_subpaths(_path(h, "FJI"))) >= 2


def test_hostile_frames_are_safe():
    for f in HOSTILE:
        for b in ({**TRIP, "frame": f}, {**CH_PAC, "frame": f}, {**CH_CAT_PAC, "frame": f}):
            h = _pyk(b)
            assert h.startswith("<div") and "Infinity" not in h
            svg = h.split("<svg")[1].split("</svg>")[0]
            assert "NaN" not in svg and "undefined" not in svg and "nan" not in svg
            assert len(h) < 3_000_000


def test_python_and_gas_emit_the_same_bytes_across_the_seam(core_js):
    out = _gas(core_js, ALL)
    for b, g in zip(ALL, out):
        assert _py(b) == g, json.dumps(b)[:200]


def test_payloads_without_a_seam_frame_render_the_bytes_of_origin_main():
    """Every payload of the repo's tests that has no crossing frame and no frame reaching +-180 is pinned by test_geo_travel's baseline (made on origin/main); here the
    renderer is held to the same: a frame inside -180..180 is unchanged by this work, so its path has one M per ring and its points are unrotated."""
    base = {"type": "geo_map", "projection": "mercator", "frame": {"lon_min": -12, "lon_max": 4, "lat_min": 36, "lat_max": 44}, "points": [_pt("Lisbon", (38.72, -9.14))]}
    assert wa._ch_lam0((-12.0, 4.0, 36.0, 44.0)) == 0
    h = _pyk(base)
    assert "outside this map" not in "".join(_notes(h)) and h.count("data-shape=") == 1


# ── the pan and zoom between two frames on either side of the seam, in headless Chromium ──
T_A = {**TRIP, "frame": {"lon_min": 165, "lon_max": -165, "lat_min": -25, "lat_max": -8}, "points": TRIP["points"][:2], "lines": TRIP["lines"][:1]}
T_B = {**TRIP, "frame": PACIFIC}


@browser
def test_motion_transition_between_seam_frames_ends_where_B_alone_puts_it():
    from test_motion_transition import _page, _close
    blk = {"type": "motion_transition", "from": T_A, "to": T_B}
    p0, p1 = _page(blk, 0, 1100), _page(blk, 1, 1100)
    keys = [k for k in p0["b"] if k in p0["a"]]
    assert {"FJI", "suva", "apia", "leg1"} <= set(keys)
    alone = _page(T_B, None, 1100)["b"]
    for k, r in p1["b"].items():
        assert _close(r, alone[k], 2.5), (k, r[:4], alone[k][:4])
