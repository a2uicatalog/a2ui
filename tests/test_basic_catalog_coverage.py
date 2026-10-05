"""Every A2UI v1.0 Basic Catalog component is drawable on every surface we ship.

Written 2026-10-05 after finding the web renderer drew 12 of the 18 and the Android library 7:
both had been scoped to what OUR emitter sends (form atoms travel as extension components), so
a plain-spec agent's TextField, CheckBox, ChoicePicker, Slider, DateTimeInput and List drew
nothing, and Icon drew an empty span. Coverage is checked against the vendored spec catalog,
never against our own output, so the gap can't reopen silently.
"""
import json
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

SPEC = json.loads((ROOT / "tests/fixtures/a2ui_v1_0_spec/catalogs/basic/catalog.json").read_text())
SPEC_COMPONENTS = sorted(SPEC["components"])
GAS = ROOT / "apps-script-surface/gas-wired-renderer"
ANDROID = ROOT / "android/a2ui-atoms/src/main/java/ai/a2uicatalog/android"


def test_spec_catalog_is_the_18_we_expect():
    assert len(SPEC_COMPONENTS) == 18


def test_every_spec_component_has_a_web_renderer():
    src = "\n".join(p.read_text() for p in GAS.glob("*.gs"))
    missing = [c for c in SPEC_COMPONENTS if f"_RENDERERS['{c}'] = function" not in src]
    assert not missing, f"web renderer cannot draw Basic Catalog components: {missing}"


def test_every_spec_component_is_drawn_on_android():
    src = "\n".join(p.read_text() for p in ANDROID.glob("*.kt"))
    impls = dict(re.findall(r"object (\w+) : A2uiBasicCatalogV1\.(\w+)\b", src))
    registered = re.search(r"val defaultBasicComponents[^=]*=\s*listOf\((.*?)\)", src, re.S).group(1)
    drawn = {impls[o] for o in re.findall(r"\w+", registered) if o in impls}
    missing = [c for c in SPEC_COMPONENTS if c not in drawn]
    assert not missing, f"Android library does not draw Basic Catalog components: {missing}"


def test_icon_table_covers_the_spec_enum_and_is_generated():
    icon = SPEC["components"]["Icon"]
    props = icon["allOf"][1]["properties"] if "allOf" in icon else icon["properties"]
    names = next(o["enum"] for o in props["name"]["oneOf"] if "enum" in o)
    table = json.loads((ROOT / "atoms/basic-catalog-icons.json").read_text())["icons"]
    assert sorted(names) == sorted(table), "icon table and spec Icon enum differ"
    assert all(v["d"][:1] in "Mm" for v in table.values())
    r = subprocess.run([sys.executable, str(ROOT / "scripts/gen_basic_icons.py"), "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout


@pytest.fixture(scope="module")
def core_js():
    bundle = gen.build_bundle()
    blocks = re.findall(r"<script>\n(.*?)\n</script>", bundle, re.S)
    return [b for b in blocks if "a2ui-core" in b[:300]][0]


FORM = {
    "surfaceId": "booking",
    "dataModel": {"form": {"name": "Ada", "agree": False, "size": ["m"], "guests": 2, "day": ""}},
    "components": [
        {"id": "root", "component": "Column", "children": ["name", "pw", "agree", "size", "guests", "day", "ic", "go"]},
        {"id": "name", "component": "TextField", "label": "Name", "value": {"path": "/form/name"}},
        {"id": "pw", "component": "TextField", "label": "PIN", "variant": "obscured", "value": {"path": "/form/pin"}},
        {"id": "agree", "component": "CheckBox", "label": "I agree", "value": {"path": "/form/agree"}},
        {"id": "size", "component": "ChoicePicker", "label": "Size", "variant": "mutuallyExclusive",
         "options": [{"label": "Small", "value": "s"}, {"label": "Medium", "value": "m"}], "value": {"path": "/form/size"}},
        {"id": "guests", "component": "Slider", "label": "Guests", "min": 1, "max": 8, "value": {"path": "/form/guests"}},
        {"id": "day", "component": "DateTimeInput", "label": "Day", "enableDate": True, "value": {"path": "/form/day"}},
        {"id": "ic", "component": "Icon", "name": "calendarToday"},
        {"id": "go", "component": "Button", "variant": "primary", "child": "go-t",
         "action": {"event": {"name": "book", "context": {"who": {"path": "/form/name"}, "agree": {"path": "/form/agree"},
                                                            "size": {"path": "/form/size"}, "guests": {"path": "/form/guests"},
                                                            "day": {"path": "/form/day"}, "source": "test"}}}},
        {"id": "go-t", "component": "Text", "text": "Book"},
    ],
}


def _render(core_js, surface):
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "d.js"
        d.write_text("global.window = global;\n" + core_js +
                     f"\nvar out = _rehydrateV1Surface({json.dumps(surface)});\nconsole.log(JSON.stringify(renderAtoms(out.blocks, {{}})));")
        p = subprocess.run(["node", str(d)], capture_output=True, text=True, timeout=60)
        assert p.returncode == 0, p.stderr[-1500:]
        return json.loads(p.stdout.strip().split("\n")[-1])


def test_inputs_render_bound_with_one_runtime(core_js):
    html = _render(core_js, FORM)
    for ptr in ("/form/name", "/form/pin", "/form/agree", "/form/size", "/form/guests", "/form/day"):
        assert f'data-a2ui-bind="{ptr}"' in html, ptr
    assert 'type="password"' in html and 'type="range"' in html and 'type="date"' in html
    assert 'value="Ada"' in html and 'value="m" data-a2ui-kind="choice" checked' in html
    assert html.count("_A2UI_V1_RUNTIME") == 0 and html.count('id="a2rt-') == 1, "exactly one runtime per surface"
    assert "data-a2ui-action=" in html and '<path d="M' in html


def test_display_only_surface_gets_no_runtime(core_js):
    html = _render(core_js, {"surfaceId": "s", "components": [
        {"id": "root", "component": "Column", "children": ["t", "b"]}, {"id": "t", "component": "Text", "text": "hi"},
        {"id": "b", "component": "Button", "child": "bt", "action": {"event": {"name": "openUrl", "context": {"url": "https://a2uicatalog.ai/"}}}},
        {"id": "bt", "component": "Text", "text": "Open"}]})
    assert 'id="a2rt-' not in html and 'href="https://a2uicatalog.ai/"' in html


def test_hostile_values_stay_escaped(core_js):
    evil = '"><script>alert(1)</script>'
    html = _render(core_js, {"surfaceId": evil, "dataModel": {"x": evil}, "components": [
        {"id": "root", "component": "Column", "children": ["f", "b"]},
        {"id": "f", "component": "TextField", "label": evil, "placeholder": evil, "value": {"path": "/x"}},
        {"id": "b", "component": "Button", "child": "bt", "action": {"event": {"name": evil, "context": {"v": {"path": "/x"}}}}},
        {"id": "bt", "component": "Text", "text": "Go"}]})
    assert "<script>alert(1)" not in html
    assert html.count("<script>") == 1        # the runtime itself, nothing injected


CHROMIUM = shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome")


@pytest.mark.skipif(not CHROMIUM, reason="no Chromium for the in-browser runtime test")
def test_runtime_sends_the_spec_action_with_live_values(core_js):
    html = _render(core_js, FORM)
    driver = """<script>
window.addEventListener('load', function () {
  var got = null;
  document.addEventListener('a2ui:action', function (e) { got = e.detail; });
  function set(sel, v) { var el = document.querySelector(sel); el.value = v; el.dispatchEvent(new Event('input', {bubbles: true})); }
  set('[data-a2ui-bind="/form/name"]', 'Grace');
  set('[data-a2ui-bind="/form/guests"]', '5');
  set('[data-a2ui-bind="/form/day"]', '2026-10-20');
  var cb = document.querySelector('[data-a2ui-bind="/form/agree"]'); cb.checked = true; cb.dispatchEvent(new Event('change', {bubbles: true}));
  var s = document.querySelector('input[value="s"]'); s.checked = true; s.dispatchEvent(new Event('change', {bubbles: true}));
  document.querySelector('[data-a2ui-action]').click();
  var pre = document.createElement('pre'); pre.id = 'out'; pre.textContent = JSON.stringify(got); document.body.appendChild(pre);
});
</script>"""
    with tempfile.TemporaryDirectory() as td:
        page = Path(td) / "p.html"
        page.write_text("<!doctype html><html><body><div id='surface'>" + html + "</div>" + driver + "</body></html>")
        p = subprocess.run([CHROMIUM, "--headless=new", "--no-sandbox", "--disable-gpu", "--virtual-time-budget=3000",
                            "--dump-dom", page.as_uri()], capture_output=True, text=True, timeout=90)
    m = re.search(r'<pre id="out">(.*?)</pre>', p.stdout, re.S)
    assert m, p.stdout[-800:]
    msg = json.loads(m.group(1).replace("&quot;", '"').replace("&amp;", "&"))
    assert msg["version"] == "v1.0"
    a = msg["action"]
    assert a["name"] == "book" and a["surfaceId"] == "booking" and a["sourceComponentId"] == "go" and a["timestamp"]
    assert a["context"] == {"who": "Grace", "agree": True, "size": ["s"], "guests": 5, "day": "2026-10-20", "source": "test"}


# ── emitter: a basic-only renderer gets real inputs, not form atoms flattened to Text ─────────
from renderers.a2ui_v1 import emit_messages, emit_surface  # noqa: E402
from renderers.a2ui_capabilities import BASIC_CATALOG_IDS, parse_client_capabilities  # noqa: E402

FORM_PAYLOAD = {"title": "Book a visit", "blocks": [
    {"type": "form", "title": "Your visit", "submit_label": "Book", "fields": [
        {"label": "Name", "name": "name", "type": "text"},
        {"label": "PIN", "name": "pin", "type": "password"},
        {"label": "Guests", "name": "guests", "type": "slider"},
        {"label": "Room", "name": "room", "type": "select", "options": [{"value": "a", "label": "Annex"}, {"value": "m", "label": "Main"}]},
        {"label": "Day", "name": "day", "type": "date"},
        {"label": "News", "name": "news", "type": "checkbox"}]},
    {"type": "toggle_switch", "label": "Remember me", "name": "remember", "is_checked": True},
    {"type": "stat_card", "label": "Open slots", "value": "4"}]}


def _caps(version):
    return parse_client_capabilities({"a2uiClientCapabilities": {version: {"supportedCatalogIds": [BASIC_CATALOG_IDS[version]]}}})


def test_basic_only_client_gets_real_inputs():
    cs = emit_surface(FORM_PAYLOAD, capabilities=_caps("v1.0"))["createSurface"]
    by = {c["id"]: c for c in cs["components"]}
    kinds = sorted(c["component"] for c in cs["components"])
    assert all(k in SPEC_COMPONENTS for k in kinds), kinds
    for k in ("TextField", "Slider", "ChoicePicker", "DateTimeInput", "CheckBox", "Button"):
        assert k in kinds, k
    assert by["form-0-f1"]["variant"] == "obscured"
    assert cs["dataModel"]["form-0"]["name"] == "" and cs["dataModel"]["remember"] is True
    ctx = by["form-0-submit"]["action"]["event"]["context"]
    assert ctx["name"] == {"path": "/form-0/name"} and ctx["form"] == "form-0" and len(ctx) == 7


def test_catalog_client_keeps_the_richer_form_atoms():
    caps = parse_client_capabilities({"a2uiClientCapabilities": {"v1.0": {"supportedCatalogIds": [
        BASIC_CATALOG_IDS["v1.0"], "https://a2uicatalog.ai/catalogue/a2ui-atoms-v1.json"]}}})
    cs = emit_surface(FORM_PAYLOAD, capabilities=caps)["createSurface"]
    assert "form" in [c["component"] for c in cs["components"]] and "dataModel" not in cs


def test_v09_split_sends_the_data_before_the_components():
    msgs = emit_messages(FORM_PAYLOAD, capabilities=_caps("v0.9"))
    assert [next(k for k in m if k != "version") for m in msgs] == ["createSurface", "updateDataModel", "updateComponents"]
    assert msgs[1]["updateDataModel"]["path"] == "/" and "form-0" in msgs[1]["updateDataModel"]["value"]
    assert "dataModel" not in msgs[0]["createSurface"]


def test_degraded_form_is_interactive_in_our_own_web_renderer(core_js):
    html = _render(core_js, emit_surface(FORM_PAYLOAD, capabilities=_caps("v1.0"))["createSurface"])
    assert 'data-a2ui-bind="/form-0/name"' in html and 'id="a2rt-' in html and "data-a2ui-action=" in html


# ── v0.9 is a DOWNGRADE for renderers that ask for it: validate it against v0.9 itself ───────
from tests.a2ui_v09_conformance import SERVER_TO_CLIENT as V09  # noqa: E402
from tests.a2ui_v09_conformance import assert_conforms as assert_v09  # noqa: E402


@pytest.mark.parametrize("with_catalog", [False, True])
def test_v09_downgrade_conforms_to_the_v09_spec(with_catalog):
    ids = [BASIC_CATALOG_IDS["v0.9"]] + (["https://a2uicatalog.ai/catalogue/a2ui-atoms-v1.json"] if with_catalog else [])
    caps = parse_client_capabilities({"a2uiClientCapabilities": {"v0.9": {"supportedCatalogIds": ids}}})
    for msg in emit_messages(FORM_PAYLOAD, capabilities=caps):
        assert msg["version"] == "v0.9"
        assert_v09(msg, V09)


def test_default_emit_is_still_v1():
    assert emit_messages(FORM_PAYLOAD)[0]["version"] == "v1.0"


# ── the fuzzers in a2ui-private/security/xss-fuzz drive schema.yaml ATOMS; the 18 spec components
# are not atoms, so hostile input for every field they take lives here.
EVIL = '"><img src=x onerror=alert(1)><script>alert(2)</script>'
EVIL_URL = "javascript:alert(3)"


def _hostile_surface():
    return {"surfaceId": EVIL, "dataModel": {"v": EVIL, "list": [EVIL], "n": EVIL}, "components": [
        {"id": "root", "component": "Column", "children": [
            "tf", "tf2", "cb", "cp", "cp2", "sl", "dt", "ic", "ic2", "ic3", "vi", "au", "li", "md", "tb", "bt"]},
        {"id": "tf", "component": "TextField", "label": EVIL, "placeholder": EVIL, "variant": EVIL, "value": {"path": "/v"}},
        {"id": "tf2", "component": "TextField", "label": "x", "variant": "longText", "value": EVIL},
        {"id": "cb", "component": "CheckBox", "label": EVIL, "value": {"path": "/v"}},
        {"id": "cp", "component": "ChoicePicker", "label": EVIL, "variant": EVIL, "displayStyle": "chips",
         "options": [{"label": EVIL, "value": EVIL}, EVIL, None], "value": {"path": "/list"}},
        {"id": "cp2", "component": "ChoicePicker", "label": "y", "variant": "multipleSelection", "options": EVIL, "value": EVIL},
        {"id": "sl", "component": "Slider", "label": EVIL, "min": EVIL, "max": EVIL, "steps": EVIL, "value": {"path": "/n"}},
        {"id": "dt", "component": "DateTimeInput", "label": EVIL, "min": EVIL, "max": EVIL, "enableTime": True, "value": {"path": "/v"}},
        {"id": "ic", "component": "Icon", "name": EVIL},
        {"id": "ic2", "component": "Icon", "name": {"svgPath": EVIL}},
        {"id": "ic3", "component": "Icon", "name": "toString"},
        {"id": "vi", "component": "Video", "url": EVIL_URL, "posterUrl": EVIL_URL},
        {"id": "au", "component": "AudioPlayer", "url": EVIL_URL, "description": EVIL},
        {"id": "li", "component": "List", "direction": EVIL, "align": EVIL, "children": ["lt"]},
        {"id": "lt", "component": "Text", "text": "item"},
        {"id": "md", "component": "Modal", "trigger": "mt", "content": "mc"},
        {"id": "mt", "component": "Text", "text": "open"}, {"id": "mc", "component": "Text", "text": "inside"},
        {"id": "tb", "component": "Tabs", "tabs": [{"title": EVIL, "child": "lt"}]},
        {"id": "bt", "component": "Button", "variant": EVIL, "child": "btt",
         "action": {"event": {"name": EVIL, "userMessage": EVIL, "context": {EVIL: {"path": "/v"}, "u": EVIL}}}},
        {"id": "btt", "component": "Text", "text": "Go"},
    ]}


def test_every_basic_component_escapes_hostile_input(core_js):
    html = _render(core_js, _hostile_surface())
    assert "<img src=x" not in html and "<script>alert" not in html, "markup injected"
    assert "javascript:" not in html.lower(), "script URL reached an attribute"
    assert html.count("<script>") == 1, "only the surface runtime may carry a script"
    assert "\\u003cimg" in html or "<img" not in html      # the runtime's JSON model is escaped too


@pytest.mark.skipif(not CHROMIUM, reason="no Chromium")
def test_hostile_surface_executes_nothing_in_a_browser(core_js):
    html = _render(core_js, _hostile_surface())
    probe = """<script>window.__hit=0;window.alert=function(){window.__hit++};
window.addEventListener('load',function(){document.querySelector('[data-a2ui-bind]').dispatchEvent(new Event('input',{bubbles:true}));
document.querySelector('[data-a2ui-action]').click();
setTimeout(function(){var p=document.createElement('pre');p.id='hits';p.textContent=String(window.__hit);document.body.appendChild(p);},300);});</script>"""
    with tempfile.TemporaryDirectory() as td:
        page = Path(td) / "p.html"
        page.write_text("<!doctype html><html><head>" + probe + "</head><body>" + html + "</body></html>")
        p = subprocess.run([CHROMIUM, "--headless=new", "--no-sandbox", "--disable-gpu", "--virtual-time-budget=3000",
                            "--dump-dom", page.as_uri()], capture_output=True, text=True, timeout=90)
    m = re.search(r'<pre id="hits">(\d+)</pre>', p.stdout)
    assert m and m.group(1) == "0", f"hostile payload executed: {m.group(1) if m else p.stdout[-400:]}"


# ── in an MCP Apps host the action goes back into the conversation (ui/message via the host bridge)
def _run_with_bridge(core_js, surface, bridge_js, clicks=1):
    html = _render(core_js, surface)
    driver = """<script>
var sent = [];
""" + bridge_js + """
window.addEventListener('load', function () {
  var n = document.querySelector('[data-a2ui-bind="/form/name"]');
  if (n) { n.value = 'Grace'; n.dispatchEvent(new Event('input', {bubbles: true})); }
  var b = document.querySelector('[data-a2ui-action]');
  for (var i = 0; i < """ + str(clicks) + """; i++) b.click();
  setTimeout(function () {
    var s = document.querySelector('.a2ui-status');
    var pre = document.createElement('pre'); pre.id = 'out';
    pre.textContent = JSON.stringify({sent: sent, status: s ? s.textContent : null, disabled: b.disabled});
    document.body.appendChild(pre);
  }, 200);
});
</script>"""
    with tempfile.TemporaryDirectory() as td:
        page = Path(td) / "p.html"
        page.write_text("<!doctype html><html><head>" + driver + "</head><body>" + html + "</body></html>")
        p = subprocess.run([CHROMIUM, "--headless=new", "--no-sandbox", "--disable-gpu", "--virtual-time-budget=3000",
                            "--dump-dom", page.as_uri()], capture_output=True, text=True, timeout=90)
    m = re.search(r'<pre id="out">(.*?)</pre>', p.stdout, re.S)
    assert m, p.stdout[-600:]
    return json.loads(m.group(1).replace("&quot;", '"').replace("&amp;", "&"))


OK_BRIDGE = "window._A2UI_HOST_BRIDGE = {sendMessage: function (t) { sent.push(t); return Promise.resolve({}); }};"
NO_BRIDGE = "window._A2UI_HOST_BRIDGE = {sendMessage: function (t) { sent.push(t); return Promise.reject(new Error('Message sending denied')); }};"


@pytest.mark.skipif(not CHROMIUM, reason="no Chromium")
def test_action_is_sent_to_the_conversation_once(core_js):
    out = _run_with_bridge(core_js, FORM, OK_BRIDGE, clicks=2)
    assert len(out["sent"]) == 1, out                       # a double tap sends once
    assert out["sent"][0].startswith("Book: who Grace") and "agree no" in out["sent"][0] and "source test" in out["sent"][0]
    assert out["status"] == "Sent" and out["disabled"] is True


@pytest.mark.skipif(not CHROMIUM, reason="no Chromium")
def test_user_message_wins_and_a_refusal_is_shown(core_js):
    surface = json.loads(json.dumps(FORM))
    go = next(c for c in surface["components"] if c["id"] == "go")
    go["action"]["event"]["userMessage"] = "Please book it"
    out = _run_with_bridge(core_js, surface, NO_BRIDGE)
    assert out["sent"] == ["Please book it"]
    assert out["status"] == "Message sending denied" and out["disabled"] is False   # host's words, button usable again


# ── v1.0 streams: createSurface, then updateComponents / updateDataModel redraw the same surface ──
UPDATES_JS = re.search(r"<script>\n(.*?)</script>", (GAS / "A2uiUpdates.html").read_text(), re.S).group(1)


def _stream(core_js, deliveries):
    """Feed each delivery to _a2uiAcceptV1 in turn (as successive tool results would); returns the
    rendered html after each (null when the delivery isn't accepted)."""
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "d.js"
        d.write_text("global.window = global;\n" + core_js + "\n" + UPDATES_JS + f"""
var out = {json.dumps(deliveries)}.map(function (p) {{
  var r = _a2uiAcceptV1(p); return r === null ? null : renderAtoms(r.blocks, {{}});
}});
out.push(JSON.stringify(window._A2UI_SURFACES));
console.log(JSON.stringify(out));""")
        p = subprocess.run(["node", str(d)], capture_output=True, text=True, timeout=60)
        assert p.returncode == 0, p.stderr[-1500:]
        return json.loads(p.stdout.strip().split("\n")[-1])


def _m(kind, body):
    return {"version": "v1.0", kind: body}


CREATE = _m("createSurface", {"surfaceId": "s1", "catalogId": "x", "dataModel": {"who": "Ada"},
                              "components": [{"id": "root", "component": "Column", "children": ["hello"]},
                                             {"id": "hello", "component": "Text", "text": {"path": "/who"}}]})
MORE = _m("updateComponents", {"surfaceId": "s1", "components": [
    {"id": "root", "component": "Column", "children": ["hello", "later"]},
    {"id": "later", "component": "Text", "text": "arrived in a second message"}]})
DATA = _m("updateDataModel", {"surfaceId": "s1", "path": "/who", "value": "Grace"})


def test_stream_builds_one_surface_over_several_messages(core_js):
    first, second, third, _ = _stream(core_js, [CREATE, MORE, DATA])
    assert "Ada" in first and "arrived in a second message" not in first
    assert "Ada" in second and "arrived in a second message" in second
    assert "Grace" in third and "arrived in a second message" in third


def test_a_list_of_messages_in_one_delivery(core_js):
    (html, _) = _stream(core_js, [[CREATE, MORE, DATA]])
    assert "Grace" in html and "arrived in a second message" in html
    (html2, _) = _stream(core_js, [{"messages": [CREATE, MORE]}])
    assert "arrived in a second message" in html2


def test_delete_and_strays_and_v09(core_js):
    gone, stray, v09, store = _stream(core_js, [[CREATE, _m("deleteSurface", {"surfaceId": "s1"})],
                                                _m("updateComponents", {"surfaceId": "nope", "components": []}),
                                                dict(CREATE, version="v0.9")])
    assert gone == "" and stray == "" and v09 is None
    assert json.loads(store) == {}


def test_typed_values_survive_more_components(core_js):
    form = _m("createSurface", {"surfaceId": "f", "catalogId": "x", "dataModel": {"name": ""},
                                "components": [{"id": "root", "component": "Column", "children": ["n"]},
                                               {"id": "n", "component": "TextField", "label": "Name", "value": {"path": "/name"}}]})
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "d.js"
        d.write_text("global.window = global;\n" + core_js + "\n" + UPDATES_JS + f"""
_a2uiAcceptV1({json.dumps(form)});
window._A2UI_SURFACES.f.dataModel.name = 'Typed by the user';   // what the runtime's live() writes
var r = _a2uiAcceptV1({json.dumps(_m("updateComponents", {"surfaceId": "f", "components": [
    {"id": "root", "component": "Column", "children": ["n", "x"]}, {"id": "x", "component": "Text", "text": "more"}]}))});
console.log(JSON.stringify(renderAtoms(r.blocks, {{}})));""")
        p = subprocess.run(["node", str(d)], capture_output=True, text=True, timeout=60)
        assert p.returncode == 0, p.stderr[-1500:]
        html = json.loads(p.stdout.strip().split("\n")[-1])
    assert 'value="Typed by the user"' in html and "more" in html
