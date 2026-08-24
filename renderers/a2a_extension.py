"""a2a_extension — A2A (Agent-to-Agent) transport binding for A2UI v1.0.

Wraps/unwraps already-correct v1.0 envelopes (renderers/a2ui_v1.py's
emit_surface() etc., renderers/a2ui_v1_updates.py's update_components()
etc.) for A2A transport, and builds the capability-negotiation objects the
real A2A extension spec defines. Companion to those two modules, imported
not duplicated — this module knows NOTHING about what a createSurface or
action message means; PR 2 (2026-08-24, this repo's own commit history)
made those two modules' output genuinely conform to the real spec, which
is what makes wrapping it for A2A meaningful at all rather than
transporting garbage correctly.

Deliberately does NOT implement message DISPATCH. `unwrap_data_part()`
returns the raw message list; a caller processes each message using
a2ui_v1_updates.py's existing apply_update()/surface_state_from_create() —
building a second, parallel receive-side mechanism here would duplicate
real, already-correct logic. This module's job stops at transport: get a
real v1.0 message list on or off the DataPart wire shape, nothing about
what those messages DO.

Reference: extensions/a2a/docs/a2ui_extension_specification.md
(a2ui-private/spec/a2ui-v1.0-upstream/, vendored 2026-08-24 from
a2ui-project/a2ui, the real canonical repo). Every shape below is taken
directly from that doc's own concrete JSON examples, not inferred.

Real spec processing rule (that doc's own words), the reason
unwrap_data_part() does NOT eagerly validate or dispatch: "This list is
NOT a transactional unit. Receivers... MUST process messages in the list
sequentially. If a single message... fails to validate or apply..., the
receiver SHOULD report/log the error for that specific message and MUST
continue processing the remaining messages." A caller doing that
processing needs the raw list first; validating/failing the whole batch
here would make honoring that rule impossible upstream.
"""
from __future__ import annotations

from typing import Any, Dict, List

A2A_EXTENSION_URI = "https://a2ui.org/a2a-extension/a2ui/v1.0"
A2UI_MIME_TYPE = "application/a2ui+json"


class NotAnA2uiDataPart(ValueError):
    """Raised by unwrap_data_part() when the DataPart's own mimeType marker
    is missing or wrong -- a real, distinguishable error (this DataPart
    isn't A2UI at all), not silently returning an empty list."""


def wrap_messages(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build the A2A DataPart carrying a batch of v1.0 messages. Direction-
    agnostic by design -- confirmed against the real spec's own two worked
    examples (an agent_to_renderer batch and a renderer_to_agent batch):
    the wrapper shape is identical either way; only the CONTENTS of
    `messages` differ. `messages` are already-built v1.0 envelopes (e.g.
    emit_surface() output) -- this function only wraps them for transport,
    it does not build or validate them."""
    return {"data": messages, "kind": "data",
            "metadata": {"mimeType": A2UI_MIME_TYPE}}


def unwrap_data_part(data_part: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract the v1.0 message list from an incoming A2A DataPart.
    Real shape confirmed against the spec's own examples: `metadata` is a
    SIBLING of `data`/`kind` on the DataPart itself, not nested inside
    `data` (an earlier, less careful read of this same doc via a
    summarization tool got this wrong -- corrected 2026-08-24 by reading
    the raw markdown's own JSON examples directly)."""
    metadata = data_part.get("metadata") or {}
    if metadata.get("mimeType") != A2UI_MIME_TYPE:
        raise NotAnA2uiDataPart(
            f"DataPart.metadata.mimeType is {metadata.get('mimeType')!r}, "
            f"expected {A2UI_MIME_TYPE!r} -- this DataPart is not A2UI data.")
    data = data_part.get("data")
    if not isinstance(data, list):
        raise NotAnA2uiDataPart(
            "DataPart.data must be an array of messages (real spec's own "
            "words: 'It MUST be an array of messages'), got "
            f"{type(data).__name__}.")
    return data


def agent_card_extension(supported_catalog_ids: List[str],
                         accepts_inline_catalogs: bool = False,
                         required: bool = False,
                         description: str = "Ability to render A2UI v1.0") -> Dict[str, Any]:
    """Build the one entry an agent's AgentCard.capabilities.extensions
    list needs to advertise A2UI v1.0 support -- shape taken verbatim from
    the spec's own worked AgentCard example."""
    return {
        "uri": A2A_EXTENSION_URI,
        "description": description,
        "required": required,
        "params": {
            "supportedCatalogIds": supported_catalog_ids,
            "acceptsInlineCatalogs": accepts_inline_catalogs,
        },
    }


def renderer_capabilities(supported_catalog_ids: List[str]) -> Dict[str, Any]:
    """Build message.metadata["a2uiRendererCapabilities"] -- namespaced
    under "v1.0", per the spec's own worked example. Lives on the A2A
    `message` object itself, NOT the DataPart -- a different location from
    wrap_messages()'s own metadata, easy to conflate, kept as two
    separate functions rather than one to keep that distinction visible
    at every call site."""
    return {"v1.0": {"supportedCatalogIds": supported_catalog_ids}}


def renderer_data_model(surfaces_data_model: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Build message.metadata["a2uiRendererDataModel"] -- the renderer's
    current-state report back to the agent, sent on every message once a
    surface has Data Model Sync enabled (createSurface.sendDataModel:
    true). `surfaces_data_model` maps surfaceId -> that surface's current
    data model, e.g. {"main_surface_id": {"user_id": "12345"}}."""
    return {"version": "v1.0", "surfaces": surfaces_data_model}
