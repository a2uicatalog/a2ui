"""a2a_counterpart — a minimal, real A2A v1.0 echo service.

Deliberately NOT a rendering agent: it has no catalogue knowledge and
generates no UI of its own. Its only job is to prove the WIRE round-trip —
receive an A2UI v1.0 DataPart over a real `a2a-sdk` server, send the exact
same message list straight back — so `renderers/a2a_extension.py`'s
wrap/unwrap functions can be proven against a real A2A server/client pair,
not just unit-tested in isolation.

Modeled directly on the live `a2ui-ge-agent/main.py` (same
AgentCard/A2AStarletteApplication/DefaultRequestHandler shape, same
`uvicorn.run` entrypoint), trimmed to only what an echo needs: no rendering,
no GCS, no image bridge, no v0.8 probe history. See tests/test_a2a_counterpart.py
for the real round-trip test (in-process, no network, via httpx.ASGITransport)
that this service exists to make possible.

Bare message reply, not a modeled Task: an echo has no state and never
progresses through submitted/working/completed, so forcing it through
TaskUpdater would add lifecycle boilerplate that proves nothing extra
(Gemini design review, 2026-08-24, endorsed this explicitly — the full task
lifecycle already has a real example in a2ui-ge-agent's rendering jobs).
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

AGENT_BASE_URL = os.environ.get("AGENT_BASE_URL", "https://placeholder.a.run.app")


class EchoExecutor(AgentExecutor):
    """Reflects the incoming A2UI v1.0 DataPart back unchanged. Proves the
    round trip; generates nothing of its own — see module docstring."""

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

        echoed = Part(root=DataPart(**wrap_messages_for_sdk(messages)))
        await event_queue.enqueue_event(new_agent_parts_message(
            [echoed], context.context_id, context.task_id))

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        raise Exception("cancel not supported")


skill = AgentSkill(
    id="echo_a2ui_v1",
    name="Echo an A2UI v1.0 DataPart",
    description="Reflects a received A2UI v1.0 DataPart back unchanged — proves the A2A wire round-trip.",
    tags=["a2ui", "a2a", "interop-test"],
    examples=[],
)

a2ui_extension = AgentExtension(**agent_card_extension(
    supported_catalog_ids=[DEFAULT_CATALOG_ID],
    description="Echoes A2UI v1.0 DataParts for interop testing",
))

agent_card = AgentCard(
    name="a2a_counterpart_echo",
    description="Minimal A2A v1.0 echo service — reflects A2UI DataParts back unchanged for interop testing.",
    url=AGENT_BASE_URL,
    version="0.1.0",
    default_input_modes=["text/plain", "application/a2ui+json"],
    default_output_modes=["text/plain", "application/a2ui+json"],
    capabilities=AgentCapabilities(streaming=True, extensions=[a2ui_extension]),
    skills=[skill],
)

app = A2AStarletteApplication(
    agent_card=agent_card,
    http_handler=DefaultRequestHandler(
        agent_executor=EchoExecutor(), task_store=InMemoryTaskStore()),
).build()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
