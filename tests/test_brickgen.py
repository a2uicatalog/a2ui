"""scripts/brick_models/brickgen.py -- material-context-aware architecture seam (cozy-forging-newt.md Track B
item 1). tile()/build() accept an optional material_profile carrying max_run/bond_period, defaulting to
LEGO_MATERIAL_PROFILE (max_run=4, bond_period=4). No second material profile exists yet -- these tests prove
(a) the default path is byte-identical to the pre-seam behaviour, and (b) the seam itself actually works
(a different profile really does change tiling), not just that it was threaded through without effect.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "brick_models"))

from brickgen import LEGO_MATERIAL_PROFILE, tile  # noqa: E402


def _row_cells(length, colour="#ffffff"):
    """A single straight row of `length` same-coloured cells along x, one layer (y=0), one row (z=0)."""
    return {(x, 0, 0): colour for x in range(length)}


def test_default_profile_matches_pre_seam_behaviour():
    """No material_profile passed -> identical to LEGO's hardcoded max_run=4/bond_period=4."""
    cells = _row_cells(9)
    box = (0, 8, 0, 0, 0, 0)
    default = tile(cells, box)
    explicit_lego = tile(cells, box, LEGO_MATERIAL_PROFILE)
    assert default == explicit_lego
    # A 9-long row tiles into runs capped at 4 studs, staggered on a mod-4 boundary (par=0 on y=0):
    # boundaries land at x=4 and x=8, giving widths [4, 4, 1].
    assert [b["w"] for b in default] == [4, 4, 1]


def test_material_profile_actually_changes_tiling():
    """A different max_run must produce different output -- proves the seam has real effect, not just plumbing."""
    cells = _row_cells(9)
    box = (0, 8, 0, 0, 0, 0)
    default = tile(cells, box)
    other = tile(cells, box, {"max_run": 2, "bond_period": 2})
    assert default != other
    # max_run=2 caps every run at 2 studs: widths [2, 2, 2, 2, 1].
    assert [b["w"] for b in other] == [2, 2, 2, 2, 1]


def test_bond_period_changes_stagger_between_layers():
    """par (the inter-layer stagger) is derived from bond_period, not an independent constant -- verify it
    actually tracks a non-default bond_period rather than silently staying LEGO's half-of-4."""
    cells = {(x, y, 0): "#ffffff" for y in (0, 1) for x in range(6)}
    box = (0, 5, 0, 1, 0, 0)
    bricks = tile(cells, box, {"max_run": 6, "bond_period": 6})
    by_y = {y: [b for b in bricks if b["y"] == y] for y in (0, 1)}
    # bond_period=6 staggers layer 1 by 6//2=3 studs relative to layer 0's run boundaries.
    assert by_y[0][0]["w"] == 6
    assert [b["x"] for b in by_y[1]] == [0, 3]
