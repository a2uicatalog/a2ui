"""Proves tests/a2ui_v1_conformance.py's validator itself is correct — using
synthetic fixtures, not this repo's real emitters. renderers/a2ui_v1.py's
CURRENT output is known, confirmed (2026-08-24, by running it through this
exact validator), to NOT conform — it targets an earlier A2UI draft (see
a2ui-private/a2uithoughts.md's 2026-08-23/24 entries). Fixing that is
separate, sequenced work — asserting real conformance against the CURRENT
emitter here would land this file red on main, which this repo's own
CLAUDE.md forbids ("pytest tests/ -q before any push"). This file is the
safety net the fix gets verified against, not the fix itself.
"""
from __future__ import annotations

import pytest

from tests.a2ui_v1_conformance import AGENT_TO_RENDERER, RENDERER_TO_AGENT, assert_conforms


def test_a_minimal_real_createsurface_conforms():
    """Ground truth: a message shaped exactly per the real spec must pass —
    proves the registry/$ref resolution chain works at all before any test
    relies on it to catch a REAL problem."""
    assert_conforms({
        "version": "v1.0",
        "createSurface": {
            "surfaceId": "s1",
            "components": [{"id": "root", "component": "Text", "text": "hi"}],
        },
    }, AGENT_TO_RENDERER)


def test_surfaceproperties_is_rejected():
    """The exact real bug found 2026-08-23/24: renderers/a2ui_v1.py emits a
    `surfaceProperties` key that does not exist in the real schema. Confirms
    the validator actually catches it, not just theoretically would."""
    with pytest.raises(AssertionError):
        assert_conforms({
            "version": "v1.0",
            "createSurface": {
                "surfaceId": "s1",
                "components": [{"id": "root", "component": "Text", "text": "hi"}],
                "surfaceProperties": {"title": "x"},
            },
        }, AGENT_TO_RENDERER)


def test_updatecomponents_conforms():
    assert_conforms({
        "version": "v1.0",
        "updateComponents": {"surfaceId": "s1",
                             "components": [{"id": "a", "component": "Text", "text": "hi"}]},
    }, AGENT_TO_RENDERER)


def test_updatedatamodel_conforms():
    assert_conforms({
        "version": "v1.0",
        "updateDataModel": {"surfaceId": "s1", "path": "/count", "value": 5},
    }, AGENT_TO_RENDERER)


def test_deletesurface_conforms():
    assert_conforms({"version": "v1.0", "deleteSurface": {"surfaceId": "s1"}}, AGENT_TO_RENDERER)


def test_callrendererfunction_conforms():
    """FunctionCall.call/args are validated against a real oneOf of the
    basic catalog's actual functions (catalog.json's own `anyFunction`) --
    an invented function name would fail for a DIFFERENT reason than the
    one this test is about, so this uses openUrl, a real basic-catalog
    function, confirmed by reading catalog.json directly (its own `call`
    field is a `const: "openUrl"`, `args.url` required)."""
    assert_conforms({
        "version": "v1.0",
        "callRendererFunction": {
            "functionCallId": "call-1",
            "callFunction": {"catalogId": "https://a2ui.org/specification/v1_0/catalog.json",
                             "call": "openUrl", "args": {"url": "https://example.com"}},
        },
    }, AGENT_TO_RENDERER)


def test_actionresponse_is_not_a_real_message_type():
    """The real spec has NO 'actionResponse' message at all (confirmed
    2026-08-24 by reading renderer_to_agent.json directly) — `action` is
    one-way, renderer->agent only. renderers/a2ui_v1.py's action_response()
    invents a message shape the protocol doesn't define. This test locks
    that finding so it can't silently regress back into "assumed real"."""
    with pytest.raises(AssertionError):
        assert_conforms({
            "version": "v1.0", "actionId": "a1",
            "actionResponse": {"value": {"ok": True}},
        }, AGENT_TO_RENDERER)


def test_action_conforms_on_the_renderer_to_agent_side():
    assert_conforms({
        "version": "v1.0",
        "action": {"name": "submit", "surfaceId": "s1", "sourceComponentId": "btn-1",
                   "timestamp": "2026-08-24T00:00:00Z", "context": {}},
    }, RENDERER_TO_AGENT)


def test_wantresponse_is_not_a_real_field():
    """renderers/a2ui_v1.py's call_function() emits a top-level `wantResponse`
    key on the callFunction envelope -- not a real field on either direction's
    schema (confirmed by reading both agent_to_renderer.json's
    CallRendererFunctionMessage and renderer_to_agent.json's
    callAgentFunction -- neither declares it, and both are additionalProperties
    false at the message-object level via their enclosing oneOf)."""
    with pytest.raises(AssertionError):
        assert_conforms({
            "version": "v1.0", "wantResponse": True,
            "callRendererFunction": {
                "functionCallId": "call-1",
                "callFunction": {"catalogId": "https://a2ui.org/specification/v1_0/catalog.json",
                                 "call": "openUrl", "args": {"url": "https://example.com"}},
            },
        }, AGENT_TO_RENDERER)
