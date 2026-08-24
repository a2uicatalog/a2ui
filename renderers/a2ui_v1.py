"""a2ui_v1 — emit A2UI protocol v1.0 (Google, https://a2ui.org) createSurface messages
from the catalogue's *blocks* dialect.

Positioning: a2uicatalog is a CATALOG for the A2UI protocol. v1.0's `createSurface`
carries a required `catalogId`; this emitter produces conformant messages so that:
  - the ~78 high-frequency "standard-mappable" atoms render on a BARE A2UI host
    (mapped to the 18 basic-catalog components: Text/Image/Button/Card/…), and
  - the ~421 extension atoms travel as valid components under `catalogId`
    (a host without the catalog simply skips them — correct A2UI behaviour, not
    a violation).

Scope (tiers 1 + 2-core, plus Track B1 + C1 + Phase 0 schema-driven children):
  - Full envelope/metadata: version, surfaceId, catalogId, surfaceProperties.
  - Deterministic ID minting; flat `components` list with parent→child ID refs.
  - Standard-component mapping for clean atoms; common container inversion
    (columns, color_section, card, tabs, modal, generic `blocks`).
  - B1 exotic containers: split_pane -> Row of two Columns; row_open/row_close
    (wired-dialect bracket pseudo-atoms) -> a Row wrapping the bracketed run;
    hub (2-level subject/slide deck nav) -> nested Tabs (outer = subjects,
    inner = slides, each slide a Column of its blocks).
  - Schema-driven children (spec/childlist-migration-v0.1.md, Phase 0): any
    atom NOT already covered by an explicit case above, but that declares a
    `children:` block in atoms/schema.yaml (shape: simple/single/wrapper_list/
    wrapper_single + inner_path), gets its nested atom content flattened into
    ID refs generically — driven by that declaration, not a hand-written case
    per atom type. Covers blur_fade_in, playbook, quiz_set, atom_anatomy,
    module_map, chat_thread — atoms that previously fell through to raw
    pass-through with their nested atoms still embedded, non-conformant with
    v1.0's ChildList rule. See _emit_declared_children.
  - Safe pass-through for everything else (extension components, and any
    field this cut doesn't recognize as child-bearing at all).
  - Action-contract adapter: {ok,data,total,error} -> actionResponse {value|error}.
  - C1 client-facing function RPC: call_function() builds the `callFunction`
    request; function_response() adapts the catalogue envelope into the
    `functionResponse` (success) / `error` (failure) reply pair, keyed by
    functionCallId.

Deferred (flagged, not faked): the wired dialect itself (state_primitives /
#node.prop reactive graph → catalogId: a2ui-state-v1) — row_open/row_close are
its bracket primitives and ARE handled here (see _bracket_rows), but the
broader reactive-binding graph is not. See DEFERRED_CONTAINERS.

Reference: https://a2ui.org/specification/v1.0-a2ui/
"""
import uuid
from typing import List, Dict, Any, Optional, Tuple

A2UI_VERSION = "v1.0"
# catalogId MUST be a resolvable URI (Google's basic catalog uses its full URL) — a
# bare token can't be dereferenced by a host. This is what createSurface.catalogId
# carries; it points at public/catalogue/a2ui-atoms-v1.json served from the site.
DEFAULT_CATALOG_ID = "https://a2uicatalog.ai/catalogue/a2ui-atoms-v1.json"

# Container atom types this cut does NOT yet transform to A2UI primitives; they
# pass through as extension components (renderable only by a host carrying the
# catalog). Named so the gap is explicit, not silent. (Empty as of B1 — hub and
# split_pane are now handled; kept as an extension point for the next gap.)
DEFERRED_CONTAINERS: set = set()


# ── ID minting ────────────────────────────────────────────────────────────────
class _IdGen:
    """Deterministic, collision-free component IDs. Honours an author-supplied
    `id` when present and unique; otherwise mints `<type>-<n>`."""
    def __init__(self) -> None:
        self._used: set = set()
        self._n = 0

    def take(self, block: Dict[str, Any]) -> str:
        cid = block.get("id")
        if isinstance(cid, str) and cid and cid not in self._used:
            self._used.add(cid)
            return cid
        base = str(block.get("type", "block")).replace(" ", "_")
        while True:
            cand = f"{base}-{self._n}"
            self._n += 1
            if cand not in self._used:
                self._used.add(cand)
                return cand


# ── standard-component mapping (atom type -> A2UI basic-catalog component) ──────
# Each mapper takes the source block and returns the A2UI component props dict
# (WITHOUT id/component — those are stamped by the walker). Return None to fall
# through to pass-through (extension component).
def _text(prefix: str = ""):
    def m(b):
        t = b.get("text", b.get("content", b.get("heading", "")))
        return {"component": "Text", "text": f"{prefix}{t}"}
    return m

def _map_quote(b):
    t = b.get("text", "")
    attr = b.get("attribution")
    body = f"> {t}" + (f"\n> — {attr}" if attr else "")
    return {"component": "Text", "text": body}

def _map_image(b):
    # 2026-08-24: real basic-catalog Image has no `alt` field at all --
    # confirmed by reading catalogs/basic/catalog.json directly. The real
    # accessibility-text field is `description`.
    return {"component": "Image", "url": b.get("url", ""),
            "description": b.get("alt", b.get("caption", ""))}

def _map_divider(b):
    return {"component": "Divider"}

def _map_video(b):
    return {"component": "Video", "url": b.get("url", b.get("video_url", ""))}

def _map_audio(b):
    return {"component": "AudioPlayer", "url": b.get("audio_url", b.get("url", "")), "title": b.get("title", "")}

def _map_icon(b):
    return {"component": "Icon", "name": b.get("name", b.get("icon", ""))}

def _list(marker: str):
    def m(b):
        items = b.get("items", [])
        lines = []
        for i, it in enumerate(items):
            label = it if isinstance(it, str) else (it.get("text") or it.get("label") or "")
            pref = f"{i+1}. " if marker == "1." else "- "
            lines.append(f"{pref}{label}")
        return {"component": "Text", "text": "\n".join(lines)}
    return m

# 2026-08-24: real basic-catalog Button needs `child` (a component id --
# typically pointing at a Text) and REQUIRES `action`, confirmed by reading
# catalogs/basic/catalog.json directly -- no `label` field exists at all.
# Handled as a special case in _emit_block (needs to emit a synthetic Text
# child, which a flat STANDARD_MAP mapper can't do), not a STANDARD_MAP
# entry -- see _BUTTON_TYPES + the Button branch there. Real Action.event
# shape ({event: {name, context}}) was already correct; only `label`/no-
# action were the bugs.
_BUTTON_TYPES = {"ripple_button", "cta_button", "link_button", "glow_button"}


def _map_button_url(b) -> Optional[str]:
    return b.get("url") or b.get("href")


# atom -> mapper. Only clean, lossless-ish maps live here; styling-only variants
# collapse onto the same standard component (their flourish is catalog-scoped).
STANDARD_MAP = {
    "heading": _text("# "), "subheading": _text("## "),
    "body": _text(), "paragraph": _text(), "text_block": _text(), "markdown_block": _text(),
    "quote": _map_quote,
    "image": _map_image,
    "divider": _map_divider,
    "youtube": _map_video, "video_card": _map_video, "video": _map_video,
    "audio_player": _map_audio,
    "google_icon": _map_icon,
    "bullet_list": _list("-"), "numbered_list": _list("1."),
}


# ── container inversion (nested blocks -> flat components + children refs) ──────
def _bracket_rows(blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Pre-pass over a sibling block list: collapse any `row_open` ... `row_close`
    bracketed run (wired-dialect layout primitives that bracket a run of blocks
    rather than nesting them — see apps-script-surface/gas-wired-renderer/
    Code.gs:1936-1942) into a single synthetic `row_bracket` container block,
    BEFORE per-block flattening sees the list. Nested open/close pairs are
    balanced via a depth counter; an unmatched trailing `row_open` brackets the
    remainder of the list (best-effort — never crashes on malformed input).
    Blocks outside any bracket pass through untouched."""
    out: List[Dict[str, Any]] = []
    i, n = 0, len(blocks)
    while i < n:
        b = blocks[i]
        if isinstance(b, dict) and b.get("type") == "row_open":
            depth = 1
            run: List[Dict[str, Any]] = []
            j = i + 1
            while j < n and depth > 0:
                bt = blocks[j].get("type") if isinstance(blocks[j], dict) else None
                if bt == "row_open":
                    depth += 1
                elif bt == "row_close":
                    depth -= 1
                    if depth == 0:
                        break
                run.append(blocks[j])
                j += 1
            bracket = {"type": "row_bracket", "blocks": run}
            for k in ("gap", "align", "style"):          # optional flourish, carried lossless
                if b.get(k) is not None:
                    bracket[k] = b[k]
            out.append(bracket)
            i = j + 1                                     # skip past the matching row_close
            continue
        out.append(b)
        i += 1
    return out


def _child_blocklists(b: Dict[str, Any]) -> Optional[Tuple[str, List[Dict[str, Any]]]]:
    """For a container atom this cut supports, return (a2ui_component, ordered
    child block dicts). None => not a supported container."""
    t = b.get("type")
    if t == "columns":
        # Each item becomes its OWN Column (preserves per-column grouping) —
        # flattening straight into the Row (pre-Phase-0 behaviour) silently lost
        # which block belonged to which column whenever a column held >1 block.
        cols = []
        for item in b.get("items", []):
            cols.append({"type": "_column_item", "blocks": item.get("blocks", []) if isinstance(item, dict) else []})
        return ("Row", cols)
    if t == "_column_item":
        return ("Column", b.get("blocks", []))
    if t == "color_section":
        return ("Column", b.get("blocks", []))
    if t in ("info_card", "card", "glass_card"):
        kids = list(b.get("blocks", []))
        # title/text on the card become leading Text children (lossless)
        lead = []
        if b.get("title"):
            lead.append({"type": "heading", "text": b["title"]})
        if b.get("text"):
            lead.append({"type": "body", "text": b["text"]})
        # Real basic-catalog Card takes ONE `child` id, not a `children` list
        # (confirmed 2026-08-24 by reading catalogs/basic/catalog.json
        # directly) — wrap multiple items in a synthetic Column first, same
        # pattern _column_item/_split_pane_side already use for "need an
        # intermediate wrapper" cases elsewhere in this file. Handled by
        # _emit_block's Card special-case below, not the generic
        # children-list path every other container here uses.
        return ("Card", lead + kids)
    if t == "tabs":
        # each tab's content flattened under a Column; Tabs holds the columns
        cols = []
        for tab in b.get("tabs", []):
            cols.append({"type": "color_section", "blocks": tab.get("blocks", tab.get("content", []))})
        return ("Tabs", cols)
    if t == "modal":
        return ("Modal", b.get("children", b.get("blocks", [])))
    if t == "split_pane":
        # B1: two-panel split -> Row of two Columns, one per side. Each side's
        # own bg (distinct from `columns`, which has no per-item background)
        # is carried through the synthetic `_split_pane_side` type below.
        sides = []
        for side_key in ("left", "right"):
            side = b.get(side_key) or {}
            pane = {"type": "_split_pane_side", "blocks": side.get("blocks", [])}
            if side.get("bg"):
                pane["background"] = side["bg"]
            sides.append(pane)
        return ("Row", sides)
    if t == "_split_pane_side":
        return ("Column", b.get("blocks", []))
    if t == "row_bracket":
        # B1: row_open/row_close bracketed run (see _bracket_rows) -> a Row.
        return ("Row", b.get("blocks", []))
    if "blocks" in b and isinstance(b["blocks"], list) and t not in DEFERRED_CONTAINERS:
        # generic container with a plain nested block list
        return ("Column", b["blocks"])
    return None


def _emit_hub(b: Dict[str, Any], cid: str, components: List[Dict[str, Any]], ids: _IdGen) -> str:
    """B1: hub (2-level subject/slide deck nav, fields: subjects[].{id,label,
    color,slides[].{id,label,blocks}}) -> nested Tabs. A2UI's basic catalog has
    no native 2-level nav primitive, so this composes the closest standard
    shape: outer Tabs = subjects, each subject's panel = an inner Tabs of that
    subject's slides, each slide = a Column of its flattened blocks.

    Unlike this module's other container mappings (which reuse the generic
    `{component, children:[...]}` shape via _child_blocklists), real A2UI Tabs
    carry PER-TAB LABELS as `tabs: [{label, child}]` (one child ref each) —
    see https://a2ui.org/specification/v1.0-a2ui/ — so hub gets a dedicated
    builder rather than forcing labels through the flat-children contract.

    Lossiness: subject/slide `color` and hub-level `background`/
    `nav_background` (nav-rail styling with no Tabs equivalent) are dropped;
    everything else (labels, blocks, ordering) is preserved."""
    outer_tabs: List[Dict[str, Any]] = []
    for subj in b.get("subjects", []):
        inner_tabs: List[Dict[str, Any]] = []
        for slide in subj.get("slides", []):
            slide_blocks = _bracket_rows(slide.get("blocks", []))
            slide_children = [_emit_block(sb, components, ids) for sb in slide_blocks]
            col_id = ids.take({"type": "hub_slide"})
            components.append({"id": col_id, "component": "Column", "children": slide_children})
            inner_tabs.append({"title": slide.get("label", ""), "child": col_id})
        inner_id = ids.take({"type": "hub_subject"})
        components.append({"id": inner_id, "component": "Tabs", "tabs": inner_tabs})
        outer_tabs.append({"title": subj.get("label", ""), "child": inner_id})
    components.append({"id": cid, "component": "Tabs", "tabs": outer_tabs})
    return cid


def _emit_content_tabs(b: Dict[str, Any], cid: str, components: List[Dict[str, Any]], ids: _IdGen) -> str:
    """content_tabs (tabs[].{label, blocks}) -> real A2UI Tabs — the DIRECT
    standard mapping: per-tab labels as `tabs: [{label, child}]`, one Column
    child per pane (spec's own Tabs contract, same shape _emit_hub composes
    two levels of). Unlike legacy `tabs` (code panes forced through
    color_section Columns with labels dropped), content_tabs is label-lossless.
    Lossiness: `accent` and `default_index` only (no Tabs equivalent)."""
    out_tabs: List[Dict[str, Any]] = []
    for tab in b.get("tabs", []):
        pane_blocks = _bracket_rows(tab.get("blocks", []))
        children = [_emit_block(sb, components, ids) for sb in pane_blocks]
        col_id = ids.take({"type": "content_tab_pane"})
        components.append({"id": col_id, "component": "Column", "children": children})
        out_tabs.append({"title": tab.get("label", ""), "child": col_id})
    components.append({"id": cid, "component": "Tabs", "tabs": out_tabs})
    return cid


# ── Phase 0: schema-driven children (spec/childlist-migration-v0.1.md) ──────────
_ATOM_CHILDREN_CACHE: Optional[Dict[str, Dict[str, Any]]] = None

# Atom types with an explicit, hand-written container-inversion case above
# (including the generic `"blocks" in b` fallback in _child_blocklists) — these
# keep their existing handling. Every OTHER atom that declares a `children:`
# block in schema.yaml routes through _emit_declared_children instead.
_EXPLICITLY_HANDLED_TYPES = {
    "hub", "columns", "_column_item", "color_section", "info_card", "card",
    "glass_card", "tabs", "content_tabs", "modal", "split_pane",
    "_split_pane_side", "row_bracket",
}


def _atom_children_schema() -> Dict[str, Dict[str, Any]]:
    """type -> declared `children` block (Phase 0) from atoms/schema.yaml, for
    atoms that declare one. Cached at module scope — schema.yaml is static for
    the life of a process."""
    global _ATOM_CHILDREN_CACHE
    if _ATOM_CHILDREN_CACHE is None:
        import os as _os
        import yaml as _yaml
        root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
        schema = _yaml.safe_load(open(_os.path.join(root, "atoms", "schema.yaml")))
        _ATOM_CHILDREN_CACHE = {
            b["type"]: b["children"]
            for b in schema["blocks"] if isinstance(b, dict) and b.get("type") and b.get("children")
        }
    return _ATOM_CHILDREN_CACHE


def _emit_wrapper_item(item: Any, inner_key: str, components: List[Dict[str, Any]], ids: _IdGen,
                        default_type: str = "_wrapper_item") -> str:
    """Promote a wrapper object (its own properties alongside nested atom
    content at `inner_key`) to its own flat component. ChildList can only ever
    hold a reference, never an inline object with its own properties — so for
    shapes like module_map's `modules[]` ({id,title,icon,...,page:[blocks]}),
    the wrapper itself has to become the referenced component: its own
    properties (minus the nested-content key) become that component's
    properties, and the nested content — if present; may be absent for
    conditional shapes like chat_thread.messages — becomes a ChildList/
    ComponentId at `inner_key` on the new component.

    Single-level inner_key only. hub.subjects's inner_path ('slides.blocks')
    is the one two-level case in the catalogue today; it keeps its own
    dedicated builder (_emit_hub) rather than going through this generic
    path — not worth generalizing to two levels for a single caller."""
    if not isinstance(item, dict):
        cid = ids.take({"type": default_type})
        components.append({"id": cid, "component": default_type, "value": item})
        return cid

    cid = ids.take(item)
    node: Dict[str, Any] = {"id": cid, "component": item.get("type", default_type)}
    for k, v in item.items():
        if k in ("id", "type", inner_key):
            continue
        node[k] = v

    nested = item.get(inner_key)
    if isinstance(nested, list):
        node[inner_key] = [_emit_block(nb, components, ids) for nb in nested if isinstance(nb, dict)]
    elif isinstance(nested, dict):
        node[inner_key] = _emit_block(nested, components, ids)

    components.append(node)
    return cid


def _emit_declared_children(b: Dict[str, Any], cid: str, components: List[Dict[str, Any]], ids: _IdGen) -> str:
    """Flatten an atom's schema-declared child-bearing fields into ID refs,
    generically — driven by atoms/schema.yaml's `children:` block (shape:
    simple/single/wrapper_list/wrapper_single + inner_path) instead of a
    hand-written case per atom type. The atom keeps its OWN component type
    (an extension component under catalogId) rather than being remapped to a
    standard A2UI primitive — unlike _child_blocklists's cases, which exist
    specifically because a clean standard-component mapping exists."""
    decl = _atom_children_schema()[b["type"]]
    node: Dict[str, Any] = {"id": cid, "component": b["type"]}
    child_fields = set(decl.keys())
    for k, v in b.items():
        if k in ("id", "type") or k in child_fields:
            continue
        node[k] = v

    for field, spec in decl.items():
        shape = spec["shape"]
        value = b.get(field)
        if shape == "simple":
            if isinstance(value, list):
                node[field] = [_emit_block(item, components, ids) for item in value if isinstance(item, dict)]
        elif shape == "single":
            if isinstance(value, dict):
                node[field] = _emit_block(value, components, ids)
        elif shape == "wrapper_list":
            if isinstance(value, list):
                inner_key = spec["inner_path"].split(".")[0]
                item_type = f"{b['type']}.{field}"
                node[field] = [_emit_wrapper_item(item, inner_key, components, ids, item_type) for item in value]
        elif shape == "wrapper_single":
            if isinstance(value, dict):
                inner_key = spec["inner_path"].split(".")[0]
                item_type = f"{b['type']}.{field}"
                node[field] = _emit_wrapper_item(value, inner_key, components, ids, item_type)

    components.append(node)
    return cid


def _emit_block(b: Dict[str, Any], components: List[Dict[str, Any]], ids: _IdGen) -> str:
    """Append the flattened component(s) for `b` (and its descendants) to
    `components`; return this block's minted component id."""
    cid = ids.take(b)

    if b.get("type") == "hub":
        return _emit_hub(b, cid, components, ids)
    if b.get("type") == "content_tabs":
        return _emit_content_tabs(b, cid, components, ids)

    btype = b.get("type")
    if btype not in _EXPLICITLY_HANDLED_TYPES and btype in _atom_children_schema():
        return _emit_declared_children(b, cid, components, ids)

    container = _child_blocklists(b)
    if container is not None:
        comp_type, child_blocks = container
        child_blocks = _bracket_rows(child_blocks)          # B1: resolve row_open/row_close first
        child_ids = [_emit_block(cb, components, ids) for cb in child_blocks]

        if comp_type == "Card":
            # Real basic-catalog Card.child is ONE id, not a list (confirmed
            # 2026-08-24) -- wrap >1 items in a synthetic Column so Card
            # still gets a single, valid child ref; pass a lone item straight
            # through with no extra wrapper (matches this file's own "don't
            # add a node the shape didn't need" instinct elsewhere).
            if len(child_ids) == 1:
                single_child = child_ids[0]
            elif not child_ids:
                # child is REQUIRED on real Card -- an info_card with no
                # title/text/blocks at all is empty content, not an
                # invalid message; give it a real, empty, valid child
                # rather than crash on child_ids[0] or omit a required field.
                empty_id = ids.take({"type": "card_empty"})
                components.append({"id": empty_id, "component": "Text", "text": ""})
                single_child = empty_id
            else:
                wrap_id = ids.take({"type": "card_content"})
                components.append({"id": wrap_id, "component": "Column", "children": child_ids})
                single_child = wrap_id
            node = {"id": cid, "component": "Card", "child": single_child}
            components.append(node)
            return cid

        node = {"id": cid, "component": comp_type, "children": child_ids}
        # carry a light label/flourish where present (Card/Tabs/Modal titles;
        # row_bracket align). 2026-08-24: confirmed against the real basic
        # catalog that Row/Column have NO `gap`, `style`, or `background`
        # field at all -- `align` is the only one of these that's real.
        # split_pane side backgrounds and row_bracket gap/style are dropped
        # (real, checked loss, not an oversight -- same "no basic-catalog
        # equivalent" pattern this file's own hub docstring already
        # documents for subject/slide color and hub-level background).
        if b.get("title") and comp_type in ("Modal",):
            node["title"] = b["title"]
        if b.get("type") == "row_bracket" and b.get("align") is not None:
            node["align"] = b["align"]
        components.append(node)
        return cid

    if b.get("type") in _BUTTON_TYPES:
        url = _map_button_url(b)
        if url is not None:
            # Only map to real Button when there's a genuine action to give
            # it -- action is REQUIRED on the real schema, and fabricating
            # a fake agent event for a button with no defined behaviour
            # (confirmed real, e.g. a decorative demo button) would be
            # dishonest. No url -> falls through to pass-through below,
            # same "a host without the catalog simply skips it" contract
            # every other unmapped extension gets.
            label = b.get("label", b.get("text", "Button"))
            label_id = ids.take({"type": "button_label"})
            components.append({"id": label_id, "component": "Text", "text": label})
            node = {"id": cid, "component": "Button", "child": label_id,
                   "action": {"event": {"name": "openUrl", "context": {"url": url}}}}
            components.append(node)
            return cid

    mapper = STANDARD_MAP.get(b.get("type"))
    if mapper is not None:
        node = mapper(b)
        if node is not None:
            node["id"] = cid
            components.append(node)
            return cid

    # pass-through: extension component (renderable only under the catalogId).
    node = {"id": cid, "component": b.get("type", "Unknown")}
    for k, v in b.items():
        if k not in ("id", "type"):
            node[k] = v
    components.append(node)
    return cid


# ── public API ─────────────────────────────────────────────────────────────────
def emit_surface(payload: Dict[str, Any], surface_id: Optional[str] = None,
                 catalog_id: str = DEFAULT_CATALOG_ID) -> Dict[str, Any]:
    """Convert a catalogue *blocks*-dialect payload
    ({title?, theme?, blocks:[...]}) into an A2UI v1.0 `createSurface` message.

    Top-level blocks are gathered under a single root `Column` (A2UI renders a
    surface from a component tree; the flat list carries parent→child refs)."""
    if not isinstance(payload, dict):
        raise TypeError("payload must be a dict (blocks dialect)")
    blocks = payload.get("blocks")
    if not isinstance(blocks, list):
        raise ValueError("payload has no top-level 'blocks' list — not the blocks dialect")

    ids = _IdGen()
    components: List[Dict[str, Any]] = []
    blocks = _bracket_rows(blocks)                        # B1: resolve top-level row_open/row_close
    root_children = [_emit_block(b, components, ids) for b in blocks]
    components.append({"id": "root", "component": "Column", "children": root_children})

    # 2026-08-24: `surfaceProperties` is NOT a real v1.0 field (confirmed
    # against the live spec — CreateSurfaceMessage.createSurface has
    # surfaceId/catalogId/sendDataModel/components/dataModel/metadata, no
    # such key). title/theme/catalogs are a2uicatalog's OWN metadata, not
    # part of core A2UI, so they ride in the real spec's own sanctioned
    # extension point: metadata.extensions, namespaced under a prefix that
    # ISN'T `a2ui_` (common_types.json#/$defs/Extensions reserves that
    # prefix for OFFICIAL extensions only). Rejected alternative: stuffing
    # these into `dataModel` — that field is meant to be pure application
    # state a renderer binds UI to, not envelope metadata about the surface
    # itself.
    surface_ext: Dict[str, Any] = {}
    if payload.get("title"):
        surface_ext["title"] = payload["title"]
    if payload.get("theme"):
        surface_ext["theme"] = payload["theme"]

    # Auto-declare the catalogs this surface draws from — DETERMINISTIC, derived from the
    # payload's atoms (renderers.catalog_map), never hand-picked. catalogId stays the base
    # (required, singular); this states the full resolvable set so a host knows exactly
    # what to load and the agent never chooses catalogs itself.
    try:
        from renderers.catalog_map import required_catalogs
    except ImportError:                                # allow direct-script/relative import
        from catalog_map import required_catalogs
    surface_ext["catalogs"] = required_catalogs(payload.get("blocks", []))

    surface: Dict[str, Any] = {
        "surfaceId": surface_id or _slugify(payload.get("title", "surface")),
        "catalogId": catalog_id,
        "components": components,
    }
    if surface_ext:
        surface["metadata"] = {"extensions": {"a2uicatalog_surface": surface_ext}}

    return {"version": A2UI_VERSION, "createSurface": surface}


# 2026-08-24: action_response() removed. The real spec has NO "actionResponse"
# message type at all (confirmed against renderer_to_agent.json's real oneOf:
# action/callAgentFunction/rendererFunctionResponse/error — no response
# concept for `action`). `action` is one-way: the renderer reports what a
# user did; the agent's actual reaction IS whatever createSurface/
# updateComponents/updateDataModel it sends next, not a special reply
# envelope. This had zero callers (confirmed) so nothing else changes.
#
# The correlation question this raised (how does code that receives an
# `action` know which later updateDataModel call is its response?) turns
# out not to need new machinery: the code that DISPATCHES an action already
# knows the surfaceId/path the result belongs at, because it's the one that
# looked up what the action means. That's exactly what
# update_data_model()'s existing signature already takes as arguments — the
# correlation lives in ordinary application code deciding where to push a
# result, not in a wire-level id the protocol was ever going to carry.


# ── C1: callRendererFunction / rendererFunctionResponse, and the reverse pair ───
# Real spec, confirmed by reading agent_to_renderer.json and
# renderer_to_agent.json directly: TWO structurally different, direction-
# specific pairs, not one bidirectional callFunction/functionResponse (the
# old code's shape, which doesn't exist in the real protocol at all).
#   agent -> renderer: `callRendererFunction` (this module emits it, asking
#     the renderer to run one of ITS registered functions) ... the renderer
#     replies `rendererFunctionResponse` (renderer -> agent) — RECEIVING and
#     parsing that reply is a transport/dispatch concern, out of scope for
#     this emitter module (same as this module never parses `action` either).
#   renderer -> agent: `callAgentFunction` (the renderer asks THIS module,
#     acting as agent, to run something) ... this module answers with
#     `agentFunctionResponse` (agent -> renderer) — the RECEIVE side of
#     callAgentFunction is a transport/dispatch concern too; this module
#     only builds the emitted reply once dispatch elsewhere decides one is
#     needed.
# Both response messages wrap the SAME common_types.json#/$defs/FunctionResponse
# shape ({functionCallId, value|error} — no `call` field at all, confirmed;
# the old function_response()'s assumption of one was never real either).
def call_renderer_function(catalog_id: str, call: str, args: Optional[Dict[str, Any]] = None,
                           function_call_id: Optional[str] = None) -> Dict[str, Any]:
    """Build a v1.0 `callRendererFunction` message: ask the renderer to
    execute `call` (a function registered under `catalog_id`) with `args`.
    catalogId is REQUIRED on the real schema — unlike everything else in
    this module, there is no sensible default; the caller must know which
    catalog the function it's calling belongs to. Auto-mints a
    functionCallId if the caller doesn't supply one."""
    fid = function_call_id or f"{call}-{uuid.uuid4().hex[:8]}"
    return {
        "version": A2UI_VERSION,
        "callRendererFunction": {
            "functionCallId": fid,
            "callFunction": {"catalogId": catalog_id, "call": call, "args": args or {}},
        },
    }


def _function_response_body(envelope: Dict[str, Any], function_call_id: str) -> Dict[str, Any]:
    """The real, shared FunctionResponse shape both response messages wrap —
    {functionCallId, value} on success, {functionCallId, error: {code,
    message}} on failure (oneOf, exactly one of value/error — confirmed by
    reading common_types.json#/$defs/FunctionResponse directly)."""
    if envelope.get("ok"):
        value = envelope.get("data")
        if envelope.get("total") is not None and isinstance(value, list):
            value = {"items": value, "total": envelope["total"]}
        return {"functionCallId": function_call_id, "value": value}
    return {"functionCallId": function_call_id,
            "error": {"code": "function_call_failed", "message": envelope.get("error", "error")}}


def agent_function_response(envelope: Dict[str, Any], function_call_id: str) -> Dict[str, Any]:
    """Build a v1.0 `agentFunctionResponse` (agent -> renderer): this
    module's reply to a `callAgentFunction` it received from the renderer.
    Adapts the catalogue's own {ok,data,total,error} action-contract
    envelope into the real FunctionResponse shape."""
    return {"version": A2UI_VERSION,
            "agentFunctionResponse": _function_response_body(envelope, function_call_id)}


def _slugify(s: str) -> str:
    out = "".join(c.lower() if c.isalnum() else "-" for c in str(s)).strip("-")
    while "--" in out:
        out = out.replace("--", "-")
    return out or "surface"


if __name__ == "__main__":                                    # CLI: payload file -> v1.0 message JSON
    import sys, json as _json
    if len(sys.argv) < 2:
        sys.exit("usage: python3 renderers/a2ui_v1.py <payload.json> [catalogId]")
    _payload = _json.load(open(sys.argv[1]))
    _catalog = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_CATALOG_ID
    print(_json.dumps(emit_surface(_payload, catalog_id=_catalog), ensure_ascii=False, indent=2))
