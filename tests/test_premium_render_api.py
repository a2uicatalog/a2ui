"""Tests for premium-render-api/server.py -- the lightweight trigger+status+signing Cloud Run Service in
front of the brick-premium-render Job. Real end-to-end verification (a real trigger, a real multi-minute
Cycles render, a real signed URL that actually downloads) was already done against the live deployed service
2026-10-01 before this file was written -- these are the PURE-LOGIC unit tests that belong in CI (no GCP
credentials needed), covering validation/rate-limiting/response-shape handling with the real Cloud Run Admin
API and GCS calls mocked out, matching tests/test_cloud_run_renderer.py's own established pattern for this
repo's other Cloud Run service.

Needs this subproject's OWN dependencies (premium-render-api/requirements.txt: flask, google-auth,
google-cloud-storage), which the base repo's tests/ suite doesn't otherwise require -- skipped entirely if
not installed, same mechanism as test_cloud_run_renderer.py.
"""
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

PREMIUM_RENDER_API = Path(__file__).parent.parent / "premium-render-api"
sys.path.insert(0, str(PREMIUM_RENDER_API))

pytest.importorskip("flask", reason="premium-render-api's own dependency, not the base repo's")
pytest.importorskip("google.auth", reason="premium-render-api's own dependency, not the base repo's")

import server as pra_server  # noqa: E402


@pytest.fixture()
def client(monkeypatch):
    # Never let a test accidentally make a real network/GCP call -- every test that needs _authed_post/
    # _authed_get/_access_token monkeypatches them explicitly; this fixture's own default raises loudly if
    # one is reached unexpectedly, instead of a test silently trying real network access.
    def _unexpected(*a, **k):
        raise AssertionError("real network call attempted in a unit test -- mock it explicitly")
    monkeypatch.setattr(pra_server, "_authed_post", _unexpected)
    monkeypatch.setattr(pra_server, "_authed_get", _unexpected)
    monkeypatch.setattr(pra_server, "_access_token", _unexpected)
    pra_server._request_times.clear()
    return pra_server.app.test_client()


@pytest.fixture()
def fake_storage(monkeypatch):
    # /trigger stages the BOM to GCS before calling the Admin API -- stub out google.cloud.storage so tests
    # don't need real credentials/network, and record what was uploaded for assertions.
    uploads = {}

    class _FakeBlob:
        def __init__(self, name):
            self.name = name

        def upload_from_string(self, data, content_type=None):
            uploads[self.name] = (data, content_type)

    class _FakeBucket:
        def blob(self, name):
            return _FakeBlob(name)

    class _FakeClient:
        def __init__(self, **kw):
            pass

        def bucket(self, name):
            return _FakeBucket()

    monkeypatch.setitem(sys.modules, "google.cloud.storage", MagicMock(Client=_FakeClient))
    monkeypatch.setattr(pra_server, "_access_token", lambda: (MagicMock(), "fake-token"))
    return uploads


def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.get_json()["ok"] is True


def test_trigger_rejects_missing_parts_model(client):
    r = client.post("/trigger", json={})
    assert r.status_code == 400
    assert r.get_json()["ok"] is False


def test_trigger_rejects_oversized_parts_model(client):
    rows = [["3001", 0, -24, 0, 0, 4]] * (pra_server.MAX_PARTS_MODEL_ROWS + 1)
    r = client.post("/trigger", json={"partsModel": rows})
    assert r.status_code == 400
    assert "too large" in r.get_json()["error"]


def test_trigger_rejects_malformed_row(client):
    r = client.post("/trigger", json={"partsModel": [["only", "five", "fields", "here", 0]]})
    assert r.status_code == 400


def test_trigger_calls_admin_api_and_returns_job_id(client, fake_storage, monkeypatch):
    calls = []

    def fake_authed_post(url, body):
        calls.append((url, body))
        return {"metadata": {"name": "projects/p/locations/r/jobs/j/executions/brick-premium-render-abc12"}}

    monkeypatch.setattr(pra_server, "_authed_post", fake_authed_post)
    r = client.post("/trigger", json={"partsModel": [["3001", 0, -24, 0, 0, 4]]})
    assert r.status_code == 202
    body = r.get_json()
    assert body["ok"] is True
    assert body["jobId"] == "brick-premium-render-abc12"
    assert body["renderId"]  # a real UUID was generated

    assert len(calls) == 1
    url, run_body = calls[0]
    assert url.endswith(f"/jobs/{pra_server.JOB_NAME}:run")
    env = {e["name"]: e["value"] for e in run_body["overrides"]["containerOverrides"][0]["env"]}
    assert env["OUT_GCS_PREFIX"] == f"renders/{body['renderId']}"
    assert env["PARTS_MODEL_GCS_PATH"] == f"renders/{body['renderId']}/input.json"
    assert run_body["overrides"]["taskCount"] == 1

    # the BOM was actually staged to GCS at the path handed to the Job
    uploaded_data, uploaded_content_type = fake_storage[env["PARTS_MODEL_GCS_PATH"]]
    assert json.loads(uploaded_data) == {"partsModel": [["3001", 0, -24, 0, 0, 4]]}
    assert uploaded_content_type == "application/json"


def test_trigger_rate_limited_after_max_per_hour(client, fake_storage, monkeypatch):
    monkeypatch.setattr(pra_server, "_authed_post", lambda url, body: {
        "metadata": {"name": "projects/p/locations/r/jobs/j/executions/x"}})
    for _ in range(pra_server.MAX_RENDERS_PER_HOUR):
        r = client.post("/trigger", json={"partsModel": [["3001", 0, -24, 0, 0, 4]]})
        assert r.status_code == 202
    r = client.post("/trigger", json={"partsModel": [["3001", 0, -24, 0, 0, 4]]})
    assert r.status_code == 429
    assert r.get_json()["ok"] is False


def test_trigger_reports_admin_api_failure_without_crashing(client, fake_storage, monkeypatch):
    def fake_authed_post(url, body):
        raise RuntimeError("simulated Admin API error")
    monkeypatch.setattr(pra_server, "_authed_post", fake_authed_post)
    r = client.post("/trigger", json={"partsModel": [["3001", 0, -24, 0, 0, 4]]})
    assert r.status_code == 502
    assert r.get_json()["ok"] is False


def test_trigger_reports_gcs_staging_failure_without_crashing(client, monkeypatch):
    class _FailingClient:
        def __init__(self, **kw):
            pass

        def bucket(self, name):
            raise RuntimeError("simulated GCS error")

    monkeypatch.setitem(sys.modules, "google.cloud.storage", MagicMock(Client=_FailingClient))
    monkeypatch.setattr(pra_server, "_access_token", lambda: (MagicMock(), "fake-token"))
    r = client.post("/trigger", json={"partsModel": [["3001", 0, -24, 0, 0, 4]]})
    assert r.status_code == 502
    assert r.get_json()["ok"] is False


def test_status_requires_job_id_and_render_id(client):
    r = client.get("/status")
    assert r.status_code == 400


def test_status_reports_running_for_non_terminal_state(client, monkeypatch):
    # Real condition shape confirmed live against the actual Cloud Run Admin API v2 REST endpoint
    # (2026-10-01, NOT the gcloud CLI's own translated --format=yaml shape -- see server.py's own module
    # docstring): conditions[].state, not conditions[].status.
    monkeypatch.setattr(pra_server, "_authed_get", lambda url: {
        "conditions": [{"type": "Completed", "state": "CONDITION_RECONCILING"}]})
    r = client.get("/status?jobId=x&renderId=y")
    assert r.get_json() == {"ok": True, "state": "running"}


def test_status_reports_failed(client, monkeypatch):
    monkeypatch.setattr(pra_server, "_authed_get", lambda url: {
        "conditions": [{"type": "Completed", "state": "CONDITION_FAILED"}]})
    r = client.get("/status?jobId=x&renderId=y")
    body = r.get_json()
    assert body["ok"] is False
    assert body["state"] == "failed"


def test_status_mints_signed_urls_on_success(client, monkeypatch):
    monkeypatch.setattr(pra_server, "_authed_get", lambda url: {
        "conditions": [{"type": "Completed", "state": "CONDITION_SUCCEEDED"}]})

    fake_credentials = MagicMock()
    fake_credentials.service_account_email = "premium-render-api@artful-patrol-502116-b7.iam.gserviceaccount.com"
    monkeypatch.setattr(pra_server, "_access_token", lambda: (fake_credentials, "fake-token"))

    fake_blob = MagicMock()
    fake_blob.exists.return_value = True
    fake_blob.generate_signed_url.return_value = "https://storage.googleapis.com/signed-url-here"
    fake_bucket = MagicMock()
    fake_bucket.blob.return_value = fake_blob
    fake_client = MagicMock()
    fake_client.bucket.return_value = fake_bucket

    monkeypatch.setitem(sys.modules, "google.cloud.storage", MagicMock(Client=lambda **kw: fake_client))

    r = client.get("/status?jobId=x&renderId=some-uuid")
    body = r.get_json()
    assert body["ok"] is True
    assert body["state"] == "done"
    assert body["heroUrl"] == "https://storage.googleapis.com/signed-url-here"
    assert body["turntableUrl"] == "https://storage.googleapis.com/signed-url-here"
    fake_bucket.blob.assert_any_call("renders/some-uuid/hero.png")
    fake_bucket.blob.assert_any_call("renders/some-uuid/turntable.mp4")


def test_cors_headers_present(client, fake_storage, monkeypatch):
    monkeypatch.setattr(pra_server, "_authed_post", lambda url, body: {
        "metadata": {"name": "projects/p/locations/r/jobs/j/executions/x"}})
    r = client.post("/trigger", json={"partsModel": [["3001", 0, -24, 0, 0, 4]]})
    assert r.headers.get("Access-Control-Allow-Origin") == "*"
