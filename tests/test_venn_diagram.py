"""venn_diagram optional third set (I50, owner decision D9), ported by hand into BOTH renderers (Python and GAS).

No d3 module is involved, so there are no golden vectors: the three-circle layout is fixed and symmetric (NOT area-proportional, no venn.js).
Held here: a payload without set_c_name renders BYTE FOR BYTE as before (sha256 of the pre-change output of both twins, held in
tests/fixtures/venn_diagram_2set_baseline.json), Python/GAS HTML parity for 3-set payloads, the Region/Items hidden table, the aria label,
the per-region line caps with "+n more", malformed input, the `version` field, escaping and the schema entry.
The region geometry is measured in a browser by tests/test_venn_diagram_layout_box.py.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path

import pytest
import yaml

from test_histogram import ATTACK, _table
from test_motion_atoms import _gas_batch, _py, core_js  # noqa: F401  (core_js is a fixture)

ROOT = Path(__file__).resolve().parent.parent
BASE = json.loads((ROOT / "tests/fixtures/venn_diagram_2set_baseline.json").read_text())


def _v3(**kw):
    b = {"type": "venn_diagram", "set_a_name": "Design", "set_b_name": "Engineering", "set_c_name": "Product",
         "set_a_exclusive": ["Typography", "Colour", "Motion"], "set_b_exclusive": ["Compilers", "Testing"], "set_c_exclusive": ["Roadmap", "Pricing"],
         "intersection": ["Prototyping"], "intersection_ac": ["User research", "Journeys"], "intersection_bc": ["Estimation"], "intersection_abc": ["Design systems"]}
    b.update(kw)
    return b


PAYLOADS = {
    "full": _v3(title="Who owns what"),
    "sparse": {"type": "venn_diagram", "set_a_name": "A", "set_b_name": "B", "set_c_name": "C", "intersection_abc": ["Only the middle"]},
    "names_only": {"type": "venn_diagram", "set_a_name": "A", "set_b_name": "B", "set_c_name": "C"},
    "long": _v3(set_a_name="A" * 40, set_b_name="Engineering and platform reliability", set_c_name="Product management and strategy",
                set_a_exclusive=["An item whose text is much too long to fit a region at 320px wide"] + list("bcd")),
    "over_caps": _v3(set_a_exclusive=["a%d" % i for i in range(9)], set_c_exclusive=["c%d" % i for i in range(5)], intersection=["ab%d" % i for i in range(4)],
                     intersection_ac=["ac%d" % i for i in range(3)], intersection_bc=["bc0", "bc1", "bc2", "bc3"], intersection_abc=["x%d" % i for i in range(5)]),
    "at_caps": _v3(set_a_exclusive=list("abcde"), intersection=list("fgh"), intersection_abc=list("ijkl")),
    "huge": _v3(set_a_exclusive=["n%d" % i for i in range(75)]),
    "malformed": _v3(set_a_exclusive=["ok", None, {"x": 1}, ["y"], True, "", "  ", 7, 2.5, "last"], set_b_exclusive="not a list", intersection={"a": 1}, intersection_ac=5),
    "numeric_names": {"type": "venn_diagram", "set_a_name": 1, "set_b_name": None, "set_c_name": 3},
    "version_2": _v3(version=2),
    "version_junk": _v3(version=True),
}


@pytest.mark.parametrize("name", list(PAYLOADS))
def test_python_and_gas_emit_identical_html(name, core_js):
    assert _py(PAYLOADS[name]) == _gas_batch(core_js, [PAYLOADS[name]])[0]


# ─── the contract: a 2-set payload is byte for byte what it was ────────────────
@pytest.mark.parametrize("name", list(BASE))
def test_without_set_c_name_both_twins_render_exactly_the_pre_change_bytes(name, core_js):
    b = BASE[name]["payload"]
    want = BASE[name]["sha256"]
    assert hashlib.sha256(_py(b).encode()).hexdigest() == want
    assert hashlib.sha256(_gas_batch(core_js, [b])[0].encode()).hexdigest() == want


def test_the_new_fields_and_a_default_version_change_nothing_while_set_c_name_is_absent(core_js):
    extras = {"set_c_exclusive": ["x"], "intersection_ac": ["y"], "intersection_bc": ["z"], "intersection_abc": ["w"], "version": 1, "set_c_name": ""}
    for name in BASE:
        b = BASE[name]["payload"]
        with_extras = dict(b, **extras)
        assert _py(with_extras) == _py(b), name
        assert _gas_batch(core_js, [with_extras])[0] == _gas_batch(core_js, [b])[0], name


# ─── 3-set rendering ────────────────────────────────────────────────────────────
def test_three_set_table_lists_every_region_in_full(core_js):
    b = PAYLOADS["over_caps"]
    for html in (_py(b), _gas_batch(core_js, [b])[0]):
        head, rows = _table(html)
        assert head == ["Region", "Items"]
        assert [r[0] for r in rows] == ["Only Design", "Only Engineering", "Only Product", "Design and Engineering only", "Design and Product only", "Engineering and Product only", "All three sets"]
        assert rows[0][1] == "; ".join("a%d" % i for i in range(9)) and rows[1][1] == "Compilers; Testing"
        assert rows[6][1] == "x0; x1; x2; x3; x4"
        t = html.index("<table")
        assert 'role="img"' in html[:t] and 'role="img"' not in html[t:]
    _, rows = _table(_py(PAYLOADS["names_only"]))
    assert all(r[1] == "none" for r in rows)


def test_aria_label_names_the_sets_and_counts_every_region(core_js):
    for html in (_py(PAYLOADS["full"]), _gas_batch(core_js, [PAYLOADS["full"]])[0]):
        a = re.search(r'role="img" aria-label="([^"]*)"', html).group(1)
        assert a.startswith("Venn diagram of three sets: Design, Engineering and Product. Only Design: 3 items. Only Engineering: 2 items. Only Product: 2 items. ")
        assert "Design and Engineering only: 1 item. Design and Product only: 2 items. Engineering and Product only: 1 item. All three sets: 1 item. " in a
        assert a.endswith("not drawn to scale. Every item is in the table.")


def test_line_caps_per_region_and_a_plus_n_more_line(core_js):
    # lines per region: exclusive 5, pairwise 3, all three 4; over that, (lines - 1) items and "+k more" where k is what is left over
    for html in (_py(PAYLOADS["over_caps"]), _gas_batch(core_js, [PAYLOADS["over_caps"]])[0]):
        box = lambda r: re.search(r'<div class="v3t v3%s" data-r="%s".*?(?=<div class="v3t|</div></div><div style="display:flex;justify-content:center)' % (r, r), html, re.S).group(0)
        assert box("a").count('class="v3i"') == 5 and "+5 more" in box("a") and "a3" in box("a") and "a4" not in box("a")
        assert box("c").count('class="v3i"') == 5 and "c4" in box("c") and "more" not in box("c")      # exactly 5 items: all shown, no "+1 more"
        assert box("ab").count('class="v3i"') == 3 and "+2 more" in box("ab") and "ab1" in box("ab") and "ab2" not in box("ab")
        assert box("ac").count('class="v3i"') == 3 and "more" not in box("ac")
        assert box("bc").count('class="v3i"') == 3 and "+2 more" in box("bc")
        assert box("abc").count('class="v3i"') == 4 and "+2 more" in box("abc") and "x2" in box("abc") and "x3" not in box("abc")
    h = _py(PAYLOADS["at_caps"])
    assert "more" not in h.split("<table")[0].replace("Three fixed circles, not drawn to scale", "")


def test_empty_regions_draw_no_text_box_and_every_circle_is_drawn(core_js):
    for html in (_py(PAYLOADS["sparse"]), _gas_batch(core_js, [PAYLOADS["sparse"]])[0]):
        assert re.findall(r'class="v3t v3(\w+)"', html) == ["abc"] and html.count('class="v3o"') == 3
        assert "Only the middle" in html


def test_the_note_says_not_to_scale_and_no_script(core_js):
    for html in (_py(PAYLOADS["full"]), _gas_batch(core_js, [PAYLOADS["full"]])[0]):
        assert "Three fixed circles, not drawn to scale" in html and "<script" not in html.lower()
        assert "NaN" not in html and "undefined" not in html and "Infinity" not in html and "[object" not in html


def test_item_text_boxes_are_never_below_12px_and_use_theme_tokens():
    h = _py(PAYLOADS["full"])
    sizes = [float(x) for x in re.findall(r"font-size:([\d.]+)px", h)]
    assert sizes and min(sizes) >= 12
    assert "var(--text," in h and "var(--muted," in h and "var(--accent," in h


def test_malformed_items_are_skipped_and_explained(core_js):
    for h in (_py(PAYLOADS["malformed"]), _gas_batch(core_js, [PAYLOADS["malformed"]])[0]):
        _, rows = _table(h)
        assert rows[0][1] == "ok; 7; 2.5; last"
        assert rows[1][1] == rows[3][1] == rows[4][1] == "none"
        assert "6 entries were not text or a number and were skipped." in h
        assert "NaN" not in h and "undefined" not in h and "[object" not in h


def test_only_the_first_sixty_items_of_a_region_are_read_and_the_note_says_so(core_js):
    for h in (_py(PAYLOADS["huge"]), _gas_batch(core_js, [PAYLOADS["huge"]])[0]):
        assert "15 entries beyond the first 60 in a region were left out." in h
        assert _table(h)[1][0][1].count(";") == 59


def test_unnamed_or_numeric_names_get_a_label(core_js):
    for h in (_py(PAYLOADS["numeric_names"]), _gas_batch(core_js, [PAYLOADS["numeric_names"]])[0]):
        assert "Venn diagram of three sets: 1, Set B and 3." in h


def test_version_above_one_is_noted_and_otherwise_silent(core_js):
    for h in (_py(PAYLOADS["version_2"]), _gas_batch(core_js, [PAYLOADS["version_2"]])[0]):
        assert "Written for venn_diagram version 2; drawn as version 1." in h
    assert "version" not in _py(PAYLOADS["version_junk"]).lower()
    assert _py(dict(PAYLOADS["full"], version=1)) == _py(PAYLOADS["full"])
    # the 2-set drawing carries the same note
    assert "Written for venn_diagram version 3; drawn as version 1." in _py(dict(BASE["example"]["payload"], version=3))


def test_hostile_text_is_escaped_in_both_twins(core_js):
    b = _v3(title=ATTACK, set_a_name=ATTACK, set_b_name=ATTACK, set_c_name=ATTACK, set_a_exclusive=[ATTACK], intersection_abc=[ATTACK])
    for h in (_py(b), _gas_batch(core_js, [b])[0]):
        assert "<img" not in h and "<script" not in h.replace("<style", "") and 'onerror=alert(1)>' not in h.replace("&gt;", "")


# ─── registration ─────────────────────────────────────────────────────────────
def test_schema_documents_the_new_fields_and_the_fixed_layout():
    blocks = {a["type"]: a for a in yaml.safe_load((ROOT / "atoms/schema.yaml").read_text())["blocks"]}
    a = blocks["venn_diagram"]
    assert {"set_c_name", "set_c_exclusive", "intersection_ac", "intersection_bc", "intersection_abc", "version"} <= set(a["fields"])
    assert "not area-proportional" in a["notes"] and "venn.js" in a["notes"]
    assert "intersection" in a["fields"] and "A and B only" in a["fields"]["intersection"]


# ─── a cut item always says it was cut ─────────────────────────────────────────
def _item_lines(html):
    return re.findall(r'<div class="v3i" style="[^"]*">• ([^<]*)</div>', html)


def test_every_cut_item_ends_in_an_ellipsis_and_an_uncut_one_does_not(core_js):
    exact, over = "x" * 28, "An item whose text is much too long to fit a region at 320px wide"
    b = _v3(set_a_exclusive=[exact, over, "y" * 29, "z" * 60, "short"], set_b_exclusive=["w" * 200])
    for html in (_py(b), _gas_batch(core_js, [b])[0]):
        lines = _item_lines(html)
        assert exact in lines and "short" in lines                                    # 28 characters or fewer: untouched
        cut = [l for l in lines if l.endswith("\u2026")]
        assert len(cut) == 4 and all(2 <= len(l) <= 28 for l in cut), cut        # over, 29 x, 60 x and 200 x characters
        assert exact in lines and "short" in lines and len(lines) == 13, lines   # the other items are whole and unmarked
        assert over[:60] in html.split("<table")[1]                                        # the table keeps the text (60 characters at most, as before)


def test_the_long_payload_has_no_mid_word_cut_without_an_ellipsis(core_js):
    for html in (_py(PAYLOADS["long"]), _gas_batch(core_js, [PAYLOADS["long"]])[0]):
        assert "An item whose text is much t…" in html or "An item whose text is much…" in html
        assert "much t</div>" not in html


def test_a_cut_set_name_ends_in_an_ellipsis_too_in_the_legend_and_the_label(core_js):
    cut = lambda t: t[:27].rstrip() + "\u2026"
    names = [cut("A" * 40), cut("Engineering and platform reliability"), cut("Product management and strategy")]
    for html in (_py(PAYLOADS["long"]), _gas_batch(core_js, [PAYLOADS["long"]])[0]):
        assert all(">" + n + "</span>" in html for n in names), names
        assert "Only " + names[0] in html and "Only " + names[2] in html                # the aria label and the table use the same cut name
