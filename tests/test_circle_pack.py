"""circle_pack (I46): d3-hierarchy pack() (packSiblings front chain and packEnclose with d3's fixed LCG), ported by hand into BOTH renderers.

GOLDEN (tests/fixtures/circle_pack_d3_golden.json, from circle_pack_d3_golden_gen.mjs) holds what the REAL d3-hierarchy 3.1.2
(hierarchy().sum().sort(by value descending), pack().size([w, h]).padding(3)) gives for 55 trees (hand cases and seeded fuzz of up to 60 leaves),
at two sizes, as [depth, x, y, r, value, name] for every node in eachBefore order.
 * Every x, y and r is compared with == in both twins: the algorithm uses only + - * / and Math.sqrt, which are correctly rounded IEEE operations in
   Python and V8 alike, and the twins keep d3's operation order and its single LCG (seed 1) shared by all groups in eachAfter order. The only
   places JavaScript and Python differ are x / 0 and sqrt of a negative number (Infinity or NaN in JavaScript); the twins return those values too.
Also held here: Python/GAS HTML parity, the hidden table, the aria label, the motion index, malformed input, caps with notes, the `version`
field, escaping, the label rule and registration.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

import pytest
import yaml

from test_histogram import ATTACK, _table
from test_motion_atoms import _gas_batch, _node, _py, core_js  # noqa: F401  (core_js is a fixture)
from test_motion_atoms import wa  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
D = json.loads((ROOT / "tests/fixtures/circle_pack_d3_golden.json").read_text())
CASES = D["cases"]


# ─── the layout against real d3 ────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("name", list(CASES))
def test_python_pack_matches_d3_exactly(name):
    c = CASES[name]
    for size, want in zip(D["sizes"], c["packs"]):
        assert [list(r) for r in wa._cp_rows(c["spec"], size[0], size[1], D["padding"])] == want


def test_gas_pack_matches_d3_exactly(core_js):
    names = list(CASES)
    res = _node(core_js, "var G = " + json.dumps([CASES[n]["spec"] for n in names]) + ", S = " + json.dumps(D["sizes"]) + ", P = " + json.dumps(D["padding"])
                + "; console.log(JSON.stringify(G.map(function(s){ return S.map(function(z){ return _cpRows(s, z[0], z[1], P); }); })));")
    for n, got in zip(names, res):
        assert got == CASES[n]["packs"], n


def test_the_golden_set_covers_the_hard_cases():
    assert len(CASES) == 55
    assert max(len(c["packs"][0]) for c in CASES.values()) >= 60
    assert len(CASES["one_chain"]["packs"][0]) == 5 and CASES["flat_two"]["packs"][0][0][3] == 300
    # a circle in a group lies inside it (with the padding), and no two siblings overlap
    for c in CASES.values():
        rows = c["packs"][0]
        assert rows[0][3] > 0 and all(math.isfinite(v) for r in rows for v in r[1:5])


def test_the_lcg_is_d3s_with_seed_one():
    r = wa._cp_lcg()
    want, s = [], 1
    for _ in range(5):
        s = (1664525 * s + 1013904223) % 4294967296
        want.append(s / 4294967296)
    assert [r() for _ in range(5)] == want


def test_degenerate_circles_never_raise_or_loop():
    for spec in ({"n": "r", "c": [{"n": "a", "v": 1}, {"n": "b", "v": 1}, {"n": "c", "v": 1}]},
                 {"n": "r", "c": [{"n": "a", "v": 1e-300}, {"n": "b", "v": 1e300}]},
                 {"n": "r", "c": [{"n": "a", "v": 5e-324}, {"n": "b", "v": 5e-324}, {"n": "c", "v": 1}]}):
        rows = wa._cp_rows(spec, 600, 600, 3)
        assert len(rows) == len(wa._cp_rows(spec, 600, 600, 3))


# ─── rendering ─────────────────────────────────────────────────────────────────────────────────────────────────
def _it(path, name, value):
    return ({"path": path} if path else {}) | {"name": name, "value": value}


BUDGET = [
    _it(["Operations", "Cloud"], "Compute", 420), _it(["Operations", "Cloud"], "Storage", 180), _it(["Operations", "Cloud"], "Network", 95),
    _it(["Operations", "Offices"], "Rent", 300), _it(["Operations", "Offices"], "Utilities", 60), _it(["Operations"], "Insurance", 70),
    _it(["People", "Engineering"], "Salaries", 900), _it(["People", "Engineering"], "Training", 40), _it(["People", "Sales"], "Salaries", 520),
    _it(["People", "Sales"], "Commission", 130), _it(["People"], "Recruiting", 85),
    _it(["Marketing", "Paid"], "Search", 160), _it(["Marketing", "Paid"], "Social", 110), _it(["Marketing", "Events"], "Conference", 75), _it(["Marketing"], "Content", 55),
    _it([], "Legal", 90),
]
FLAT = [_it([], "Rent", 300), _it([], "Salaries", 900), _it([], "Tools", 80), _it([], "Travel", 40)]
DEEP = [_it(["A", "B", "C"], "one", 50), _it(["A", "B", "C"], "two", 30), _it(["A", "B"], "three", 20), _it(["A"], "four", 10),
        _it(["D", "E", "F"], "five", 40), _it(["D", "E", "F"], "six", 25), _it(["D", "E", "F"], "seven", 5), _it(["D", "E"], "eight", 15), _it(["D"], "nine", 12), _it([], "ten", 8)]
SIXTY = [_it(["Group %d" % (k % 10), "Sub %d" % (k % 3)] if k % 4 else ["Group %d" % (k % 10)], "Item %d" % k, 1 + (k * 7) % 13 + k / 8) for k in range(60)]
PAYLOADS = {
    "budget": {"type": "circle_pack", "title": "Where the money goes", "unit": "k EUR", "items": BUDGET},
    "flat": {"type": "circle_pack", "items": FLAT},
    "two": {"type": "circle_pack", "items": [_it(["A"], "x", 3), _it(["B"], "y", 1)]},
    "one_group": {"type": "circle_pack", "items": [_it(["Only"], "a", 7), _it(["Only"], "b", 3)]},
    "deep": {"type": "circle_pack", "items": DEEP},
    "sixty": {"type": "circle_pack", "unit": "GB", "items": SIXTY},
    "sixty_one": {"type": "circle_pack", "items": [_it(["G%d" % (k % 5)], "Item %d" % k, k + 1) for k in range(61)]},
    "tiny_share": {"type": "circle_pack", "items": [_it(["Big"], "huge", 1e9), _it(["Big"], "tiny", 1e-9), _it(["Small"], "ok", 5)]},
    "long_names": {"type": "circle_pack", "items": [_it(["A very long group name!!"], "An item with a name of twenty-four chars", 40), _it(["A very long group name!!"], "Short", 5), _it(["Other"], "Another quite long item name", 30)]},
    "twelve_groups": {"type": "circle_pack", "items": [_it(["G%d" % k], "item %d" % k, 12 - k) for k in range(12)]},
    "bad_values": {"type": "circle_pack", "items": [_it(["A"], "zero", 0), _it(["A"], "neg", -3), _it(["A"], "str", "12"), _it(["A"], "junk", "x"), _it(["A"], "none", None), _it(["A"], "inf", float("inf")),
                                                     "text", None, 7, {"path": ["B"], "name": "good", "value": 5}, {"name": "ok", "value": 3.5}, {"name": 12, "value": 2}, {"path": ["B"], "value": 4}]},
    "path_junk": {"type": "circle_pack", "items": [{"path": ["a", "", "  ", 5, None, "b", "c", "d", "e"], "name": "x", "value": 3}, {"path": "notalist", "name": "y", "value": 2}, {"path": [], "name": "z", "value": 1},
                                                    {"path": ["a" * 40], "name": "w", "value": 1}]},
    "too_few": {"type": "circle_pack", "title": "T", "items": [_it(["A"], "only", 5)]},
    "no_items": {"type": "circle_pack"},
    "items_not_list": {"type": "circle_pack", "items": {"name": "x", "value": 3}},
    "all_bad": {"type": "circle_pack", "items": [_it([], "a", 0), _it([], "b", -1)]},
    "version_2": {"type": "circle_pack", "version": 2, "items": FLAT},
    "version_junk": {"type": "circle_pack", "version": True, "items": FLAT},
}


@pytest.mark.parametrize("name", list(PAYLOADS))
def test_python_and_gas_emit_identical_html(name, core_js):
    assert _py(PAYLOADS[name]) == _gas_batch(core_js, [PAYLOADS[name]])[0]


def test_hostile_text_python_and_gas_agree_and_are_escaped(core_js):
    b = {"type": "circle_pack", "title": ATTACK, "unit": ATTACK, "items": [_it([ATTACK], ATTACK, 5), _it([ATTACK, "x"], ATTACK, 3), _it([], ATTACK, 2)]}
    outs = [_py(b), _gas_batch(core_js, [b])[0]]
    assert outs[0] == outs[1]
    for h in outs:
        assert "<img" not in h and "<svg onload" not in h and "<script" not in h.replace("<style", "") and 'onerror=alert(1)>' not in h.replace("&gt;", "")
        assert "&lt;img" in h


def _circles(html):
    return re.findall(r'<circle cx="([\d.]+)" cy="([\d.]+)" r="([\d.]+)" ([^>]*)><title>(.*?)</title></circle>', html)


def test_draws_one_circle_per_node_with_a_title_and_a_hidden_table(core_js):
    for html in (_py(PAYLOADS["budget"]), _gas_batch(core_js, [PAYLOADS["budget"]])[0]):
        assert "<script" not in html and "<svg " in html and "NaN" not in html and "undefined" not in html
        cs = _circles(html)
        assert len(cs) == 16 + 9                                              # 16 items and 9 groups
        head, rows = _table(html)
        assert head == ["Item", "Path", "Value", "Share of total"] and len(rows) == 16
        t = html.index("<table")
        assert 'role="img"' in html[:t] and 'role="img"' not in html[t:]
        assert rows[0] == ["Compute", "Operations / Cloud", "420 k EUR", "%.1f%%" % (420 / 3290 * 100)]
        assert rows[-1][1] == "Top level"
        assert abs(sum(float(r[3][:-1]) for r in rows) - 100) < 1
        titles = [c[4] for c in cs]
        assert "Operations / Cloud / Compute: 420 k EUR (12.8%)" in titles and "Operations: 1,125 k EUR (34.2%)" in titles
        assert "Legal: 90 k EUR (2.7%)" in titles
        for cx, cy, r, *_ in cs:
            assert 0 <= float(cx) - float(r) and float(cx) + float(r) <= 600.01 and 0 <= float(cy) - float(r) and float(cy) + float(r) <= 600.01


def test_groups_are_outlined_and_leaves_are_filled():
    cs = _circles(_py(PAYLOADS["budget"]))
    groups = [c for c in cs if c[4].count(":") == 1 and 'fill="none"' in c[3]]
    leaves = [c for c in cs if 'fill="#' in c[3]]
    assert len(groups) == 9 and len(leaves) == 16 and all("stroke=" in g[3] for g in groups)


def test_aria_label_gives_total_group_count_and_largest_item(core_js):
    for html in (_py(PAYLOADS["budget"]), _gas_batch(core_js, [PAYLOADS["budget"]])[0]):
        a = re.search(r'role="img" aria-label="([^"]*)"', html).group(1)
        assert a == "Circle packing of 16 items in 4 top-level groups, total 3,290 k EUR. Largest item: Salaries, 900 k EUR, 27.4% of the total."
    a = re.search(r'aria-label="([^"]*)"', _py(PAYLOADS["one_group"])).group(1)
    assert a == "Circle packing of 2 items in 1 top-level group, total 10. Largest item: a, 7, 70.0% of the total."


def test_colour_follows_the_top_level_group_and_deeper_leaves_are_lighter():
    fills = {c[4].split(":")[0]: re.search(r'fill="(#[0-9A-F]{6})"', c[3]).group(1) for c in _circles(_py(PAYLOADS["budget"])) if 'fill="#' in c[3]}
    lum = lambda c: sum(int(c[i:i + 2], 16) for i in (1, 3, 5))
    assert fills["Operations / Cloud / Compute"] != fills["People / Engineering / Salaries"]
    assert lum(fills["Operations / Insurance"]) < lum(fills["Operations / Cloud / Compute"])
    assert fills["Operations / Cloud / Compute"] == fills["Operations / Offices / Rent"]
    assert fills["Legal"] == wa._sb_fill(wa._SB_PALETTE[3], 1)                # the 4th top-level entry in first-seen order (Operations, People, Marketing, Legal)


def test_text_is_never_below_12px_and_nothing_has_a_script():
    for n, b in PAYLOADS.items():
        h = _py(b)
        assert all(int(x) >= 12 for x in re.findall(r"font-size:(\d+)px", h)), n
        assert "<script" not in h and "NaN" not in h and "Infinity" not in h and "undefined" not in h and "[object Object]" not in h, n


def test_motion_index_per_depth_stays_inside_its_clamp(core_js):
    for name, depths in (("budget", 3), ("deep", 4), ("flat", 1)):
        for html in (_py(PAYLOADS[name]), _gas_batch(core_js, [PAYLOADS[name]])[0]):
            ks = re.findall(r'<g class="cpr" style="--k:clamp\(0,calc\(var\(--p,1\)\*(\d+) - (\d+)\),1\);', html)
            assert [int(i) for _, i in ks] == list(range(depths)) and all(int(n) == depths + 1 for n, _ in ks), name


def test_malformed_items_are_dropped_and_explained(core_js):
    for h in (_py(PAYLOADS["bad_values"]), _gas_batch(core_js, [PAYLOADS["bad_values"]])[0]):
        head, rows = _table(h)
        assert [r[0] for r in rows] == ["str", "good", "ok", "12", "Item 13"] and [r[1] for r in rows] == ["A", "B", "Top level", "Top level", "B"]
        assert "8 entries had no value above 0 or were not an item and were left out." in h
        assert "NaN" not in h and "undefined" not in h and "[object Object]" not in h


def test_path_keeps_three_usable_names_of_twenty_characters():
    _, rows = _table(_py(PAYLOADS["path_junk"]))
    assert rows[0][1] == "a / b / c" and rows[1][1] == "Top level" and rows[2][1] == "Top level" and rows[3][1] == "a" * 20


def test_too_few_or_no_items_gives_a_note_and_no_chart():
    for k in ("too_few", "no_items", "items_not_list", "all_bad"):
        h = _py(PAYLOADS[k])
        assert "A circle pack needs at least 2 items with a value above 0." in h
        assert 'role="img"' not in h and "<table" not in h and "NaN" not in h
    assert ">T</div>" in _py(PAYLOADS["too_few"])


def test_only_the_first_sixty_items_are_read():
    h = _py(PAYLOADS["sixty_one"])
    assert len(_table(h)[1]) == 60 and "1 item beyond the first 60 was not drawn." in h
    assert "Item 60" not in h
    assert len(_table(_py(PAYLOADS["sixty"]))[1]) == 60


def test_the_largest_item_is_packed_first_by_d3s_descending_sort():
    titles = [c[4].split(":")[0] for c in _circles(_py(PAYLOADS["budget"]))]
    tops = [t for t in titles if "/" not in t]
    assert tops[:4] == ["People", "Operations", "Marketing", "Legal"]


def test_tiny_share_has_no_label_and_no_nan():
    h = _py(PAYLOADS["tiny_share"])
    assert "NaN" not in h and "Infinity" not in h
    assert len(_circles(h)) == 5


def test_version_above_one_is_noted_and_otherwise_silent(core_js):
    for h in (_py(PAYLOADS["version_2"]), _gas_batch(core_js, [PAYLOADS["version_2"]])[0]):
        assert "Written for circle_pack version 2; drawn as version 1." in h
    assert "version" not in _py(PAYLOADS["version_junk"]).lower()
    assert _py(dict(PAYLOADS["flat"], version=1)) == _py(PAYLOADS["flat"])


# ─── the label rule ────────────────────────────────────────────────────────────────────────────────────────────
K = wa._CP_K


def _leaf_labels(html):
    """(gate of the name, gate of the value or 0, left %, top %, name, value or None) of every leaf label."""
    return [(int(m.group(3) or 0), int(m.group(5) or 0), float(m.group(1)), float(m.group(2)), m.group(4), m.group(6))
            for m in re.finditer(r'<div class="cpl" style="position:absolute;left:([\d.]+)%;top:([\d.]+)%;[^"]*"><div class="cpn(?: tmw(\d+))?" style="[^"]*">(.*?)</div>'
                                 r'(?:<div class="cpv(?: tmw(\d+))?" style="[^"]*">(.*?)</div>)?</div>', html)]


def _group_labels(html):
    """(gate, left %, top %, name) of every group label."""
    return [(int(m.group(1) or 0), float(m.group(2)), float(m.group(3)), m.group(4))
            for m in re.finditer(r'<div class="cpg(?: tmw(\d+))?" style="position:absolute;left:([\d.]+)%;top:calc\(([\d.]+)% \+ 10px\);[^"]*">(.*?)</div>', html)]


def _radius_at(circles, left, top):
    """The radius of the circle whose centre the label's left/top percentages (of the 604 box that starts at -2) name."""
    for cx, cy, r, *_ in circles:
        if abs((float(cx) + 2) / 604 * 100 - left) < 0.002 and abs((float(cy) + 2) / 604 * 100 - top) < 0.002:
            return float(r)
    raise AssertionError((left, top))


def test_a_leaf_label_is_gated_to_the_container_width_where_its_circle_holds_it():
    h = _py(PAYLOADS["budget"])
    cs = _circles(h)
    labs = _leaf_labels(h)
    assert labs and len(labs) <= 16
    ws = sorted({w for g, v, *_ in labs for w in (g, v) if w})
    assert ws and all(w % 10 == 0 and w <= 640 for w in ws)
    css = re.search(r"<style>(.*?)</style>", h).group(1)
    assert all("@container (width<%dpx){.tmw%d{display:none}}" % (w, w) in css for w in ws)
    for g, v, left, top, name, val in labs:
        r = _radius_at(cs, left, top)
        # at the narrowest width where the gate lets the name show (the gate itself is the width the circle needs; ungated means 240 or less)
        w = max(g, 240)
        px = r * w / 600
        c = min(len(name), 6)
        assert px >= math.sqrt((c * K / 2) ** 2 + 49) + 2 - 1e-9 and px >= (c * K + 4) / 1.4 - 1e-9 and px >= 21 - 1e-9, (name, g, px)
        if val:
            wv = max(v, 240)
            pv = r * wv / 600
            assert wv >= w and pv >= math.sqrt((len(val) * K / 2) ** 2 + 196) + 2 - 1e-9 or val is None, (name, val)


def test_a_group_label_sits_inside_the_top_of_its_circle_where_it_fits():
    h = _py(PAYLOADS["budget"])
    groups = [c for c in _circles(h) if 'fill="none"' in c[3]]
    labs = _group_labels(h)
    assert labs and len(labs) <= len(groups)
    for g, left, top, name in labs:
        for cx, cy, r, *_ in groups:
            if abs((float(cx) + 2) / 604 * 100 - left) < 0.002 and abs((float(cy) - float(r) + 2) / 604 * 100 - top) < 0.002:
                px = float(r) * max(g, 240) / 600
                assert px >= 40 - 1e-9 and 0.8 * px >= min(len(name), 6) * K + 8 - 1e-9, (name, px)
                break
        else:
            raise AssertionError(name)


def test_a_circle_too_small_for_a_name_has_no_label():
    assert len(_leaf_labels(_py(PAYLOADS["sixty"]))) < 60
    assert len(_leaf_labels(_py(PAYLOADS["flat"]))) == 4


def test_registered_as_a_preview_charts_atom_with_an_example_and_every_field_documented():
    blocks = {a["type"]: a for a in yaml.safe_load((ROOT / "atoms/schema.yaml").read_text())["blocks"]}
    a = blocks["circle_pack"]
    assert a["stage"] == "preview" and set(a["fields"]) == {"title", "items", "unit", "version"}
    assert a["surfaces"] == blocks["treemap"]["surfaces"] and a["source"] == blocks["treemap"]["source"]
    assert "treemap" in a["routing_text"] and "bar chart" in a["routing_text"] and "grouping and rough size" in a["routing_text"] and len(a["intent_phrases"]) == 3
    assert re.search(r"^a2ui-charts-v1:\n(?:- .*\n)*- circle_pack$", (ROOT / "atoms/atom-packs.yaml").read_text(), re.M)
    assert '"circle_pack":"a2ui-charts-v1"' in (ROOT / "apps-script-surface/gas-wired-renderer/PackMap.gs").read_text()
    import generate_atom_pages as g
    ex = g._EXAMPLE_BLOCKS["circle_pack"]
    assert ex["type"] == "circle_pack" and "<table" in _py(ex) and "<circle" in _py(ex)
    txt = (ROOT / "atoms/schema.yaml").read_text()
    assert txt.index("- type: circle_pack") < txt.index("# ── Motion candidates (2026-10-10, preview) ──")


def test_d3_credit_names_pack():
    t = (ROOT / "THIRD-PARTY-NOTICES.md").read_text()
    assert "packSiblings" in t and "tests/test_circle_pack.py" in t
