"""Real jsonschema validation against the vendored A2UI v0.9 spec (tests/fixtures/a2ui_v0_9_spec/,
fetched from github.com/a2ui-project/a2ui specification/v0_9 on 2026-10-05).

v1.0 is what we emit by default; v0.9 is only a DOWNGRADE for renderers that declare v0.9
capabilities (Google's androidx.a2ui alpha). This validates that downgrade against v0.9 itself,
not against our reading of the evolution guide. Same machinery as a2ui_v1_conformance.py (its
regex-aware validator and its permissive branch for extension components), same bare
"catalog.json" $ref quirk, v0.9 file names (server_to_client.json, client_to_server.json).
"""
from __future__ import annotations

import json
import pathlib

from referencing import Registry, Resource

from tests.a2ui_v1_conformance import _PERMISSIVE_EXTENSION_BRANCH, _RegexAwareValidator, assert_conforms  # noqa: F401

FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures" / "a2ui_v0_9_spec"
_BARE_CATALOG_ALIAS = "https://a2ui.org/specification/v0_9/catalog.json"


def _registry() -> Registry:
    resources = []
    for path in list((FIXTURES / "json").glob("*.json")) + list((FIXTURES / "catalogs" / "basic").glob("*.json")):
        doc = json.loads(path.read_text())
        if path.name == "catalog.json":
            doc = json.loads(json.dumps(doc))
            doc["$defs"]["anyComponent"]["oneOf"].append(_PERMISSIVE_EXTENSION_BRANCH)
        if not doc.get("$id"):
            continue
        resources.append((doc["$id"], Resource.from_contents(doc)))
        if path.name == "catalog.json":
            resources.append((_BARE_CATALOG_ALIAS, Resource.from_contents(doc)))
    return Registry().with_resources(resources)


_REGISTRY = _registry()
SERVER_TO_CLIENT = _RegexAwareValidator(json.loads((FIXTURES / "json" / "server_to_client.json").read_text()), registry=_REGISTRY)
CLIENT_TO_SERVER = _RegexAwareValidator(json.loads((FIXTURES / "json" / "client_to_server.json").read_text()), registry=_REGISTRY)
