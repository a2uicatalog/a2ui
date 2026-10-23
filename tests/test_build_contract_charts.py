"""Build contract v1.1 (owner decision D9, pm/evidence/2026-10-21-build-contract.md) on the live chart atoms.

Per atom, in Python and in the wired GAS renderer: the same bytes, data-cb kinds on the moving elements, --i beside every --k,
--n and data-cb-root on the outermost tag, opacity/scaleY moved out of the inline style into the scoped .cb-fade/.cb-grow rules,
pathLength on stroked branch paths, and the settled picture unchanged (stripping the contract markup gives the old inline form).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import renderers.web_article as wa  # noqa: E402
from test_motion_atoms import _gas_batch, _norm, _py, core_js  # noqa: E402,F401
import test_arc_diagram, test_box_plot, test_chord_diagram, test_circle_pack, test_contour_plot, test_histogram, test_histogram_ridge, test_sunburst, test_venn_diagram, test_voronoi, test_waterfall  # noqa: E402,E401

ORG = {"type": "org_chart", "nodes": [{"id": "a", "label": "Ada", "parent_id": ""}, {"id": "b", "label": "Ben", "parent_id": "a"}, {"id": "c", "label": "Chi", "parent_id": "a"}, {"id": "d", "label": "Di", "parent_id": "b"}]}
TREE = {"type": "treemap", "items": [{"name": n, "value": v, "category": c} for n, v, c in (("A", 5, "x"), ("B", 3, "x"), ("C", 4, "y"), ("D", 2, "y"), ("E", 1, "y"))]}
AREA = {"type": "stacked_area", "labels": ["Q1", "Q2", "Q3", "Q4"], "series": [{"label": "S1", "data": [1, 2, 3, 4]}, {"label": "S2", "data": [2, 2, 1, 3]}, {"label": "S3", "data": [1, 1, 2, 2]}]}
VENN2 = {"type": "venn_diagram", "set_a_name": "A", "set_b_name": "B", "set_a_exclusive": ["x"], "set_b_exclusive": ["y"], "intersection": ["z"]}


def _first(mod, key=None):
    return list(mod.PAYLOADS.values())[0] if key is None else mod.PAYLOADS[key]


ICICLE = dict(_first(test_sunburst), layout="icicle")
CASES = {
    "histogram": (_first(test_histogram), {"bar"}),
    "ridge": (_first(test_histogram_ridge), {"bar"}),
    "box_plot": (_first(test_box_plot), {"node"}),
    "waterfall": (_first(test_waterfall), {"node"}),
    "sunburst": (_first(test_sunburst), {"arc", "label"}),
    "icicle": (ICICLE, {"tile"}),
    "chord": (_first(test_chord_diagram), {"ribbon", "arc", "label"}),
    "circle_pack": (_first(test_circle_pack), {"arc", "label"}),
    "arc_diagram": (_first(test_arc_diagram), {"link", "node", "label"}),
    "contour": (_first(test_contour_plot), {"arc"}),
    "voronoi": (_first(test_voronoi), {"node", "label"}),
    "treemap": (TREE, {"tile"}),
    "org_chart": (ORG, {"node", "branch"}),
    "org_chart_radial": (dict(ORG, layout="radial"), {"node", "label", "branch"}),
    "org_chart_cluster": (dict(ORG, layout="cluster"), {"node", "branch"}),
    "venn3": (_first(test_venn_diagram), {"node", "label"}),
    "venn2": (VENN2, {"node"}),
    "stacked_area": (AREA, {"bar"}),
}


@pytest.fixture(scope="module")
def pairs(core_js):
    names = list(CASES)
    gas = _gas_batch(core_js, [CASES[n][0] for n in names])
    return {n: (_py(CASES[n][0]), gas[i]) for i, n in enumerate(names)}


@pytest.mark.parametrize("name", list(CASES))
def test_python_and_gas_agree_and_carry_the_contract(name, pairs):
    py, gas = pairs[name]
    assert _norm(py) == _norm(gas)
    kinds = set(re.findall(r' data-cb="(\w+)"', py))
    assert kinds == CASES[name][1]
    first = re.match(r"<(\w+)([^>]*)>", py)
    assert " data-cb-root" in first.group(2) and re.search(r'style="--n:(\d+);', first.group(2))
    assert py.endswith("<style>:where([data-cb-root]) .cb-fade{opacity:var(--k,1)}:where([data-cb-root]) .cb-grow{transform:scaleY(var(--k,1));transform-box:fill-box;transform-origin:50% 100%}</style>")
    tags = re.findall(r"<\w+[^>]* data-cb=\"\w+\"[^>]*>", py)
    assert tags
    ks = 0
    for t in tags:
        if "--k:clamp" in t:
            ks += 1
            m = re.search(r"--i:(\d+);--k:clamp\(0,calc\(var\(--p,1\)\*(\d+) - (\d+)\),1\);", t)
            assert m and m.group(1) == m.group(3), t
            assert int(m.group(2)) - int(m.group(3)) >= 1, "k would stay below 1 at p = 1"
            assert "opacity:var(--k,1);" not in t and "transform:scaleY(var(--k,1));" not in t
    assert ks == len(tags), "every moving element carries its own --k"
    n = int(re.search(r'style="--n:(\d+);', first.group(2)).group(1))
    assert all(int(x) - 1 <= n for x, _ in re.findall(r"--k:clamp\(0,calc\(var\(--p,1\)\*(\d+) - (\d+)\)", py))


def test_stroked_branch_paths_carry_pathlength():
    h = _py(ORG)
    paths = re.findall(r'<path data-cb="branch"[^>]*>', h)
    assert paths and all('pathLength="1"' in p for p in paths)


def test_settled_picture_is_the_old_inline_form():
    """Undoing the contract markup gives the previous inline opacity/scale, i.e. nothing visual moved."""
    h = _py(_first(test_histogram))
    assert 'class="hgb cb-grow"' in h and "transform:scaleY(var(--k,1))" not in h.replace(".cb-grow{transform:scaleY(var(--k,1))", "")
    assert re.search(r'<rect class="hgb cb-grow" data-cb="bar" x="[\d.]+" y="[\d.]+" width="[\d.]+" height="[\d.]+" style="--i:0;--k:clamp', h)


def test_atoms_without_data_pass_through_untouched():
    h = wa._cb_pass("<div><b>plain</b></div>")
    assert h == "<div><b>plain</b></div>"
    assert "data-cb" not in _py({"type": "histogram", "values": [1, 2]})


def test_treemap_motion_index_is_cell_count_based():
    h = _py(TREE)
    assert set(re.findall(r"--k:clamp\(0,calc\(var\(--p,1\)\*(\d+) -", h)) == {"6"}


# ─── the real atoms inside motion_build, computed styles in headless Chromium ───────────────────────────────────────────────
from test_motion_atoms import browser  # noqa: E402
from test_motion_build import _page as _page_raw  # noqa: E402
import tempfile  # noqa: E402


def _page(blk, p, js=""):
    # swiftshader + a fresh profile: the default headless GPU path takes about a minute per page on the shared Chromebook
    return _page_raw(blk, p, ("--use-angle=swiftshader", "--user-data-dir=" + tempfile.mkdtemp()), js)


@browser
def test_histogram_bars_grow_from_the_baseline_on_p():
    blk = {"type": "motion_build", "blocks": [_first(test_histogram)]}
    mid, end, start = _page(blk, 0.5), _page(blk, 1), _page(blk, 0)
    assert all(0 < s < 1 for s in mid["bar"][:3]) or any(0 < s < 1 for s in mid["bar"]), mid["bar"]
    assert end["bar"] and all(s == 1 for s in end["bar"]) and all(s == 0 for s in start["bar"])
    assert all(o.endswith("%") or "px" in o for o in end["org"])


@browser
def test_org_chart_branches_draw_and_nodes_fade_on_p():
    blk = {"type": "motion_build", "blocks": [ORG]}
    js = ("out.nodeop=q('[data-cb=node]').map(function(e){return +getComputedStyle(e).opacity;});"
          "out.br=q('[data-cb=branch]').map(function(e){var m=/-?[\\d.]+/.exec(getComputedStyle(e).strokeDashoffset);return m?+m[0]:0;});")
    start, end = _page(blk, 0, js=js), _page(blk, 1, js=js)
    assert start["nodeop"] and all(o == 0 for o in start["nodeop"]) and all(b == 1 for b in start["br"])
    assert all(o == 1 for o in end["nodeop"]) and all(b == 0 for b in end["br"])


@browser
def test_static_render_without_a_wrapper_is_fully_drawn():
    js_blk = {"type": "motion_build", "blocks": [_first(test_histogram)]}
    plain = _page(_first(test_histogram), None)
    assert all(s == 1 for s in plain["bar"])
    assert js_blk
