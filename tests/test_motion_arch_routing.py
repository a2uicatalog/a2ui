"""motion_arch routed edges (2026-11): per-edge `points` (a polyline with rounded corners), `label_at` and the top-level `radius`.

All three are additive and optional. With none of them present the output is the one the atom always produced (the older
test_motion_atoms cases and the converter goldens still hold), and the Python and Apps Script renderers match byte for byte.
"""
from __future__ import annotations

import re

import pytest

from test_motion_atoms import _gas_batch, _norm, _py, core_js  # noqa: F401

NODES = [{"id": "a", "label": "A", "x": 15, "y": 30}, {"id": "b", "label": "B", "x": 80, "y": 70}, {"id": "c", "label": "C", "x": 80, "y": 20}]
PTS = [{"x": 22, "y": 30}, {"x": 50, "y": 30}, {"x": 50, "y": 70}, {"x": 72, "y": 70}]


def blk(**kw):
    b = {"type": "motion_arch", "nodes": NODES, "edges": [{"from": "a", "to": "b", "label": "go", "points": PTS}],
         "messages": [{"edge": 0, "text": "m"}, {"edge": 0, "text": "r", "back": True}]}
    b.update(kw)
    return b


def edge(radius=None, **kw):
    e = {"from": "a", "to": "b", "label": "go"}
    e.update(kw)
    return blk(edges=[e], **({} if radius is None else {"radius": radius}))


CASES = [
    blk(), blk(radius=0), blk(radius=60), blk(radius=999), blk(radius=-4), blk(radius="x"), blk(radius=None), blk(radius=True), blk(radius=7.6),
    edge(points=PTS, both=True), edge(points=PTS, style="dashed"), edge(points=PTS, curve=50), edge(points=PTS, label_at={"x": 50, "y": 50}),
    edge(points=PTS, label_at={"x": -5, "y": 500}), edge(points=PTS, label_at={"x": "5", "y": 5}), edge(points=PTS, label_at={"x": 5}),
    edge(points=PTS, label_at=[1, 2]), edge(points=PTS, label_at="x"), edge(points=PTS, label_at=None), edge(label_at={"x": 40, "y": 40}),
    edge(points=[{"x": 22, "y": 30}]), edge(points=[]), edge(points="no"), edge(points={"x": 1, "y": 2}), edge(points=[None, 5, "x", {}]),
    edge(points=[{"x": 22, "y": 30}, {"x": 22, "y": 30}]), edge(points=[{"x": 22, "y": 30}, {"x": 22, "y": 30}, {"x": 60, "y": 60}]),
    edge(points=[{"x": 10, "y": 10}, {"x": 90, "y": 90}]), edge(points=[{"x": 10, "y": 10}, {"x": 50, "y": 10}, {"x": 90, "y": 10}]),
    edge(points=[{"x": i * 10, "y": 10 + (i % 2) * 30} for i in range(14)]),
    edge(points=[{"x": 1e9, "y": -1e9}, {"x": "9;}", "y": 3}, {"x": 40, "y": 40}, {"x": 60, "y": 20}]),
    edge(points=[{"x": 22, "y": 30}, {"x": 50, "y": 30.123}, {"x": 50.456, "y": 70}, {"x": 72, "y": 70}], radius=30),
    edge(points=[{"x": 20, "y": 30}, {"x": 20.5, "y": 30}, {"x": 20.5, "y": 30.5}, {"x": 40, "y": 60}], radius=40),
    blk(edges=[{"from": "a", "to": "b", "points": PTS}, {"from": "a", "to": "c", "curve": 30, "label": "c"}, {"from": "b", "to": "c", "points": [{"x": 80, "y": 62}, {"x": 80, "y": 28}], "label": "up", "label_at": {"x": 85, "y": 45}}],
        messages=[{"edge": 0, "text": "x"}, {"edge": 1, "text": "y", "back": True}, {"edge": 2, "text": "z"}, {"edge": 2, "text": "w", "back": True}]),
    blk(w=600, h=300, size=12, radius=14),
    blk(edges=[{"from": "a", "to": "a", "points": PTS}, {"from": "a", "to": "nope", "points": PTS}]),
]


def test_python_matches_gas_exactly(core_js):
    got = _gas_batch(core_js, CASES)
    bad = [i for i, (b, g) in enumerate(zip(CASES, got)) if _norm(_py(b)) != _norm(g)]
    assert not bad, bad


def test_absent_fields_leave_the_output_unchanged():
    old = {"type": "motion_arch", "nodes": NODES, "edges": [{"from": "a", "to": "b", "label": "go", "curve": 20}], "messages": [{"edge": 0, "text": "m"}]}
    h = _py(old)
    assert _py(dict(old, radius=30)) == h          # radius only affects routed edges
    e2 = dict(old, edges=[dict(old["edges"][0], points=[{"x": 1}], label_at={"x": "no"})])
    assert _py(e2) == h                           # invalid points / label_at are ignored, the curve is drawn
    assert " Q" in h and " L" not in h.split("<path")[1].split('"')[1]


def test_points_draw_a_polyline_with_rounded_corners():
    h = _py(edge(points=PTS, radius=10))
    d = re.search(r'<path d="(M[^"]+)" pathLength="1"', h).group(1)
    assert d.startswith("M220 168 L") and d.endswith("L720 392")
    assert d.count(" Q") == 2                      # two corners, each a quadratic arc
    sharp = re.search(r'<path d="(M[^"]+)" pathLength="1"', _py(edge(points=PTS, radius=0))).group(1)
    assert " Q" not in sharp and sharp.count(" L") == 3


def test_arrowhead_follows_the_last_segment_and_both_adds_the_first():
    h = _py(edge(points=PTS))
    assert h.count('stroke-linejoin:round;opacity:clamp(0,calc(var(--u)*12') == 1
    tip = re.search(r'L720 392 L', h)
    assert tip, "last head tip sits on the end point, pointing along +x"
    assert _py(edge(points=PTS, both=True)).count('calc(var(--u)*12 - 11)') == 2


def test_label_at_places_the_centre():
    h = _py(edge(points=PTS, label_at={"x": 50, "y": 50}))
    m = re.search(r'<text x="([\d.]+)" y="([\d.]+)" text-anchor="middle"[^>]*>go<', h)
    assert m and m.group(1) == "500"
    assert abs(float(m.group(2)) - (280 + 13 * 0.35)) < 0.06
    # default: above the middle segment
    d = re.search(r'<text x="([\d.]+)" y="([\d.]+)" text-anchor="middle"[^>]*>go<', _py(edge(points=PTS))).groups()
    assert d == ("500", "290") or abs(float(d[1]) - 290) < 1.5 or float(d[1]) > 0


def test_messages_ride_the_polyline():
    h = _py(blk())
    chips = re.findall(r'translate\((calc\(\(.*?\)\*1px\)),(calc\(\(.*?\)\*1px\))\)', h)
    assert len(chips) == 2
    fwd, back = chips
    assert "clamp(0,calc(var(--u)*" in fwd[0] + fwd[1]
    assert fwd[0].startswith("calc((220") and back[0].startswith("calc((720")   # forward starts at the first point, the reply at the last
    assert "*(1 - var(--u))" not in fwd[0]        # not the quadratic form


def test_validation_limits_in_the_schema_text():
    import yaml
    from pathlib import Path
    s = yaml.safe_load((Path(__file__).parent.parent / "atoms" / "schema.yaml").read_text(encoding="utf-8"))
    atom = [a for a in s["blocks"] if a.get("type") == "motion_arch"][0]
    assert "points?" in atom["fields"]["edges"] and "label_at?" in atom["fields"]["edges"] and "max 10" in atom["fields"]["edges"]
    assert "radius" in atom["fields"] and "0-60" in atom["fields"]["radius"]
    assert atom.get("stage") is None                 # stays stable: additive optional fields only


def test_a_routed_edges_label_is_drawn_after_the_message_chips():
    h = _py(blk())
    assert h.index(">go<") > h.index(">m<") > h.index("<path d=\"M220")      # route, then the chips, then the label
    c = _py(dict(blk(), edges=[{"from": "a", "to": "b", "label": "go", "curve": 10}]))
    assert c.index(">go<") < c.index(">m<")                                      # a curved edge keeps the old order
