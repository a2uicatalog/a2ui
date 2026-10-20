"""decision_tree layout "tree" in a real browser: same checks, widths and harness as tests/test_org_chart_layout_box.py (the layout and boxes are org_chart's):
exactly one of the two layouts is visible, boxes never overlap or clip their text, connectors end on box edges, nothing is wider than its container
(320 / 600 / 650 / 1200 / 1400 / 2400 px and a 2-column grid), with and without a leaking page stylesheet; the outline fallback stays inside its container too."""
from __future__ import annotations

import pytest

from test_decision_tree_layout import DRAWN, PAYLOADS
from test_motion_atoms import _gas_batch, _py, core_js  # noqa: F401
from test_org_chart_layout_box import CHROME, WIDTHS, _run

pytestmark = pytest.mark.skipif(not CHROME, reason="needs chromium")


@pytest.mark.parametrize("leak", [False, True], ids=["clean", "leaking-stylesheet"])
def test_boxes_and_connectors_share_a_containing_block_at_every_width(leak, core_js):
    blocks = {n: _py(PAYLOADS[n]) for n in DRAWN}
    blocks.update({n + "_gas": _gas_batch(core_js, [PAYLOADS[n]])[0] for n in ("ship", "forest", "thirty_one", "long_labels")})
    res = _run(blocks, leak)
    assert len(res) == len(blocks) * (len(WIDTHS) + 1)
    bad = [(r["id"], r["errs"][:3]) for r in res if r["errs"] or not r["n"]]
    assert not bad, bad


def test_small_trees_fit_a_650px_column_top_down_and_a_wide_one_goes_left_to_right_in_a_narrow_column(core_js):
    res = {r["id"]: r for r in _run({"ship": _py(PAYLOADS["ship"]), "thirty_one": _py(PAYLOADS["thirty_one"]), "ship_gas": _gas_batch(core_js, [PAYLOADS["ship"]])[0]}, False)}
    for n in ("ship", "ship_gas"):
        assert res[n + "-w650"]["fits"] and res[n + "-w650"]["mode"] == "td", n
    assert res["thirty_one-w320"]["mode"] == "ltr" and res["thirty_one-w320"]["rootVisible"]
    assert res["thirty_one-w2400"]["mode"] == "td" and res["thirty_one-w2400"]["fits"]
