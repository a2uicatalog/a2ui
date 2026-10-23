"""The motion_transition acceptance matrix (I75): every same-data pair in tests/fixtures/transition_pairs.json, in Chromium.

The pairs were proposed by Gemini 3.8 Flash and kept only where rendering both blocks showed at least three keys join.
For each: at p = 0 every matched B element starts on its A partner (exactly, box to box; fitted and centred where a
curved shape is involved) and at least three do; at p = 1 the page is B alone. Atoms with no same-data partner (contour,
voronoi: continuous fields) are named in the review page, not forced.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from test_motion_build import browser  # noqa: E402
from test_motion_transition import _close, _expected_start, _page  # noqa: E402

PAIRS = json.loads((Path(__file__).parent / "fixtures" / "transition_pairs.json").read_text())


def _blk(p):
    b = {"type": "motion_transition", "from": p["from"], "to": p["to"], "match": p.get("match", "path")}
    if p.get("key_map"):
        b["key_map"] = p["key_map"]
    return b


@browser
@pytest.mark.parametrize("pair", PAIRS, ids=[p["id"] for p in PAIRS])
def test_matched_elements_start_on_their_partners(pair):
    got = _page(_blk(pair), 0, 800)
    km = pair.get("key_map") or {}
    a = {km.get(k, k): v for k, v in got["a"].items()}
    matched = 0
    for k, r in got["b"].items():
        s = _expected_start(a, k) if pair.get("match", "path") == "path" else (a[k][:4] if k in a else None)
        if s is None:
            continue
        matched += 1
        rect_a = all(v[5] for q, v in a.items() if q == k or q.startswith(k + "/") or k.startswith(q + "/"))
        if r[5] and rect_a:
            assert _close(r, s, 2.5), (k, r[:4], s)
        else:
            assert abs(r[0] + r[2] / 2 - s[0] - s[2] / 2) <= 2.5 and abs(r[1] + r[3] / 2 - s[1] - s[3] / 2) <= 2.5, (k, r[:4], s)
    assert matched >= 3


@browser
@pytest.mark.parametrize("pair", PAIRS, ids=[p["id"] for p in PAIRS])
def test_at_p1_the_page_is_b(pair):
    got = _page(_blk(pair), 1, 800)
    alone = _page(pair["to"], None, 800)["b"]
    assert set(got["b"]) == set(alone)
    for k, r in got["b"].items():
        assert _close(r, alone[k], 0.6), k
    assert got["aop"] == pytest.approx(0)
