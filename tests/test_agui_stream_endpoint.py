"""GET /agui-stream/{context_id}/{surface_id} -- the real SSE bridge from
A2A traffic to AG-UI-shaped events. Sending is driven through the real
A2A client/server pair (httpx.ASGITransport works fine for ordinary
request/response calls -- proven throughout tests/test_a2a_counterpart.py).

Receiving is driven by calling main.agui_event_lines() DIRECTLY, not
through an HTTP client: httpx.ASGITransport was confirmed (2026-08-24,
building this) to buffer an ASGI response's ENTIRE body before returning
anything to the caller, which makes a genuinely infinite SSE stream
untestable through it at all (a real transport limitation, not a bug in
the endpoint -- reproduced with a minimal Starlette repro before
concluding this). Driving the real generator function directly still
exercises the real subscribe/publish/format logic end to end; only the
HTTP/ASGI plumbing around it is untested here (structurally identical to
every other route already registered and exercised in this file's
sibling tests). The real end-to-end HTTP+browser path is the manual/
visual proof (scripts/a2a_demo_composition.py + a real browser), per the
approved Phase 4 plan.
"""
from __future__ import annotations

import asyncio
import json

import httpx
import pytest
from a2a.client import A2ACardResolver, ClientConfig, ClientFactory
from a2a.types import DataPart, Message, Part, Role

from a2a_counterpart.main import agui_event_lines
from a2a_counterpart.main import app as counterpart_app
from renderers.a2a_extension import A2A_EXTENSION_URI, wrap_messages_for_sdk
from renderers.a2ui_v1 import emit_surface
from renderers.a2ui_v1_updates import update_components


async def _send(context_id: str, message_id: str, messages: list[dict]) -> None:
    transport = httpx.ASGITransport(app=counterpart_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://counterpart.local") as hc:
        card = await A2ACardResolver(hc, "http://counterpart.local").get_agent_card()
        client = ClientFactory(ClientConfig(httpx_client=hc, streaming=False)).create(
            card, extensions=[A2A_EXTENSION_URI])
        msg = Message(role=Role.user, message_id=message_id, context_id=context_id,
                      parts=[Part(root=DataPart(**wrap_messages_for_sdk(messages)))])
        async for _ in client.send_message(msg, extensions=[A2A_EXTENSION_URI]):
            pass


def _parse_sse_line(line: str) -> dict:
    assert line.startswith("data:")
    return json.loads(line.split("data:", 1)[1].strip())


async def _collect_n_records(context_id: str, surface_id: str, count: int,
                             ready: asyncio.Event) -> list[dict]:
    records = []
    gen = agui_event_lines(context_id, surface_id)
    first = await gen.__anext__()
    assert _parse_sse_line(first.strip().split("\n")[-1])["type"] == "Connected"
    ready.set()
    async for chunk in gen:
        records.append(_parse_sse_line(chunk.strip().split("\n")[-1]))
        if len(records) >= count:
            await gen.aclose()
            return records
    return records


def test_real_composition_scenario_streams_in_order():
    async def scenario():
        import uuid
        context_id = f"sse-{uuid.uuid4().hex[:8]}"
        surface_id = "sse-surface"
        ready = asyncio.Event()

        collector = asyncio.ensure_future(
            _collect_n_records(context_id, surface_id, count=12, ready=ready))
        await ready.wait()  # subscriber must be registered before sending, or events are missed

        create_msg = emit_surface(
            {"title": "SSE Test", "blocks": [{"type": "body", "text": "hi"}]},
            surface_id=surface_id)
        await _send(context_id, "sse-1", [create_msg])

        flights_update = update_components(surface_id, [
            {"id": "flights_card", "component": "Text", "text": "on time"}])
        await _send(context_id, "sse-2", [flights_update])

        weather_update = update_components(surface_id, [
            {"id": "weather_card", "component": "Text", "text": "sunny"}])
        await _send(context_id, "sse-3", [weather_update])

        return await asyncio.wait_for(collector, timeout=10)

    records = asyncio.run(scenario())
    types = [r["type"] for r in records]
    assert types == [
        "RunStarted", "StepStarted",
        "ToolCallStart", "ToolCallResult",
        "TextMessageStart", "TextMessageContent", "TextMessageEnd",
        "ToolCallStart", "ToolCallResult",
        "TextMessageStart", "TextMessageContent", "TextMessageEnd",
    ]
    assert records[2]["payload"]["toolName"] == "flights_card"
    assert records[5]["payload"]["delta"] == "on time"
    assert records[7]["payload"]["toolName"] == "weather_card"
    assert records[10]["payload"]["delta"] == "sunny"


def test_a_message_sent_before_subscribing_is_not_retroactively_delivered():
    """Real live-stream semantics: a subscriber only sees events published
    AFTER it subscribes -- confirms this isn't accidentally a replay/log,
    which would be a different (and more expensive) thing to have built."""
    async def scenario():
        import uuid
        context_id = f"sse-early-{uuid.uuid4().hex[:8]}"
        surface_id = "sse-early-surface"

        create_msg = emit_surface(
            {"title": "Too Early", "blocks": [{"type": "body", "text": "hi"}]},
            surface_id=surface_id)
        await _send(context_id, "early-1", [create_msg])

        ready = asyncio.Event()
        collector = asyncio.ensure_future(
            _collect_n_records(context_id, surface_id, count=5, ready=ready))
        await ready.wait()

        second_update = update_components(surface_id, [
            {"id": "late_card", "component": "Text", "text": "after subscribe"}])
        await _send(context_id, "early-2", [second_update])

        return await asyncio.wait_for(collector, timeout=10)

    records = asyncio.run(scenario())
    assert [r["type"] for r in records] == [
        "ToolCallStart", "ToolCallResult",
        "TextMessageStart", "TextMessageContent", "TextMessageEnd",
    ]
