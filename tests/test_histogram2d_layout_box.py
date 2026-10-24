"""histogram2d in a real browser: it is drawn by the heatmap atom, so it must pass the heatmap's own layout checks (cells never overlap, labels >= 12px and
unclipped, never wider than the container) at 320 / 650 / 1200 / 1400 px and in a 300 px cell."""
from __future__ import annotations

import json

import pytest

from test_histogram_layout_box import CHROME, WIDTHS, _run
from test_motion_atoms import _gas_batch, _py, core_js  # noqa: F401

pytestmark = pytest.mark.skipif(not CHROME, reason="needs chromium")

from test_heatmap_layout_box import HARNESS

BLOCKS = {
    "small": {"type": "histogram2d", "x": [1, 1, 5, 5, 5, 3, 4], "y": [1, 1, 1, 5, 5, 2, 3], "nbinsx": 3, "nbinsy": 3, "title": "Small", "x_label": "x", "y_label": "y"},
    "blob": {"type": "histogram2d", "x": [(i * 37) % 101 + (i % 7) * 0.5 for i in range(400)], "y": [((i * 53) % 97) * 0.3 + (i % 5) for i in range(400)], "nbinsx": 8, "nbinsy": 6},
    "wide": {"type": "histogram2d", "x": [(i * 37) % 1009 * 0.01 for i in range(900)], "y": [(i * 53) % 997 * 1000.5 for i in range(900)], "nbinsx": 40, "nbinsy": 40},
    "flat": {"type": "histogram2d", "x": [3, 3, 3, 3], "y": [1, 2, 3, 4]},
    "bignum": {"type": "histogram2d", "x": [1e6 + i * 12345 for i in range(60)], "y": [i * 1e-4 for i in range(60)], "nbinsx": 10, "nbinsy": 10, "scale": "YlOrRd"},
}


@pytest.mark.parametrize("renderer", ["python", "gas"])
def test_drawn_grid_fits_at_every_width(renderer, core_js):
    html = {n: _py(dict(b)) for n, b in BLOCKS.items()} if renderer == "python" else dict(zip(BLOCKS, _gas_batch(core_js, list(BLOCKS.values()))))
    res = _run(html, harness=HARNESS)
    assert len(res) == len(BLOCKS) * len(WIDTHS)
    bad = {r["id"]: r["errs"] for r in res if r["errs"]}
    assert not bad, json.dumps(bad, indent=1)[:3000]
