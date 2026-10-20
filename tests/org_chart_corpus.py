"""Shared org_chart payloads: every one the existing org_chart tests use, plus malformed and seeded random trees.

Used by tests/test_org_chart_layouts.py to prove that an absent `layout`, "tree" and any unknown value render exactly what org_chart
rendered before the `layout` field existed (tests/fixtures/org_chart_tree_baseline.json holds the hashes from the pre-change code),
and by the cluster and radial tests as a common set of trees. No imports from the renderer: plain data.
"""
from __future__ import annotations

from test_org_chart_tree import GOLDEN, FOREST, _payload


def _tree(title, spec):
    return {"type": "org_chart", "title": title, "nodes": [{"id": i, "label": l, "parent_id": p} for i, l, p in spec]}


def _lcg(seed):
    s = [seed]

    def r():
        s[0] = (s[0] * 1664525 + 1013904223) % 4294967296
        return s[0] / 4294967296
    return r


def random_tree(seed, max_nodes=30, forest=False):
    """A tree within the caps (30 nodes, 4 tiers, 6 children), labels of varying length; with forest=True several top-level nodes."""
    r = _lcg(seed)
    n = 1 + int(r() * max_nodes)
    depth, kids = [0], [0]
    parent = [-1]
    top = 0
    for _i in range(1, n):
        m = len(parent)
        for _ in range(40):
            p = int(r() * m)
            if depth[p] < 3 and kids[p] < 6:
                break
        else:
            p = -2
        if p == -2:
            if forest and top < 6:
                parent.append(-1)
                depth.append(0)
                kids.append(0)
                top += 1
            continue
        parent.append(p)
        depth.append(depth[p] + 1)
        kids.append(0)
        kids[p] += 1
    words = ["Platform", "Design", "Ops", "Finance lead", "Infrastructure", "QA", "Growth marketing", "Data science", "Legal", "R&D <b>", "Workstream", "People"]
    nodes = []
    for i, p in enumerate(parent):
        lab = words[int(r() * len(words))] + (" %d" % i if r() < 0.5 else "")
        if r() < 0.12:
            lab = "x" * (1 + int(r() * 28))
        nodes.append({"id": "n%d" % i, "label": lab, "parent_id": "" if p < 0 else "n%d" % p})
    return {"type": "org_chart", "title": "Fuzz %d" % seed, "nodes": nodes}


def corpus():
    c = {}
    for name, g in GOLDEN.items():
        c["golden_" + name] = _payload(g, name == FOREST)
    c["leadership"] = _tree("Leadership", [("ceo", "CEO", ""), ("e", "VP Engineering", "ceo"), ("p", "Platform lead", "e"), ("m", "ML lead", "e"), ("s", "VP Sales", "ceo"),
                                           ("a", "Account executives", "s"), ("se", "Solutions engineers", "s"), ("o", "VP Operations", "ceo"), ("f", "Facilities", "o"), ("c", "CFO", "ceo")])
    c["unbalanced"] = _tree("Unbalanced", [("p", "Programme", ""), ("a", "Workstream A", "p"), ("d", "Discovery", "a"), ("b", "Build", "a"), ("l", "Launch", "a"), ("w", "Workstream B", "p"), ("m", "Migration", "w")])
    c["small"] = _tree("Small", [("h", "Head of design", ""), ("pd", "Product design", "h"), ("br", "Brand", "h")])
    c["example"] = {"type": "org_chart", "title": "Engineering leadership", "nodes": [{"id": "1", "label": "VP Engineering", "parent_id": ""}, {"id": "2", "label": "Staff architect", "parent_id": "1"}, {"id": "3", "label": "Director, core", "parent_id": "1"}, {"id": "4", "label": "Director, apps", "parent_id": "1"}, {"id": "5", "label": "Data lead", "parent_id": "3"}, {"id": "6", "label": "Frontend lead", "parent_id": "4"}]}
    nodes = [{"id": "r", "label": "R", "parent_id": ""}]
    nodes += [{"id": "c%d" % i, "label": "C%d" % i, "parent_id": "r"} for i in range(8)]
    nodes += [{"id": "g1", "label": "G1", "parent_id": "c0"}, {"id": "g2", "label": "G2", "parent_id": "g1"}, {"id": "g3", "label": "G3", "parent_id": "g2"}, {"id": "g4", "label": "G4", "parent_id": "g3"}]
    nodes += [{"id": "x%d" % i, "label": "X%d" % i, "parent_id": "c1"} for i in range(30)]
    c["caps"] = {"type": "org_chart", "nodes": nodes}
    c["dup_ids"] = {"type": "org_chart", "nodes": [{"id": "a", "label": "A", "parent_id": ""}, {"id": "b", "label": "B1", "parent_id": "a"}, {"id": "b", "label": "B2", "parent_id": "a"}, {"id": "c", "label": "C", "parent_id": "b"}]}
    c["malformed"] = {"type": "org_chart", "title": "T", "nodes": [{"id": "a", "label": "A", "parent_id": ""}, {"id": "b", "label": "B", "parent_id": "a"}, {"id": "c", "parent_id": "b"}, {"id": "d", "label": 4, "parent_id": "c"}, {"id": "e", "parent_id": "d"}, {"id": "f", "label": "loop", "parent_id": "f"}, {"id": 1, "parent_id": None}, {"parent_id": "a"}, 5, None]}
    c["empty"] = {"type": "org_chart", "nodes": []}
    c["not_list"] = {"type": "org_chart", "nodes": "x"}
    c["hostile"] = _tree("<script>alert(1)</script>", [("r", "<img src=x onerror=1>", ""), ("a", "a&b \"q\" 'z'", "r"), ("b", "é中\U0001F600 emoji", "r")])
    c["cycle"] = _tree("Cycle", [("a", "A", "b"), ("b", "B", "a")])
    for seed in range(1, 41):
        c["fuzz%d" % seed] = random_tree(seed)
    for seed in range(101, 111):
        c["fuzzforest%d" % seed] = random_tree(seed, forest=True)
    return c
