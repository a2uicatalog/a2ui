#!/usr/bin/env python3
"""a2a_demo_composition.py — drives the orchestrator/specialist multi-agent
UI composition use case (the one Gemini's ideation ranked highest, and
tests/test_a2a_counterpart.py::test_multiple_agents_compose_one_shared_surface_via_a2a
already proves) through REAL A2A calls against a RUNNING a2a_counterpart
instance.

Two ways to see the result, both real, neither faked:
  - Phase 3's /render/{context_id}/{surface_id}: a static HTML snapshot,
    reload to see the current composed state.
  - Phase 4's /demo/{context_id}/{surface_id}: live_step_tracker +
    agent_run_sketch, fed by the real /agui-stream SSE bridge -- watch it
    build as the specialists' A2A calls actually happen. This requires the
    page to be OPEN AND CONNECTED before the calls are sent (subscribe-
    before-send is real live-stream semantics, confirmed in
    tests/test_agui_stream_endpoint.py -- a late subscriber does not see
    replayed history), so this script prints the /demo URL FIRST and
    waits for you to open it.

Usage:
    # 1. Run the service:
    uvicorn a2a_counterpart.main:app --port 8091 &
    AGENT_BASE_URL=http://localhost:8091 (must match, see a2a_live_probe.py's
    own note on why -- restart with it set if you didn't)

    # 2. Drive the demo:
    python3 scripts/a2a_demo_composition.py --url http://localhost:8091

    # 3. Open the printed /demo URL, then press Enter in this terminal.
"""
import argparse
import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import httpx
from a2a.client import A2ACardResolver, ClientConfig, ClientFactory
from a2a.types import DataPart, Message, Part, Role

from renderers.a2a_extension import A2A_EXTENSION_URI, wrap_messages_for_sdk
from renderers.a2ui_v1 import emit_surface
from renderers.a2ui_v1_updates import update_components


async def _send(client, url_note, context_id, message_id, messages):
    msg = Message(role=Role.user, message_id=message_id, context_id=context_id,
                  parts=[Part(root=DataPart(**wrap_messages_for_sdk(messages)))])
    async for event in client.send_message(msg, extensions=[A2A_EXTENSION_URI]):
        pass
    print(f"[a2a_demo_composition] sent {message_id} ({url_note})")


async def run(url: str, wait_for_open) -> str:
    context_id = f"demo-{uuid.uuid4().hex[:8]}"
    surface_id = "shared-dashboard"

    demo_url = f"{url}/demo/{context_id}/{surface_id}"
    render_url = f"{url}/render/{context_id}/{surface_id}"
    print()
    print("LIVE demo (open this first, then come back here):")
    print(f"  {demo_url}")
    print()
    wait_for_open()

    async with httpx.AsyncClient(base_url=url, timeout=30) as hc:
        card = await A2ACardResolver(hc, url).get_agent_card()
        client = ClientFactory(ClientConfig(httpx_client=hc, streaming=False)).create(
            card, extensions=[A2A_EXTENSION_URI])

        # Orchestrator declares REAL placeholder children up front, with
        # pinned ids -- _IdGen honours an author-supplied `id` (renderers/
        # a2ui_v1.py). A specialist's updateComponents upserts the SAME id
        # in place, so the tree stays wired and the update actually
        # renders -- an id that was never a child of anything would sit in
        # derived state correctly (proven in the pytest test) but never
        # reach the rendered tree at all (found live building this demo).
        orchestrator_create = emit_surface({
            "title": "Shared Dashboard (Multi-Agent Demo)",
            "blocks": [
                {"type": "body", "text": "Orchestrator: waiting for specialists...",
                 "id": "status_line"},
                {"type": "body", "text": "(flights specialist pending)", "id": "flights_card"},
                {"type": "body", "text": "(weather specialist pending)", "id": "weather_card"},
            ],
        }, surface_id=surface_id)
        await _send(client, "orchestrator: createSurface", context_id, "orch-1",
                    [orchestrator_create])

        flights_update = update_components(surface_id, [
            {"id": "flights_card", "component": "Text",
             "text": "Flight AA123 to SFO — on time, gate B14"}])
        await _send(client, "specialist A (flights)", context_id, "specialist-flights",
                    [flights_update])

        weather_update = update_components(surface_id, [
            {"id": "weather_card", "component": "Text",
             "text": "San Francisco: sunny, 22C, light wind"}])
        await _send(client, "specialist B (weather)", context_id, "specialist-weather",
                    [weather_update])

    return render_url


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default="http://localhost:8091",
                    help="Base URL of a running a2a_counterpart service")
    ap.add_argument("--no-wait", action="store_true",
                    help="Don't pause for the demo page to be opened -- "
                         "fine for --url .../render only, the live /demo "
                         "stream will show nothing (see module docstring)")
    args = ap.parse_args()

    def wait_for_open():
        if args.no_wait:
            return
        input("Press Enter once the LIVE demo page above is open in a browser... ")

    render_url = asyncio.run(run(args.url.rstrip("/"), wait_for_open))
    print()
    print("Static snapshot (reload to see current state):")
    print(f"  {render_url}")


if __name__ == "__main__":
    main()
