"""The twelve infographic atoms (2026-10-10, preview): quadrant, bullet_graph, swimlane, gantt, change_chart, cycle_diagram, journey_map,
maturity_ladder, treemap, venn_diagram, callout_anatomy, org_chart.

Held here: each renders its schema example, is motion-ready (reads --p), carries no script, survives hostile and extreme input, hides a decorative
SVG behind a text table, and really does build with p in a browser.
"""
from __future__ import annotations

import copy
import re
from html.parser import HTMLParser

import pytest

from test_motion_atoms import _gas_batch, _probe, _scene, browser, core_js  # noqa: F401  (core_js is a fixture)
import generate_atom_pages as g

ATOMS = ["quadrant", "bullet_graph", "swimlane", "gantt", "change_chart", "cycle_diagram", "journey_map", "maturity_ladder", "treemap", "venn_diagram", "callout_anatomy", "org_chart"]
ATTACK = '"><img src=x onerror=alert(1)>\'"><svg onload=alert(1)></script><script>alert(4)</script> onmouseover=alert(2)'


def _example(t):
    return copy.deepcopy(g._EXAMPLE_BLOCKS[t])


def _mutate(v, f):
    if isinstance(v, str): return f(v)
    if isinstance(v, list): return [_mutate(i, f) for i in v]
    if isinstance(v, dict): return {k: (x if k == "type" else _mutate(x, f)) for k, x in v.items()}
    return v


@pytest.fixture(scope="module")
def out(core_js):
    return dict(zip(ATOMS, _gas_batch(core_js, [_example(t) for t in ATOMS])))


def test_all_twelve_are_preview_atoms_in_the_schema_and_a_pack():
    import yaml
    from pathlib import Path
    root = Path(__file__).parent.parent
    d = {a["type"]: a for a in yaml.safe_load((root / "atoms/schema.yaml").read_text())["blocks"]}
    packs = (root / "atoms/atom-packs.yaml").read_text()
    for t in ATOMS:
        assert d[t].get("stage") == "preview", t
        assert re.search(rf"^- {t}$", packs, re.M), t


def test_each_example_renders_its_own_text(out):
    for t in ATOMS:
        h = out[t]
        assert len(h) > 300 and "NaN" not in h and "undefined" not in h and "Infinity" not in h and "[object" not in h, t
    assert "Backlog prioritisation" in out["quadrant"] and "target met" in out["bullet_graph"] and "Triage" in out["swimlane"]
    assert "Data" in out["gantt"] and "Auth service" in out["change_chart"] and "1. Plan" in out["cycle_diagram"]
    assert "Positive" in out["journey_map"] and "[CURRENT]" in out["maturity_ladder"] and "Worker nodes" in out["treemap"]
    assert "Sprint planning" in out["venn_diagram"] and "TLS terminator" in out["callout_anatomy"] and "VP Engineering" in out["org_chart"]


def test_every_atom_is_motion_ready_and_script_free(out):
    for t in ATOMS:
        assert "var(--p,1)" in out[t], f"{t}: does not read --p"
        assert "<script" not in out[t].lower(), t


def test_a_decorative_svg_is_hidden_and_has_a_text_table(out):
    for t in ("change_chart", "cycle_diagram"):
        assert 'aria-hidden="true"' in out[t], t
    assert "<table" in out["change_chart"] and "<ol" in out["cycle_diagram"]


def test_status_is_always_a_word_as_well_as_a_colour(out):
    assert "Positive" in out["journey_map"] and "Negative" in out["journey_map"] and "Neutral" in out["journey_map"]
    assert "target met" in out["bullet_graph"] or "below target" in out["bullet_graph"]


class _Audit(HTMLParser):
    def __init__(self):
        super().__init__(); self.bad = set()

    def handle_starttag(self, tag, attrs):
        for k, v in attrs:
            if k.startswith("on"): self.bad.add(f"handler {k}")
            if k in ("href", "src") and (v or "").strip().lower().startswith("javascript:"): self.bad.add("js url")
        if tag in ("img", "script", "iframe", "object", "embed"): self.bad.add(tag)


def test_hostile_text_never_becomes_markup(core_js):
    blocks = [_mutate(_example(t), lambda s: ATTACK) for t in ATOMS]
    for t, h in zip(ATOMS, _gas_batch(core_js, blocks)):
        a = _Audit(); a.feed(h)
        assert not a.bad, (t, a.bad)
        assert "alert(4)</script>" not in h, t


def test_extreme_numbers_are_clamped_not_printed_raw(core_js):
    big = _example("bullet_graph"); big["rows"][0].update(actual=-5, target=1e30, ranges=[9e99, "x", None])
    ch = _example("change_chart"); ch["rows"][0].update({"from": -3, "to": "NaN"})
    tm = _example("treemap"); tm["items"][0]["value"] = 1e400
    for t, h in zip(("bullet", "change", "treemap"), _gas_batch(core_js, [big, ch, tm])):
        assert "NaN" not in h and "Infinity" not in h and "e+" not in h, t


def test_garbage_shapes_do_not_throw(core_js):
    junk = [{"type": t, **{k: v for k, v in []}} for t in ATOMS] + [{"type": t, "items": "x", "rows": 3, "stages": None, "tasks": {}, "nodes": [None, 4], "levels": "no", "callouts": [1], "x_axis": "q"} for t in ATOMS]
    for h in _gas_batch(core_js, junk):
        assert "Error rendering" not in h


def _probe_gas(core_js, block, t, js):
    """Render `block` with the GAS core (these atoms have no Python twin), seek the film to t seconds in headless Chromium and run js on the live DOM."""
    import html as _h, json, subprocess, tempfile
    from pathlib import Path
    from test_motion_atoms import CHROMIUM
    page = "<!doctype html><meta charset=utf-8><body style='margin:0'>" + _gas_batch(core_js, [block])[0] + "<script>document.documentElement.setAttribute('data-probe', JSON.stringify((function(){" + js + "})()));</script>"
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "p.html"; f.write_text(page)
        dump = subprocess.run([CHROMIUM, "--headless=new", "--password-store=basic", "--no-sandbox", "--disable-gpu", "--window-size=1000,700", "--virtual-time-budget=1500", "--dump-dom", f"file://{f}#t={t}"], capture_output=True, text=True, timeout=90).stdout
    m = re.search(r"data-probe='([^']*)'|data-probe=\"([^\"]*)\"", dump)
    assert m, dump[:300]
    return json.loads(_h.unescape(m.group(1) or m.group(2)))


@browser
def test_quadrant_cards_build_with_p(core_js):
    tl = _scene([dict(_example("quadrant"), id="q", place={"x": 5, "y": 5, "w": 90})], [{"target": "q", "keys": [{"t": 0, "p": 0}, {"t": 4, "p": 1}]}])
    js = "var c=document.querySelectorAll('[data-mt-id=q] div[style*=\"--k\"]');return Array.prototype.map.call(c,function(e){return +getComputedStyle(e).opacity;}).slice(0,4);"
    start, end = _probe_gas(core_js, tl, 0, js), _probe_gas(core_js, tl, 4, js)
    assert start and max(start) < 0.05, start
    assert end and min(end) > 0.95, end


@browser
def test_bullet_bar_grows_with_p(core_js):
    tl = _scene([dict(_example("bullet_graph"), id="b", place={"x": 5, "y": 5, "w": 90})], [{"target": "b", "keys": [{"t": 0, "p": 0}, {"t": 4, "p": 1}]}])
    js = "var e=document.querySelector('[data-mt-id=b] div[style*=\"background:#0F172A\"]');return e?e.getBoundingClientRect().width:-1;"
    w0, w1 = _probe_gas(core_js, tl, 0, js), _probe_gas(core_js, tl, 4, js)
    assert w0 >= 0 and w1 > w0 + 20, (w0, w1)


# ── Python twins of the twelve atoms must match the GAS renderer byte for byte ─────────────────────────────────────────────────────────────────
from test_motion_atoms import _norm, _py  # noqa: E402


def _twin_cases():
    cases = [_example(t) for t in ATOMS]
    cases += [_mutate(_example(t), lambda s: ATTACK + s) for t in ATOMS]
    cases += [_mutate(_example(t), lambda s: s * 40) for t in ATOMS]                       # over-long text is cut at the same place
    cases += [{"type": t} for t in ATOMS]                                                     # empty payloads
    cc = _example("change_chart")
    cases += [dict(cc, mode=m) for m in ("bars", "slope", "dumbbell", "nope")]
    cases += [dict(cc, mode="slope", rows=[{"label": "a", "from": 0.125, "to": 2.5}, {"label": "b", "from": "7", "to": None}, {"label": "c", "from": True, "to": [3]}, {"label": "d", "from": -4, "to": "x"}, 5, None]),
              dict(cc, mode="bars", series=["x", 7, None], rows=[{"label": 1, "from": 1e13, "to": 0.005}]), dict(cc, mode="dumbbell", rows=[]), dict(cc, series=[["a", "b"], {"k": 1}])]
    bg = _example("bullet_graph")
    cases += [dict(bg, rows=[{"label": "z", "actual": 0, "target": 0, "ranges": []}, {"label": "y", "actual": "12.345", "target": 12.345, "ranges": [5, "x", 1, 99, 100]}, {"label": "w", "actual": 1e10, "target": -5, "ranges": [0.125]}, 7, None])]
    g_ = _example("gantt")
    cases += [dict(g_, intervals=["a"], tasks=[{"task": 1, "start_slot": 9, "duration_slots": 9, "category": 5}, {"task": None, "start_slot": "1", "duration_slots": 0, "category": None}, "x", None, {"category": True}]),
              dict(g_, intervals=[], tasks=[{"task": "t"}]), dict(g_, tasks=[{"task": str(i), "start_slot": i % 5, "duration_slots": 2, "category": "c" + str(i % 7)} for i in range(14)])]
    sw = _example("swimlane")
    cases += [dict(sw, roles=["r", 1, None, True, "x"], phases=["p", 2, False], tasks=[{"role": "r", "phase": "p", "task": "a"}, {"role": 1, "phase": 2, "task": "b"}, {"role": True, "phase": False, "task": 3}, 7, None, "s"] * 3)]
    tm = _example("treemap")
    cases += [dict(tm, items=[{"category": "a", "name": "n", "value": 0.1}, {"category": "a", "name": "m", "value": 0.2}, {"category": "b", "value": "5"}, {"category": 7, "name": 1, "value": -3}, {"name": "q", "value": 1e-7}, {"category": "e", "name": "f", "value": 0}, {"category": "c"}, {"category": "d", "name": "z", "value": 9}, {"category": "x", "name": "y", "value": 1}, 4, None])]
    qd = _example("quadrant")
    cases += [dict(qd, items=[{"item": "a", "quadrant": "top_left", "note": 0}, {"item": "b", "quadrant": "top_left", "note": "n"}, {"item": 3, "quadrant": "nope"}, "x", None, {"item": "c", "quadrant": 7}] + [{"item": str(i), "quadrant": "top_right"} for i in range(6)], x_axis="bad", y_axis=None)]
    ca = _example("callout_anatomy")
    cases += [dict(ca, callouts=[{"id": 0, "title": "a", "pin_position": "bottom_right"}, {"id": "7", "title": "b", "pin_position": "bottom_left"}, {"id": 99.6, "title": "c"}, {"id": None, "pin_position": "x"}, {"id": 500, "pin_position": "top_right"}, 3, None])]
    oc = _example("org_chart")
    cases += [dict(oc, nodes=[{"id": "a", "label": "A", "parent_id": ""}, {"id": "b", "label": "B", "parent_id": "a"}, {"id": "c", "parent_id": "b"}, {"id": "d", "label": 4, "parent_id": "c"}, {"id": "e", "parent_id": "d"}, {"id": "f", "label": "loop", "parent_id": "f"}, {"id": 1, "parent_id": None}, {"parent_id": "a"}, 5, None])]
    jm, ml, vd, cy = _example("journey_map"), _example("maturity_ladder"), _example("venn_diagram"), _example("cycle_diagram")
    cases += [dict(jm, stages=[{"stage": 1, "sentiment": "bogus"}, {"stage": "x", "sentiment": "positive"}, None, "s", {}]), dict(ml, levels=[{"level": 12345, "name": 9, "is_current": "true"}, {"level": 2, "is_current": True}, None, 4]),
              dict(vd, set_a_exclusive="notalist", intersection=[1, None, True, ["a"], {"k": 1}], set_b_exclusive=[]), dict(cy, stages=[{"name": "only"}]), dict(cy, stages=[{"name": str(i), "description": "d"} for i in range(9)])]
    return cases


def test_python_twins_of_the_twelve_infographic_atoms_match_gas_exactly(core_js):
    cases = _twin_cases()
    got = _gas_batch(core_js, cases)
    bad = [(c.get("type"), i) for i, (c, gh) in enumerate(zip(cases, got)) if _norm(_py(c)) != _norm(gh)]
    assert not bad, bad
