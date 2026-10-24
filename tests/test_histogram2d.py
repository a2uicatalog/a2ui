"""histogram2d (preview): d3-array 3.2.4 bin() run twice (x, then y), counted into a grid and drawn through the heatmap atom.

GOLDEN (tests/fixtures/histogram2d_d3_golden.json, made by histogram2d_d3_golden_gen.mjs from the real d3-array) holds the x and y bin
edges and the 2-D counts. Both twins must reproduce them exactly. The drawing itself is the heatmap atom's: this atom builds a heatmap
block (`_h2_block`) and hands it to the registered heatmap renderer, so the colour scale, colour bar, cell values and hidden table are
the heatmap options of the plotly-heatmap-r2 branch (on main since wave A)."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

from test_motion_atoms import _gas_batch, _node, _py, core_js  # noqa: F401  (core_js is a fixture)
from test_motion_atoms import wa  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
D = json.loads((ROOT / "tests/fixtures/histogram2d_d3_golden.json").read_text())
CASES = {**D["golden"], **{f"fuzz{i}": c for i, c in enumerate(D["fuzz"])}}
ATTACK = '"><img src=x onerror=alert(1)>\'"><svg onload=alert(1)></script><script>alert(4)</script> onmouseover=alert(2)'
assert hasattr(wa, "_hm_ext"), "histogram2d draws through the heatmap options (_hm_ext)"
BAD = re.compile(r"NaN|undefined|Infinity|\[object")


# ─── the layout against real d3 ────────────────────────────────────────────────
@pytest.mark.parametrize("name", list(CASES))
def test_python_bins_match_d3_exactly(name):
    c = CASES[name]
    xe, ye, counts = wa._h2_bin([float(v) for v in c["x"]], [float(v) for v in c["y"]], c["nbinsx"], c["nbinsy"])
    assert [list(e) for e in xe] == c["xedges"]
    assert [list(e) for e in ye] == c["yedges"]
    assert counts == c["counts"]


def test_gas_bins_match_d3_exactly(core_js):
    names = list(CASES)
    res = _node(core_js, "var G = " + json.dumps([[CASES[n]["x"], CASES[n]["y"], CASES[n]["nbinsx"], CASES[n]["nbinsy"]] for n in names]) +
                "; console.log(JSON.stringify(G.map(function(g){ return _h2Bin(g[0], g[1], g[2], g[3]); })));")
    for n, (xe, ye, counts) in zip(names, res):
        assert xe == CASES[n]["xedges"] and ye == CASES[n]["yedges"] and counts == CASES[n]["counts"], n


def test_every_point_is_counted_once():
    for n, c in CASES.items():
        assert sum(map(sum, c["counts"])) == len(c["x"]), n


# ─── the block handed to the heatmap ───────────────────────────────────────────
def _blk(**kw):
    return {"type": "histogram2d", "x": [1, 1, 5, 5, 5], "y": [1, 1, 1, 5, 5], "nbinsx": 3, "nbinsy": 3, **kw}


def test_block_puts_the_highest_y_row_first_and_labels_the_bins():
    hb, notes, _n = wa._h2_block(_blk(title="T", scale="Viridis"))
    assert hb["type"] == "heatmap" and hb["title"] == "T" and hb["scale"] == "Viridis"
    xe, ye, counts = wa._h2_bin([1.0, 1.0, 5.0, 5.0, 5.0], [1.0, 1.0, 1.0, 5.0, 5.0], 3, 3)
    assert hb["data"] == counts[::-1] and sum(map(sum, hb["data"])) == 5
    assert len(hb["labels_x"]) == len(xe) and len(hb["labels_y"]) == len(ye)
    assert hb["labels_y"][0].startswith(wa._hg_num(ye[-1][0], wa._hg_decimals([e for p in ye for e in p])))
    assert hb["show_values"] is True and hb["show_colorbar"] is True


def test_block_notes_say_what_the_axes_are():
    _, notes, _n = wa._h2_block(_blk(x_label="Age", y_label="Spend"))
    assert "Age" in notes and "Spend" in notes and "5 points" in notes and "top" in notes


def test_bins_never_exceed_the_heatmap_cap():
    xs = [i * 0.37 for i in range(300)]
    hb, notes, _n = wa._h2_block({"type": "histogram2d", "x": xs, "y": list(reversed(xs)), "nbinsx": 40, "nbinsy": 40})
    assert len(hb["labels_x"]) <= 40 and len(hb["labels_y"]) <= 40


def test_unusable_pairs_are_skipped_with_a_note_and_never_thrown_on():
    hb, notes, _n = wa._h2_block({"type": "histogram2d", "x": [1, 2, "a", None, 4, True], "y": [1, 2, 3, 4, float("nan"), 6]})
    assert sum(map(sum, hb["data"])) == 2 and "4 " in notes and "skipped" in notes


def test_too_many_points_are_capped_with_a_note():
    n = 20050
    hb, notes, _n = wa._h2_block({"type": "histogram2d", "x": [i % 97 for i in range(n)], "y": [i % 89 for i in range(n)]})
    assert sum(map(sum, hb["data"])) == 20000 and "20,000" in notes


@pytest.mark.parametrize("b", [
    {"type": "histogram2d"}, {"type": "histogram2d", "x": [], "y": []}, {"type": "histogram2d", "x": [1], "y": [1]},
    {"type": "histogram2d", "x": "abc", "y": {"a": 1}}, {"type": "histogram2d", "x": [1, 2, 3], "y": [1]},
    {"type": "histogram2d", "x": [1e300, -1e300], "y": [1, 2]}, {"type": "histogram2d", "x": [3, 3, 3], "y": [4, 4, 4]},
    {"type": "histogram2d", "x": [1, 2, 3], "y": [1, 2, 3], "nbinsx": "x", "nbinsy": -5, "scale": ATTACK, "title": ATTACK, "x_label": ATTACK, "version": 3},
])
def test_malformed_input_never_throws_or_prints_junk(b, core_js):
    py = _py(dict(b))
    gas = _gas_batch(core_js, [b])[0]
    for h in (py, gas):
        assert isinstance(h, str) and not BAD.search(re.sub(r"<[^>]*>", " ", h)), h[:300]
        assert "<script" not in h.lower() and "onerror=alert(1)" not in h.replace("&quot;", '"') or "&lt;" in h


def test_too_few_points_say_so():
    assert "at least two" in _py({"type": "histogram2d", "x": [1], "y": [1]})


def test_hostile_text_is_escaped():
    h = _py(_blk(title=ATTACK, x_label=ATTACK, y_label=ATTACK))
    assert "<script>alert(4)" not in h and "<img src=x" not in h and "<svg onload" not in h


def test_version_note():
    assert "Written for histogram2d version 4; drawn as version 1." in _py(_blk(version=4))
    assert "Written for" not in _py(_blk(version=1))


# ─── drawn through the heatmap ─────────────────────────────────────────────────
def test_drawn_with_the_heatmap_options_and_a_hidden_table():
    h = _py(_blk())
    assert 'role="img"' in h and "Heatmap," in h and "<table" in h and 'class="hmc"' in h
    assert "points in" in h


def test_python_and_gas_emit_identical_html(core_js):
    bs = [_blk(), _blk(scale="Blues", x_label="a", y_label="b"), {"type": "histogram2d", "x": [i % 13 for i in range(300)], "y": [(i * 7) % 11 for i in range(300)]},
          {"type": "histogram2d", "x": [1], "y": [1]}, _blk(version=2, title="t")]
    gas = _gas_batch(core_js, bs)
    for b, g in zip(bs, gas):
        assert _py(dict(b)) == g


def test_python_and_gas_agree_on_block_notes(core_js):
    # parity that holds with or without the heatmap options: the heatmap renderer is each twin's own
    bs = [_blk(), _blk(x_label="a", y_label="b"), {"type": "histogram2d", "x": [1, 2, "a", None], "y": [1, 2, 3, 4]}, {"type": "histogram2d"}]
    gas = _gas_batch(core_js, bs)
    tail = lambda h: h[h.find("<div style=\"font-size:0.75rem") if "Columns bin" in h else 0:]   # from the notes on: the old heatmap twins differ on matrix data
    for b, g in zip(bs, gas):
        assert tail(_py(dict(b))) == tail(g)


# ─── registration ──────────────────────────────────────────────────────────────
def test_registered_as_a_preview_atom():
    sch = yaml.safe_load((ROOT / "atoms/schema.yaml").read_text())
    e = [x for x in sch["blocks"] if x.get("type") == "histogram2d"]
    assert len(e) == 1 and e[0].get("stage") == "preview"
    for k in ("description", "compact_description", "routing_text", "fields"):
        assert e[0].get(k), k
    assert len(e[0]["intent_phrases"]) == 3
    packs = yaml.safe_load((ROOT / "atoms/atom-packs.yaml").read_text())
    assert any("histogram2d" in (v if isinstance(v, list) else json.dumps(v)) for v in json.dumps(packs).split("\n")) or "histogram2d" in json.dumps(packs)


# ─── wave B fixes ──────────────────────────────────────────────────────────────
def test_default_wide_grid_gives_no_values_warning_and_one_wrapper(core_js):
    wide = {"type": "histogram2d", "x": [i % 41 for i in range(400)], "y": [(i * 7) % 43 for i in range(400)], "nbinsx": 20, "nbinsy": 4}
    gas = _gas_batch(core_js, [wide])[0]
    for h in (_py(dict(wide)), gas):
        assert "Values are not drawn above" not in h
        assert h.count("margin:var(--a2ui-block-gap,1.25rem) 0;") == 1
    asked = dict(wide, show_values=True)
    assert "Values are not drawn above" in _py(asked)
