"""wall_elevation -- a deterministic, AI-free masonry wall elevation atom.
No LLM anywhere in this render path: real semantic parameters in, real
course/cost/weight/build-time math out, ported faithfully from
wall-builder-agent (a real Gemini Enterprise A2A demo). Every number here
is independently verifiable by hand from the same formulas the renderer
itself uses -- these tests check the actual arithmetic, not just "it
rendered something"."""

import pytest

from renderers.web_article import (
    WALL_BLOCKS,
    WALL_BUILDERS_MAX,
    WALL_BUILDERS_MIN,
    WALL_DIM_MAX_M,
    WALL_DIM_MIN_M,
    _render_wall_elevation,
    _wall_build_days_curve,
    _wall_calc,
    _wall_snap,
    _wall_snap_builders,
)


def _base(**overrides):
    b = {"height_m": 2.0, "width_m": 3.0}
    b.update(overrides)
    return b


def test_golden_case_courses_and_totals():
    """height_m=2.0, width_m=3.0, parpaing200, running -- independently
    verified: courses=ceil(2000/210)=10, per_course=ceil(3000/510)=6,
    total=60, weight=60*18.0=1080.0, cost=60*1.80=108.0."""
    calc = _wall_calc("parpaing200", 2.0, 3.0, "running")
    assert calc["courses"] == 10
    assert calc["per_course"] == 6
    assert calc["total_units"] == 60
    assert calc["total_weight_kg"] == 1080.0
    assert calc["total_cost"] == 108.0


def test_render_produces_real_svg_with_correct_numbers():
    out = _render_wall_elevation(_base(block_id="parpaing200", pattern="running"))
    assert "<svg" in out
    assert "60" in out  # total units, appears in the SVG's own summary line
    assert "1080" in out  # weight


def test_both_block_types_render_with_different_geometry():
    """brique (230x65mm) vs parpaing200 (510x210mm) for the SAME wall
    dimensions must produce genuinely different course/unit counts, not
    just a different label -- proves block_id actually drives the math."""
    parpaing = _wall_calc("parpaing200", 2.0, 3.0, "running")
    brique = _wall_calc("brique", 2.0, 3.0, "running")
    assert parpaing["courses"] != brique["courses"]
    assert parpaing["per_course"] != brique["per_course"]
    assert brique["courses"] == 31  # ceil(2000/65)
    assert brique["per_course"] == 14  # ceil(3000/230)


def test_both_patterns_are_valid_and_distinct_in_output():
    running = _render_wall_elevation(_base(pattern="running"))
    stack = _render_wall_elevation(_base(pattern="stack"))
    assert "Running bond" in running
    assert "Stack bond" in stack
    # Same wall dimensions, same block -> same course/unit COUNTS (pattern
    # only changes stagger offset, not how many blocks fit), but the
    # actual SVG markup differs since running bond offsets alternate rows.
    assert running != stack


def test_unknown_block_id_falls_back_to_parpaing200():
    calc = _wall_calc("not_a_real_block", 2.0, 3.0, "running")
    assert calc["block_id"] == "not_a_real_block"  # preserved for display
    assert calc["block"] == WALL_BLOCKS["parpaing200"]  # but math uses the fallback


def test_unknown_pattern_falls_back_to_running_in_the_renderer():
    out = _render_wall_elevation(_base(pattern="not_a_real_pattern"))
    assert "Running bond" in out


def test_dimension_snapping_and_clamping():
    # Snaps to the nearest 0.2m step.
    assert _wall_snap(2.05) == 2.0
    assert _wall_snap(2.15) == 2.2
    # Clamps below the real minimum.
    assert _wall_snap(0.05) == WALL_DIM_MIN_M
    # Clamps above the real maximum.
    assert _wall_snap(500.0) == WALL_DIM_MAX_M


def test_load_bearing_advisory_fires_for_a_light_block():
    # brique weighs 2.3kg, well under WALL_LOAD_BEARING_MIN_WEIGHT_KG (10.0).
    calc = _wall_calc("brique", 2.0, 3.0, "running", load_bearing=True)
    assert calc["load_bearing_advisory"] is True


def test_load_bearing_advisory_does_not_fire_for_a_heavy_block():
    # parpaing200 weighs 18.0kg, well over the threshold.
    calc = _wall_calc("parpaing200", 2.0, 3.0, "running", load_bearing=True)
    assert calc["load_bearing_advisory"] is False


def test_load_bearing_advisory_does_not_fire_when_load_bearing_is_false():
    calc = _wall_calc("brique", 2.0, 3.0, "running", load_bearing=False)
    assert calc["load_bearing_advisory"] is False


def test_height_advisory_fires_above_threshold_and_not_below():
    tall = _wall_calc("parpaing200", 2.4, 3.0, "running")
    short = _wall_calc("parpaing200", 1.8, 3.0, "running")
    assert tall["height_advisory"] is True
    assert short["height_advisory"] is False


def test_include_dpc_true_sets_a_real_linear_length_matching_width():
    calc = _wall_calc("parpaing200", 2.0, 3.0, "running", include_dpc=True)
    assert calc["include_dpc"] is True
    assert calc["dpc_length_m"] == calc["width_m"]


def test_include_dpc_false_has_zero_length():
    calc = _wall_calc("parpaing200", 2.0, 3.0, "running", include_dpc=False)
    assert calc["dpc_length_m"] == 0.0


def test_dpc_row_only_appears_in_rendered_output_when_included():
    with_dpc = _render_wall_elevation(_base(include_dpc=True))
    without_dpc = _render_wall_elevation(_base(include_dpc=False))
    assert "DPC" in with_dpc
    assert "DPC" not in without_dpc


@pytest.mark.parametrize("raw,expected", [
    (0, WALL_BUILDERS_MIN),
    (-5, WALL_BUILDERS_MIN),
    (999, WALL_BUILDERS_MAX),
    (3, 3),
    ("not a number", 2),  # falls back to the default of 2
    (None, 2),
])
def test_builder_count_clamping(raw, expected):
    assert _wall_snap_builders(raw) == expected


def test_build_days_curve_has_exactly_the_right_number_of_entries():
    curve = _wall_build_days_curve(60)
    assert len(curve) == WALL_BUILDERS_MAX - WALL_BUILDERS_MIN + 1


def test_build_days_curve_is_monotonically_decreasing():
    """More builders on the same job -> fewer days. A real diminishing-
    returns relationship, not a flat or increasing one."""
    curve = _wall_build_days_curve(240)
    for earlier, later in zip(curve, curve[1:]):
        assert later <= earlier


def test_build_days_selected_matches_the_curve_at_the_chosen_builder_count():
    calc = _wall_calc("parpaing200", 2.0, 3.0, "running", builders=4)
    assert calc["builders"] == 4
    assert calc["build_days_selected"] == calc["build_days_curve"][4 - WALL_BUILDERS_MIN]


def test_renderer_never_raises_on_missing_optional_fields():
    """Only height_m/width_m are required -- every other field must have a
    sane default, matching this repo's own convention for optional atom
    fields."""
    out = _render_wall_elevation({"height_m": 2.0, "width_m": 3.0})
    assert "<svg" in out


def test_summary_numbers_are_legible_outside_the_svg_itself():
    """The rendered card must surface courses/units/weight/cost/mortar/
    build-time as real text alongside the diagram, not just bake a single
    summary line into the SVG and call it done."""
    out = _render_wall_elevation(_base(block_id="parpaing200", pattern="running", builders=2))
    for expected_fragment in ("Courses:", "Total units:", "Weight:", "Cost:", "Mortar:", "Build time"):
        assert expected_fragment in out
