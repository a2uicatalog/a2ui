"""a2ui_capabilities — read what a renderer says it can draw, so the emitter never
sends it something it can't.

Two wire forms exist today, both namespaced by protocol version:
  * the v1.0 spec: transport metadata `a2uiRendererCapabilities`
    ({"v1.0": {"supportedCatalogIds": [...]}}, see renderers/a2a_extension.py's
    renderer_capabilities(), which builds the same shape);
  * Google's androidx.a2ui 1.0.0-alpha01: `a2uiClientCapabilities`
    ({"v0.9": {"supportedCatalogIds": [...], "inlineCatalogs": [...]}}), sent
    automatically from the catalogues an Android app registers.

Why it matters: Google's engine throws on any component type its catalogues don't
register (no catch-all), so emitting one of our atoms to a stock Android app crashes
the surface. With capabilities in hand, emit_surface() degrades instead.
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

BASIC_CATALOG_IDS = {
    "v1.0": "https://a2ui.org/specification/v1_0/catalogs/basic/catalog.json",
    "v0.9": "https://a2ui.org/specification/v0_9/catalogs/basic/catalog.json",
}

# Basic Catalog V1 component names: identical in the v1.0 spec catalogue and in
# Google's v0.9 alpha (checked against both, 2026-10-04).
BASIC_COMPONENTS = frozenset({
    "AudioPlayer", "Button", "Card", "CheckBox", "ChoicePicker", "Column",
    "DateTimeInput", "Divider", "Icon", "Image", "List", "Modal", "Row", "Slider",
    "Tabs", "Text", "TextField", "Video",
})

# Versions we can emit, best first. "v0.9.1" is accepted by Google's parser and
# is wire-identical to v0.9 for everything the emitter produces.
_VERSIONS = ("v1.0", "v0.9", "v0.9.1")
_METADATA_KEYS = ("a2uiRendererCapabilities", "a2uiClientCapabilities")


@dataclass(frozen=True)
class ClientCapabilities:
    version: str                     # protocol version to emit: "v1.0" or "v0.9"
    supported_catalog_ids: tuple     # catalogue ids the renderer can draw

    def supports(self, catalog_id: str) -> bool:
        return catalog_id in self.supported_catalog_ids

    @property
    def basic_catalog_id(self) -> Optional[str]:
        """The Basic Catalog id this renderer declared, if any."""
        for cid in self.supported_catalog_ids:
            if cid in BASIC_CATALOG_IDS.values():
                return cid
        return None


def parse_client_capabilities(metadata: Optional[Dict[str, Any]]) -> Optional[ClientCapabilities]:
    """Return the renderer's capabilities from transport metadata, or None when it
    sent none (callers then keep today's behaviour). Accepts the metadata object
    itself or the bare {"<version>": {...}} value. Prefers the newest version we
    can emit when the renderer offers several."""
    if not isinstance(metadata, dict):
        return None
    candidates: List[Dict[str, Any]] = [metadata[k] for k in _METADATA_KEYS if isinstance(metadata.get(k), dict)]
    if not candidates:
        candidates = [metadata]
    for version in _VERSIONS:
        for cand in candidates:
            body = cand.get(version)
            if isinstance(body, dict) and isinstance(body.get("supportedCatalogIds"), list):
                ids = tuple(x for x in body["supportedCatalogIds"] if isinstance(x, str))
                emit_version = "v0.9" if version.startswith("v0.9") else version
                return ClientCapabilities(version=emit_version, supported_catalog_ids=ids)
    return None
