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
    assert "Written for motion_map3d version 3; drawn as version 1." in _py(dict(FULL, version=3))
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
