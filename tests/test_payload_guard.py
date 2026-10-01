"""Payload guard (2026-10-01): the check that runs before every renderer, in both twins.

Fields whose NAME says they hold a CSS value, a number, a URL, an id or an icon are VALIDATED (kept byte-for-byte or dropped, so the
atom falls back to its default); text is escaped by each renderer. Plus the two script-safe JSON helpers and the markdown shim.
Proven three ways: GAS/Python parity over hostile and legitimate values, legitimate values survive unchanged, hostile ones never do.
"""
from __future__ import annotations

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

from renderers import web_article as wa  # noqa: E402

LS, PS = chr(0x2028), chr(0x2029)

LEGIT = {
    "accent": ["#6366f1", "#fff", "rebeccapurple", "var(--accent)", "rgb(0 0 0 / 50%)", "hsl(220, 90%, 56%)", "transparent",
               "linear-gradient(120deg, #6366f1, #22d3ee)", "color-mix(in srgb, #fff 20%, transparent)"],
    "size": ["sm", "lg", "100px", "1.5rem", "clamp(1rem, 2vw, 3rem)", "calc(100% - 12px)"],
    "align": ["left", "center"], "gradient": ["radial-gradient(circle at 50% 0%, #fff, #000)"],
    "speed": ["slow", "1.5", "200ms", "-3"], "duration": ["slow", "2.0"], "delay": ["0.3s"],
    "url": ["https://a2uicatalog.ai/atoms?q=stat#x", "/docs/", "?nav=lesson1", "mailto:a@b.c", "tel:+331", "data:image/png;base64,iVBOR"],
    "image_url": ["https://x.y/z.png"], "link": ["Read more", "https://x.y"],
    "course_id": ["course-101", "a.b:c"], "id": ["fn1", "https://x.y/z?a=1&b=2"], "nav_slug": ["lesson-1"],
    "icon": ["🏆", "check", "&#9888;", "→"],
}
HOSTILE = {
    "accent": ["red;background:url(javascript:alert(1))", '#fff" onmouseover="alert(1)', "expression(alert(1))", "url(x.png)",
               "#fff}</style><script>alert(1)</script>", "a/*x*/b", "a\\62", "x" * 400, "a" + LS + "b", "#fff!important"],
    "size": ['1" onload="alert(1)', "1;top:0", "attr(data-x)"],
    "speed": ["1;alert(1)", "alert(1)", "Slow Speed"],
    "url": ["javascript:alert(1)", " JaVaScRiPt:alert(1)", "vbscript:x", "data:text/html,<b>", 'https://x.y" onclick="a', "https://x y"],
    "href": ["java\tscript:alert(1)"], "link": ["https://x.y'><b>"],
    "course_id": ["a b", "a<b>", "a'b"], "icon": ['"><img src=x onerror=alert(1)>', "a'b", "x" * 80],
}


@pytest.fixture(scope="module")
def core_js():
    bundle = gen.build_bundle()
    return [b for b in re.findall(r"<script>\n(.*?)\n</script>", bundle, re.S) if "a2ui-core" in b[:300]][0]


def _node(core_js: str, body: str):
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "d.js"
        d.write_text("global.window = global;\n" + core_js + "\n" + body)
        proc = subprocess.run(["node", str(d)], capture_output=True, text=True, timeout=60)
        assert proc.returncode == 0, proc.stderr[-1500:]
        return json.loads(proc.stdout.strip().splitlines()[-1])


def _corpus():
    blocks = []
    for k, vals in list(LEGIT.items()) + list(HOSTILE.items()):
        for v in vals:
            blocks.append({k: v})
            blocks.append({"items": [{k: v, "label": "x"}], k: [v, 3]})
    blocks += [
        {"rows": [["Apple", "1"]], "columns": ["Price ($)", "Name: x"], "count": "51 atoms", "total": "$124.00", "current_title": "Intro"},
        {"colors": [{"name": "A", "hex": "#fff"}], "scale": {"min": 1, "max": 9}, "accent": [{"x": "<b>"}], "size": {"w": 1}},
        {"reactions": ["🔥", '"><b>'], "colours": ["#fff", "url(x)"], "enter": {"effect": "rise", "duration": "slow"}},
    ]
    return blocks


def test_guard_twins_agree(core_js):
    blocks = _corpus()
    gas = _node(core_js, f"var B = {json.dumps(blocks)}; console.log(JSON.stringify(B.map(function(b){{ return _gdClean(b, ''); }})));")
    for b, g in zip(blocks, gas):
        assert g == wa._gd_clean(b, ""), json.dumps(b)[:200]


def test_legitimate_values_pass_byte_for_byte():
    for k, vals in LEGIT.items():
        for v in vals:
            assert wa._gd_clean({k: v}, "") == {k: v}, (k, v)


def test_hostile_values_never_survive():
    for k, vals in HOSTILE.items():
        for v in vals:
            assert k not in wa._gd_clean({k: v}, ""), (k, v)


def test_structured_fields_keep_their_structure():
    b = {"rows": [["Apple", "1"]], "columns": ["Price ($)"], "count": "51 atoms", "total": "$124.00", "current_title": "Intro",
         "colors": [{"name": "A", "hex": "#fff"}], "scale": {"min": 1, "max": 9}}
    assert wa._gd_clean(b, "") == b


def test_single_value_fields_never_hold_objects_but_plural_colour_lists_may_hold_structure():
    out = wa._gd_clean({"accent": [{"x": "<b>"}, "#fff", "red;x", 3], "size": {"w": 1}, "icon": ["🏆", '"><b>'],
                        "colors": [{"name": "A", "hex": "#fff"}], "scale": {"min": 1, "max": 9}}, "")
    assert out == {"accent": ["#fff", 3], "icon": ["🏆"], "colors": [{"name": "A", "hex": "#fff"}], "scale": {"min": 1, "max": 9}}


def test_every_renderer_is_guarded_and_still_motion_wrapped():
    wa._mo_install()
    wa._gd_install()
    assert all(getattr(f, "_gd", False) for k, f in wa._RENDERERS.items() if k not in wa._GD_SELF_VALIDATED)
    assert all(getattr(f, "_mo", False) for f in wa._RENDERERS.values())
    # the exemption is exactly the atoms that run their own real parser + allowlist
    assert wa._GD_SELF_VALIDATED == {"freeform_canvas", "agent_sketchpad"}


def test_script_safe_json_twins_agree(core_js):
    vals = ["</script><script>alert(1)</script>", "a'b&c>d", "x" + LS + "y" + PS, {"k": ["<", 1, None, True]}, "é ☃ 🏆"]
    gas = _node(core_js, f"var V = {json.dumps(vals)}; console.log(JSON.stringify(V.map(function(v){{ return _jsJson(v); }})));")
    for v, g in zip(vals, gas):
        py = wa._js_json(v, separators=(",", ":"), ensure_ascii=False)
        assert g == py, (v, g, py)
        assert json.loads(py) == v
        assert not re.search("[<>&'" + LS + PS + "]", py)


def test_markdown_shows_raw_html_as_text_and_drops_unsafe_links():
    html = wa._md.markdown('<img src=x onerror=alert(1)> [a](javascript:alert(2)) ![i](javascript:alert(3)) [ok](https://x.y)\n\n'
                           '<script>alert(4)</script>', extensions=["tables", "fenced_code"])
    assert "<img src=x" not in html and "<script>" not in html and "javascript:" not in html
    assert '<a href="https://x.y">ok</a>' in html
