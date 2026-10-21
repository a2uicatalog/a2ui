"""swimlane `links` and `layout: "auto"` (I32 / D10): numbered tasks joined by labelled arrows, and columns derived from the links.

Held here:
* GOLDEN (tests/fixtures/swimlane_depth_d3_golden.json, from swimlane_depth_d3_golden_gen.mjs) is node.depth from the REAL d3-sankey 0.12.3
  on acyclic graphs; both twins' longest-path layering must equal it. Cycles (d3-sankey throws on them) are hand-computed below.
* BASELINE (tests/fixtures/swimlane_baseline.json, rendered by the code before this change): every existing swimlane payload renders byte for
  byte as before, in both twins, with `layout` absent, "grid" or unknown, and with `links` absent or empty.
* Python and GAS give byte-identical HTML; the geometry (no connector through a card, no chip over a card or another chip) is checked on the
  markup for hand-made and 300 random payloads; the hidden table, aria label, notes, caps, version, escaping and registration.
"""
from __future__ import annotations

import copy
import json
import random
import re
from pathlib import Path

import pytest
import yaml

from test_motion_atoms import _gas_batch, _node, _py, core_js  # noqa: F401  (core_js is a fixture)
from test_motion_atoms import wa  # noqa: E402
import generate_atom_pages as g

ROOT = Path(__file__).resolve().parent.parent
GOLD = json.loads((ROOT / "tests/fixtures/swimlane_depth_d3_golden.json").read_text())["cases"]
ATTACK = '"><img src=x onerror=alert(1)>\'"><svg onload=alert(1)></script><script>alert(4)</script> onmouseover=alert(2)'


def _sw(**kw):
    b = {"type": "swimlane"}
    b.update(kw)
    return b


# ─── the existing payloads (the baseline) ───────────────────────────────────────
_EX = copy.deepcopy(g._EXAMPLE_BLOCKS["swimlane"])
BASE = {
    "example": _EX,
    "full": _sw(title="Release", roles=["Dev", "QA", "Ops", "PM"], phases=["Plan", "Build", "Test", "Ship", "Run"],
                tasks=[{"role": r, "phase": p, "task": "%s in %s" % (r, p)} for r in ("Dev", "QA", "Ops", "PM") for p in ("Plan", "Build", "Test")][:12]),
    "three_in_a_cell": _sw(roles=["a", "b"], phases=["x", "y"], tasks=[{"role": "a", "phase": "x", "task": "one"}, {"role": "a", "phase": "x", "task": "two"},
                                                                        {"role": "a", "phase": "x", "task": "three"}, {"role": "b", "phase": "y", "task": "four"}]),
    "odd": _sw(roles=["r", 1, None, True, "x"], phases=["p", 2, False], tasks=[{"role": "r", "phase": "p", "task": "a"}, {"role": 1, "phase": 2, "task": "b"},
                                                                                 {"role": True, "phase": False, "task": 3}, 7, None, "s"] * 3),
    "hostile": _sw(title=ATTACK, roles=[ATTACK, "b"], phases=[ATTACK, "q"], tasks=[{"role": ATTACK, "phase": ATTACK, "task": ATTACK}, {"role": "b", "phase": "q", "task": "ok"}]),
    "unlisted": _sw(roles=["a", "b"], phases=["x", "y"], tasks=[{"role": "zzz", "phase": "x", "task": "lost"}, {"role": "a", "phase": "nope", "task": "lost too"}, {"role": "b", "phase": "y", "task": "kept"}]),
    "no_phases": _sw(roles=["a", "b"], tasks=[{"role": "a", "phase": "x", "task": "t"}]),
    "no_roles": _sw(phases=["a", "b"], tasks=[{"role": "a", "phase": "a", "task": "t"}]),
    "tasks_not_list": _sw(roles=["a", "b"], phases=["x", "y"], tasks={"role": "a"}),
    "bare": _sw(),
    "title_numbers": _sw(title=7, roles=[1, 2], phases=[3, 4], tasks=[{"role": 1, "phase": 3, "task": 5}, {"role": 2, "phase": 4}]),
}
VARIANTS = {"plain": {}, "grid": {"layout": "grid"}, "unknown": {"layout": "nope"}, "number": {"layout": 7}, "empty_links": {"links": []},
            "grid_empty_links": {"layout": "grid", "links": []}, "links_not_list": {"links": "x"}}
BASELINE = json.loads((ROOT / "tests/fixtures/swimlane_baseline.json").read_text()) if (ROOT / "tests/fixtures/swimlane_baseline.json").exists() else {}


def test_baseline_fixture_covers_every_payload():
    assert set(BASELINE) == set(BASE)


@pytest.mark.parametrize("name", list(BASE))
def test_existing_payloads_render_byte_for_byte_as_before_in_python(name):
    for vn, extra in VARIANTS.items():
        assert _py(dict(BASE[name], **extra)) == BASELINE[name], (name, vn)


def test_existing_payloads_render_byte_for_byte_as_before_in_gas(core_js):
    blocks = [dict(BASE[n], **ex) for n in BASE for ex in VARIANTS.values()]
    res = iter(_gas_batch(core_js, blocks))
    for n in BASE:
        for vn in VARIANTS:
            assert next(res) == BASELINE[n], (n, vn)


# ─── layering against real d3-sankey ─────────────────────────────────────────────
@pytest.mark.parametrize("name", list(GOLD))
def test_python_depths_match_d3_sankey(name):
    c = GOLD[name]
    depth, ignored = wa._sw_depth(c["n"], [tuple(e) for e in c["edges"]])
    assert depth == c["depth"] and ignored == []


def test_gas_depths_match_d3_sankey(core_js):
    names = list(GOLD)
    res = _node(core_js, "var G = " + json.dumps([GOLD[n] for n in names]) + "; console.log(JSON.stringify(G.map(function(c){ return _swDepth(c.n, c.edges); })));")
    for n, (depth, ignored) in zip(names, res):
        assert depth == GOLD[n]["depth"] and ignored == [], n


CYCLES = {  # (n, edges) -> (depth, ignored edge indexes): the back edge found by a depth-first walk from the tasks with no incoming link, then from task 1
    "two_cycle": (2, [(0, 1), (1, 0)], [0, 1], [1]),
    "tail_cycle": (3, [(0, 1), (1, 2), (2, 1)], [0, 1, 2], [2]),
    "ring_no_root": (3, [(1, 2), (2, 0), (0, 1)], [0, 1, 2], [1]),
    "self_edge": (2, [(0, 1), (1, 1)], [0, 1], [1]),
    "cycle_then_exit": (4, [(0, 1), (1, 2), (2, 1), (2, 3)], [0, 1, 2, 3], [2]),
}


@pytest.mark.parametrize("name", list(CYCLES))
def test_cycles_ignore_the_back_edge_python(name):
    n, edges, depth, ignored = CYCLES[name]
    assert wa._sw_depth(n, edges) == (depth, ignored)


def test_cycles_ignore_the_back_edge_gas(core_js):
    names = list(CYCLES)
    res = _node(core_js, "var C = " + json.dumps([[CYCLES[n][0], CYCLES[n][1]] for n in names]) + "; console.log(JSON.stringify(C.map(function(c){ return _swDepth(c[0], c[1]); })));")
    for n, (depth, ignored) in zip(names, res):
        assert [depth, ignored] == [CYCLES[n][2], CYCLES[n][3]], n


# ─── payloads with links ─────────────────────────────────────────────────────────
ARCH = _sw(title="Voice assistant", roles=["Device", "Server", "Cloud"], layout="auto",
           tasks=[{"role": "Device", "task": "Phone app records the request"}, {"role": "Server", "task": "API gateway checks the token"},
                  {"role": "Cloud", "task": "Model turns speech into an answer"}, {"role": "Cloud", "task": "Store keeps the transcript"},
                  {"role": "Device", "task": "Phone app shows the answer"}],
           links=[{"from": 1, "to": 2, "label": "HTTPS request"}, {"from": 2, "to": 3, "label": "audio"}, {"from": 3, "to": 4, "label": "save"},
                  {"from": 3, "to": 5, "label": "answer"}])
GRIDL = _sw(title="Release", roles=["Dev", "QA", "Ops"], phases=["Build", "Verify", "Ship"],
            tasks=[{"role": "Dev", "phase": "Build", "task": "Merge"}, {"role": "QA", "phase": "Verify", "task": "Regression run"},
                   {"role": "Ops", "phase": "Ship", "task": "Deploy"}, {"role": "QA", "phase": "Build", "task": "Write tests"},
                   {"role": "Dev", "phase": "Ship", "task": "Announce"}],
            links=[{"from": 1, "to": 2, "label": "build"}, {"from": 4, "to": 2}, {"from": 2, "to": 3, "label": "green"}, {"from": 1, "to": 5, "label": "skip"},
                   {"from": 3, "to": 1, "label": "rollback"}, {"from": 4, "to": 1}])
SAMECOL = _sw(roles=["a", "b"], layout="auto",
              tasks=[{"role": "a", "task": "root"}, {"role": "a", "task": "left one"}, {"role": "b", "task": "left two"}, {"role": "b", "task": "left three"}],
              links=[{"from": 1, "to": 2, "label": "x"}, {"from": 1, "to": 3}, {"from": 1, "to": 4, "label": "y"}, {"from": 2, "to": 3, "label": "same column"}])
CYC = _sw(roles=["a", "b"], layout="auto", tasks=[{"role": "a", "task": "one"}, {"role": "b", "task": "two"}, {"role": "a", "task": "three"}],
          links=[{"from": 1, "to": 2}, {"from": 2, "to": 3, "label": "next"}, {"from": 3, "to": 2, "label": "retry"}])
LONG = _sw(roles=["a", "b"], layout="auto", tasks=[{"role": "ab"[i % 2], "task": "step %d" % (i + 1)} for i in range(9)],
           links=[{"from": i + 1, "to": i + 2, "label": "to %d" % (i + 2)} for i in range(8)])
NOLINKS_AUTO = _sw(roles=["a", "b"], layout="auto", tasks=[{"role": "a", "task": "x"}, {"role": "b", "task": "y"}])
LONGLABEL = _sw(roles=["a", "b", "c"], layout="auto", tasks=[{"role": "a", "task": "alpha"}, {"role": "b", "task": "beta"}, {"role": "c", "task": "gamma"}],
                links=[{"from": 1, "to": 2, "label": "W" * 24}, {"from": 2, "to": 3, "label": "mmmmmmmmmmmmmmmmmmmmmmmm"}, {"from": 1, "to": 3, "label": "i" * 24}])
NINE = _sw(title="Nine tasks, four lanes", roles=["Client", "Edge", "Core", "Data"], layout="auto", phases=["Send", "Route", "Work", "Persist", "Reply"],
           tasks=[{"role": "Client", "task": "Browser sends a request"}, {"role": "Edge", "task": "CDN checks its cache"}, {"role": "Edge", "task": "Gateway authenticates"},
                  {"role": "Core", "task": "Service A prepares a job"}, {"role": "Core", "task": "Service B enriches it"}, {"role": "Data", "task": "Database stores it"},
                  {"role": "Data", "task": "Queue schedules a mail"}, {"role": "Core", "task": "Service A builds the reply"}, {"role": "Client", "task": "Browser shows the result"}],
           links=[{"from": 1, "to": 2, "label": "GET"}, {"from": 2, "to": 3, "label": "miss"}, {"from": 3, "to": 4, "label": "token ok"}, {"from": 3, "to": 5},
                  {"from": 4, "to": 6, "label": "write"}, {"from": 5, "to": 6, "label": "write"}, {"from": 4, "to": 7, "label": "enqueue"}, {"from": 6, "to": 8, "label": "ack"},
                  {"from": 8, "to": 9, "label": "200 OK"}, {"from": 2, "to": 9, "label": "cached hit"}, {"from": 7, "to": 8}])
LINKED = {"arch": ARCH, "grid": GRIDL, "samecol": SAMECOL, "cyc": CYC, "long": LONG, "nolinks_auto": NOLINKS_AUTO, "longlabel": LONGLABEL, "nine": NINE}


def _rand_payload(rng):
    R = rng.randint(2, 4)
    roles = ["Lane %d" % i for i in range(R)]
    n = rng.randint(2, 12)
    mode = rng.choice(["auto", "grid"])
    ph = ["P%d" % i for i in range(rng.randint(2, 5))]
    tasks = []
    for i in range(n):
        t = {"role": rng.choice(roles), "task": "t%d %s" % (i + 1, "word " * rng.randint(0, 11))}
        if mode == "grid":
            t["phase"] = rng.choice(ph)
        tasks.append(t)
    links = []
    for _ in range(rng.randint(0, 24)):
        l = {"from": rng.randint(1, n), "to": rng.randint(1, n)}
        if rng.random() < 0.7:
            l["label"] = rng.choice(["go", "hand off", "W" * rng.randint(1, 24), "a b c d e f g h", "ok"])
        links.append(l)
    b = _sw(roles=roles, tasks=tasks, links=links, layout=mode)
    if mode == "grid":
        b["phases"] = ph
    return b


RANDOM = {"rnd%d" % i: _rand_payload(random.Random(1000 + i)) for i in range(300)}


# ─── reading the markup ─────────────────────────────────────────────────────────
def _geo(html):
    cards = {int(m[0]): tuple(int(x) for x in m[1:]) for m in re.findall(r'class="swc" data-n="(\d+)" style="position:absolute;left:(-?\d+)px;top:(-?\d+)px;width:(\d+)px;height:(\d+)px', html)}
    chips = [tuple(int(x) for x in m) for m in re.findall(r'class="swl" style="position:absolute;left:(-?\d+)px;top:(-?\d+)px;width:(\d+)px;height:(\d+)px', html)]
    paths = [(int(f), int(t), d) for f, t, d in re.findall(r'<path class="swp" data-f="(\d+)" data-t="(\d+)" d="([^"]+)"', html)]
    m = re.search(r'class="swv" style="position:relative;width:(\d+)px;height:(\d+)px', html)
    return cards, chips, paths, (int(m[1]), int(m[2])) if m else None


def _segments(d):
    toks = re.findall(r'([MHV])(-?\d+)', d)
    x = y = 0
    segs = []
    for c, v in toks:
        v = int(v)
        if c == 'M':
            x, y = v, y
        elif c == 'H':
            segs.append(((x, y), (v, y)))
            x = v
        else:
            segs.append(((x, y), (x, v)))
            y = v
        if c == 'M':
            pass
    return segs


def _path_points(d):
    pts, x, y = [], 0, 0
    m = re.match(r'M(-?\d+) (-?\d+)', d)
    x, y = int(m[1]), int(m[2])
    pts.append((x, y))
    for c, v in re.findall(r'([HV])(-?\d+)', d):
        v = int(v)
        if c == 'H':
            x = v
        else:
            y = v
        pts.append((x, y))
    return pts


def _check_geometry(html):
    cards, chips, paths, size = _geo(html)
    errs = []
    for (f, t, d) in paths:
        pts = _path_points(d)
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            for n, (cx, cy, cw, ch) in cards.items():
                if y1 == y2:
                    hit = cy < y1 < cy + ch and min(x1, x2) < cx + cw and max(x1, x2) > cx
                else:
                    hit = cx < x1 < cx + cw and min(y1, y2) < cy + ch and max(y1, y2) > cy
                if hit:
                    errs.append("link %d->%d crosses card %d" % (f, t, n))
    for i, (x, y, w, h) in enumerate(chips):
        for n, (cx, cy, cw, ch) in cards.items():
            if x < cx + cw and cx < x + w and y < cy + ch and cy < y + h:
                errs.append("chip %d over card %d" % (i, n))
        for j in range(i):
            x2, y2, w2, h2 = chips[j]
            if x < x2 + w2 and x2 < x + w and y < y2 + h2 and y2 < y + h:
                errs.append("chips %d and %d overlap" % (i, j))
        if size and (x < 0 or y < 0 or x + w > size[0] or y + h > size[1]):
            errs.append("chip %d outside the canvas" % i)
    for n, (cx, cy, cw, ch) in cards.items():
        if size and (cx < 0 or cy < 0 or cx + cw > size[0] or cy + ch > size[1]):
            errs.append("card %d outside the canvas" % n)
        for m, (dx, dy, dw, dh) in cards.items():
            if m < n and cx < dx + dw and dx < cx + cw and cy < dy + dh and dy < cy + ch:
                errs.append("cards %d and %d overlap" % (m, n))
    return errs


@pytest.fixture(scope="module")
def gas_all(core_js):
    allp = {**LINKED, **RANDOM}
    return dict(zip(allp, _gas_batch(core_js, list(allp.values()))))


def test_python_and_gas_are_byte_identical_on_every_linked_payload(gas_all):
    for n, b in {**LINKED, **RANDOM}.items():
        assert _py(b) == gas_all[n], n


def test_python_and_gas_are_byte_identical_on_malformed_links(core_js):
    cases = []
    for lk in ([None, 5, "x", [], {"from": 1}, {"from": "1", "to": "2", "label": 7}, {"from": 1.5, "to": 2}, {"from": True, "to": 2}, {"from": 1, "to": 1},
                {"from": 1, "to": 2, "label": {"a": 1}}, {"from": 1, "to": 2, "label": ATTACK}, {"from": 0, "to": 2}, {"from": 99, "to": 1}, {"from": "01", "to": " 2"}],
               "nope", {"from": 1, "to": 2}, [{"from": 1, "to": 2}] * 30, [{"from": 1, "to": 3, "label": None}, {"from": 3, "to": 1, "label": ""}]):
        for lay in ("auto", "grid", None):
            b = dict(ARCH if lay == "auto" else GRIDL, links=lk)
            if lay is None:
                b.pop("layout", None)
            else:
                b["layout"] = lay
            cases.append(b)
    cases += [dict(ARCH, tasks=[None, 7, "s", {"role": "Device"}, {"role": "Cloud", "task": None}, {"task": "norole"}], links=[{"from": 4, "to": 5}, {"from": 1, "to": 5}]),
              dict(ARCH, roles=["x"], links=[{"from": 1, "to": 2}]), dict(ARCH, roles=None), dict(ARCH, phases=["only"]), dict(ARCH, phases="x", layout="auto"),
              dict(ARCH, tasks=[{"role": "Device", "task": "a"}] * 12, links=[{"from": i, "to": i + 1} for i in range(1, 12)]), dict(ARCH, version=3), dict(ARCH, version="x")]
    py = [_py(b) for b in cases]
    gas = _gas_batch(core_js, cases)
    assert py == gas
    for h in py:
        assert not re.search(r'NaN|undefined|Infinity|\[object|<script', h)


# ─── content ─────────────────────────────────────────────────────────────────────
def _table_rows(h):
    t = re.search(r'<table style="[^"]*"><thead><tr><th scope="col">From</th><th scope="col">To</th><th scope="col">Label</th></tr></thead><tbody>(.*?)</tbody></table>', h, re.S)
    assert t, h[-600:]
    return [re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', r) for r in re.findall(r'<tr>(.*?)</tr>', t[1], re.S)]


def test_hidden_table_lists_every_drawn_link_and_the_aria_label_counts_them():
    h = _py(ARCH)
    assert _table_rows(h) == [["1. Phone app records the request", "2. API gateway checks the token", "HTTPS request"],
                              ["2. API gateway checks the token", "3. Model turns speech into an answer", "audio"],
                              ["3. Model turns speech into an answer", "4. Store keeps the transcript", "save"],
                              ["3. Model turns speech into an answer", "5. Phone app shows the answer", "answer"]]
    assert 'role="group" aria-label="Voice assistant: 5 tasks across 3 lanes, 4 links"' in h and 'tabindex="0"' in h
    assert h.count('class="swp"') == 4 and h.count('class="swl"') == 4
    assert re.search(r'<svg[^>]* aria-hidden="true"', h) and 'marker-end="url(#swarr)"' in h and '<marker id="swarr"' in h
    assert "<table" in h and h.index("</table>") > h.index('class="swv"')          # the table is a sibling after the picture, not inside it
    assert "1 link" in _py(dict(ARCH, links=[{"from": 1, "to": 2}])) and "1 links" not in _py(dict(ARCH, links=[{"from": 1, "to": 2}]))


def test_the_label_is_missing_from_the_chip_when_empty_and_blank_in_the_table():
    h = _py(dict(ARCH, links=[{"from": 1, "to": 2}, {"from": 2, "to": 3, "label": ""}, {"from": 3, "to": 4, "label": "ok"}]))
    assert h.count('class="swl"') == 1 and [r[2] for r in _table_rows(h)] == ["", "", "ok"]


def test_numbers_on_the_cards_are_the_list_order_and_the_links_use_them():
    cards, chips, paths, _ = _geo(_py(GRIDL))
    assert sorted(cards) == [1, 2, 3, 4, 5] and [(f, t) for f, t, _ in paths] == [(1, 2), (4, 2), (2, 3), (1, 5), (3, 1), (4, 1)]


def test_grid_layout_keeps_the_phase_columns_and_auto_derives_them_from_the_links():
    cards = _geo(_py(GRIDL))[0]
    xs = {n: cards[n][0] for n in cards}
    assert xs[1] == xs[4] and xs[2] < xs[3] and xs[1] < xs[2] and xs[3] == xs[5]                 # Build, Verify, Ship
    ca = _geo(_py(ARCH))[0]
    assert ca[1][0] < ca[2][0] < ca[3][0] < ca[4][0] and ca[4][0] == ca[5][0]                    # depths 0,1,2,3,3
    assert len({ca[n][0] for n in ca}) == 4
    cn = _geo(_py(NOLINKS_AUTO))[0]
    assert cn[1][0] == cn[2][0]                                                                  # no links: everything in column 1


def test_a_task_with_no_phase_is_fine_in_auto_and_unplaced_in_grid():
    h = _py(dict(ARCH, layout="grid"))
    assert "Phone app" not in h and "4 links were dropped" in h and 'class="swv"' not in h        # grid mode needs phases: nothing is placed, the old grid draws


def test_auto_column_headers_come_from_phases_when_given_and_are_absent_otherwise():
    assert 'class="swh"' not in _py(ARCH)
    h = _py(dict(ARCH, phases=["Capture", "Gate", "Think", "Return"]))
    assert [x for x in re.findall(r'class="swh"[^>]*>([^<]*)<', h)] == ["Capture", "Gate", "Think", "Return"]
    h2 = _py(dict(ARCH, phases=["Capture", "Gate"]))
    assert re.findall(r'class="swh"[^>]*>([^<]*)<', h2) == ["Capture", "Gate", "", ""]


def test_barycentre_orders_a_cell_in_auto_but_not_in_grid():
    tasks = [{"role": "L0", "task": "a"}, {"role": "L2", "task": "b"}, {"role": "L1", "task": "x"}, {"role": "L1", "task": "y"}]
    links = [{"from": 2, "to": 3}, {"from": 1, "to": 4}]
    c = _geo(_py(_sw(roles=["L0", "L1", "L2"], layout="auto", tasks=tasks, links=links)))[0]
    assert c[3][0] == c[4][0] and c[4][1] < c[3][1]                                              # y hangs from the upper lane, so it goes first
    cg = _geo(_py(_sw(roles=["L0", "L1", "L2"], layout="grid", phases=["p", "q"], tasks=[dict(t, phase="p" if i < 2 else "q") for i, t in enumerate(tasks)], links=links)))[0]
    assert cg[3][1] < cg[4][1]                                                                   # grid keeps the list order


def test_more_than_six_columns_fold_into_the_last_one_with_a_note():
    h = _py(LONG)
    cards = _geo(h)[0]
    assert len({v[0] for v in cards.values()}) == 6 and cards[6][0] == cards[7][0] == cards[9][0]
    assert "last column" in h and "3 tasks would need more than 6 columns" in h
    assert "last column" not in _py(ARCH)


def test_links_that_cannot_be_drawn_are_dropped_with_a_note_and_the_rest_drawn():
    h = _py(dict(ARCH, links=[{"from": 1, "to": 2}, {"from": 9, "to": 1}, {"from": 2, "to": 2}, {"from": 1, "to": 2}, "x", {"from": 3}, {"from": 2, "to": 3}]))
    assert h.count('class="swp"') == 2 and "5 links were dropped" in h
    one = _py(dict(ARCH, links=[{"from": 1, "to": 2}, {"from": 9, "to": 1}]))
    assert "1 link was dropped" in one
    allbad = _py(dict(ARCH, layout="grid", links=[{"from": 9, "to": 1}]))
    assert "1 link was dropped" in allbad and 'class="swp"' not in allbad and 'class="swv"' not in allbad


def test_link_list_is_capped_at_24():
    b = dict(LONG, links=[{"from": 1, "to": 2, "label": str(i)} for i in range(30)])
    assert _py(b).count('class="swp"') == 1                                    # the 30 are repeats: the first is drawn, the other 23 inside the cap are dropped
    many = _sw(roles=["a", "b"], layout="auto", tasks=[{"role": "ab"[i % 2], "task": "t%d" % i} for i in range(12)],
               links=[{"from": i % 11 + 1, "to": i % 11 + 2} for i in range(30)])
    assert "dropped" in _py(many) and len(_table_rows(_py(many))) == 11


def test_a_cycle_is_drawn_and_noted_for_layering():
    h = _py(CYC)
    assert h.count('class="swp"') == 3 and "cycle" in h and "1 link was ignored" in h
    cards = _geo(h)[0]
    assert cards[1][0] < cards[2][0] < cards[3][0]
    assert "cycle" not in _py(ARCH)


def test_version_note_for_future_versions_only():
    assert "Written for swimlane version 3; drawn as version 1." in _py(dict(ARCH, version=3))
    assert "Written for swimlane" in _py(dict(BASE["example"], version=3))
    for v in (1, "x", None, 0.5, True):
        assert "Written for" not in _py(dict(ARCH, version=v))


def test_cards_are_motion_ready_and_script_free():
    h = _py(ARCH)
    assert "<script" not in h and "var(--k,1)" in h and "--k:clamp(0,calc(var(--p,1)*" in h
    ks = re.findall(r'class="swc" data-n="(\d+)" style="[^"]*--k:clamp\(0,calc\(var\(--p,1\)\*(\d+) - (\d+)\)', h)
    assert [(int(n) - 1, int(a) - 1) for n, a, _ in ks] == [(i, 5) for i in range(5)] and [int(i) for _, _, i in ks] == list(range(5))


def test_hostile_text_is_escaped_everywhere():
    b = dict(ARCH, title=ATTACK, roles=[ATTACK, "Server", "Cloud"], tasks=[dict(t, role=ATTACK if t["role"] == "Device" else t["role"], task=ATTACK) for t in ARCH["tasks"]],
             links=[dict(l, label=ATTACK) for l in ARCH["links"]])
    h = _py(b)
    assert "<img" not in h and "<svg onload" not in h and "<script" not in h and "&lt;img" in h


# ─── geometry ────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("name", list(LINKED))
def test_no_connector_crosses_a_card_and_no_label_sits_on_a_card_or_another_label(name):
    assert _check_geometry(_py(LINKED[name])) == []


def test_300_random_payloads_keep_connectors_off_cards_and_labels_apart():
    bad = {n: e for n, b in RANDOM.items() for e in [_check_geometry(_py(b))] if e}
    assert not bad, json.dumps(dict(list(bad.items())[:5]), indent=1)
    drawn = sum(_py(b).count('class="swp"') for b in RANDOM.values())
    assert drawn > 1000


def test_straight_neighbours_are_straight_and_arrows_end_on_the_card_edge():
    h = _py(_sw(roles=["a"], layout="auto", tasks=[{"role": "a", "task": "one"}, {"role": "a", "task": "two"}], links=[{"from": 1, "to": 2, "label": "go"}]))
    cards, chips, paths, _ = _geo(h)
    (x, y, w, ht) = cards[1]
    (x2, y2, _, _) = cards[2]
    pts = _path_points(paths[0][2])
    assert pts[0] == (x + w, y + ht // 2) and pts[-1] == (x2, y2 + ht // 2) and len({p[1] for p in pts}) == 1


# ─── registration ────────────────────────────────────────────────────────────────
def test_schema_describes_links_layout_and_version():
    d = {a["type"]: a for a in yaml.safe_load((ROOT / "atoms/schema.yaml").read_text())["blocks"]}["swimlane"]
    f = d["fields"]
    for k in ("links", "layout", "version"):
        assert k in f, k
    assert "24" in f["links"] and "auto" in f["layout"] and "grid" in f["layout"]
    assert "architecture" in d["routing_text"] and "sequence_diagram" in d["routing_text"]
    assert "phase" in f["tasks"] and "optional" in f["tasks"].lower()
    assert "cycle" in d["notes"].lower() and "6 columns" in (d["notes"] + f["layout"])
