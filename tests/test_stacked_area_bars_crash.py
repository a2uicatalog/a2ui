"""I64: the stacked_area bar list (until 2026-10-21 the default; since D22 it is `layout: "bars"`) raised ZeroDivisionError on all-zero data and TypeError on a text
cell in Python (the GAS twin renders both without throwing). A renderer must never throw on a payload. Payloads that rendered
before must render byte for byte as before (hashes captured from the pre-fix code, 2026-10-21)."""
from __future__ import annotations

import hashlib

import pytest

from test_motion_atoms import _py

BEFORE = {
    "quarters": ({"type": "stacked_area", "title": "Workloads", "labels": ["Q1", "Q2", "Q3", "Q4"],
                  "series": [{"label": "Enterprise", "data": [10, 25, 45, 60], "color": "#00f2ff"}, {"label": "SMB", "data": [5, 10, 12, 20]}]}, None),
    "short_series": ({"type": "stacked_area", "labels": ["a", "b", "c"], "series": [{"label": "A", "data": [1, 2]}, {"label": "B", "data": [3, 1, 2]}]}, None),
}


def _h(s):
    return hashlib.sha256(s.encode()).hexdigest()


@pytest.mark.parametrize("payload", [
    {"type": "stacked_area", "labels": ["a", "b"], "series": [{"label": "A", "data": [0, 0]}]},
    {"type": "stacked_area", "labels": ["a", "b"], "series": [{"label": "A", "data": [1, "x"]}]},
    {"type": "stacked_area", "labels": ["a", "b"], "series": [{"label": "A", "data": [None, True]}, {"label": "B", "data": [{"k": 1}, [2]]}]},
    {"type": "stacked_area", "labels": ["a"], "series": [{"label": "A", "data": [float("nan")]}]},
])
def test_the_bar_list_never_throws_and_never_prints_nan(payload):
    h = _py({**payload, "layout": "bars"})
    assert "NaN" not in h.split("title=")[0] and "inf%" not in h and "nan%" not in h
    assert 'width:0.0%' in h or 'width:' in h


def test_payloads_that_rendered_before_are_unchanged_under_layout_bars():
    got = {k: _h(_py({**b, "layout": "bars"})) for k, (b, _) in BEFORE.items()}
    assert got == EXPECTED, got


EXPECTED = {'quarters': '6ca14a91710389eb6a41caea1f28913945ca369619bea6a75f4b657d2716aa89', 'short_series': '79588fa9efa390a26ff1cd6d9462ddc68d22b6c020e1f8572ee02b51e6870f04'}
