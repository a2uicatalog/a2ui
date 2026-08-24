"""Real A2A interop test: a real `a2a-sdk` CLIENT talking to a real
`a2a-sdk` SERVER (a2a_counterpart/main.py's EchoExecutor), in-process via
httpx.ASGITransport -- no network, no deployed service needed, fast enough
for CI, but every object on both sides is the genuine SDK type, not a
mock or a hand-rolled JSON-RPC call.

Proves the whole chain: real renderers/a2ui_v1.py emit_surface() output ->
real renderers/a2a_extension.py wrap_messages_for_sdk() -> real
a2a.types.DataPart -> real a2a-sdk client send_message() -> real
A2AStarletteApplication/DefaultRequestHandler -> EchoExecutor -> real
a2a-sdk server response -> unwrap_sdk_data_part() -> still byte-identical
to the original messages AND still schema-valid A2UI v1.0.

Why wrap_messages_for_sdk()/unwrap_sdk_data_part(), not the plain
wrap_messages()/unwrap_data_part() that tests/test_a2a_extension.py uses:
see renderers/a2a_extension.py's own docstring on those functions -- the
real a2a-sdk 0.3.x DataPart.data field is dict-only (a2ui-project/a2ui#645,
closed: fixed only under A2A 1.0 semantics, which this estate's pinned SDK
version doesn't implement).

The deployed Cloud Run round trip is a separate, manual smoke test (see
ops/project-ops.yaml's a2a-counterpart-deploy verify step) -- an
authenticated live-network check isn't suited to unattended CI, and this
in-process test already proves the message-shape correctness that matters.
"""
from __future__ import annotations

import asyncio

import httpx
import pytest
from a2a.client import A2ACardResolver, ClientConfig, ClientFactory
from a2a.types import DataPart, Message, Part, Role

from a2a_counterpart.main import app as counterpart_app
from renderers.a2a_extension import (
    A2A_EXTENSION_URI, unwrap_sdk_data_part, wrap_messages_for_sdk,
)
from renderers.a2ui_v1 import emit_surface
from renderers.a2ui_v1_updates import update_data_model
from tests.test_a2a_extension import AGENT_TO_RENDERER_LIST


async def _round_trip(messages: list[dict]) -> list[dict]:
    """Sends `messages` to the real in-process counterpart, returns what it
    echoed back (already unwrapped)."""
    transport = httpx.ASGITransport(app=counterpart_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://counterpart.local") as hc:
        card = await A2ACardResolver(hc, "http://counterpart.local").get_agent_card()
        client = ClientFactory(ClientConfig(httpx_client=hc, streaming=False)).create(
            card, extensions=[A2A_EXTENSION_URI])

        msg = Message(role=Role.user, message_id="probe-1",
                      parts=[Part(root=DataPart(**wrap_messages_for_sdk(messages)))])

        got = None
        async for event in client.send_message(msg, extensions=[A2A_EXTENSION_URI]):
            got = event

        assert isinstance(got, Message), f"expected a bare Message reply, got {type(got)}"
        data_part = next(
            (getattr(p, "root", p) for p in got.parts
             if isinstance(getattr(p, "root", p), DataPart)),
            None)
        assert data_part is not None, "counterpart's reply carried no DataPart"
        return unwrap_sdk_data_part(data_part.model_dump())


def test_agent_card_advertises_the_v1_extension():
    async def _get_card():
        transport = httpx.ASGITransport(app=counterpart_app)
        async with httpx.AsyncClient(transport=transport, base_url="http://counterpart.local") as hc:
            return await A2ACardResolver(hc, "http://counterpart.local").get_agent_card()

    card = asyncio.run(_get_card())
    uris = [ext.uri for ext in (card.capabilities.extensions or [])]
    assert A2A_EXTENSION_URI in uris


def test_real_emitted_surface_round_trips_through_a_real_a2a_server():
    surface = emit_surface({
        "title": "Interop Probe", "theme": "dark",
        "blocks": [{"type": "body", "text": "hello from the real emitter"}],
    })
    echoed = asyncio.run(_round_trip([surface]))

    assert echoed == [surface]
    errors = list(AGENT_TO_RENDERER_LIST.iter_errors(echoed))
    assert not errors, errors


def test_a_batch_of_real_messages_round_trips_in_order():
    surface = emit_surface({"title": "Batch", "blocks": [{"type": "heading", "text": "Hi"}]})
    dmu = update_data_model("s1", value={"count": 1}, path="/count")
    echoed = asyncio.run(_round_trip([surface, dmu]))

    assert echoed == [surface, dmu]
    errors = list(AGENT_TO_RENDERER_LIST.iter_errors(echoed))
    assert not errors, errors


def test_non_a2ui_data_part_is_rejected_not_silently_dropped():
    """The counterpart's own not-A2UI-shaped-data branch (no DataPart at
    all) still replies, rather than hanging or 500ing -- confirms
    EchoExecutor's error path is real, not just its happy path."""
    async def _send_naked_text():
        transport = httpx.ASGITransport(app=counterpart_app)
        async with httpx.AsyncClient(transport=transport, base_url="http://counterpart.local") as hc:
            card = await A2ACardResolver(hc, "http://counterpart.local").get_agent_card()
            client = ClientFactory(ClientConfig(httpx_client=hc, streaming=False)).create(card)
            from a2a.types import TextPart
            msg = Message(role=Role.user, message_id="probe-2",
                          parts=[Part(root=TextPart(text="no data part here"))])
            got = None
            async for event in client.send_message(msg):
                got = event
            return got

    got = asyncio.run(_send_naked_text())
    assert isinstance(got, Message)
    text_parts = [getattr(p, "root", p).text for p in got.parts
                  if hasattr(getattr(p, "root", p), "text")]
    assert any("No DataPart" in t for t in text_parts)
