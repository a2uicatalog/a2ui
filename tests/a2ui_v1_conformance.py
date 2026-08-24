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

import regex  # stdlib `re` cannot compile \p{...} Unicode-property syntax —
# real spec requirement, not avoidable: common_types.json#/$defs/Extensions
# uses exactly this in its patternProperties key
# ("^[\\p{XID_Start}_][\\p{XID_Continue}]*$"), which any message using
# metadata.extensions (this module's own emit_surface() fix does, via
# a2uicatalog_surface) has to validate against. Hit this for real running
# the fixed emitter through the validator, not discovered by inspection.
from jsonschema import Draft202012Validator
from jsonschema.validators import extend
from referencing import Registry, Resource

FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures" / "a2ui_v1_0_spec"


def _pattern(validator, patrn, instance, schema):
    """Drop-in replacement for jsonschema's own `pattern` keyword function,
    swapping stdlib `re` for the `regex` package (same API, adds \\p{...}
    Unicode property support). See module-level import comment above."""
    if validator.is_type(instance, "string") and not regex.search(patrn, instance):
        from jsonschema.exceptions import ValidationError
        yield ValidationError(f"{instance!r} does not match {patrn!r}")


def _pattern_properties(validator, pattern_properties, instance, schema):
    """Same swap, for `patternProperties` — see _pattern() above."""
    if not validator.is_type(instance, "object"):
        return
    for patrn, subschema in pattern_properties.items():
        for k, v in instance.items():
            if regex.search(patrn, k):
                yield from validator.descend(v, subschema, path=k, schema_path=patrn)


_RegexAwareValidator = extend(
    Draft202012Validator,
    validators={"pattern": _pattern, "patternProperties": _pattern_properties})

# The VALIDATORS override above is NOT enough on its own: `unevaluatedProperties`
# (used throughout these schemas via `additionalProperties`/
# `unevaluatedProperties: false`) needs to independently know which keys a
# patternProperties pattern already covers, and jsonschema computes that via
# its own internal jsonschema._utils.find_evaluated_property_keys_by_schema —
# a SEPARATE code path with its own hardcoded `re.search(pattern, property)`,
# not routed through the VALIDATORS dict at all (confirmed by reading its
# source directly after the VALIDATORS-only fix above still failed on the
# exact same \p{...} pattern). No clean per-instance override point exists
# for this, so this patches that module's own `re` name to point at `regex`
# instead — scoped to exactly this one internal helper's use, not a global
# `sys.modules["re"]` replacement.
import jsonschema._utils as _js_utils  # noqa: E402
_js_utils.re = regex

_BARE_CATALOG_ALIAS = "https://a2ui.org/specification/v1_0/catalog.json"

# a2uicatalog's real EXTENSION catalog (~480 of its ~551 atoms) is served
# live at https://a2uicatalog.ai/catalogue/a2ui-atoms-v1.json — not a real
# A2UI-shaped JSON Schema catalog document, and not vendored here. A real
# v1.0 host without that catalog loaded is explicitly SPEC-CORRECT to skip
# validating those components deeply ("a host without the catalog simply
# skips them" — a2ui_v1.py's own docstring, matching the real extension
# model) — so strict validation against ONLY the basic catalog's closed
# `anyComponent` oneOf would flag every legitimate extension component as
# broken, which is a real GAP in this test fixture's catalog coverage, not
# a real protocol violation. Confirmed live 2026-08-24: emit_surface()'s
# real output for a `glowing_stat` extension atom failed this way even
# though nothing about it is actually wrong.
#
# Fix: extend anyComponent with one more oneOf branch, permitting any
# `component` name NOT in the basic catalog's own closed list, with no
# further field-level checking (exactly what a real host without that
# catalog would do). The 18 real basic-catalog components stay STRICTLY
# validated -- a genuine bug in how Image/Card/Button/etc. are built is
# still caught; only genuinely unregistered extension names get waved
# through.
_PERMISSIVE_EXTENSION_BRANCH = {
    "type": "object",
    "required": ["component"],
    "properties": {"component": {"not": {"enum": [
        "Text", "Image", "Icon", "Video", "AudioPlayer", "Row", "Column",
        "List", "Card", "Tabs", "Modal", "Divider", "Button", "TextField",
        "CheckBox", "ChoicePicker", "Slider", "DateTimeInput"]}}},
    # Matching the branch structurally isn't enough on its own: jsonschema's
    # unevaluatedProperties needs a branch to also mark keys as EVALUATED
    # (it looks for additionalProperties/patternProperties/etc, not just
    # oneOf membership) -- without this, extension components still failed
    # on their own extra fields even once this branch let them match.
    "additionalProperties": True,
}


def _registry() -> Registry:
    resources = []
    schema_files = list((FIXTURES / "json").glob("*.json")) + \
        list((FIXTURES / "catalogs" / "basic").glob("*.json"))
    for path in schema_files:
        doc = json.loads(path.read_text())
        if path.name == "catalog.json":
            # Deep-copy the one $def being extended -- never mutate the
            # vendored file's own parsed dict in place.
            doc = json.loads(json.dumps(doc))
            doc["$defs"]["anyComponent"]["oneOf"].append(_PERMISSIVE_EXTENSION_BRANCH)
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
    return _RegexAwareValidator(schema, registry=_REGISTRY)


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
