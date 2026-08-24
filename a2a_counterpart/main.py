"""a2a_counterpart — a minimal, real A2A v1.0 service. Started as a pure
echo (Topic B); now (Topic C, Phase 1) also maintains real DERIVED STATE
across multiple A2A calls, reusing renderers/a2ui_v1_updates.py's reference
receive semantics (surface_state_from_create()/apply_update()) -- the same
functions the deployed GAS surface's poll loop already uses, and the same
ones A2uiUpdates.html ports faithfully to JS. Nothing here reimplements
that logic; StatefulSurfaceExecutor only threads real A2A message batches
into it.

Reply behavior is UNCHANGED from Topic B on purpose: still echoes the same
messages back (proven, tested, and what tests/test_a2a_counterpart.py's
existing round-trip tests assert on) -- Phase 1's new capability is purely
the internal state tracking, inspectable directly via the module-level
`executor` object in tests. Phase 2 (not built yet) adds a way to read
derived state back over A2A itself, for a real agent consumer rather than
a test's direct object access.

Modeled directly on the live `a2ui-ge-agent/main.py` (same
AgentCard/A2AStarletteApplication/DefaultRequestHandler shape, same
`uvicorn.run` entrypoint), trimmed to only what this needs: no rendering,
no GCS, no image bridge, no v0.8 probe history. See tests/test_a2a_counterpart.py
for the real round-trip tests (in-process, no network, via httpx.ASGITransport).

Bare message reply, not a modeled Task: still no Task/TaskUpdater lifecycle
(Gemini design review, 2026-08-24, endorsed this for the echo case; state
tracking here is keyed on (context_id, surfaceId), independent of A2A's own
task lifecycle, so it doesn't change this call).
"""
import os

import uvicorn
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities, AgentCard, AgentExtension, AgentSkill,
    DataPart, Part, TextPart,
)
from a2a.utils import new_agent_parts_message

from renderers.a2a_extension import (
    A2A_EXTENSION_URI, agent_card_extension, unwrap_sdk_data_part,
    wrap_messages_for_sdk,
)
from renderers.a2ui_v1 import DEFAULT_CATALOG_ID
from renderers.a2ui_v1_updates import apply_update, surface_state_from_create

AGENT_BASE_URL = os.environ.get("AGENT_BASE_URL", "https://placeholder.a.run.app")


def _surface_id_of(msg: dict) -> str | None:
    """The one surfaceId-bearing key a v1.0 message carries, whichever kind
    it is -- mirrors the same dispatch apply_update() itself does."""
    for key in ("createSurface", "updateComponents", "updateDataModel", "deleteSurface"):
        if key in msg:
            return msg[key].get("surfaceId")
    return None


class StatefulSurfaceExecutor(AgentExecutor):
    """Reflects the incoming A2UI v1.0 DataPart back unchanged (same proven
    behavior as Topic B's EchoExecutor), AND maintains one derived surface
    state per (context_id, surfaceId) in memory -- same in-memory-store
    shape InMemoryTaskStore already uses for tasks, same real
    per-message-not-transactional error tolerance the extension spec itself
    requires (a message that fails to apply is skipped, not fatal to the
    rest of the batch -- see renderers/a2a_extension.py's own docstring
    quoting the spec on this)."""

    def __init__(self) -> None:
        self.state: dict[tuple[str, str], dict] = {}
        # Cheap debugging lever (Gemini post-impl review, 2026-08-24): not
        # surfaced anywhere yet, but a client that swears it sent updates
        # and sees no effect needs SOME internal signal that they were
        # tolerated-skipped, not silently mis-applied.
        self.skipped_updates_count = 0

    def _apply_batch(self, context_id: str, messages: list[dict]) -> None:
        for msg in messages:
            sid = _surface_id_of(msg)
            if sid is None:
                continue
            key = (context_id, sid)
            try:
                if "createSurface" in msg:
                    self.state[key] = surface_state_from_create(msg)
                elif key in self.state:
                    apply_update(self.state[key], msg)
                else:
                    # An update for a surface with no createSurface seen yet
                    # in this context -- real spec's own per-message error
                    # tolerance, skip and keep processing the rest of the
                    # batch.
                    self.skipped_updates_count += 1
            except Exception:
                self.skipped_updates_count += 1

    async def execute(self, context: RequestContext, event_queue: EventQueue):
        context.add_activated_extension(A2A_EXTENSION_URI)

        data_part = next(
            (getattr(p, "root", p) for p in (context.message.parts or [])
             if isinstance(getattr(p, "root", p), DataPart)),
            None,
        )
        if data_part is None:
            reply = [Part(root=TextPart(
                text="No DataPart found on the incoming message — nothing to echo."))]
            await event_queue.enqueue_event(new_agent_parts_message(
                reply, context.context_id, context.task_id))
            return

        try:
            messages = unwrap_sdk_data_part(data_part.model_dump())
        except Exception as e:
            reply = [Part(root=TextPart(text=f"unwrap_sdk_data_part failed: {e}"))]
            await event_queue.enqueue_event(new_agent_parts_message(
                reply, context.context_id, context.task_id))
            return

        self._apply_batch(context.context_id, messages)

        echoed = Part(root=DataPart(**wrap_messages_for_sdk(messages)))
        await event_queue.enqueue_event(new_agent_parts_message(
            [echoed], context.context_id, context.task_id))

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        raise Exception("cancel not supported")


skill = AgentSkill(
    id="echo_a2ui_v1",
    name="Echo an A2UI v1.0 DataPart",
    description="Reflects a received A2UI v1.0 DataPart back unchanged, and tracks its derived surface state across calls.",
    tags=["a2ui", "a2a", "interop-test"],
    examples=[],
)

a2ui_extension = AgentExtension(**agent_card_extension(
    supported_catalog_ids=[DEFAULT_CATALOG_ID],
    description="Echoes A2UI v1.0 DataParts and derives their surface state for interop testing",
))

agent_card = AgentCard(
    name="a2a_counterpart_echo",
    description="Minimal A2A v1.0 echo service — reflects A2UI DataParts back unchanged and tracks derived surface state, for interop testing.",
    url=AGENT_BASE_URL,
    version="0.1.0",
    default_input_modes=["text/plain", "application/a2ui+json"],
    default_output_modes=["text/plain", "application/a2ui+json"],
    capabilities=AgentCapabilities(streaming=True, extensions=[a2ui_extension]),
    skills=[skill],
)

# Module-level, not built inline: tests import this directly to inspect
# derived state after driving it through real A2A calls (see
# tests/test_a2a_counterpart.py's multi-turn state test).
executor = StatefulSurfaceExecutor()

app = A2AStarletteApplication(
    agent_card=agent_card,
    http_handler=DefaultRequestHandler(
        agent_executor=executor, task_store=InMemoryTaskStore()),
).build()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
