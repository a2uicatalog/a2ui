"""Every wire in a wired surface must bind to a control that actually exists.

DECLARED 2026-08-03, after shipping a workspace in which all nine wires were
dead and reporting it verified. Three independent causes, none of which any
existing test could see:

  1. cta_button renders <a href="#">, but the binder attaches onClick via
     querySelector('button') -> null -> no listener. Buttons were decoration.
  2. setValue is an INPUT wire (state -> DOM). Reading a control back into
     state is onChange, so six fields were write-only.
  3. <select> matched neither 'input' nor 'textarea' in the onChange selector,
     so every dropdown on every wired surface bound nothing.

The check that let it through asserted every wire REFERENCED a declared node.
That is a strictly weaker claim than "the control exists and binds", and it
cannot fail for the reason that matters -- it reported 0 dangling wires while
nothing on the surface worked.

So this test does not invent its own notion of correctness. It reads the
SELECTORS OUT OF THE BINDER ITSELF (A2UIState.html) and applies them to the
rendered HTML, which means the day someone teaches the binder a new control
this test learns it too, and the day an atom stops rendering a bindable
control this fails instead of the user finding out by clicking.
"""
import json
import re
import subprocess
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
BUNDLE = ROOT / "public" / "surfaces" / "mcp-apps" / "renderer-bundle.html"
STATE = ROOT / "apps-script-surface" / "gas-wired-renderer" / "A2UIState.html"
REFERENCE_PAYLOADS = sorted((ROOT / "mcp" / "data").glob("*demo*.json"))


@pytest.fixture(scope="module")
def binder_selectors():
    """The selectors the LIVE binder uses, parsed from its source.

    Deliberately extracted rather than restated: a copy here would drift, and a
    drifted copy in a test is worse than no test -- it would keep passing while
    describing a binder that no longer exists.
    """
    src = STATE.read_text()
    out = {}
    # onClick / onChange / onToggle each do `domEl.querySelector('...')` inside
    # their own branch of the output-wire dispatch.
    for prop in ("onClick", "onChange", "onToggle"):
        m = re.search(
            r"prop === '%s'\)\s*\{\s*var \w+ = domEl\.querySelector\('([^']+)'\)" % prop,
            src,
        )
        if m:
            out[prop] = m.group(1)
    assert "onClick" in out and "onChange" in out, (
        "could not read the binder's selectors out of A2UIState.html -- the "
        "dispatch shape changed; update this parser rather than hardcoding."
    )
    return out


@pytest.fixture(scope="module")
def render_wired():
    """Render a wired payload through the real bundle and return its HTML."""
    raw = BUNDLE.read_text()
    blocks = re.findall(r"<script>\n(.*?)\n</script>", raw, re.S)
    core = [b for b in blocks if "a2ui-core" in b[:300]][0]
    partial = [b for b in blocks if "_a2uiRenderWiredLayout" in b][0]

    def _render(payload):
        with tempfile.TemporaryDirectory() as td:
            pj = Path(td) / "p.json"
            pj.write_text(json.dumps(payload))
            drv = Path(td) / "d.js"
            drv.write_text(
                "global.window = global;\nglobal.document = undefined;\n"
                + core + "\n" + partial + f"""
var fs = require('fs');
var p = JSON.parse(fs.readFileSync({json.dumps(str(pj))}, 'utf8'));
process.stdout.write(_a2uiRenderWiredLayout(p));
"""
            )
            r = subprocess.run(["node", str(drv)], capture_output=True,
                               text=True, timeout=120)
            assert r.returncode == 0, r.stderr[-2000:]
            return r.stdout

    return _render


def _segment_for(html, el_id):
    """The markup the binder would see for one element.

    Mirrors getElementById('a2ui-' + id): everything from that id up to the
    next one. Returns None when the element never rendered at all, which is
    itself a binding failure -- the binder would get null.
    """
    m = re.search(r'id="a2ui-%s"([\s\S]*?)(?=id="a2ui-|$)' % re.escape(el_id), html)
    return m.group(1) if m else None


def _matches(segment, selector):
    """Approximate a CSS selector against raw markup.

    Only the shapes the binder actually uses: a comma-separated list of tag
    names, optionally with :not([type=checkbox]).
    """
    for part in selector.split(","):
        part = part.strip()
        neg = ":not([type=checkbox])" in part
        tag = part.split(":")[0].strip()
        if neg:
            for m in re.finditer(r"<%s\b([^>]*)>" % tag, segment):
                if 'type="checkbox"' not in m.group(1) and "type=checkbox" not in m.group(1):
                    return True
        elif re.search(r"<%s\b" % tag, segment):
            return True
    return False


def _unbound(payload, html, selectors):
    bad = []
    for el in payload.get("layout") or []:
        wire = el.get("wire") or {}
        if not el.get("id"):
            continue
        seg = _segment_for(html, el["id"])
        for prop in wire:
            sel = selectors.get(prop)
            if sel is None:
                continue          # a wire prop this test cannot check yet
            if seg is None or not _matches(seg, sel):
                bad.append(f"{el['id']} ({el.get('atom')}) .{prop} "
                           f"-> no element matching {sel!r}")
    return bad


@pytest.mark.parametrize("path", REFERENCE_PAYLOADS,
                         ids=[p.stem for p in REFERENCE_PAYLOADS])
def test_reference_payload_wires_all_bind(path, render_wired, binder_selectors):
    """Every shipped reference wired payload must be fully live."""
    payload = json.loads(path.read_text())
    if payload.get("type") != "a2ui_wired_surface":
        pytest.skip(f"{path.name} is not a wired surface")
    bad = _unbound(payload, render_wired(payload), binder_selectors)
    assert not bad, (
        "wires that bind to nothing (the control renders, but not as something "
        "the binder can attach to):\n  " + "\n  ".join(bad)
    )


def test_the_check_can_actually_fail(render_wired, binder_selectors):
    """A gate that cannot fail is worth nothing.

    Reproduces the exact shipped bug: cta_button renders <a href="#">, so an
    onClick wire on it finds no <button>. If this ever passes, the test above
    has stopped testing anything.
    """
    broken = {
        "type": "a2ui_wired_surface", "title": "regression probe",
        "app": {"id": "probe"},
        "state_primitives": [],
        "actions": [{"id": "act", "type": "mcp:get_profile", "props": {}}],
        "layout": [{"id": "btn", "atom": "cta_button",
                    "props": {"label": "inert"},
                    "wire": {"onClick": "#act.run"}}],
    }
    bad = _unbound(broken, render_wired(broken), binder_selectors)
    assert bad, ("cta_button + onClick must be reported as unbound -- it "
                 "renders an anchor, not a button. This test failing means the "
                 "detector stopped detecting.")


def test_a_correctly_wired_surface_passes(render_wired, binder_selectors):
    """The positive control: ripple_button + onClick, form_select + onChange."""
    good = {
        "type": "a2ui_wired_surface", "title": "positive control",
        "app": {"id": "probe"},
        "state_primitives": [{"id": "v", "primitive": "ValueStore",
                              "props": {"initialValue": ""}}],
        "actions": [{"id": "act", "type": "mcp:get_profile", "props": {}}],
        "layout": [
            {"id": "btn", "atom": "ripple_button", "props": {"label": "go"},
             "wire": {"onClick": "#act.run"}},
            {"id": "sel", "atom": "form_select",
             "props": {"label": "pick", "options": [{"label": "a", "value": "a"}]},
             "wire": {"onChange": "#v.setValue"}},
            {"id": "txt", "atom": "form_input", "props": {"label": "type"},
             "wire": {"onChange": "#v.setValue"}},
        ],
    }
    bad = _unbound(good, render_wired(good), binder_selectors)
    assert not bad, "these are the atoms the wired dialect documents: " + str(bad)
