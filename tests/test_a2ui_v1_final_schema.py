"""Emitter output vs the FINAL A2UI v1.0 schemas (tests/fixtures/a2ui_v1_0_spec, vendored from upstream).

Samples every second atom of scripts/build_web_preview.DEMO (sorted; ~95 atoms with real example props) and
validates the emitted createSurface twice: (a) default emit with the repo's permissive extension branch
(basic components strictly checked, extension components waved through) and (b) degraded to a Basic-only
renderer against the STRICT validator (no extension branch: every component must be a real basic one)."""
import copy
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from renderers.a2ui_v1 import emit_surface, emit_messages, call_renderer_function  # noqa: E402
from renderers.a2ui_v1_wired import emit_wired_surface  # noqa: E402
from renderers.a2ui_capabilities import ClientCapabilities, BASIC_CATALOG_IDS  # noqa: E402
from tests.a2ui_v1_conformance import AGENT_TO_RENDERER, AGENT_TO_RENDERER_STRICT, assert_conforms  # noqa: E402

BASIC_CAPS = ClientCapabilities(version="1.0", supported_catalog_ids=(BASIC_CATALOG_IDS["1.0"],))


def _sample():
    import build_web_preview as b
    keys = sorted(b.DEMO)[::2]
    return [(k, {"title": k, "blocks": [dict(b.DEMO[k], type=k)]}) for k in keys]


SAMPLE = _sample()


def _walk(o):
    if isinstance(o, dict):
        yield o
        for v in o.values():
            yield from _walk(v)
    elif isinstance(o, list):
        for v in o:
            yield from _walk(v)


def test_sample_size():
    assert len(SAMPLE) >= 90


def test_default_emit_validates_for_the_atom_sample():
    bad = {}
    for k, payload in SAMPLE:
        errs = [e.message[:120] for e in AGENT_TO_RENDERER.iter_errors(emit_surface(copy.deepcopy(payload)))]
        if errs:
            bad[k] = errs[:1]
    assert not bad, bad


def test_basic_only_emit_validates_strictly_for_the_atom_sample():
    bad = {}
    for k, payload in SAMPLE:
        m = emit_surface(copy.deepcopy(payload), capabilities=BASIC_CAPS)
        errs = [e.message[:120] for e in AGENT_TO_RENDERER_STRICT.iter_errors(m)]
        if errs:
            bad[k] = errs[:1]
    assert not bad, bad


def test_no_unprefixed_binding_or_call_is_emitted_in_1_0():
    """DataBinding/FunctionCall positions carry '@'; ChildList templates keep plain 'path'."""
    from renderers.a2ui_v1_wired import emit_wired_surface
    d = json.load(open(os.path.join(ROOT, "payloads", "expenses-demo.json")))
    cs = emit_wired_surface(d)["createSurface"]
    assert_conforms({"version": "1.0", "createSurface": cs}, AGENT_TO_RENDERER)
    sole_path = [o for o in _walk(cs["components"]) if set(o) == {"path"}]
    assert sole_path == [], "a bare {path} binding leaked into a 1.0 message"
    assert any("@path" in o for o in _walk(cs["components"]))
    assert any(set(o) == {"componentId", "path"} for o in _walk(cs["components"]))   # template stays unprefixed


def test_wired_has_no_surface_properties_and_closed_action_event():
    d = json.load(open(os.path.join(ROOT, "payloads", "expenses-demo.json")))
    cs = emit_wired_surface(d)["createSurface"]
    assert "surfaceProperties" not in cs and "theme" not in cs
    for o in _walk(cs["components"]):
        ev = o.get("event") if isinstance(o, dict) else None
        if isinstance(ev, dict):
            assert set(ev) <= {"name", "userMessage", "context"}, ev
    assert "a2uicatalog_wired" in cs["metadata"]["extensions"]


def test_v09_downgrade_maps_back_only_at_binding_positions():
    payload = {"title": "t", "blocks": [{"type": "form", "title": "F", "fields": [{"name": "a", "type": "text", "label": "A"}]}]}
    msgs = emit_messages(payload, ClientCapabilities(version="v0.9", supported_catalog_ids=(BASIC_CATALOG_IDS["v0.9"],)))
    assert all(m["version"] == "v0.9" for m in msgs)
    objs = [o for m in msgs for o in _walk(m)]
    assert not any("@path" in o or "@call" in o for o in objs)
    assert any(set(o) == {"path"} for o in objs)


def test_call_renderer_function_uses_at_call():
    m = call_renderer_function(BASIC_CATALOG_IDS["1.0"], "openUrl", {"url": "https://example.com"}, "c1")
    assert m["callRendererFunction"]["callFunction"]["@call"] == "openUrl"
    assert "call" not in m["callRendererFunction"]["callFunction"]


def test_modal_is_trigger_and_content():
    m = emit_surface({"title": "m", "blocks": [{"type": "modal", "title": "Details", "blocks": [{"type": "body", "text": "x"}]}]})
    assert_conforms(m, AGENT_TO_RENDERER_STRICT)
    modal = [c for c in m["createSurface"]["components"] if c["component"] == "Modal"][0]
    assert set(modal) == {"id", "component", "trigger", "content"}
