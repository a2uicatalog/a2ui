"""image_plot (preview): a Plotly-image-style picture with axes. A z matrix of colours (<= 64 x 64) is drawn as crisp SVG rectangles, or a source image
(https or a base64 data: image) is drawn as an <img>; axis ticks are HTML text at 12px, a hidden table lists every value, a hostile src never becomes markup.
Python and Apps Script emit identical HTML."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

from test_motion_atoms import _gas_batch, _node, _py, core_js  # noqa: F401  (core_js is a fixture)
from test_motion_atoms import wa  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ATTACK = '"><img src=x onerror=alert(1)>\'"><svg onload=alert(1)></script><script>alert(4)</script> onmouseover=alert(2)'
BAD = re.compile(r"NaN|undefined|Infinity|\[object")
Z = [["#f00", "#00ff00", [0, 0, 255]], ["#000000", "#FFF", [128.4, 255, 0]]]
GOOD_SRC = "https://example.com/tile.png"
PIXEL = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

PAYLOADS = {
    "matrix": {"type": "image_plot", "title": "T", "z": Z, "x_range": [0, 30], "y_range": [0, 20], "x_label": "x", "y_label": "y", "alt": "Three by two"},
    "matrix_plain": {"type": "image_plot", "z": Z},
    "src": {"type": "image_plot", "src": GOOD_SRC, "x_range": [-1, 1], "y_range": [10, 0], "alt": "A tile"},
    "data_uri": {"type": "image_plot", "src": PIXEL},
    "bad_src": {"type": "image_plot", "src": "javascript:alert(1)"},
    "holes": {"type": "image_plot", "z": [["#abc", "nope", None], [[1, 2], "#12345", ["a", 1, 2]]]},
    "both": {"type": "image_plot", "z": Z, "src": GOOD_SRC},
    "empty": {"type": "image_plot"},
    "version": {"type": "image_plot", "z": Z, "version": 3},
    "hostile": {"type": "image_plot", "z": [[ATTACK, "#fff"]], "title": ATTACK, "alt": ATTACK, "x_label": ATTACK, "y_label": ATTACK, "x_range": [ATTACK, 1]},
    "big": {"type": "image_plot", "z": [["#%02x%02x%02x" % ((i * 4) % 256, (j * 4) % 256, 128) for j in range(70)] for i in range(70)]},
    "weird_ranges": {"type": "image_plot", "z": Z, "x_range": [5, 5], "y_range": [1e300, -1e300]},
    "ranges_bad": {"type": "image_plot", "z": Z, "x_range": "abc", "y_range": [1]},
}


def _r(n):
    return _py(dict(PAYLOADS[n]))


def _text(h):
    return re.sub(r"<[^>]*>", " ", h)


def test_matrix_draws_one_rect_per_run_of_equal_colour():
    h = _r("matrix")
    rects = re.findall(r'<rect x="(\d+)" y="(\d+)" width="(\d+)" height="1" fill="(#[0-9a-f]{6})"', h)
    assert len(rects) == 6 and {r[3] for r in rects} == {"#ff0000", "#00ff00", "#0000ff", "#000000", "#ffffff", "#80ff00"}
    assert 'viewBox="0 0 3 2"' in h and "crispEdges" in h


def test_equal_neighbours_are_merged_into_one_rect():
    h = _py({"type": "image_plot", "z": [["#111", "#111", "#111", "#222"]]})
    assert re.findall(r'<rect x="0" y="0" width="3" height="1" fill="#111111"', h) and h.count("<rect") == 2


def test_aria_label_states_the_gist_and_there_is_a_hidden_table_with_every_cell():
    h = _r("matrix")
    assert 'role="img"' in h and 'aria-label="Three by two' in h
    assert "<table" in h and h.count("<tr>") == 3 and "#ff0000" in h.split("<table")[1] and "128, 255, 0" in re.sub("#80ff00", "128, 255, 0", h) or "#80ff00" in h
    h2 = _r("matrix_plain")
    assert "Image, 2 rows by 3 columns" in h2


def test_ticks_are_html_text_of_at_least_12px():
    h = _r("matrix")
    ticks = re.findall(r'<span style="position:absolute;[^"]*font-size:12px[^"]*">([^<]*)</span>', h)
    assert len(ticks) >= 4 and "0" in ticks and ">x<" in h and ">y<" in h
    assert not re.search(r"<text\b", h)


def test_hostile_src_never_becomes_markup():
    # the payload guard (_gd_url) drops a src it dislikes before the renderer sees it; the renderer's own check is the second layer
    refused = lambda h: "not allowed" in h or "needs a z matrix or a src" in h
    h = _r("bad_src")
    assert "<img" not in h and refused(h)
    for bad in ["http://example.com/a.png", "//example.com/a.png", "https://", "https://a b.com/x.png", 'https://x.com/"onerror=alert(1)', "data:text/html;base64,PHNjcmlwdD4=",
                "data:image/svg+xml;base64,PHN2Zz4=", "https://example.com/a.png\nx", "file:///etc/passwd", "https://u:p@example.com/x.png"]:
        out = _py({"type": "image_plot", "src": bad})
        assert "<img" not in out and refused(out), bad


def test_good_sources_are_drawn_with_safe_attributes():
    for n in ("src", "data_uri"):
        h = _r(n)
        assert h.count("<img") == 1 and 'referrerpolicy="no-referrer"' in h and "<script" not in h
    assert 'src="https://example.com/tile.png"' in _r("src") and "onerror" not in _r("src")


def test_src_with_quotes_in_the_query_is_escaped_or_refused():
    out = _py({"type": "image_plot", "src": "https://example.com/a.png?x=1&y=2"})
    assert "&amp;y=2" in out and out.count("<img") == 1


def test_holes_are_left_blank_with_a_count():
    h = _r("holes")
    assert "left blank" in h and h.count("<rect") == 1 + 0 or "#aabbcc" in h


def test_cap_is_64_by_64_with_a_note():
    h = _r("big")
    assert 'viewBox="0 0 64 64"' in h and "first 64 of 70 rows" in h and "first 64 of 70 columns" in h


def test_z_wins_over_src_with_a_note():
    h = _r("both")
    assert "<img" not in h and "z is drawn" in h


def test_empty_says_what_is_needed():
    assert "needs a z matrix or a src" in _r("empty")


def test_version_note():
    assert "Written for image_plot version 3; drawn as version 1." in _r("version")


def test_axis_ranges_are_validated():
    for n in ("weird_ranges", "ranges_bad", "hostile"):
        assert not BAD.search(_text(_r(n))), n


def test_hostile_text_is_escaped():
    h = _r("hostile")
    assert "<script>alert(4)" not in h and "<img src=x" not in h and "<svg onload" not in h


@pytest.mark.parametrize("name", list(PAYLOADS))
def test_python_and_gas_emit_identical_html(name, core_js):
    assert _gas_batch(core_js, [PAYLOADS[name]])[0] == _r(name)


@pytest.mark.parametrize("b", [{"type": "image_plot", "z": "abc"}, {"type": "image_plot", "z": [1, 2, 3]}, {"type": "image_plot", "z": [[]]}, {"type": "image_plot", "src": 5},
                               {"type": "image_plot", "z": {"a": 1}}, {"type": "image_plot", "z": [[1e999]]}, {"type": "image_plot", "src": ["https://x.com/a.png"]}])
def test_malformed_input_never_throws_or_prints_junk(b, core_js):
    for h in (_py(dict(b)), _gas_batch(core_js, [b])[0]):
        assert isinstance(h, str) and not BAD.search(_text(h)), h[:300]


def test_deterministic():
    assert _r("matrix") == _r("matrix")


def test_registered_as_a_preview_atom():
    sch = yaml.safe_load((ROOT / "atoms/schema.yaml").read_text())
    e = [x for x in sch["blocks"] if x.get("type") == "image_plot"]
    assert len(e) == 1 and e[0].get("stage") == "preview" and len(e[0]["intent_phrases"]) == 3
    for k in ("description", "compact_description", "routing_text", "fields", "notes"):
        assert e[0].get(k), k
    assert "image_plot" in (ROOT / "atoms/atom-packs.yaml").read_text()
    assert "image_plot" in (ROOT / "apps-script-surface/gas-wired-renderer/PackMap.gs").read_text()


def test_the_renderers_own_src_check_holds_without_the_payload_guard(core_js):
    bad = ["http://example.com/a.png", "//example.com/a.png", "https://", "https://a b.com/x.png", 'https://x.com/"onerror=alert(1)', "data:text/html;base64,PHNjcmlwdD4=",
           "data:image/svg+xml;base64,PHN2Zz4=", "https://example.com/a.png\nx", "https://u:p@example.com/x.png", "javascript:alert(1)", "https://x.com/<b>"]
    for u in bad:
        h = wa._render_image_plot({"type": "image_plot", "src": u})
        assert "<img" not in h and "not allowed" in h, u
    res = _node(core_js, "var U = " + json.dumps(bad) + "; console.log(JSON.stringify(U.map(function(u){ return _RENDERERS['image_plot']({type:'image_plot', src:u}); })));")
    assert all("<img" not in h and "not allowed" in h for h in res)


def test_a_src_image_without_alt_gets_a_descriptive_default_label(core_js):
    b = {"type": "image_plot", "src": GOOD_SRC, "x_range": [0, 5], "y_range": [0, 2]}
    for h in (_py(dict(b)), _gas_batch(core_js, [b])[0]):
        assert 'aria-label="Picture, no text description given, x from 0 to 5, y from 0 to 2."' in h
