"""The table atom's col_widths go into a style attribute, so each one is checked: a number followed by %, px or rem, nothing else.
Both renderers (Python web_article and the Apps Script twin) must keep the good widths and drop the rest (Opus review, 1 Nov 2026)."""
from __future__ import annotations

import re

import pytest

from test_gas_twins import _gas_batch
from test_motion_atoms import _py, core_js  # noqa: F401  (core_js is a fixture)

BASE = {"type": "table", "headers": ["a", "b", "c"], "rows": [["1", "2", "3"]]}
HOSTILE = [
    'x;background:url(https://evil.example/p)',
    '10%" onmouseover="alert(1)',
    '50%;position:fixed',
    'expression(alert(1))',
    '-5%', '12', 'auto', '1e9px', '<script>', '', None, 40, {'a': 1}, ['1%'],
]


def _widths(html: str) -> list[str]:
    return re.findall(r'<th style="[^"]*?width:([^;"]+);', html) + re.findall(r'<th style="width:([^;"]+);"', html)


def _both(core_js, block):
    return [_py(block), _gas_batch(core_js, [block])[0]]


def test_valid_widths_survive_in_both_renderers(core_js):
    for html in _both(core_js, dict(BASE, col_widths=["46%", "12.5px", "10rem"])):
        assert "table-layout:fixed" in html
        for w in ("46%", "12.5px", "10rem"):
            assert "width:" + w + ";" in html, html[:400]


@pytest.mark.parametrize("bad", HOSTILE)
def test_a_bad_width_is_dropped_in_both_renderers(core_js, bad):
    for html in _both(core_js, dict(BASE, col_widths=["30%", bad, "20%"])):
        assert "width:30%;" in html and "width:20%;" in html
        assert "evil.example" not in html and "onmouseover" not in html and "position:fixed" not in html
        assert "expression(" not in html and "<script>" not in html
        assert "width:-5" not in html and "width:1e9" not in html
        # exactly two widths reach the header cells; the bad one left no width at all
        assert len(re.findall(r"width:[^;\"]+;", html.split("<tbody>")[0])) - html.split("<tbody>")[0].count("width:100%;") == 2, html[:500]


def test_no_valid_width_means_automatic_layout(core_js):
    for html in _both(core_js, dict(BASE, col_widths=["evil;x", "auto"])):
        assert "table-layout:fixed" not in html


@pytest.mark.parametrize("notalist", ["50%", 7, {"0": "10%"}, True])
def test_col_widths_that_is_not_a_list_is_ignored(core_js, notalist):
    for html in _both(core_js, dict(BASE, col_widths=notalist)):
        assert "table-layout:fixed" not in html and "10%" not in html and "50%" not in html
