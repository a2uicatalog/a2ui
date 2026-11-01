import json
from pathlib import Path

import pytest

from a2uicatalog import Client

REPO = Path(__file__).resolve().parents[3]
FIXTURE_SCHEMA = {
    "items": {"oneOf": [
        {"type": "object", "required": ["type", "text"], "additionalProperties": False,
         "properties": {"type": {"type": "string", "const": "heading"}, "text": {"type": "string"}}},
        {"type": "object", "required": ["type", "value"], "additionalProperties": False,
         "properties": {"type": {"type": "string", "const": "stat_card"}, "value": {"type": "string"},
                        "label": {"type": "string"}, "delta": {"type": "string"}}},
    ]}
}


class FakeTransport:
    """Records calls and answers from a table of (method, path) -> list of responses."""

    def __init__(self, routes):
        self.routes = {k: list(v) for k, v in routes.items()}
        self.calls = []

    def __call__(self, method, url, headers, body, timeout):
        path = url.split("//", 1)[1].split("/", 1)[1]
        path = "/" + path
        self.calls.append((method, path, dict(headers), json.loads(body) if body else None))
        key = (method, path.split("?")[0])
        status, hdrs, data = self.routes[key].pop(0) if len(self.routes[key]) > 1 else self.routes[key][0]
        return status, hdrs, data if isinstance(data, bytes) else json.dumps(data).encode()


@pytest.fixture
def make_client():
    def _make(routes, **kw):
        t = FakeTransport(routes)
        return Client(transport=t, sleep=kw.pop("sleep", lambda s: None), **kw), t
    return _make


@pytest.fixture
def schema_routes():
    return {("GET", "/catalogue/atoms-json-schema.json"): [(200, {}, FIXTURE_SCHEMA)]}
