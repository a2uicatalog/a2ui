"""a2a_counterpart/agui_adapter.py -- real messages in, exact AG-UI event
sequences out. No server, no browser -- matches this repo's existing
pytest-everything discipline. Uses the SAME messages
tests/test_a2a_counterpart.py's composition test already exercises.
"""
from __future__ import annotations

from a2a_counterpart.agui_adapter import adapt_to_agui_events
from renderers.a2ui_v1 import emit_surface
from renderers.a2ui_v1_updates import delete_surface, update_components, update_data_model


def test_create_surface_emits_run_started_and_step_started():
    surface = emit_surface({"title": "T", "blocks": [{"type": "body", "text": "hi"}]},
                           surface_id="s1")
    events = adapt_to_agui_events("ctx1", "s1", surface, surface_already_started=False)

    assert events == [
        {"type": "RunStarted", "payload": {"runId": "ctx1"}},
        {"type": "StepStarted", "payload": {"runId": "ctx1", "stepId": "s1"}},
    ]


def test_create_surface_is_a_noop_when_already_started():
    """A second createSurface for the same (context, surface) -- e.g. a
    replay or a redundant message -- must not re-fire RunStarted, which
    would confuse live_step_tracker's own state machine."""
    surface = emit_surface({"title": "T", "blocks": [{"type": "body", "text": "hi"}]},
                           surface_id="s1")
    events = adapt_to_agui_events("ctx1", "s1", surface, surface_already_started=True)
    assert events == []


def test_update_components_emits_tool_call_pair_per_component():
    msg = update_components("s1", [
        {"id": "flights_card", "component": "Text", "text": "on time"},
        {"id": "weather_card", "component": "Text", "text": "sunny"},
    ])
    events = adapt_to_agui_events("ctx1", "s1", msg, surface_already_started=True)

    assert len(events) == 4
    assert [e["type"] for e in events] == [
        "ToolCallStart", "ToolCallResult", "ToolCallStart", "ToolCallResult"]
    assert events[0]["payload"]["toolName"] == "flights_card"
    assert events[2]["payload"]["toolName"] == "weather_card"
    # Same component -> same toolCallId, across the pair.
    assert events[0]["payload"]["toolCallId"] == events[1]["payload"]["toolCallId"]
    assert events[0]["payload"]["toolCallId"] != events[2]["payload"]["toolCallId"]


def test_update_components_toolcallid_is_stable_across_separate_calls():
    """A LATER updateComponents touching the SAME component id must map to
    the SAME toolCallId -- agent_run_sketch node identity, not a fresh
    node every time the same component gets touched again."""
    msg1 = update_components("s1", [{"id": "flights_card", "component": "Text", "text": "v1"}])
    msg2 = update_components("s1", [{"id": "flights_card", "component": "Text", "text": "v2"}])
    e1 = adapt_to_agui_events("ctx1", "s1", msg1, surface_already_started=True)
    e2 = adapt_to_agui_events("ctx1", "s1", msg2, surface_already_started=True)
    assert e1[0]["payload"]["toolCallId"] == e2[0]["payload"]["toolCallId"]


def test_delete_surface_emits_run_finished():
    events = adapt_to_agui_events("ctx1", "s1", delete_surface("s1"),
                                  surface_already_started=True)
    assert events == [{"type": "RunFinished", "payload": {"runId": "ctx1"}}]


def test_update_data_model_emits_state_delta_replace():
    msg = update_data_model("s1", value=1, path="/count")
    events = adapt_to_agui_events("ctx1", "s1", msg, surface_already_started=True)
    assert events == [{"type": "StateDelta", "payload": {
        "runId": "ctx1", "delta": [{"op": "replace", "path": "/count", "value": 1}]}}]


def test_update_data_model_with_null_value_emits_state_delta_remove():
    msg = update_data_model("s1", value=None, path="/count")
    events = adapt_to_agui_events("ctx1", "s1", msg, surface_already_started=True)
    assert events == [{"type": "StateDelta", "payload": {
        "runId": "ctx1", "delta": [{"op": "remove", "path": "/count"}]}}]


def test_update_data_model_can_carry_an_arbitrary_object_value():
    """The adapter makes no claim about CONTENT -- an agent can put
    anything in the data model (e.g. live_cost_trend's own real
    {turn, cumulativeTokens, cumulativeCostUsd} points shape)."""
    point = {"turn": 1, "cumulativeTokens": 120, "cumulativeCostUsd": 0.002}
    msg = update_data_model("s1", value=[point], path="/points")
    events = adapt_to_agui_events("ctx1", "s1", msg, surface_already_started=True)
    assert events[0]["payload"]["delta"][0]["value"] == [point]


def test_the_full_composition_scenario_produces_a_coherent_agui_sequence():
    """The SAME orchestrator/specialist scenario
    tests/test_a2a_counterpart.py::test_multiple_agents_compose_one_shared_surface_via_a2a
    already proves at the A2UI level -- here, the resulting AG-UI event
    sequence a viewer would actually see."""
    orchestrator_create = emit_surface({
        "title": "Shared Dashboard", "blocks": [{"type": "body", "text": "waiting"}],
    }, surface_id="shared-dashboard")
    flights_update = update_components("shared-dashboard", [
        {"id": "flights_card", "component": "Text", "text": "on time"}])
    weather_update = update_components("shared-dashboard", [
        {"id": "weather_card", "component": "Text", "text": "sunny"}])

    all_events = []
    all_events += adapt_to_agui_events("ctx1", "shared-dashboard", orchestrator_create,
                                       surface_already_started=False)
    all_events += adapt_to_agui_events("ctx1", "shared-dashboard", flights_update,
                                       surface_already_started=True)
    all_events += adapt_to_agui_events("ctx1", "shared-dashboard", weather_update,
                                       surface_already_started=True)

    types = [e["type"] for e in all_events]
    assert types == [
        "RunStarted", "StepStarted",
        "ToolCallStart", "ToolCallResult",
        "ToolCallStart", "ToolCallResult",
    ]
