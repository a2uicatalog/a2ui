"""freeform_canvas -- the sanitized SVG escape hatch. Security-sensitive:
every hard-block gets its own test asserting the WHOLE payload is rejected
(never a partial render), and the two authoring forms (structured
`elements[]` vs raw `svg` string) are proven to converge on identical
output for equivalent content, not just "both happen to work"."""

import pytest

from renderers.web_article import (
    FreeformCanvasError,
    _render_freeform_canvas,
    _parse_freeform_svg,
    validate_freeform_canvas,
    validate_freeform_canvas_element,
)


REJECTED = "rejected by the safety policy"

VALID_SUMMARY = "Three-node ring topology diagram with directional flow."
VALID_JUSTIFICATION = "No catalog atom represents a directed ring topology diagram."


def _base(**overrides):
    b = {
        "summary": VALID_SUMMARY,
        "justification": VALID_JUSTIFICATION,
        "viewbox": "0 0 600 300",
    }
    b.update(overrides)
    return b


# ── Happy path: structured elements[] ───────────────────────────────────────

def test_structured_elements_render(renderer):
    html = renderer([{
        "type": "freeform_canvas",
        **_base(elements=[
            {"tag": "g", "children": [
                {"tag": "circle", "cx": 150, "cy": 150, "r": 40, "fill": "#0284c7"},
                {"tag": "text", "x": 150, "y": 155, "text": "Node A", "font_size": 14},
            ]},
            {"tag": "path", "d": "M 190 150 L 410 150", "stroke": "#94a3b8"},
        ]),
    }])
    assert "<svg" in html
    assert 'role="img"' in html
    assert 'aria-label="Three-node ring topology' in html
    assert "Node A" in html
    assert '<circle cx="150" cy="150" r="40" fill="#0284c7"/>' in html
    assert '<path d="M 190 150 L 410 150" stroke="#94a3b8"/>' in html


def test_background_renders_as_backing_rect(renderer):
    html = renderer([{
        "type": "freeform_canvas",
        **_base(background="#0f172a", elements=[{"tag": "circle", "cx": 1, "cy": 1, "r": 1}]),
    }])
    assert 'fill="#0f172a"' in html


def test_default_viewbox_used_when_omitted():
    out = _render_freeform_canvas({
        "summary": VALID_SUMMARY, "justification": VALID_JUSTIFICATION,
        "elements": [{"tag": "circle", "cx": 1, "cy": 1, "r": 1}],
    })
    assert 'viewBox="0 0 800 500"' in out


# ── Happy path: raw svg string, and convergence with structured form ───────

def test_raw_svg_string_renders(renderer):
    html = renderer([{
        "type": "freeform_canvas",
        **_base(svg='<svg><circle cx="150" cy="150" r="40" fill="#0284c7"/>'
                    '<text x="150" y="155" font-size="14">Node A</text></svg>'),
    }])
    assert "Node A" in html
    assert '<circle cx="150" cy="150" r="40" fill="#0284c7"/>' in html


def test_structured_and_raw_svg_converge_on_identical_output():
    structured = _render_freeform_canvas({
        **_base(elements=[
            {"tag": "g", "children": [
                {"tag": "circle", "cx": 150, "cy": 150, "r": 40, "fill": "#0284c7"},
                {"tag": "text", "x": 150, "y": 155, "text": "Node A", "font_size": 14},
            ]},
        ]),
    })
    raw = _render_freeform_canvas({
        **_base(svg='<svg><g><circle cx="150" cy="150" r="40" fill="#0284c7"/>'
                    '<text x="150" y="155" font-size="14">Node A</text></g></svg>'),
    })
    assert structured == raw


def test_nested_gradient_defs_chain_round_trips_both_forms():
    elements = [{
        "tag": "defs", "children": [
            {"tag": "linearGradient", "id": "g1", "x1": 0, "y1": 0, "x2": 1, "y2": 0,
             "children": [
                 {"tag": "stop", "offset": "0%", "stop_color": "#fff"},
                 {"tag": "stop", "offset": "100%", "stop_color": "#000"},
             ]},
        ],
    }, {"tag": "rect", "x": 0, "y": 0, "width": 10, "height": 10, "fill": "url(#g1)"}]
    structured = _render_freeform_canvas({**_base(elements=elements)})
    raw = _render_freeform_canvas({**_base(
        svg='<svg><defs><linearGradient id="g1" x1="0" y1="0" x2="1" y2="0">'
            '<stop offset="0%" stop-color="#fff"/><stop offset="100%" stop-color="#000"/>'
            '</linearGradient></defs><rect x="0" y="0" width="10" height="10" fill="url(#g1)"/></svg>'
    )})
    assert structured == raw
    assert 'fill="url(#g1)"' in structured
    assert "<linearGradient" in structured
    assert "<stop" in structured


# ── Required-field / shape validation ───────────────────────────────────────

def test_missing_summary_rejected():
    out = _render_freeform_canvas({"justification": VALID_JUSTIFICATION,
                                    "elements": [{"tag": "circle", "cx": 1, "cy": 1, "r": 1}]})
    assert REJECTED in out


def test_missing_justification_rejected():
    out = _render_freeform_canvas({"summary": VALID_SUMMARY,
                                    "elements": [{"tag": "circle", "cx": 1, "cy": 1, "r": 1}]})
    assert REJECTED in out


def test_short_justification_rejected():
    out = _render_freeform_canvas({**_base(justification="too short",
                                            elements=[{"tag": "circle", "cx": 1, "cy": 1, "r": 1}])})
    assert REJECTED in out


def test_neither_elements_nor_svg_rejected():
    out = _render_freeform_canvas({**_base()})
    assert REJECTED in out


def test_both_elements_and_svg_rejected():
    out = _render_freeform_canvas({**_base(
        elements=[{"tag": "circle", "cx": 1, "cy": 1, "r": 1}],
        svg="<svg><circle cx='1' cy='1' r='1'/></svg>",
    )})
    assert REJECTED in out


# ── Hard security blocks -- each its own test, whole-payload rejection ─────

def test_script_tag_rejected_structured():
    out = _render_freeform_canvas({**_base(elements=[{"tag": "script"}])})
    assert REJECTED in out


def test_script_tag_rejected_raw_svg():
    out = _render_freeform_canvas({**_base(svg="<svg><script>alert(1)</script></svg>")})
    assert REJECTED in out


def test_foreign_object_rejected():
    out = _render_freeform_canvas({**_base(
        svg='<svg><foreignObject><div>hi</div></foreignObject></svg>')})
    assert REJECTED in out


def test_image_tag_rejected():
    out = _render_freeform_canvas({**_base(
        elements=[{"tag": "image", "href": "#x"}])})
    assert REJECTED in out


def test_external_href_rejected():
    out = _render_freeform_canvas({**_base(
        elements=[{"tag": "use", "href": "https://evil.example/x.svg#y"}])})
    assert REJECTED in out


def test_javascript_href_rejected():
    out = _render_freeform_canvas({**_base(
        elements=[{"tag": "use", "href": "javascript:alert(1)"}])})
    assert REJECTED in out


def test_on_attribute_rejected():
    out = _render_freeform_canvas({**_base(
        elements=[{"tag": "rect", "x": 0, "y": 0, "width": 1, "height": 1,
                   "onload": "alert(1)"}])})
    assert REJECTED in out


def test_on_attribute_rejected_via_raw_svg():
    out = _render_freeform_canvas({**_base(
        svg='<svg><rect x="0" y="0" width="1" height="1" onload="alert(1)"/></svg>')})
    assert REJECTED in out


def test_style_attribute_rejected():
    out = _render_freeform_canvas({**_base(
        elements=[{"tag": "rect", "x": 0, "y": 0, "width": 1, "height": 1,
                   "style": "background:url(javascript:alert(1))"}])})
    assert REJECTED in out


def test_external_url_in_fill_rejected():
    out = _render_freeform_canvas({**_base(
        elements=[{"tag": "rect", "x": 0, "y": 0, "width": 1, "height": 1,
                   "fill": "url(https://evil.example/steal.svg#x)"}])})
    assert REJECTED in out


def test_local_fragment_url_in_fill_is_allowed():
    out = _render_freeform_canvas({**_base(
        elements=[{"tag": "rect", "x": 0, "y": 0, "width": 1, "height": 1,
                   "fill": "url(#validGradient)"}])})
    assert REJECTED not in out
    assert 'fill="url(#validGradient)"' in out


def test_unknown_tag_rejected():
    out = _render_freeform_canvas({**_base(elements=[{"tag": "div"}])})
    assert REJECTED in out


def test_unknown_attribute_rejected():
    out = _render_freeform_canvas({**_base(
        elements=[{"tag": "circle", "cx": 1, "cy": 1, "r": 1, "not_a_real_attr": "x"}])})
    assert REJECTED in out


def test_children_on_non_container_tag_rejected():
    out = _render_freeform_canvas({**_base(
        elements=[{"tag": "circle", "cx": 1, "cy": 1, "r": 1,
                   "children": [{"tag": "circle", "cx": 1, "cy": 1, "r": 1}]}])})
    assert REJECTED in out


def test_text_content_on_non_text_tag_rejected():
    out = _render_freeform_canvas({**_base(
        elements=[{"tag": "circle", "cx": 1, "cy": 1, "r": 1, "text": "nope"}])})
    assert REJECTED in out


# ── XML parsing safety (raw svg path only) ──────────────────────────────────

def test_entity_expansion_attack_rejected():
    payload = """<?xml version="1.0"?>
<!DOCTYPE lolz [
 <!ENTITY lol "lol">
 <!ELEMENT lolz (#PCDATA)>
 <!ENTITY lol1 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
]>
<svg>&lol1;</svg>"""
    out = _render_freeform_canvas({**_base(svg=payload)})
    assert REJECTED in out


def test_external_entity_xxe_rejected():
    payload = ('<?xml version="1.0"?><!DOCTYPE svg ['
               '<!ENTITY x SYSTEM "file:///etc/passwd">]><svg>&x;</svg>')
    out = _render_freeform_canvas({**_base(svg=payload)})
    assert REJECTED in out


def test_non_svg_root_rejected():
    out = _render_freeform_canvas({**_base(svg="<div><circle/></div>")})
    assert REJECTED in out


def test_malformed_xml_rejected():
    out = _render_freeform_canvas({**_base(svg="<svg><circle cx='1'></svg>")})
    assert REJECTED in out


# ── Low-level validator unit tests ──────────────────────────────────────────

def test_validate_freeform_canvas_empty_list_raises():
    with pytest.raises(FreeformCanvasError):
        validate_freeform_canvas([])


def test_validate_freeform_canvas_element_normalizes_shape():
    out = validate_freeform_canvas_element({"tag": "circle", "cx": 1, "cy": 1, "r": 1})
    assert out == {"tag": "circle", "attrs": {"cx": 1, "cy": 1, "r": 1},
                    "text": None, "children": []}


def test_parse_freeform_svg_strips_xlink_href_namespace():
    parsed = _parse_freeform_svg(
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'xmlns:xlink="http://www.w3.org/1999/xlink">'
        '<use xlink:href="#thing"/></svg>')
    assert parsed[0]["tag"] == "use"
    assert parsed[0]["href"] == "#thing"
