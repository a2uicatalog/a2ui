"""stacked_area `offset` (I49): "expand" | "silhouette" | "wiggle" (streamgraph) next to today's zero-baseline bars.

GOLDEN (tests/fixtures/stacked_area_d3_golden.json) holds what the REAL d3-shape 3.2.0 stack() produced for stackOffsetNone / Expand /
Silhouette / Wiggle (see stacked_area_d3_golden_gen.mjs); wiggle is stacked in stackOrderInsideOut, the order of d3's streamgraph example
(the other three keep stackOrderNone). Python and every Apps Script copy must reproduce the doubles EXACTLY (== , not a tolerance).

BYTE FOR BYTE: an absent, "none" or unknown `offset` must render exactly what the renderer rendered before this field existed. The
fixture stacked_area_baseline.json holds the output of the UNMODIFIED code (Python, and the Apps Script copies) for every stacked_area
payload in the repository plus malformed ones; this file compares against it. (The live stacked_area is the CSS horizontal-bar renderer,
not the SVG area chart that is still in web_article.py above it and is shadowed by the later definition; `offset` adds a real chart.)

Also held: Python/GAS byte-identical HTML, all six Apps Script copies carry the same block, the hidden table, the aria label,
the axis rules, malformed input, caps, escaping and the version note.
"""
from __future__ import annotations

import json
import re
import subprocess
import tempfile
from pathlib import Path

import pytest

from test_motion_atoms import _gas_batch, _node, _py, core_js  # noqa: F401  (core_js is a fixture)
from test_motion_atoms import wa  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
D = json.loads((ROOT / "tests/fixtures/stacked_area_d3_golden.json").read_text())
CASES = {**D["golden"], **{f"fuzz{i}": c for i, c in enumerate(D["fuzz"])}}
GAS_DIRS = ["gas-wired-renderer", "gas-schema-renderer", "gas-fakes-schema-renderer-private"]
GAS_FILES = [f"apps-script-surface/{d}/atoms_unstub.gs" for d in GAS_DIRS] + [f"apps-script-surface/{d}/atoms_unstub.js" for d in GAS_DIRS[1:]]
ATTACK = '"><img src=x onerror=alert(1)>\'"><svg onload=alert(1)></script><script>alert(4)</script> onmouseover=alert(2)'
OFFSETS = ["expand", "silhouette", "wiggle"]


def _label_list(n):
    return [f"P{i + 1}" for i in range(n)]


def _block(vals, **kw):
    b = {"type": "stacked_area", "labels": _label_list(len(vals[0])), "series": [{"label": f"S{i + 1}", "data": row} for i, row in enumerate(vals)]}
    b.update(kw)
    return b


# ─── d3 layout, exactly ───────────────────────────────────────────────────────
def _golden_modes(c):
    return [m for m in ("none", "expand", "silhouette", "wiggle", "wiggle@none") if m in c]


@pytest.mark.parametrize("name", list(CASES))
def test_python_stack_matches_d3_exactly(name):
    c = CASES[name]
    for mode in _golden_modes(c):
        if mode == "wiggle@none":
            continue
        order, lo, hi = wa._sa_stack(c["values"], mode)
        assert order == c[mode]["order"], (name, mode)
        assert lo == c[mode]["lo"] and hi == c[mode]["hi"], (name, mode)


def test_gas_stack_matches_d3_exactly_in_every_copy(core_js):
    names = list(CASES)
    jobs = [[CASES[n]["values"], m, n] for n in names for m in _golden_modes(CASES[n]) if m != "wiggle@none"]
    body = "var G = " + json.dumps(jobs) + "; console.log(JSON.stringify(G.map(function(g){ var r = _saStack(g[0], g[1]); return [r.order, r.lo, r.hi]; })));"
    res = _node(core_js, body)
    for (vals, mode, n), (order, lo, hi) in zip(jobs, res):
        g = CASES[n][mode]
        assert order == g["order"] and lo == g["lo"] and hi == g["hi"], (n, mode)


@pytest.mark.parametrize("gas_dir", GAS_DIRS[1:])
def test_gas_stack_matches_d3_in_the_schema_renderer_copies(gas_dir):
    jobs = [[CASES[n]["values"], m, n] for n in ("three_by_four", "peaks_late", "ties_in_peaks", "zero_series", "huge_and_tiny", "fuzz3", "fuzz9") for m in OFFSETS]
    body = "var G = " + json.dumps(jobs) + "; console.log(JSON.stringify(G.map(function(g){ var r = _saStack(g[0], g[1]); return [r.order, r.lo, r.hi]; })));"
    res = _run_standalone(gas_dir, body)
    for (vals, mode, n), (order, lo, hi) in zip(jobs, res):
        g = CASES[n][mode]
        assert order == g["order"] and lo == g["lo"] and hi == g["hi"], (n, mode)


def test_the_golden_set_covers_the_hard_cases():
    g = D["golden"]
    assert g["zero_series"]["expand"]["hi"][0] == [0, 0, 0, 0]                           # a series of zeros stays flat
    assert g["with_zero_column"]["expand"]["hi"][2][0] == 0                               # a column that sums to 0 is not divided
    assert g["peaks_late"]["wiggle"]["order"] != [0, 1, 2, 3]                             # inside-out really reorders
    assert len(CASES["series_twelve_pts_ten"]["none"]["hi"]) == 12
    assert any(g[n]["wiggle"]["lo"] != g[n]["wiggle@none"]["lo"] for n in g)             # the order matters for wiggle: the golden keeps both


# ─── Apps Script: all copies carry the same block ──────────────────────────────
def _block_text(path):
    s = (ROOT / path).read_text()
    a = s.index("// ─── stacked_area `offset`")
    return s[a:s.index("function _saGate", a) + s[s.index("function _saGate", a):].index("\n}\n") + 3]


def test_every_apps_script_copy_carries_the_identical_offset_block():
    texts = {p: _block_text(p) for p in GAS_FILES}
    assert len(set(texts.values())) == 1, {p: len(t) for p, t in texts.items()}
    for p in GAS_FILES:
        s = (ROOT / p).read_text()
        assert "var _sa = _saGate(b);" in s and "+ _sa.tail;" in s, p


def _run_standalone(gas_dir, body):
    """gas-schema-renderer and the private fakes copy have no bundle: the file is loaded alone against a bare _RENDERERS and its own _esc."""
    esc = re.search(r"function _esc\(str\) \{.*?\n\}\n", (ROOT / "apps-script-surface" / gas_dir / "atom.gs").read_text(), re.S).group(0)
    src = (ROOT / "apps-script-surface" / gas_dir / "atoms_unstub.gs").read_text()
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "d.js"
        p.write_text("var _RENDERERS = {};\n" + esc + "\n" + src + "\n" + body)
        proc = subprocess.run(["node", str(p)], capture_output=True, text=True, timeout=60)
        assert proc.returncode == 0, proc.stderr[-1500:]
        return json.loads(proc.stdout.strip().split("\n")[-1])


def _standalone_render(gas_dir, blocks):
    return _run_standalone(gas_dir, "var B = " + json.dumps(blocks) + "; console.log(JSON.stringify(B.map(function(b){ return _RENDERERS.stacked_area(b); })));")


# ─── today's output, byte for byte ─────────────────────────────────────────────
BASE = {
    "showcase": {"type": "stacked_area", "title": "Atom categories over time", "labels": ["Q1", "Q2", "Q3", "Q4"],
                 "series": [{"label": "Core", "data": [40, 60, 80, 100], "color": "#6366f1"}, {"label": "LMS", "data": [10, 20, 35, 50], "color": "#10b981"}, {"label": "Charts", "data": [5, 15, 25, 40], "color": "#f59e0b"}]},
    "mrr": {"type": "stacked_area", "title": "MeetStudio MRR Growth Projections", "labels": ["Jan 2026", "Mar 2026", "May 2026"],
            "series": [{"label": "Basic Tier", "data": [1200, 2400, 4800], "color": "#00f2ff"}, {"label": "Pro Multi Split Tier", "data": [400, 1200, 3200], "color": "#8430ce"}]},
    "renderer_test": {"type": "stacked_area", "title": "MRR", "labels": ["Jan", "Feb"], "series": [{"label": "SaaS", "data": [10, 20], "color": "#00f2ff"}]},
    "stage_deck": {"type": "stacked_area", "title": "SaaS Cumulative Monthly Recurring Revenue (MRR)", "labels": ["Q1", "Q2", "Q3", "Q4"],
                   "series": [{"label": "Enterprise Plan", "data": [12000, 24000, 48000, 72000], "color": "#00f2ff"}, {"label": "Pro Plan", "data": [6000, 9000, 15000, 21000]}]},
    "catalogue_page": {"type": "stacked_area", "labels": ["Category A", "Category B", "Category C", "Category D"],
                       "series": [{"label": "Series A", "data": [10, 20, 30, 40]}, {"label": "Series B", "data": [5, 15, 25, 35]}]},
    "no_colors_seven": _block([[i + j for j in range(4)] for i in range(7)]),
    "zeros": _block([[0, 0, 0], [0, 0, 0]]),
    "floats_negatives": _block([[1.5, -2.25, 3.125], [0.1, 0.2, 0.3]]),
    "ragged": {"type": "stacked_area", "labels": ["a", "b", "c", "d"], "series": [{"label": "short", "data": [1, 2]}, {"label": "long", "data": [3, 4, 5, 6, 7, 8]}]},
    "single_label": _block([[5], [7]]),
    "empty_series": {"type": "stacked_area", "title": "T", "labels": ["a", "b"], "series": []},
    "empty_labels": {"type": "stacked_area", "title": "T", "labels": [], "series": [{"label": "x", "data": [1, 2]}]},
    "hostile": {"type": "stacked_area", "title": ATTACK, "labels": [ATTACK, "b"], "series": [{"label": ATTACK, "data": [1, 2], "color": ATTACK}]},
    "html_in_values": {"type": "stacked_area", "labels": ["a", "b"], "series": [{"label": "<b>x</b>", "data": [1, "2"]}]},
}


def _pyx(b):
    """The Python renderer's output, or "!<ExceptionName>": the bars renderer has always raised on two of these payloads (all-zero totals, a text cell), and that must not change."""
    try:
        return _py(b)
    except Exception as e:  # noqa: BLE001
        return "!" + type(e).__name__


BASELINE = json.loads((ROOT / "tests/fixtures/stacked_area_baseline.json").read_text())
JUNK = [None, "none", "None", "NONE", "bogus", "EXPAND", "expand ", "wiggle2", "", 0, 1, True, False, [], ["expand"], {}, {"a": 1}, 1.5]


def test_the_baseline_fixture_covers_every_payload():
    assert set(BASELINE["python"]) == set(BASE) == set(BASELINE["gas"]) == set(BASELINE["gas_schema"])


@pytest.mark.parametrize("name", list(BASE))
def test_absent_offset_is_byte_for_byte_todays_output_in_python(name):
    assert _pyx(BASE[name]) == BASELINE["python"][name]


def test_absent_offset_is_byte_for_byte_todays_output_in_gas(core_js):
    out = _gas_batch(core_js, list(BASE.values()))
    assert dict(zip(BASE, out)) == BASELINE["gas"]


@pytest.mark.parametrize("gas_dir", GAS_DIRS[1:])
def test_absent_offset_is_byte_for_byte_todays_output_in_the_schema_copies(gas_dir):
    out = _standalone_render(gas_dir, list(BASE.values()))
    assert dict(zip(BASE, out)) == BASELINE["gas_schema"]


@pytest.mark.parametrize("junk", JUNK, ids=lambda j: json.dumps(j))
def test_none_and_unknown_offsets_render_todays_output_in_every_twin(junk, core_js):
    blocks = [{**b, "offset": junk} for b in BASE.values()]
    assert [_pyx(b) for b in blocks] == [BASELINE["python"][n] for n in BASE]
    assert _gas_batch(core_js, blocks) == [BASELINE["gas"][n] for n in BASE]
    for d in GAS_DIRS[1:]:
        assert _standalone_render(d, blocks) == [BASELINE["gas_schema"][n] for n in BASE]


def test_version_one_and_junk_versions_change_nothing(core_js):
    for v in (1, 0, -3, 2.5, "2", None, True, [2]):
        blocks = [{**b, "version": v} for b in BASE.values()]
        assert [_pyx(b) for b in blocks] == [BASELINE["python"][n] for n in BASE], v
        assert _gas_batch(core_js, blocks) == [BASELINE["gas"][n] for n in BASE], v


# ─── rendering: parity, table, axes, aria ─────────────────────────────────────
PAYLOADS = {
    "expand": _block(CASES["three_by_four"]["values"], title="Share of revenue", offset="expand"),
    "silhouette": _block(CASES["three_by_four"]["values"], title="Centred", offset="silhouette"),
    "wiggle": _block(CASES["peaks_late"]["values"], title="Streams", offset="wiggle"),
    "wiggle_many": _block(CASES["series_twelve_pts_ten"]["values"], offset="wiggle"),
    "expand_sixty": _block(CASES["series_four_pts_forty"]["values"], offset="expand"),
    "long_labels": {"type": "stacked_area", "offset": "expand", "labels": ["January 2026 (provisional)", "February 2026 (provisional)", "March 2026 (provisional)", "April 2026 (provisional)"],
                    "series": [{"label": "A very long series name that keeps going", "data": [3, 4, 5, 6]}, {"label": "B", "data": [1, 1, 2, 3]}]},
    "single_series": _block(CASES["single_series"]["values"], offset="wiggle"),
    "two_points": _block(CASES["two_by_two"]["values"], offset="silhouette"),
    "colors": {"type": "stacked_area", "offset": "wiggle", "labels": ["a", "b", "c"], "series": [{"label": "red", "data": [1, 2, 3], "color": "#ff0000"}, {"label": "short", "data": [3, 2, 1], "color": "#0f0"}, {"label": "bad", "data": [2, 2, 2], "color": "red"}]},
    "zeros": _block([[0, 0, 0], [0, 0, 0]], offset="expand"),
    "zero_silhouette": _block([[0, 0, 0], [0, 0, 0]], offset="wiggle"),
    "negatives_and_text": {"type": "stacked_area", "offset": "expand", "labels": ["a", "b", "c", "d"], "series": [{"label": "x", "data": [1, -2, "3", None]}, {"label": "y", "data": [4, 5, 6, 7, 8]}]},
    "ragged": {"type": "stacked_area", "offset": "silhouette", "labels": ["a", "b", "c", "d"], "series": [{"label": "short", "data": [1, 2]}, {"label": "long", "data": [3, 4, 5, 6, 7, 8]}]},
    "numbers_as_labels": {"type": "stacked_area", "offset": "expand", "labels": [2020, 2021.5, 2022], "series": [{"label": 7, "data": [1, 2, 3]}]},
    "version2": _block(CASES["three_by_four"]["values"], offset="expand", version=2),
    "hostile": {"type": "stacked_area", "offset": "wiggle", "title": ATTACK, "labels": [ATTACK, "b", "c"], "series": [{"label": ATTACK, "data": [1, 2, 3], "color": ATTACK}]},
    "too_few_labels": _block([[1], [2]], offset="expand"),
    "no_labels": {"type": "stacked_area", "offset": "wiggle", "series": [{"label": "x", "data": [1, 2, 3]}]},
    "no_series": {"type": "stacked_area", "offset": "wiggle", "labels": ["a", "b"]},
    "series_not_objects": {"type": "stacked_area", "offset": "expand", "labels": ["a", "b"], "series": [1, None, "x", [1, 2], {"label": "ok", "data": [1, 2]}]},
    "series_not_a_list": {"type": "stacked_area", "offset": "expand", "labels": ["a", "b"], "series": "x"},
    "labels_not_a_list": {"type": "stacked_area", "offset": "expand", "labels": "a,b", "series": [{"label": "x", "data": [1, 2]}]},
    "huge": _block([[1e12, 2e12, 5e11], [1e-9, 3e-9, 2e-9]], offset="silhouette"),
    "odd_cells": {"type": "stacked_area", "offset": "wiggle", "labels": [{"a": 1}, [1, 2], None, True], "series": [{"label": {"a": 1}, "data": [1, 2, 3, 4]}, {"label": [], "data": [4, 3, 2, 1]}]},
    "over_caps": _block([[(i * j) % 7 + 1 for j in range(70)] for i in range(14)], offset="expand"),
}
CHARTS = [n for n in PAYLOADS if n not in ("too_few_labels", "no_labels", "no_series", "series_not_a_list", "labels_not_a_list")]


FALLBACKS = ("too_few_labels", "no_labels", "no_series", "series_not_a_list", "labels_not_a_list")


@pytest.mark.parametrize("name", list(PAYLOADS))
def test_python_and_gas_emit_identical_html(name, core_js):
    assert _py(PAYLOADS[name]) == _gas_batch(core_js, [PAYLOADS[name]])[0]


@pytest.mark.parametrize("gas_dir", GAS_DIRS[1:])
def test_the_schema_copies_emit_the_same_chart(gas_dir):
    names = [n for n in PAYLOADS if n in CHARTS]
    out = _standalone_render(gas_dir, [PAYLOADS[n] for n in names])
    assert out == [_py(PAYLOADS[n]) for n in names]


@pytest.mark.parametrize("name", list(PAYLOADS))
def test_never_throws_and_never_prints_junk(name):
    html = _py(PAYLOADS[name])
    for bad in ("NaN", "undefined", "Infinity", "[object Object]", "None", "True", "False"):
        assert bad not in re.sub(r"<style>.*?</style>", "", html, flags=re.S).replace("var(--", ""), (name, bad)


def _table(html):
    m = re.search(r'<table style="position:absolute[^"]*"><thead><tr>(.*?)</tr></thead><tbody>(.*?)</tbody></table>', html, re.S)
    assert m
    head = re.findall(r'<th scope="col">(.*?)</th>', m.group(1))
    rows = [re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', r) for r in re.findall(r'<tr>(.*?)</tr>', m.group(2), re.S)]
    return head, rows


@pytest.mark.parametrize("name", ["expand", "silhouette", "wiggle", "wiggle_many", "expand_sixty"])
def test_hidden_table_lists_the_raw_values_per_series_and_point(name, core_js):
    b = PAYLOADS[name]
    for html in (_py(b), _gas_batch(core_js, [b])[0]):
        head, rows = _table(html)
        assert head == ["Point"] + [s["label"] for s in b["series"]]
        assert len(rows) == len(b["labels"])
        for j, r in enumerate(rows):
            assert r[0] == b["labels"][j] and [float(x) for x in r[1:]] == [float(s["data"][j]) for s in b["series"]]
        assert "<table" in html and html.index("<table") > html.index("</svg>")          # a sibling after the picture, not inside the img


def test_the_raw_values_stay_raw_even_when_the_offset_changes_what_is_drawn():
    raw = _table(_py(PAYLOADS["expand"]))[1]
    assert raw == _table(_py({**PAYLOADS["expand"], "offset": "silhouette"}))[1] == _table(_py({**PAYLOADS["expand"], "offset": "wiggle"}))[1]
    assert raw[0] == ["P1", "10", "5", "30"]


def test_negative_and_text_cells_show_raw_in_the_table_and_are_drawn_as_zero():
    html = _py(PAYLOADS["negatives_and_text"])
    head, rows = _table(html)
    assert rows[1][1] == "-2" and rows[2][1] == "" and rows[3][1] == ""
    assert "3 values were negative or not a usable number and are drawn as 0." in html


def test_expand_has_a_zero_to_hundred_percent_axis_and_the_others_have_none():
    e, s, w = (_py(PAYLOADS[n]) for n in ("expand", "silhouette", "wiggle"))
    assert [re.sub(r"<.*?>", "", x) for x in re.findall(r'<div class="say".*?</div>', e)] == ["0%", "25%", "50%", "75%", "100%"]
    for h in (s, w):
        assert 'class="say"' not in h and "%</div>" not in re.sub(r'<div class="sax.*?</div></div>', "", h)
        assert "There is no value axis" in h and "exact values are in the table" in h
        assert 'class="sax' in h                                                                  # the x axis stays
    assert "scaled so its layers add up to 100%" in e and "There is no value axis" not in e
    assert "inside-out" in w and "inside-out" not in s


def test_one_svg_no_script_no_canvas_and_the_picture_is_named():
    for n in CHARTS:
        h = _py(PAYLOADS[n])
        assert h.count("<svg") == 1 and "<script" not in h
        assert "<canvas" not in h
        assert re.search(r'<div role="img" aria-label="Stacked area chart, [^"]+: \d+ series over \d+ points from ', h), n
        assert 'aria-hidden="true" focusable="false" viewBox="0 0 1000 100"' in h


def test_aria_label_states_the_gist():
    a = re.search(r'aria-label="([^"]*)"', _py(PAYLOADS["wiggle"])).group(1)
    assert a == "Stacked area chart, streamgraph, baseline chosen to minimise wiggle: 4 series over 5 points from P1 to P5. Series: S1, S2, S3, S4."
    assert "each point scaled to 100 percent" in re.search(r'aria-label="([^"]*)"', _py(PAYLOADS["expand"])).group(1)
    assert "centred baseline" in re.search(r'aria-label="([^"]*)"', _py(PAYLOADS["silhouette"])).group(1)


def test_the_picture_reproduces_the_stack_it_was_computed_from():
    c = CASES["three_by_four"]
    for mode in OFFSETS:
        h = _py(_block(c["values"], offset=mode))
        polys = re.findall(r'<polygon points="([^"]*)"', h)
        assert len(polys) == 3
        g = c[mode]
        ymin = 0.0 if mode == "expand" else min(min(r) for r in g["lo"])
        ymax = 1.0 if mode == "expand" else max(max(r) for r in g["hi"])
        for i, p in enumerate(polys):
            pts = [tuple(float(t) for t in q.split(",")) for q in p.split()]
            top, bot = pts[:4], pts[4:][::-1]
            for j in range(4):
                assert abs(top[j][1] - (ymax - g["hi"][i][j]) / (ymax - ymin) * 100) < 0.006, (mode, i, j)
                assert abs(bot[j][1] - (ymax - g["lo"][i][j]) / (ymax - ymin) * 100) < 0.006, (mode, i, j)
                assert abs(top[j][0] - j / 3 * 1000) < 0.006


def test_expand_fills_the_plot_and_wiggle_leaves_the_baseline_free():
    h = _py(PAYLOADS["expand"])
    polys = [[tuple(float(t) for t in q.split(",")) for q in p.split()] for p in re.findall(r'<polygon points="([^"]*)"', h)]
    assert min(y for p in polys for _, y in p) == 0.0 and max(y for p in polys for _, y in p) == 100.0
    w = _py(PAYLOADS["wiggle"])
    ys = [float(q.split(",")[1]) for p in re.findall(r'<polygon points="([^"]*)"', w) for q in p.split()]
    assert min(ys) == 0.0 and max(ys) == 100.0                                                 # the extent is fitted to the plot


def test_colours_are_validated_and_the_legend_names_every_series():
    h = _py(PAYLOADS["colors"])
    assert 'fill="#ff0000"' in h and 'fill="#0f0"' in h and 'fill="red"' not in h and 'fill="#15803D"' in h
    for n in ("expand", "wiggle"):
        h = _py(PAYLOADS[n])
        for s in PAYLOADS[n]["series"]:
            assert f">{s['label']}</span>" in h


def test_text_is_never_below_twelve_px_and_uses_theme_tokens():
    for n in CHARTS:
        h = _py(PAYLOADS[n])
        assert not re.search(r"font-size:(?:0\.[0-6]\d*|[0-9]|1[01])(?:px|rem)", h.replace("font-size:0.75rem", "")), n
        assert "var(--muted,#475569)" in h and "var(--border,#CBD5E1)" in h and "var(--text,#0F172A)" in h and "var(--bg,#fff)" in h


# ─── caps, fallbacks, escaping, version ───────────────────────────────────────
def test_caps_say_what_was_not_drawn():
    h = _py(PAYLOADS["over_caps"])
    assert "2 series beyond the first 12 were not drawn." in h and "10 labels beyond the first 60 were not drawn." in h
    head, rows = _table(h)
    assert len(head) == 13 and len(rows) == 60 and h.count("<polygon") == 12


def test_unusable_data_gets_a_message_never_an_exception(core_js):
    msg = "A stacked area chart with an offset needs at least two labels and one series with numbers."
    extra = {"series_all_junk": {"type": "stacked_area", "offset": "expand", "labels": ["a", "b"], "series": [1, None]},
             "empty_series": {"type": "stacked_area", "offset": "wiggle", "title": "T", "labels": ["a", "b"], "series": []}}
    for n, b in {**{k: PAYLOADS[k] for k in FALLBACKS}, **extra}.items():
        for h in (_py(b), _gas_batch(core_js, [b])[0]):
            assert msg in h and "<svg" not in h, n
        assert _py(b) == _gas_batch(core_js, [b])[0], n
    for n in ("series_not_a_list", "labels_not_a_list"):
        assert msg in _py(PAYLOADS[n])



def test_malformed_series_are_counted_not_silently_dropped():
    h = _py(PAYLOADS["series_not_objects"])
    assert "4 series were not an object and were left out." in h and h.count("<polygon") == 1


def test_version_note():
    assert "Written for stacked_area version 2; drawn as version 1." in _py(PAYLOADS["version2"])
    for v in (1, 0, "2", 2.5, None):
        assert "Written for" not in _py({**PAYLOADS["expand"], "version": v})
    assert "Written for stacked_area version 3; drawn as version 1." in _py({**BASE["mrr"], "version": 3})
    assert "Written for stacked_area version 3; drawn as version 1." in _py({**BASE["mrr"], "offset": "none", "version": 3})


def test_hostile_text_is_escaped_everywhere():
    h = _py(PAYLOADS["hostile"])
    assert "<img" not in h and "<script>" not in h and "onerror=alert(1)>" not in h.replace("&gt;", "")
    assert 'fill="&quot;' not in h and "alert(1)" in h                                          # text survives, as text


# ─── registration ─────────────────────────────────────────────────────────────
def test_schema_declares_offset_and_version():
    import yaml
    s = yaml.safe_load((ROOT / "atoms/schema.yaml").read_text())
    a = next(x for x in s["blocks"] if x.get("type") == "stacked_area")
    assert "offset" in a["fields"] and "version" in a["fields"]
    for w in ("expand", "silhouette", "wiggle", "none"):
        assert w in a["fields"]["offset"]
