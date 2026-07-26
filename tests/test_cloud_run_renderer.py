"""Tests for cloud-run-renderer/server.py -- added after the 2026-07-26
roast panel flagged zero automated coverage existed for /render,
/render.png, /render.gif, or /chat (every prior verification was a manual
curl against a manually-started process, gone the moment the shell
closed -- see cloud-run-renderer/ROAST-2026-07-26.md).

Extended the same day to cover the cost/DoS hardening pass: HMAC-signed
render tokens, payload-size bounds, and the render-rate limiter.

Needs this subproject's OWN dependencies (cloud-run-renderer/requirements.txt:
Playwright/Chromium, Pillow in particular), which the base repo's tests/
suite doesn't otherwise require -- skipped entirely if they're not
installed, so this never breaks a CI job that only installs the base
repo's own dependencies.
"""
import sys
from pathlib import Path

import pytest

CLOUD_RUN_RENDERER = Path(__file__).parent.parent / "cloud-run-renderer"
sys.path.insert(0, str(CLOUD_RUN_RENDERER))

pytest.importorskip("playwright", reason="cloud-run-renderer's own dependency, not the base repo's")
pytest.importorskip("PIL", reason="cloud-run-renderer's own dependency, not the base repo's")

import server as crr_server  # noqa: E402

# Use the server's OWN encode functions rather than a duplicated local
# copy -- a hand-rolled copy here silently drifted out of sync with the
# real wire format once HMAC signing was added to the real functions
# (caught while extending this exact file, 2026-07-26).
_encode_block = crr_server._encode_block_qs
_encode_deck = crr_server._encode_deck_qs

SLA_BLOCK = {"type": "gauge_sla", "value": 82, "max_value": 100, "label": "P1 Incident SLA"}


@pytest.fixture
def client():
    crr_server.app.config["TESTING"] = True
    return crr_server.app.test_client()


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """The rate limiter is process-global state (a module-level deque) --
    without resetting it, tests run in sequence would eventually trip
    MAX_RENDERS_PER_MINUTE against each other, which is a test-ordering
    artifact, not a real finding."""
    crr_server._render_timestamps.clear()
    yield
    crr_server._render_timestamps.clear()


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


def test_render_post_rejects_oversized_block(client):
    huge_block = {"type": "gauge_sla", "value": 82, "padding": "x" * crr_server.MAX_BLOCK_JSON_BYTES}
    resp = client.post("/render", json={"block": huge_block})
    assert resp.status_code == 400
    assert "too large" in resp.get_json()["error"]


def test_render_png_get_round_trip(client):
    b = _encode_block(SLA_BLOCK)
    resp = client.get(f"/render.png?b={b}")
    assert resp.status_code == 200
    assert resp.data.startswith(b"\x89PNG")


def test_render_png_rejects_oversized_width(client):
    b = _encode_block(SLA_BLOCK, width=50000)
    resp = client.get(f"/render.png?b={b}")
    assert resp.status_code == 400
    assert b"width must be between" in resp.data


def test_render_png_rejects_forged_token(client):
    b = _encode_block(SLA_BLOCK)
    token, _, _sig = b.rpartition(".")
    forged = f"{token}.0000000000000000"
    resp = client.get(f"/render.png?b={forged}")
    assert resp.status_code == 403
    assert b"invalid or forged" in resp.data


def test_render_png_rejects_tampered_payload(client):
    """Same signature, different payload -- the classic tamper attempt:
    take a validly-signed token for one block and splice in different
    base64 content, keeping the original signature. Must still fail."""
    b1 = _encode_block(SLA_BLOCK, width=620)
    b2 = _encode_block(SLA_BLOCK, width=621)
    tampered = f"{b2.rpartition('.')[0]}.{b1.rpartition('.')[2]}"
    resp = client.get(f"/render.png?b={tampered}")
    assert resp.status_code == 403


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
    assert resp.status_code == 400
    assert b"deck too large" in resp.data


def test_render_rate_limit_enforced(client):
    """Fill the rate-limit window directly (bypassing real renders --
    this test is about the limiter's own bookkeeping, not re-proving
    Chromium works) then confirm the NEXT real render attempt is refused."""
    import time
    now = time.time()
    for _ in range(crr_server.MAX_RENDERS_PER_MINUTE):
        crr_server._render_timestamps.append(now)
    resp = client.post("/render", json={"block": {**SLA_BLOCK, "value": 999}})
    assert resp.status_code == 429
    assert "rate limit" in resp.get_json()["error"]


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


def test_chat_generated_url_is_honored_by_render_png(client):
    """The whole point of signing: a URL /chat itself produced must still
    work end to end through render.png, not just decode without error."""
    resp = client.post("/chat", json={"type": "MESSAGE", "message": {"text": "sla 82"}})
    img_url = resp.get_json()["cardsV2"][0]["card"]["sections"][0]["widgets"][0]["image"]["imageUrl"]
    query_string = img_url.split("/render.png?", 1)[1]
    png_resp = client.get(f"/render.png?{query_string}")
    assert png_resp.status_code == 200
    assert png_resp.data.startswith(b"\x89PNG")
