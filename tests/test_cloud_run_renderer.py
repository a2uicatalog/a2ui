"""Tests for cloud-run-renderer/server.py -- added after the 2026-07-26
roast panel flagged zero automated coverage existed for /render,
/render.png, /render.gif, or /chat (every prior verification was a manual
curl against a manually-started process, gone the moment the shell
closed -- see cloud-run-renderer/ROAST-2026-07-26.md).

Needs this subproject's OWN dependencies (cloud-run-renderer/requirements.txt:
Playwright/Chromium, Pillow in particular), which the base repo's tests/
suite doesn't otherwise require -- skipped entirely if they're not
installed, so this never breaks a CI job that only installs the base
repo's own dependencies.
"""
import base64
import gzip
import json
import sys
from pathlib import Path

import pytest

CLOUD_RUN_RENDERER = Path(__file__).parent.parent / "cloud-run-renderer"
sys.path.insert(0, str(CLOUD_RUN_RENDERER))

pytest.importorskip("playwright", reason="cloud-run-renderer's own dependency, not the base repo's")
pytest.importorskip("PIL", reason="cloud-run-renderer's own dependency, not the base repo's")

import server as crr_server  # noqa: E402


def _encode_block(block, width=620):
    payload = json.dumps({"block": block, "width": width}, separators=(",", ":")).encode()
    compressed = gzip.compress(payload, compresslevel=9, mtime=0)
    return base64.urlsafe_b64encode(compressed).decode("ascii").rstrip("=")


def _encode_deck(cards, duration_ms=1000):
    blocks = [{"block": c["block"], "width": c.get("width", 620)} for c in cards]
    payload = json.dumps({"blocks": blocks, "duration_ms": duration_ms}, separators=(",", ":")).encode()
    compressed = gzip.compress(payload, compresslevel=9, mtime=0)
    return base64.urlsafe_b64encode(compressed).decode("ascii").rstrip("=")


SLA_BLOCK = {"type": "gauge_sla", "value": 82, "max_value": 100, "label": "P1 Incident SLA"}


@pytest.fixture
def client():
    crr_server.app.config["TESTING"] = True
    return crr_server.app.test_client()


def test_status(client):
    resp = client.get("/status")
    assert resp.status_code == 200
    assert resp.get_json() == {"ok": True}


def test_render_post_returns_real_png(client):
    resp = client.post("/render", json={"block": SLA_BLOCK})
    assert resp.status_code == 200
    assert resp.data.startswith(b"\x89PNG")


def test_render_post_rejects_oversized_width(client):
    resp = client.post("/render", json={"block": SLA_BLOCK, "width": 999999})
    assert resp.status_code == 400
    assert "width must be between" in resp.get_json()["error"]


def test_render_post_rejects_unknown_atom(client):
    resp = client.post("/render", json={"block": {"type": "not_a_real_atom"}})
    assert resp.status_code == 400


def test_render_png_get_round_trip(client):
    b = _encode_block(SLA_BLOCK)
    resp = client.get(f"/render.png?b={b}")
    assert resp.status_code == 200
    assert resp.data.startswith(b"\x89PNG")


def test_render_png_rejects_oversized_width(client):
    b = _encode_block(SLA_BLOCK, width=50000)
    resp = client.get(f"/render.png?b={b}")
    assert resp.status_code == 502
    assert b"width must be between" in resp.data


def test_render_gif_get_round_trip(client):
    b = _encode_deck([{"block": SLA_BLOCK, "width": 620}])
    resp = client.get(f"/render.gif?b={b}")
    assert resp.status_code == 200
    assert resp.data[:6] in (b"GIF87a", b"GIF89a")


def test_render_gif_rejects_oversized_deck(client):
    cards = [{"block": {**SLA_BLOCK, "value": i}, "width": 620}
             for i in range(crr_server.MAX_DECK_BLOCKS + 1)]
    b = _encode_deck(cards)
    resp = client.get(f"/render.gif?b={b}")
    assert resp.status_code == 502
    assert b"deck too large" in resp.data


def test_chat_message_returns_self_referencing_image_url(client):
    resp = client.post("/chat", json={"type": "MESSAGE", "message": {"text": "sla 82"}})
    assert resp.status_code == 200
    body = resp.get_json()
    img_url = body["cardsV2"][0]["card"]["sections"][0]["widgets"][0]["image"]["imageUrl"]
    assert "/render.png?b=" in img_url
    # AGENT_BASE_URL isn't set in this test process, so this must fall back
    # to the request's own host, not the old hardcoded external default --
    # regression guard for the exact bug this session's change fixed.
    assert "a2ui-ge-agent" not in img_url


def test_chat_message_gif_variant_uses_render_gif(client):
    resp = client.post("/chat", json={"type": "MESSAGE", "message": {"text": "sla 82 gif"}})
    assert resp.status_code == 200
    body = resp.get_json()
    img_url = body["cardsV2"][0]["card"]["sections"][0]["widgets"][0]["image"]["imageUrl"]
    assert "/render.gif?b=" in img_url
