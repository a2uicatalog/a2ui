"""Locks in declaration_prealable/dp2_plan_masse.py's geometry math and SVG output directly,
mirroring tests/test_blender_view_math.py's own hand-computed-assertion style.
"""
import math

import pytest

from declaration_prealable import dp2_plan_masse as dp2
from declaration_prealable.project_schema import DPProject, PlotGeometry, WallSpec


def test_distance_point_to_segment_perpendicular_case():
    # point directly "above" the segment's midpoint -- shortest distance is the perpendicular
    d, nearest = dp2.distance_point_to_segment((5, 3), (0, 0), (10, 0))
    assert math.isclose(d, 3.0)
    assert nearest == (5.0, 0.0)


def test_distance_point_to_segment_clamps_to_endpoint():
    # point beyond the segment's end -- closest point is the endpoint, not an extrapolated line
    d, nearest = dp2.distance_point_to_segment((15, 4), (0, 0), (10, 0))
    assert math.isclose(d, math.hypot(5, 4))
    assert nearest == (10.0, 0.0)


def test_nearest_boundary_distance_square_plot():
    # 10x10 square boundary, point at (5, 5) (centre) is 5m from every edge
    square = [(0, 0), (10, 0), (10, 10), (0, 10)]
    d, _ = dp2.nearest_boundary_distance((5, 5), square)
    assert math.isclose(d, 5.0)


def test_nearest_boundary_distance_point_near_one_edge():
    square = [(0, 0), (10, 0), (10, 10), (0, 10)]
    d, nearest = dp2.nearest_boundary_distance((2, 1), square)
    assert math.isclose(d, 1.0)
    assert nearest == (2.0, 0.0)


def test_nearest_boundary_distance_empty_boundary_returns_none():
    d, nearest = dp2.nearest_boundary_distance((1, 1), [])
    assert d is None and nearest is None


def _project():
    wall = WallSpec(length_m=4.0, height_m=1.8)
    plot = PlotGeometry(
        boundary_points_m=[(0, 0), (12, 0), (12, 15), (0, 15)],
        existing_structures=[{"label": "Maison", "points_m": [(1, 1), (6, 1), (6, 6), (1, 6)]}],
        wall_points_m=[(0.5, 10.0), (4.5, 10.0)],
        north_angle_deg=15.0,
    )
    return DPProject(commune="Exemple-sur-Seine", address="12 rue des Tilleuls",
                      wall=wall, plot=plot, date_iso="2026-10-01")


def test_dp2_svg_contains_wall_length_label():
    svg = dp2.render_dp2_svg(_project())
    assert "4.00 m" in svg
    assert "Clôture à créer" in svg


def test_dp2_svg_contains_existing_structure_label():
    svg = dp2.render_dp2_svg(_project())
    assert "Maison" in svg


def test_dp2_svg_labels_do_not_use_paint_order():
    # Regression: cairosvg (used by render_dp2_png) does not support the CSS
    # paint-order property and silently paints stroke OVER fill, which made a
    # single paint-order="stroke" halo text element render fully invisible
    # (confirmed live 2026-10-01). Labels must use _text_with_halo's
    # two-element approach instead.
    svg = dp2.render_dp2_svg(_project())
    assert "paint-order" not in svg


def test_dp2_svg_handles_missing_geometry_without_crashing():
    empty = DPProject(commune="X", address="Y", wall=WallSpec(), plot=PlotGeometry(), date_iso="2026-10-01")
    svg = dp2.render_dp2_svg(empty)
    assert "<svg" in svg and "</svg>" in svg


def test_render_dp2_png_produces_a_real_png(tmp_path):
    pytest.importorskip("cairosvg", reason="optional rasterization dependency, see README.md")
    out = tmp_path / "dp2.png"
    dp2.render_dp2_png(_project(), out, width=400)
    data = out.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
