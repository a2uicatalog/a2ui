"""premium-render-api -- the lightweight (no bpy) Cloud Run SERVICE that triggers a real
brick-premium-render Cloud Run JOB execution and reports back its status, matching this project's own
established pattern for "second containerized service, same repo" (a2a_counterpart/). Deliberately a
SEPARATE service from cloud-run-renderer (that one is --no-allow-unauthenticated, an anonymous browser
structurally can't call it; its gunicorn worker timeout is 60s, far shorter than a Cycles render).

Design, confirmed against the REAL Cloud Run Admin API v2 REST shape live (2026-10-01, not assumed):
  - POST .../jobs/{job}:run returns a long-running-operation whose metadata.name embeds the real execution
    resource path; the execution's own short name is the LAST path segment.
  - GET .../jobs/{job}/executions/{execution} returns a `conditions` array of {type, state, ...} -- the
    `Completed` entry's `state` is `CONDITION_SUCCEEDED` / `CONDITION_FAILED` when done, something else
    (CONDITION_RECONCILING/CONDITION_PENDING) while still running. NOT the `status: "True"` shape gcloud's
    own `--format=yaml` CLI output shows -- that's a CLI-side translation, not the raw API's real shape;
    confirmed live by calling the REST endpoint directly, not by trusting the CLI's own display format.

Stateless by design (no database, no in-memory job table -- a Cloud Run Service can have multiple instances
with no sticky session, so any in-process state would be unreliable anyway, and this is explicitly NOT the
scale that needs a real job-tracking store, see the plan's own "out of scope for v1" section): the GCS output
prefix is a UUID generated HERE at trigger time (before the real Cloud Run execution name is even known) and
handed back to the client alongside the execution name; the client passes BOTH back on every /status poll.

The partsModel BOM itself is staged to GCS (`renders/<uuid>/input.json`) and the Job is handed only that path
via env var -- NOT base64-embedded directly into the Admin API's containerOverrides.env, which is what the
original v1 implementation did. Found live 2026-10-01: Cloud Run Jobs caps total env var size at 32KiB: a
real, complete kit (1798 parts, H175) base64-encodes to ~87.5KB, well past that ceiling, and the Admin API
rejected the jobs.run call with a 400 the first time a real (not test-slice) BOM was tried. GCS staging has no
such ceiling. Requires this service's own SA to hold write (not just read) access on the output bucket --
upgraded from roles/storage.objectViewer to roles/storage.objectAdmin, still scoped to this one bucket only.
"""
import collections
import json
import os
import time
import uuid

from flask import Flask, jsonify, request
import google.auth
import google.auth.transport.requests

PROJECT = os.environ.get("GCP_PROJECT", "artful-patrol-502116-b7")
REGION = os.environ.get("GCP_REGION", "europe-west1")
JOB_NAME = os.environ.get("RENDER_JOB_NAME", "brick-premium-render")
OUT_BUCKET = os.environ.get("OUT_GCS_BUCKET", "brick-premium-renders")
RUN_API_BASE = f"https://run.googleapis.com/v2/projects/{PROJECT}/locations/{REGION}"

SIGNED_URL_TTL_SECONDS = 7 * 24 * 3600  # 7 days -- see the plan's own reasoning (a premium render is a
                                          # deliberate asset a user may revisit, longer than the printer's 48h
                                          # transient-chat-image TTL)

MAX_PARTS_MODEL_ROWS = 2000  # a real, scoped cap -- prevents a pathological BOM from exploding Job cost;
                               # the live catalogue's own largest kits cap well under this today

MAX_RENDERS_PER_HOUR = 10  # see the plan's own reasoning: a Cycles Job is genuinely several minutes of
                             # multi-core CPU, real dollars per click -- categorically different from
                             # cloud-run-renderer's own MAX_RENDERS_PER_MINUTE (sub-second Chromium shots),
                             # so a much lower PER-HOUR ceiling, not a per-minute one, mirroring that
                             # service's _BoundedCache STYLE without copying its number. Per-INSTANCE, same
                             # known limitation as cloud-run-renderer's own _BoundedCache (a Cloud Run
                             # Service can scale to multiple instances with no shared state) -- an accepted
                             # trade-off already established by that precedent, not a new gap introduced here.

app = Flask(__name__)

_request_times = collections.deque()


def _rate_limited():
    now = time.time()
    while _request_times and now - _request_times[0] > 3600:
        _request_times.popleft()
    if len(_request_times) >= MAX_RENDERS_PER_HOUR:
        return True
    _request_times.append(now)
    return False


def _access_token():
    credentials, _ = google.auth.default()
    credentials.refresh(google.auth.transport.requests.Request())
    return credentials, credentials.token


def _authed_post(url, body):
    import requests
    _, token = _access_token()
    resp = requests.post(url, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                          json=body, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _authed_get(url):
    import requests
    _, token = _access_token()
    resp = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _validate_parts_model(body):
    parts_model = body.get("partsModel") if isinstance(body, dict) else None
    if not isinstance(parts_model, list) or not parts_model:
        return None, "partsModel must be a non-empty array"
    if len(parts_model) > MAX_PARTS_MODEL_ROWS:
        return None, f"partsModel too large (max {MAX_PARTS_MODEL_ROWS} rows)"
    for row in parts_model:
        ok = (isinstance(row, list) and len(row) >= 6) or (isinstance(row, dict) and "p" in row)
        if not ok:
            return None, "malformed partsModel row"
    return parts_model, None


def _cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp


@app.after_request
def _add_cors(resp):
    return _cors(resp)


@app.route("/trigger", methods=["POST", "OPTIONS"])
def trigger():
    if request.method == "OPTIONS":
        return _cors(app.make_default_options_response())

    body = request.get_json(silent=True) or {}
    parts_model, err = _validate_parts_model(body)
    if err:
        return jsonify({"ok": False, "error": err}), 400

    if _rate_limited():
        return jsonify({"ok": False, "error": "Too many premium renders requested recently -- try again later."}), 429

    render_id = str(uuid.uuid4())
    input_path = f"renders/{render_id}/input.json"

    try:
        from google.cloud import storage
        credentials, _ = _access_token()
        client = storage.Client(credentials=credentials, project=PROJECT)
        bucket = client.bucket(OUT_BUCKET)
        bucket.blob(input_path).upload_from_string(
            json.dumps({"partsModel": parts_model}), content_type="application/json")
    except Exception as e:  # noqa: BLE001
        return jsonify({"ok": False, "error": f"could not stage render input: {e}"}), 502

    env = [
        {"name": "PARTS_MODEL_GCS_PATH", "value": input_path},
        {"name": "OUT_GCS_BUCKET", "value": OUT_BUCKET},
        {"name": "OUT_GCS_PREFIX", "value": f"renders/{render_id}"},
    ]
    run_body = {"overrides": {"containerOverrides": [{"env": env}], "taskCount": 1}}

    try:
        op = _authed_post(f"{RUN_API_BASE}/jobs/{JOB_NAME}:run", run_body)
    except Exception as e:  # noqa: BLE001 -- report to the client, don't leak a stack trace
        return jsonify({"ok": False, "error": f"could not start render: {e}"}), 502

    execution_path = op.get("metadata", {}).get("name", "")
    execution_name = execution_path.rsplit("/", 1)[-1]
    if not execution_name:
        return jsonify({"ok": False, "error": "render job did not return an execution name"}), 502

    return jsonify({"ok": True, "jobId": execution_name, "renderId": render_id}), 202


@app.route("/status", methods=["GET"])
def status():
    job_id = request.args.get("jobId", "")
    render_id = request.args.get("renderId", "")
    if not job_id or not render_id:
        return jsonify({"ok": False, "error": "jobId and renderId are required"}), 400

    try:
        execution = _authed_get(f"{RUN_API_BASE}/jobs/{JOB_NAME}/executions/{job_id}")
    except Exception as e:  # noqa: BLE001
        return jsonify({"ok": False, "error": f"could not check render status: {e}"}), 502

    completed = next((c for c in execution.get("conditions", []) if c.get("type") == "Completed"), None)
    state = completed.get("state") if completed else None

    if state not in ("CONDITION_SUCCEEDED", "CONDITION_FAILED"):
        return jsonify({"ok": True, "state": "running"})

    if state == "CONDITION_FAILED":
        return jsonify({"ok": False, "state": "failed", "error": "render failed"})

    # CONDITION_SUCCEEDED -- mint signed URLs for the two real output files. Signing lives HERE, not in the
    # render Job itself (see entrypoint.py's own module docstring): this service's SA is the one granted
    # roles/iam.serviceAccountTokenCreator on itself, the Job's SA stays narrowly scoped to
    # roles/storage.objectAdmin on the bucket only.
    from google.cloud import storage
    credentials, token = _access_token()
    client = storage.Client(credentials=credentials, project=PROJECT)
    bucket = client.bucket(OUT_BUCKET)

    # credentials.service_account_email only exists on genuine service-account-flavoured credentials (what
    # this service's own deployed identity will be) -- plain user OAuth credentials (e.g. local `gcloud auth
    # application-default login` during dev) lack the attribute entirely, confirmed live 2026-10-01
    # (AttributeError during local container testing). SIGNING_SA env var lets local/dev testing supply the
    # real SA email explicitly without that account needing to BE the ambient identity.
    sa_email = getattr(credentials, "service_account_email", None) or os.environ.get("SIGNING_SA")
    if not sa_email:
        return jsonify({"ok": False, "error": "server misconfigured: no service account identity for signing"}), 500

    urls = {}
    for name, key in (("hero.png", "heroUrl"), ("turntable.mp4", "turntableUrl")):
        blob = bucket.blob(f"renders/{render_id}/{name}")
        if not blob.exists(client=client):
            continue
        urls[key] = blob.generate_signed_url(
            version="v4", expiration=SIGNED_URL_TTL_SECONDS, method="GET",
            service_account_email=sa_email, access_token=token,
        )

    if not urls:
        return jsonify({"ok": False, "state": "failed", "error": "render reported success but produced no output"})

    return jsonify({"ok": True, "state": "done", **urls})


@app.route("/healthz", methods=["GET"])
def healthz():
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
