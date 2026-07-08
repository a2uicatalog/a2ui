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
    return {"component": "Image", "url": b.get("url", ""), "alt": b.get("alt", b.get("caption", ""))}

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

def _map_button(b):
    label = b.get("label", b.get("text", "Button"))
    out = {"component": "Button", "label": label}
    url = b.get("url") or b.get("href")
    if url:
        out["action"] = {"event": {"name": "openUrl", "context": {"url": url}}}
    return out

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
    "ripple_button": _map_button, "cta_button": _map_button,
    "link_button": _map_button, "glow_button": _map_button,
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
            inner_tabs.append({"label": slide.get("label", ""), "child": col_id})
        inner_id = ids.take({"type": "hub_subject"})
        components.append({"id": inner_id, "component": "Tabs", "tabs": inner_tabs})
        outer_tabs.append({"label": subj.get("label", ""), "child": inner_id})
    components.append({"id": cid, "component": "Tabs", "tabs": outer_tabs})
    return cid


# ── Phase 0: schema-driven children (spec/childlist-migration-v0.1.md) ──────────
_ATOM_CHILDREN_CACHE: Optional[Dict[str, Dict[str, Any]]] = None

# Atom types with an explicit, hand-written container-inversion case above
# (including the generic `"blocks" in b` fallback in _child_blocklists) — these
# keep their existing handling. Every OTHER atom that declares a `children:`
# block in schema.yaml routes through _emit_declared_children instead.
_EXPLICITLY_HANDLED_TYPES = {
    "hub", "columns", "_column_item", "color_section", "info_card", "card",
    "glass_card", "tabs", "modal", "split_pane", "_split_pane_side", "row_bracket",
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

    btype = b.get("type")
    if btype not in _EXPLICITLY_HANDLED_TYPES and btype in _atom_children_schema():
        return _emit_declared_children(b, cid, components, ids)

    container = _child_blocklists(b)
    if container is not None:
        comp_type, child_blocks = container
        child_blocks = _bracket_rows(child_blocks)          # B1: resolve row_open/row_close first
        child_ids = [_emit_block(cb, components, ids) for cb in child_blocks]
        node = {"id": cid, "component": comp_type, "children": child_ids}
        # carry a light label/flourish where present (Card/Tabs/Modal titles;
        # split_pane side backgrounds; row_bracket gap/align/style)
        if b.get("title") and comp_type in ("Modal",):
            node["title"] = b["title"]
        if b.get("type") == "_split_pane_side" and b.get("background"):
            node["background"] = b["background"]
        if b.get("type") == "row_bracket":
            for k in ("gap", "align", "style"):
                if b.get(k) is not None:
                    node[k] = b[k]
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

    surface_props: Dict[str, Any] = {}
    if payload.get("title"):
        surface_props["title"] = payload["title"]
    if payload.get("theme"):
        surface_props["theme"] = payload["theme"]      # theme -> surfaceProperties (0.9->1.0 rename)

    # Auto-declare the catalogs this surface draws from — DETERMINISTIC, derived from the
    # payload's atoms (renderers.catalog_map), never hand-picked. catalogId stays the base
    # (required, singular); surfaceProperties.catalogs states the full resolvable set so a
    # host knows exactly what to load and the agent never chooses catalogs itself.
    try:
        from renderers.catalog_map import required_catalogs
    except ImportError:                                # allow direct-script/relative import
        from catalog_map import required_catalogs
    surface_props["catalogs"] = required_catalogs(payload.get("blocks", []))

    surface: Dict[str, Any] = {
        "surfaceId": surface_id or _slugify(payload.get("title", "surface")),
        "catalogId": catalog_id,
        "components": components,
    }
    if surface_props:
        surface["surfaceProperties"] = surface_props

    return {"version": A2UI_VERSION, "createSurface": surface}


def action_response(envelope: Dict[str, Any], action_id: str) -> Dict[str, Any]:
    """Adapt the catalogue action contract {ok,data,total,error} to A2UI v1.0
    `actionResponse {value | error}` (exactly one of value/error)."""
    if envelope.get("ok"):
        value = envelope.get("data")
        if envelope.get("total") is not None and isinstance(value, list):
            value = {"items": value, "total": envelope["total"]}
        return {"version": A2UI_VERSION, "actionId": action_id, "actionResponse": {"value": value}}
    return {"version": A2UI_VERSION, "actionId": action_id,
            "actionResponse": {"error": {"code": "action_failed", "message": envelope.get("error", "error")}}}


# ── C1: callFunction / functionResponse RPC ─────────────────────────────────────
# Per spec (https://a2ui.org/specification/v1.0-a2ui/): `callFunction` flows
# SERVER -> CLIENT (request the client run a function it has registered);
# `functionResponse` flows CLIENT -> SERVER and carries ONLY a success value —
# a failed call is reported via the separate top-level `error` envelope
# (keyed by functionCallId), not an error field on functionResponse itself.
def call_function(name: str, args: Optional[Dict[str, Any]] = None,
                   function_call_id: Optional[str] = None,
                   want_response: bool = True) -> Dict[str, Any]:
    """Build a v1.0 `callFunction` message: ask the client to execute `name`
    (a function it has registered) with `args`. Auto-mints a functionCallId
    if the caller doesn't supply one (so call sites that don't care about
    correlating the reply can omit it)."""
    fid = function_call_id or f"{name}-{uuid.uuid4().hex[:8]}"
    return {
        "version": A2UI_VERSION,
        "functionCallId": fid,
        "wantResponse": want_response,
        "callFunction": {"call": name, "args": args or {}},
    }


def function_response(envelope: Dict[str, Any], function_call_id: str, call: str) -> Dict[str, Any]:
    """Adapt the catalogue action contract {ok,data,total,error} into the
    client's reply for a prior call_function() — mirrors action_response()'s
    envelope handling, but for the callFunction/functionResponse RPC pair and
    keyed by functionCallId instead of actionId.

    envelope.ok=True  -> `functionResponse` {functionCallId, call, value}.
    envelope.ok=False -> the separate `error` envelope {code, message,
    functionCallId} (functionResponse itself carries no error field per spec)."""
    if envelope.get("ok"):
        value = envelope.get("data")
        if envelope.get("total") is not None and isinstance(value, list):
            value = {"items": value, "total": envelope["total"]}
        return {"version": A2UI_VERSION,
                "functionResponse": {"functionCallId": function_call_id, "call": call, "value": value}}
    return {"version": A2UI_VERSION,
            "error": {"code": "function_call_failed", "message": envelope.get("error", "error"),
                      "functionCallId": function_call_id}}


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
