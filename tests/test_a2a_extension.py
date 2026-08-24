"""renderers/a2a_extension.py -- real jsonschema validation of the A2A
DataPart wrapping against the vendored spec's own list schemas
(agent_to_renderer_list.json / renderer_to_agent_list.json), plus a real
end-to-end proof that the ALREADY-FIXED emitters (renderers/a2ui_v1.py,
renderers/a2ui_v1_updates.py) produce content that survives the full
wrap -> unwrap -> validate round trip, not just each half in isolation.
"""
from __future__ import annotations

import json
import pathlib

import pytest
from jsonschema import Draft202012Validator

from renderers.a2a_extension import (
    A2A_EXTENSION_URI, A2UI_MIME_TYPE, NotAnA2uiDataPart,
    agent_card_extension, renderer_capabilities, renderer_data_model,
    unwrap_data_part, wrap_messages,
)
from renderers.a2ui_v1 import emit_surface, call_renderer_function
from renderers.a2ui_v1_updates import update_components, update_data_model
from tests.a2ui_v1_conformance import FIXTURES, _RegexAwareValidator, _REGISTRY


def _list_validator(schema_filename: str) -> Draft202012Validator:
    schema = json.loads((FIXTURES / "json" / schema_filename).read_text())
    return _RegexAwareValidator(schema, registry=_REGISTRY)


AGENT_TO_RENDERER_LIST = _list_validator("agent_to_renderer_list.json")
RENDERER_TO_AGENT_LIST = _list_validator("renderer_to_agent_list.json")


def test_wrap_shape_matches_the_specs_own_worked_example():
    """Confirms the exact shape from the spec's own JSON example: `data`,
    `kind`, and `metadata` as three top-level siblings -- `metadata` NOT
    nested inside `data` (the mistake an earlier, less careful read of
    this doc made)."""
    dp = wrap_messages([{"version": "v1.0", "action": {
        "name": "submit_form", "surfaceId": "s1", "sourceComponentId": "btn",
        "timestamp": "2026-01-15T12:00:00Z", "context": {}}}])
    assert set(dp.keys()) == {"data", "kind", "metadata"}
    assert dp["kind"] == "data"
    assert dp["metadata"] == {"mimeType": A2UI_MIME_TYPE}
    assert isinstance(dp["data"], list)


def test_agent_to_renderer_batch_conforms():
    surface_msg = emit_surface({"title": "T", "blocks": [{"type": "heading", "text": "Hi"}]})
    update_msg = update_components("t", [{"id": "root", "component": "Text", "text": "hi"}])
    dp = wrap_messages([surface_msg, update_msg])
    errors = list(AGENT_TO_RENDERER_LIST.iter_errors(dp["data"]))
    assert not errors, errors


def test_renderer_to_agent_batch_conforms():
    action_msg = {"version": "v1.0", "action": {
        "name": "submit_form", "surfaceId": "contact_form_1",
        "sourceComponentId": "submit_button", "timestamp": "2026-01-15T12:00:00Z",
        "context": {"email": "user@example.com"}}}
    dp = wrap_messages([action_msg])
    errors = list(RENDERER_TO_AGENT_LIST.iter_errors(dp["data"]))
    assert not errors, errors


def test_unwrap_round_trips():
    msgs = [{"version": "v1.0", "deleteSurface": {"surfaceId": "s1"}}]
    dp = wrap_messages(msgs)
    assert unwrap_data_part(dp) == msgs


def test_unwrap_rejects_wrong_mime_type():
    with pytest.raises(NotAnA2uiDataPart):
        unwrap_data_part({"data": [], "kind": "data", "metadata": {"mimeType": "text/plain"}})


def test_unwrap_rejects_missing_metadata():
    with pytest.raises(NotAnA2uiDataPart):
        unwrap_data_part({"data": [], "kind": "data"})


def test_unwrap_rejects_non_list_data():
    """Real spec's own words: 'It MUST be an array of messages.'"""
    with pytest.raises(NotAnA2uiDataPart):
        unwrap_data_part({"data": {"version": "v1.0"}, "kind": "data",
                          "metadata": {"mimeType": A2UI_MIME_TYPE}})


def test_end_to_end_real_emitter_through_wrap_unwrap_validate():
    """The critical proof Gemini's design review called for: the ALREADY-
    FIXED emitters (not synthetic fixtures) survive the full real pipeline
    -- emit -> wrap -> unwrap -> re-validate -- proving the fixed emitter
    and the new transport module compose correctly, not just pass in
    isolation."""
    payload = {"title": "Dashboard", "theme": "dark", "blocks": [
        {"type": "heading", "text": "Sales"},
        {"type": "body", "text": "Q3 results"},
    ]}
    surface_msg = emit_surface(payload, surface_id="dash-1")
    call_msg = call_renderer_function(
        "https://a2ui.org/specification/v1_0/catalog.json", "openUrl",
        args={"url": "https://example.com"})
    update_msg = update_data_model("dash-1", value={"revenue": 42}, path="/metrics")

    dp = wrap_messages([surface_msg, call_msg, update_msg])
    round_tripped = unwrap_data_part(dp)
    assert round_tripped == [surface_msg, call_msg, update_msg]

    errors = list(AGENT_TO_RENDERER_LIST.iter_errors(round_tripped))
    assert not errors, errors


def test_agent_card_extension_matches_the_specs_worked_example_shape():
    entry = agent_card_extension(
        ["https://a2ui.org/specification/v1_0/catalogs/basic/catalog.json"],
        accepts_inline_catalogs=True)
    assert entry["uri"] == A2A_EXTENSION_URI
    assert entry["required"] is False
    assert entry["params"]["acceptsInlineCatalogs"] is True
    # Real schema check: agent_capabilities.json's top-level shape wraps
    # everything under a "v1.0" key (required: ["v1.0"]) -- confirmed by
    # reading the schema directly, not assumed; entry["params"] is that
    # inner object, so it validates as {"v1.0": entry["params"]}.
    schema = json.loads((FIXTURES / "json" / "agent_capabilities.json").read_text())
    validator = _RegexAwareValidator(schema, registry=_REGISTRY)
    errors = list(validator.iter_errors({"v1.0": entry["params"]}))
    assert not errors, errors


def test_renderer_capabilities_namespaced_under_v1_0():
    caps = renderer_capabilities(["https://example.com/catalog.json"])
    assert caps == {"v1.0": {"supportedCatalogIds": ["https://example.com/catalog.json"]}}


def test_renderer_data_model_shape():
    dm = renderer_data_model({"main_surface_id": {"user_id": "12345"}})
    assert dm == {"version": "v1.0", "surfaces": {"main_surface_id": {"user_id": "12345"}}}
