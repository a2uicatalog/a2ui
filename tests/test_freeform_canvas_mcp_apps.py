"""freeform_canvas's mcp-apps (JS) renderer -- apps-script-surface/gas-
wired-renderer/atoms_freeform.gs. Security-sensitive, same as its Python
sibling (renderers/web_article.py) and reviewed against the identical
allowlist/hard-block spec: every hard-block gets its own test asserting
the WHOLE payload is rejected, and the two authoring forms (structured
`elements[]` vs raw `svg` string) are proven to converge on equivalent
output. Drives the atom through the REAL browser-portable bundle
(gen_mcp_apps_bundle.build_bundle()) via a single Node process per test
module -- .gs renderer files aren't Node-requireable modules, so this is
the established pattern this repo already uses for testing them (see
test_mcp_apps_bundle.py), not tests-js/.
"""

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

REJECTED = "rejected by the safety policy"
VALID_JUSTIFICATION = "No catalog atom represents this specific diagram."


@pytest.fixture(scope="module")
def core_js():
    bundle = gen.build_bundle()
    blocks = re.findall(r"<script>\n(.*?)\n</script>", bundle, re.S)
    core = [b for b in blocks if "a2ui-core" in b[:300]]
    assert core, "a2ui-core script block missing"
    return core[0]


def _render_all(core_js, cases):
    """{name: block} -> {name: html or 'THREW: <message>'}, one real Node
    process for the whole batch (matches test_mcp_apps_bundle.py's own
    single-invocation-per-module discipline)."""
    for c in cases.values():
        c.setdefault("component", c["type"])
    with tempfile.TemporaryDirectory() as td:
        driver = Path(td) / "driver.js"
        driver.write_text(
            "global.window = global;\n" + core_js +
            "\nvar cases = " + json.dumps(cases) + ";\n"
            "var out = {};\n"
            "for (var k in cases) {\n"
            "  try { out[k] = renderAtoms([cases[k]], {theme: 'light'}); }\n"
            "  catch (e) { out[k] = 'THREW: ' + e.message; }\n"
            "}\n"
            "console.log(JSON.stringify(out));\n"
        )
        proc = subprocess.run(["node", str(driver)], capture_output=True,
                               text=True, timeout=60)
        assert proc.returncode == 0, proc.stderr[-2000:]
        return json.loads(proc.stdout)


def _base(**overrides):
    b = {"type": "freeform_canvas", "summary": "A diagram.",
         "justification": VALID_JUSTIFICATION}
    b.update(overrides)
    return b


def test_structured_elements_render(core_js):
    out = _render_all(core_js, {"case": _base(
        elements=[{"tag": "circle", "cx": 1, "cy": 1, "r": 1, "fill": "#000"}])})["case"]
    assert not out.startswith("THREW:")
    assert REJECTED not in out
    assert '<circle cx="1" cy="1" r="1" fill="#000"/>' in out


def test_raw_svg_converges_with_structured_form(core_js):
    out = _render_all(core_js, {
        "structured": _base(elements=[{"tag": "circle", "cx": 1, "cy": 1, "r": 1, "fill": "#000"}]),
        "raw": _base(svg='<svg><circle cx="1" cy="1" r="1" fill="#000"/></svg>'),
    })
    assert out["structured"] == out["raw"]


def test_missing_summary_rejected(core_js):
    out = _render_all(core_js, {"case": {
        "type": "freeform_canvas", "justification": VALID_JUSTIFICATION,
        "elements": [{"tag": "circle", "cx": 1, "cy": 1, "r": 1}]}})["case"]
    assert REJECTED in out


def test_missing_justification_rejected(core_js):
    out = _render_all(core_js, {"case": _base(
        justification=None,
        elements=[{"tag": "circle", "cx": 1, "cy": 1, "r": 1}])})["case"]
    assert REJECTED in out


def test_short_justification_rejected(core_js):
    out = _render_all(core_js, {"case": _base(
        justification="too short",
        elements=[{"tag": "circle", "cx": 1, "cy": 1, "r": 1}])})["case"]
    assert REJECTED in out


def test_both_elements_and_svg_rejected(core_js):
    out = _render_all(core_js, {"case": _base(
        elements=[{"tag": "circle", "cx": 1, "cy": 1, "r": 1}],
        svg="<svg></svg>")})["case"]
    assert REJECTED in out


def test_neither_elements_nor_svg_rejected(core_js):
    out = _render_all(core_js, {"case": _base()})["case"]
    assert REJECTED in out


@pytest.mark.parametrize("name,element", [
    ("script_tag", {"tag": "script"}),
    ("foreignObject_tag", {"tag": "foreignObject"}),
    ("image_tag", {"tag": "image"}),
    ("iframe_tag", {"tag": "iframe"}),
    ("unknown_tag", {"tag": "div"}),
    ("style_attr", {"tag": "rect", "x": 0, "y": 0, "width": 1, "height": 1, "style": "x:y"}),
    ("on_attr", {"tag": "rect", "x": 0, "y": 0, "width": 1, "height": 1, "onload": "alert(1)"}),
    ("unknown_attr", {"tag": "circle", "cx": 1, "cy": 1, "r": 1, "not_real": "x"}),
    ("external_href", {"tag": "use", "href": "http://evil.example/x"}),
    ("javascript_href", {"tag": "use", "href": "javascript:alert(1)"}),
    ("external_url_fill", {"tag": "rect", "x": 0, "y": 0, "width": 1, "height": 1,
                            "fill": "url(http://evil.example/x)"}),
    ("bare_external_url_fill", {"tag": "rect", "x": 0, "y": 0, "width": 1, "height": 1,
                                 "fill": "http://evil.example/track.png"}),
    ("mailto_scheme", {"tag": "rect", "x": 0, "y": 0, "width": 1, "height": 1,
                        "fill": "mailto:x@example.com"}),
    ("data_uri", {"tag": "rect", "x": 0, "y": 0, "width": 1, "height": 1,
                   "fill": "data:text/html,<script>alert(1)</script>"}),
])
def test_hard_block_rejects_whole_payload(core_js, name, element):
    out = _render_all(core_js, {"case": _base(elements=[element])})["case"]
    assert REJECTED in out, f"{name} was not rejected: {out}"


def test_local_fragment_url_in_fill_is_allowed(core_js):
    out = _render_all(core_js, {"case": _base(
        elements=[{"tag": "rect", "x": 0, "y": 0, "width": 1, "height": 1,
                   "fill": "url(#validGradient)"}])})["case"]
    assert REJECTED not in out
    assert re.search(r'fill="url\(#[0-9a-f]{8}-validGradient\)"', out)


def test_bad_viewbox_rejected(core_js):
    out = _render_all(core_js, {"case": _base(
        viewbox='0 0 10 10" onload="alert(1)',
        elements=[{"tag": "rect", "x": 0, "y": 0, "width": 1, "height": 1}])})["case"]
    assert REJECTED in out


def test_bad_background_scheme_rejected(core_js):
    out = _render_all(core_js, {"case": _base(
        background="javascript:alert(1)",
        elements=[{"tag": "rect", "x": 0, "y": 0, "width": 1, "height": 1}])})["case"]
    assert REJECTED in out


def test_valid_hex_background_allowed(core_js):
    out = _render_all(core_js, {"case": _base(
        background="#0f172a",
        elements=[{"tag": "rect", "x": 0, "y": 0, "width": 1, "height": 1}])})["case"]
    assert REJECTED not in out
    assert 'fill="#0f172a"' in out


def test_doctype_and_entity_declaration_rejected_not_expanded(core_js):
    """No general entity-expansion mechanism exists in this tokenizer at
    all (structural, not a runtime check) -- DOCTYPE is rejected outright.
    A real billion-laughs-shaped payload must fail cleanly, not hang or
    expand."""
    payload = ('<!DOCTYPE svg [<!ENTITY a "AAAAAAAAAA">'
               '<!ENTITY b "&a;&a;&a;&a;&a;&a;&a;&a;&a;&a;">]>'
               '<svg><text>&b;</text></svg>')
    out = _render_all(core_js, {"case": _base(svg=payload)})["case"]
    assert REJECTED in out
    assert "AAAAAAAAAA" not in out


def test_unknown_numeric_entity_out_of_range_rejected(core_js):
    out = _render_all(core_js, {"case": _base(
        svg='<svg><text>&#x110000;</text></svg>')})["case"]
    assert REJECTED in out


def test_nested_gradient_defs_chain_renders(core_js):
    elements = [{
        "tag": "defs", "children": [
            {"tag": "linearGradient", "id": "g1", "x1": 0, "y1": 0, "x2": 1, "y2": 0,
             "children": [
                 {"tag": "stop", "offset": "0%", "stop_color": "#fff"},
                 {"tag": "stop", "offset": "100%", "stop_color": "#000"},
             ]},
        ],
    }, {"tag": "rect", "x": 0, "y": 0, "width": 10, "height": 10, "fill": "url(#g1)"}]
    out = _render_all(core_js, {"case": _base(elements=elements)})["case"]
    assert REJECTED not in out
    assert "linearGradient" in out and "<stop" in out


def test_two_instances_on_same_page_get_non_colliding_ids(core_js):
    elements = [
        {"tag": "defs", "children": [
            {"tag": "linearGradient", "id": "grad1", "x1": 0, "y1": 0, "x2": 1, "y2": 0,
             "children": [{"tag": "stop", "offset": "0%", "stop_color": "#fff"}]},
        ]},
        {"tag": "rect", "x": 0, "y": 0, "width": 10, "height": 10, "fill": "url(#grad1)"},
    ]
    out = _render_all(core_js, {
        "a": _base(summary="Diagram A.", elements=elements),
        "b": _base(summary="Diagram B.", elements=elements),
    })
    id_a = re.search(r'id="([0-9a-f]{8}-grad1)"', out["a"]).group(1)
    id_b = re.search(r'id="([0-9a-f]{8}-grad1)"', out["b"]).group(1)
    assert id_a != id_b
    assert f"url(#{id_a})" in out["a"] and f"url(#{id_b})" in out["b"]
    assert "url(#grad1)" not in out["a"] and "url(#grad1)" not in out["b"]
