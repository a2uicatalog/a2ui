"""Design motion (2026-09-30): tokens, the generic `enter` prop, motion_group,
motion_tokens, motion_timeline and the demo kit (demo_window/page/wordmark/kpis/
chart/toggle_grid/progress/cursor/caption/orb/panel).

Proven four ways, because each catches a different failure:
  1. GAS/Python PARITY modulo uid, over every atom and hostile/edge payloads
     (the twins are hand-kept: atoms_motion.gs <-> renderers/web_article.py).
  2. The generic `enter` wrapper is INERT without `enter`: wrapping every renderer
     must not change a single byte for blocks that do not ask for motion.
  3. HOSTILE INPUT: ids, ease names, captions and titles can never reach the page
     as markup or into the timeline's config object.
  4. The CLIENT MATHS, by running the timeline in real headless Chromium at fixed
     instants (#t=) and reading back what the runtime did to the DOM. Skipped if
     no Chromium is installed.
"""
from __future__ import annotations

import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import gen_mcp_apps_bundle as gen  # noqa: E402

from renderers import web_article as wa  # noqa: E402

DEMO_ATOMS = ["demo_window", "demo_page", "demo_wordmark", "demo_kpis", "demo_chart", "demo_toggle_grid", "demo_progress",
              "demo_cursor", "demo_caption", "demo_orb", "demo_panel"]
PRIMITIVES = ["motion_layer", "motion_text", "motion_shape", "motion_counter"]
REEL = ["motion_pill", "motion_checklist", "motion_stepper", "motion_orbit", "motion_code", "motion_mark", "motion_browser", "motion_sketch", "motion_leader", "motion_path", "motion_mask"]  # from the studied reference film, 2026-10-01
REEL3 = ["motion_device", "motion_strike", "motion_rays", "motion_hud", "motion_cells", "motion_stack3d", "motion_shake", "motion_flash"]  # third reference, 2026-10-01
MOTION_ATOMS = ["motion_group", "motion_tokens", "motion_timeline"] + PRIMITIVES + REEL + REEL3 + DEMO_ATOMS

UID_RE = re.compile(r'id="(?:mt|mo)-([a-z0-9]{6})"')


def _norm(html: str) -> str:
    """Replace each element uid (random in GAS, content-derived in Python) with a stable placeholder."""
    for i, uid in enumerate(dict.fromkeys(UID_RE.findall(html))):
        html = html.replace(uid, f"UID{i}")
    return html


@pytest.fixture(scope="module")
def core_js():
    bundle = gen.build_bundle()
    blocks = re.findall(r"<script>\n(.*?)\n</script>", bundle, re.S)
    return [b for b in blocks if "a2ui-core" in b[:300]][0]


def _node(core_js: str, body: str):
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "d.js"
        d.write_text("global.window = global;\n" + core_js + "\n" + body)
        proc = subprocess.run(["node", str(d)], capture_output=True, text=True, timeout=60)
        assert proc.returncode == 0, proc.stderr[-1500:]
        return json.loads(proc.stdout.strip().splitlines()[-1])


def _gas_batch(core_js: str, blocks: list[dict]) -> list[str]:
    return _node(core_js, f"var B = {json.dumps(blocks)}; console.log(JSON.stringify(B.map(function(b){{ return renderAtoms([b], {{}}); }})));")


def _py(block: dict) -> str:
    wa._mo_install()
    return wa._RENDERERS[block.get("component") or block["type"]](dict(block))


# ─── payloads ─────────────────────────────────────────────────────────────────
TIMELINE = {
    "type": "motion_timeline", "duration": 8, "bpm": 120, "ease": "standard", "title": "T",
    "blocks": [
        {"type": "demo_window", "id": "win", "stack": True, "nav": [{"label": "Home", "active": True}, "Reports"], "place": {"x": 4, "y": 6, "w": 66, "h": 86, "z": 2},
         "blocks": [{"type": "demo_page", "id": "a", "heading": "A", "blocks": [{"type": "demo_kpis", "id": "kpi", "items": [{"label": "P", "value": 2.4, "prefix": "€", "suffix": "M", "decimals": 1}]}]},
                    {"type": "demo_page", "id": "b", "heading": "B"}]},
        {"type": "demo_cursor", "id": "cur", "label": "Agent", "place": {"x": 40, "y": 60, "origin": "tl"}},
        {"type": "demo_caption", "id": "cap", "lines": [{"who": "agent", "text": "one"}, {"who": "you", "text": "two"}], "layer": "hud", "place": {"x": 0, "y": 90, "w": 100}},
    ],
    "tracks": [{"target": "kpi", "keys": [{"beat": 0, "p": 0}, {"beat": 8, "p": 1, "ease": "expo-out"}]},
               {"target": "cur", "keys": [{"t": 0, "x": 40, "y": 60}, {"t": 2, "x": 10, "y": 20, "ease": "overshoot"}]},
               {"target": "a", "keys": [{"t": 0, "opacity": 1}, {"t": 3, "opacity": 0, "ease": [0.1, 0.2, 0.3, 0.4]}]},
               {"target": "cap", "keys": [{"t": 0, "step": 0}, {"t": 4, "step": 1, "ease": "hold"}]}],
    "camera": {"keys": [{"t": 0, "zoom": 1}, {"t": 4, "zoom": 1.2, "ry": -8, "rx": 4, "ease": "quart-in-out"}]},
}

STITCHED = {
    "type": "motion_timeline", "duration": 9, "bpm": 120, "title": "S", "stitch": "push",
    "blocks": [{"type": "motion_layer", "id": "s1", "blocks": [{"type": "motion_text", "id": "a", "text": "One", "place": {"x": 5, "y": 5, "w": 50}}]},
               {"type": "motion_layer", "id": "s2", "blocks": [{"type": "motion_text", "text": "Two", "place": {"x": 5, "y": 5, "w": 50}}]},
               {"type": "motion_layer", "id": "s3", "blocks": [{"type": "motion_pill", "text": "Three *now*", "place": {"x": 5, "y": 5}}]}],
    "scenes": [{"layer": "s1", "t": 0}, {"layer": "s2", "beat": 6, "transition": "zoom-through"}, {"layer": "s3", "t": 6}],
}

PAYLOADS = {
    "motion_group": [{}, {"effect": "pop", "stagger": 40, "blocks": [{"type": "demo_orb"}, {"type": "demo_cursor", "id": "c"}]},
                     {"effect": "<bad>", "ease": "zzz", "duration": -5, "delay": 99999999, "on": "view", "blocks": [{"type": "demo_orb"}]}],
    "motion_tokens": [{}, {"show": "ease", "theme": "light", "accent": "#F97316"}, {"show": "duration"}],
    "motion_timeline": [{}, TIMELINE,
                        dict(TIMELINE, aspect="9:16", loop=False, autoplay=False, controls=False, backdrop="grid", theme="light", poster=3, accent="#F97316", background="#101820"),
                        STITCHED, dict(STITCHED, stitch="zoom-through", overlap=1.2), dict(STITCHED, stitch="cut"), dict(STITCHED, stitch="<x>", overlap="no"),
                        dict(STITCHED, stitch="whip"), dict(STITCHED, stitch="wipe", overlap=1.0), dict(STITCHED, scenes=[{"layer": "s1", "t": 0}, {"layer": "s2", "t": 3, "transition": "wipe"}, {"layer": "s3", "t": 6, "transition": "whip"}]),
                        dict(STITCHED, scenes=[{"layer": "s1", "t": 0}, {"layer": "nope", "t": 2}, {"layer": "s2", "beat": 2, "transition": "blur"}, {"layer": "s3", "t": "x"}, "junk", {"layer": "s3", "t": 5, "transition": "<b>"}]),
                        dict(TIMELINE, blocks=TIMELINE["blocks"] + [{"type": "motion_timeline"}, {"type": "no_such_atom"}, "junk"],
                             tracks=TIMELINE["tracks"] + [{"target": "nope", "keys": []}, {"target": "cur", "keys": [{"t": "x"}, None, {"beat": 1, "x": 5}]}])],
    "demo_window": [{}, {"title": "Lumen", "tone": "dark", "accent": "#2563EB", "nav": [{"label": "Home"}, {"label": "Reports", "active": True}, "Contacts"], "heading": "Hi", "sub": "there",
                         "blocks": [{"type": "demo_kpis", "id": "k", "items": [{"label": "A", "value": 1}]}, {"type": "no_such_atom"}], "height": 500},
                    {"stack": True, "blocks": [{"type": "demo_page", "id": "p1"}, {"type": "demo_page"}]}],
    "demo_page": [{}, {"heading": "H <b>", "sub": "s", "blocks": [{"type": "demo_progress", "id": "x", "label": "L", "to": 10}]}],
    "demo_wordmark": [{}, {"text": "Supersonik", "size": 99, "outline": "accent", "accent": "#22c55e", "tone": "light"}],
    "demo_kpis": [{}, {"items": [{"label": "Pipeline", "value": 2.4, "prefix": "€", "suffix": "M", "decimals": 1, "delta": "+12%"}, {"label": "Open", "value": 184},
                                 {"label": "Neg", "value": -1234567.891, "decimals": 2}, {"label": "Junk", "value": "abc", "decimals": 9}, "str"]}],
    "demo_chart": [{}, {"kind": "bars", "data": [3, 4, 2.5, 8], "labels": ["a", "b", "c"], "highlight": 1, "callout": "+38% vs <last>", "height": 300, "accent": "#ef4444", "title": "T"},
                   {"kind": "line", "data": [1, 1, 1], "highlight": 99}, {"kind": "line", "data": [5]}, {"kind": "bars", "data": [-3, 4, -1]}],
    "demo_toggle_grid": [{}, {"columns": 2, "cards": [{"title": "CRM", "sub": "s", "on_at": 0.3}, "Chat", {"title": "Mail", "on_at": 7}], "accent": "#0ea5e9"}, {"cards": [{"title": "only"}]}],
    "demo_progress": [{}, {"label": "Syncing", "to": 1207, "suffix": "contacts"}, {"label": "Pct", "to": 99.5, "decimals": 1, "suffix": "%", "prefix": "~"}],
    "demo_cursor": [{}, {"label": "Supersonik <x>", "accent": "#ff0000"}, {"label": ""}],
    "demo_caption": [{}, {"lines": [{"who": "agent pt", "text": "Claro <b>"}, {"text": "no who"}, "bare"], "tone": "light", "accent": "#00ff00"}],
    "demo_orb": [{}, {"size": 200, "bars": 5, "label": "Agent", "accent": "#22d3ee"}, {"size": 9999, "bars": 99}],
    "motion_layer": [{}, {"blocks": [{"type": "motion_text", "id": "a", "text": "Hi", "place": {"x": 5, "y": 5, "w": 50}},
                                      {"type": "motion_shape", "shape": "ring", "place": {"x": 60, "y": 10, "w": 30, "h": 50, "z": 3}},
                                      "junk", {"type": "motion_timeline"}, {"type": "no_such_atom"}, {"type": "motion_layer", "id": "inner", "blocks": []}]}],
    "motion_text": [{}, {"text": "NORTH\nLIGHT", "size": 260, "font": "display", "weight": "black", "reveal": "mask", "tracking": -0.045, "line_height": 0.92, "color": "#FFF6E8", "uppercase": True},
                    {"text": "a b c\nd e", "mode": "words", "reveal": "drop", "overlap": 5, "align": "middle"},
                    {"text": "chars <b>& \"q\" \u2603", "mode": "chars", "reveal": "blur", "align": "end"},
                    {"text": "x" * 200, "mode": "chars"}, {"text": "a\nb\nc\nd\ne\nf", "mode": "block", "reveal": "fade"}, {"text": ""},
                    {"text": "x", "color": "red", "reveal": "toString", "mode": "constructor", "font": "__proto__", "weight": "hasOwnProperty", "size": 99999},
                    {"text": "il te faut un *plan*.\nand *a b* c", "mode": "words", "reveal": "fade", "accent": "#ff6a2b"},
                    {"text": "co*mm*ent *on fait ?*", "mode": "chars", "reveal": "mask"}, {"text": "*all* ** star <b>*", "mode": "lines"},
                    {"text": "*x\ny* z", "mode": "block"}, {"text": "*" * 150, "mode": "chars"},
                    {"text": "Vos meubles sont\nidentifi\u00e9s", "reveal": "bar", "bar": "#12467a", "color": "#ffffff", "size": 40, "mode": "lines"}, {"text": "a b *c*", "reveal": "bar", "mode": "words", "bar": "red"},
                    {"text": "M\u00c9TRIE", "extrude": 18, "extrude_color": "#7a1d6b", "font": "display", "weight": "black"}, {"text": "UP", "extrude": 99, "extrude_dir": "down", "extrude_color": "url(x)"}],
    "motion_shape": [{}, {"shape": "circle", "fill": "#FF0000", "fill2": "#0000ff", "angle": 135, "blur": 150, "draw": "fade", "w": 400, "h": 300},
                     {"shape": "ring", "thickness": 10, "fill": "#ffb347", "fill2": "#ff3d81"}, {"shape": "ring", "draw": "scale"}, {"shape": "line", "thickness": 4, "draw": "grow-y"},
                     {"shape": "rect", "radius": 80, "draw": "sweep", "fill": "url(javascript:alert(1))"}, {"shape": "<x>", "draw": "none", "w": "9", "h": True}],
    "motion_counter": [{}, {"to": 1207, "from": 100, "decimals": 1, "prefix": "\u20ac", "suffix": "M", "size": 200, "label": "artists <b>", "label_size": 20, "align": "middle", "color": "#ffb347"},
                       {"to": "abc"}, {"to": -5.5, "from": "x", "decimals": 9, "font": "mono", "weight": "regular"}],
    "motion_pill": [{}, {"text": "Comment *Motion* under this post", "icon": "\u2191", "size": 40, "align": "middle", "accent": "#ff6a2b", "color": "#fff6e8", "fill": "#1a1020"},
                    {"text": "a ** b <i>*x", "align": "end"}, {"text": 5, "icon": "\"><b>", "size": 9999, "align": "toString"}],
    "motion_checklist": [{}, {"title": "The recipe <b>", "items": ["Your know-how", {"text": "Your process", "icon": "\U0001F4C1"}, "Your automations", {"text": ""}, 5, None, "x" * 80, "g", "h"], "skeleton": 2, "size": 30, "accent": "#ff6a2b"},
                          {"items": "nope", "skeleton": 99}],
    "motion_stepper": [{}, {"title": "Process map", "scan": True, "accent": "#ff6a2b", "size": 18,
                            "columns": [{"title": "Prospecting", "items": ["Find leads", {"text": "LinkedIn messages", "meta": "5 h/wk", "value": 0.6}, "Enrich"]},
                                        {"title": "Sales <b>", "items": [{"text": "Calls", "meta": "7 h/wk", "value": 2}, "Proposals"]},
                                        {"title": "Delivery"}, "junk", None, [], {}, {"title": "Seventh", "items": ["x"]}],
                            "focus": [[0, 1], [1, 0], [9, 9], "bad", [0.9, 1.9], [True, 1]], "badges": ["92", "<81>", "x", "y", 7]},
                       {"columns": [{"items": [1, 2, 3, 4, 5, 6]}], "focus": [[0, 0]]}, {"columns": "no", "focus": "no"}],
    "motion_orbit": [{}, {"items": ["N", "G", "Mail", {"text": "Drive"}, "", 5, "This is long", "<b>", "&", "Q", "R", "S", "T"], "size": 80, "rx": 42, "ry": 30, "start": -60, "spin": 120, "fill": "#101820", "ink": "#ffb347"},
                        {"items": ["A"], "ring": False, "size": 9999, "rx": 0, "spin": "x"}, {"items": 3}],
    "motion_code": [{}, {"file": "Cockpit.tsx <x>", "size": 20, "accent": "#ff6a2b", "lines": ["export default function Cockpit() {", "  const leads = useLeads(\"enrichie\");", "  // we don't type this by hand", "", "  return await sync(leads, 'auto') ", "x" * 100, 5]},
                       {"lines": "no"}, {"lines": ["a"] * 30}],
    "motion_mark": [{}, {"size": 200, "accent": "#6267e7", "accent2": "#2ac4ce"}, {"size": 9999, "accent": "red", "accent2": "url(x)"}, {"size": "x"}],
    "motion_browser": [{}, {"query": "stat", "placeholder": "Search atoms\u2026", "chips": ["All", "Web", "MCP Apps", "", 5], "count": "51 atoms", "columns": 2, "pick": 1, "accent": "#6267e7", "well": "#dfe6f1",
                           "cards": [{"title": "Stat Card", "text": "single KPI value with label delta and accent colour indicator", "badge": "MCP Apps", "source": "a2uicatalog", "preview": {"type": "stat_card", "value": "1,234", "label": "Stat"}},
                                     {"title": "Status <b>", "text": "x" * 120, "badge": "<i>", "preview": {"type": "stat_card", "value": "9", "label": "<Live>", "delta": "+1"}}, "junk", {"title": "", "preview": {"type": "no_such_atom"}}, {"preview": "no"}]},
                          {"cards": "no", "chips": "no", "pick": 99, "query": "q" * 40}, {"query": "ab", "pick": 5, "cards": [{"title": "Only"}]}],
    "motion_sketch": [{}, {"label": "A robot <b>", "w": 300, "h": 200, "strokes": [{"d": "M 10 10 L 100 10 Q 120 10 120 30 Z", "color": "#6267e7", "width": 8, "fill": "#00b7c3", "fill_opacity": 0.3},
                                                                 {"d": "M10 10 a 10 10 0 1 0 20 0 a 10 10 0 1 0 -20 0"}, {"d": "M 0 0 L 1e2 -5.5"}]},
                       {"strokes": [{"d": "M 0 0\" onload=\"alert(1)"}, {"d": "<script>alert(1)</script>"}, {"d": "url(javascript:alert(1))"}, {"d": "M 0 0 L 10 10 \n L 5 5"}, {"d": "x" * 800}, {"d": 5}, "junk", {"d": "M 1 1 Z", "color": "red", "fill": "url(x)", "width": 999}]},
                       {"strokes": "no", "w": "x", "h": 9999}],
    "motion_leader": [{}, {"from": [20, 250], "to": [350, 40], "curve": 35, "label": "Entr\u00e9e H2O <b>", "label_at": "start", "color": "#ff6a2b", "label_color": "#fff6e8", "width": 7, "size": 30, "w": 500, "h": 320},
                      {"from": [0, 0], "to": [0, 0], "arrow": False, "dot": False, "label": "same point"}, {"from": "no", "to": [1], "curve": 999, "width": 999, "size": 1, "w": "x"},
                      {"from": [1e12, "x"], "to": [-5e9, 7], "label": "x" * 80, "color": "red", "label_color": "url(javascript:alert(1))"}],
    "motion_path": [{}, {"d": "M 20 300 C 100 100 300 100 380 300", "nodes": [{"x": 20, "y": 300, "at": 0, "label": "Start"}, {"x": 200, "y": 150, "at": 0.5, "label": "Mid <i>"}, {"x": 380, "y": 300, "at": 1}], "color": "#0a66c2", "label_color": "#ffffff", "width": 9, "size": 26, "label": "Line A", "w": 400, "h": 400},
                     {"d": "M 0 0\" onload=\"alert(1)", "nodes": ["junk", None, [], {}, {"x": "9", "y": "x", "at": 7, "label": "<script>"}], "marker": False}, {"d": 5, "nodes": [{"x": 1, "y": 1}] * 12, "w": 9999}],
    "motion_device": [{}, {"kind": "laptop", "width": 640, "scroll": 400, "label": "Site <b>", "fill": "#101820", "accent": "#ff6a2b", "blocks": [{"type": "motion_pill", "text": "Hello"}, {"type": "motion_counter", "to": 5}]},
                      {"kind": "tablet", "blocks": ["junk", {"type": "no_such_atom"}] + [{"type": "motion_pill", "text": "x"}] * 9}, {"kind": "toString", "width": 99999, "scroll": "x", "fill": "url(x)", "blocks": "no"}],
    "motion_strike": [{}, {"text": "The old way <b>", "mode": "highlight", "size": 90, "align": "middle", "accent": "#ff6a2b", "color": "#fff6e8", "weight": "bold"}, {"text": "Cut", "mode": "underline"},
                      {"text": "x" * 200, "mode": "constructor", "weight": "hasOwnProperty", "color": "red", "size": 99999}, {"text": 5}],
    "motion_rays": [{}, {"kind": "speed", "count": 12, "thickness": 0.3, "strength": 0.6, "accent": "#ff6a2b"}, {"kind": "burst", "count": 7, "thickness": 0.77, "spin": -90, "strength": 1},
                    {"kind": "__proto__", "count": 9999, "thickness": "x", "spin": "9;}", "strength": 99, "accent": "url(javascript:alert(1))"}, {"count": 3, "thickness": 0}],
    "motion_hud": [{}, {"seconds": 36, "label": "REC <b>", "size": 18, "corners": False, "accent": "#ff3d3d", "color": "#ffffff"}, {"bar": False, "seconds": 99999, "size": 1}, {"seconds": "x", "label": "x" * 80, "corners": "no"}],
    "motion_cells": [{}, {"columns": 8, "rows": 8, "mode": "flip", "numbers": True, "gap": 2, "radius": 0, "size": 12, "accent": "#222222", "accent2": "#eeeeee"}, {"mode": "fill", "chess": False, "columns": 3, "rows": 2},
                     {"mode": "toString", "columns": 999, "rows": "x", "gap": "9;}", "radius": 9999, "numbers": "yes", "accent2": "url(x)"}],
    "motion_stack3d": [{}, {"mode": "stack", "items": ["Idea", {"title": "Build <b>", "text": "ship it & go", "icon": "\u2713"}, {"title": ""}, "x" * 50, 5, None, "f", "g"], "w": 260, "h": 160, "size": 20, "fill": "#101820", "accent": "#ff6a2b"},
                        {"mode": "ring", "items": ["A", "B"]}, {"mode": "ring", "items": ["A", "B", "C", "D", "E", "F"], "w": 80}, {"mode": "constructor", "items": "no", "w": 99999, "h": "x", "fill": "url(x)"}],
    "motion_shake": [{}, {"amount": 30, "frequency": 14, "tilt": 3.5, "blocks": [{"type": "motion_text", "id": "t", "text": "Hit", "place": {"x": 1, "y": 1}}, {"type": "motion_pill", "text": "x"}]},
                     {"amount": 9999, "frequency": "x", "tilt": 99, "blocks": ["junk", {"type": "no_such_atom"}] + [{"type": "motion_pill", "text": "x"}] * 9}, {"blocks": "no"}],
    "motion_flash": [{}, {"color": "#ffeecc", "strength": 0.5}, {"color": "red;x", "strength": 99}, {"strength": "x"}],
    "motion_mask": [{}, {"shape": "circle", "blocks": [{"type": "motion_text", "id": "t", "text": "Hi", "place": {"x": 1, "y": 1}}, {"type": "motion_shape", "shape": "rect"}]},
                    {"shape": "diagonal", "blocks": [{"type": "motion_counter", "to": 5}]}, {"shape": "rounded", "blocks": ["junk", {"type": "no_such_atom"}]}, {"shape": "bars", "blocks": [{"type": "motion_pill", "text": "x"}] * 9},
                    {"shape": "toString", "blocks": "no"}],
    "demo_panel": [{}, {"tone": "dark", "accent": "#38bdf8", "avatar": "SKX", "title": "Sam", "sub": "Head of Sales", "badge": "Prospect", "rows": [{"label": "Team", "value": "40"}, "x"]}],
}
CASES = [(a, b) for a, bs in PAYLOADS.items() for b in bs]


def test_every_motion_atom_has_a_parity_case():
    assert set(PAYLOADS) == set(MOTION_ATOMS)


def test_python_matches_gas_exactly(core_js):
    blocks = [dict(b, type=a) for a, b in CASES]
    gas = _gas_batch(core_js, blocks)
    for (a, _), blk, g in zip(CASES, blocks, gas):
        assert _norm(g) == _norm(_py(blk)), f"{a}: GAS and Python differ for {json.dumps(blk)[:200]}"


def test_token_tables_match_gas(core_js):
    g = _node(core_js, "console.log(JSON.stringify({e:_MO_EASE,d:_MO_DUR,f:Object.keys(_MO_FX),o:_MO_EASE_ORDER,n:_MO_EASE_NOTE}));")
    assert g["e"] == wa._MO_EASE and g["d"] == wa._MO_DUR and g["f"] == list(wa._MO_FX) and g["o"] == wa._MO_EASE_ORDER and g["n"] == wa._MO_EASE_NOTE
    assert set(wa._MO_EASE_ORDER) == set(wa._MO_EASE) and set(wa._MO_EASE_NOTE) == set(wa._MO_EASE)


def test_legacy_bezier_easing_presets_are_tokens():
    for name, pts in wa._BZ_PRESETS.items():
        assert wa._MO_EASE[name] == pts, name


def test_js_templates_are_byte_identical(core_js):
    g = _node(core_js, "console.log(JSON.stringify({t:_MO_TIMELINE_JS,v:_MO_VIEW_JS}));")
    assert g["t"] == wa._MO_TIMELINE_JS and g["v"] == wa._MO_VIEW_JS


# ─── the generic `enter` prop ────────────────────────────────────────────────
def test_enter_is_inert_without_enter(core_js):
    """Wrapping every renderer must not change any block that does not ask for motion (GAS side, all atoms)."""
    out = _node(core_js, """
      var orig = {}; for (var k in _RENDERERS) orig[k] = _RENDERERS[k];
      var diffs = [], n = 0;
      var samples = {body:{text:'hi'}, badge:{text:'x'}, demo_orb:{}, demo_kpis:{items:[{label:'a',value:1}]}, motion_tokens:{}, heading:{text:'h'}};
      for (var t in samples) { if (!orig[t]) continue; n++;
        var a = orig[t](JSON.parse(JSON.stringify(samples[t])));
        var b = renderAtoms([Object.assign({type:t}, samples[t])], {});
        if (a !== b) diffs.push(t); }
      console.log(JSON.stringify({n:n, diffs:diffs, wrapped:Object.keys(_RENDERERS).filter(function(k){return _RENDERERS[k]._mo;}).length, total:Object.keys(_RENDERERS).length}));
    """)
    assert out["n"] >= 4 and out["diffs"] == []
    assert out["wrapped"] == out["total"] > 500


def test_enter_wraps_any_atom_and_nested_atoms(core_js):
    blk = {"type": "demo_kpis", "items": [{"label": "a", "value": 1}], "enter": {"effect": "blur", "ease": "quint-out", "duration": "slow", "delay": 120}}
    html = _gas_batch(core_js, [blk])[0]
    assert "@keyframes moe-blur{from{opacity:0;filter:blur(12px)" in html
    assert "animation:moe-blur 640ms cubic-bezier(0.22,1,0.36,1) 120ms both" in html
    assert _norm(html) == _norm(_py(blk))
    nested = {"type": "demo_page", "blocks": [{"type": "demo_orb", "enter": "pop"}]}
    assert "moe-pop" in _gas_batch(core_js, [nested])[0] and "moe-pop" in _py(nested)


def test_enter_on_view_is_armed_by_script_not_by_default():
    html = _py({"type": "demo_orb", "enter": {"effect": "rise", "on": "view"}})
    assert 'class="mo-x"' in html and "mo-arm" in html and html.count("<script>") == 1
    # no script => nothing hides it: the armed class is added by the script, never baked in
    assert 'class="mo-x mo-arm"' not in html


def test_enter_hostile_values_never_become_markup():
    e = {"effect": "\"><script>alert(1)</script>", "ease": "x;}</style><script>alert(2)</script>", "duration": "9;}", "delay": "<b>"}
    html = _py({"type": "demo_orb", "enter": e})
    assert "alert" not in html and "<b>" not in html
    # "9;}" is no longer read leniently as 9: the payload guard drops a duration that is not a plain number, so the default applies.
    # The bad effect/ease fall back to the defaults too. Nothing hostile reaches the CSS.
    assert re.search(r"animation:moe-rise [0-9]+ms cubic-bezier\(0\.16,1,0\.3,1\) 0ms both", html) and "9;}" not in html


# ─── hostile input on the timeline ──────────────────────────────────────────
def test_timeline_config_holds_only_numbers_and_validated_ids():
    hostile = {"type": "motion_timeline", "title": "</script><script>alert(1)</script>", "duration": "9</script>",
               "blocks": [{"type": "demo_caption", "id": "cap\"><img src=x onerror=alert(1)>", "lines": [{"who": "</script>", "text": "\"></div><script>alert(3)</script>"}]},
                          {"type": "demo_cursor", "id": "ok", "label": "</script><b>"}],
               "tracks": [{"target": "ok", "keys": [{"t": 1, "x": "<script>", "opacity": 0.5, "ease": "</script>"}]}]}
    html = _py(hostile)
    assert "alert(1)" not in html.replace("&lt;", "") or "<script>alert" not in html
    assert html.count("<script>") == 1, "only the runtime may be a script element"
    cfg = re.search(r"var C=(\{.*?\});var root", html).group(1)
    assert re.fullmatch(r'[-0-9A-Za-z_.,:\[\]{}"]*', cfg), cfg
    assert 'data-mt-id="ok"' in html and "onerror" not in html.split("<script>")[0].replace("&quot;", "")


def test_timelines_cannot_nest_even_through_a_window(core_js):
    inner = {"type": "motion_timeline", "id": "in"}
    outer = {"type": "motion_timeline", "blocks": [{"type": "demo_window", "id": "w", "blocks": [inner]}]}
    for html in (_gas_batch(core_js, [outer])[0], _py(outer)):
        assert "cannot nest inside another motion_timeline" in html and html.count('class="mt-root"') == 1
    assert _py(inner).count('class="mt-root"') == 1, "depth resets after a render"


def test_timeline_reports_what_it_drops_instead_of_truncating_silently():
    t = json.loads(json.dumps(TIMELINE))
    t["blocks"] = [{"type": "demo_orb", "id": f"o{i}"} for i in range(30)] + [{"type": "demo_orb", "id": "o1"}]
    t["tracks"] = [{"target": "o0", "keys": [{"t": i * 0.1, "p": 0.5} for i in range(60)]}, {"target": "missing", "keys": []}]
    html = _py(t)
    m = re.search(r"<!-- a2ui: motion_timeline ignored (\d+) invalid", html)
    assert m and int(m.group(1)) >= 6 + 12 + 1
    assert _norm(html) == _norm(_gas_batch_cached(t))


_GAS_CACHE: dict = {}


def _gas_batch_cached(block):
    # one node process per distinct block, only used by the drop-report test
    key = json.dumps(block, sort_keys=True)
    if key not in _GAS_CACHE:
        bundle = gen.build_bundle()
        core = [b for b in re.findall(r"<script>\n(.*?)\n</script>", bundle, re.S) if "a2ui-core" in b[:300]][0]
        _GAS_CACHE[key] = _gas_batch(core, [block])[0]
    return _GAS_CACHE[key]


# ─── the client maths, in a real browser ────────────────────────────────────
CHROMIUM = shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome")
browser = pytest.mark.skipif(not CHROMIUM, reason="no Chromium installed")


def _bez(a, b, t):
    u = 1 - t
    return 3 * u * u * t * a + 3 * u * t * t * b + t * t * t


def _ease(p, u):
    lo, hi, t = 0.0, 1.0, u
    for _ in range(40):
        t = (lo + hi) / 2
        if _bez(p[0], p[2], t) < u:
            lo = t
        else:
            hi = t
    return _bez(p[1], p[3], t)


def _at(block: dict, t: float) -> str:
    html = "<!doctype html><meta charset=utf-8><body style='margin:0'>" + _py(block)
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "p.html"
        f.write_text(html)
        out = subprocess.run([CHROMIUM, "--headless=new", "--no-sandbox", "--disable-gpu", "--window-size=1000,700", "--virtual-time-budget=1500",
                              "--dump-dom", f"file://{f}#t={t}"], capture_output=True, text=True, timeout=90).stdout
    assert "mt-root" in out, out[:300]
    return out


def _style(dom: str, mt_id: str) -> dict:
    m = re.search(r'<div class="mt-el" data-mt-id="%s"[^>]*style="([^"]*)"' % mt_id, dom)
    assert m, f"no element {mt_id}"
    return {k.strip(): v.strip() for k, v in (s.split(":", 1) for s in m.group(1).split(";") if ":" in s)}


def _stage(tracks, extra=None, dur=4):
    blk = {"type": "motion_timeline", "duration": dur, "controls": False, "autoplay": False, "ease": "linear",
           "blocks": [{"type": "demo_kpis", "id": "k", "items": [{"label": "P", "value": 2.4, "prefix": "€", "suffix": "M", "decimals": 1}], "place": {"x": 10, "y": 20, "w": 50, "h": 20}},
                      {"type": "demo_progress", "id": "sync", "label": "S", "to": 1207, "suffix": "contacts", "place": {"x": 10, "y": 50, "w": 50}},
                      {"type": "demo_cursor", "id": "cur", "place": {"x": 0, "y": 0}}],
           "tracks": tracks}
    blk.update(extra or {})
    return blk


@browser
def test_linear_track_is_exact_at_the_midpoint():
    dom = _at(_stage([{"target": "k", "keys": [{"t": 0, "x": 10, "opacity": 0, "p": 0}, {"t": 4, "x": 60, "opacity": 1, "p": 1}]}]), 2)
    s = _style(dom, "k")
    assert s["transform"] == "translate(320px, 0px)"          # (35-10)% of the 1280px stage
    assert float(s["opacity"]) == pytest.approx(0.5, abs=0.001)
    assert s["--p"] == "0.5000"
    assert "€1.2M" in dom                                     # 2.4 * 0.5, counted by the runtime


@browser
@pytest.mark.parametrize("name", ["expo-out", "standard", "overshoot", "anticipate", "quart-in-out"])
def test_named_ease_matches_an_independent_solver(name):
    dom = _at(_stage([{"target": "k", "keys": [{"t": 0, "opacity": 0}, {"t": 4, "opacity": 1, "ease": name}]}]), 1)
    expected = _ease(wa._MO_EASE[name], 0.25)
    got = float(_style(dom, "k")["opacity"])
    assert got == pytest.approx(max(0, min(1, expected)), abs=0.002)


@browser
def test_hold_ease_jumps_at_the_key_and_beat_keys_land_on_the_grid():
    tracks = [{"target": "cur", "keys": [{"t": 0, "step": 0}, {"t": 2, "step": 3, "ease": "hold"}]}]
    assert _style(_at(_stage(tracks), 1.9), "cur")["--s"] == "0.0000"
    assert _style(_at(_stage(tracks), 2.0), "cur")["--s"] == "3.0000"
    beat = _stage([{"target": "k", "keys": [{"beat": 0, "p": 0}, {"beat": 4, "p": 1}]}], {"bpm": 120})  # 4 beats @120 = 2s
    assert _style(_at(beat, 1.0), "k")["--p"] == "0.5000"


@browser
def test_progress_counter_formats_like_the_server():
    dom = _at(_stage([{"target": "sync", "keys": [{"t": 0, "p": 0}, {"t": 4, "p": 1}]}]), 4)
    assert "1,207 contacts" in dom
    assert wa._mo_fmt(1207, 0, "", " contacts") == "1,207 contacts"
    dom0 = _at(_stage([{"target": "sync", "keys": [{"t": 0, "p": 0}, {"t": 4, "p": 1}]}]), 0)
    assert "0 contacts" in dom0


@browser
def test_camera_transform_and_before_after_hold():
    """Before a property's first key it HOLDS that first value (like CSS animation-fill-mode: backwards), so an
    element can be hidden until its first key; after the last key it holds the last."""
    cam = {"camera": {"keys": [{"t": 1, "zoom": 1, "ry": 0}, {"t": 3, "zoom": 2, "ry": -10, "ease": "linear"}]}}
    def cam_tf(t):
        dom = _at(_stage([], cam), t)
        return re.search(r'class="mt-cam" style="[^"]*transform: ([^;"]*)', dom).group(1)
    assert cam_tf(0) == "translate(640px, 360px) scale(1) rotateX(0deg) rotateY(0deg) rotate(0deg) translate(-640px, -360px)"
    mid = cam_tf(2)
    assert "scale(1.5" in mid and "rotateY(-5" in mid
    assert "scale(2" in cam_tf(4) and "rotateY(-10" in cam_tf(4)


@browser
def test_runtime_exposes_a_seek_api_and_survives_reduced_data():
    dom = _at(_stage([{"target": "k", "keys": [{"t": 0, "x": 10}, {"t": 4, "x": 10}]}, {"target": "missing", "keys": [{"t": 0, "x": 1}]}]), 1)
    assert _style(dom, "k")["transform"] == "translate(0px, 0px)"


@browser
def test_overshoot_curves_never_push_opacity_outside_zero_to_one():
    for name in ("anticipate", "overshoot"):
        for t in (0.3, 1.0, 2.0, 3.0):
            dom = _at(_stage([{"target": "k", "keys": [{"t": 0, "opacity": 0}, {"t": 4, "opacity": 1, "ease": name}]}]), t)
            assert 0 <= float(_style(dom, "k")["opacity"]) <= 1


# ─── schema declarations ─────────────────────────────────────────────────────
# Promoted to stable 2026-10-01 on Curtis's explicit go-ahead (the a2uicatalog.ai landing film is built from them). The demo kit (demo_*)
# and motion_path stay preview: nothing published uses them yet, and a stable atom's field names are a public contract.
PROMOTED = {"motion_timeline", "motion_group", "motion_tokens", "motion_layer", "motion_text", "motion_shape", "motion_counter", "motion_mark", "motion_browser",
            "motion_orbit", "motion_code", "motion_checklist", "motion_pill", "motion_sketch", "motion_leader", "motion_mask"}


def test_every_motion_atom_is_declared_with_the_right_stage():
    import yaml
    atoms = {a["type"]: a for a in yaml.safe_load((ROOT / "atoms" / "schema.yaml").read_text())["blocks"]}
    for name in MOTION_ATOMS:
        assert name in atoms, f"{name} missing from atoms/schema.yaml"
        a = atoms[name]
        want = "stable" if name in PROMOTED else "preview"
        assert a.get("stage", "stable") == want, f"{name} should be {want}"
        assert a.get("fields") and a.get("description") and a.get("compact_description") and a.get("surfaces", {}).get("works_on")


def test_every_documented_field_is_actually_read_by_the_renderer():
    """A field in the schema that no code reads is a lie an agent will act on."""
    import yaml
    src = (ROOT / "apps-script-surface" / "gas-wired-renderer" / "atoms_motion.gs").read_text()
    atoms = {a["type"]: a for a in yaml.safe_load((ROOT / "atoms" / "schema.yaml").read_text())["blocks"]}
    starts = {m.group(1): m.start() for m in re.finditer(r"_RENDERERS\['([a-z0-9_]+)'\] = function", src)}
    order = sorted(starts.values()) + [len(src)]
    # motion_group builds its entrance through _moEnterSpec (reads effect/ease/duration/delay/on from its own block);
    # the timeline reads per-child fields (id/place/layer) and track/camera keys in its helpers.
    shared = {"motion_group": src[src.index("function _moEnterSpec"):src.index("var _MO_VIEW_JS")],
              "motion_timeline": src[src.index("var _MO_ASPECT"):src.index("_RENDERERS['motion_timeline']")] + src[src.index("var _MO_STITCH ="):]}
    missing = []
    for name in MOTION_ATOMS:
        a = starts[name]
        body = src[a:order[order.index(a) + 1]] + shared.get(name, "")
        for field in atoms[name]["fields"]:
            via_helper = (field == "theme" and "_ffTheme(b)" in body) or (field == "accent" and ("_moAcc(b)" in body or "_moAccRgb(b)" in body))
            if not via_helper and not re.search(r"\.%s\b|\['%s'\]|'%s'|\b%s:" % ((field,) * 4), body):
                missing.append(f"{name}.{field}")
    assert not missing, missing


def test_enter_joins_the_public_json_schema_only_on_promotion():
    import gen_atom_json_schemas as g
    preview = [{"type": "motion_timeline", "stage": "preview"}]
    assert not g.motion_is_public(preview, False)
    assert g.motion_is_public(preview, True), "the gated full mirror always carries it"
    assert g.motion_is_public([{"type": "motion_timeline"}], False), "promotion (no stage: preview) switches it on"
    blk = {"type": "x", "fields": {"a": "string (optional)"}}
    assert "enter" not in g.build_atom_schema(blk, False)["properties"]
    assert "enter" in g.build_atom_schema(blk, True)["properties"]


def test_enter_schema_accepts_what_the_renderer_accepts():
    jsonschema = pytest.importorskip("jsonschema")
    import gen_atom_json_schemas as g
    v = jsonschema.Draft7Validator(g.ENTER_SCHEMA)
    for ok in ("rise", {"effect": "pop", "ease": [0.1, 0.2, 0.3, 1], "duration": "slow", "delay": 120, "on": "view"}, {"ease": "expo-out"}):
        assert v.is_valid(ok), ok
    for bad in ("spin", {"effect": "rise", "extra": 1}, {"ease": "bounce"}, {"duration": 99999}, 5):
        assert not v.is_valid(bad), bad
    assert set(g.MOTION_TOKENS) == set(wa._MO_EASE) and g.MOTION_EFFECTS == list(wa._MO_FX)


# ─── the topic-free primitives, in a real browser ───────────────────────────
def _probe(block: dict, t: float, js: str):
    """Render block at time t in headless Chromium, run `js` (an expression over the live DOM), return its JSON value."""
    html = ("<!doctype html><meta charset=utf-8><body style='margin:0'>" + _py(block)
            + "<script>document.documentElement.setAttribute('data-probe', JSON.stringify((function(){" + js + "})()));</script>")
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "p.html"
        f.write_text(html)
        out = subprocess.run([CHROMIUM, "--headless=new", "--no-sandbox", "--disable-gpu", "--window-size=1000,700", "--virtual-time-budget=1500",
                              "--dump-dom", f"file://{f}#t={t}"], capture_output=True, text=True, timeout=90).stdout
    m = re.search(r"data-probe='([^']*)'|data-probe=\"([^\"]*)\"", out)
    assert m, out[:400]
    import html as _h
    return json.loads(_h.unescape(m.group(1) or m.group(2)))


def _scene(children, tracks, **kw):
    blk = {"type": "motion_timeline", "duration": 4, "controls": False, "autoplay": False, "ease": "linear",
           "blocks": [{"type": "motion_layer", "id": "scene", "blocks": children}], "tracks": tracks}
    blk.update(kw)
    return blk


@browser
def test_motion_text_units_reveal_in_turn_with_the_expected_opacity():
    blk = _scene([{"type": "motion_text", "id": "t", "text": "ONE\nTWO", "reveal": "fade", "overlap": 3, "place": {"x": 5, "y": 5, "w": 80}}],
                 [{"target": "t", "keys": [{"t": 0, "p": 0}, {"t": 4, "p": 1}]}])
    # N = 2 lines, overlap 3: unit i = clamp((p*(N+3) - i)/3). At p = 0.5: unit 0 -> 0.8333, unit 1 -> 0.5
    got = _probe(blk, 2, "var u=document.querySelectorAll('[data-mt-id=t] span[aria-hidden] > span');return Array.prototype.map.call(u,function(e){return +getComputedStyle(e).opacity;});")
    assert got == pytest.approx([2.5 / 3, 1.5 / 3], abs=0.01)
    start = _probe(blk, 0, "var u=document.querySelectorAll('[data-mt-id=t] span[aria-hidden] > span');return Array.prototype.map.call(u,function(e){return +getComputedStyle(e).opacity;});")
    end = _probe(blk, 4, "var u=document.querySelectorAll('[data-mt-id=t] span[aria-hidden] > span');return Array.prototype.map.call(u,function(e){return +getComputedStyle(e).opacity;});")
    assert start == [0, 0] and end == [1, 1]


@browser
def test_motion_text_mask_slides_each_line_up_out_of_a_clip():
    blk = _scene([{"type": "motion_text", "id": "t", "text": "ONE\nTWO", "reveal": "mask", "size": 100, "place": {"x": 5, "y": 5, "w": 80}}],
                 [{"target": "t", "keys": [{"t": 0, "p": 0}, {"t": 4, "p": 1}]}])
    js = "var u=document.querySelectorAll('[data-mt-id=t] span[aria-hidden] > span > span');return Array.prototype.map.call(u,function(e){var m=getComputedStyle(e).transform;return m==='none'?0:parseFloat(m.split(',')[5]);});"
    y0, y1 = _probe(blk, 0, js)
    assert y0 > 0 and y1 > 0, "fully hidden below the clip at p = 0"
    assert _probe(blk, 4, js) == [0, 0], "settled at p = 1"


@browser
def test_motion_counter_counts_from_a_start_value():
    blk = _scene([{"type": "motion_counter", "id": "c", "from": 100, "to": 300, "suffix": "k", "label": "Followers", "place": {"x": 5, "y": 5, "w": 40}}],
                 [{"target": "c", "keys": [{"t": 0, "p": 0}, {"t": 4, "p": 1}]}])
    js = "return document.querySelector('[data-mt-num]').textContent;"
    assert _probe(blk, 0, js) == "100k" and _probe(blk, 2, js) == "200k" and _probe(blk, 4, js) == "300k"


@browser
def test_motion_shape_draws_with_progress():
    kids = [{"type": "motion_shape", "id": "bar", "shape": "rect", "place": {"x": 5, "y": 5, "w": 50, "h": 10}},
            {"type": "motion_shape", "id": "ring", "shape": "ring", "thickness": 8, "place": {"x": 5, "y": 30, "w": 20, "h": 36}}]
    blk = _scene(kids, [{"target": "bar", "keys": [{"t": 0, "p": 0}, {"t": 4, "p": 1}]}, {"target": "ring", "keys": [{"t": 0, "p": 0}, {"t": 4, "p": 1}]}])
    bar = "return getComputedStyle(document.querySelector('[data-mt-id=bar] > div')).transform;"
    ring = "return getComputedStyle(document.querySelector('[data-mt-id=ring] > div')).backgroundImage;"
    assert _probe(blk, 2, bar) == "matrix(0.5, 0, 0, 1, 0, 0)"
    assert "180deg" in _probe(blk, 2, ring) and "conic-gradient" in _probe(blk, 2, ring)
    assert "360deg" in _probe(blk, 4, ring)


@browser
def test_layers_move_as_one_and_their_children_stay_addressable():
    blk = _scene([{"type": "motion_text", "id": "inner", "text": "Hi", "reveal": "fade", "place": {"x": 10, "y": 10, "w": 30}}],
                 [{"target": "scene", "keys": [{"t": 0, "opacity": 0, "x": 10}, {"t": 4, "opacity": 1, "x": 0}]},
                  {"target": "inner", "keys": [{"t": 0, "p": 0}, {"t": 4, "p": 1}]}])
    js = "var s=document.querySelector('[data-mt-id=scene]'),i=document.querySelector('[data-mt-id=inner]');return [+s.style.opacity, s.style.transform, i.style.getPropertyValue('--p')];"
    op, tf, p = _probe(blk, 2, js)
    assert op == pytest.approx(0.5, abs=0.01) and tf == "translate(64px, 0px)" and p == "0.5000"
    # a layer with no place fills the stage: its children are positioned against the stage, not against a zero box
    box = _probe(blk, 0, "var e=document.querySelector('[data-mt-id=scene]').getBoundingClientRect(),v=document.querySelector('.mt-vp').getBoundingClientRect();return [Math.round(e.width/v.width*100), Math.round(e.height/v.height*100)];")
    assert box == [100, 100]


def test_motion_sketch_only_ever_emits_paths_from_a_strict_grammar():
    """Strokes are path data, not markup: an attribute break-out, a tag, a URL or a control character drops the stroke."""
    hostile = ['M 0 0" onload="alert(1)', "<script>alert(1)</script>", "url(javascript:alert(1))", "M 0 0 L 1 1; background:red", "M 0 0 L 1 1 '", "x" * 800, "M 0 0   L 1 1"]
    html = _py({"type": "motion_sketch", "strokes": [{"d": d} for d in hostile] + [{"d": "M 0 0 L 10 10 Z", "color": "red", "fill": "url(x)", "width": 999}]})
    assert html.count("pathLength") == 1, "only the one valid stroke is drawn"
    assert "onload" not in html and "<script" not in html and "javascript" not in html and "background:red" not in html
    # the colour fell back (not a #rrggbb), the width clamped to 24, and no fill layer was made
    assert "stroke:var(--mt-ink,#f1f5f9)" in html and "stroke-width:24" in html and "url(x)" not in html
    # the drawing is a pure function of p: stroke 0 of 1 is complete at p = 1 and undrawn at p = 0
    assert "stroke-dashoffset:calc(1 - var(--u))" in html and "clamp(0,calc(var(--p,1)*1 - 0),1)" in html


# ─── the second reel's atoms (leader lines, route paths, masks, wipes, text bars) ───────────────────────────────────────
def test_leader_and_path_only_emit_numbers_and_validated_paths():
    hostile = _py({"type": "motion_leader", "from": ["<x>", 1e300], "to": [None, "\" onload=\"alert(1)"], "label": "<img src=x onerror=alert(1)>", "color": "red;x", "label_color": "url(javascript:alert(1))", "curve": "9;}", "w": "\"><b>"})
    assert "<img" not in hostile and "onload" not in hostile and "javascript" not in hostile and "red;x" not in hostile
    assert "&lt;img" in hostile, "the label is escaped text"
    assert re.findall(r' d="([^"]*)"', hostile) and all(re.fullmatch(r"[MLQZ0-9 .\-]+", d) for d in re.findall(r' d="([^"]*)"', hostile))
    path = _py({"type": "motion_path", "d": "M 0 0\" onload=\"alert(1)", "nodes": [{"x": "<b>", "y": "\"", "label": "<script>alert(1)</script>"}]})
    assert "onload" not in path and "<script" not in path and "M 20 200 C 120 40 280 360 380 200" in path, "a bad path falls back to the default"
    assert "&lt;script&gt;" in path


def test_mask_children_stay_ids_and_the_shape_never_comes_from_the_payload():
    html = _py({"type": "motion_mask", "shape": "x;}</style><script>alert(1)</script>", "blocks": [{"type": "motion_pill", "text": "x", "id": "kid"}]})
    assert "<script" not in html and html.count("clip-path:polygon(") == 2, "an unknown shape falls back to the blob (clip-path and its -webkit- twin)"
    assert 'data-mt-id="kid"' in html
    assert html.count("calc(50% + ") == 80, "20 vertices, x and y each, written for clip-path and its -webkit- twin"


def test_text_bar_and_extrude_take_only_validated_colours_and_depth():
    html = _py({"type": "motion_text", "text": "HI", "reveal": "bar", "bar": "red;}</style>", "extrude": 9999, "extrude_color": "url(javascript:alert(1))"})
    assert "red;}" not in html and "javascript" not in html and "<style" not in html
    assert html.count("px 0 #0b0b14") == 30, "depth clamps to 30 and the colour falls back"


@browser
def test_wipe_reveals_the_new_scene_left_to_right_and_keeps_the_old_one_until_covered():
    blk = dict(STITCHED, stitch="wipe", overlap=2.0, bpm=0, duration=9,
               scenes=[{"layer": "s1", "t": 0}, {"layer": "s2", "t": 3}], controls=False, autoplay=False)
    clip = "return getComputedStyle(document.querySelector('[data-mt-id=%s]')).clipPath;"
    opac = "return +document.querySelector('[data-mt-id=%s]').style.opacity;"
    assert _probe(blk, 3, clip % "s2") != "none", "at the start of the wipe the new scene is still clipped"
    mid = _probe(blk, 4, clip % "s2")
    assert mid.startswith("inset(") and mid != "inset(0px)", mid
    assert _probe(blk, 6, clip % "s2") in ("none", "inset(0px)"), "fully revealed"
    assert _probe(blk, 4, opac % "s1") == 1, "the old scene is still fully visible mid-wipe"
    assert _probe(blk, 5.5, opac % "s1") == 0, "and gone once the new one has covered it"


@browser
def test_whip_blurs_and_slides_both_scenes():
    blk = dict(STITCHED, stitch="whip", overlap=2.0, bpm=0, duration=9, scenes=[{"layer": "s1", "t": 0}, {"layer": "s2", "t": 3}], controls=False, autoplay=False)
    f = "var e=document.querySelector('[data-mt-id=%s]');return [e.style.filter, e.style.transform];"
    out_f, out_t = _probe(blk, 4, f % "s1")
    in_f, in_t = _probe(blk, 4, f % "s2")
    assert out_f.startswith("blur(") and in_f.startswith("blur(") and "translate(" in out_t and "translate(" in in_t


@browser
def test_mask_grows_with_p_and_is_gone_at_zero():
    kid = {"type": "motion_pill", "text": "Hello", "id": "kid"}
    blk = _scene([{"type": "motion_mask", "id": "m", "shape": "circle", "blocks": [kid], "place": {"x": 10, "y": 10, "w": 60, "h": 60}}],
                 [{"target": "m", "keys": [{"t": 0, "p": 0}, {"t": 4, "p": 1}]}])
    js = "var e=document.querySelector('[data-mt-id=m] > div');var r=e.getBoundingClientRect();return [getComputedStyle(e).clipPath.slice(0,8), e.style.getPropertyValue('--m')];"
    assert _probe(blk, 0, js) == ["polygon(", "clamp(0,var(--p,1),1)"]
    # the polygon's vertices scale with --m: at p = 0.5 the first vertex sits half way out from the centre
    first = "var e=document.querySelector('[data-mt-id=m] > div');return getComputedStyle(e).clipPath.split(',')[0];"
    zero, half, full = (_probe(blk, t, first) for t in (0, 2, 4))
    assert zero != half != full and zero != full


@browser
def test_path_marker_rides_the_path_with_p():
    blk = _scene([{"type": "motion_path", "id": "r", "d": "M 0 0 L 400 0", "w": 400, "h": 100, "nodes": [{"x": 200, "y": 0, "at": 0.5, "label": "Mid"}], "place": {"x": 0, "y": 0, "w": 100}}],
                 [{"target": "r", "keys": [{"t": 0, "p": 0}, {"t": 4, "p": 1}]}])
    js = "var s=document.querySelectorAll('[data-mt-id=r] svg path');var m=s[2];var g=document.querySelector('[data-mt-id=r] svg g');return [getComputedStyle(m).strokeDashoffset, getComputedStyle(s[1]).strokeDashoffset, +getComputedStyle(g).getPropertyValue('--k')||g.style.getPropertyValue('--k')];"
    a, b_, c = _probe(blk, 2, js)
    num = lambda v: float(re.search(r"-?[0-9.]+", str(v)).group(0))
    assert num(b_) == pytest.approx(0.5, abs=0.02), "the drawn line is half drawn at p = 0.5"
    assert abs(num(a)) == pytest.approx(0.5, abs=0.02), "and the marker sits at the same place"
