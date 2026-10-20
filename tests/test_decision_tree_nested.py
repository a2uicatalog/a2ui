"""decision_tree: the documented payload (atoms/schema.yaml: nodes = array of {text, children: [{text, children}]})
must render in the Python web renderer. It used to raise KeyError 'id' (the renderer only knew an id/next graph)."""
from __future__ import annotations

from test_motion_atoms import _py  # noqa: F401
from test_motion_atoms import wa  # noqa: F401

NESTED = {"type": "decision_tree", "title": "Should we ship?",
          "nodes": [{"text": "Tests pass?", "children": [{"text": "Yes: ship"},
                                                         {"text": "No: fix first", "children": [{"text": "Re-run <b>CI</b>"}]}]}]}

GRAPH = {"type": "decision_tree", "title": "Graph form",
         "nodes": [{"id": "a", "label": "Start", "type": "question", "children": [{"label": "go", "next": "b"}]},
                   {"id": "b", "label": "End", "type": "leaf"}]}


def test_documented_nested_payload_renders_every_node_text():
    html = _py(NESTED)
    for t in ("Should we ship?", "Tests pass?", "Yes: ship", "No: fix first"):
        assert t in html


def test_nested_text_is_escaped():
    html = _py(NESTED)
    assert "<b>CI</b>" not in html and "&lt;b&gt;CI&lt;/b&gt;" in html


def test_nested_branches_are_collapsible_like_the_gas_twin():
    assert "<details" in _py(NESTED)


def test_id_graph_form_still_renders():
    html = _py(GRAPH)
    assert "Start" in html and "End" in html
