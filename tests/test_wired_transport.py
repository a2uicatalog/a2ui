"""Wired action transport (wired-transport-v0.1, a2ui-private) — the wired
dialect on the MCP Apps view. Runs the REAL engine + REAL extracted render
loop headlessly: transport selection (gas → host → none), verb mapping onto
store_* tools, the declared-inert honesty rule, and the americano acceptance
loop (save round via host bridge → query → standings fold)."""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import gen_mcp_apps_bundle as gen  # noqa: E402

ENGINE = re.sub(r"^\s*<script>|</script>\s*$", "",
                (ROOT / "apps-script-surface" / "gas-wired-renderer" /
                 "A2UIState.html").read_text().strip(), flags=re.S)

BOOT_STUB = """
global.window = global;
var L = {};
global.document = {
  addEventListener: function (ev, fn) { L[ev] = fn; },
  getElementById: function () { return null; },
  querySelectorAll: function () { return []; },
  querySelector: function () { return null; },
};
"""

SCHEMA = {
    "type": "a2ui_wired_surface",
    "app": {"id": "americano-night"},
    "state_primitives": [
        {"id": "r1m1a", "primitive": "ValueStore", "props": {"initialValue": "21"}},
    ],
    "actions": [
        {"id": "save_round_1", "type": "gas:sheet_append",
         "props": {"sheet": "A2UI_Americano_8_Scores",
                   "collect": {"round": "1", "m1_score_a": "#r1m1a.value"}}},
        {"id": "load_scores", "type": "gas:sheet_query",
         "props": {"sheet": "A2UI_Americano_8_Scores"}},
        {"id": "send_mail", "type": "gas:email_send", "props": {}},
    ],
    "layout": [],
}


def _node(js):
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "d.js"
        d.write_text(js)
        p = subprocess.run(["node", str(d)], capture_output=True, text=True, timeout=90)
        assert p.returncode == 0, p.stderr[-1200:]
        return json.loads(p.stdout.strip().split("\n")[-1])


def test_none_transport_declared_inert():
    """No google, no bridge: actions resolve isError with the declared
    message — never a dead button, never a silent success."""
    r = _node(BOOT_STUB + ENGINE + f"""
window._a2uiBootWiredSurface({json.dumps(SCHEMA)});
var eng = window._a2uiEngine;
eng.nodes.save_round_1._run();
console.log(JSON.stringify({{err: eng.nodes.save_round_1.isError,
  msg: eng.nodes.save_round_1.error}}));
""")
    assert r["err"] is True
    assert "cannot reach" in r["msg"] and "inert" in r["msg"]


def test_host_transport_maps_verbs_to_store_tools():
    """Bridge present: sheet verbs map to store_* with the per-app store
    name; collect resolves from live state; envelope contract untouched."""
    r = _node(BOOT_STUB + ENGINE + f"""
var calls = [];
window._A2UI_HOST_BRIDGE = {{ callTool: function (name, args) {{
  calls.push({{ name: name, args: args }});
  var sc = name === 'store_read'
    ? {{ ok: true, data: [{{ round: 1, m1_score_a: 21 }}], total: 1 }}
    : {{ ok: true, data: {{ inserted_rows: 1 }} }};
  return Promise.resolve({{ structuredContent: sc }});
}} }};
window._a2uiBootWiredSurface({json.dumps(SCHEMA)});
var eng = window._a2uiEngine;
eng.nodes.save_round_1._run();
eng.nodes.load_scores._run();
setTimeout(function () {{
  console.log(JSON.stringify({{ calls: calls,
    saveOk: eng.nodes.save_round_1.isSuccess,
    rows: eng.nodes.load_scores.result }}));
}}, 20);
""")
    assert r["calls"][0]["name"] == "store_append"
    assert r["calls"][0]["args"]["store"] == "wired:americano-night:A2UI_Americano_8_Scores"
    assert r["calls"][0]["args"]["record"] == {"round": "1", "m1_score_a": "21"}
    assert r["calls"][1]["name"] == "store_read"
    assert r["saveOk"] is True
    assert r["rows"] == [{"round": 1, "m1_score_a": 21}]


def test_host_transport_session_isolates_store():
    """&t= token (injected by the host as app.session) namespaces the store —
    one link, one tournament; no token = the app's shared default."""
    schema = dict(SCHEMA, app={"id": "americano-night", "session": "t-abc123"})
    r = _node(BOOT_STUB + ENGINE + f"""
var calls = [];
window._A2UI_HOST_BRIDGE = {{ callTool: function (name, args) {{
  calls.push(args.store);
  return Promise.resolve({{ structuredContent: {{ ok: true, data: [] }} }});
}} }};
window._a2uiBootWiredSurface({json.dumps(schema)});
window._a2uiEngine.nodes.save_round_1._run();
setTimeout(function () {{ console.log(JSON.stringify(calls)); }}, 20);
""")
    assert r == ["wired:americano-night:t-abc123:A2UI_Americano_8_Scores"]


def test_play_host_injects_session_token():
    import generate_atom_pages as gap3
    js = gap3.MCP_APPS_HOST_JS
    seg = js[js.index("function normalize"):js.index("function send")]
    assert "[#&]t=" in seg and "session" in seg


def test_americano_payload_rehydrates_names():
    payload = json.loads(Path("/home/curtis/a2ui-private/tests/americano_wired.json").read_text())
    binders = [s for s in payload["wired_templates"]["state"]
               if isinstance(s, dict) and s.get("id") == "binder_players"]
    assert len(binders) == 1
    b = binders[0]
    assert b["wire"]["rows"] == "#load_players.result"
    assert {"match": {}, "take": "p1", "into": "p1"} in b["props"]["bind"]


def test_wire_delivery_is_raw_not_html_escaped():
    """The americano '&amp;' incident: values delivered to the DOM bridge must
    arrive RAW — text sinks write via textContent, so escaping at delivery
    displays literal '&amp;'. innerHTML sinks sanitize per-cell themselves."""
    schema = {
        "type": "a2ui_wired_surface",
        "app": {"id": "amp-check"},
        "state_primitives": [
            {"id": "lbl", "primitive": "StringTemplate",
             "props": {"template": "{a} & {b}  vs  {c}",
                       "inputs": {"a": "#s.value", "b": "#s.value", "c": "#s.value"},
                       "fallbacks": {"a": "P1", "b": "P2", "c": "P3"}}},
            {"id": "s", "primitive": "ValueStore", "props": {"initialValue": ""}},
        ],
        "actions": [],
        "layout": [{"atom": "body", "id": "match-label",
                    "props": {"text": "Court 1"},
                    "wire": {"text": "#lbl.value"}}],
    }
    r = _node(BOOT_STUB + ENGINE + f"""
var writes = [];
window._a2uiBootWiredSurface({json.dumps(schema)});
window._a2uiEngine.compileWires({json.dumps(schema["layout"][0])},
  {{ setProp: function (id, prop, val) {{ writes.push(val); }} }});
window._a2uiEngine.trigger('s', 'setValue', 'Ann & Bob <3');
console.log(JSON.stringify(writes));
""")
    assert any("Ann & Bob <3" in str(w) for w in r), r
    assert not any("&amp;" in str(w) or "&lt;" in str(w) for w in r), r


def test_host_transport_refuses_unmapped_verbs():
    r = _node(BOOT_STUB + ENGINE + f"""
window._A2UI_HOST_BRIDGE = {{ callTool: function () {{
  throw new Error('must not be called for unmapped verbs'); }} }};
window._a2uiBootWiredSurface({json.dumps(SCHEMA)});
var eng = window._a2uiEngine;
eng.nodes.send_mail._run();
console.log(JSON.stringify({{ err: eng.nodes.send_mail.isError,
  msg: eng.nodes.send_mail.error }}));
""")
    assert r["err"] is True and "no host transport" in r["msg"]


@pytest.fixture(scope="module")
def core_js():
    bundle = gen.build_bundle()
    blocks = re.findall(r"<script>\n(.*?)\n</script>", bundle, re.S)
    return [b for b in blocks if "a2ui-core" in b[:300]][0]


def test_bundle_carries_wired_path(core_js):
    bundle = gen.build_bundle()
    assert "_a2uiRenderWiredLayout" in core_js          # extracted loop ships in core
    assert "a2ui_wired_surface" in bundle               # paint() branches on it
    assert "_A2UI_HOST_BRIDGE" in bundle                # view->host bridge
    assert "'tools/call'" in bundle or '"tools/call"' in bundle


def test_americano_renders_through_extracted_loop(core_js):
    """Acceptance: the real americano payload's expanded layout renders via
    the SAME loop GAS uses, inside the bundle core, headlessly."""
    payload = json.loads(Path("/home/curtis/a2ui-private/tests/americano_wired.json").read_text())
    with tempfile.TemporaryDirectory() as td:
        pj = Path(td) / "p.json"
        pj.write_text(json.dumps(payload))
        d = Path(td) / "d.js"
        d.write_text("global.window = global;\n" + core_js + f"""
var payload = JSON.parse(require('fs').readFileSync({json.dumps(str(pj))}, 'utf8'));
var expanded = _expandWiredSurface(payload, '8', 'https://x/exec?p=abc');
var html = _a2uiRenderWiredLayout(expanded);
console.log(JSON.stringify({{ len: html.length,
  standings: html.indexOf('data-a2ui-standings') > -1,
  steps: (html.match(/data-a2ui-step=/g) || []).length,
  numeric: html.indexOf('type="number"') > -1 }}));
""")
        p = subprocess.run(["node", str(d)], capture_output=True, text=True, timeout=90)
        assert p.returncode == 0, p.stderr[-1000:]
        r = json.loads(p.stdout)
    assert r["standings"] and r["numeric"]
    assert r["steps"] > 20          # per-round stepped elements materialized
    assert r["len"] > 30000


def test_play_host_passes_envelopes_through():
    """The black-page incident: /play's normalize() must NOT wrap wired
    surfaces or v1.0 envelopes as a single atom block."""
    import generate_atom_pages as gap2
    js = gap2.MCP_APPS_HOST_JS
    assert "a2ui_wired_surface" in js.split("function normalize")[1].split("}")[3] or \
           "a2ui_wired_surface" in js[js.index("function normalize"):js.index("function send")]
    assert "createSurface" in js[js.index("function normalize"):js.index("function send")]
