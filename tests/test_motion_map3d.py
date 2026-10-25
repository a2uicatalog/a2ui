"""motion_map3d (backlog I72, from the owner's uploaded reference video): a tilted 3D city map built from CSS alone.

Blocks are three-faced boxes on a rotated plane (a seeded city or explicit blocks), stations are billboards, the route is SVG paths drawn with
stroke-dashoffset, the clock is a CSS integer counter. Every moving value is a pure function of var(--p, 1); p = 1 (no timeline, no script, reduced
motion, print) is the settled picture: full route, final station states, final clock, plus a visually hidden text alternative.

Layers as in test_motion_lightning.py: Python == GAS byte for byte, hostile input never becomes markup, build-contract keys, and a real browser
shows the map at fixed p.
"""
from __future__ import annotations

import html as _h
import json
import re
import subprocess
import tempfile
from pathlib import Path

import pytest

from test_motion_atoms import CHROMIUM, _gas_batch, _norm, _py, _py_keyed, browser, core_js  # noqa: F401

HOSTILE = 'x";}</style><script>alert(1)</script><b onload="1"'
BASE = {"type": "motion_map3d"}
ST = [{"id": "depot", "x": 12, "y": 78, "label": "Depot", "state": "done"}, {"id": "north", "x": 38, "y": 30, "label": "North Hub", "state": "done"},
      {"id": "market", "x": 70, "y": 42, "label": "Market", "state": "active"}, {"id": "port", "x": 86, "y": 80, "label": "Port", "state": "idle"},
      {"id": "spare", "x": 20, "y": 15, "label": "Spare", "state": "idle"}]
FULL = dict(BASE, seed=11, stations=ST, route=["depot", "north", "market", "port"], clock={"from": "08:00", "to": "08:47"}, tilt=58, camera={"from": 0.5, "to": 1.2})

CASES = [
    BASE, FULL, dict(FULL, seed=0), dict(FULL, seed=9999), dict(FULL, seed=-4), dict(FULL, seed="x"), dict(FULL, seed=None), dict(FULL, seed=3.7), dict(FULL, seed="12"),
    dict(FULL, tilt=0), dict(FULL, tilt=75), dict(FULL, tilt=999), dict(FULL, tilt=-30), dict(FULL, tilt="x"), dict(FULL, tilt=None), dict(FULL, tilt=True), dict(FULL, tilt=42.55),
    dict(FULL, camera=None), dict(FULL, camera={"from": 0.1, "to": 9}), dict(FULL, camera={"from": "x"}), dict(FULL, camera=[1, 2]), dict(FULL, camera={"from": 2, "to": 0.4}),
    dict(FULL, clock={"from": "23:30", "to": "00:15"}), dict(FULL, clock={"from": "8:05", "to": "9:00"}), dict(FULL, clock={"from": "25:00", "to": "01:00"}),
    dict(FULL, clock={"from": "08:00"}), dict(FULL, clock="08:00"), dict(FULL, clock={"from": HOSTILE, "to": "x"}), dict(FULL, clock={"from": "08:00", "to": "08:00"}),
    dict(FULL, clock={"from": " 07:59 ", "to": "08:60"}), dict(FULL, clock={"from": "08:00\n", "to": "09:00"}), dict(FULL, clock={}),
    dict(FULL, color="#ff2200"), dict(FULL, color="red"), dict(FULL, color=HOSTILE), dict(FULL, color="#FFF"), dict(FULL, color=5),
    dict(FULL, route=[]), dict(FULL, route=["depot"]), dict(FULL, route=["depot", "depot", "port"]), dict(FULL, route=["ghost", "depot", None, 3, "north", "nope"]),
    dict(FULL, route=["depot", "north", "depot", "north", "depot"]), dict(FULL, route="depot"), dict(FULL, route=None), dict(FULL, route=[HOSTILE, "depot", "port"]),
    dict(FULL, route=["spare", "port"]), dict(FULL, route=["depot", "constructor", "toString", "__proto__"]),
    dict(FULL, stations=[]), dict(FULL, stations=None), dict(FULL, stations="x"), dict(FULL, stations=[1, None, "x", {}]), dict(FULL, route=["s1", "s2"], stations=[{"x": 10, "y": 10}, {"x": 90, "y": 90}]),
    dict(FULL, stations=ST + [dict(ST[0], label="again")]), dict(FULL, stations=[dict(ST[0], id=HOSTILE, label=HOSTILE)]),
    dict(FULL, stations=[{"id": "constructor", "x": 30, "y": 30}, {"id": "toString", "x": 60, "y": 60, "state": "done"}], route=["constructor", "toString"]),
    dict(FULL, stations=[dict(ST[0], x=-50, y=500), dict(ST[1], x="x", y=None), dict(ST[2], state="gone"), dict(ST[3], state=HOSTILE, label="L" * 90)]),
    dict(FULL, stations=[{"id": "s%d" % i, "x": i * 4, "y": i * 3, "state": ["idle", "active", "done"][i % 3]} for i in range(30)], route=["s%d" % i for i in range(30)]),
    dict(FULL, route=["depot", "north"] * 20),
    dict(FULL, route=["depot", "port"], stations=[dict(ST[0], x=50, y=50), dict(ST[3], x=50, y=50)]),
    dict(FULL, blocks=[{"x": 10, "y": 10, "w": 20, "h": 15, "height": 12}, {"x": 60, "y": 50, "w": 25, "h": 25}, {"x": -5, "y": 200, "w": 0, "h": 999, "height": 9999}, "x", None, 5, {}]),
    dict(FULL, blocks=[]), dict(FULL, blocks="x"), dict(FULL, blocks=[{"x": i % 20 * 5, "y": i // 20 * 9, "w": 4, "h": 8, "height": i % 17} for i in range(260)]),
    dict(FULL, blocks=[{"x": "1", "y": "2", "w": "3", "h": "4", "height": "5"}]),
    dict(BASE, stations=ST), dict(BASE, route=["a", "b"]), dict(BASE, clock={"from": "10:00", "to": "10:10"}),
    dict(FULL, version=2), dict(FULL, version=1), dict(FULL, version="x"), dict(FULL, id="m1", enter="rise"),
] + [dict(FULL, seed=s, tilt=s * 2, route=ST and [x["id"] for x in ST][: 2 + s % 4]) for s in range(1, 25)]


def _count(h, attr):
    return len(re.findall(attr, h))


def test_python_matches_gas_exactly(core_js):
    got = _gas_batch(core_js, CASES)
    bad = [str(b)[:110] for b, g in zip(CASES, got) if _norm(_py(b)) != _norm(g)]
    assert not bad, bad


def test_structure_is_decorative_and_scriptless():
    h = _py(FULL)
    svg = re.search(r'<svg\b[^>]*>', h).group(0)
    assert 'aria-hidden="true"' in svg and 'focusable="false"' in svg and "tabindex" not in h and "role=" not in h
    assert re.search(r'class="m3-stage" aria-hidden="true"', h)
    for bad in ("<script", "<button", "<img", "<foreignObject", "@keyframes", "animation", "Math.random", "http://", "https://", "url(", "<canvas", "fetch("):
        assert bad not in h, bad
    assert _count(h, r'data-m3="station"') == 5 and _count(h, r'data-m3="seg"') == 3
    assert "Math.random" not in Path(__file__).parent.parent.joinpath("renderers/web_article.py").read_text().split("def _render_motion_map3d")[1].split("_RENDERERS['motion_map3d']")[0]


def test_every_moving_value_reads_p_and_the_settled_frame_is_the_default():
    h = _py(FULL)
    assert "var(--p,1)" in h and "var(--p)" not in h.replace("var(--p,", "")
    assert not re.search(r'(?<![\w-])--p:', re.sub(r'<style>.*?</style>', '', h, flags=re.S)), "no inline --p: the atom reads the dial, it never sets it"
    assert "@media (prefers-reduced-motion:reduce),print{.m3-root{--p:1!important}}" in h


def test_settled_frame_contents_route_fully_drawn_states_final_clock_and_text_alternative():
    h = _py(FULL)
    offs = re.findall(r'stroke-dashoffset:calc\(1 - clamp\(0,calc\(\(var\(--p,1\) - ([\d.]+)\)/([\d.]+)\),1\)\)', h)
    assert len(offs) == 3
    prev_end = 0.3
    for s, w in offs:   # segments are in order, inside p 0.3..0.92, each drawn when p reaches s + w, so at p = 1 every one is complete
        s, w = float(s), float(w)
        assert s >= prev_end - 1e-9 and s + w <= 0.92 + 1e-3
        prev_end = s + w
    assert '<span class="m3-cs">08:47</span>' in h and 'data-m3="clock"' in h and "--m0:480;--m1:527" in h
    alt = re.search(r'data-m3="alt"[^>]*>([^<]*)<', h).group(1)
    assert "Route: Depot, then North Hub, then Market, then Port." in alt
    assert "Depot (done)" in alt and "Market (active)" in alt and "Spare (idle)" in alt and "08:00 to 08:47" in alt
    assert 'data-state="done"' in h and 'data-state="active"' in h
    # the route travels through every station in order, each station's active window opens when its segment arrives
    sts = re.findall(r'data-key="(\w+)" data-m3="station" data-state="(\w+)"', _py_keyed(FULL))
    assert sts == [("depot", "done"), ("north", "done"), ("market", "active"), ("port", "idle"), ("spare", "idle")]


def test_settled_layers_at_p_one_show_only_the_final_state():
    """Evaluate the opacity formulas at p = 1: idle, active and done layers resolve to exactly the station's own state."""
    h = _py_keyed(FULL)
    for sid, state in (("depot", "done"), ("north", "done"), ("market", "active"), ("port", "idle")):
        block = re.search(r'data-key="%s" data-m3="station".*?<span class="m3-lab"' % sid, h, re.S).group(0)
        layers = re.findall(r'class="m3-pin m3-(\w+)" style="opacity:([^;]*);', block)
        assert [n for n, _ in layers] == ["idle", "active", "done"][: len(layers)] and len(layers) >= 2
        for name, op in layers:
            expr = op.replace("var(--p,1)", "1").replace("calc", "").replace("clamp(0,", "_c(")
            val = eval(expr, {"_c": lambda x, hi: max(0, min(hi, x))})   # noqa: S307 (our own generated arithmetic)
            assert abs(val - (1 if name == state else 0)) < 1e-9, (sid, name, op)
    spare = re.search(r'data-key="spare" data-m3="station".*?<span class="m3-lab"', h, re.S).group(0)
    assert re.findall(r'm3-pin m3-(\w+)" style="opacity:1;', spare) == ["idle"]


def test_keys_nodes_labels_and_segments_are_unique_and_named():
    h = _py_keyed(FULL)
    nodes = re.findall(r'data-cb="node" data-key="([^"]*)"', h)
    labels = re.findall(r'data-cb="label" data-key="([^"]*)"', h)
    links = re.findall(r'data-cb="link" data-key="([^"]*)"', h)
    assert nodes == ["depot", "north", "market", "port", "spare"] and labels == nodes
    assert links == ["depot-north", "north-market", "market-port"]
    again = re.findall(r'data-cb="link" data-key="([^"]*)"', _py_keyed(dict(FULL, route=["depot", "north", "depot", "north"])))
    assert again == ["depot-north", "north-depot", "depot-north-2"]
    shapes = nodes + links
    assert len(shapes) == len(set(shapes))
    assert 'data-key=""' not in _py_keyed(dict(FULL, stations=[{"x": 1, "y": 2}]))


def test_unknown_route_ids_are_skipped_with_a_note_and_never_reach_the_markup():
    h = _py(dict(FULL, route=["ghost", "depot", None, 3, "north", HOSTILE]))
    assert _count(h, r'data-m3="seg"') == 1 and "4 route entries were not a known station and were skipped." in h
    assert "ghost" not in h and "<script" not in h and "alert(1)" not in h
    one = _py(dict(FULL, route=["ghost", "depot", "port"]))
    assert "1 route entry was not a known station and was skipped." in one and _count(one, r'data-m3="seg"') == 1
    assert "known station" not in _py(FULL)


def test_more_than_200_blocks_are_capped_with_a_note():
    many = [{"x": i % 20 * 5, "y": i // 20 * 9, "w": 4, "h": 8, "height": 5} for i in range(260)]
    h = _py(dict(FULL, blocks=many))
    assert _count(h, r'class="m3-b"') == 200 and "Showing the first 200 of 260 blocks." in h
    assert _count(_py(dict(FULL, blocks=many[:200])), r'class="m3-b"') == 200 and "Showing the first" not in _py(dict(FULL, blocks=many[:200]))
    assert _count(_py(dict(FULL, blocks=many[:7])), r'class="m3-b"') == 7


def test_the_seeded_city_is_deterministic_varies_with_the_seed_and_leaves_the_route_clear():
    a, b2 = _py(dict(FULL, seed=5)), _py(dict(FULL, seed=6))
    assert a == _py(dict(FULL, seed=5)) and a != b2
    assert 20 <= _count(a, r'class="m3-b"') <= 49
    blocks = [tuple(map(float, m)) for m in re.findall(r'class="m3-b" style="left:([\d.]+)%;top:([\d.]+)%;width:([\d.]+)%;height:([\d.]+)%', a)]
    pts = {s["id"]: (s["x"], s["y"]) for s in ST}
    for (x, y, w, h) in blocks:
        for sid in ("depot", "north", "market", "port"):   # no block sits on a station
            px, py = pts[sid]
            assert not (x - 1 <= px <= x + w + 1 and y - 1 <= py <= y + h + 1), (sid, x, y, w, h)
    assert _count(_py(BASE), r'class="m3-b"') > 10, "a bare payload still draws the default seeded city"


def test_bad_tilt_and_camera_are_clamped():
    def tilt(v):
        return float(re.search(r'--tilt:([\d.]+);', _py(dict(FULL, tilt=v))).group(1))
    assert tilt(999) == 75 and tilt(-30) == 0 and tilt(0) == 0 and tilt(75) == 75 and tilt("x") == 55 and tilt(None) == 55 and tilt(True) == 55 and tilt("40") == 55
    z = _py(dict(FULL, camera={"from": 0.1, "to": 9}))
    assert "--z0:0.3;--z1:3;" in z
    assert "--z0:0.55;--z1:1;" in _py(dict(FULL, camera=None)) and "--z0:0.55;--z1:1;" in _py(BASE)


def test_empty_payload_gives_a_note_and_an_alternative():
    h = _py(BASE)
    assert "No stations to show." in h and 'data-m3="alt"' in h and "City map." in h
    assert 'data-m3="seg"' not in h and 'data-m3="clock"' not in h and "<script" not in h
    assert "No stations to show." not in _py(FULL)
    two = _py(dict(FULL, stations=ST + [ST[0]]))
    assert "1 station was left out (duplicate id or more than 24)." in two


def test_clock_handles_midnight_and_bad_values():
    assert "--m0:1410;--m1:1455;" in _py(dict(FULL, clock={"from": "23:30", "to": "00:15"})) and '<span class="m3-cs">00:15</span>' in _py(dict(FULL, clock={"from": "23:30", "to": "00:15"}))
    for bad in ({"from": "08:00"}, {"from": "25:00", "to": "01:00"}, {"from": "08:00", "to": "08:60"}, {"from": HOSTILE, "to": "x"}, "08:00", None, {}):
        assert 'data-m3="clock"' not in _py(dict(FULL, clock=bad)), bad
    assert 'data-m3="clock"' in _py(dict(FULL, clock={"from": "8:05", "to": "9:00"}))


def test_hostile_values_never_reach_markup():
    h = _py(dict(FULL, color=HOSTILE, stations=[dict(ST[0], id=HOSTILE, label=HOSTILE, state=HOSTILE), dict(ST[1], id="ok", label='<b onclick="1">')], route=[HOSTILE, "ok"],
                 clock={"from": HOSTILE, "to": HOSTILE}))
    assert "<script" not in h and "onload=" not in h and "<b onclick" not in h and "alert(1)" not in h.replace("&quot;", "")
    assert HOSTILE not in h


def test_version_note():
    assert "Written for motion_map3d version 3; drawn as version 2." in _py(dict(FULL, version=3))
    assert "Written for" not in _py(dict(FULL, version=2))
    assert "Written for" not in _py(dict(FULL, version=1))


def test_registered_everywhere():
    root = Path(__file__).resolve().parent.parent
    import yaml
    schema = yaml.safe_load((root / "atoms" / "schema.yaml").read_text())
    ent = [a for a in schema["blocks"] if isinstance(a, dict) and a.get("type") == "motion_map3d"]
    assert len(ent) == 1 and ent[0]["stage"] == "preview"
    for k in ("description", "compact_description", "routing_text", "intent_phrases", "fields", "notes", "surfaces", "source"):
        assert ent[0].get(k), k
    for f in ("seed", "blocks", "stations", "route", "clock", "tilt", "camera", "color", "version"):
        assert f in ent[0]["fields"], f
    packs = yaml.safe_load((root / "atoms" / "atom-packs.yaml").read_text())
    assert "motion_map3d" in packs["a2ui-effects-v1"]
    assert '"motion_map3d":"a2ui-effects-v1"' in (root / "apps-script-surface" / "gas-wired-renderer" / "PackMap.gs").read_text()
    assert '"motion_map3d"' in (root / "scripts" / "generate_atom_pages.py").read_text()
    reg = json.loads((root / "tests" / "fixtures" / "contract_registry.json").read_text())["atoms"]
    assert reg["motion_map3d"]["status"] == "sweep"
    sweep = json.loads((root / "tests" / "fixtures" / "contract_sweep.json").read_text())
    assert sweep["motion_map3d"]["status"] == "keyed" and sweep["motion_map3d"]["kind"] == "node"


# ─── a real browser: fixed p ─────────────────────────────────────────────────
def _page(block_html: str, p, width: int, js: str):
    page = ("<!doctype html><meta charset=utf-8><body style='margin:0;font:16px system-ui;background:#fff'><div style='width:" + str(width) + "px;" + ("--p:" + str(p) if p is not None else "") + "'>" + block_html
            + "</div><script>document.documentElement.setAttribute('data-probe', JSON.stringify((function(){" + js + "})()));</script>")
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "p.html"
        f.write_text(page)
        out = subprocess.run([CHROMIUM, "--headless=new", "--password-store=basic", "--no-sandbox", "--disable-gpu", f"--window-size={width},900", "--virtual-time-budget=1000",
                              "--dump-dom", f"file://{f}"], capture_output=True, text=True, timeout=90).stdout
    m = re.search(r"data-probe='([^']*)'|data-probe=\"([^\"]*)\"", out)
    assert m, out[:300]
    return json.loads(_h.unescape(m.group(1) or m.group(2)))


_STATE = ("function f(s){var m=/([\\d.]+)px/.exec(s);return m?+(+m[1]).toFixed(3):0;}"
          "var off=Array.prototype.slice.call(document.querySelectorAll('[data-m3=seg]')).map(function(e){return f(getComputedStyle(e).strokeDashoffset);});"
          "var pins=Array.prototype.slice.call(document.querySelectorAll('.m3-pin')).map(function(e){return e.className.replace('m3-pin m3-','')+':'+(+(+getComputedStyle(e).opacity).toFixed(2));});"
          "var clk=document.querySelector('.m3-cn');var cs=getComputedStyle(clk);var cm=[+cs.getPropertyValue('--m3m'),+cs.getPropertyValue('--m3h'),+cs.getPropertyValue('--m3n')];"
          "var root=document.querySelector('.m3-root');var r=root.getBoundingClientRect();var pl=getComputedStyle(document.querySelector('.m3-plane')).transform;"
          "return {off:off,pins:pins,clock:cm,w:Math.round(r.width),h:Math.round(r.height),plane:pl,sw:document.documentElement.scrollWidth};")


@browser
def test_the_route_draws_on_with_p_and_is_settled_at_one_and_by_default():
    h = _py(FULL)
    s0 = _page(h, 0, 650, _STATE)
    s1 = _page(h, 1, 650, _STATE)
    sd = _page(h, None, 650, _STATE)
    assert all(abs(o) >= 0.99 for o in s0["off"]) and all(abs(o) < 0.001 for o in s1["off"]) and sd["off"] == s1["off"]
    sm = _page(h, 0.5, 650, _STATE)
    assert abs(sm["off"][0]) < 0.001 and abs(sm["off"][1] - 1) < 0.001 or 0.001 < sm["off"][0] < 0.999, sm
    assert s1["clock"] == [527, 8, 47] and sd["clock"] == [527, 8, 47], (s1["clock"], sd["clock"])
    assert s0["clock"] == [480, 8, 0]
    mid = _page(h, 0.61, 650, _STATE)["clock"]
    assert 480 < mid[0] < 527 and mid[1] == 8 and mid[2] == mid[0] - 480, mid
    assert "idle:1" in " ".join(s0["pins"]) and not any(x.startswith("active:1") for x in s0["pins"])
    assert "done:1" in " ".join(s1["pins"]) and "active:1" in " ".join(s1["pins"])


@browser
def test_the_camera_tilts_in_and_nothing_is_wider_than_the_container_at_650_and_320():
    h = _py(FULL)
    for w in (650, 320):
        s = _page(h, 1, w, _STATE)
        # headless Chromium never goes below a 500 px window, so the page-width bound is 500 there
        assert s["w"] == w and s["sw"] <= max(w, 500) and abs(s["h"] - round(w * 9 / 16)) <= 1
    flat, tilted = _page(h, 0, 650, _STATE)["plane"], _page(h, 1, 650, _STATE)["plane"]
    assert flat != tilted and tilted.startswith("matrix3d(")


@browser
def test_reduced_motion_is_the_settled_picture():
    h = _py(FULL)
    page = ("<!doctype html><meta charset=utf-8><body style='margin:0'><div style='width:650px;--p:0.1'>" + h + "</div><script>document.documentElement.setAttribute('data-probe', JSON.stringify((function(){"
            "var e=document.querySelector('[data-m3=seg]');var m=/([\\d.]+)px/.exec(getComputedStyle(e).strokeDashoffset);return m?+m[1]:0;})()));</script>")
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "p.html"
        f.write_text(page)
        out = subprocess.run([CHROMIUM, "--headless=new", "--password-store=basic", "--no-sandbox", "--disable-gpu", "--window-size=650,900", "--virtual-time-budget=1000", "--force-prefers-reduced-motion",
                              "--dump-dom", f"file://{f}"], capture_output=True, text=True, timeout=90).stdout
    m = re.search(r"data-probe='([^']*)'|data-probe=\"([^\"]*)\"", out)
    assert m and abs(float(_h.unescape(m.group(1) or m.group(2)))) < 0.001


# ─── version 2 (I145) ───
# --- motion_map3d v2 tests ---

V2_ST = [
    {"id": "depot", "x": 12, "y": 78, "label": "Depot", "state": "warn"},
    {"id": "north", "x": 38, "y": 30, "label": "North Hub", "state": "error"},
    {"id": "market", "x": 70, "y": 42, "label": "Market", "state": "active"},
    {"id": "port", "x": 86, "y": 80, "label": "Port", "state": "idle"},
    {"id": "spare", "x": 20, "y": 15, "label": "Spare", "state": "done"}
]

V2_CASES = [
    dict(FULL, stations=V2_ST),
    dict(FULL, clock={"unit": "s", "from": 0, "to": 45}),
    dict(FULL, clock={"unit": "s", "from": 10.4, "to": 60.9}),
    dict(FULL, clock={"unit": "ms", "from": 500, "to": 12000}),
    dict(FULL, clock={"unit": "s", "from": -1, "to": 50}),
    dict(FULL, clock={"unit": "s", "from": 100, "to": 50}),
    dict(FULL, clock={"unit": "s", "from": 90000, "to": 90001}),
    dict(FULL, clock={"unit": "ms", "from": 0, "to": 3700000}),
    dict(FULL, clock={"unit": "s", "from": True, "to": 50}),
    dict(FULL, clock={"unit": "s", "from": 10, "to": "50"}),
    dict(FULL, clock={"unit": "unknown", "from": "08:00", "to": "08:30"}),
    dict(FULL, legs=[{"route": ["depot", "north", "market"], "color": "#10b981"}, {"route": ["market", "port"], "color": "#f43f5e"}]),
    dict(FULL, legs=[{"route": ["depot", "north"], "back": True}]),
    dict(FULL, legs=[{"route": ["depot", "north"]}, {"route": ["depot"]}, {"route": ["north", "port"]}]),
    dict(FULL, legs=[{"route": ["depot", "north"]}, {"route": ["north", "market"]}, {"route": ["market", "port"]}, {"route": ["port", "spare"]}, {"route": ["spare", "depot"]}]),
    dict(FULL, legs=[]),
    dict(FULL, legs="invalid"),
    dict(FULL, legs=[{"route": ["depot", "depot", "north"], "color": HOSTILE}]),
    dict(FULL, legs=[{"route": ["ghost", "depot", None, "north"]}]),
    dict(FULL, legs=[{"route": ["depot", "north"]}], messages=[{"text": "Ping", "leg": 0, "at": 0.4}]),
    dict(FULL, legs=[{"route": ["depot", "north"]}], messages=[{"text": "Ping", "back": True}]),
    dict(FULL, legs=[{"route": ["depot", "north"]}], messages=[{"text": "Late", "at": 0.99}]),
    dict(FULL, legs=[{"route": ["depot", "north"]}], messages=[{"text": ""}]),
    dict(FULL, legs=[{"route": ["depot", "north"]}], messages=[{"text": HOSTILE, "leg": 0}]),
    dict(FULL, legs=[{"route": ["depot", "north"]}], messages=[{"text": "Long text " * 5}]),
    dict(FULL, legs=[{"route": ["depot", "north"]}], messages=[{"text": "Invalid leg", "leg": 5}]),
    dict(FULL, legs=[{"route": ["depot", "north"]}], messages=[{"text": "Invalid at", "at": "0.5"}]),
    dict(FULL, legs=[{"route": ["depot", "north"]}], messages=[{"text": "Bool at", "at": True}]),
    dict(FULL, legs=[{"route": ["depot", "north"]}], messages=[{"text": "M%d" % i} for i in range(15)]),
    dict(FULL, version=2),
    dict(FULL, version=3),
    dict(FULL, version=5),
    dict(FULL, version=2.0),
    dict(FULL, version=2.5),
    dict(FULL, version=1),
    dict(FULL, stations=[], route=[], legs=[]),
    dict(FULL, stations=V2_ST, legs=[{"route": ["depot", "north", "market"], "color": "#10b981", "back": True}, {"route": ["market", "port"]}],
         messages=[{"text": "Req", "leg": 0}, {"text": "Resp", "leg": 1, "back": True}],
         clock={"unit": "s", "from": 0, "to": 120})
]


def test_v2_python_matches_gas_exactly(core_js):
    got = _gas_batch(core_js, V2_CASES)
    bad = [str(b)[:110] for b, g in zip(V2_CASES, got) if _norm(_py(b)) != _norm(g)]
    assert not bad, bad


def test_v2_warn_and_error_glyphs():
    h = _py(dict(FULL, stations=V2_ST))
    assert '<span class="m3-pin m3-warn" style="opacity:leave;">!</span>' or '!</span>' in h
    assert '<span class="m3-pin m3-error" style="opacity:leave;">\u00d7</span>' or '\u00d7</span>' in h
    assert ".m3-warn{background:var(--mt-warn,#f59e0b)}" in h
    assert ".m3-error{background:var(--mt-err,#dc2626)}" in h


def test_v2_labels_in_over_plane():
    h = _py(FULL)
    assert '<div class="m3-plane m3-over"' in h
    assert h.index('<div class="m3-plane"') < h.index('<div class="m3-plane m3-over"')
    assert ".m3-over{background:none;box-shadow:none;pointer-events:none}" in h
    # pins are in over plane
    plane_split = h.split('<div class="m3-plane m3-over"')
    assert '<path data-cb="link"' in plane_split[0]
    assert '<div class="m3-st"' in plane_split[1]


def test_v2_clock_units_and_invalids():
    h_s = _py(dict(FULL, clock={"unit": "s", "from": 5.2, "to": 50.8}))
    assert 'data-u="s"' in h_s
    assert '--m0:5;--m1:50;' in h_s
    assert '<span class="m3-cs">50 s</span>' in h_s
    assert "Clock runs from 5 s to 50 s." in h_s

    h_ms = _py(dict(FULL, clock={"unit": "ms", "from": 100, "to": 2000}))
    assert 'data-u="ms"' in h_ms
    assert '<span class="m3-cs">2000 ms</span>' in h_ms
    assert "Clock runs from 100 ms to 2000 ms." in h_ms

    # Invalids emit no chip
    for bad_clk in [
        {"unit": "s", "from": 60, "to": 50},
        {"unit": "s", "from": -1, "to": 50},
        {"unit": "s", "from": 86401, "to": 86402},
        {"unit": "ms", "from": 0, "to": 3600001},
        {"unit": "s", "from": True, "to": 50},
    ]:
        h_bad = _py(dict(FULL, clock=bad_clk))
        assert 'data-m3="clock"' not in h_bad


def test_v2_legs_replace_route_and_timing():
    payload = dict(FULL, route=["depot", "spare"], legs=[{"route": ["depot", "north", "market"], "color": "#112233"}, {"route": ["market", "port"], "back": True}])
    h = _py(payload)
    assert 'data-key="depot-spare"' not in h
    assert 'data-leg="0"' in h and 'data-leg="1"' in h
    assert 'stroke="#112233"' in h
    assert "Leg 1: Depot, then North Hub, then Market." in h
    assert "Leg 2 (back): Port, then Market." in h


def test_v2_messages_calculation_and_alt():
    payload = dict(
        FULL,
        legs=[{"route": ["depot", "north"]}],
        messages=[{"text": "Hello", "leg": 0, "at": 0.4, "back": False}]
    )
    h = _py(payload)
    assert '<div class="m3-msg" data-m3="msg" data-leg="0"' in h
    assert '<span class="m3-chip"' in h
    assert "Hello" in h
    assert "var(--p,1)" in h
    assert "Messages: Hello (Depot to North Hub)." in h


def test_v2_version_note():
    h2 = _py(dict(FULL, version=2))
    assert "Written for" not in h2
    h1 = _py(dict(FULL, version=1))
    assert "Written for" not in h1
    h3 = _py(dict(FULL, version=3))
    assert "Written for motion_map3d version 3; drawn as version 2." in h3
    h4 = _py(dict(FULL, version=4))
    assert "Written for motion_map3d version 4; drawn as version 2." in h4
    h_float = _py(dict(FULL, version=3.5))
    assert "Written for" not in h_float


def test_v2_over_plane_is_transparent_so_the_city_shows_through():
    # the over-plane also carries .m3-plane; a same-specificity rule would lose to .m3-plane's floor colour and hide the whole city (seen in review)
    h = _py(FULL)
    assert ".m3-plane.m3-over{background:none" in h
    assert h.index('class="m3-plane m3-over"') > h.index('class="m3-plane"')


def test_v2_back_leg_drives_in_its_own_lane():
    legs = [{"route": ["depot", "north"]}, {"route": ["depot", "north"], "back": True}]
    h = _py(dict(FULL, legs=legs))
    out = re.search(r'data-leg="0" data-m3="seg" d="([^"]+)"', h).group(1)
    back = re.search(r'data-leg="1" data-m3="seg" d="([^"]+)"', h).group(1)
    assert out == "M12,78 L38,30" and back != "M38,30 L12,78" and back.startswith("M3")


# ─── camera keys and follow (I145, owner: "multiple angle rotation ... at every couple of destinations and the last destination") ───
LONG = dict(FULL, stations=ST, route=["depot", "north", "market", "port", "spare"])
CAM_CASES = [
    dict(FULL, camera={"keys": [{"at": 0, "turn": 0, "tilt": 0, "zoom": 0.6}, {"at": 0.3, "turn": 22, "tilt": 55, "zoom": 1}, {"at": 0.6, "turn": -40}, {"at": 1, "turn": 90, "zoom": 1.4}]}),
    dict(FULL, camera={"keys": [{"at": 0.5, "turn": 45}]}),
    dict(FULL, camera={"keys": [{"at": 0.5}, {"at": 0.4}, {"at": 0.5}, {"at": "x"}, {"at": None}, {"at": True}, {"at": 2}, {"at": -1}, {"at": 0.9, "turn": 999, "tilt": -5, "zoom": 9}]}),
    dict(FULL, camera={"keys": [{"at": i / 10, "turn": i * 20} for i in range(11)]}),
    dict(FULL, camera={"keys": "x"}), dict(FULL, camera={"keys": [HOSTILE, {"at": 0.2, "turn": HOSTILE}]}), dict(FULL, camera={"keys": []}),
    dict(FULL, camera={"follow": 1}), dict(FULL, camera={"follow": 2}), dict(LONG, camera={"follow": 2}), dict(LONG, camera={"follow": 3, "from": 0.4, "to": 1.6}),
    dict(LONG, camera={"follow": 6}), dict(LONG, camera={"follow": 0}), dict(LONG, camera={"follow": 99}), dict(LONG, camera={"follow": -2}), dict(LONG, camera={"follow": "2"}),
    dict(LONG, camera={"follow": True}), dict(LONG, camera={"follow": 2.7}), dict(LONG, camera={"follow": HOSTILE}), dict(LONG, camera={"follow": None}),
    dict(LONG, tilt=0, camera={"follow": 1}), dict(dict(FULL, route=["depot"]), camera={"follow": 2}),
    dict(LONG, camera={"follow": 2, "keys": [{"at": 0.5, "turn": 10}]}),
    dict(FULL, legs=[{"route": ["depot", "north", "market"]}, {"route": ["depot", "north", "market"], "back": True}], camera={"follow": 2}),
]


def test_camera_python_matches_gas_exactly(core_js):
    got = _gas_batch(core_js, CAM_CASES)
    bad = [str(b)[:110] for b, g in zip(CAM_CASES, got) if _norm(_py(b)) != _norm(g)]
    assert not bad, bad


def test_camera_keys_drive_turn_tilt_and_zoom_from_p_and_drop_bad_keys():
    h = _py(CAM_CASES[0])
    root = re.search(r'data-m3="root" style="([^"]+)"', h).group(1)
    assert root.startswith("--tilt:calc(0 + 55*clamp(0,calc((var(--p,1) - 0)/0.3),1))") and ";--e:1;" in root and "--rz:calc(0 + 22*" in root
    assert "--c:" not in root   # the default descent is replaced, not mixed in
    bad = _py(CAM_CASES[2])
    assert "8 camera keys were left out" in bad and "--rz:calc(22);" in bad   # 7 bad entries + 1 past the cap of 8; the one good key holds still
    assert "--rz:calc(180);--e:1;--zm:calc(3);" in _py(dict(FULL, camera={"keys": [{"at": 0, "turn": 999, "zoom": 9}]}))   # clamped
    assert "--c:clamp" in _py(FULL)   # no keys: the default descent, as before


def test_camera_follow_turns_at_every_nth_arrival_and_closes_in_on_the_last():
    h = _py(dict(LONG, camera={"follow": 2}))
    rz = re.search(r'--rz:calc\(([^;]+)\);', h).group(1)
    zm = re.search(r'--zm:calc\(([^;]+)\);', h).group(1)
    # 4 segments, follow 2: re-angle on arriving at stations 2 and 4 (the last), each a short move just before the arrival
    assert rz.count("clamp(") == 3   # the descent, the turn arriving at station 2, the turn arriving at the last station
    assert "-50*clamp" in rz and "5*clamp" in rz   # 22 -> -28, then -28 -> -23 at the last destination
    assert zm.count("clamp(") == 3   # descent zoom, a little closer at station 2, closest at the last destination
    assert _py(dict(LONG, camera=dict(LONG["camera"], follow=0))) == _py(LONG)
    assert _py(dict(LONG, camera={"follow": 2, "keys": [{"at": 0.5, "turn": 10}]})) == _py(dict(LONG, camera={"keys": [{"at": 0.5, "turn": 10}]}))


TRACK_CASES = [
    dict(LONG, camera={"follow": 2}), dict(LONG, camera={"follow": 1, "track": 1}), dict(LONG, camera={"follow": 2, "track": 0}),
    dict(LONG, camera={"track": 0.4}), dict(LONG, camera={"track": 9}), dict(LONG, camera={"track": -1}), dict(LONG, camera={"track": "x"}), dict(LONG, camera={"track": True}),
    dict(LONG, camera={"track": HOSTILE}), dict(LONG, camera={"keys": [{"at": 0.5, "turn": 10}], "track": 0.5}), dict(LONG, camera={"keys": [{"at": 0.5}], "follow": 2}),
    dict(FULL, legs=[{"route": ["depot", "north", "market"]}, {"route": ["port", "spare"]}, {"route": ["depot", "north", "market"], "back": True}], camera={"follow": 2}),
    dict(FULL, route=["depot"], camera={"track": 1}), dict(FULL, route=["depot", "port"], stations=[dict(ST[0], x=50, y=50), dict(ST[3], x=50, y=50)], camera={"track": 1}),
]


def test_track_python_matches_gas_exactly(core_js):
    got = _gas_batch(core_js, TRACK_CASES)
    bad = [str(b)[:110] for b, g in zip(TRACK_CASES, got) if _norm(_py(b)) != _norm(g)]
    assert not bad, bad


def test_track_pans_both_planes_after_the_head_of_the_route():
    h = _py(dict(LONG, camera={"follow": 2}))   # follow tracks at 0.6 by default
    assert h.count("translate(var(--px),var(--py))") == 2   # the city plane and the label plane move together
    px = re.search(r"--px:calc\(\(50 - \(([^;]+)\)\)\*0\.6\*1%\);", h).group(1)
    assert px.startswith("12 + 26*clamp(0,calc((var(--p,1) - 0.3)/")   # starts on the first station (Depot, x 12), then rides the first segment
    assert px.count("clamp(") == 4   # one term per segment; one leg, so no jumps
    jumps = _py(dict(FULL, legs=[{"route": ["depot", "north"]}, {"route": ["port", "spare"]}], camera={"track": 1}))
    assert re.search(r"--px:calc\(\(50 - \(([^;]+)\)\)", jumps).group(1).count("clamp(") == 3   # two segments plus the jump to the second leg
    assert "translate(" not in _py(dict(LONG, camera={"follow": 2, "track": 0})) and "translate(" not in _py(LONG)


NEW_CASES = [
    # 1. Ground: valid sets and windows
    dict(FULL, ground={"set": "us-states", "window": [-125, -65, 24, 50], "highlight": ["CA", "NY"], "fill": "#112233", "accent": "#445566"}),
    dict(FULL, ground={"set": "europe-countries", "window": [-10, 30, 35, 65], "highlight": ["FRA", "DEU"]}),
    dict(FULL, ground={"set": "world-countries", "window": [-180, 180, -58, 84], "highlight": ["USA", "CAN", "GBR"]}),
    # Ground invalid inputs
    dict(FULL, ground={"set": "unknown-set", "window": [-10, 10, 10, 20]}),
    dict(FULL, ground={"set": "us-states", "window": "invalid"}),
    dict(FULL, ground={"set": "us-states", "window": [-10, 10, 20]}),
    dict(FULL, ground={"set": "us-states", "window": [10, -10, 20, 30]}),
    dict(FULL, ground={"set": "us-states", "window": [-10, 10, 40, 20]}),
    dict(FULL, ground={"set": "us-states", "window": [-200, 10, 20, 30]}),
    dict(FULL, ground="not-an-object"),
    dict(FULL, ground={"set": "us-states", "window": [-120, -70, 25, 48], "fill": HOSTILE, "accent": HOSTILE, "highlight": [HOSTILE] * 30}),
    # 2. Station lon/lat projection
    dict(FULL, ground={"set": "us-states", "window": [-125, -65, 24, 50]},
         stations=[{"id": "sf", "lon": -122.4, "lat": 37.7, "label": "San Francisco"},
                   {"id": "nyc", "lon": -74.0, "lat": 40.7, "label": "New York"}],
         route=["sf", "nyc"]),
    dict(FULL, stations=[{"id": "sf", "lon": -122.4, "lat": 37.7, "x": 10, "y": 20, "label": "SF"}], route=["sf"]),
    dict(FULL, ground={"set": "us-states", "window": [-125, -65, 24, 50]},
         stations=[{"id": "sf", "lon": "x", "lat": None, "x": 15, "y": 25}], route=["sf"]),
    # 3. Cities
    dict(FULL, cities=[{"x": 10, "y": 10, "w": 20, "h": 20, "count": 6, "seed": 42, "height": 12},
                       {"x": 60, "y": 50, "w": 30, "h": 30, "count": 9}]),
    dict(FULL, cities=[{"x": i * 10, "y": 10, "w": 8, "h": 8} for i in range(12)]),
    dict(FULL, cities=["not-an-obj", None, {}]),
    dict(FULL, blocks=[{"x": 5, "y": 5, "w": 10, "h": 10}],
         cities=[{"x": 50, "y": 50, "w": 20, "h": 20, "count": 4}]),
    # 4. Arc
    dict(FULL, arc=True),
    dict(FULL, arc=0.3),
    dict(FULL, arc=0.6),
    dict(FULL, arc=0.0),
    dict(FULL, arc=-0.5),
    dict(FULL, arc=1.5),
    dict(FULL, arc="invalid"),
    dict(FULL, arc=0.25, legs=[{"route": ["depot", "market"], "back": False}, {"route": ["depot", "market"], "back": True}]),
    dict(FULL, arc=0.2, messages=[{"leg": 0, "text": "Packet", "at": 0.4}]),
    dict(FULL, arc=0.2, camera={"track": 0.8, "follow": 2}),
    # 5. Dwell
    dict(FULL, stations=[dict(ST[0], dwell=0.1), dict(ST[1], dwell=0.15), dict(ST[2], dwell=0.05), ST[3], ST[4]]),
    dict(FULL, stations=[dict(ST[0], dwell=0.3), dict(ST[1], dwell=0.3), dict(ST[2], dwell=0.3), ST[3], ST[4]]),
    dict(FULL, stations=[dict(ST[0], dwell=-0.1), dict(ST[1], dwell=0.5), dict(ST[2], dwell="invalid")]),
    # Combined features
    dict(FULL, arc=0.25, ground={"set": "europe-countries", "window": [-10, 25, 40, 60], "highlight": ["FRA"]},
         stations=[{"id": "par", "lon": 2.35, "lat": 48.85, "dwell": 0.1, "label": "Paris"},
                   {"id": "ber", "lon": 13.4, "lat": 52.52, "label": "Berlin"}],
         route=["par", "ber"],
         cities=[{"x": 20, "y": 20, "w": 15, "h": 15, "count": 5}],
         messages=[{"leg": 0, "text": "Msg"}],
         camera={"track": 0.5}),
]


def test_new_cases_python_matches_gas(core_js):
    py_outs = [_norm(_py(b)) for b in NEW_CASES]
    gas_outs = [_norm(s) for s in _gas_batch(core_js, NEW_CASES)]
    diffs = []
    for i, (p, g) in enumerate(zip(py_outs, gas_outs)):
        if p != g:
            diffs.append((i, p, g))
    if diffs:
        idx, p, g = diffs[0]
        pytest.fail(f"Mismatch at case {idx}:\nPAYLOAD: {json.dumps(NEW_CASES[idx])}\nPY:\n{p}\nGAS:\n{g}")


def test_new_fields_do_what_they_say():
    """Behaviour, not only twin parity (Distribution PM review of the Gemini draft)."""
    g = dict(FULL, ground={"set": "world-countries", "window": [-84, 18, 14, 75], "highlight": ["FRA", "USA"]})
    h = _py(g)
    svg = re.search(r'<svg class="m3-ground"[^>]*>(.*?)</svg>', h, re.S)
    assert svg and 'aria-hidden="true"' in svg.group(0) and svg.group(1).count("<path") > 20
    assert svg.group(1).count('fill="#3a4a63"') == 2, "exactly the two highlighted regions take the accent"
    assert "France" in h and "United States" in h   # named in the text alternative
    # with a ground and no blocks/cities, no generated city is drawn
    assert 'class="m3-b"' not in h
    # lon/lat place the station only when a ground is valid
    one = lambda extra: dict(FULL, stations=[{"id": "a", "lon": -77.5, "lat": 39.0, "x": 90, "y": 90}, {"id": "b", "x": 10, "y": 10}], route=["a", "b"], **extra)
    with_g, without_g = _py(one({"ground": g["ground"]})), _py(one({}))
    assert with_g != without_g and "left:90%;top:90%" in without_g.replace(".00", "")
    # cities add their blocks and replace the whole-plane city
    c = _py(dict(FULL, cities=[{"x": 10, "y": 10, "w": 20, "h": 20, "count": 6, "seed": 3}]))
    assert 0 < c.count('class="m3-b"') <= 6
    # arc bends each segment into one quadratic path; no arc keeps straight lines
    assert _py(dict(FULL, arc=0.3)).count('data-m3="seg" d="M') == 3 and " Q" in _py(dict(FULL, arc=0.3)) and " Q" not in _py(FULL)
    # dwell delays the next segment's start
    starts = lambda b: [float(s) for s, _ in re.findall(r'stroke-dashoffset:calc\(1 - clamp\(0,calc\(\(var\(--p,1\) - ([\d.]+)\)/([\d.]+)\),1\)\)', _py(b))]
    plain, held = starts(FULL), starts(dict(FULL, stations=[dict(ST[0]), dict(ST[1], dwell=0.1), ST[2], ST[3], ST[4]]))
    assert plain[0] == held[0] and held[2] > plain[2]
    # hostile colours and ids never reach markup
    bad = _py(dict(FULL, ground={"set": "us-states", "window": [-120, -70, 25, 48], "fill": HOSTILE, "accent": HOSTILE, "highlight": [HOSTILE]}))
    assert "<script" not in bad and "onload" not in bad
