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
MOTION_ATOMS = ["motion_group", "motion_tokens", "motion_timeline"] + DEMO_ATOMS

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

PAYLOADS = {
    "motion_group": [{}, {"effect": "pop", "stagger": 40, "blocks": [{"type": "demo_orb"}, {"type": "demo_cursor", "id": "c"}]},
                     {"effect": "<bad>", "ease": "zzz", "duration": -5, "delay": 99999999, "on": "view", "blocks": [{"type": "demo_orb"}]}],
    "motion_tokens": [{}, {"show": "ease", "theme": "light", "accent": "#F97316"}, {"show": "duration"}],
    "motion_timeline": [{}, TIMELINE,
                        dict(TIMELINE, aspect="9:16", loop=False, autoplay=False, controls=False, backdrop="grid", theme="light", poster=3, accent="#F97316", background="#101820"),
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
    # "9;}" is read like parseInt("9;}") = 9: a number, never CSS. The bad effect/ease fall back to the defaults.
    assert re.search(r"animation:moe-rise 9ms cubic-bezier\(0\.16,1,0\.3,1\) 0ms both", html)


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
def test_every_motion_atom_is_declared_as_a_preview_atom():
    import yaml
    atoms = {a["type"]: a for a in yaml.safe_load((ROOT / "atoms" / "schema.yaml").read_text())["blocks"]}
    for name in MOTION_ATOMS:
        assert name in atoms, f"{name} missing from atoms/schema.yaml"
        a = atoms[name]
        assert a.get("stage") == "preview", f"{name} must stay preview until Curtis opts in"
        assert a.get("fields") and a.get("description") and a.get("compact_description") and a.get("surfaces", {}).get("works_on")


def test_every_documented_field_is_actually_read_by_the_renderer():
    """A field in the schema that no code reads is a lie an agent will act on."""
    import yaml
    src = (ROOT / "apps-script-surface" / "gas-wired-renderer" / "atoms_motion.gs").read_text()
    atoms = {a["type"]: a for a in yaml.safe_load((ROOT / "atoms" / "schema.yaml").read_text())["blocks"]}
    starts = {m.group(1): m.start() for m in re.finditer(r"_RENDERERS\['([a-z_]+)'\] = function", src)}
    order = sorted(starts.values()) + [len(src)]
    # motion_group builds its entrance through _moEnterSpec (reads effect/ease/duration/delay/on from its own block);
    # the timeline reads per-child fields (id/place/layer) and track/camera keys in its helpers.
    shared = {"motion_group": src[src.index("function _moEnterSpec"):src.index("var _MO_VIEW_JS")],
              "motion_timeline": src[src.index("var _MO_ASPECT"):src.index("_RENDERERS['motion_timeline']")]}
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
