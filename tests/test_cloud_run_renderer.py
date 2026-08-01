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

# Flask is checked FIRST and by the same mechanism as the other two: without
# it, `import server` below raises at COLLECTION time, which pytest reports as
# an error that aborts the whole run -- not as a skip. That is what happened in
# the base repo's own environment (found 2026-08-01), so the guard this file's
# docstring promises was not actually working.
pytest.importorskip("flask", reason="cloud-run-renderer's own dependency, not the base repo's")
pytest.importorskip("playwright", reason="cloud-run-renderer's own dependency, not the base repo's")
pytest.importorskip("PIL", reason="cloud-run-renderer's own dependency, not the base repo's")

from flask.testing import FlaskClient  # noqa: E402
import server as crr_server  # noqa: E402

# Use the server's OWN encode functions rather than a duplicated local
# copy -- a hand-rolled copy here silently drifted out of sync with the
# real wire format once HMAC signing was added to the real functions
# (caught while extending this exact file, 2026-07-26).
_encode_block = crr_server._encode_block_qs
_encode_deck = crr_server._encode_deck_qs

SLA_BLOCK = {"type": "gauge_sla", "value": 82, "max_value": 100, "label": "P1 Incident SLA"}


TEST_KEY = "test-render-signing-key"


@pytest.fixture(autouse=True)
def _signing_key(monkeypatch):
    """Pin the signing key instead of letting the module's random per-process
    fallback stand. Every test then signs and verifies against a known value,
    and the X-Render-Token the client fixture sends is the same one the guard
    checks."""
    monkeypatch.setattr(crr_server, "RENDER_SIGNING_KEY", TEST_KEY)


class _AuthedClient(FlaskClient):
    """Sends X-Render-Token on every request, so the existing behavior tests
    stay about behavior. The guard itself is covered explicitly by the
    test_auth_* tests below, which use a raw client."""

    def open(self, *args, **kwargs):
        headers = dict(kwargs.pop("headers", None) or {})
        headers.setdefault("X-Render-Token", TEST_KEY)
        return super().open(*args, headers=headers, **kwargs)


@pytest.fixture
def client(monkeypatch):
    # /chat authenticates a bearer token that only Google Chat can sign, so no
    # local test can produce a valid one. Stubbing the check keeps the /chat
    # BEHAVIOR tests (card shape, image URLs) meaningful; the check's own
    # fail-closed behavior is asserted separately in test_auth_chat_*.
    monkeypatch.setattr(crr_server, "_require_chat_caller", lambda: None)
    crr_server.app.config["TESTING"] = True
    crr_server.app.test_client_class = _AuthedClient
    try:
        return crr_server.app.test_client()
    finally:
        crr_server.app.test_client_class = None


@pytest.fixture
def anon_client():
    """No X-Render-Token, no /chat stub -- for asserting the guards reject."""
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


# ---------------------------------------------------------------------------
# Route authentication (added 2026-08-01).
#
# These exist because the service has to be deployable
# --allow-unauthenticated for Google Chat's image widget to fetch a rendered
# card, and Cloud Run's public/private switch is per SERVICE, not per route.
# Before this pass, making /render.png reachable also published POST /render:
# an open headless-Chromium renderer. Each assertion below is one way that
# could come back.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("method,path,body", [
    ("post", "/render", {"block": SLA_BLOCK}),
    ("post", "/render-deck", {"blocks": [{"block": SLA_BLOCK, "width": 620}]}),
    ("get", "/deck?text=sla+82", None),
])
def test_auth_costly_routes_reject_without_token(anon_client, method, path, body):
    call = getattr(anon_client, method)
    resp = call(path, json=body) if body is not None else call(path)
    assert resp.status_code == 403
    assert "X-Render-Token" in resp.get_json()["error"]


def test_auth_rejects_wrong_token(anon_client):
    resp = anon_client.post("/render", json={"block": SLA_BLOCK},
                            headers={"X-Render-Token": "not-the-key"})
    assert resp.status_code == 403


def test_auth_ignores_query_string_token(anon_client):
    """No ?t= fallback, deliberately: Cloud Run logs full query strings, and
    this key also signs the image HMACs -- leaking it into log storage would
    let an attacker mint valid /render.png URLs too."""
    resp = anon_client.post(f"/render?t={TEST_KEY}", json={"block": SLA_BLOCK})
    assert resp.status_code == 403


def test_auth_status_stays_open(anon_client):
    """The one route that must answer without credentials -- it is a liveness
    probe returning a constant, and gating it breaks health checking."""
    assert anon_client.get("/status").status_code == 200


def test_auth_chat_fails_closed_without_audience(anon_client, monkeypatch):
    """An unset security variable must mean CLOSED, not 'skip the check'.
    The guard-only-if-configured shape is how a gated service silently ends
    up open."""
    monkeypatch.setattr(crr_server, "CHAT_AUDIENCE", "")
    resp = anon_client.post("/chat", json={"type": "MESSAGE",
                                           "message": {"text": "sla 82"}})
    assert resp.status_code == 403
    assert "CHAT_AUDIENCE" in resp.get_json()["error"]


def test_auth_chat_rejects_missing_bearer(anon_client, monkeypatch):
    monkeypatch.setattr(crr_server, "CHAT_AUDIENCE", "https://example.invalid/chat")
    resp = anon_client.post("/chat", json={"type": "MESSAGE",
                                           "message": {"text": "sla 82"}})
    assert resp.status_code == 403
    assert "bearer" in resp.get_json()["error"].lower()


def test_auth_chat_rejects_unverifiable_bearer(anon_client, monkeypatch):
    """A syntactically plausible token that Google did not sign must not pass,
    and the 403 must not explain WHY -- that is free reconnaissance."""
    monkeypatch.setattr(crr_server, "CHAT_AUDIENCE", "https://example.invalid/chat")
    resp = anon_client.post("/chat", json={"type": "MESSAGE",
                                           "message": {"text": "sla 82"}},
                            headers={"Authorization": "Bearer aaa.bbb.ccc"})
    assert resp.status_code == 403
    assert resp.get_json()["error"] == "invalid Chat bearer token"


def test_auth_render_png_needs_no_token_only_a_signature(anon_client):
    """The image GETs stay reachable without credentials -- Chat's widget
    fetch is anonymous by Google's design -- but only for a URL this service
    itself minted. Forged tokens are covered by
    test_render_png_rejects_forged_token; this asserts the other half: a
    legitimately signed URL works with no header at all."""
    b = _encode_block(SLA_BLOCK, width=200)
    resp = anon_client.get(f"/render.png?b={b}")
    assert resp.status_code != 403
