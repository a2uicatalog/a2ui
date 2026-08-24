"""Shared Vertex AI REST client — Express Mode (API key) or plain IAM,
whichever this deployment has configured.

Vendored verbatim from maison/vertex_rest.py (2026-08-24) -- that's the
ONE place this exact URL-shape/auth logic had already been gotten right
the hard way (see its own docstring for the real outage that proved it:
the plain-IAM URL shape 404s some models on some projects regardless of
credentials; only Express Mode's shape -- no project, no region in the
path, `x-goog-api-key` header instead of a bearer token -- reaches them).
Pure infrastructure, no a2uicatalog-specific logic, low drift risk unlike
this repo's own atom renderers -- kept as a plain copy rather than a
cross-repo import so this repo's own scripts (scripts/a2a_agent_sketch.py)
don't depend on maison's checkout existing at a relative path.

Vertex AI over REST rather than an SDK: the app already carries google-auth
for Drive/Sheets/Calendar and this is one signed POST. A whole SDK for that is
more surface to keep current, not less.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

DEFAULT_LOCATION = "europe-west1"       # co-located with Cloud Run and Firestore (eur3)


class NotConfigured(Exception):
    """Phrased for the person (or the log) reading it."""


def endpoint(model_name: str) -> str:
    """Two distinct URL shapes. Express Mode (MAISON_GEMINI_API_KEY set) has
    no project or region in the path at all; the plain-IAM path does, and
    404s a model Express Mode reaches fine — see this module's docstring.
    """
    if os.environ.get("MAISON_GEMINI_API_KEY"):
        return ("https://aiplatform.googleapis.com/v1beta1/publishers/google"
                "/models/{model}:generateContent").format(model=model_name)
    project = os.environ.get("MAISON_PROJECT")
    if not project:
        raise NotConfigured(
            "Needs MAISON_PROJECT set (or MAISON_GEMINI_API_KEY for Express Mode).")
    location = os.environ.get("MAISON_VERTEX_LOCATION", DEFAULT_LOCATION)
    return ("https://{loc}-aiplatform.googleapis.com/v1/projects/{proj}"
            "/locations/{loc}/publishers/google/models/{model}:generateContent"
            ).format(loc=location, proj=project, model=model_name)


def token() -> str:
    import google.auth
    import google.auth.transport.requests

    creds, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"])
    creds.refresh(google.auth.transport.requests.Request())
    return creds.token


def call(model_name: str, contents: List[Dict[str, Any]], *,
         system: Optional[str] = None,
         schema: Optional[Dict[str, Any]] = None,
         tools: Optional[List[Dict[str, Any]]] = None,
         tool_config: Optional[Dict[str, Any]] = None,
         temperature: float = 0.2,
         max_output_tokens: int = 1200,
         timeout: int = 45) -> Dict[str, Any]:
    """One `generateContent` call. Returns the FULL parsed response body
    (`{"candidates": [...], ...}`) rather than pre-extracting a part — a
    tool-calling turn's part holds a `functionCall`, a structured-output
    turn's holds `text` with a JSON string, and only the caller knows which
    it asked for. Use `first_part()` below to get at it safely.

    `schema` and `tools` are mutually meaningful but not mutually exclusive
    at the API level; callers pass whichever they need (nlp.py: schema only;
    daily_agent.py: tools only, no schema — a function-calling turn cannot
    also be constrained to a fixed JSON shape).
    """
    import urllib.error
    import urllib.request

    generation_config: Dict[str, Any] = {
        "temperature": temperature,
        "maxOutputTokens": max_output_tokens,
    }
    if schema is not None:
        generation_config["responseMimeType"] = "application/json"
        generation_config["responseSchema"] = schema

    body: Dict[str, Any] = {"contents": contents, "generationConfig": generation_config}
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}
    if tools:
        body["tools"] = tools
    if tool_config:
        # e.g. {"functionCallingConfig": {"mode": "ANY"}} — FORCES a function
        # call every turn, eliminating the model-answered-in-prose failure
        # class at the API level instead of merely prompting against it.
        body["toolConfig"] = tool_config

    api_key = os.environ.get("MAISON_GEMINI_API_KEY")
    # Express Mode authenticates by header, not a bearer token — token()
    # fetches Application Default Credentials, which this deployment may not
    # even have configured if it is running on the key alone.
    headers = ({"x-goog-api-key": api_key, "Content-Type": "application/json"}
              if api_key else
              {"Authorization": "Bearer %s" % token(),
               "Content-Type": "application/json"})
    req = urllib.request.Request(
        endpoint(model_name), method="POST",
        data=json.dumps(body).encode(),
        headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="ignore")[:200]
        if e.code == 403:
            raise NotConfigured(
                "Not allowed to call Vertex AI yet — the runtime service "
                "account needs roles/aiplatform.user (or set "
                "MAISON_GEMINI_API_KEY for Express Mode).")
        if e.code == 429:
            raise RateLimited("Gemini answered HTTP 429: %s" % detail)
        raise RuntimeError("Gemini answered HTTP %d: %s" % (e.code, detail))


class RateLimited(RuntimeError):
    """HTTP 429 from Vertex — quota pressure, not a real failure. Confirmed
    live, 2026-08-19, after several back-to-back daily-agent runs in one
    day: Express Mode's quota recovers on its own, so the caller should
    back off and retry rather than abort the whole run (which is what the
    generic RuntimeError below caused before this class existed)."""


class MalformedFunctionCall(RuntimeError):
    """The model attempted a tool call that failed Gemini's OWN validation
    (finishReason MALFORMED_FUNCTION_CALL) — confirmed live, 2026-08-17, on
    the daily agent's first real run. Worth one immediate retry before
    treating it as a real failure, the same "transient miss" reasoning
    agent.compose's own retry-once already uses (concepts.py:
    retry_resilience) — a caller that wants that behaviour catches this
    specifically; anything else raises the plain RuntimeError below, which
    is NOT worth retrying (a safety block or genuine refusal repeats).

    `payload` carries the full raw response so a caller can log it —
    diagnosing WHY a call was malformed needs to see what Gemini actually
    attempted, and this is the only place that still has it.
    """
    def __init__(self, message: str, payload: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.payload = payload


def first_part(payload: Dict[str, Any]) -> Dict[str, Any]:
    """The first content part of the first candidate. A blocked or empty
    candidate has no parts — named as such rather than surfacing a bare
    KeyError."""
    try:
        return payload["candidates"][0]["content"]["parts"][0]
    except (KeyError, IndexError):
        reason = (payload.get("candidates") or [{}])[0].get("finishReason", "unknown")
        if reason == "MALFORMED_FUNCTION_CALL":
            raise MalformedFunctionCall(
                "Gemini attempted a function call that failed its own validation.",
                payload=payload)
        raise RuntimeError("Gemini returned no usable answer (finishReason: %s)" % reason)
