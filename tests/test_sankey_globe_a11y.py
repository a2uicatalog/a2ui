"""I1 (sankey_flow cycle data-loss) and I2 (globe_3d WCAG 1.1.1 text alternative) regression
tests, 2026-10-20.

sankey_flow's web (Python) renderer draws a strict two-column layout: every node is placed in
the LEFT (source) column or the RIGHT (target) column, never both. A link whose target is ALSO
a source elsewhere -- the two-column shape of a cycle, e.g. A -> B -> A -- used to just vanish:
`continue`d past with no note, no error, nothing. Fixed so those links are collected and surfaced
as a visible note (the numbers in that note are the only proof the data survived the render).

globe_3d renders a bare <canvas> with pins (`dots`) and great-circle `arcs` that only ever
existed as pixels -- nothing conveyed them as text (WCAG 1.1.1). Both renderers (web/Python,
Apps Script/gas-wired-renderer) now emit a visually-hidden list of the pins and arcs alongside
the pre-existing role="img" aria-label.

sankey_flow's Apps Script twin (atoms_charts.gs) renders a grouped bar-list keyed by source, not
a two-column layout, so it never had the cycle bug in the first place -- confirmed below rather
than assumed, as the control for this change.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from test_motion_atoms import _node, core_js  # noqa: F401  (core_js is a fixture)
from renderers import web_article as wa

ATTACK = '"><img src=x onerror=alert(1)><script>alert(2)</script>'


def _gas_render(core_js, block):
    return _node(core_js, "var B = " + json.dumps([block]) +
                 "; console.log(JSON.stringify(B.map(function(b){ return renderAtoms([b], {}); })));")[0]


CYCLIC_SANKEY = {
    "type": "sankey_flow", "title": "Cyclic",
    "nodes": [{"id": "a", "label": "Alpha"}, {"id": "b", "label": "Beta"}],
    "links": [{"source": "a", "target": "b", "value": 5}, {"source": "b", "target": "a", "value": 0.3}],
}


def test_web_cyclic_sankey_links_are_noted_not_silently_dropped():
    html = wa._RENDERERS["sankey_flow"](dict(CYCLIC_SANKEY))
    # the two link VALUES are the proof: the old code dropped both links with no trace anywhere
    # the note itself must list each undrawn link with its real value (0.3 must not round to 0)
    assert "<li>Alpha → Beta: 5</li>" in html, "A -> B (value 5) vanished with no record"
    assert "<li>Beta → Alpha: 0.3</li>" in html, "B -> A (value 0.3) vanished or was rounded"
    assert "Alpha" in html and "Beta" in html
    assert "not shown" in html.lower()  # a clear, visible note -- not a silent drop


def test_web_sankey_note_escapes_hostile_node_labels():
    b = dict(CYCLIC_SANKEY)
    b["nodes"] = [{"id": "a", "label": ATTACK}, {"id": "b", "label": "Beta"}]
    html = wa._RENDERERS["sankey_flow"](dict(b))
    assert "<img" not in html and "<script>alert" not in html
    assert "&lt;img" in html


def test_gas_sankey_flow_already_lists_both_directions_of_a_cycle(core_js):
    """Control: atoms_charts.gs groups links by source (a bar list, not two columns), so a
    cycle was never dropped there. This change does not need to (and does not) touch it."""
    html = _gas_render(core_js, CYCLIC_SANKEY)
    assert "5" in html and "0.3" in html
    assert "Alpha" in html and "Beta" in html


GLOBE_WITH_PINS = {
    "type": "globe_3d", "size": 200,
    "dots": [{"lat": 48.85, "lon": 2.35, "label": ATTACK}, {"lat": 40.7, "lon": -74.0}],
    "arcs": [{"from": [48.85, 2.35], "to": [40.7, -74.0]}],
}


def test_web_globe_has_accessible_name_and_text_alternative():
    html = wa._RENDERERS["globe_3d"](dict(GLOBE_WITH_PINS))
    assert 'role="img"' in html and 'aria-label="Rotating 3D globe"' in html
    assert "Pin 2" in html            # the unlabelled second pin gets a usable fallback name
    assert "48.85" in html and "2.35" in html and "40.7" in html and "-74" in html
    assert "Arc 1" in html


def test_web_globe_escapes_a_hostile_pin_label():
    html = wa._RENDERERS["globe_3d"](dict(GLOBE_WITH_PINS))
    assert "<img" not in html and "<script>alert" not in html
    assert "&lt;img" in html


def test_gas_globe_has_accessible_name_and_text_alternative(core_js):
    html = _gas_render(core_js, GLOBE_WITH_PINS)
    assert 'role="img"' in html and 'aria-label="Rotating 3D globe"' in html
    assert "Pin 2" in html
    assert "48.85" in html and "40.7" in html
    assert "Arc 1" in html


def test_gas_globe_escapes_a_hostile_pin_label(core_js):
    html = _gas_render(core_js, GLOBE_WITH_PINS)
    assert "<img" not in html and "<script>alert" not in html
    assert "&lt;img" in html
