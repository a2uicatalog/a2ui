"""stacked_area `layout` (D22, owner decision 2026-10-21): "area" (the default) draws the SVG stacked area chart the schema always
described; "bars" keeps the CSS bar list, byte for byte (tests/test_stacked_area_offset.py and test_stacked_area_bars_crash.py pin
those bytes under layout "bars").

Held here: absent / null / unknown layout means "area"; the default is the zero-baseline chart (d3.stack() with no offset, golden
vectors from the real d3-shape in tests/fixtures/stacked_area_d3_golden.json, mode "none"); `offset` still works on top of it;
layout "bars" wins over an offset (the bars ignore it and say so); every payload that rendered before renders without throwing
and without NaN/undefined in both layouts and both twins; Python and Apps Script emit identical HTML.
"""
from __future__ import annotations

import json
import re

import pytest

from test_motion_atoms import _gas_batch, _py, core_js  # noqa: F401
from test_stacked_area_bars_crash import BEFORE
from test_stacked_area_offset import ATTACK, BASE, CASES, JUNK, _block, _pyx, _table

BAD_WORDS = ("NaN", "undefined", "Infinity", "[object Object]")
JUNK_LAYOUT = [None, "area ", "AREA", "Bars", "bar", "BARS", "stacked", "", 0, 1, True, False, [], ["bars"], {}, {"a": 1}, 1.5]
CRASH = [
    {"type": "stacked_area", "labels": ["a", "b"], "series": [{"label": "A", "data": [0, 0]}]},
    {"type": "stacked_area", "labels": ["a", "b"], "series": [{"label": "A", "data": [1, "x"]}]},
    {"type": "stacked_area", "labels": ["a", "b"], "series": [{"label": "A", "data": [None, True]}, {"label": "B", "data": [{"k": 1}, [2]]}]},
    {"type": "stacked_area", "labels": ["a"], "series": [{"label": "A", "data": [float("nan")]}]},
]
EVERY = {**{f"base_{k}": v for k, v in BASE.items()}, **{f"before_{k}": b for k, (b, _) in BEFORE.items()}, **{f"crash{i}": c for i, c in enumerate(CRASH)}}


def _strip(h):
    return re.sub(r"<style>.*?</style>", "", h, flags=re.S).replace("var(--", "")


def _clean(name, h):
    for w in BAD_WORDS:
        assert w not in _strip(h), (name, w)
    assert "inf%" not in h and "nan%" not in h


def _aria(h):
    return re.search(r'aria-label="([^"]*)"', h).group(1)


def _polys(h):
    return [[tuple(float(t) for t in q.split(",")) for q in p.split()] for p in re.findall(r'<polygon (?:data-cb="bar" )?points="([^"]*)"', h)]


# ─── the default is the area chart ────────────────────────────────────────────
def test_the_default_layout_is_the_svg_area_chart(core_js):
    b = BASE["showcase"]
    for h in (_py(b), _gas_batch(core_js, [b])[0]):
        assert h.count("<svg") == 1 and h.count("<polygon") == 3 and "<script" not in h
        assert re.search(r'<div role="img" aria-label="Stacked area chart, zero baseline: 3 series over 4 points from Q1 to Q4\. Series: Core, LMS, Charts\."', h)
        assert 'display:flex;">' not in h and "inline-block;\" title=" not in h        # none of the bar list's markup


@pytest.mark.parametrize("junk", JUNK_LAYOUT, ids=lambda j: json.dumps(j))
def test_absent_null_and_unknown_layouts_mean_area(junk, core_js):
    blocks = [dict(b) for b in BASE.values()]
    want_py = [_pyx(b) for b in blocks]
    want_gas = _gas_batch(core_js, blocks)
    junked = [{**b, "layout": junk} for b in blocks]
    assert [_pyx(b) for b in junked] == want_py
    assert _gas_batch(core_js, junked) == want_gas
    assert want_py == want_gas
    assert all("<svg" in h or "needs at least two labels" in h for h in want_py)


@pytest.mark.parametrize("junk", JUNK, ids=lambda j: json.dumps(j))
def test_none_and_unknown_offsets_in_the_default_layout_are_the_zero_baseline_chart(junk, core_js):
    blocks = [dict(b) for b in BASE.values()]
    junked = [{**b, "offset": junk} for b in blocks]
    assert [_pyx(b) for b in junked] == [_pyx(b) for b in blocks]
    assert _gas_batch(core_js, junked) == _gas_batch(core_js, blocks)


def test_offset_none_spelled_out_is_the_default(core_js):
    b = _block(CASES["three_by_four"]["values"])
    assert _py({**b, "offset": "none"}) == _py(b) == _py({**b, "layout": "area"})


@pytest.mark.parametrize("name", list(CASES))
def test_the_default_picture_reproduces_d3_stack_with_no_offset(name):
    c = CASES[name]
    vals, g = c["values"], c["none"]
    m = len(vals[0])
    if m < 2:
        return
    polys = _polys(_py(_block(vals)))
    assert len(polys) == len(vals)
    top = max(max(r) for r in g["hi"])
    ys = [y for p in polys for _, y in p]
    # the axis is fitted to a "nice" maximum >= the tallest stack: recover it from where the tallest stack lands, then check every vertex against d3
    ymax = top * 100 / (100 - min(ys)) if top > 0 else 1.0
    assert top <= ymax * (1 + 1e-4) and ymax < top * 2.5 + 1e-9
    for i, p in enumerate(polys):
        hi, lo = p[:m], p[m:][::-1]
        for j in range(m):
            assert abs(hi[j][0] - j / (m - 1) * 1000) < 0.006 and abs(lo[j][0] - j / (m - 1) * 1000) < 0.006
            assert abs(hi[j][1] - (ymax - g["hi"][i][j]) / ymax * 100) < 0.02, (name, i, j)
            assert abs(lo[j][1] - (ymax - g["lo"][i][j]) / ymax * 100) < 0.02, (name, i, j)
    assert max(ys) == 100.0                                                              # the first layer sits on the baseline


def _axis(vals):
    return [re.sub(r"<.*?>", "", x) for x in re.findall(r'<div class="say".*?</div>', _py(_block(vals)))]


def test_axis_ticks_for_known_totals():
    assert _axis([[1, 2, 3, 4]]) == ["0", "1", "2", "3", "4"]
    assert _axis([[10, 20], [90, 80]]) == ["0", "50", "100"]
    assert _axis([[1500, 3000]]) == ["0", "1k", "2k", "3k"]
    assert _axis([[0.1, 0.2, 0.4]]) == ["0", "0.1", "0.2", "0.3", "0.4"]
    assert _axis([[2e6, 5e6]]) == ["0", "2M", "4M", "6M"]
    assert _axis([[0, 0, 0]]) == ["0"]
    for n in ("three_by_four", "decimals", "huge_and_tiny", "series_twelve_pts_ten", "integers_nine"):
        t = _axis(CASES[n]["values"])
        assert t[0] == "0" and 2 <= len(t) <= 6 and len(set(t)) == len(t), (n, t)


def test_a_note_tells_the_reader_how_to_read_the_stack():
    h = _py(_block([[1, 2, 3], [3, 2, 1]]))
    assert "The top edge is the total of all layers; each layer’s thickness is its own value, and the exact values are in the table." in h
    z = _py(_block([[0, 0, 0], [0, 0, 0]]))
    assert "Every value is 0, so there is nothing to draw above the baseline." in z
    assert "<svg" in z and z.count("<polygon") == 2


def test_offsets_still_work_on_top_of_the_default(core_js):
    b = _block(CASES["three_by_four"]["values"])
    for off in ("expand", "silhouette", "wiggle"):
        assert _py({**b, "offset": off, "layout": "area"}) == _py({**b, "offset": off}) != _py(b)
        assert _gas_batch(core_js, [{**b, "offset": off}])[0] == _py({**b, "offset": off})


def test_the_default_fallback_message_says_how_to_get_the_bars(core_js):
    for b in ({"type": "stacked_area", "labels": ["a"], "series": [{"label": "x", "data": [1]}]},
              {"type": "stacked_area", "title": "T", "labels": [], "series": [{"label": "x", "data": [1, 2]}]},
              {"type": "stacked_area", "labels": ["a", "b"], "series": []},
              {"type": "stacked_area", "labels": ["a", "b"], "series": "x"},
              {"type": "stacked_area"}):
        for h in (_py(b), _gas_batch(core_js, [b])[0]):
            assert "A stacked area chart needs at least two labels and one series with numbers. Set layout to bars for a bar list." in h and "<svg" not in h
    # a payload that names an offset keeps the message it always had
    h = _py({"type": "stacked_area", "offset": "expand", "labels": ["a"], "series": [{"label": "x", "data": [1]}]})
    assert "A stacked area chart with an offset needs at least two labels and one series with numbers." in h


# ─── layout "bars" ─────────────────────────────────────────────────────────────
def test_layout_bars_is_the_bar_list(core_js):
    for b in (BASE["showcase"], BASE["mrr"]):
        for h in (_py({**b, "layout": "bars"}), _gas_batch(core_js, [{**b, "layout": "bars"}])[0]):
            assert "<svg" not in h and 'display:flex;' in h and "title=" in h


def test_bars_ignore_an_offset_and_say_so(core_js):
    b = {**BASE["showcase"], "layout": "bars"}
    plain = _py(b)
    for off in ("expand", "silhouette", "wiggle"):
        h = _py({**b, "offset": off})
        assert "<svg" not in h and h.startswith(plain[:-len("</div>")][:200])
        note = f"The bar list has no offset; “{off}” only applies to the area layout."
        assert note in h and h.replace(note, "").count("Written for") == 0
        assert h == plain + '<div style="font-size:0.75rem;color:var(--muted,#475569);margin-top:4px;">' + note + "</div>"
        gas_plain = _gas_batch(core_js, [b])[0]                                           # the two bar lists have always differed in bytes
        assert _gas_batch(core_js, [{**b, "offset": off}])[0] == gas_plain + '<div style="font-size:0.75rem;color:var(--muted,#475569);margin-top:4px;">' + note + "</div>"
    for quiet in (None, "none", "bogus", 3, [], ""):
        assert _py({**b, "offset": quiet}) == plain                                       # no note when the offset would not have mattered
    h = _py({**b, "offset": "wiggle", "version": 2})
    assert h.index("has no offset") < h.index("Written for stacked_area version 2")


def test_the_version_note_follows_the_layout(core_js):
    for lay in ("bars", "area"):
        b = {**BASE["mrr"], "layout": lay, "version": 2}
        assert "Written for stacked_area version 2; drawn as version 1." in _py(b)
        if lay == "area":
            assert _gas_batch(core_js, [b])[0] == _py(b)
        else:
            assert "Written for stacked_area version 2; drawn as version 1." in _gas_batch(core_js, [b])[0]
        assert "Written for" not in _py({**b, "version": 1})


# ─── nothing that rendered before throws or prints junk, in either layout and twin ──
@pytest.mark.parametrize("layout", ["area", "bars", None])
def test_every_known_payload_renders_clean_in_both_twins(layout, core_js):
    blocks = {n: ({**b, "layout": layout} if layout else dict(b)) for n, b in EVERY.items()}
    gas = dict(zip(blocks, _gas_batch(core_js, list(blocks.values()))))
    for n, b in blocks.items():
        h = _py(b)                                                                        # must not raise
        _clean(n, h)
        _clean(n, gas[n])
        if layout != "bars":
            assert h == gas[n], n
    if layout == "area":
        for n in ("base_showcase", "crash0", "crash1", "crash2"):
            assert "<svg" in _py(blocks[n]) and "role=\"img\"" in _py(blocks[n])


def test_the_crash_payloads_keep_raw_values_in_the_table():
    h = _py({**CRASH[1], "layout": "area"})
    head, rows = _table(h)
    assert rows == [["a", "1"], ["b", ""]]                                                # the text cell is blank in the table, drawn as 0
    assert "1 value was negative or not a usable number and is drawn as 0." in h
    z = _py({**CRASH[0], "layout": "area"})
    assert "Every value is 0" in z and "NaN" not in z


def test_hostile_text_is_escaped_in_both_layouts():
    b = {"type": "stacked_area", "title": ATTACK, "labels": [ATTACK, "b"], "series": [{"label": ATTACK, "data": [1, 2], "color": ATTACK}]}
    for lay in ("area", "bars"):
        h = _py({**b, "layout": lay})
        assert "<img" not in h and "<script>" not in h and "onerror=alert(1)>" not in h.replace("&gt;", "")


# ─── a leftover from before D22 ────────────────────────────────────────────────
def test_the_shadowed_glowing_area_renderer_is_gone():
    from pathlib import Path
    src = (Path(__file__).resolve().parent.parent / "renderers/web_article.py").read_text()
    assert src.count("def _render_stacked_area(") == 1
    assert "stack_layer_" not in src


# ─── registration ──────────────────────────────────────────────────────────────
def test_schema_describes_what_is_drawn():
    import yaml
    from pathlib import Path
    s = yaml.safe_load((Path(__file__).resolve().parent.parent / "atoms/schema.yaml").read_text())
    a = next(x for x in s["blocks"] if x.get("type") == "stacked_area")
    text = " ".join(str(a.get(k, "")) for k in ("description", "compact_description", "routing_text"))
    assert "glow" not in text.lower() and "gradient" not in text.lower()
    assert "area" in text.lower() and "bars" in a["fields"]["layout"] and "area" in a["fields"]["layout"]
    assert "2026-10-21" in a["fields"]["layout"] or "2026-10-21" in str(a.get("notes", ""))
    assert "layout" in a["fields"] and "version" in a["fields"] and "offset" in a["fields"]


# ─── layout "bars" is origin/main's output, proven by hash ─────────────────────
def test_layout_bars_matches_the_hashes_of_origin_main_3a52a9b61():
    """tests/fixtures/stacked_area_bars_origin_main_hashes.json: sha256 of what origin/main 3a52a9b61's renderers/web_article.py rendered
    for every payload above, each with no offset, offset "none", "bogus" and "" (no layout field existed then). Python only; the Apps Script
    twin is pinned byte for byte by stacked_area_baseline.json in test_stacked_area_offset.py."""
    import hashlib
    from pathlib import Path
    want = json.loads((Path(__file__).resolve().parent / "fixtures/stacked_area_bars_origin_main_hashes.json").read_text())
    got = {}
    for n, b in EVERY.items():
        for off in (None, "none", "bogus", ""):
            bb = {**b, "layout": "bars"}
            if off is not None:
                bb["offset"] = off
            got[f"{n}|{off}"] = hashlib.sha256(_py(bb).encode()).hexdigest()
    assert got == want
