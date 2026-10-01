"""Locks in declaration_prealable/dp5_elevation.py's block-coursing math and SVG output directly,
mirroring tests/test_blender_view_math.py's own hand-computed-assertion style.
"""
import pytest

from declaration_prealable import dp5_elevation as dp5
from declaration_prealable.project_schema import DPProject, PlotGeometry, WallSpec


def _project(**wall_kwargs):
    wall = WallSpec(**wall_kwargs)
    return DPProject(commune="Exemple-sur-Seine", address="12 rue des Tilleuls",
                      wall=wall, plot=PlotGeometry(), date_iso="2026-10-01")


def test_wall_coursing_exact_multiple_of_block_size():
    # parpaing200: unit_l=510mm, course_h=210mm -- 2040mm / 510mm = exactly 4, 630mm / 210mm = exactly 3
    calc = dp5.wall_coursing("parpaing200", length_m=2.04, height_m=0.63)
    assert calc["per_course"] == 4
    assert calc["courses"] == 3
    assert calc["actual_w_mm"] == 2040
    assert calc["actual_h_mm"] == 630


def test_wall_coursing_rounds_up_partial_course():
    # 2050mm requested width needs 5 units of 510mm (2550mm actual), not 4 (2040mm, which would be short)
    calc = dp5.wall_coursing("parpaing200", length_m=2.05, height_m=0.21)
    assert calc["per_course"] == 5
    assert calc["actual_w_mm"] == 2550


def test_wall_coursing_unknown_block_falls_back_to_parpaing200():
    calc = dp5.wall_coursing("not-a-real-block", length_m=1.0, height_m=1.0)
    assert calc["block"] is dp5.BLOCKS["parpaing200"]


def test_dp5_threshold_is_the_real_sourced_two_metres():
    # See README.md -- service-public.gouv.fr/particuliers/vosdroits/F3131, not
    # renderers/web_article.py's own explicitly-illustrative WALL_ADVISORY_HEIGHT_M.
    assert dp5.DP_WALL_HEIGHT_THRESHOLD_M == 2.0


def test_dp5_svg_contains_finish_label_callout():
    project = _project(finish_label="Enduit lisse peint en blanc")
    svg = dp5.render_dp5_svg(project)
    assert "Enduit lisse peint en blanc" in svg
    assert "<svg" in svg and "</svg>" in svg


def test_dp5_svg_escapes_finish_label():
    project = _project(finish_label='Enduit <taloché> & "gris"')
    svg = dp5.render_dp5_svg(project)
    assert "<taloché>" not in svg
    assert "&lt;taloché&gt;" in svg


def test_dp5_svg_shows_height_advisory_when_at_or_above_threshold():
    tall = _project(height_m=2.0)
    short = _project(height_m=1.0)
    assert "DP obligatoire" in dp5.render_dp5_svg(tall)
    assert "DP obligatoire" not in dp5.render_dp5_svg(short)


def test_dp5_svg_contains_dimension_labels_in_metres():
    project = _project(length_m=3.0, height_m=1.5, block_id="parpaing200")
    svg = dp5.render_dp5_svg(project)
    calc = dp5.wall_coursing("parpaing200", 3.0, 1.5)
    assert f'{calc["actual_w_mm"]/1000:.2f} m' in svg
    assert f'{calc["actual_h_mm"]/1000:.2f} m' in svg


def test_render_dp5_png_produces_a_real_png(tmp_path):
    pytest.importorskip("cairosvg", reason="optional rasterization dependency, see README.md")
    project = _project()
    out = tmp_path / "dp5.png"
    dp5.render_dp5_png(project, out, width=400)
    data = out.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
