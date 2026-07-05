"""catalog_map — the deterministic atom→catalog binding + required-catalog derivation.

The A2UI-1.0-aligned answer to "which catalogs does this surface need?": it's a PURE
FUNCTION of the surface's atoms, never a guess. `required_catalogs(blocks)` walks every
atom (recursively through nested blocks), maps each to its catalog via atoms/atom-packs.yaml,
and returns the sorted set of resolvable catalog URIs (base `a2ui-atoms-v1` always included).

Two consumers:
  - the emitters call it to AUTO-DECLARE surfaceProperties.catalogs — so the agent never
    hand-picks catalogs; the emitted surface states exactly what a host must resolve.
  - an agent/tool calls it directly (CLI below) to know, deterministically, which extension
    catalogs a payload draws from before/without emitting.

CLI:  python3 renderers/catalog_map.py <payload.json>   # prints the required catalog URIs
"""
import json
import os
from typing import Any, Dict, Iterable, List, Set

import yaml

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
_PACKS = os.path.join(_ROOT, "atoms", "atom-packs.yaml")

BASE_URL = "https://a2uicatalog.ai"
BASE_CATALOG_SLUG = "a2ui-atoms-v1"

# child-bearing keys the block dialect uses to nest atoms — walked recursively so a
# catalog required only by a deeply-nested atom is still discovered.
_CHILD_KEYS = ("blocks", "items", "children", "content", "left", "right",
               "modules", "page", "slides", "subjects", "tabs", "columns")


def _load_type_to_slug() -> Dict[str, str]:
    part = yaml.safe_load(open(_PACKS))
    return {atom: slug for slug, atoms in part.items() for atom in atoms}


_TYPE_TO_SLUG = _load_type_to_slug()


def catalog_uri(slug: str) -> str:
    return f"{BASE_URL}/catalogue/{slug}.json"


def catalog_of(atom_type: str) -> str:
    """Resolvable catalog URI for an atom type (base if core or unknown extension)."""
    return catalog_uri(_TYPE_TO_SLUG.get(atom_type, BASE_CATALOG_SLUG))


def collect_types(blocks: Any, out: Set[str] = None) -> Set[str]:
    """Every atom `type` appearing anywhere in a blocks payload (recursive)."""
    out = out if out is not None else set()
    if isinstance(blocks, dict):
        t = blocks.get("type") or blocks.get("component")
        if isinstance(t, str):
            out.add(t)
        for k in _CHILD_KEYS:
            if k in blocks:
                collect_types(blocks[k], out)
    elif isinstance(blocks, list):
        for b in blocks:
            collect_types(b, out)
    return out


def required_catalogs(payload_or_blocks: Any) -> List[str]:
    """Sorted resolvable catalog URIs a payload needs. Base first, then extensions.

    Deterministic: same payload → same set, no model judgement involved."""
    blocks = payload_or_blocks
    if isinstance(payload_or_blocks, dict) and "blocks" in payload_or_blocks:
        blocks = payload_or_blocks["blocks"]
    types = collect_types(blocks)
    slugs: Set[str] = {_TYPE_TO_SLUG.get(t, BASE_CATALOG_SLUG) for t in types}
    slugs.add(BASE_CATALOG_SLUG)                       # base is always resolved
    base = catalog_uri(BASE_CATALOG_SLUG)
    others = sorted(catalog_uri(s) for s in slugs if s != BASE_CATALOG_SLUG)
    return [base] + others


def extension_catalogs(payload_or_blocks: Any) -> List[str]:
    """Just the non-base catalogs (what a lean host must additionally resolve)."""
    return [c for c in required_catalogs(payload_or_blocks)
            if c != catalog_uri(BASE_CATALOG_SLUG)]


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        sys.exit("usage: python3 renderers/catalog_map.py <payload.json>")
    payload = json.load(open(sys.argv[1]))
    cats = required_catalogs(payload)
    print(json.dumps({"required_catalogs": cats,
                      "extensions": [c for c in cats if not c.endswith(f"{BASE_CATALOG_SLUG}.json")]},
                     indent=2))
