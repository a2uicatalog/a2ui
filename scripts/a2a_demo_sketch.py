#!/usr/bin/env python3
"""a2a_demo_sketch.py — drives a SINGLE agent progressively drawing one
coherent picture (a sunrise over mountains) via real A2A calls, using the
new agent_sketchpad atom (2026-08-24) -- one real "M ..." stroke added
per real A2A message, each fully re-sent (A2UI carries full values, not
deltas) so the picture visibly grows and the newest stroke draws itself
in via agent_sketchpad's own real CSS animation.

This is a DIFFERENT scenario from a2a_demo_composition.py's multi-agent
UI composition demo -- this one is a single "artist" agent, proving the
literal "watch a picture build stroke by stroke" capability (the actual
parity target for the original hand-rolled AG-UI sketch demo), via a
real catalogue atom rather than any invented mechanism.

Usage: same pattern as a2a_demo_composition.py --
    uvicorn a2a_counterpart.main:app --port 8091 &  (with AGENT_BASE_URL set)
    python3 scripts/a2a_demo_sketch.py --url http://localhost:8091
"""
import argparse
import asyncio
import os
import sys
import time
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import httpx
from a2a.client import A2ACardResolver, ClientConfig, ClientFactory
from a2a.types import DataPart, Message, Part, Role

from renderers.a2a_extension import A2A_EXTENSION_URI, wrap_messages_for_sdk
from renderers.a2ui_v1 import emit_surface
from renderers.a2ui_v1_updates import update_components

# A real, hand-designed 5-stage illustration -- a sunrise over a mountain
# range with two birds -- within agent_sketchpad's configurable viewBox
# (unlike svg_path_draw's fixed 400x80 box, this one can be a real scene).
# Each stage is ONE ADDITIONAL stroke; the cumulative list is resent in
# full each time (agent_sketchpad's own real contract).
SKETCH_STAGES = [
    ("horizon", '<path d="M 0 170 L 400 170" stroke="#94a3b8" stroke-width="2" fill="none"/>'),
    ("sun", '<circle cx="200" cy="60" r="35" fill="#f59e0b"/>'),
    ("left mountain", '<path d="M 30 170 L 110 60 L 190 170" stroke="#475569" stroke-width="3" fill="none"/>'),
    ("right mountain", '<path d="M 170 170 L 260 90 L 350 170" stroke="#334155" stroke-width="3" fill="none"/>'),
    ("birds", '<path d="M 60 40 Q 70 30 80 40 Q 90 30 100 40 M 120 25 Q 130 15 140 25 Q 150 15 160 25" '
              'stroke="#1e293b" stroke-width="2" fill="none"/>'),
]


async def _send(client, context_id, message_id, messages):
    msg = Message(role=Role.user, message_id=message_id, context_id=context_id,
                  parts=[Part(root=DataPart(**wrap_messages_for_sdk(messages)))])
    async for _ in client.send_message(msg, extensions=[A2A_EXTENSION_URI]):
        pass


async def run(url: str, wait_for_open, pace_seconds: float) -> str:
    context_id = f"sketch-{uuid.uuid4().hex[:8]}"
    surface_id = "sketch-surface"

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

        # Placeholder block with a PINNED id, same lesson as
        # a2a_demo_composition.py: an id that was never wired as a child
        # of the root sits in derived state correctly (proven in
        # tests/test_agent_sketchpad.py) but never reaches the rendered
        # tree at all unless it was already a real child from the start.
        create_msg = emit_surface({
            "title": "Agent Sketchpad — Sunrise (Real A2A, Real Atom)",
            "blocks": [
                {"type": "body", "text": "The artist agent is about to begin...",
                 "id": "status_line"},
                {"type": "agent_sketchpad", "id": "sketch",
                 "viewBox": "0 0 400 200", "strokes": []},
            ],
        }, surface_id=surface_id)
        await _send(client, context_id, "sketch-orch", [create_msg])

        strokes = []
        for i, (name, element) in enumerate(SKETCH_STAGES):
            strokes.append({"element": element, "label": name})
            upd = update_components(surface_id, [
                {"id": "sketch", "component": "agent_sketchpad",
                 "viewBox": "0 0 400 200", "strokes": list(strokes)}])
            await _send(client, context_id, f"sketch-stroke-{i}", [upd])
            print(f"[a2a_demo_sketch] drew stroke {i + 1}/{len(SKETCH_STAGES)}: {name}")
            time.sleep(pace_seconds)

    return render_url


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default="http://localhost:8091",
                    help="Base URL of a running a2a_counterpart service")
    ap.add_argument("--no-wait", action="store_true",
                    help="Don't pause for the demo page to be opened")
    ap.add_argument("--pace-seconds", type=float, default=1.5,
                    help="Real delay between strokes, so a human watching "
                         "the /demo page can see each one land distinctly "
                         "(on top of the SSE endpoint's own short visual "
                         "pacing) -- default 1.5s")
    args = ap.parse_args()

    def wait_for_open():
        if args.no_wait:
            return
        input("Press Enter once the LIVE demo page above is open in a browser... ")

    render_url = asyncio.run(run(args.url.rstrip("/"), wait_for_open, args.pace_seconds))
    print()
    print("Static snapshot (reload to see the finished picture):")
    print(f"  {render_url}")


if __name__ == "__main__":
    main()
