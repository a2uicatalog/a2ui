"""stacked_area in its DEFAULT layout (the zero-baseline area chart, D22) in a real browser: the picture fills its plot, the value axis and x labels never
overlap or clip, the legend stays inside, and the chart is never wider than its container. Same harness and widths as
tests/test_stacked_area_offset_layout_box.py (320 / 650 / 1200 / 1400 px and a 300 px grid cell)."""
from __future__ import annotations

import json

import pytest

from test_histogram_layout_box import CHROME, WIDTHS, _run
from test_motion_atoms import _gas_batch, _py, core_js  # noqa: F401
from test_stacked_area_offset import ATTACK, BASE, CASES, _block
from test_stacked_area_offset_layout_box import HARNESS

pytestmark = pytest.mark.skipif(not CHROME, reason="needs chromium")

PAYLOADS = {
    "showcase": BASE["showcase"],
    "mrr_thousands": BASE["mrr"],
    "stage_deck": BASE["stage_deck"],
    "three_by_four": _block(CASES["three_by_four"]["values"], title="Share of revenue"),
    "twelve_series": _block(CASES["series_twelve_pts_ten"]["values"]),
    "sixty_points": _block(CASES["series_four_pts_forty"]["values"]),
    "huge": _block([[1e12, 2e12, 5e11], [1e11, 3e11, 2e11]]),
    "tiny": _block([[0.001, 0.002, 0.004], [0.0005, 0.001, 0.002]]),
    "decimals": _block(CASES["decimals"]["values"]),
    "all_zero": _block([[0, 0, 0], [0, 0, 0]]),
    "text_cells": {"type": "stacked_area", "labels": ["a", "b", "c"], "series": [{"label": "x", "data": [1, "x", None]}, {"label": "y", "data": [True, 5, 6]}]},
    "long_labels": {"type": "stacked_area", "labels": ["January 2026 (provisional)", "February 2026 (provisional)", "March 2026 (provisional)", "April 2026 (provisional)"],
                    "series": [{"label": "A very long series name that keeps going", "data": [3, 4, 5, 6]}, {"label": "B", "data": [1, 1, 2, 3]}]},
    "hostile": {"type": "stacked_area", "title": ATTACK, "labels": [ATTACK, "b", "c"], "series": [{"label": ATTACK, "data": [1, 2, 3], "color": ATTACK}]},
}


@pytest.mark.parametrize("renderer", ["python", "gas"])
def test_default_area_layers_axes_and_legend_never_overlap_clip_or_widen_the_container(renderer, core_js):
    html = {n: _py(b) for n, b in PAYLOADS.items()} if renderer == "python" else dict(zip(PAYLOADS, _gas_batch(core_js, list(PAYLOADS.values()))))
    res = _run(html, harness=HARNESS)
    assert len(res) == len(PAYLOADS) * len(WIDTHS)
    bad = {r["id"]: r["errs"] for r in res if r["errs"]}
    assert not bad, json.dumps(bad, indent=1)[:3000]
    by = {r["id"]: r for r in res}
    assert by["showcase-w320"]["xlabels"] <= by["showcase-w1200"]["xlabels"] and by["showcase-w1200"]["xlabels"] >= 3
    assert all(r["ylabels"] >= 1 for r in res)                                           # the default layout always has a value axis (a lone 0 when all zero)
    assert by["three_by_four-w650"]["ylabels"] >= 3 and by["all_zero-w650"]["ylabels"] == 1
    assert all(r["layers"] == html[r["id"].split("-")[0]].count("<polygon") for r in res)
