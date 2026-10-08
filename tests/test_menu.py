"""menu (preview) -- a CSS-only menu of links behind one trigger.

Both real renderers are exercised: GAS (via the same Node-eval harness
test_agent_sketchpad.py uses, over the generated MCP Apps bundle) and the Python
twin in renderers/web_article.py. They must agree byte for byte, and both must
hold the v1 contract: links, separators, headings and submenus only, no wire,
nothing hostile reaching markup.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import gen_mcp_apps_bundle as gen  # noqa: E402

from renderers.web_article import _RENDERERS  # noqa: E402

# The registered renderer, not _render_menu: the payload guard wraps the registry, and the GAS
# side runs it too, so parity only holds through the guarded entry.
_render_menu = _RENDERERS["menu"]

FULL = {
    "type": "menu",
    "trigger": {"kind": "button", "label": "Create", "icon": "+"},
    "items": [
        {"type": "heading", "label": "New"},
        {"id": "post", "label": "New post", "description": "Write and share ideas",
         "icon": "✎", "shortcut": "⌘N", "badge": "beta", "url": "https://example.com/post"},
        {"label": "Anchor", "url": "#section"},
        {"label": "Locked", "url": "https://example.com/x", "disabled": True},
        {"type": "separator"},
        {"type": "submenu", "label": "From template", "icon": "▦", "items": [
            {"label": "Blank", "url": "/blank"},
            {"type": "separator"},
            {"type": "submenu", "label": "Too deep", "items": [{"label": "Never", "url": "/x"}]},
        ]},
        {"label": "Delete", "danger": True, "url": "https://example.com/del"},
    ],
}
ICON = {"type": "menu", "trigger": {"kind": "icon", "label": "More actions", "icon": "⋯"},
        "items": [{"label": "Edit", "url": "/e"}]}
SPLIT = {"type": "menu", "trigger": {"kind": "split", "label": "Publish", "url": "https://example.com/pub"},
         "items": [{"label": "Schedule", "url": "/s"}, {"label": "Save as draft", "url": "/d"}]}
SPLIT_NO_URL = {"type": "menu", "trigger": {"kind": "split", "label": "Publish"},
                "items": [{"label": "Schedule", "url": "/s"}]}
CONTEXTUAL = {"type": "menu", "trigger": {"kind": "contextual", "label": "Row"}, "items": [{"label": "A", "url": "/a"}]}
ALIGN_END = {"type": "menu", "align": "end", "trigger": {"label": "More"}, "items": [{"label": "A", "url": "/a"}]}
SPLIT_START = {"type": "menu", "align": "start", "trigger": {"kind": "split", "label": "P", "url": "/p"}, "items": [{"label": "A", "url": "/a"}]}
ALIGN_JUNK = {"type": "menu", "align": "left\" x", "trigger": {"label": "More"}, "items": [{"label": "A", "url": "/a"}]}
EMPTY = {"type": "menu"}
JUNK = {"type": "menu", "trigger": "nope", "items": [None, 5, "x", {"type": "action", "label": "Act"},
                                                    {"type": "checkbox", "label": "Chk"},
                                                    {"label": ""}, {"type": "heading"}]}
HOSTILE = {
    "type": "menu",
    "trigger": {"kind": "button\" onmouseover=\"alert(1)", "label": "<script>alert(1)</script>",
                "icon": "<img src=x onerror=alert(1)>"},
    "items": [
        {"label": "<img src=x onerror=alert(1)>", "url": "javascript:alert(1)"},
        {"label": "data", "url": "data:text/html,<script>alert(1)</script>"},
        {"label": "proto-relative", "url": "//evil.example/x"},
        {"label": "q\"'><b>", "description": "</div><script>x</script>", "badge": "\"><i>",
         "shortcut": "'><u>", "url": "https://example.com/\"onmouseover=\"alert(1)"},
        {"type": "submenu", "label": "</details><script>1</script>",
         "items": [{"label": "k", "url": "vbscript:x"}]},
    ],
}
ALL = {"full": FULL, "icon": ICON, "split": SPLIT, "split_no_url": SPLIT_NO_URL,
       "contextual": CONTEXTUAL, "align_end": ALIGN_END, "split_start": SPLIT_START, "align_junk": ALIGN_JUNK, "empty": EMPTY, "junk": JUNK, "hostile": HOSTILE}


@pytest.fixture(scope="module")
def gas_html():
    bundle = gen.build_bundle()
    blocks = re.findall(r"<script>\n(.*?)\n</script>", bundle, re.S)
    core = [b for b in blocks if "a2ui-core" in b[:300]]
    assert core, "a2ui-core script block missing"
    with tempfile.TemporaryDirectory() as td:
        driver = Path(td) / "d.js"
        driver.write_text(
            "global.window = global;\n" + core[0] + f"""
var cases = {json.dumps(ALL)};
var out = {{}};
Object.keys(cases).forEach(function(k) {{ out[k] = renderAtoms([cases[k]], {{}}); }});
console.log(JSON.stringify(out));
""")
        proc = subprocess.run(["node", str(driver)], capture_output=True, text=True, timeout=60)
        assert proc.returncode == 0, proc.stderr[-1500:]
        return json.loads(proc.stdout)


@pytest.fixture(scope="module")
def py_html():
    return {k: _render_menu(v) for k, v in ALL.items()}


def _inner(html: str) -> str:
    """The atom's own markup, without any wrapper the generic renderer adds."""
    i = html.find("<div data-a2ui-menu")
    assert i >= 0, html[:300]
    return html[i:]


@pytest.mark.parametrize("name", list(ALL))
def test_gas_and_python_agree(name, gas_html, py_html):
    assert _inner(gas_html[name]).startswith(py_html[name][:60])
    assert py_html[name] in gas_html[name], f"{name}: GAS and Python diverge"


@pytest.fixture(params=["gas", "py"])
def html(request, gas_html, py_html):
    return (lambda n: gas_html[n]) if request.param == "gas" else (lambda n: py_html[n])


def test_button_trigger_opens_a_details_menu(html):
    h = html("full")
    assert 'data-a2ui-menu="button"' in h
    assert re.search(r"<details[^>]*><summary aria-haspopup=\"menu\"", h)
    assert ">Create<" in h or "Create<svg" in h


def test_icon_trigger_is_labelled_and_label_free(html):
    h = html("icon")
    assert 'data-a2ui-menu="icon"' in h
    assert 'aria-label="More actions"' in h
    assert ">More actions<" not in h


def test_link_navigates_and_anchor_stays_in_page(html):
    h = html("full")
    assert 'href="https://example.com/post" target="_blank" rel="noopener noreferrer"' in h
    assert 'href="#section" style=' in h  # anchor: no target


def test_disabled_item_is_not_a_link(html):
    h = html("full")
    assert '<span role="menuitem" aria-disabled="true"' in h
    assert "https://example.com/x" not in h


def test_danger_styling_renders(html):
    assert "#b3261e" in html("full")


def test_separator_and_heading_render(html):
    h = html("full")
    assert 'role="separator"' in h
    assert ">New</div>" in h and "text-transform:uppercase" in h


def test_submenu_expands_in_place_and_stops_one_level_deep(html):
    h = html("full")
    assert h.count("<details") == 2  # the trigger + one submenu
    assert "Blank" in h
    assert "Too deep" not in h and "Never" not in h


def test_split_keeps_primary_link_and_menu(html):
    h = html("split")
    assert 'data-a2ui-menu="split"' in h
    assert 'href="https://example.com/pub"' in h and ">Publish</a>" in h
    assert 'aria-label="Publish options"' in h
    assert "right:0;" in h and "Schedule" in h


def test_align_moves_the_panel_edge(html):
    assert "right:0;" in html("align_end") and "left:0;" not in html("align_end")
    assert "left:0;" in html("split_start") and "right:0;" not in html("split_start")
    assert "left:0;" in html("full") and "right:0;" in html("split")
    assert "left:0;" in html("align_junk")  # not start/end: default for a button
    assert "left\"" not in html("align_junk")


def test_split_halves_share_one_box_height(html):
    h = html("split")
    assert h.count("box-sizing:border-box;height:2.5rem;line-height:1.2;") == 2  # the link and the arrow


def test_split_without_url_degrades_to_button(html):
    assert 'data-a2ui-menu="button"' in html("split_no_url")


def test_contextual_opens_on_contextmenu_and_still_works_as_a_button(html):
    h = html("contextual")
    assert 'data-a2ui-menu="contextual"' in h
    assert '<details' in h and 'aria-haspopup="menu"' in h          # no script: a tap still opens it
    assert 'addEventListener("contextmenu"' in h and "e.preventDefault()" in h
    assert "-webkit-touch-callout:none;-webkit-user-select:none;" in h   # no native selection toolbar on long-press
    assert 'Escape' in h and "data-bound" in h                      # dismissal and idempotent binding
    assert h.count("<script>") == 1


def test_only_contextual_ships_a_script(html):
    for name in ALL:
        if name == "contextual":
            continue
        assert "<script" not in html(name).lower() or name == "hostile"
    assert "<script" not in html("hostile").lower().replace("&lt;script&gt;", "")


SPRING = {"type": "menu", "spring": "snappy", "trigger": {"label": "S"}, "items": [{"label": "A", "url": "/a"}]}
SPRING_JUNK = {"type": "menu", "spring": "wobbly\" x", "trigger": {"label": "S"}, "items": [{"label": "A", "url": "/a"}]}


def test_spring_rules_have_a_cubic_bezier_fallback_and_linear_curve():
    h = _render_menu(SPRING)
    assert 'data-spring="snappy"' in h
    rule = re.search(r"\[data-spring=snappy\] details\[open\]>\[role=menu\]\{([^}]*)\}", h).group(1)
    first, second = rule.split(";animation:")
    assert "cubic-bezier(0.34,1.56,0.64,1)" in first and "linear(" in second
    assert "calc(420ms * var(--a2ui-motion-duration-scale,1))" in first
    assert "data-spring" not in _render_menu(SPRING_JUNK).split("<style>")[0]
    assert 'data-spring="wobbly' not in _render_menu(SPRING_JUNK)


def test_spring_tables_are_the_damped_spring_step_response_and_match_between_renderers():
    import math
    from renderers.web_article import _MO_SPRING
    zetas = {"gentle": 0.8, "snappy": 0.55, "heavy": 0.35}
    assert set(_MO_SPRING) == set(zetas)
    for name, z in zetas.items():
        w0 = math.log(200) / z
        wd = w0 * math.sqrt(1 - z * z)
        pts = [0.0] + [1 - math.exp(-z * w0 * i / 32) * (math.cos(wd * i / 32) + (z * w0 / wd) * math.sin(wd * i / 32))
                       for i in range(1, 32)] + [1.0]
        got = [float(x) for x in _MO_SPRING[name]["lin"][len("linear("):-1].split(",")]
        assert len(got) == 33 and all(abs(a - b) <= 0.0006 for a, b in zip(got, pts)), name
        assert got[0] == 0 and got[-1] == 1
    assert max(float(x) for x in _MO_SPRING["heavy"]["lin"][7:-1].split(",")) > 1.2  # heavy visibly overshoots


def test_gas_spring_table_equals_python(gas_html, py_html):
    # the menu <style> embeds every spring rule, so equal markup means equal tables
    assert _MENU_SPRING_RULES(py_html["full"]) == _MENU_SPRING_RULES(gas_html["full"])


def _MENU_SPRING_RULES(h):
    return re.findall(r"\[data-spring=\w+\][^}]*\}", h)


def test_v1_has_no_action_checkbox_or_radio(html):
    h = html("junk")
    assert "Act" not in h and "Chk" not in h


def test_empty_and_junk_payloads_still_render(html):
    assert 'role="menu"' in html("empty")
    assert 'role="menu"' in html("junk")


def test_plain_payload_carries_no_wire_or_script(html):
    for name in ALL:
        h = html(name)
        assert "<script" not in h.lower() or name in ("hostile", "contextual")
        assert "data-row-json" not in h and "onclick" not in h.lower()


class _Audit(HTMLParser):
    def __init__(self):
        super().__init__()
        self.bad = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "img", "iframe", "object", "embed", "i", "b", "u"):
            self.bad.append(tag)
        for k, v in attrs:
            if k.startswith("on"):
                self.bad.append(k)
            if k == "href" and v and not re.match(r"(https?://|mailto:|#|/(?!/))", v):
                self.bad.append(f"href={v}")


def test_hostile_payload_yields_no_active_markup(html):
    p = _Audit()
    p.feed(html("hostile"))
    assert p.bad == [], p.bad
    h = html("hostile")
    assert "javascript:" not in h and "vbscript:" not in h and "data:text" not in h
    assert 'href="//evil' not in h
    assert 'data-a2ui-menu="button"' in h  # the injected kind fell back to the enum default


def test_schema_declares_menu_as_a_preview_with_surface_metadata():
    atoms = yaml.safe_load((ROOT / "atoms" / "schema.yaml").read_text())["blocks"]
    m = next(a for a in atoms if a["type"] == "menu")
    assert m.get("stage") == "preview"
    assert {"trigger", "items"} <= set(m["fields"])
    assert "wire" not in m  # v1 is wire-free by contract
    assert {i["surface"] for i in m["surfaces"]["incompatible_on"]} >= {"google-chat", "email", "pdf"}


# ---- motion policy v0: palette scales -> :root variables, menu is the pilot consumer ----

PALETTES = {
    "none": {"type": "palette"},
    "scales": {"type": "palette", "duration_scale": 0.75, "intensity_scale": "1.5", "stagger_scale": 0.125},
    "clamped": {"type": "palette", "duration_scale": 99, "intensity_scale": -4, "stagger_scale": 0.001},
    "junk": {"type": "palette", "duration_scale": "fast", "intensity_scale": True, "stagger_scale": None},
    "hostile": {"type": "palette", "duration_scale": "1;}body{display:none}", "intensity_scale": "1e9"},
}


@pytest.fixture(scope="module")
def palette_gas():
    bundle = gen.build_bundle()
    core = [b for b in re.findall(r"<script>\n(.*?)\n</script>", bundle, re.S) if "a2ui-core" in b[:300]][0]
    with tempfile.TemporaryDirectory() as td:
        driver = Path(td) / "d.js"
        driver.write_text("global.window = global;\n" + core + f"""
var cases = {json.dumps(PALETTES)}; var out = {{}};
Object.keys(cases).forEach(function(k) {{ out[k] = renderAtoms([cases[k]], {{}}); }});
console.log(JSON.stringify(out));""")
        proc = subprocess.run(["node", str(driver)], capture_output=True, text=True, timeout=60)
        assert proc.returncode == 0, proc.stderr[-1500:]
        return json.loads(proc.stdout)


@pytest.mark.parametrize("name", list(PALETTES))
def test_palette_scales_agree_between_renderers(name, palette_gas):
    assert _RENDERERS["palette"](PALETTES[name]) in palette_gas[name], name


def test_palette_scales_become_clamped_variables(palette_gas):
    py = {k: _RENDERERS["palette"](v) for k, v in PALETTES.items()}
    for h in (py["scales"], palette_gas["scales"]):
        assert "--a2ui-motion-duration-scale:0.75;" in h
        assert "--a2ui-motion-intensity-scale:1.5;" in h
        assert "--a2ui-motion-stagger-scale:0.13;" in h  # 0.125 rounds half up, same in both
    for h in (py["clamped"], palette_gas["clamped"]):
        assert "--a2ui-motion-duration-scale:3;" in h
        assert "--a2ui-motion-intensity-scale:0;" in h
        assert "--a2ui-motion-stagger-scale:0;" in h
    for k in ("none", "junk", "hostile"):
        for h in (py[k], palette_gas[k]):
            assert "duration-scale:" not in h or k == "hostile"
            assert "display:none" not in h and "e9" not in h


def test_hostile_scale_strings_are_not_written(palette_gas):
    for h in (_RENDERERS["palette"](PALETTES["hostile"]), palette_gas["hostile"]):
        assert "--a2ui-motion-duration-scale" not in h and "--a2ui-motion-intensity-scale" not in h


def test_menu_animation_reads_the_scales_and_respects_reduced_motion(html):
    h = html("full")
    assert "calc(240ms * var(--a2ui-motion-duration-scale,1))" in h
    assert "var(--a2ui-motion-intensity-scale,1)" in h
    assert "prefers-reduced-motion:reduce" in h
    assert "details[open]>[role=menu]" in h


def test_a_surface_without_a_palette_is_unchanged_by_the_scales(py_html):
    # the fallbacks are 1, so a missing variable means the default 240 ms / 6 px
    assert "--a2ui-motion" not in _RENDERERS["palette"]({"type": "palette"})
