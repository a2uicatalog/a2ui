"""A thin, dependency-free client for https://a2uicatalog.ai (no account, no key).

Endpoints used (all in https://a2uicatalog.ai/openapi.json): /spec.json, /catalogue/index.json,
/catalogue/atoms-json-schema.json, /ask, /api/compose, /api/render, /api/render/batch.
"""
from __future__ import annotations

import difflib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Iterable, Mapping

from .errors import (A2UIError, HTTPError, NetworkError, RateLimitError, UnknownAtomError,
                     ValidationError)

DEFAULT_BASE_URL = "https://a2uicatalog.ai"
SURFACES = ("web", "mcp-apps", "google-apps-script-web", "google-meet-stage")
MAX_RETRY_WAIT = 30.0   # seconds; a longer Retry-After (a daily limit) raises instead of sleeping

# A transport takes (method, url, headers, body, timeout) and returns (status, headers, body).
# Header names in the returned mapping must be lower-case. Tests pass a fake; the default uses urllib.
Transport = Callable[[str, str, Mapping[str, str], "bytes | None", float], "tuple[int, Mapping[str, str], bytes]"]

_JSON_TYPES: dict[str, tuple[type, ...]] = {
    "string": (str,), "boolean": (bool,), "array": (list, tuple), "object": (dict,),
    "integer": (int,), "number": (int, float),
}


def _urllib_transport(method: str, url: str, headers: Mapping[str, str], body: "bytes | None",
                      timeout: float) -> "tuple[int, Mapping[str, str], bytes]":
    req = urllib.request.Request(url, data=body, method=method, headers=dict(headers))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:   # noqa: S310 (https base URL)
            return resp.status, {k.lower(): v for k, v in resp.headers.items()}, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, {k.lower(): v for k, v in e.headers.items()}, e.read()
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise NetworkError(f"{method} {url}: {e}") from e


def _retry_after(headers: Mapping[str, str]) -> "float | None":
    raw = headers.get("retry-after")
    try:
        return float(raw) if raw is not None else None
    except ValueError:
        return None


def _blocks_of(payload: Any) -> list[Any]:
    """A payload is {'blocks': [...]} , a bare list of blocks, or one block."""
    if isinstance(payload, Mapping) and "blocks" in payload:
        blocks = payload["blocks"]
        return list(blocks) if isinstance(blocks, (list, tuple)) else [blocks]
    if isinstance(payload, (list, tuple)):
        return list(payload)
    return [payload]


class Client:
    """Reads the catalogue and renders payloads.

    Client(base_url=..., timeout=30) works against production with no setup. `transport` and `sleep`
    exist so tests can run with no network.
    """

    def __init__(self, base_url: str = DEFAULT_BASE_URL, *, timeout: float = 30.0,
                 user_agent: "str | None" = None, transport: "Transport | None" = None,
                 sleep: Callable[[float], None] = time.sleep):
        from . import __version__
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._ua = user_agent or f"a2uicatalog-python/{__version__}"
        self._transport = transport or _urllib_transport
        self._sleep = sleep
        self._spec: "dict | None" = None
        self._schema: "list[dict] | None" = None

    # ---- transport ---------------------------------------------------------------------------
    def _request(self, method: str, path: str, *, params: "Mapping[str, str] | None" = None,
                 json_body: Any = None, idempotency_key: "str | None" = None,
                 accept: str = "application/json") -> "tuple[Mapping[str, str], bytes]":
        url = self.base_url + path
        query = {k: v for k, v in (params or {}).items() if v is not None}
        if query:
            url += "?" + urllib.parse.urlencode(query)
        headers = {"user-agent": self._ua, "accept": accept}
        body = None
        if json_body is not None:
            body = json.dumps(json_body).encode("utf-8")
            headers["content-type"] = "application/json"
        if idempotency_key:
            headers["idempotency-key"] = idempotency_key
        for attempt in (0, 1):   # one retry on 429, never more
            status, rheaders, data = self._transport(method, url, headers, body, self.timeout)
            if status == 429:
                wait = _retry_after(rheaders)
                text = data.decode("utf-8", "replace")[:500]
                if attempt == 0 and wait is not None and wait <= MAX_RETRY_WAIT:
                    self._sleep(wait)
                    continue
                raise RateLimitError(429, "rate limited", text, wait)
            if status >= 400:
                text = data.decode("utf-8", "replace")
                raise HTTPError(status, _message(text), text[:2000], _retry_after(rheaders))
            return rheaders, data
        raise A2UIError("unreachable")   # pragma: no cover

    def _json(self, method: str, path: str, **kw: Any) -> Any:
        _, data = self._request(method, path, **kw)
        try:
            return json.loads(data)
        except ValueError as e:
            raise A2UIError(f"{path}: response is not JSON") from e

    # ---- catalogue reads ---------------------------------------------------------------------
    def spec(self) -> dict:
        """The full atom vocabulary (/spec.json). Fetched once, then cached in memory."""
        if self._spec is None:
            self._spec = self._json("GET", "/spec.json")
        return self._spec

    def catalogs(self) -> dict:
        """The catalog selection menu (/catalogue/index.json)."""
        return self._json("GET", "/catalogue/index.json")

    def _atom_schemas(self) -> list[dict]:
        if self._schema is None:
            doc = self._json("GET", "/catalogue/atoms-json-schema.json")
            self._schema = list(doc["items"]["oneOf"])
        return self._schema

    def atom_types(self) -> list[str]:
        """Every published atom type name."""
        return sorted(_type_of(s) for s in self._atom_schemas())

    def atom_schema(self, atom: str) -> dict:
        """The strict JSON Schema for one atom. Raises UnknownAtomError for a name not in the catalogue."""
        for s in self._atom_schemas():
            if _type_of(s) == atom:
                return s
        raise UnknownAtomError(atom, difflib.get_close_matches(atom, self.atom_types(), n=3))

    # ---- model-backed and render calls -------------------------------------------------------
    def ask(self, question: str, *, mode: str = "list") -> dict:
        """NLWeb catalog search: ranked, typed matches for a plain-English question.

        Uses POST /ask. The OpenAPI file also documents GET /ask, which answered 404 in production
        when this client was written, so the client does not rely on it.
        """
        return self._json("POST", "/ask", json_body={"query": question, "mode": mode})

    def compose(self, prompt: str, *, idempotency_key: "str | None" = None) -> dict:
        """Plain English to candidate atom blocks: {"blocks": [...]}. Free tier: 20 requests per IP per day."""
        return self._json("POST", "/api/compose", json_body={"prompt": prompt},
                          idempotency_key=idempotency_key)

    def render(self, payload: Any, *, surface: "str | None" = None, theme: "str | None" = None,
               title: "str | None" = None, idempotency_key: "str | None" = None) -> str:
        """Render a payload to one self-contained HTML page.

        `payload` is {"blocks": [...]}, a list of blocks, or a single block. 50 requests per IP per day.
        """
        body = _as_payload(payload, title=title, theme=theme)
        _check_surface(surface)
        _, data = self._request("POST", "/api/render", params={"surface": surface}, json_body=body,
                                idempotency_key=idempotency_key, accept="text/html")
        return data.decode("utf-8")

    def render_batch(self, payloads: Iterable[Any], *, surface: "str | None" = None,
                     idempotency_key: "str | None" = None) -> dict:
        """Render up to 25 payloads in one call. Partial success is the contract: read each result's
        `status` (200 with `html`, or an error). Returns {"ok", "rendered", "failed", "results": [...]}."""
        items = [_as_payload(p) for p in payloads]
        if not 1 <= len(items) <= 25:
            raise ValueError("render_batch takes 1 to 25 payloads")
        _check_surface(surface)
        return self._json("POST", "/api/render/batch", params={"surface": surface},
                          json_body={"payloads": items}, idempotency_key=idempotency_key)

    # ---- local validation --------------------------------------------------------------------
    def check(self, payload: Any, *, strict: bool = True) -> list[str]:
        """Local check against the published atom schemas. Returns problems (empty list = clean).

        Checks that every block names a published atom, has the atom's required fields, uses no field
        the atom does not define, and gives simple fields (string/number/boolean/array/object) the right
        JSON type. strict=False reports only unknown atoms and missing required fields, because the published
        schema is stricter than the renderer (many shipped example payloads use extra fields). The first call fetches the schema file (about 2 MB); later calls use the cache.
        """
        by_type = {_type_of(s): s for s in self._atom_schemas()}
        problems: list[str] = []
        for i, block in enumerate(_blocks_of(payload)):
            where = f"blocks[{i}]"
            if not isinstance(block, Mapping):
                problems.append(f"{where}: a block must be an object")
                continue
            t = block.get("type")
            if not isinstance(t, str):
                problems.append(f"{where}: missing 'type'")
                continue
            schema = by_type.get(t)
            if schema is None:
                near = difflib.get_close_matches(t, list(by_type), n=3)
                problems.append(f"{where}: unknown atom type {t!r}" + (f" (did you mean {', '.join(near)}?)" if near else ""))
                continue
            props = schema.get("properties", {})
            for req in schema.get("required", []):
                if req not in block:
                    problems.append(f"{where} ({t}): missing required field {req!r}")
            if not strict:
                continue
            if schema.get("additionalProperties") is False:
                for key in block:
                    if key not in props:
                        problems.append(f"{where} ({t}): unknown field {key!r}")
            for key, val in block.items():
                want = props.get(key, {}).get("type")
                if isinstance(want, str) and want in _JSON_TYPES and val is not None:
                    ok = isinstance(val, _JSON_TYPES[want]) and not (want in ("integer", "number") and isinstance(val, bool))
                    if not ok:
                        problems.append(f"{where} ({t}): field {key!r} should be {want}")
        return problems

    def validate(self, payload: Any, *, strict: bool = True) -> None:
        """Like check(), but raises ValidationError (with .problems) instead of returning the list."""
        problems = self.check(payload, strict=strict)
        if problems:
            raise ValidationError(problems)


def _type_of(schema: Mapping[str, Any]) -> str:
    return schema["properties"]["type"]["const"]


def _as_payload(payload: Any, *, title: "str | None" = None, theme: "str | None" = None) -> dict:
    body: dict = dict(payload) if isinstance(payload, Mapping) and "blocks" in payload else {"blocks": _blocks_of(payload)}
    if title is not None:
        body["title"] = title
    if theme is not None:
        body["theme"] = theme
    return body


def _check_surface(surface: "str | None") -> None:
    if surface is not None and surface not in SURFACES:
        raise ValueError(f"surface must be one of {', '.join(SURFACES)}")


def _message(text: str) -> str:
    try:
        d = json.loads(text)
        if isinstance(d, dict):
            for k in ("error", "message", "detail"):
                if isinstance(d.get(k), str):
                    return d[k][:300]
    except ValueError:
        pass
    return text.strip()[:200] or "request failed"
