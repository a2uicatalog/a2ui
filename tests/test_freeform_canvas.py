"""freeform_canvas -- the sanitized SVG escape hatch. Security-sensitive:
every hard-block gets its own test asserting the WHOLE payload is rejected
(never a partial render), and the two authoring forms (structured
`elements[]` vs raw `svg` string) are proven to converge on identical
output for equivalent content, not just "both happen to work"."""

import re

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
    # Both forms carry a per-render id prefix (namespaced from the literal
    # payload, so two DIFFERENT authoring forms of equivalent content get
    # different prefixes -- see _freeform_namespace_element). Normalize that
    # away to compare structural equivalence, which is what this test is
    # actually about.
    def _strip_id_prefix(html):
        return re.sub(r'(?<=["#])[0-9a-f]{8}-', '', html)

    structured = _render_freeform_canvas({**_base(elements=elements)})
    raw = _render_freeform_canvas({**_base(
        svg='<svg><defs><linearGradient id="g1" x1="0" y1="0" x2="1" y2="0">'
            '<stop offset="0%" stop-color="#fff"/><stop offset="100%" stop-color="#000"/>'
            '</linearGradient></defs><rect x="0" y="0" width="10" height="10" fill="url(#g1)"/></svg>'
    )})
    structured, raw = _strip_id_prefix(structured), _strip_id_prefix(raw)
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
    # id-namespaced (see _freeform_namespace_element) -- the fragment name
    # is preserved, just prefixed per-render-instance.
    assert re.search(r'fill="url\(#[0-9a-f]{8}-validGradient\)"', out)


def test_completeness_pass_common_presentation_attrs_are_allowed():
    """Found live, 2026-08-25: a real Gemini-authored diagram reached for
    stroke-opacity on a <path>, then letter-spacing on a <text> -- both
    completely ordinary SVG presentation attributes, same shape as
    opacity/font-size (already allowed) -- and got rejected for gaps in
    the allowlist, not anything the validator is supposed to guard
    against. Two unrelated gaps in a row -> a completeness pass, not
    another one-off patch: every standard presentation attribute
    realistically relevant to diagram content, added once."""
    out = _render_freeform_canvas({**_base(
        elements=[{"tag": "path", "d": "M0 0 L1 1", "stroke": "#000",
                   "stroke_opacity": 0.5, "fill_opacity": 0.8,
                   "stroke_linecap": "round", "stroke_linejoin": "round",
                   "stroke_miterlimit": 4, "stroke_dashoffset": 2,
                   "fill_rule": "evenodd", "visibility": "visible",
                   "display": "inline"}])})
    assert REJECTED not in out
    for frag in ('stroke-opacity="0.5"', 'fill-opacity="0.8"',
                 'stroke-linecap="round"', 'stroke-linejoin="round"',
                 'stroke-miterlimit="4"', 'stroke-dashoffset="2"',
                 'fill-rule="evenodd"', 'visibility="visible"', 'display="inline"'):
        assert frag in out, frag


def test_completeness_pass_text_presentation_attrs_are_allowed():
    out = _render_freeform_canvas({**_base(
        elements=[{"tag": "text", "x": 0, "y": 0, "text": "hi",
                   "font_style": "italic", "letter_spacing": "0.05em",
                   "word_spacing": "0.1em", "text_decoration": "underline",
                   "dominant_baseline": "middle"}])})
    assert REJECTED not in out
    for frag in ('font-style="italic"', 'letter-spacing="0.05em"',
                 'word-spacing="0.1em"', 'text-decoration="underline"',
                 'dominant-baseline="middle"'):
        assert frag in out, frag


def test_marker_start_mid_end_allowed_and_id_namespaced():
    """Gemini's own review of the completeness pass flagged arrowheads as
    the one genuinely common remaining gap. Same url(#fragment)-only
    value shape and id-namespacing treatment as fill/stroke already get --
    proven here, not just declared."""
    elements = [
        {"tag": "defs", "children": [
            {"tag": "marker", "id": "arrow", "marker_width": 6, "marker_height": 6,
             "ref_x": 3, "ref_y": 3, "orient": "auto",
             "children": [{"tag": "path", "d": "M0 0 L6 3 L0 6 Z"}]},
        ]},
        {"tag": "line", "x1": 0, "y1": 0, "x2": 10, "y2": 10,
         "stroke": "#000", "marker_end": "url(#arrow)"},
    ]
    out = _render_freeform_canvas({**_base(elements=elements)})
    assert REJECTED not in out
    m = re.search(r'id="([0-9a-f]{8}-arrow)"', out)
    assert m
    assert f'marker-end="url(#{m.group(1)})"' in out
    assert 'marker-end="url(#arrow)"' not in out


def test_marker_start_external_url_rejected():
    out = _render_freeform_canvas({**_base(
        elements=[{"tag": "line", "x1": 0, "y1": 0, "x2": 1, "y2": 1,
                   "marker_start": "url(http://evil.example/arrow.svg)"}])})
    assert REJECTED in out


def test_pattern_gradient_marker_transform_and_focal_attrs_are_allowed():
    """Third live allowlist gap in a row for the reference-definition tags
    specifically (linearGradient/radialGradient/marker/pattern) -- found
    2026-08-25: patternTransform rejected on a real diagram needing a
    repeating brick pattern. Completing the whole group, not patching one
    more attribute reactively."""
    elements = [
        {"tag": "defs", "children": [
            {"tag": "pattern", "id": "bricks", "width": 10, "height": 10,
             "pattern_units": "userSpaceOnUse", "pattern_transform": "rotate(15)",
             "children": [{"tag": "rect", "x": 0, "y": 0, "width": 5, "height": 5}]},
            {"tag": "linearGradient", "id": "g1", "x1": 0, "y1": 0, "x2": 1, "y2": 0,
             "gradient_transform": "scale(1.5)", "spread_method": "reflect",
             "children": [{"tag": "stop", "offset": "0%", "stop_color": "#fff"}]},
            {"tag": "radialGradient", "id": "g2", "cx": 0.5, "cy": 0.5, "r": 0.5,
             "fx": 0.4, "fy": 0.4, "fr": 0.1, "gradient_transform": "rotate(30)",
             "children": [{"tag": "stop", "offset": "0%", "stop_color": "#000"}]},
            {"tag": "marker", "id": "arrow", "marker_width": 6, "marker_height": 6,
             "marker_units": "strokeWidth", "orient": "auto",
             "children": [{"tag": "path", "d": "M0 0 L6 3 Z"}]},
        ]},
        {"tag": "rect", "x": 0, "y": 0, "width": 10, "height": 10, "fill": "url(#bricks)"},
    ]
    out = _render_freeform_canvas({**_base(elements=elements)})
    assert REJECTED not in out
    for frag in ('patternTransform="rotate(15)"', 'gradientTransform="scale(1.5)"',
                 'spreadMethod="reflect"', 'fx="0.4"', 'fy="0.4"', 'fr="0.1"',
                 'markerUnits="strokeWidth"'):
        assert frag in out, frag


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


# ── Gemini security review findings, 2026-08-25 ─────────────────────────────

def test_two_instances_on_same_page_get_non_colliding_ids():
    """Two SEPARATE freeform_canvas renders, each defining id="grad1" for a
    gradient referenced via fill="url(#grad1)" -- without namespacing, both
    would emit the literal id "grad1" and a browser's global id lookup could
    resolve either diagram's reference against the OTHER diagram's element."""
    elements = [
        {"tag": "defs", "children": [
            {"tag": "linearGradient", "id": "grad1", "x1": 0, "y1": 0, "x2": 1, "y2": 0,
             "children": [{"tag": "stop", "offset": "0%", "stop_color": "#fff"}]},
        ]},
        {"tag": "rect", "x": 0, "y": 0, "width": 10, "height": 10, "fill": "url(#grad1)"},
    ]
    out_a = _render_freeform_canvas({**_base(elements=elements)})
    out_b = _render_freeform_canvas({**_base(
        summary="A different diagram entirely.", elements=elements)})
    id_a = re.search(r'id="([0-9a-f]{8}-grad1)"', out_a).group(1)
    id_b = re.search(r'id="([0-9a-f]{8}-grad1)"', out_b).group(1)
    assert id_a != id_b
    # each render's own fill reference points at ITS OWN namespaced id, not
    # the literal "grad1" and not the other render's id
    assert f'url(#{id_a})' in out_a and f'url(#{id_b})' in out_b
    assert 'url(#grad1)' not in out_a and 'url(#grad1)' not in out_b


def test_viewbox_with_embedded_quote_is_rejected_not_just_escaped():
    out = _render_freeform_canvas({**_base(
        viewbox='0 0 10 10" onload="alert(1)',
        elements=[{"tag": "rect", "x": 0, "y": 0, "width": 1, "height": 1}])})
    assert REJECTED in out


def test_background_javascript_scheme_is_rejected():
    out = _render_freeform_canvas({**_base(
        background="javascript:alert(1)",
        elements=[{"tag": "rect", "x": 0, "y": 0, "width": 1, "height": 1}])})
    assert REJECTED in out


def test_background_valid_hex_is_allowed():
    out = _render_freeform_canvas({**_base(
        background="#0f172a",
        elements=[{"tag": "rect", "x": 0, "y": 0, "width": 1, "height": 1}])})
    assert REJECTED not in out
    assert 'fill="#0f172a"' in out


def test_bare_external_url_in_fill_is_rejected_defense_in_depth():
    """Not exploitable in current browsers (fill requires <paint> grammar,
    a bare URL isn't one) -- rejected anyway so safety doesn't depend on
    today's UA parsing behaviour, per Gemini's hardening recommendation."""
    out = _render_freeform_canvas({**_base(
        elements=[{"tag": "rect", "x": 0, "y": 0, "width": 1, "height": 1,
                   "fill": "http://evil.example/track.png"}])})
    assert REJECTED in out


def test_mailto_scheme_in_attribute_value_is_rejected():
    out = _render_freeform_canvas({**_base(
        elements=[{"tag": "rect", "x": 0, "y": 0, "width": 1, "height": 1,
                   "fill": "mailto:x@example.com"}])})
    assert REJECTED in out
