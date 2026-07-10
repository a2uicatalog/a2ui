"""Server-side wired template expansion (atoms_wired_expand.gs) + the two new
state primitives (StringTemplate, RowBinder). All executed as the REAL code:
expansion runs the .gs functions in Node; primitives run the actual engine
(A2UIState.html) headlessly."""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
RENDERER = ROOT / "apps-script-surface" / "gas-wired-renderer"


def _node(js):
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "d.js"
        d.write_text(js)
        p = subprocess.run(["node", str(d)], capture_output=True, text=True, timeout=60)
        assert p.returncode == 0, p.stderr[-1200:]
        return json.loads(p.stdout)


@pytest.fixture(scope="module")
def expand_js():
    return (RENDERER / "atoms_wired_expand.gs").read_text()


@pytest.fixture(scope="module")
def engine_js():
    src = (RENDERER / "A2UIState.html").read_text()
    return re.sub(r"^\s*<script>|</script>\s*$", "", src.strip(), flags=re.S)


PAYLOAD = {
    "type": "a2ui_wired_surface",
    "title": "T — {{variant}} players",
    "default_variant": "8",
    "variants": {
        "8":  {"rounds": [{"r": 1, "m1a1": 1, "m2a1": 3}, {"r": 2, "m1a1": 1, "m2a1": 4}],
               "rounds_n": 2},
        "12": {"rounds": [{"r": 1, "m1a1": 1, "m2a1": 3, "m3a1": 9}], "rounds_n": 1},
    },
    "state_primitives": [],
    "actions": [],
    "layout": [{"atom": "heading", "props": {"text": "Chooser: {{self_url}}&n=12"}}],
    "wired_templates": {
        "state": [
            {"id": "nav", "primitive": "StepNavigator", "props": {"totalSteps": "{{data.rounds_n}}"}},
            {"repeat": "rounds", "template": [
                {"id": "r{{i}}s", "primitive": "ValueStore", "props": {"initialValue": ""}}]},
        ],
        "actions": [
            {"repeat": "rounds", "template": [
                {"id": "save_{{i}}", "type": "gas:sheet_append",
                 "props": {"sheet": "S_{{variant}}", "collect": {"round": "{{i}}", "a": "#r{{i}}s.value"}}}]},
        ],
        "layout": [
            {"repeat": "rounds", "template": [
                {"atom": "subheading", "step": "{{i0}}", "props": {"text": "Round {{i}} — m1 opens {{item.m1a1}}"}},
                {"atom": "body", "step": "{{i0}}", "if": "item.m3a1",
                 "props": {"text": "Court 3 exists: {{item.m3a1}}"}}]},
        ],
    },
}


def test_expansion_repeat_substitute_and_coerce(expand_js):
    r = _node(expand_js + f"""
var out = _expandWiredSurface({json.dumps(PAYLOAD)}, '8', 'https://x/exec?p=abc');
console.log(JSON.stringify(out));
""")
    assert r["title"] == "T — 8 players"
    assert [s["id"] for s in r["state_primitives"]] == ["nav", "r1s", "r2s"]
    assert r["state_primitives"][0]["props"]["totalSteps"] == "2"
    assert r["actions"][1]["props"]["sheet"] == "S_8"
    assert r["actions"][1]["props"]["collect"]["a"] == "#r2s.value"
    steps = [el for el in r["layout"] if el.get("atom") == "subheading"]
    assert steps[0]["step"] == 0 and steps[1]["step"] == 1   # coerced to int
    assert not any("Court 3" in json.dumps(el) for el in r["layout"])  # if-filtered out on 8
    assert "https://x/exec?p=abc&n=12" in r["layout"][0]["props"]["text"]
    assert "variants" not in r and "wired_templates" not in r


def test_expansion_variant_select_and_fallback(expand_js):
    r = _node(expand_js + f"""
var p = {json.dumps(PAYLOAD)};
console.log(JSON.stringify({{
  twelve: _expandWiredSurface(p, '12', ''),
  bogus:  _expandWiredSurface(p, '99', ''),
}}));
""")
    twelve = r["twelve"]
    assert twelve["title"] == "T — 12 players"
    assert any("Court 3 exists: 9" in json.dumps(el) for el in twelve["layout"])  # if passes
    assert r["bogus"]["title"] == "T — 8 players"   # unknown variant -> default, never blank


ENGINE_BOOT_STUB = """
global.window = global;
var listeners = {};
global.document = {
  addEventListener: function(ev, fn) { listeners[ev] = fn; },
  getElementById: function() { return null; },
  querySelectorAll: function() { return []; },
  querySelector: function() { return null; },
};
"""


def test_string_template_interpolates_with_fallbacks(engine_js):
    schema = {
        "type": "a2ui_wired_surface",
        "state_primitives": [
            {"id": "p1", "primitive": "ValueStore", "props": {"initialValue": ""}},
            {"id": "p2", "primitive": "ValueStore", "props": {"initialValue": ""}},
            {"id": "lbl", "primitive": "StringTemplate",
             "props": {"template": "Court 1 — {a} & {b}",
                       "inputs": {"a": "#p1.value", "b": "#p2.value"},
                       "fallbacks": {"a": "P1", "b": "P8"}}},
        ],
        "actions": [], "layout": [],
    }
    r = _node(ENGINE_BOOT_STUB + engine_js + f"""
window.__A2UI_SCHEMA__ = {json.dumps(schema)};
listeners['DOMContentLoaded']();
var eng = window._a2uiEngine;
var before = eng.nodes.lbl.value;
eng.trigger('p1', 'setValue', 'Ana');
console.log(JSON.stringify({{before: before, after: eng.nodes.lbl.value}}));
""")
    assert r["before"] == "Court 1 — P1 & P8"     # fallbacks on boot
    assert r["after"] == "Court 1 — Ana & P8"     # live substitution


def test_row_binder_rehydrates_value_stores(engine_js):
    schema = {
        "type": "a2ui_wired_surface",
        "state_primitives": [
            {"id": "r1s", "primitive": "ValueStore", "props": {"initialValue": ""}},
            {"id": "binder", "primitive": "RowBinder",
             "props": {"bind": [{"match": {"round": "1"}, "take": "m1_score_a", "into": "r1s"}]}},
        ],
        "actions": [], "layout": [],
    }
    rows = [{"round": 1, "m1_score_a": 5},
            {"round": 1, "m1_score_a": 21},     # later save supersedes
            {"round": 2, "m1_score_a": 9}]
    r = _node(ENGINE_BOOT_STUB + engine_js + f"""
window.__A2UI_SCHEMA__ = {json.dumps(schema)};
listeners['DOMContentLoaded']();
var eng = window._a2uiEngine;
eng.nodes.binder._apply({json.dumps(rows)});
console.log(JSON.stringify({{v: eng.nodes.r1s.value, n: eng.nodes.binder.count}}));
""")
    assert r["v"] == 21 and r["n"] == 3
