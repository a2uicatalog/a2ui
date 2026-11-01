"""The client only calls endpoints that exist in the repo's public/openapi.json, and it validates the
repo's own schema and the OpenAPI examples. Skipped when run outside the a2ui checkout (sdist)."""
import json
import re
from pathlib import Path

import pytest

import a2uicatalog.client as client_mod
from a2uicatalog import Client

REPO = Path(__file__).resolve().parents[3]
OPENAPI = REPO / "public" / "openapi.json"
SCHEMA = REPO / "public" / "catalogue" / "atoms-json-schema.json"
pytestmark = pytest.mark.skipif(not OPENAPI.exists(), reason="not inside the a2ui checkout")

# (method, path) pairs the client issues; kept next to the code by this test reading its source.
USED = {("GET", "/spec.json"), ("GET", "/catalogue/index.json"), ("GET", "/catalogue/atoms-json-schema.json"),
        ("POST", "/ask"), ("POST", "/api/compose"), ("POST", "/api/render"), ("POST", "/api/render/batch")}


def test_every_endpoint_the_client_uses_is_in_openapi():
    paths = json.loads(OPENAPI.read_text())["paths"]
    for method, path in USED:
        assert path in paths and method.lower() in paths[path], (method, path)


def test_the_used_set_matches_the_client_source():
    src = Path(client_mod.__file__).read_text()
    found = set(re.findall(r'(?:_json|_request)\(\s*"(GET|POST)",\s*"(/[^"]+)"', src))
    assert found == USED


def _offline_client():
    def transport(method, url, headers, body, timeout):
        assert url.endswith("/catalogue/atoms-json-schema.json")
        return 200, {}, SCHEMA.read_bytes()
    return Client(transport=transport)


@pytest.mark.skipif(not SCHEMA.exists(), reason="schema file missing")
def test_openapi_examples_validate_against_the_real_schema():
    c = _offline_client()
    spec = json.loads(OPENAPI.read_text())
    ex = spec["paths"]["/api/render"]["post"]["requestBody"]["content"]["application/json"]["example"]
    assert c.check(ex) == []
    batch = spec["paths"]["/api/render/batch"]["post"]["requestBody"]["content"]["application/json"]["example"]
    for p in batch["payloads"]:
        assert c.check(p) == []
    assert any("unknown atom type 'not_an_atom'" in p for p in c.check([{"type": "not_an_atom"}]))
    assert "treemap" in c.atom_types() and len(c.atom_types()) > 400
