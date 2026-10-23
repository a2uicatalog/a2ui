"""Build contract v1.2 (owner 2026-10-22, I75): every data-cb element carries a data-key, so a transition joins A and B by data.

Spec: a2ui-private briefs/I75-2d-to-3d-motion-atoms.md and pm/i64/model/spec.md section 3, item 1. Per chart case, in Python and
in the wired GAS renderer: the same bytes; a non-empty data-key on every data-cb element; keys unique among the shapes and unique
among the labels (a label may share its shape's key); a link's or ribbon's key is "source→target" (a <g> grouping several
links keeps its v1.1 data-cb and is keyed by its source; each path inside carries its own source→target data-key). Additive: stripping the
data-key attributes gives exactly the v1.1 markup.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from test_build_contract_charts import CASES  # noqa: E402
from test_motion_atoms import _gas_batch, _norm, _py, core_js  # noqa: E402,F401

TAG = re.compile(r'<\w+[^>]* data-cb="(\w+)"[^>]*>')
KEY = re.compile(r' data-key="([^"]*)"')


def _safe_pairs(core_js, cases):
    """Render every case on its own, in Python and in GAS, so one crash fails only its own case (with the error text)."""
    import json as _j
    from test_motion_atoms import _node_raw as _node, _py_keyed as _py
    names = list(cases)
    body = "var B = %s; console.log(JSON.stringify(B.map(function(b){ try { return renderAtoms([b], {}); } catch (e) { return 'GAS ERROR: ' + (e && e.stack || e); } })));" % _j.dumps([cases[n][0] for n in names])
    try:
        gas = _node(core_js, body)
    except Exception as e:  # the GAS source itself does not load
        gas = ["GAS ERROR: " + str(e)[:2000]] * len(names)
    out = {}
    for i, n in enumerate(names):
        try:
            py = _py(cases[n][0])
        except Exception as e:
            py = "PY ERROR: %s: %s" % (type(e).__name__, e)
        out[n] = (py, gas[i])
    return out


@pytest.fixture(scope="module")
def pairs(core_js):
    return _safe_pairs(core_js, CASES)


@pytest.mark.parametrize("name", list(CASES))
def test_python_and_gas_agree(name, pairs):
    py, gas = pairs[name]
    assert _norm(py) == _norm(gas)


@pytest.mark.parametrize("name", list(CASES))
def test_every_contract_element_has_a_data_key(name, pairs):
    py, _ = pairs[name]
    tags = [(m.group(1), m.group(0)) for m in TAG.finditer(py)]
    assert tags
    missing = [t for _, t in tags if not (KEY.search(t) and KEY.search(t).group(1).strip())]
    assert not missing, "data-cb without a data-key: %s" % missing[:3]


@pytest.mark.parametrize("name", list(CASES))
def test_keys_are_unique_within_shapes_and_within_labels(name, pairs):
    py, _ = pairs[name]
    shapes, labels = [], []
    for m in TAG.finditer(py):
        k = KEY.search(m.group(0))
        if k:
            (labels if m.group(1) == "label" else shapes).append((m.group(1), k.group(1)))
    for group in (shapes, labels):
        seen = [g for g in group]
        assert len(seen) == len(set(seen)), "duplicate keys: %s" % sorted({g for g in seen if seen.count(g) > 1})[:5]


@pytest.mark.parametrize("name", list(CASES))
def test_links_and_ribbons_are_keyed_source_to_target(name, pairs):
    py, _ = pairs[name]
    for m in TAG.finditer(py):
        if m.group(1) in ("link", "ribbon") and not m.group(0).startswith("<g "):   # a group of links carries its source; its paths carry source→target
            k = KEY.search(m.group(0))
            assert k and "→" in k.group(1) and all(k.group(1).split("→", 1)), m.group(0)[:200]


BASE = json.loads((Path(__file__).parent / "fixtures" / "contract_v11_baseline.json").read_text())


@pytest.mark.parametrize("name", list(CASES))
def test_the_key_is_purely_additive(name, pairs):
    """Removing every data-key attribute gives the v1.1 markup byte for byte (sha recorded before v1.2)."""
    py, _ = pairs[name]
    assert hashlib.sha256(KEY.sub("", py).encode()).hexdigest() == BASE[name]
