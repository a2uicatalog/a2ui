"""Real jsonschema validation against the vendored A2UI v1.0 spec
(tests/fixtures/a2ui_v1_0_spec/ — a self-contained copy for THIS repo's own
CI, which does not check out the sibling a2ui-private repo where the
canonical vendored copy also lives; see a2ui-private/spec/a2ui-v1.0-upstream/
README.md for provenance and the 2026-08-24 re-vendor that replaced a stale
copy this repo's emitters had drifted from).

Not test_*.py — a shared helper other test files import, matching this
repo's tests/fixtures/ convention (see tests/conftest.py for the sibling
"shared setup lives outside the test_ namespace" precedent).

Real subtlety worth recording: catalog.json's own $id is
".../catalogs/basic/catalog.json" (one directory deeper than where it
lives), but agent_to_renderer.json's Component schema references it with
the bare relative $ref "catalog.json" — which resolves (standard relative-
URI-against-base rules) to ".../catalog.json", NOT catalog.json's own real
$id. Confirmed by trying the naive approach first and hitting an
unresolvable reference. Fixed by registering catalog.json's content under
BOTH URIs: its own declared $id (in case anything ever references it that
way) and the bare-relative alias every $ref actually needs. This is a
pragmatic fix for validating structural conformance, not a claim about
resolving whatever the spec authors intended by this — see the doubly-
registered entry in _registry() below.
"""
from __future__ import annotations

import json
import pathlib
from typing import Any, Dict

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures" / "a2ui_v1_0_spec"

_BARE_CATALOG_ALIAS = "https://a2ui.org/specification/v1_0/catalog.json"


def _registry() -> Registry:
    resources = []
    schema_files = list((FIXTURES / "json").glob("*.json")) + \
        list((FIXTURES / "catalogs" / "basic").glob("*.json"))
    for path in schema_files:
        doc = json.loads(path.read_text())
        real_id = doc.get("$id")
        if not real_id:
            continue
        resources.append((real_id, Resource.from_contents(doc)))
        if path.name == "catalog.json":
            # See module docstring: the bare-relative $ref agent_to_renderer.json
            # actually uses does not match catalog.json's own declared $id.
            resources.append((_BARE_CATALOG_ALIAS, Resource.from_contents(doc)))
    return Registry().with_resources(resources)


_REGISTRY = _registry()


def _validator_for(schema_filename: str) -> Draft202012Validator:
    """schema_filename: e.g. 'agent_to_renderer.json' (agent->renderer
    envelopes: createSurface/updateComponents/updateDataModel/deleteSurface/
    callRendererFunction/agentFunctionResponse) or 'renderer_to_agent.json'
    (action/callAgentFunction/rendererFunctionResponse/error)."""
    schema = json.loads((FIXTURES / "json" / schema_filename).read_text())
    return Draft202012Validator(schema, registry=_REGISTRY)


AGENT_TO_RENDERER = _validator_for("agent_to_renderer.json")
RENDERER_TO_AGENT = _validator_for("renderer_to_agent.json")


def assert_conforms(message: Dict[str, Any], validator: Draft202012Validator) -> None:
    """Real schema validation, not eyeballed field matching — the whole
    point of this module. Raises with every real error (jsonschema's own
    oneOf failures are notoriously unhelpful alone — 'not valid under any
    of the given schemas' with no hint which one was closest — so this
    surfaces the message itself too, since that's usually enough to spot
    the offending field by inspection)."""
    errors = list(validator.iter_errors(message))
    if errors:
        detail = "\n".join(f"  - {e.message} (at {list(e.path)})" for e in errors)
        raise AssertionError(
            f"Message does not conform to the real A2UI v1.0 schema:\n{detail}\n"
            f"Message was: {json.dumps(message, indent=2)}")
