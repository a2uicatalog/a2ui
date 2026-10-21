"""chartjs_bar (plotly core-bar): the static bar chart on the shared axis helper, in BOTH renderers.

Held here: Python/GAS byte-identical HTML (fixed payloads and a seeded fuzz), the hidden table with every value, the aria gist, the bar
geometry per mode (group, stack, relative, overlay; vertical and horizontal; negatives), the log axis, range and reverse, caps with a
visible note, malformed and hostile input (never throws, never becomes markup), no script, no literal dark-theme colours, text >= 12px,
the legacy `data` shape, the version note, the I84 description and registration.
"""
from __future__ import annotations

import json
import random
import re
from html.parser import HTMLParser
from pathlib import Path

import pytest
import yaml

from test_motion_atoms import _gas_batch, _py, core_js, wa  # noqa: F401

ROOT = Path(__file__).resolve().parent.parent
ATTACK = '"><img src=x onerror=alert(1)>\'"><svg onload=alert(1)></script><script>alert(4)</script> onmouseover=alert(2)'
L = ["Q1", "Q2", "Q3", "Q4"]


def B(**kw):
    b = {"type": "chartjs_bar", "labels": L, "datasets": [{"label": "A", "data": [10, -5, 30, 2]}, {"label": "B", "data": [12, 8, 25, 7]}]}
    b.update(kw)
    return b


PAYLOADS = {
    "plain": B(),
    "one_series": B(datasets=[{"label": "Only", "data": [3, 5, 8, 13]}]),
    "values_h": B(show_values=True, orientation="h"),
    "stack": B(mode="stack", show_values=True),
    "stack_h": B(mode="stack", orientation="h", show_values=True, legend_position="bottom"),
    "relative": B(mode="relative", show_values=True),
    "overlay": B(mode="overlay", show_values=True, legend_position="right"),
    "overlay_h": B(mode="overlay", orientation="h", show_values=True),
    "log": B(datasets=[{"label": "R", "data": [3, 40, 520, 7100]}], y_scale="log", show_values=True, y_format="~s"),
    "log_drop": B(datasets=[{"label": "R", "data": [3, 0, -5, 7100]}], y_scale="log"),
    "range": B(y_range=[0, 20], show_values=True),
    "reverse": B(y_reverse=True, y_ticks=8, gap=0.5),
    "formats": B(y_format="$,.2f", value_format=",.0f", show_values=True),
    "pct": B(datasets=[{"label": "p", "data": [0.1, 0.25, 0.5, 0.75]}], y_format=".0%", value_format=".1%", show_values=True),
    "legacy": {"type": "chartjs_bar", "title": "Legacy", "data": [{"label": "a", "value": 4}, {"label": "b", "value": 9}]},
    "version": B(version=3),
    "custom_color": B(datasets=[{"label": "A", "data": [1, 2, 3, 4], "color": "#aa3311"}]),
    "gaps": B(datasets=[{"label": "A", "data": [1, None, "x", True]}, {"label": "B", "data": [2, 3]}]),
    "zeros": B(datasets=[{"label": "A", "data": [0, 0, 0, 0]}]),
    "bad_format": B(y_format="x", value_format="nonsense", show_values=True),
}


class _P(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags, self.attrs = [], []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        self.attrs += [(tag, k, v) for k, v in attrs]


def parse(html):
    p = _P()
    p.feed(html)
    return p


def table(html):
    rows = re.findall(r"<tr>(.*?)</tr>", html)
    return [[re.sub(r"<[^>]+>", "", c) for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", r)] for r in rows]


def test_both_twins_emit_identical_html(core_js):
    names = list(PAYLOADS)
    gas = _gas_batch(core_js, [PAYLOADS[n] for n in names])
    for n, g in zip(names, gas):
        assert _py(PAYLOADS[n]) == g, n


def test_twins_agree_on_a_seeded_fuzz(core_js):
    rnd = random.Random(11)
    blocks = []
    for _ in range(120):
        n, s = rnd.randint(1, 14), rnd.randint(1, 5)
        scale = 10.0 ** rnd.randint(-3, 6)
        mk = lambda: [rnd.choice([None, "x", True, rnd.uniform(-1, 1) * scale, round(rnd.uniform(0, 1) * scale, rnd.randint(0, 3)), 0]) for _ in range(rnd.randint(0, n + 2))]
        b = {"type": "chartjs_bar", "labels": [rnd.choice(["a", "bb", 3, None, "long label here"]) for _ in range(rnd.randint(0, n))],
             "datasets": [{"label": rnd.choice(["s", None, 4]), "data": mk()} for _ in range(s)],
             "mode": rnd.choice(["group", "stack", "relative", "overlay", "zzz", None]), "orientation": rnd.choice(["v", "h", "horizontal", None]),
             "show_values": rnd.choice([True, False, "true", "false", 1, None]), "y_scale": rnd.choice(["log", "linear", None]),
             "y_range": rnd.choice([None, [0, 10], [5, -5], [1, 1], ["a", 2], [0.1, 1e5]]), "y_reverse": rnd.choice([True, False, "true"]),
             "y_ticks": rnd.choice([None, 2, 5, 11, 99, "x"]), "gap": rnd.choice([None, 0, 0.5, 2, -1]),
             "y_format": rnd.choice([None, ",.0f", ".1%", "~s", "$.2f", "bad", "x", 5]), "value_format": rnd.choice([None, ".2f", "+d"]),
             "legend_position": rnd.choice([None, "top", "right", "bottom", "none", "x"])}
        blocks.append(b)
    gas = _gas_batch(core_js, blocks)
    for i, (b, g) in enumerate(zip(blocks, gas)):
        assert _py(b) == g, (i, json.dumps(b))
        assert not re.search(r"NaN|undefined|Infinity|\[object Object\]", re.sub(r'aria-label="[^"]*"', "", g)) or "NaN" not in g, (i, json.dumps(b))


@pytest.mark.parametrize("name", list(PAYLOADS))
def test_output_is_accessible_static_and_clean(name):
    h = _py(PAYLOADS[name])
    p = parse(h)
    assert "script" not in p.tags and not [a for a in p.attrs if a[1].startswith("on")]
    assert h.count('role="img"') == 1 and re.search(r'role="img" aria-label="[^"]{20,}"', h)
    assert "<table" in h and h.index("<table") > h.index('role="img"')               # the table is a sibling after the picture, not inside it
    assert not re.search(r"NaN|undefined|Infinity|\[object Object\]", re.sub(r'aria-label="[^"]*"', "", h))
    assert "rgb(15,23,42)" not in h and "#94a3b8" not in h and "monospace" not in h   # the old literal dark-theme colours
    for fs in re.findall(r"font-size:([0-9.]+)(rem|px)", h):
        v = float(fs[0])
        assert (v >= 0.75 if fs[1] == "rem" else v >= 12), fs
    assert not re.search(r"filter=|backdrop-filter", h)


def test_the_hidden_table_has_every_value():
    t = table(_py(PAYLOADS["plain"]))
    assert t[0] == ["Category", "A", "B"]
    assert t[1:] == [["Q1", "10", "12"], ["Q2", "-5", "8"], ["Q3", "30", "25"], ["Q4", "2", "7"]]
    t = table(_py(B(datasets=[{"label": "A", "data": [1.5, 2, None, 1234.25]}], y_format=".0%")))
    assert t[1:] == [["Q1", "1.50"], ["Q2", "2.00"], ["Q3", ""], ["Q4", "1,234.25"]]    # the raw numbers, not the axis format


def test_the_aria_label_states_the_gist():
    a = re.search(r'aria-label="([^"]*)"', _py(PAYLOADS["plain"])).group(1)
    assert "Grouped bar chart of 4 categories and 2 series" in a and "Highest value 30 (A, Q3)" in a and "lowest -5 (A, Q2)" in a and "from -5 to 30" in a
    a = re.search(r'aria-label="([^"]*)"', _py(PAYLOADS["stack_h"])).group(1)
    assert a.startswith("Stacked horizontal bar chart")


def _boxes(h):
    """[(left, bottom, width, height)] in % of each bar element (the ones with a border of the series colour and a position)."""
    out = []
    for m in re.finditer(r'<div style="position:absolute;box-sizing:border-box;border:1\.5px solid [^;]+;[^"]*?(?:left:([\d.\-]+)%;width:([\d.]+)%;bottom:([\d.\-]+)%;height:([\d.]+)%|top:([\d.\-]+)%;height:([\d.]+)%;left:([\d.\-]+)%;width:([\d.]+)%)', h):
        g = m.groups()
        out.append((float(g[0]), float(g[2]), float(g[1]), float(g[3])) if g[0] is not None else (float(g[6]), float(g[4]), float(g[7]), float(g[5])))
    return out


def test_group_bars_stand_on_the_zero_line_and_negatives_hang_below():
    h = _py(B(datasets=[{"label": "A", "data": [10, -5, 30, 2]}]))
    zero = float(re.search(r"bottom:([\d.]+)%;border-top:1\.5px solid", h).group(1))
    bx = _boxes(h)
    assert len(bx) == 4 and abs(zero - 100 * 5 / 35) < 1e-3                                  # axis -5..30: zero at 5/35
    assert abs(bx[0][1] - zero) < 1e-3 and abs(bx[1][1] + bx[1][3] - zero) < 1e-3              # a positive bar starts at zero, a negative one ends there
    assert bx[2][3] > bx[0][3] > bx[1][3] > 0


def test_stack_adds_signed_values_and_relative_splits_the_signs():
    s = _boxes(_py(B(mode="stack", datasets=[{"label": "A", "data": [10]}, {"label": "B", "data": [-4]}], labels=["x"])))
    r = _boxes(_py(B(mode="relative", datasets=[{"label": "A", "data": [10]}, {"label": "B", "data": [-4]}], labels=["x"])))
    assert abs(s[1][1] + s[1][3] - (s[0][1] + s[0][3])) < 1e-6                                # stack: B hangs from the top of A (10 down to 6)
    assert abs(r[1][1] + r[1][3] - r[0][1]) < 1e-6                                            # relative: B hangs from the baseline
    g = _boxes(_py(B(mode="group", datasets=[{"label": "A", "data": [3]}, {"label": "B", "data": [4]}], labels=["x"])))
    assert g[0][0] + g[0][2] <= g[1][0] + 1e-6                                                # grouped bars sit side by side
    o = _boxes(_py(B(mode="overlay", datasets=[{"label": "A", "data": [3]}, {"label": "B", "data": [4]}], labels=["x"])))
    assert abs(o[0][0] - o[1][0]) < 1e-6 and abs(o[0][2] - o[1][2]) < 1e-6                    # overlay: the same footprint


def test_horizontal_bars_grow_along_the_value_axis():
    bx = _boxes(_py(B(orientation="h", datasets=[{"label": "A", "data": [10, 20]}], labels=["a", "b"])))
    assert bx[0][0] == bx[1][0] and abs(bx[1][2] - 2 * bx[0][2]) < 1e-2                       # horizontal tuple is (left, top, width, height): a shared left edge, width ~ value


def test_log_axis_ticks_at_powers_of_ten_and_drops_non_positive_with_a_note():
    h = _py(PAYLOADS["log"])
    labels = re.findall(r"translateY\(50%\);padding-right:6px[^>]*>([^<]+)<", h)
    assert labels == ["1", "10", "100", "1k", "10k"]
    h = _py(PAYLOADS["log_drop"])
    assert "2 numbers are not above zero" in h and "Q2" in h and table(h)[2][1] == "0"          # drawn without them, listed in the table
    assert "Stacked bars need a linear axis" in _py(B(y_scale="log", mode="stack"))


def test_range_clips_with_a_note_and_reverse_flips_the_axis():
    h = _py(PAYLOADS["range"])
    assert "cut at the axis" in h and max(b[3] for b in _boxes(h)) <= 100.0001
    up = _boxes(_py(B(datasets=[{"label": "A", "data": [5]}], labels=["x"])))[0]
    dn = _boxes(_py(B(datasets=[{"label": "A", "data": [5]}], labels=["x"], y_reverse=True)))[0]
    assert abs(up[1] - 0) < 1e-6 and abs(dn[1] + dn[3] - 100) < 1e-6                           # reversed: the bar hangs from the top


def test_caps_say_so():
    h = _py(B(labels=[f"c{i}" for i in range(60)], datasets=[{"label": f"s{k}", "data": list(range(60))} for k in range(11)]))
    assert "The first 40 of 60 categories are drawn" in h and "The first 8 of 11 series are drawn" in h
    t = table(h)
    assert len(t) == 61 and len(t[0]) == 12                                                    # the table lists everything
    assert len(_boxes(h)) <= 40 * 8


def test_empty_and_malformed_input_never_throws():
    for b in ({"type": "chartjs_bar"}, B(datasets=[]), B(datasets="x"), B(datasets=[None, 5, "s"], labels=7), B(labels=None, datasets=[{"data": "abc"}]),
              B(datasets=[{"label": "A", "data": [None, "q"]}]), B(datasets=[{"label": "A", "data": [1e300, -1e300]}]), {"type": "chartjs_bar", "data": "zzz"},
              B(y_range=[1], y_scale="log"), B(y_range=[-1, 1], y_scale="log", datasets=[{"data": [1, 2]}]), B(gap="x", y_ticks=[], mode=[]), B(labels=[[1], {"a": 1}, None, 5])):
        h = _py(b)
        assert isinstance(h, str) and not re.search(r"NaN|undefined|Infinity|\[object Object\]", re.sub(r'aria-label="[^"]*"', "", h))
    assert "No numbers to draw" in _py({"type": "chartjs_bar"})


def test_hostile_text_never_becomes_markup():
    h = _py(B(title=ATTACK, labels=[ATTACK] * 4, datasets=[{"label": ATTACK, "data": [1, 2, 3, 4], "color": ATTACK}], y_format=ATTACK, value_format=ATTACK, show_values=True))
    p = parse(h)
    assert "img" not in p.tags and "svg" not in p.tags and "script" not in p.tags and not [a for a in p.attrs if a[1].startswith("on")]
    assert ATTACK not in h and "&lt;img" in h
    assert "not a number format this chart knows" in h


def test_a_custom_series_colour_must_be_a_hex_triplet():
    assert "#aa3311" in _py(PAYLOADS["custom_color"])
    assert "red;" not in _py(B(datasets=[{"label": "A", "data": [1], "color": "red;position:fixed"}]))


def test_series_are_told_apart_by_pattern_not_colour_alone():
    h = _py(B())
    assert "repeating-linear-gradient" in h and h.count("<span aria-hidden") == 2             # the legend swatches carry the same fill pattern as the bars
    assert "var(--accent,#0369A1)" in h and "var(--chart-2,#9A6120)" in h


def test_legacy_data_shape_still_draws_and_other_versions_say_so():
    t = table(_py(PAYLOADS["legacy"]))
    assert t == [["Category", "Legacy"], ["a", "4"], ["b", "9"]] or t[1:] == [["a", "4"], ["b", "9"]]
    assert "Written for chartjs_bar version 3; drawn as version 1." in _py(PAYLOADS["version"])


def test_value_labels_hide_by_container_width_not_by_overlap():
    h = _py(PAYLOADS["values_h"])
    assert "cbv" in h and "Value labels hide when the chart is too narrow" in h
    v = _py(B(show_values=True))
    assert re.search(r"@container \(max-width:\d+px\)\{\.ifcb \.cbw\d+\{display:none\}\}", v)


def test_the_output_is_deterministic():
    assert _py(PAYLOADS["stack"]) == _py(dict(PAYLOADS["stack"]))


def test_the_description_is_honest_and_the_fields_are_declared():
    s = yaml.safe_load((ROOT / "atoms/schema.yaml").read_text())
    a = next(x for x in s["blocks"] if x.get("type") == "chartjs_bar")
    txt = (a["description"] + a["compact_description"] + a["routing_text"]).lower()
    assert "interactive" not in txt.replace("no interactivity", "") and "chart.js" not in txt.replace("no chart.js", "")        # I84: it is static HTML
    for f in ("mode", "orientation", "show_values", "value_format", "legend_position", "y_scale", "y_range", "y_format", "gap", "version"):
        assert f in a["fields"], f
