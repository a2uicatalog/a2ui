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
    # onClick / onChange / onToggle each own a branch of the output-wire
    # dispatch. A branch may contain MORE than one querySelector: onChange
    # gained a group path in 2026-08 (see GROUP_SELECTORS below), so read every
    # selector in the branch rather than only the first, in source order.
    for prop in ("onClick", "onChange", "onToggle"):
        m = re.search(
            r"prop === '%s'\)\s*\{(.*?)\n      \} else if \(prop ===" % prop,
            src, re.S,
        )
        if not m:
            continue
        sels = re.findall(r"domEl\.querySelector\('([^']+)'\)", m.group(1))
        if sels:
            out[prop] = sels
    assert "onClick" in out and "onChange" in out, (
        "could not read the binder's selectors out of A2UIState.html -- the "
        "dispatch shape changed; update this parser rather than hardcoding."
    )
    return out


# Selectors whose match means the binder DELEGATES over the container instead
# of attaching to one element. Read as: "if this matches, N elements are one
# control and finding N of them is correct, not a bug."
#
# Everything not listed here binds a SINGLE element via querySelector, which is
# why _unbound treats a multi-match as a failure. That distinction is the whole
# point of this pair of rules -- see test_a_radio_group_bound_one_at_a_time.
GROUP_SELECTORS = frozenset({"input[type=radio]"})


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


def _count(segment, selector):
    """How many elements a selector would match in this markup.

    Approximate, and only over the shapes the binder actually uses: a
    comma-separated list of tag names, optionally with :not([type=checkbox]) or
    a [type=x] filter.

    Counts rather than returns a bool because "how many" is the question that
    matters: querySelector takes the FIRST, so two matches and one match are
    different outcomes for the same wire.
    """
    n = 0
    for part in selector.split(","):
        part = part.strip()
        neg = ":not([type=checkbox])" in part
        want = re.search(r"\[type=(\w+)\]", part.split(":not")[0])
        tag = re.split(r"[:\[]", part)[0].strip()
        for m in re.finditer(r"<%s\b([^>]*)>" % tag, segment):
            attrs = m.group(1)
            typ = re.search(r'type=["\']?(\w+)', attrs)
            typ = typ.group(1) if typ else None
            if neg and typ == "checkbox":
                continue
            if want and typ != want.group(1):
                continue
            n += 1
    return n


def _unbound(payload, html, selectors):
    bad = []
    for el in payload.get("layout") or []:
        wire = el.get("wire") or {}
        if not el.get("id"):
            continue
        seg = _segment_for(html, el["id"])
        for prop in wire:
            sels = selectors.get(prop)
            if not sels:
                continue          # a wire prop this test cannot check yet
            if seg is None:
                bad.append(f"{el['id']} ({el.get('atom')}) .{prop} "
                           f"-> element never rendered")
                continue
            # Source order matters: the binder takes the first branch that
            # matches, exactly as the dispatch does.
            for sel in sels:
                n = _count(seg, sel)
                if not n:
                    continue
                if sel in GROUP_SELECTORS:
                    break         # delegated over the container: N is fine
                if n > 1:
                    # The silent one. The control renders, the selector
                    # matches, and the binder still only ever hears the first
                    # of them -- which is how form_radio_group shipped
                    # bindable-looking and dead until 2026-08-14.
                    bad.append(
                        f"{el['id']} ({el.get('atom')}) .{prop} -> {n} elements "
                        f"match {sel!r} but the binder attaches to the first "
                        f"only; this control needs a delegated branch in "
                        f"A2UIState.html (and an entry in GROUP_SELECTORS)")
                break
            else:
                bad.append(f"{el['id']} ({el.get('atom')}) .{prop} "
                           f"-> no element matching any of {sels!r}")
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


def test_a_radio_group_binds_as_one_control(render_wired, binder_selectors):
    """form_radio_group + onChange, the fourth cause this file exists for.

    Until 2026-08-14 the atom rendered N perfectly good radios and the binder
    did querySelector('input:not([type=checkbox]),...') -- which MATCHES a
    radio. So the wire looked bound, this test would have passed it, and the
    surface reported only the first option's value no matter what you picked.

    That is why _unbound counts instead of asking yes/no: the failure was never
    "nothing matched", it was "N matched and only one was wired".
    """
    payload = {
        "type": "a2ui_wired_surface", "title": "radio probe",
        "app": {"id": "probe"},
        "state_primitives": [{"id": "v", "primitive": "ValueStore",
                              "props": {"initialValue": ""}}],
        "actions": [],
        "layout": [
            {"id": "sev", "atom": "form_radio_group",
             "props": {"label": "severity",
                       "options": [{"label": "low", "value": "low"},
                                   {"label": "high", "value": "high"}]},
             "wire": {"onChange": "#v.setValue"}},
        ],
    }
    html = render_wired(payload)
    seg = _segment_for(html, "sev")
    assert seg and _count(seg, "input[type=radio]") == 2, (
        "the atom must render one input per option -- otherwise this test is "
        "proving nothing about the group case")
    assert not _unbound(payload, html, binder_selectors)


def test_the_group_rule_is_what_makes_it_pass(render_wired, binder_selectors):
    """The negative control for the rule above, not for the binder.

    Drop the delegated branch from what the test believes the binder does, and
    the radio group must go straight back to being reported as broken. Without
    this, GROUP_SELECTORS could silently grow into a list that excuses every
    multi-match and the count rule would be decoration.
    """
    payload = {
        "type": "a2ui_wired_surface", "title": "radio probe",
        "app": {"id": "probe"},
        "state_primitives": [{"id": "v", "primitive": "ValueStore",
                              "props": {"initialValue": ""}}],
        "actions": [],
        "layout": [
            {"id": "sev", "atom": "form_radio_group",
             "props": {"label": "severity",
                       "options": [{"label": "low", "value": "low"},
                                   {"label": "high", "value": "high"}]},
             "wire": {"onChange": "#v.setValue"}},
        ],
    }
    without_group = {k: [s for s in v if s not in GROUP_SELECTORS]
                     for k, v in binder_selectors.items()}
    bad = _unbound(payload, render_wired(payload), without_group)
    assert bad and "binder attaches to the first only" in bad[0], (
        "a radio group must be reported as mis-bound the moment the delegated "
        "branch is not there. Got: %r" % (bad,))


def test_photo_upload_reads_its_subject_at_upload_time(render_wired):
    """`subject_id` is an INPUT wire onto an attribute, not a variable.

    The record a photo attaches to is normally created by the action
    immediately before the atom becomes visible — the confirmation-block
    pattern — so the value arrives AFTER this markup was written. Baking it
    into the inline script at render time would capture the empty string
    forever and every upload would refuse with "nothing to attach this photo
    to yet", which looks like a broken control rather than a stale read.
    """
    payload = {
        "type": "a2ui_wired_surface", "title": "photo probe",
        "app": {"id": "probe"},
        "state_primitives": [],
        "actions": [{"id": "act", "type": "mcp:get_profile", "props": {}}],
        "layout": [
            {"id": "shot", "atom": "photo_upload",
             "props": {"label": "Add a photo", "endpoint": "/photo/upload"},
             "wire": {"subject_id": "#act.id"}},
        ],
    }
    html = render_wired(payload)
    seg = _segment_for(html, "shot")
    assert seg, "photo_upload must render"
    # Camera AND library on mobile: `image/*` alone is what offers both.
    assert 'accept="image/*"' in seg
    # `capture` forces the camera and drops the library, so it must be opt-in.
    assert "capture=" not in seg
    # Read through the attribute the bridge writes, not a render-time constant.
    assert 'getAttribute("data-subject-id")' in seg


def test_the_bridge_can_deliver_subject_id(binder_selectors):
    """The input-wire half. Without this branch the wire above is accepted,
    resolves, and silently sets nothing — the renderer's oldest failure mode."""
    src = STATE.read_text()
    assert "prop === 'subject_id'" in src, (
        "photo_upload's subject_id wire needs a setProp branch in "
        "A2UIState.html, or the value never reaches the atom")


def test_a_gate_frames_real_buttons_rather_than_owning_them(render_wired):
    """gate_open/gate_close is FLAT, and that is the design, not a convention.

    The alternative was one atom holding both buttons. It renders identically
    and costs the engine two permanent wire props, because one element with two
    buttons makes querySelector('button') ambiguous — a problem that exists
    only because the buttons were grouped. Built that way on 2026-08-14 and
    replaced the same day.

    Flat means each button stays a top-level layout element and binds through
    the ordinary onClick every other button uses, which is the same reason
    row_open is flat: a container would take its contents out of the layout the
    binder walks.
    """
    payload = {
        "type": "a2ui_wired_surface", "title": "gate probe",
        "app": {"id": "probe"},
        "state_primitives": [],
        "actions": [{"id": "act", "type": "mcp:get_profile", "props": {}}],
        "layout": [
            {"atom": "gate_open",
             "props": {"prompt": "Delete it?", "tone": "danger",
                       "decision_id": "park-123"}},
            {"id": "yes", "atom": "ripple_button", "props": {"label": "Yes"},
             "wire": {"onClick": "#act.run"}},
            {"id": "no", "atom": "ripple_button", "props": {"label": "Cancel"},
             "wire": {"onClick": "#act.run"}},
            {"atom": "gate_close"},
        ],
    }
    html = render_wired(payload)
    assert 'data-decision-id="park-123"' in html, (
        "the decision must be named on the frame — a confirmation that cannot "
        "say what it confirms is not one")

    # Each button binds on its own, through the standard contract.
    for el in ("yes", "no"):
        seg = _segment_for(html, el)
        assert seg and _count(seg, "button") == 1, (
            f"{el} must be its own singly-bindable element")
    assert not _unbound(payload, html, {"onClick": ["button"]})

    # And the engine gained nothing permanent for it.
    src = STATE.read_text()
    for gone in ("onConfirm", "onCancel"):
        assert gone not in src, (
            f"{gone} is back in the engine — the flat gate exists so the wire "
            "vocabulary does not grow for a layout decision")


