"""RFC 6902 JSON Patch, conformant, in both twins (I75): the RFC's own Appendix A examples and its section 4 rules.

motion_transition's "patch" field applies it: B is A with the patch applied, and the ops give provenance (a copy grows out of
its source). Python (_jp_apply) and the GAS twin must give the same result or the same rejection on every case; a rejected
patch never half-applies. A member replaced in place keeps its position (renderers draw fields in member order).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))
import renderers.web_article as wa  # noqa: E402
from test_motion_atoms import _node_raw, core_js  # noqa: E402,F401

CASES = json.loads((Path(__file__).parent / "fixtures" / "rfc6902_cases.json").read_text())["cases"]


def _py(c):
    try:
        out = wa._jp_apply(c["doc"], c["patch"])
    except wa._JpError:
        return "error"
    return out


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_python_matches_the_rfc(case):
    before = json.dumps(case["doc"])
    got = _py(case)
    assert got == case["expected"], (got, case["expected"])
    if case["id"] == "replace-keeps-member-order":   # JSON objects are unordered, but renderers draw fields in member order
        assert list(got) == list(case["expected"])
    assert json.dumps(case["doc"]) == before, "the input document is never changed"


@pytest.fixture(scope="module")
def gas(core_js):
    body = ("var C = %s; console.log(JSON.stringify(C.map(function(c){ try { return _jpApply(c.doc, c.patch); } "
            "catch (e) { return e && e.name === 'JpError' ? 'error' : 'CRASH ' + e; } })));" % json.dumps(CASES))
    return dict(zip([c["id"] for c in CASES], _node_raw(core_js, body)))


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_gas_matches_the_rfc(case, gas):
    assert gas[case["id"]] == case["expected"], (gas[case["id"]], case["expected"])
    if case["id"] == "replace-keeps-member-order":
        assert list(gas[case["id"]]) == list(case["expected"])


PROV = {"type": "org_chart", "nodes": [{"id": "curtis", "label": "Curtis", "parent_id": ""}, {"id": "curtis/opus", "label": "Opus", "parent_id": "curtis"},
                                        {"id": "curtis/sonnet", "label": "Sonnet", "parent_id": "curtis"}]}
PROV_OPS = [{"op": "copy", "from": "/nodes/1", "path": "/nodes/-"}, {"op": "replace", "path": "/nodes/3/id", "value": "curtis/opus2"},
            {"op": "move", "from": "/nodes/2", "path": "/nodes/1"}, {"op": "replace", "path": "/nodes/0", "value": {"id": "owner", "label": "Owner", "parent_id": ""}},
            {"op": "add", "path": "/nodes/-", "value": {"id": "curtis/pm", "label": "PM", "parent_id": "curtis"}}]


def test_provenance_from_the_ops():
    after, rel = wa._mtr_from_patch(PROV, PROV_OPS)
    assert [n["id"] for n in after["nodes"]] == ["owner", "curtis/sonnet", "curtis/opus", "curtis/opus2", "curtis/pm"]
    assert rel == {"curtis/opus2": ["curtis/opus"], "owner": ["curtis"]}   # a copy given a new id; an item replaced whole
    # a moved item keeps its key (no entry); an added one has no source (the path rule lets it grow out of its parent)


def test_python_and_gas_derive_the_same_provenance(core_js):
    body = "console.log(JSON.stringify([_mtrFromPatch(%s, %s)]))" % (json.dumps(PROV), json.dumps(PROV_OPS))
    after, rel = _node_raw(core_js, body)[0]
    assert (after, rel) == tuple(json.loads(json.dumps(wa._mtr_from_patch(PROV, PROV_OPS))))
