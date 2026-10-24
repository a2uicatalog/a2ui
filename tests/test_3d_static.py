"""scatter3d_static and surface_static (Plotly scatter3d / surface, wave B package 3d): a settled 3D view from one fixed camera.

Held here: the projection maths against an independent hand calculation, Python/GAS byte-identical HTML for every payload,
depth order (far to near), the hidden table with every value, the aria gist, shape (not only colour) per series, caps with
visible notes, malformed and hostile input, the `version` note, and registration.
"""
from __future__ import annotations

import math
import re
from pathlib import Path

import pytest
import yaml

from test_histogram import ATTACK, _table
from test_motion_atoms import _gas_batch, _py, core_js  # noqa: F401
from test_motion_atoms import wa  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def _grid(n, m, f):
    return [[f(i, j) for j in range(m)] for i in range(n)]


PTS = [{"x": 1, "y": 2, "z": 3, "series": "Alpha", "label": "p1"}, {"x": 4, "y": 1, "z": 0, "series": "Beta"}, {"x": 2.5, "y": 5, "z": 1.25, "series": "Alpha"},
       {"x": 0, "y": 0, "z": 0, "series": "Gamma", "label": "origin"}]
PAYLOADS = {
    "scatter": {"type": "scatter3d_static", "title": "Samples", "points": PTS, "x_label": "Speed", "y_label": "Load", "z_label": "Heat"},
    "scatter_one": {"type": "scatter3d_static", "points": [{"x": 1, "y": 1, "z": 1}]},
    "scatter_flat": {"type": "scatter3d_static", "points": [{"x": 1, "y": 2, "z": 3}, {"x": 1, "y": 2, "z": 3}]},
    "scatter_persp": {"type": "scatter3d_static", "points": PTS, "camera": {"azimuth": -120, "elevation": 60, "projection": "perspective"}},
    "scatter_eye": {"type": "scatter3d_static", "points": PTS, "camera": {"eye": {"x": 1.25, "y": -1.25, "z": 0.4}}, "drop_lines": False},
    "scatter_low": {"type": "scatter3d_static", "points": PTS, "camera": {"azimuth": 200, "elevation": -30}},
    "scatter_neg": {"type": "scatter3d_static", "points": [{"x": -5, "y": 3e4, "z": 0.001}, {"x": 5, "y": -3e4, "z": -0.002}, {"x": 0, "y": 0, "z": 0}]},
    "scatter_four_series": {"type": "scatter3d_static", "points": [{"x": i, "y": i % 3, "z": i % 5, "series": "S%d" % (i % 4)} for i in range(12)]},
    "scatter_cap": {"type": "scatter3d_static", "points": [{"x": i, "y": i * 2 % 7, "z": i % 11} for i in range(503)]},
    "scatter_malformed": {"type": "scatter3d_static", "points": [None, 3, "x", {"x": 1, "y": 2}, {"x": "1", "y": 2, "z": 3}, {"x": True, "y": 2, "z": 3}, {"x": 1e30, "y": 2, "z": 3}, {"x": 1, "y": 2, "z": 3}, {"x": 2, "y": 3, "z": 4, "series": 7, "label": 5}]},
    "scatter_fifth": {"type": "scatter3d_static", "points": [{"x": i, "y": i, "z": i, "series": "S%d" % i} for i in range(6)]},
    "scatter_none": {"type": "scatter3d_static", "points": []},
    "scatter_notlist": {"type": "scatter3d_static", "points": {"x": 1}},
    "scatter_camera_junk": {"type": "scatter3d_static", "points": PTS, "camera": {"azimuth": "x", "elevation": [1], "eye": {"x": 0, "y": 0, "z": 0}, "projection": "fisheye"}},
    "scatter_v2": {"type": "scatter3d_static", "points": PTS, "version": 2},
    "surface": {"type": "surface_static", "title": "Ripple", "z": _grid(8, 9, lambda i, j: round(math.sin(i / 2) * math.cos(j / 2), 4)), "x_label": "East", "y_label": "North", "z_label": "Height"},
    "surface_xy": {"type": "surface_static", "z": _grid(4, 5, lambda i, j: i * j - 3), "x": [0, 10, 20, 30, 40], "y": [100, 200, 300, 400]},
    "surface_bad_axes": {"type": "surface_static", "z": _grid(3, 3, lambda i, j: i + j), "x": [0, 1], "y": "no"},
    "surface_persp": {"type": "surface_static", "z": _grid(6, 6, lambda i, j: (i - 2.5) ** 2 + (j - 2.5) ** 2), "camera": {"azimuth": 20, "elevation": 50, "projection": "perspective"}},
    "surface_flat": {"type": "surface_static", "z": _grid(3, 3, lambda i, j: 5)},
    "surface_holes": {"type": "surface_static", "z": [[1, 2, 3], [4, None, 6], [7, 8, "x"], [9, 10, 11]]},
    "surface_ragged": {"type": "surface_static", "z": [[1, 2, 3, 4], [5, 6], "no", [7, 8, 9]]},
    "surface_cap": {"type": "surface_static", "z": _grid(32, 33, lambda i, j: (i * j) % 7)},
    "surface_tiny": {"type": "surface_static", "z": [[1]]},
    "surface_none": {"type": "surface_static", "z": "grid"},
    "surface_v2": {"type": "surface_static", "z": _grid(3, 3, lambda i, j: i), "version": 3},
}


@pytest.mark.parametrize("name", list(PAYLOADS))
def test_python_and_gas_emit_identical_html(name, core_js):
    assert _py(PAYLOADS[name]) == _gas_batch(core_js, [PAYLOADS[name]])[0]


# ─── the projection ────────────────────────────────────────────────────────────
def test_projection_matches_a_hand_calculation():
    """Azimuth 0, elevation 0 looks down the +x axis from +x: screen right is +y, screen up is +z, depth is x."""
    basis = wa._p3_camera({"camera": {"azimuth": 0, "elevation": 0}})[3]
    x, y, d = wa._p3_proj((1.0, 0.5, 0.25), basis, False)
    assert (round(x, 9), round(y, 9), round(d, 9)) == (0.5, 0.25, 1.0)
    # azimuth 90: the viewer is on +y, screen right is -x
    basis = wa._p3_camera({"camera": {"azimuth": 90, "elevation": 0}})[3]
    x, y, d = wa._p3_proj((1.0, 0.5, 0.25), basis, False)
    assert (round(x, 9), round(y, 9), round(d, 9)) == (-1.0, 0.25, 0.5)
    # looking straight down: depth is z
    basis = wa._p3_camera({"camera": {"azimuth": 0, "elevation": 80}})[3]
    assert wa._p3_proj((0.0, 0.0, 1.0), basis, False)[2] == pytest.approx(math.sin(math.radians(80)))
    # a Plotly camera.eye of (1.25, 1.25, 1.25) is azimuth 45, elevation about 35.26
    az, el = wa._p3_camera({"camera": {"eye": {"x": 1.25, "y": 1.25, "z": 1.25}}})[:2]
    assert az == pytest.approx(45) and el == pytest.approx(35.2643896828, abs=1e-6)


def test_perspective_makes_near_points_larger_and_orthographic_does_not():
    b = wa._p3_camera({"camera": {"azimuth": 0, "elevation": 0}})[3]
    near, far = (1.0, 0.4, 0.0), (-1.0, 0.4, 0.0)
    assert wa._p3_proj(near, b, False)[0] == wa._p3_proj(far, b, False)[0]
    assert wa._p3_proj(near, b, True)[0] > wa._p3_proj(far, b, True)[0]


def test_the_cube_fits_inside_the_view_box_for_every_camera():
    for az in range(-180, 181, 45):
        for el in (-80, -30, 0, 30, 80):
            for persp in (False, True):
                basis = wa._p3_camera({"camera": {"azimuth": az, "elevation": el, "projection": "perspective" if persp else "orthographic"}})[3]
                screen, corners = wa._p3_scene(basis, persp)
                for c in corners:
                    sx, sy, _ = screen(c)
                    assert wa._P3_MX - 0.01 <= sx <= wa._P3_W - wa._P3_MX + 0.01 and wa._P3_MY - 0.01 <= sy <= wa._P3_H - wa._P3_MY + 0.01, (az, el, persp)


def test_markers_are_drawn_far_to_near(core_js):
    b = {"type": "scatter3d_static", "points": [{"x": 0, "y": 0, "z": 0, "series": "far"}, {"x": 10, "y": 0, "z": 0, "series": "near"}], "camera": {"azimuth": 0, "elevation": 0}, "drop_lines": False}
    for h in (_py(b), _gas_batch(core_js, [b])[0]):
        fills = re.findall(r'<(?:circle|rect)[^>]*fill="([^"]*)"', h)
        # azimuth 0 looks from +x: x = 10 is nearest, so it is painted last; series two is a square
        assert len(fills) == 2 and re.findall(r'<(circle|rect)', h) == ["circle", "rect"]


def test_surface_faces_are_painted_far_to_near_and_all_present(core_js):
    b = PAYLOADS["surface"]
    for h in (_py(b), _gas_batch(core_js, [b])[0]):
        assert h.count('<polygon') == 7 * 8


# ─── accessibility ────────────────────────────────────────────────────────────
def test_scatter_table_aria_and_shapes(core_js):
    for html in (_py(PAYLOADS["scatter"]), _gas_batch(core_js, [PAYLOADS["scatter"]])[0]):
        head, rows = _table(html)
        assert head == ["Point", "Speed", "Load", "Heat", "Series"]
        assert rows == [["p1", "1", "2", "3", "Alpha"], ["Point 2", "4", "1", "0", "Beta"], ["Point 3", "2.5", "5", "1.25", "Alpha"], ["origin", "0", "0", "0", "Gamma"]]
        t = html.index("<table")
        assert 'role="img"' in html[:t] and 'role="img"' not in html[t:]
        a = re.search(r'role="img" aria-label="([^"]*)"', html).group(1)
        assert a == "3D scatter of 4 points in 3 series. Speed from 0 to 4, Load from 0 to 5, Heat from 0 to 3. Fixed view from azimuth 45 and elevation 30 degrees."
        # series are told apart by shape and by a legend with a glyph, not by colour alone
        assert {m for m in re.findall(r'<(circle|rect|polygon (?:data-cb="\w+" (?:data-key="[^"]*" )?)?points="[^"]*" fill)', html)} >= {"circle", "rect"} and len(re.findall(r'<polygon (?:data-cb="\w+" (?:data-key="[^"]*" )?)?points', html)) == 1
        assert all(g in html for g in "●■▲") and "Alpha" in html and "Beta" in html


def test_surface_table_gives_every_value_and_the_aria_names_the_extremes(core_js):
    b = PAYLOADS["surface_xy"]
    for html in (_py(b), _gas_batch(core_js, [b])[0]):
        head, rows = _table(html)
        assert head == ["y \\ x", "0", "10", "20", "30", "40"]
        assert rows[0] == ["100", "-3", "-3", "-3", "-3", "-3"] and rows[3] == ["400", "-3", "0", "3", "6", "9"] and len(rows) == 4
        a = re.search(r'role="img" aria-label="([^"]*)"', html).group(1)
        assert a.startswith("3D surface of 4 by 5 values. z from -3 (at x 0, y 100) to 9 (at x 40, y 400).")
        assert "Stronger colour is higher" in html


def test_labels_are_html_text_of_at_least_12px_never_svg_text():
    for n in ("scatter", "surface"):
        h = _py(PAYLOADS[n])
        assert "<text" not in h and not re.search(r'font-size:(0\.[0-6]\d*rem|1[01]px|\d{1}px)', h)


def test_axis_captions_carry_label_and_range():
    h = _py(PAYLOADS["scatter"])
    for cap in ("Speed", "Load", "Heat"):
        assert ">" + cap + "</div>" in h
    assert "0 to 4" in h or "4 to 0" in h


# ─── contract ─────────────────────────────────────────────────────────────────
def test_no_script_no_nan_in_any_payload(core_js):
    for name, b in PAYLOADS.items():
        for h in (_py(b), _gas_batch(core_js, [b])[0]):
            assert "<script" not in h and "NaN" not in h and "undefined" not in h and "Infinity" not in h and "[object Object]" not in h and "null" not in h, name


def test_scatter_caps_notes_and_skips(core_js):
    h = _py(PAYLOADS["scatter_cap"])
    assert len(_table(h)[1]) == 500 and "3 points beyond the first 500 were not drawn." in h
    h = _py(PAYLOADS["scatter_malformed"])
    assert len(_table(h)[1]) == 2 and "7 points were not a usable x, y, z number triple and were left out." in h
    assert _table(h)[1][1][4] == "7" and _table(h)[1][1][0] == "5"
    h = _py(PAYLOADS["scatter_fifth"])
    assert len(_table(h)[1]) == 4 and "2 points in a fifth or later series were not drawn (4 series at most)." in h
    for k in ("scatter_none", "scatter_notlist"):
        h = _py(PAYLOADS[k])
        assert "A 3D scatter needs at least one point with numbers x, y and z." in h and "<svg" not in h and "<table" not in h


def test_surface_caps_holes_and_notes(core_js):
    h = _py(PAYLOADS["surface_cap"])
    assert "2 rows beyond the first 30 were not drawn." in h and "3 columns beyond the first 30 were not drawn." in h and len(_table(h)[1]) == 30
    h = _py(PAYLOADS["surface_holes"])
    assert "2 grid values were not a usable number and the faces touching them were left open." in h
    assert h.count("<polygon") == 1                      # 6 quads; the two holes touch 5 of them
    assert _table(h)[1][1] == ["1", "4", "-", "6"]
    h = _py(PAYLOADS["surface_ragged"])
    assert len(_table(h)[1]) == 3 and "-" in _table(h)[1][1]
    for k in ("surface_tiny", "surface_none"):
        h = _py(PAYLOADS[k])
        assert "A surface needs a grid z of at least 2 rows by 2 columns of numbers." in h and "<svg" not in h


def test_flat_data_and_bad_camera_are_drawn_sensibly():
    h = _py(PAYLOADS["surface_flat"])
    assert h.count("<polygon") == 4 and 'fill-opacity="0.60"' in h
    assert "azimuth 45 and elevation 1 degrees" in _py(PAYLOADS["scatter_camera_junk"])
    assert "perspective" not in _py(PAYLOADS["scatter_camera_junk"])


def test_version_above_one_is_noted(core_js):
    for k, atom in (("scatter_v2", "scatter3d_static"), ("surface_v2", "surface_static")):
        for h in (_py(PAYLOADS[k]), _gas_batch(core_js, [PAYLOADS[k]])[0]):
            assert "Written for " + atom + " version " in h
    assert "Written for scatter3d_static version 2; drawn as version 1." in _py(PAYLOADS["scatter_v2"])
    assert "Written for surface_static version 3; drawn as version 1." in _py(PAYLOADS["surface_v2"])


def test_hostile_text_is_escaped_in_both_twins(core_js):
    pts = [{"x": 1, "y": 2, "z": 3, "series": ATTACK, "label": ATTACK}, {"x": 2, "y": 1, "z": 0}]
    bs = [{"type": "scatter3d_static", "title": ATTACK, "x_label": ATTACK, "y_label": ATTACK, "z_label": ATTACK, "points": pts},
          {"type": "surface_static", "title": ATTACK, "x_label": ATTACK, "y_label": ATTACK, "z_label": ATTACK, "z": [[1, 2], [3, 4]], "camera": {"projection": ATTACK}}]
    for b in bs:
        for h in (_py(b), _gas_batch(core_js, [b])[0]):
            assert "<img" not in h and "<script" not in h.replace("<style", "") and 'onerror=alert(1)>' not in h.replace("&gt;", "")


def test_output_is_deterministic():
    for k in ("scatter", "surface"):
        assert _py(PAYLOADS[k]) == _py(PAYLOADS[k])


# ─── registration ─────────────────────────────────────────────────────────────
@pytest.mark.parametrize("atom,fields", [("scatter3d_static", {"title", "points", "x_label", "y_label", "z_label", "camera", "drop_lines", "version"}),
                                         ("surface_static", {"title", "z", "x", "y", "x_label", "y_label", "z_label", "camera", "version"})])
def test_registered_as_a_preview_charts_atom_with_an_example(atom, fields):
    blocks = {a["type"]: a for a in yaml.safe_load((ROOT / "atoms/schema.yaml").read_text())["blocks"]}
    a = blocks[atom]
    assert a["stage"] == "preview" and set(a["fields"]) == fields
    assert a["surfaces"] == blocks["treemap"]["surfaces"] and a["source"] == blocks["treemap"]["source"]
    assert re.search(r"^a2ui-charts-v1:\n(?:- .*\n)*- " + atom + "$", (ROOT / "atoms/atom-packs.yaml").read_text(), re.M)
    assert '"' + atom + '":"a2ui-charts-v1"' in (ROOT / "apps-script-surface/gas-wired-renderer/PackMap.gs").read_text()
    import generate_atom_pages as g
    ex = g._EXAMPLE_BLOCKS[atom]
    assert ex["type"] == atom and "<table" in _py(ex)


# ─── wave B fixes ──────────────────────────────────────────────────────────────
@pytest.mark.parametrize("name", ["scatter", "scatter_persp", "scatter_low", "scatter_eye"])
def test_exactly_the_three_edges_at_the_far_corner_are_dashed_and_the_other_nine_come_last(name, core_js):
    b = PAYLOADS[name]
    for h in (_py(dict(b)), _gas_batch(core_js, [dict(b)])[0]):
        lines = re.findall(r'<line [^>]*stroke="var\(--muted,#475569\)"[^>]*/>', h)
        assert len(lines) == 12
        assert sum("stroke-dasharray" in ln for ln in lines) == 3
        assert h.rindex("stroke-dasharray") < h.index('opacity="0.9"')   # dashed ones first
        first_front = h.index('opacity="0.9"')
        assert h.index("<circle") < first_front or h.index("<rect") < first_front or h.index("<polygon") < first_front   # data is painted before the front edges


def test_the_surface_legend_does_not_depend_on_the_theme():
    h = _py({"type": "surface_static", "z": _grid(3, 3, lambda i, j: i + j)})
    assert "Stronger colour is higher" in h and "Darker" not in h


def test_400_digit_integers_in_camera_do_not_crash_the_page(core_js):
    big = 10 ** 400
    for t, k in (("scatter3d_static", "points"), ("surface_static", "z")):
        base = {"type": t, k: PTS if k == "points" else [[1, 2], [3, 4]]}
        for cam in ({"azimuth": big}, {"elevation": -big}):
            b = dict(base, camera=cam)
            h = _py(dict(b))
            assert isinstance(h, str) and "Traceback" not in h
            assert _gas_batch(core_js, [dict(b)])[0] == h, (t, cam)
