#!/usr/bin/env python3
"""a2a_live_probe.py — sends ONE real A2UI v1.0 surface through a real A2A
round trip against a running a2a_counterpart service, over an actual
network connection (unlike tests/test_a2a_counterpart.py's in-process
httpx.ASGITransport version). Same real a2a-sdk client, same
emit_surface()/wrap_messages_for_sdk() path -- this only changes WHERE the
server is running.

Works against two targets, on purpose, so the same script proves the round
trip locally before ever touching billed Cloud Run infra:

  1. Localhost, no auth: run the service yourself first --
       uvicorn a2a_counterpart.main:app --port 8080
     then:
       python3 scripts/a2a_live_probe.py --url http://localhost:8080

  2. The deployed, IAM-gated Cloud Run URL (--no-allow-unauthenticated,
     see ops/project-ops.yaml's a2a-counterpart-deploy) -- mints a real ID
     token via this machine's own gcloud ADC identity, same pattern
     scripts/printer.py and a2ui-ge-agent/main.py already use for calling
     cloud-run-renderer:
       python3 scripts/a2a_live_probe.py --url https://a2a-counterpart-echo-...run.app

Auth is inferred from the URL: localhost/127.0.0.1 gets no Authorization
header at all (there is nothing to authenticate to); anything else mints a
real ID token audienced to that exact URL. This is deliberately the SAME
example payload as tests/test_a2a_counterpart.py's single-message test, so
a failure here that a green in-process test didn't catch is unambiguously
about the NETWORK/DEPLOYMENT, not the message logic.
"""
import argparse
import asyncio
import json
import os
import sys
from urllib.parse import urlparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import httpx
from a2a.client import A2ACardResolver, ClientConfig, ClientFactory
from a2a.types import DataPart, Message, Part, Role

from renderers.a2a_extension import (
    A2A_EXTENSION_URI, unwrap_sdk_data_part, wrap_messages_for_sdk,
)
from renderers.a2ui_v1 import emit_surface


def _is_local(url: str) -> bool:
    host = urlparse(url).hostname or ""
    return host in ("localhost", "127.0.0.1", "::1")


def _id_token(audience: str) -> str:
    import google.auth.transport.requests
    import google.oauth2.id_token
    return google.oauth2.id_token.fetch_id_token(
        google.auth.transport.requests.Request(), audience)


async def probe(url: str) -> bool:
    headers = {}
    if _is_local(url):
        print(f"[a2a_live_probe] {url} looks local — sending unauthenticated")
    else:
        print(f"[a2a_live_probe] {url} looks remote — minting a real ID token (gcloud ADC)")
        headers["Authorization"] = f"Bearer {_id_token(url)}"

    surface = emit_surface({
        "title": "Live Probe", "theme": "dark",
        "blocks": [{"type": "body", "text": "hello over the real network"}],
    })

    async with httpx.AsyncClient(base_url=url, headers=headers, timeout=30) as hc:
        card = await A2ACardResolver(hc, url).get_agent_card()
        print(f"[a2a_live_probe] AgentCard resolved: {card.name!r}")
        uris = [ext.uri for ext in (card.capabilities.extensions or [])]
        if A2A_EXTENSION_URI not in uris:
            print(f"[a2a_live_probe] FAIL — AgentCard does not advertise {A2A_EXTENSION_URI}")
            return False

        client = ClientFactory(ClientConfig(httpx_client=hc, streaming=False)).create(
            card, extensions=[A2A_EXTENSION_URI])
        msg = Message(role=Role.user, message_id="live-probe-1",
                      parts=[Part(root=DataPart(**wrap_messages_for_sdk([surface])))])

        got = None
        async for event in client.send_message(msg, extensions=[A2A_EXTENSION_URI]):
            got = event

        if not isinstance(got, Message):
            print(f"[a2a_live_probe] FAIL — expected a bare Message reply, got {type(got)}")
            return False
        data_part = next(
            (getattr(p, "root", p) for p in got.parts
             if isinstance(getattr(p, "root", p), DataPart)),
            None)
        if data_part is None:
            print("[a2a_live_probe] FAIL — reply carried no DataPart")
            return False

        echoed = unwrap_sdk_data_part(data_part.model_dump())
        if echoed != [surface]:
            print("[a2a_live_probe] FAIL — echoed message does not match what was sent")
            print("  sent:  ", json.dumps(surface)[:300])
            print("  echoed:", json.dumps(echoed)[:300])
            return False

        print("[a2a_live_probe] PASS — real A2UI v1.0 surface round-tripped byte-identical "
              f"over a real network connection to {url}")
        return True


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", required=True,
                    help="Base URL of a running a2a_counterpart service "
                         "(http://localhost:8080 or a deployed Cloud Run URL)")
    args = ap.parse_args()
    ok = asyncio.run(probe(args.url.rstrip("/")))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
