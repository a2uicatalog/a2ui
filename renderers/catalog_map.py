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
_SCHEMA = os.path.join(_ROOT, "atoms", "schema.yaml")

BASE_URL = "https://a2uicatalog.ai"
BASE_CATALOG_SLUG = "a2ui-atoms-v1"


def _load_type_to_slug() -> Dict[str, str]:
    part = yaml.safe_load(open(_PACKS))
    return {atom: slug for slug, atoms in part.items() for atom in atoms}


def _load_child_declarations() -> Dict[str, Dict[str, Any]]:
    """type -> declared `children` block (spec/childlist-migration-v0.1.md, Phase 0).
    Replaces the old hand-maintained _CHILD_KEYS name list — a catalog required only
    by an atom nested inside e.g. chat_thread.messages[].block or module_map.modules[].page
    used to be silently missed because those field names weren't in the list; this is
    schema-driven so it can't drift the same way (see renderers/a2ui_v1.py's identical fix,
    same day, same root cause)."""
    schema = yaml.safe_load(open(_SCHEMA))
    return {b["type"]: b["children"]
            for b in schema["blocks"] if isinstance(b, dict) and b.get("type") and b.get("children")}


_TYPE_TO_SLUG = _load_type_to_slug()
_CHILD_DECLARATIONS = _load_child_declarations()


def catalog_uri(slug: str) -> str:
    return f"{BASE_URL}/catalogue/{slug}.json"


def catalog_of(atom_type: str) -> str:
    """Resolvable catalog URI for an atom type (base if core or unknown extension)."""
    return catalog_uri(_TYPE_TO_SLUG.get(atom_type, BASE_CATALOG_SLUG))


def _walk_inner_path(value: Any, segments: List[str], out: Set[str]) -> None:
    """Walk a wrapper field down its declared inner_path (dot-separated; hub's
    subjects[].slides[].blocks is the one two-level case) to the actual nested atom
    content, then collect_types() it. `value` may be a single wrapper dict
    (wrapper_single) or a list of them (wrapper_list) at each level."""
    if value is None:
        return
    items = value if isinstance(value, list) else [value]
    for item in items:
        if not isinstance(item, dict):
            continue
        if not segments:
            collect_types(item, out)
            continue
        _walk_inner_path(item.get(segments[0]), segments[1:], out)


def collect_types(blocks: Any, out: Set[str] = None) -> Set[str]:
    """Every atom `type` appearing anywhere in a blocks payload (recursive) —
    driven by each atom's declared `children` shape (schema.yaml, Phase 0), not a
    flat key-name guess. A conditional/absent nested field (e.g. a chat_thread
    message with no `block`) is simply skipped, not an error."""
    out = out if out is not None else set()
    if isinstance(blocks, dict):
        t = blocks.get("type") or blocks.get("component")
        if isinstance(t, str):
            out.add(t)
        decl = _CHILD_DECLARATIONS.get(t) if isinstance(t, str) else None
        if decl:
            for field, spec in decl.items():
                value = blocks.get(field)
                if value is None:
                    continue
                if spec["shape"] in ("simple", "single"):
                    collect_types(value, out)
                else:
                    _walk_inner_path(value, spec["inner_path"].split("."), out)
        # Narrow safety net for undeclared/unknown atom types: `blocks` is the one field
        # name the schema audit found 100% reliable (5/5 real nesting) — keeps discovery
        # working for a future/undeclared atom nesting via `blocks`, without reintroducing
        # the broad name-guessing this replaced (items/tabs/columns/content were mostly
        # noise). Harmless if already covered by `decl` above (collect_types is idempotent).
        if isinstance(blocks.get("blocks"), list) and not (decl and "blocks" in decl):
            collect_types(blocks["blocks"], out)
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
