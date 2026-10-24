LEGACY = {
    "schema_form": {"type": "heatmap", "title": "Visits", "data": [[1, 2, 3], [4, 5, 6]], "labels_x": ["Mon", "Tue", "Wed"], "labels_y": ["AM", "PM"], "color_scale": ["#FFFFFF", "#FF0000"], "unit": "k"},
    "schema_minimal": {"type": "heatmap", "data": [[0, 10], [5, 5]]},
    "dict_items": {"type": "heatmap", "title": "Items", "data": [{"row": "a", "col": "x", "value": 3}, {"row": "a", "col": "y", "value": 9}]},
    "rows_cols": {"type": "heatmap", "title": "Grid", "rows": ["r1", "r2"], "cols": ["c1", "c2", "c3"], "data": [[1, 2, 3], [3, 2, 1]], "color_scheme": "blue"},
    "empty": {"type": "heatmap"},
    "empty_data": {"type": "heatmap", "data": []},
    "hostile": {"type": "heatmap", "title": "<img src=x onerror=alert(1)>", "data": [[1, "x", None], [2]], "labels_x": ["<b>", "\"'"], "labels_y": ["<script>"], "color_scale": ["red", "<x>"]},
    "all_equal": {"type": "heatmap", "data": [[3, 3], [3, 3]], "rows": ["a", "b"], "cols": ["c", "d"]},
}

# ─── tests ────────────────────────────────────────────────────────────────────
"""heatmap variants (preview-safe, additive): z_min / z_max / z_mid, named Plotly `scale`, show_colorbar, show_values + value_format.

Any payload with none of those fields renders byte for byte as at base (heatmap_base_snapshot.json, written at a2649e695).
A payload with one of them takes the extended path, which reads the schema fields (data matrix, labels_x, labels_y, color_scale, unit)
and draws an HTML grid + colour bar + hidden table, identically in the Python and the Apps Script renderer."""
import json
import re
from pathlib import Path

import pytest

from test_motion_atoms import _gas_batch, _node, _py, core_js  # noqa: F401
from test_motion_atoms import wa  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
BASE = json.loads((ROOT / "tests/fixtures/heatmap_base_snapshot.json").read_text())
SCALES = json.loads((ROOT / "tests/fixtures/plotly_scales.json").read_text())
ATTACK = '"><img src=x onerror=alert(1)><script>alert(2)</script>'
M = [[1, 2, 3], [4, 5, 6], [7, 8, 9.5]]

EXT = {
    "plain": {"type": "heatmap", "data": M, "labels_x": ["a", "b", "c"], "labels_y": ["r1", "r2", "r3"], "scale": "Viridis"},
    "values": {"type": "heatmap", "title": "T", "data": M, "show_values": True, "value_format": ",.1f", "unit": "ms", "scale": "Blues"},
    "diverging": {"type": "heatmap", "data": [[-5, 0, 2], [3, -1, 8]], "z_mid": 0, "scale": "RdBu", "show_values": True},
    "range": {"type": "heatmap", "data": M, "z_min": 0, "z_max": 20, "scale": "YlOrRd", "show_colorbar": True},
    "no_bar": {"type": "heatmap", "data": M, "scale": "Greys", "show_colorbar": False},
    "percent": {"type": "heatmap", "data": [[0.1, 0.25], [0.5, 1]], "show_values": True, "value_format": ".0%"},
    "custom": {"type": "heatmap", "data": M, "color_scale": ["#ffffff", "#0000ff"], "z_mid": 5},
    "holes": {"type": "heatmap", "data": [[1, None, "x"], [2], [float("nan"), 3, True]], "show_values": True},
    "all_equal": {"type": "heatmap", "data": [[3, 3], [3, 3]], "z_min": 3, "scale": "Hot"},
    "hostile": {"type": "heatmap", "title": ATTACK, "data": [[1, 2]], "labels_x": [ATTACK, "b"], "labels_y": [ATTACK], "unit": ATTACK, "scale": ATTACK, "value_format": ATTACK, "show_values": True},
    "bad_numbers": {"type": "heatmap", "data": [[1e300, -1e300], [float("inf"), 2]], "z_min": "lots", "z_max": {}, "z_mid": [1], "show_values": True},
    "unknown_scale": {"type": "heatmap", "data": M, "scale": "Nope"},
    "version2": {"type": "heatmap", "data": M, "version": 2, "show_colorbar": True},
    "big": {"type": "heatmap", "data": [[(i * j) % 17 for j in range(45)] for i in range(50)], "scale": "Viridis"},
    "empty": {"type": "heatmap", "data": [], "scale": "Viridis"},
    "not_lists": {"type": "heatmap", "data": "abc", "z_min": 0},
}


def _all_gas(core_js, d):
    return dict(zip(d, _gas_batch(core_js, list(d.values()))))


# Payloads whose data is a list of lists (the schema shape) used to draw nothing in Python (the second, dict-only
# _render_heatmap shadowed the schema renderer) and an unlabelled SVG in Apps Script; both twins route them to the extended
# grid (_hm_ext / _hmExt) now. Every other base payload (dict items, empty) is still byte for byte as at base.
SCHEMA_SHAPED_PY = {"schema_form", "schema_minimal", "rows_cols", "hostile", "all_equal"}
SCHEMA_SHAPED_GAS = SCHEMA_SHAPED_PY


@pytest.mark.parametrize("name", [n for n in BASE if n not in SCHEMA_SHAPED_PY])
def test_payloads_without_the_new_fields_render_byte_for_byte_as_at_base(name):
    assert _py(dict(LEGACY[name])) == BASE[name]["py"]


def test_gas_payloads_without_the_new_fields_render_byte_for_byte_as_at_base(core_js):
    g = _all_gas(core_js, LEGACY)
    names = [n for n in BASE if n not in SCHEMA_SHAPED_GAS]
    assert {n: g[n] for n in names} == {n: BASE[n]["gas"] for n in names}


SCHEMA = {
    "grid": {"type": "heatmap", "data": [[1, 2], [3, 4]], "labels_x": ["a", "b"], "labels_y": ["c", "d"]},
    "wide": {"type": "heatmap", "title": "Visits", "data": [[1, 2, 3], [4, 5, 6]], "labels_x": ["Mon", "Tue", "Wed"], "labels_y": ["AM", "PM"], "color_scale": ["#FFFFFF", "#FF0000"], "unit": "k"},
    "no_labels": {"type": "heatmap", "data": [[0, 10], [5, 5], [1, 2]]},
    "ragged": {"type": "heatmap", "data": [[1, "x", None], [2]], "labels_x": ["a", "b", "c"], "labels_y": ["r1", "r2"]},
    "one_row": {"type": "heatmap", "data": [[7, 8, 9, 10]]},
    "rows_cols": {"type": "heatmap", "rows": ["r1", "r2"], "cols": ["c1", "c2", "c3"], "data": [[1, 2, 3], [3, 2, 1]], "color_scheme": "blue"},
    "short_hex": {"type": "heatmap", "data": [[1, 2], [3, 4]], "color_scale": ["#fff", "#000"]},
    "named_colours": {"type": "heatmap", "data": [[1, 2], [3, 4]], "color_scale": ["red", "blue"]},
    "bad_colour_type": {"type": "heatmap", "data": [[1, 2], [3, 4]], "color_scale": [1, None]},
    "huge_int": {"type": "heatmap", "data": [[10 ** 400, 2], [3, 4]]},
    "infinity_string": {"type": "heatmap", "data": [["1e999", 2], [3, 4]]},
}
SCHEMA_CELLS = {"grid": 4, "wide": 6, "no_labels": 6, "ragged": 6, "one_row": 4, "rows_cols": 6, "short_hex": 4, "named_colours": 4, "bad_colour_type": 4, "huge_int": 4, "infinity_string": 4}
GARBAGE = r"NaN|undefined|Infinity|\[object"


def test_schema_shaped_payload_draws_rows_by_cols_cells_in_python():
    for n, b in SCHEMA.items():
        h = _py(dict(b))
        assert h.count('class="hmc') == SCHEMA_CELLS[n], n
        assert not re.search(GARBAGE, h), n
    h = _py(dict(SCHEMA["grid"]))
    assert ">a</div>" in h and ">d</div>" in h and "<th scope=\"row\">d</th>" in h
    h = _py(dict(SCHEMA["rows_cols"]))
    assert ">c3</div>" in h and ">r2</div>" in h
    assert "rgb(15,23,42)" not in h and "var(--muted" in h


def test_schema_shaped_payload_draws_rows_by_cols_cells_in_gas(core_js):
    g = _all_gas(core_js, SCHEMA)
    for n, h in g.items():
        assert h.count('class="hmc') == SCHEMA_CELLS[n], n
        assert "No heatmap data" not in h and not re.search(GARBAGE, h), n


def test_python_and_gas_are_byte_identical_for_schema_shaped_payloads(core_js):
    g = _all_gas(core_js, SCHEMA)
    for n, b in SCHEMA.items():
        assert _py(dict(b)) == g[n], n


def test_color_scheme_names_a_scale_for_a_list_of_lists_only(core_js):
    blue = dict(SCHEMA["rows_cols"])
    assert _py(dict(blue)) == _py(dict(blue, scale="Blues"))
    assert _py(dict(blue, color_scheme="nope")) == _py({k: v for k, v in blue.items() if k != "color_scheme"})


def test_crash_payloads_never_raise_and_draw_a_grid_with_a_table():
    for n in ("short_hex", "named_colours", "bad_colour_type", "huge_int", "infinity_string"):
        h = _py(dict(SCHEMA[n]))
        assert 'role="img"' in h and "<table" in h, n


def test_gas_infinity_string_and_huge_numbers_become_no_data_not_nan(core_js):
    g = _all_gas(core_js, SCHEMA)
    for n in ("huge_int", "infinity_string"):
        assert g[n].count("hmn") == 1 and not re.search(GARBAGE, g[n]), n


def test_large_matrix_is_capped_with_a_note_in_both_twins(core_js):
    b = {"type": "heatmap", "data": [[i + j for j in range(300)] for i in range(300)]}
    p = _py(dict(b))
    assert p.count('class="hmc"') == 1600 and "first 40 of 300 rows" in p and "first 40 of 300 columns" in p
    assert len(p) < 400000
    assert _gas_batch(core_js, [dict(b)])[0] == p


def test_legacy_dict_items_are_routed_to_the_legacy_renderer():
    b = {"type": "heatmap", "title": "Items", "data": [{"row": "a", "col": "x", "value": 3}, {"row": "a", "col": "y", "value": 9}]}
    h = _py(dict(b))
    assert h == BASE["dict_items"]["py"] and h.count("<td ") == 2 and "<rect" not in h
    assert _py({"type": "heatmap"}) == BASE["empty"]["py"]


def test_python_and_gas_emit_identical_html(core_js):
    g = _all_gas(core_js, EXT)
    for n, b in EXT.items():
        assert _py(dict(b)) == g[n], n


def test_scale_tables_equal_the_real_plotly_scales_in_both_twins(core_js):
    py = {k: [[p, list(c)] for p, c in v] for k, v in wa._HM_SCALES.items()}
    assert py == SCALES
    js = _node(core_js, "console.log(JSON.stringify(_HM_SCALES));")
    assert js == SCALES


def test_colour_at_the_stops_is_the_stop_colour_and_between_is_linear():
    assert wa._hm_rgb("Greys", 0) == (0, 0, 0) and wa._hm_rgb("Greys", 1) == (255, 255, 255)
    assert wa._hm_rgb("Greys", 0.5) == (128, 128, 128)
    assert wa._hm_rgb("RdBu", 0.5) == (190, 190, 190)
    assert wa._hm_rgb("Viridis", 1) == (0xfd, 0xe7, 0x25)


def test_domain_rules_zmid_symmetric_unless_both_limits_given():
    assert wa._hm_domain([-5, 8], None, None, 0) == (-8, 8)
    assert wa._hm_domain([-5, 8], 0, 20, 0) == (0, 20)           # both limits set: z_mid has no effect (as Plotly)
    assert wa._hm_domain([1, 9], 0, None, None) == (0, 9)
    assert wa._hm_domain([3, 3], None, None, None) == (3, 4)


def test_diverging_midpoint_gets_the_scale_midpoint_colour():
    h = _py(dict(EXT["diverging"]))
    assert "background:rgb(190,190,190)" in h        # the 0 cell, RdBu t=0.5


def test_value_format_subset():
    f = wa._hm_fmt
    assert f(1234.5, ",.1f") == "1,234.5" and f(0.256, ".0%") == "26%" and f(2, ".2f") == "2.00" and f(-1234567, ",") == "-1,234,567"
    assert f(0.5, None) == "0.5" and f(-0.001, None) == "0" and f(1e6, ",") == "1,000,000"
    assert f(3.14159, None) == "3.14" and f(3, None) == "3" and f(12.5, "d") == "13" and f(5, "nonsense") == "5"


def test_extended_output_has_aria_label_hidden_table_and_colour_bar():
    h = _py(dict(EXT["plain"]))
    assert 'role="img"' in h and re.search(r'aria-label="Heatmap, 3 rows by 3 columns[^"]*1[^"]*9\.5', h)
    assert h.count("<td>") == 9 and "<th scope=\"row\">r2</th>" in h
    assert "linear-gradient(to right" in h and ">1</span>" in h
    assert "linear-gradient" not in _py(dict(EXT["no_bar"]))
    assert "<script" not in h.lower()


def test_values_are_drawn_only_on_request_and_never_colour_only():
    assert "hmv" not in _py(dict(EXT["plain"]))
    h = _py(dict(EXT["values"]))
    assert "1,234" not in h and ">9.5<" in h
    assert h.count('class="hmc"') == 9 and all("title=" in c for c in re.findall(r'<div class="hmc"[^>]*>', h))


def test_missing_cells_are_marked_not_dropped():
    h = _py(dict(EXT["holes"]))
    assert h.count("hmn") == 6 and "no data" in h.lower()


def test_hostile_text_is_escaped_and_nothing_prints_garbage():
    for n in ("hostile", "bad_numbers", "unknown_scale", "not_lists", "empty"):
        h = _py(dict(EXT[n]))
        assert "<img" not in h and "<script" not in h.lower(), n
        assert not re.search(r"NaN|undefined|Infinity|\[object", h), n
    assert "Nope" in _py(dict(EXT["unknown_scale"])) and "Viridis" in _py(dict(EXT["unknown_scale"]))


def test_caps_are_stated():
    h = _py(dict(EXT["big"]))
    assert "first 40 of 50 rows" in h and "first 40 of 45 columns" in h and h.count("<tr>") == 41


def test_version_note_and_empty_state():
    assert "Written for heatmap version 2; drawn as version 1." in _py(dict(EXT["version2"]))
    assert "needs at least one number" in _py(dict(EXT["empty"]))


def test_schema_registration():
    import yaml
    s = yaml.safe_load((ROOT / "atoms/schema.yaml").read_text())
    atom = [a for a in s["blocks"] if a.get("type") == "heatmap"][0]
    for f in ("z_min", "z_max", "z_mid", "scale", "show_colorbar", "show_values", "value_format", "version"):
        assert f in atom["fields"], f


# ─── round 2 (review HM-2 / HM-3) ─────────────────────────────────────────────
OBJ_LABELS = {"type": "heatmap", "data": [[1, 2], [3, 4]], "labels_x": [{"o": 1}, ["q"]], "labels_y": [{"o": 1}, True], "scale": "Viridis"}
OBJ_SCALE = {"type": "heatmap", "data": [[1, 2]], "scale": {"name": "Jet"}}
DICT_ITEMS = {"type": "heatmap", "version": 1, "data": [{"row": "a", "col": "x", "value": 3}, {"row": "a", "col": "y", "value": 9}, {"row": "b", "col": "y", "value": 5}]}


def test_object_labels_fall_back_to_row_col_names_not_object_object(core_js):
    for b in (OBJ_LABELS, OBJ_SCALE):
        for h in (_py(dict(b)), _gas_batch(core_js, [dict(b)])[0]):
            assert "[object" not in h and "object Object" not in h
    h = _py(dict(OBJ_LABELS))
    assert "Col 1" in h and "Col 2" in h and "Row 1" in h and "Row 2" in h
    assert 'Unknown scale' in _py(dict(OBJ_SCALE))


def test_legacy_row_col_value_items_still_draw_with_a_new_field(core_js):
    h = _py(dict(DICT_ITEMS))
    assert "needs at least one number" not in h
    assert h.count('class="hmc"') == 3 and h.count("hmn") == 1
    assert ">a<" in h and ">x<" in h and ">y<" in h and ">b<" in h
    assert _gas_batch(core_js, [dict(DICT_ITEMS)])[0] == h
    assert 'aria-label="Heatmap, 2 rows by 2 columns, values from 3 to 9.' in h
