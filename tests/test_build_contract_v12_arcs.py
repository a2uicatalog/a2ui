"""Build contract v1.2, per-arc keys (I75): in sunburst and circle_pack every arc or circle carries its own data-key.

v1.1 animates whole rings, so each ring <g> keeps data-cb="arc" and its ring key. A transition joins single arcs by data, so
each <path> or <circle> inside a ring also carries a data-key: the item's category path, the same key its label uses. The
shapes inside carry no data-cb (as the chord ribbons and arc_diagram paths). Additive: test_build_contract_v12 still checks
that stripping every data-key gives the v1.1 bytes.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from test_build_contract_charts import CASES  # noqa: E402
from test_build_contract_v12 import KEY, _safe_pairs  # noqa: E402
from test_motion_atoms import _norm, core_js  # noqa: E402,F401

ARC_CASES = {n: CASES[n] for n in ("sunburst", "circle_pack")}
RING = re.compile(r'<g class="(?:sbr|cpr)(?: cb-fade)?" data-cb="arc"[^>]*>(.*?)</g>', re.S)
SHAPE = re.compile(r'<(path|circle)\b[^>]*>')
LABEL = re.compile(r'<div data-cb="label"[^>]*>')


@pytest.fixture(scope="module")
def pairs(core_js):
    return _safe_pairs(core_js, ARC_CASES)


def _shapes(html):
    return [m.group(0) for r in RING.finditer(html) for m in SHAPE.finditer(r.group(1))]


@pytest.mark.parametrize("name", list(ARC_CASES))
def test_python_and_gas_agree(name, pairs):
    py, gas = pairs[name]
    assert _norm(py) == _norm(gas)


@pytest.mark.parametrize("name", list(ARC_CASES))
def test_every_arc_carries_a_unique_data_key(name, pairs):
    py, _ = pairs[name]
    shapes = _shapes(py)
    assert shapes, "no arcs found inside the rings"
    keys = [(KEY.search(s).group(1) if KEY.search(s) else '') for s in shapes]
    assert all(k.strip() for k in keys), "arc without a data-key: %s" % [s[:120] for s, k in zip(shapes, keys) if not k.strip()][:3]
    assert len(keys) == len(set(keys)), "duplicate arc keys: %s" % sorted({k for k in keys if keys.count(k) > 1})[:5]


@pytest.mark.parametrize("name", list(ARC_CASES))
def test_the_arcs_carry_no_data_cb(name, pairs):
    py, _ = pairs[name]
    assert not [s for s in _shapes(py) if 'data-cb=' in s]


@pytest.mark.parametrize("name", list(ARC_CASES))
def test_every_label_shares_its_arcs_key(name, pairs):
    py, _ = pairs[name]
    arcs = {KEY.search(s).group(1) for s in _shapes(py) if KEY.search(s)}
    labels = [KEY.search(l).group(1) for l in LABEL.findall(py) if KEY.search(l)]
    assert labels
    assert not [k for k in labels if k not in arcs], "labels whose key no arc carries: %s" % [k for k in labels if k not in arcs][:5]
