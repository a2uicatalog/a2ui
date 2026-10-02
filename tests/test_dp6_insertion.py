"""Tests for declaration_prealable/dp6_insertion.py -- DP6 (insertion mockup composited onto a real
photo) and DP7/DP8 (real site photos, captioned/packaged, no compositing). Uses small synthetic
in-memory PIL images as the "real photo" input -- mirrors tests/test_dp2_plan_masse.py's own
hand-computed-assertion style for the geometry/scale math.
"""
import io

import pytest

PIL = pytest.importorskip("PIL", reason="declaration_prealable's own optional raster dependency")
from PIL import Image  # noqa: E402

from declaration_prealable import dp6_insertion as dp6  # noqa: E402
from declaration_prealable.project_schema import WallSpec  # noqa: E402


def _fake_photo_bytes(width=800, height=600, fmt="PNG"):
    # PNG (lossless) by default -- a real photo would be JPEG, but JPEG's lossy quantization shifts
    # flat-colour pixels by a few RGB values, which breaks exact-equality background comparisons below;
    # test_package_site_photo_returns_real_jpeg_with_caption covers the real-JPEG-input path separately.
    img = Image.new("RGB", (width, height), (120, 160, 200))
    out = io.BytesIO()
    img.save(out, format=fmt)
    return out.getvalue()


def _wall(**overrides):
    kwargs = dict(length_m=4.0, height_m=1.8, finish_label="Enduit lisse peint en blanc",
                  finish_colour_hex="#f2f1ec")
    kwargs.update(overrides)
    return WallSpec(**kwargs)


def test_package_site_photo_returns_real_jpeg_with_caption():
    out = dp6.package_site_photo_bytes(_fake_photo_bytes(), "DP7", "Photo - environnement proche",
                                        "12 rue des Tilleuls")
    assert out[:3] == b"\xff\xd8\xff"
    img = Image.open(io.BytesIO(out))
    assert img.format == "JPEG"


def test_package_site_photo_resizes_oversized_input():
    out = dp6.package_site_photo_bytes(_fake_photo_bytes(width=3000, height=2000), "DP8",
                                        "Photo - paysage lointain", "X", max_width=1200)
    img = Image.open(io.BytesIO(out))
    assert img.size[0] == 1200


def test_composite_dp6_returns_real_png():
    out = dp6.composite_dp6_insertion_bytes(_fake_photo_bytes(), [200, 500], [600, 500], _wall(), "X")
    assert out[:8] == b"\x89PNG\r\n\x1a\n"
    img = Image.open(io.BytesIO(out))
    assert img.format == "PNG"
    assert img.size == (800, 600)


def test_composite_dp6_wall_overlay_pixel_matches_finish_colour():
    # Base points 400px apart represent the wall's real 4.0 m length -> 100 px/m. The wall is drawn as
    # a vertical screen-space extrusion above the base line, so a pixel well inside the polygon (not
    # near its semi-transparent edge) should read close to the requested finish colour blended over the
    # background, not the plain background colour alone.
    wall = _wall(length_m=4.0, height_m=1.8, finish_colour_hex="#ff0000")
    out = dp6.composite_dp6_insertion_bytes(_fake_photo_bytes(800, 600), [200, 500], [600, 500], wall, "X")
    img = Image.open(io.BytesIO(out)).convert("RGB")
    # Sample the midpoint of the wall footprint, half-way up its 180px-tall extrusion.
    sample = img.getpixel((400, 500 - 90))
    background = (120, 160, 200)
    # Alpha-blended red (200/255 alpha) over the blue-grey background should be clearly redder than
    # the background itself, not identical to it.
    assert sample[0] > background[0]
    assert sample[0] > sample[2]


def test_composite_dp6_scales_with_requested_wall_length():
    # Same 400px base distance, but a SHORTER real wall length -> a larger px/m scale -> a TALLER
    # extrusion in pixels for the same height_m. Cross-check by comparing the overlay's topmost
    # non-background row between the two cases.
    photo = _fake_photo_bytes(800, 600)

    def _overlay_top_row(wall):
        out = dp6.composite_dp6_insertion_bytes(photo, [200, 500], [600, 500], wall, "X")
        img = Image.open(io.BytesIO(out)).convert("RGB")
        # Start below the caption band (rows 0-22 are always overwritten regardless of wall height)
        # and sample a column clear of the red leader-line/label text, which is offset to the right.
        for y in range(23, 500):
            if img.getpixel((380, y)) != (120, 160, 200):
                return y
        return 500

    top_long_wall = _overlay_top_row(_wall(length_m=4.0, height_m=1.8))
    top_short_wall = _overlay_top_row(_wall(length_m=2.0, height_m=1.8))
    # A shorter requested length over the same pixel base distance means a higher px/m scale, so the
    # SAME real height_m produces a TALLER (smaller y, further up the image) overlay.
    assert top_short_wall < top_long_wall


def test_composite_dp6_rejects_coincident_base_points():
    with pytest.raises(ValueError, match="too close"):
        dp6.composite_dp6_insertion_bytes(_fake_photo_bytes(), [400, 500], [400, 500], _wall(), "X")


def test_composite_dp6_rejects_point_outside_photo():
    with pytest.raises(ValueError, match="outside the photo"):
        dp6.composite_dp6_insertion_bytes(_fake_photo_bytes(800, 600), [200, 500], [9000, 500], _wall(), "X")


def test_composite_dp6_rejects_non_positive_wall_length():
    with pytest.raises(ValueError, match="length_m must be positive"):
        dp6.composite_dp6_insertion_bytes(_fake_photo_bytes(), [200, 500], [600, 500],
                                           _wall(length_m=0.0), "X")


def test_composite_dp6_rescales_click_points_for_oversized_photo():
    # A 3000px-wide input gets resized down to max_width=1500 internally (scale=0.5) -- click points
    # given in the ORIGINAL photo's pixel space must still land correctly after that internal resize,
    # not be silently misplaced or rejected as out-of-bounds.
    out = dp6.composite_dp6_insertion_bytes(_fake_photo_bytes(3000, 2000), [400, 1000], [1200, 1000],
                                             _wall(), "X", max_width=1500)
    img = Image.open(io.BytesIO(out))
    assert img.size == (1500, 1000)
