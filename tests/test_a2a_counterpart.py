"""Real A2A interop test: a real `a2a-sdk` CLIENT talking to a real
`a2a-sdk` SERVER (a2a_counterpart/main.py's StatefulSurfaceExecutor), in-
process via httpx.ASGITransport -- no network, no deployed service needed,
fast enough for CI, but every object on both sides is the genuine SDK
type, not a mock or a hand-rolled JSON-RPC call.

Topic C, Phase 1 (2026-08-24) adds test_multi_turn_state_follows_a_real_a2a_conversation:
proves the executor's INTERNAL derived state (not just its echo reply)
correctly tracks a real, multi-call A2A conversation -- the actual
capability this phase exists to prove, per the plan at
~/.claude/plans/encapsulated-cuddling-kay.md ("a derived state which can
be followed by A2A", Curtis's own framing).

Phase 2 (same day) adds the getSurfaceState/surfaceStateResult query tests
below -- a way to read that derived state back OVER A2A, not just via
direct Python object access. test_multiple_agents_compose_one_shared_surface_via_a2a
is the concrete proof of the ideated use case (Gemini, 2026-08-24):
several agents, each owning a different zone of ONE shared surface, write
independently and an orchestrator that wrote nothing itself reads the
composed result -- A2A as a UI gateway across a multi-agent collection.

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
from a2a_counterpart.main import executor as counterpart_executor
from renderers.a2a_extension import (
    A2A_EXTENSION_URI, unwrap_sdk_data_part, wrap_messages_for_sdk,
)
from renderers.a2ui_v1 import emit_surface
from renderers.a2ui_v1_updates import (
    apply_update, surface_state_from_create, update_components, update_data_model,
)
from tests.test_a2a_extension import AGENT_TO_RENDERER_LIST


async def _round_trip(messages: list[dict], context_id: str | None = None,
                      message_id: str = "probe-1") -> list[dict]:
    """Sends `messages` to the real in-process counterpart, returns what it
    echoed back (already unwrapped). Passing the SAME context_id across
    separate calls simulates one A2A conversation -- see
    test_multi_turn_state_follows_a_real_a2a_conversation below."""
    transport = httpx.ASGITransport(app=counterpart_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://counterpart.local") as hc:
        card = await A2ACardResolver(hc, "http://counterpart.local").get_agent_card()
        client = ClientFactory(ClientConfig(httpx_client=hc, streaming=False)).create(
            card, extensions=[A2A_EXTENSION_URI])

        msg = Message(role=Role.user, message_id=message_id, context_id=context_id,
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


def test_multi_turn_state_follows_a_real_a2a_conversation():
    """Topic C, Phase 1's actual deliverable: the counterpart's INTERNAL
    derived state -- not just its echo reply -- correctly reflects a real,
    multi-call A2A conversation (createSurface, then updateComponents,
    then updateDataModel, each a SEPARATE send_message() call sharing one
    context_id). Cross-checked against calling apply_update() directly,
    step by step, with no A2A involved at all -- proves the executor's
    A2A-mediated derivation matches the reference semantics bit-for-bit,
    the same semantics the deployed GAS surface's poll loop already uses
    (renderers/a2ui_v1_updates.py's own docstring)."""
    import uuid
    context_id = f"multiturn-{uuid.uuid4().hex[:8]}"
    surface_id = "mt-surface"

    create_msg = emit_surface(
        {"title": "Multi-turn", "blocks": [{"type": "heading", "text": "v1"}]},
        surface_id=surface_id)
    update_msg = update_components(surface_id, [
        {"id": "extra", "component": "Text", "text": "added later"}])
    dmu_msg = update_data_model(surface_id, value=1, path="/count")

    asyncio.run(_round_trip([create_msg], context_id=context_id, message_id="turn-1"))
    asyncio.run(_round_trip([update_msg], context_id=context_id, message_id="turn-2"))
    asyncio.run(_round_trip([dmu_msg], context_id=context_id, message_id="turn-3"))

    expected = surface_state_from_create(create_msg)
    apply_update(expected, update_msg)
    apply_update(expected, dmu_msg)

    actual = counterpart_executor.state[(context_id, surface_id)]
    assert actual == expected
    # And specifically, the part a human would recognize as "it followed":
    assert "extra" in actual["components"]
    assert actual["dataModel"]["count"] == 1


def test_state_is_isolated_per_context_not_shared_globally():
    """A second, unrelated conversation using the SAME surfaceId must not
    see or corrupt the first conversation's state -- state is keyed on
    (context_id, surfaceId), not surfaceId alone."""
    import uuid
    ctx_a = f"iso-a-{uuid.uuid4().hex[:8]}"
    ctx_b = f"iso-b-{uuid.uuid4().hex[:8]}"
    surface_id = "shared-name-surface"

    create_a = emit_surface({"title": "A", "blocks": [{"type": "body", "text": "from A"}]},
                            surface_id=surface_id)
    create_b = emit_surface({"title": "B", "blocks": [{"type": "body", "text": "from B"}]},
                            surface_id=surface_id)

    asyncio.run(_round_trip([create_a], context_id=ctx_a, message_id="iso-1"))
    asyncio.run(_round_trip([create_b], context_id=ctx_b, message_id="iso-2"))

    state_a = counterpart_executor.state[(ctx_a, surface_id)]
    state_b = counterpart_executor.state[(ctx_b, surface_id)]
    assert state_a != state_b
    assert state_a == surface_state_from_create(create_a)
    assert state_b == surface_state_from_create(create_b)


def test_query_returns_current_derived_state():
    """getSurfaceState (this counterpart's own extension, not a real A2UI
    message type -- see a2a_counterpart/main.py's module docstring) reads
    the SAME state Phase 1 proved gets derived correctly, over A2A itself
    this time instead of direct Python object access."""
    import uuid
    context_id = f"query-{uuid.uuid4().hex[:8]}"
    surface_id = "query-surface"

    create_msg = emit_surface(
        {"title": "Queryable", "blocks": [{"type": "body", "text": "v1"}]},
        surface_id=surface_id)
    asyncio.run(_round_trip([create_msg], context_id=context_id, message_id="q-1"))

    query = {"getSurfaceState": {"surfaceId": surface_id}}
    reply = asyncio.run(_round_trip([query], context_id=context_id, message_id="q-2"))

    assert len(reply) == 1
    result = reply[0]["surfaceStateResult"]
    assert result["surfaceId"] == surface_id
    assert result["found"] is True
    assert result["state"] == surface_state_from_create(create_msg)


def test_query_for_unknown_surface_is_honest_not_a_crash():
    import uuid
    context_id = f"query-unknown-{uuid.uuid4().hex[:8]}"
    query = {"getSurfaceState": {"surfaceId": "never-created"}}
    reply = asyncio.run(_round_trip([query], context_id=context_id, message_id="q-unknown"))

    assert len(reply) == 1
    result = reply[0]["surfaceStateResult"]
    assert result["found"] is False
    assert result["state"] is None


def test_multiple_agents_compose_one_shared_surface_via_a2a():
    """The actual ideated use case, proven in code: an ORCHESTRATOR agent
    creates a surface with a placeholder; two SPECIALIST agents, each in
    its own separate A2A call, populate a DIFFERENT component -- no
    coordination beyond the shared context_id and the component ids they
    were each told to own (spatial partitioning, per Gemini's ideation:
    no conflict, so no locking/ownership model is needed at this stage). A
    fourth call (the orchestrator/observer) queries and sees BOTH
    contributions composed into one state -- A2A carrying a shared,
    followable UI across more than one writer, not just one agent talking
    to one renderer."""
    import uuid
    context_id = f"compose-{uuid.uuid4().hex[:8]}"
    surface_id = "shared-dashboard"

    orchestrator_create = emit_surface({
        "title": "Shared Dashboard",
        "blocks": [{"type": "body", "text": "waiting for specialists..."}],
    }, surface_id=surface_id)
    asyncio.run(_round_trip([orchestrator_create], context_id=context_id, message_id="orch-1"))

    flights_update = update_components(surface_id, [
        {"id": "flights_card", "component": "Text", "text": "Flight AA123 - on time"}])
    asyncio.run(_round_trip([flights_update], context_id=context_id, message_id="specialist-flights"))

    weather_update = update_components(surface_id, [
        {"id": "weather_card", "component": "Text", "text": "Sunny, 22C"}])
    asyncio.run(_round_trip([weather_update], context_id=context_id, message_id="specialist-weather"))

    query = {"getSurfaceState": {"surfaceId": surface_id}}
    reply = asyncio.run(_round_trip([query], context_id=context_id, message_id="orch-2"))
    composed = reply[0]["surfaceStateResult"]["state"]

    assert composed["components"]["flights_card"]["text"] == "Flight AA123 - on time"
    assert composed["components"]["weather_card"]["text"] == "Sunny, 22C"

    expected = surface_state_from_create(orchestrator_create)
    apply_update(expected, flights_update)
    apply_update(expected, weather_update)
    assert composed == expected


def test_update_to_a_real_placeholder_child_does_not_warn_orphaned():
    """flights_card/weather_card are real children of root (declared in
    the createSurface fixture above) -- updating them must NOT trigger
    the orphaned-component warning."""
    import uuid
    context_id = f"no-orphan-{uuid.uuid4().hex[:8]}"
    surface_id = "no-orphan-surface"
    before = len(counterpart_executor.orphaned_component_warnings)

    create_msg = emit_surface({
        "title": "T", "blocks": [
            {"type": "body", "text": "placeholder", "id": "real_child"}]},
        surface_id=surface_id)
    asyncio.run(_round_trip([create_msg], context_id=context_id, message_id="no-orphan-1"))

    update_msg = update_components(surface_id, [
        {"id": "real_child", "component": "Text", "text": "updated"}])
    asyncio.run(_round_trip([update_msg], context_id=context_id, message_id="no-orphan-2"))

    assert len(counterpart_executor.orphaned_component_warnings) == before


def test_update_to_a_never_declared_component_warns_orphaned():
    """A component id updated without ever being wired as a child of
    root -- the exact real bug found building scripts/a2a_demo_sketch.py."""
    import uuid
    context_id = f"orphan-{uuid.uuid4().hex[:8]}"
    surface_id = "orphan-surface"
    before = len(counterpart_executor.orphaned_component_warnings)

    create_msg = emit_surface({
        "title": "T", "blocks": [{"type": "body", "text": "hi", "id": "real_child"}]},
        surface_id=surface_id)
    asyncio.run(_round_trip([create_msg], context_id=context_id, message_id="orphan-1"))

    update_msg = update_components(surface_id, [
        {"id": "never_declared", "component": "Text", "text": "ghost"}])
    asyncio.run(_round_trip([update_msg], context_id=context_id, message_id="orphan-2"))

    warnings = counterpart_executor.orphaned_component_warnings[before:]
    assert len(warnings) == 1
    assert "never_declared" in warnings[0]


def test_sketch_form_page_serves():
    """GET /sketch -- the real prompt-to-drawing web demo page. No live
    Gemini call involved, just confirms the route + form render."""
    async def _get():
        transport = httpx.ASGITransport(app=counterpart_app)
        async with httpx.AsyncClient(transport=transport, base_url="http://counterpart.local") as hc:
            return await hc.get("/sketch")
    resp = asyncio.run(_get())
    assert resp.status_code == 200
    assert "form" in resp.text and 'name="subject"' in resp.text


def test_sketch_submit_without_subject_is_a_clean_400():
    """POST /sketch with no subject -- must fail cleanly, not 500. This is
    also the real regression test for the python-multipart dependency gap
    found live (request.form() 500'd with it missing, even for a plain
    application/x-www-form-urlencoded body)."""
    async def _post():
        transport = httpx.ASGITransport(app=counterpart_app)
        async with httpx.AsyncClient(transport=transport, base_url="http://counterpart.local") as hc:
            return await hc.post("/sketch", data={"subject": ""})
    resp = asyncio.run(_post())
    assert resp.status_code == 400


def test_sketch_submit_creates_a_real_wired_placeholder_surface():
    """POST /sketch must create the surface SYNCHRONOUSLY (before
    redirecting) with the sketch component already a real child of root --
    same orphaned-component lesson as scripts/a2a_demo_sketch.py, tested
    here directly against the executor's own derived state rather than
    waiting for the (real-Gemini-dependent) background task to run."""
    async def _post():
        transport = httpx.ASGITransport(app=counterpart_app)
        async with httpx.AsyncClient(transport=transport, base_url="http://counterpart.local",
                                     follow_redirects=False) as hc:
            return await hc.post("/sketch", data={"subject": "a test subject"})
    resp = asyncio.run(_post())
    assert resp.status_code == 303
    location = resp.headers["location"]
    assert location.startswith("/demo/web-sketch-")
    context_id = location.split("/")[2]
    state = counterpart_executor.state.get((context_id, "web-sketch-surface"))
    assert state is not None
    assert "sketch" in state["components"]
    # Reachable from root, not orphaned -- confirms the placeholder is a
    # real child, matching the fix already proven in test_a2a_counterpart.py's
    # orphaned-component tests above.
    root = state["components"]["root"]
    assert "sketch" in root.get("children", [])


def test_render_fragment_is_empty_for_unknown_surface_not_404():
    """/demo pulls this into the page on every ToolCallResult -- an
    empty-but-200 response for "not created yet" lets the page's own
    fetch loop just skip the update, rather than treating it as an error
    each time (real difference from /render, which 404s intentionally for
    a human following a stale link)."""
    async def _get():
        transport = httpx.ASGITransport(app=counterpart_app)
        async with httpx.AsyncClient(transport=transport, base_url="http://counterpart.local") as hc:
            return await hc.get("/render-fragment/never-created-ctx/never-created-surface")
    resp = asyncio.run(_get())
    assert resp.status_code == 200
    assert resp.text == ""


def test_render_fragment_reflects_real_derived_state():
    """The actual thing Curtis asked for, 2026-08-24: the live drawing
    pulled into the SAME page as the AG-UI panels, not a separate /render
    URL -- this is the fragment /demo's own JS fetches and injects."""
    import uuid
    context_id = f"fragment-{uuid.uuid4().hex[:8]}"
    surface_id = "fragment-surface"
    create_msg = emit_surface({
        "title": "T", "blocks": [
            {"type": "agent_sketchpad", "id": "sketch", "viewBox": "0 0 400 200",
             "strokes": [{"path": "M 0 0 L 10 10", "color": "red", "width": 2}]}]},
        surface_id=surface_id)
    asyncio.run(_round_trip([create_msg], context_id=context_id, message_id="frag-1"))

    async def _get():
        transport = httpx.ASGITransport(app=counterpart_app)
        async with httpx.AsyncClient(transport=transport, base_url="http://counterpart.local") as hc:
            return await hc.get(f"/render-fragment/{context_id}/{surface_id}")
    resp = asyncio.run(_get())
    assert resp.status_code == 200
    assert "<svg" in resp.text and 'd="M 0 0 L 10 10"' in resp.text
    # A fragment, not a full page -- /demo injects this straight into a div.
    assert "<html" not in resp.text.lower()
