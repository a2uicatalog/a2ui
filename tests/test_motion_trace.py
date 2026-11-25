"""motion_trace (2026-11-25, preview): a request trace, a latency waterfall of spans on one time axis.

Everything numeric is derived by code from the raw spans (python-for-math): the total, the widths, the ticks and the slowest span.
Parity of the Python and Apps Script twins is in test_motion_atoms.py (the PAYLOADS case list); this file pins the behaviour.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from renderers import web_article as wa  # noqa: E402

TRIP = [
    {"id": "req", "name": "Request", "start_ms": 0, "duration_ms": 1480},
    {"id": "net", "name": "Network", "start_ms": 0, "duration_ms": 120, "parent": "req", "kind": "network"},
    {"id": "srv", "name": "Server render", "start_ms": 120, "duration_ms": 900, "parent": "req", "kind": "server"},
    {"id": "paint", "name": "Paint", "start_ms": 1020, "duration_ms": 460, "parent": "req", "kind": "client"},
]


def _r(**kw):
    return wa._render_motion_trace(dict({"spans": TRIP}, **kw))


def test_total_and_slowest_are_computed_never_supplied():
    out = _r(total_ms=1)
    label = re.search(r'role="img" aria-label="([^"]*)"', out).group(1)
    assert "total 1480 ms" in label                       # the latest end of any span; the supplied total_ms is ignored
    assert "slowest Server render 900 ms" in label        # the longest leaf: the parent Request (1480) encloses the others
    assert "Total 1480 ms" in out and "<title>" in out and "900 ms · slowest" in out


def test_spans_are_drawn_in_start_order_and_animate_left_to_right():
    shuffled = [TRIP[3], TRIP[2], TRIP[1], TRIP[0]]
    out = _r(spans=shuffled)
    assert [out.index(n) for n in (">Request<", ">Network<", ">Server render<", ">Paint<")] == sorted(out.index(n) for n in (">Request<", ">Network<", ">Server render<", ">Paint<"))
    ats = [float(m) for m in re.findall(r"--u:clamp\(0,calc\(\(var\(--p,1\) - ([0-9.]+)\)/", out)][:4]
    assert ats == sorted(ats) and ats[0] < ats[-1]
    assert "scaleX(var(--u))" in out


def test_bars_scale_with_duration_and_stay_inside_the_axis():
    out = _r(w=600)
    rects = [(float(x), float(w)) for x, w in re.findall(r'<rect x="([0-9.]+)" y="[0-9.]+" width="([0-9.]+)" height="[0-9.]+" rx="3"', out)]
    assert len(rects) == 4
    assert all(x + w <= 600 - 14 + 0.2 for x, w in rects)
    assert rects[0][1] == pytest.approx(600 - 14 - 228, abs=0.2)          # the whole trace spans the whole axis
    assert rects[2][1] / rects[1][1] == pytest.approx(900 / 120, rel=0.02)


def test_short_spans_put_the_label_outside_the_bar():
    out = wa._render_motion_trace({"spans": [{"id": "a", "name": "Long", "start_ms": 0, "duration_ms": 1000}, {"id": "b", "name": "Blip", "start_ms": 100, "duration_ms": 3}]})
    labels = re.findall(r'<text x="([0-9.]+)" y="[0-9.]+" text-anchor="(start|end)" style="font-family:[^"]*font-size:13px;font-weight:\d+;fill:([^;]+);', out)
    inside = [l for l in labels if l[2] == "#0b0f19"]
    outside = [l for l in labels if l[2] != "#0b0f19"]
    assert len(inside) == 1 and len(outside) == 1


def test_nesting_is_depth_limited_and_bad_parents_become_roots():
    chain = [{"id": "a", "name": "A", "start_ms": 0, "duration_ms": 50}] + [
        {"id": c, "name": c.upper(), "start_ms": 0, "duration_ms": 50 - i, "parent": p} for i, (c, p) in enumerate([("b", "a"), ("c", "b"), ("d", "c")], 1)]
    chain.append({"id": "z", "name": "Z", "start_ms": 1, "duration_ms": 2, "parent": "nope"})
    chain.append({"id": "y", "name": "Y", "start_ms": 2, "duration_ms": 2, "parent": "y"})
    out = wa._render_motion_trace({"spans": chain})
    indents = dict((n, float(x)) for x, n in re.findall(r'<text x="([0-9.]+)" y="[0-9.]+" style="font-family:system-ui[^"]*font-size:15px;fill:var\(--mt-ink,currentColor\);">([A-Z])</text>', out))
    assert indents["A"] == indents["Z"] == indents["Y"] == 8 and indents["B"] == 22
    assert indents["C"] == indents["D"] == 36               # depth is capped at 3 levels


def test_invalid_spans_are_dropped_and_at_most_14_are_kept():
    raw = [{"id": f"s{i}", "name": f"S{i}", "start_ms": i, "duration_ms": 1} for i in range(20)]
    assert len(wa._mo_trace_spans(raw)) == 14
    bad = [{"id": "a", "start_ms": -1, "duration_ms": 1}, {"id": "b", "start_ms": 0, "duration_ms": 0}, {"id": "c", "start_ms": 0, "duration_ms": float("inf")},
           {"id": "d", "start_ms": 599999, "duration_ms": 5}, {"id": "A b", "start_ms": 0, "duration_ms": 1}, {"id": "e", "start_ms": "0", "duration_ms": 1}, "x", None]
    assert wa._mo_trace_spans(bad) == []
    assert "No spans" in wa._render_motion_trace({"spans": bad})


def test_text_is_escaped_and_nothing_raw_reaches_markup():
    out = wa._render_motion_trace({"title": "<script>alert(1)</script>", "spans": [{"id": "a", "name": '"><img src=x onerror=alert(1)>', "start_ms": 0, "duration_ms": 5, "kind": "<x>"}]})
    from html.parser import HTMLParser
    tags = set()

    class P(HTMLParser):
        def handle_starttag(self, tag, attrs):
            tags.add(tag)
    P().feed(out)
    assert tags <= {"svg", "title", "text", "g", "rect", "line"}, tags


def test_reduced_motion_is_the_finished_trace():
    # no script and no animation of its own: --p defaults to 1 outside a motion_timeline, and the timeline holds p at 1 for reduced motion
    out = _r()
    assert "<script" not in out and "@keyframes" not in out and "var(--p,1)" in out


def test_schema_entry_is_preview_and_documents_every_field():
    atoms = {a["type"]: a for a in yaml.safe_load((ROOT / "atoms" / "schema.yaml").read_text())["blocks"]}
    a = atoms["motion_trace"]
    assert a["stage"] == "preview" and set(a["fields"]) == {"spans", "title", "w", "h", "size", "label"}
    packs = (ROOT / "atoms" / "atom-packs.yaml").read_text()
    assert "- motion_trace\n" in packs


def test_examples_validate_against_the_atom_contract():
    import json
    for f in sorted((ROOT / "examples" / "motion_trace").glob("*.json")):
        doc = json.loads(f.read_text())
        blocks = doc["blocks"] if isinstance(doc, dict) and "blocks" in doc else [doc]
        for b in blocks:
            assert b["type"] == "motion_trace" and 1 <= len(b["spans"]) <= 14
            ids = [s["id"] for s in b["spans"]]
            assert len(set(ids)) == len(ids) and all(s.get("parent") in ids or "parent" not in s for s in b["spans"])
            out = wa._render_motion_trace(b)
            assert "slowest" in out and "No spans" not in out
