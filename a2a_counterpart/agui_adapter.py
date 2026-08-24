"""agui_adapter.py — Topic C, Phase 4: translates real A2UI v1.0 messages
(the same ones StatefulSurfaceExecutor already applies to derived state)
into the event shape and vocabulary AG-UI's live-atoms runtime consumes
(cloud-run-renderer/static/a2ui-stream-runtime.v1.js +
a2ui-atoms-live.v1.js — a separate, already-merged, already-tested
workstream this session had nothing to do with until today).

This provides SEMANTIC COMPATIBILITY FOR UI REUSE, not a guarantee of 1:1
fidelity with a native AG-UI event stream (Gemini design review,
2026-08-24). The goal is deliberately near-parity, not full parity —
Curtis's own framing: chasing exact AG-UI fidelity isn't the objective;
letting A2A drive the SAME real, tested UI components AG-UI already has
is. Reuses AG-UI's own event names verbatim (RunStarted/StepStarted/
ToolCallStart/ToolCallResult/RunFinished) rather than inventing a
parallel vocabulary -- this module's own name and docs are where the
honesty about what's really happening lives, not a renamed event type.

Mapping (each justified on its own):
  - First createSurface seen for a (context_id, surfaceId) -> RunStarted
    + StepStarted. The step IS the surface -- one A2UI surface is the
    natural unit of "one piece of work."
  - Each updateComponents -> one ToolCallStart + ToolCallResult PAIR per
    touched component id. An update to one component is an honest analog
    of "one unit of work an agent performed" -- this is what makes
    agent_run_sketch draw one node per contribution (e.g. one specialist
    populating one card in the orchestrator/specialist composition use
    case, see tests/test_a2a_counterpart.py).
  - deleteSurface -> RunFinished.
  - updateDataModel -> INTENTIONALLY UNMAPPED. Neither live_step_tracker
    nor agent_run_sketch has any visual concept of a data-only patch;
    StateDelta would be the semantically honest AG-UI event (the runtime
    already has real JSON-Patch-apply support for it), but wiring a
    consumer for it is out of scope for this phase's two chosen atoms.

Pure, synchronous function -- no sleeping, no I/O. The deliberate
ToolCallStart/ToolCallResult visual pacing (so a viewer actually sees the
in-progress state, not an instantly-collapsed one) belongs at the
STREAMING boundary (main.py's SSE endpoint), not here -- keeps this
function trivially unit-testable without any timing dependency.
"""
from __future__ import annotations

import hashlib
from typing import Any, Dict, List


def _tool_call_id(surface_id: str, component_id: str) -> str:
    """Stable across repeated updates to the SAME component -- a real
    agent_run_sketch node identity, not a fresh id (and fresh node) every
    time the same component gets touched again."""
    return hashlib.sha256(f"{surface_id}:{component_id}".encode()).hexdigest()[:12]


def adapt_to_agui_events(context_id: str, surface_id: str,
                         a2ui_message: Dict[str, Any],
                         *, surface_already_started: bool) -> List[Dict[str, Any]]:
    """`surface_already_started`: caller's own knowledge of whether
    RunStarted/StepStarted were already emitted for this (context_id,
    surfaceId) -- this function does not keep its own state (kept pure),
    the caller (StatefulSurfaceExecutor, which already tracks this exact
    surface's lifecycle) is the natural place for that bookkeeping."""
    events: List[Dict[str, Any]] = []

    if "createSurface" in a2ui_message:
        if not surface_already_started:
            events.append({"type": "RunStarted", "payload": {"runId": context_id}})
            events.append({"type": "StepStarted",
                           "payload": {"runId": context_id, "stepId": surface_id}})
        return events

    if "updateComponents" in a2ui_message:
        uc = a2ui_message["updateComponents"]
        for comp in uc.get("components", []):
            component_id = comp.get("id")
            if component_id is None:
                continue
            tool_call_id = _tool_call_id(surface_id, component_id)
            events.append({"type": "ToolCallStart", "payload": {
                "runId": context_id, "toolCallId": tool_call_id,
                "toolName": component_id}})
            events.append({"type": "ToolCallResult", "payload": {
                "runId": context_id, "toolCallId": tool_call_id,
                "result": {"componentType": comp.get("component")}}})
        return events

    if "deleteSurface" in a2ui_message:
        events.append({"type": "RunFinished", "payload": {"runId": context_id}})
        return events

    # updateDataModel and anything else: intentionally unmapped, see
    # module docstring.
    return events
