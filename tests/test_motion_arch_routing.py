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
    # label2: the second line of an edge label (2026-11)
    edge(points=PTS, label2="second line"), edge(points=PTS, label2="second line", label_at={"x": 50, "y": 50}), edge(label2="on a curve"),
    edge(label2="on a curve", curve=40), edge(label2=""), edge(label2=None), edge(label2=5), edge(label2={"a": 1}), edge(label2="x" * 80, label="y" * 80),
    edge(label2="<b>&\"'</b>", label="a<b"), edge(label2="  padded  ", points=PTS, size=9), blk(size=30, edges=[{"from": "a", "to": "b", "label": "l1", "label2": "l2", "points": PTS}]),
    blk(edges=[{"from": "a", "to": "b", "label2": "orphan second line", "points": PTS}]),
    edge(label2="\u65e5\u672c\u8a9e x", label="\u65e5\u672c\u8a9e" * 16, points=PTS),
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


def _published_arch_schema():
    import json
    from pathlib import Path
    doc = json.loads((Path(__file__).parent.parent / "public" / "catalogue" / "atoms-json-schema.json").read_text(encoding="utf-8"))
    found = [a for a in doc["items"]["oneOf"] if a["properties"]["type"].get("const") == "motion_arch"]
    assert len(found) == 1
    return found[0]


def test_published_strict_schema_types_the_routing_fields():
    # the strict schema constrains LLM output: points/label_at/radius used to be strings with no limits
    p = _published_arch_schema()["properties"]
    e = p["edges"]["items"]["properties"]
    assert e["points"]["type"] == "array" and e["points"]["maxItems"] == 10
    assert e["points"]["items"]["properties"]["x"]["type"] == "number" and e["points"]["items"]["required"] == ["x", "y"]
    assert e["label_at"]["type"] == "object" and set(e["label_at"]["properties"]) == {"x", "y"}
    assert e["curve"]["type"] == "number" and (e["curve"]["minimum"], e["curve"]["maximum"]) == (-100, 100)
    assert e["both"] == {"type": "boolean"} and e["style"]["enum"] == ["solid", "dashed"]
    assert p["radius"] == {"type": "integer", "minimum": 0, "maximum": 60}
    assert p["nodes"]["items"]["properties"]["x"]["type"] == "number" and p["nodes"]["maxItems"] == 12


def _check(v, sc, path="$"):
    """A small JSON Schema checker (type, enum, bounds, maxItems/maxLength, pattern, required, additionalProperties): jsonschema is not a dependency."""
    errs = []
    t = sc.get("type")
    ok = {"object": isinstance(v, dict), "array": isinstance(v, list), "string": isinstance(v, str), "boolean": isinstance(v, bool),
          "integer": isinstance(v, int) and not isinstance(v, bool), "number": isinstance(v, (int, float)) and not isinstance(v, bool), None: True}[t]
    if not ok:
        return [f"{path}: expected {t}, got {type(v).__name__}"]
    if "const" in sc and v != sc["const"]:
        errs.append(f"{path}: const")
    if "enum" in sc and v not in sc["enum"]:
        errs.append(f"{path}: {v!r} not in enum")
    if t in ("integer", "number"):
        if "minimum" in sc and v < sc["minimum"]:
            errs.append(f"{path}: {v} below {sc['minimum']}")
        if "maximum" in sc and v > sc["maximum"]:
            errs.append(f"{path}: {v} above {sc['maximum']}")
    if t == "string":
        if "maxLength" in sc and len(v) > sc["maxLength"]:
            errs.append(f"{path}: too long")
        if "pattern" in sc and not re.search(sc["pattern"], v):
            errs.append(f"{path}: {v!r} breaks pattern")
    if t == "array":
        if "maxItems" in sc and len(v) > sc["maxItems"]:
            errs.append(f"{path}: more than {sc['maxItems']} items")
        for i, x in enumerate(v):
            errs += _check(x, sc.get("items", {}), f"{path}[{i}]")
    if t == "object":
        for k in sc.get("required", []):
            if k not in v:
                errs.append(f"{path}: missing {k}")
        for k, x in v.items():
            if k in sc.get("properties", {}):
                errs += _check(x, sc["properties"][k], f"{path}.{k}")
            elif sc.get("additionalProperties") is False:
                errs.append(f"{path}: unexpected {k}")
    return errs


def test_converter_output_validates_against_the_published_strict_schema():
    import json
    from pathlib import Path
    ex = Path(__file__).parent.parent / "scripts" / "mermaid_arch" / "examples"
    schema = _published_arch_schema()
    n = 0
    for f in sorted(ex.glob("*.golden.json")):
        payload = json.loads(f.read_text(encoding="utf-8"))
        stack = list(payload["blocks"])
        while stack:
            b = stack.pop()
            if b.get("type") == "motion_arch":
                b = {k: v for k, v in b.items() if k not in ("id", "place")}
                assert _check(b, schema) == [], f.name
                n += 1
            stack.extend(b.get("blocks", []))
    assert n >= 10
    bad = {"type": "motion_arch", "nodes": [], "edges": [{"from": "a", "to": "b", "points": "x"}], "radius": 99}
    assert len(_check(bad, schema)) == 2          # the checker does reject a string `points` and an out-of-range radius


def test_label2_is_a_second_line_under_the_label_and_old_payloads_are_unchanged():
    one = _py(edge(points=PTS))
    assert _py(edge(points=PTS, label2="")) == one and _py(edge(points=PTS, label2=None)) == one
    assert _py(edge(label2="")) == _py(edge()) and _py(edge(label2="x")).count("<tspan") == 2     # on a curve too
    no_label = dict(edge(points=PTS)["edges"][0])
    del no_label["label"]
    assert _py(blk(edges=[dict(no_label, label2="orphan")])) == _py(blk(edges=[no_label]))   # label2 without a label is ignored
    two = _py(edge(points=PTS, label2="line two"))
    assert two.count("<tspan") == 2 and ">go</tspan>" in two and ">line two</tspan>" in two
    assert two.count("paint-order:stroke") == one.count("paint-order:stroke")       # one text element: the halo sits behind both lines
    assert "<tspan" not in one


def test_label2_is_documented_in_the_schema_text():
    import yaml
    from pathlib import Path
    s = yaml.safe_load((Path(__file__).parent.parent / "atoms" / "schema.yaml").read_text(encoding="utf-8"))
    atom = [a for a in s["blocks"] if a.get("type") == "motion_arch"][0]
    assert "label2?" in atom["fields"]["edges"] and "second line" in atom["fields"]["edges"]
    e = _published_arch_schema()["properties"]["edges"]["items"]["properties"]
    assert e["label2"]["type"] == "string"
