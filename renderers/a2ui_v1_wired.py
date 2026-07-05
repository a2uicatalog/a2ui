"""a2ui_v1_wired — emit A2UI protocol v1.0 (Google, https://a2ui.org) createSurface
messages from the catalogue's *wired* (stateful) dialect.

Companion to renderers/a2ui_v1.py (the *blocks* dialect emitter — imported, not
edited). The wired dialect ({state_primitives, actions, layout} with `#node.field`
wires; see spec/a2ui-state.yaml and payloads/expenses-demo.json) carries a reactive
client graph that is RICHER than bare A2UI v1.0. This emitter maps the
cleanly-conformant subset onto the protocol's actual state model and flags the
rest as a `catalogId: a2ui-state-v1` extension.

The conformance seam (why this mapping is honest, not lossy-by-accident):
A2UI v1.0 keeps the client simple — a `dataModel` JSON object, JSON-Pointer
property bindings ({"text": {"path": "/x/y"}}), a `List` template
(children: {path, componentId}), and an `action`/`actionResponse` RPC
(https://a2ui.org/specification/v1.0-a2ui/). The catalogue's own normative
derivation boundary (spec/gas-actions-v1.yaml + spec/a2ui-state.yaml:
"the client engine derives over ONE delivered array within ONE render;
anything temporal/aggregate/joined is server-side") lands at exactly the same
granularity as A2UI's dataModel. So the submit+reload-shaped subset maps 1:1:

CONFORMANT SUBSET (emitted as bare A2UI v1.0)
  - layout entries {atom, id?, props, wire}  →  flat `components`
    [{id, component, ...props FLATTENED}], root Column, deterministic IDs
    (reuses a2ui_v1's _IdGen + STANDARD_MAP for text-ish atoms).
  - ValueStore primitive        →  dataModel entry {"<id>": {"value": initialValue}};
    read wire `#id.value` → {"path": "/<id>/value"}.
  - input atom wire onChange:"#mem.setValue"  →  two-way `value: {path}` binding
    (per spec: "the client immediately updates the value at the bound path in the
    local Data Model") + createSurface.sendDataModel: true.
  - action trigger:"onLoad"     →  pre-resolved SERVER-SIDE (optional
    `resolve_action` hook returning the catalogue envelope {ok,data,total,error})
    and embedded directly in createSurface.dataModel at /<actionId>/result —
    no client round-trip needed, a strict simplification.
  - server-array reads `#action.result` (sheet_query / store_read / store_derive
    outputs) → {"path": "/<actionId>/result"}.
  - data_table with a conformant rows source → Column[header Row + List] where
    List.children = {path: "/<actionId>/result", componentId: "<id>-row"} and the
    row template's cells use RELATIVE JSON-Pointer bindings ({"path": "colKey"}),
    per the spec's collection-scope rule.
  - button wire onClick:"#action.run" + actions[].props.collect →
    action: {event: {name, context: <collect with wire refs resolved to {path}
    bindings, literals/{{templates}} passed verbatim for server resolution>,
    wantResponse: true, responsePath}, actionId: <deterministic>}.
    onSuccess: [reloadAction] → responsePath = "/<reloadAction>/result" — the
    server answers the submit with the refreshed array (actionResponse.value
    lands at responsePath; the List re-renders). That IS the submit+reload loop.
  - the catalogue action envelope {ok,data,total,error} → actionResponse
    {value | error} via a2ui_v1.action_response (re-exported).

DEGRADED-BUT-RENDERABLE (documented in surfaceProperties.extensions.notes)
  - a read of `#arrayFilter.output` is traced ONE conformant hop to the filter's
    delivered source array (action push wire / wire.source / static props.source)
    and bound there UNFILTERED. A bare host renders the full array; a host
    carrying a2ui-state-v1 upgrades to live filtering. Static non-empty
    props.source arrays are embedded at /<filterId>/source.

EXTENSION-ONLY (emitted under catalogId a2ui-state-v1 — pass-through, flagged in
surfaceProperties.extensions; NOT forced into bare A2UI)
  - reactive primitives: ArrayFilter, Computed, DerivedStore, StringValidator,
    NumericThreshold, Timer, StepNavigator — emitted as non-visual flat
    components {id, component: <Primitive>, ...props, wire} outside the root
    tree (a host without the catalog skips them — correct A2UI behaviour).
  - action lifecycle reads (#action.isPending/isSuccess/isError/error/status) and
    any wire into a validator/threshold/computed field: the owning layout atom
    keeps its original `wire` dict (pass-through) and is flagged; if the atom is
    otherwise standard-mappable it is still emitted as the standard component
    with its conformant wires resolved (extension-enhanced, not extension-lost).
  - clearOnSuccess (form reset) and Timer-triggered actions (wire.trigger) —
    no bare-A2UI equivalent; recorded as notes.
  - the payload `app` block (auth/storage/lifecycle) is server configuration,
    not UI — intentionally not serialized into the surface.

Reference: https://a2ui.org/specification/v1.0-a2ui/
"""
import re
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

try:  # package import (tests: `from renderers.a2ui_v1_wired import ...`)
    from .a2ui_v1 import (A2UI_VERSION, STANDARD_MAP, _IdGen, _slugify,
                          action_response)
except ImportError:  # direct CLI run from repo root or renderers/
    import os as _os
    import sys as _sys
    _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
    from a2ui_v1 import (A2UI_VERSION, STANDARD_MAP, _IdGen, _slugify,  # noqa: F401
                         action_response)

__all__ = ["emit_wired_surface", "action_response", "A2UI_VERSION",
           "DEFAULT_CATALOG_ID", "DEFAULT_STATE_CATALOG_ID"]

# resolvable URIs, not bare tokens — see renderers/a2ui_v1.py
DEFAULT_CATALOG_ID = "https://a2uicatalog.ai/catalogue/a2ui-atoms-v1.json"
DEFAULT_STATE_CATALOG_ID = "https://a2uicatalog.ai/catalogue/a2ui-state-v1.json"

# state primitives that dissolve into the A2UI dataModel (no component emitted)
CONFORMANT_PRIMITIVES = {"ValueStore"}
# action node readable fields that only the a2ui-state-v1 engine surfaces
ACTION_LIFECYCLE_FIELDS = {"isPending", "isSuccess", "isError", "error", "status"}

# wired input atoms -> A2UI standard input components (two-way `value` binding)
WIRED_INPUT_MAP = {
    "text_input": "TextField",
    "form_input": "TextField",
    "search_input": "TextField",
    "textarea": "TextField",
    "checkbox": "CheckBox",
    "toggle": "CheckBox",
    "slider": "Slider",
    "date_input": "DateTimeInput",
}

_REF_RE = re.compile(r"^#([A-Za-z0-9_\-]+)\.([A-Za-z0-9_\-]+)$")


def _parse_ref(v: Any) -> Optional[Tuple[str, str]]:
    """'#nodeId.field' -> (nodeId, field); anything else -> None."""
    if not isinstance(v, str):
        return None
    m = _REF_RE.match(v)
    return (m.group(1), m.group(2)) if m else None


# ── wired-payload context: node registry + wire resolution ────────────────────
class _WiredContext:
    def __init__(self, payload: Dict[str, Any],
                 resolve_action: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]],
                 state_catalog_id: str) -> None:
        self.state_catalog_id = state_catalog_id
        self.resolve_action = resolve_action
        prims = payload.get("state_primitives") or []
        self.value_stores: Dict[str, Dict[str, Any]] = {}
        self.ext_prims: Dict[str, Dict[str, Any]] = {}
        for p in prims:
            pid = p.get("id")
            if not pid:
                continue
            if p.get("primitive") in CONFORMANT_PRIMITIVES:
                self.value_stores[pid] = p
            else:
                self.ext_prims[pid] = p
        self.actions: Dict[str, Dict[str, Any]] = {
            a["id"]: a for a in (payload.get("actions") or []) if a.get("id")
        }
        # action output pushed into a primitive input, e.g. an onLoad query's
        # wire {result: "#filter.source"} — inverted here so filter-source
        # tracing can find the delivered array's dataModel path.
        self.pushed_source: Dict[str, str] = {}   # primId -> actionId
        for aid, a in self.actions.items():
            for out_field, target in (a.get("wire") or {}).items():
                t = _parse_ref(target)
                if out_field == "result" and t and t[1] == "source":
                    self.pushed_source[t[0]] = aid
        # collected while emitting
        self.needed_action_slots: Set[str] = set()   # actions whose /id/result must exist
        self.static_embeds: Dict[str, Dict[str, Any]] = {}  # extra dataModel entries
        self.extension_ids: Set[str] = set()
        self.notes: List[str] = []
        self.send_data_model = False

    # ---- read-wire resolution: '#node.field' -> JSON Pointer or None ---------
    def resolve_read(self, ref: Any, _seen: Optional[Set[str]] = None) -> Optional[str]:
        parsed = _parse_ref(ref)
        if not parsed:
            return None
        node, field = parsed
        if node in self.value_stores:
            return f"/{node}/value" if field == "value" else None
        if node in self.actions:
            if field == "result":
                self.needed_action_slots.add(node)
                return f"/{node}/result"
            if field == "total":
                self.needed_action_slots.add(node)
                return f"/{node}/total"
            return None  # lifecycle fields -> extension
        prim = self.ext_prims.get(node)
        if prim and prim.get("primitive") == "ArrayFilter" and field == "output":
            seen = _seen or set()
            if node in seen:
                return None
            seen.add(node)
            src = self._filter_source_path(node, prim, seen)
            if src:
                self.notes.append(
                    f"'{ref}' degraded to unfiltered source '{src}' — ArrayFilter "
                    f"'{node}' requires {self.state_catalog_id}")
                return src
        return None

    def _filter_source_path(self, fid: str, prim: Dict[str, Any],
                            seen: Set[str]) -> Optional[str]:
        """Trace an ArrayFilter to the ONE delivered array it derives over."""
        if fid in self.pushed_source:                       # action → filter push
            aid = self.pushed_source[fid]
            self.needed_action_slots.add(aid)
            return f"/{aid}/result"
        src_ref = (prim.get("wire") or {}).get("source")     # filter pulls source
        if src_ref:
            return self.resolve_read(src_ref, seen)
        static = (prim.get("props") or {}).get("source")     # static rows
        if isinstance(static, list) and static:
            self.static_embeds[fid] = {"source": static}
            return f"/{fid}/source"
        return None

    # ---- '#action.run' -> component `action` object --------------------------
    def action_for(self, action_id: str) -> Optional[Dict[str, Any]]:
        a = self.actions.get(action_id)
        if a is None:
            return None
        context: Dict[str, Any] = {}
        collect = (a.get("props") or {}).get("collect") or {}
        for key, val in collect.items():
            path = self.resolve_read(val)
            if path:
                context[key] = {"path": path}     # resolved at fire time from dataModel
            else:
                if _parse_ref(val):
                    self.notes.append(
                        f"collect '{key}': '{val}' not conformant — passed verbatim "
                        f"(requires {self.state_catalog_id})")
                context[key] = val                 # literal / {{template}} — server resolves
        on_success = [x for x in (a.get("onSuccess") or []) if x in self.actions]
        # submit+reload: the server answers with the refreshed array; writing it
        # at the reload action's result path re-renders every List bound there.
        target = on_success[0] if on_success else action_id
        self.needed_action_slots.add(target)
        if a.get("clearOnSuccess"):
            self.notes.append(
                f"action '{action_id}': clearOnSuccess deferred to "
                f"{self.state_catalog_id} (no bare-A2UI form-reset primitive)")
        return {
            "event": {
                "name": action_id,
                "context": context,
                "wantResponse": True,
                "responsePath": f"/{target}/result",
            },
            # deterministic correlation id so this emitter's server side can
            # answer with action_response(envelope, actionId) (hosts may mint
            # their own per-fire ids; this one makes the round trip testable).
            "actionId": action_id,
        }


# ── layout emission ────────────────────────────────────────────────────────────
def _emit_table(cid: str, props: Dict[str, Any], rows_path: str,
                components: List[Dict[str, Any]], ids: _IdGen) -> None:
    """data_table → Column[header Row, List(template Row of Text cells)].
    Cell bindings are RELATIVE JSON Pointers (collection scope per spec)."""
    cols = props.get("columns") or []
    header_ids, cell_ids = [], []
    for col in cols:
        if isinstance(col, dict):   # column-hint objects: key + label conform; hints are catalog-scoped
            key = col.get("key") or col.get("field") or col.get("label") or "value"
            label = col.get("label") or key
        else:
            key, label = str(col), str(col)
        hid = ids.take({"id": f"{cid}-h-{key}", "type": "text"})
        components.append({"id": hid, "component": "Text", "text": str(label)})
        header_ids.append(hid)
        tid = ids.take({"id": f"{cid}-c-{key}", "type": "text"})
        components.append({"id": tid, "component": "Text", "text": {"path": key}})
        cell_ids.append(tid)
    header_id = ids.take({"id": f"{cid}-header", "type": "row"})
    components.append({"id": header_id, "component": "Row", "children": header_ids})
    row_tpl_id = ids.take({"id": f"{cid}-row", "type": "row"})
    components.append({"id": row_tpl_id, "component": "Row", "children": cell_ids})
    list_id = ids.take({"id": f"{cid}-list", "type": "list"})
    components.append({"id": list_id, "component": "List",
                       "children": {"path": rows_path, "componentId": row_tpl_id}})
    components.append({"id": cid, "component": "Column",
                       "children": [header_id, list_id]})


def _emit_layout_entry(entry: Dict[str, Any], components: List[Dict[str, Any]],
                       ids: _IdGen, ctx: _WiredContext) -> str:
    atom = entry.get("atom") or entry.get("type") or "Unknown"
    props = dict(entry.get("props") or {})
    wire = entry.get("wire") or {}
    cid = ids.take({"id": entry.get("id"), "type": atom})

    # classify this entry's wires
    bindings: Dict[str, str] = {}        # prop -> absolute JSON Pointer (read)
    ext_wires: Dict[str, Any] = {}       # prop -> raw ref (a2ui-state-v1 only)
    action_obj: Optional[Dict[str, Any]] = None
    twoway_path: Optional[str] = None
    for prop, ref in wire.items():
        parsed = _parse_ref(ref)
        if parsed:
            node, field = parsed
            if field == "setValue" and node in ctx.value_stores:
                twoway_path = f"/{node}/value"
                ctx.send_data_model = True
                continue
            if field == "run" and node in ctx.actions:
                action_obj = ctx.action_for(node)
                if action_obj is not None:
                    continue
            path = ctx.resolve_read(ref)
            if path:
                bindings[prop] = path
                continue
        ext_wires[prop] = ref

    # 1) data_table with a conformant delivered-array source → List cluster
    if atom == "data_table" and "rows" in bindings:
        _emit_table(cid, props, bindings.pop("rows"), components, ids)
        node = components[-1]            # the wrapper Column
        leftover = dict(bindings)
        leftover.update(ext_wires)
        if leftover:
            node["wire"] = {k: wire[k] for k in wire if k != "rows"}
            ctx.extension_ids.add(cid)
        return cid

    # 2) standard input atoms → two-way bound input component
    if atom in WIRED_INPUT_MAP:
        node = {"id": cid, "component": WIRED_INPUT_MAP[atom]}
        if props.get("label"):
            node["label"] = props["label"]
        for k, v in props.items():       # carry remaining static props flat
            if k != "label":
                node[k] = v
        if twoway_path:
            node["value"] = {"path": twoway_path}
        for prop, path in bindings.items():
            node[prop] = {"path": path}
        if ext_wires:
            node["wire"] = ext_wires
            ctx.extension_ids.add(cid)
        components.append(node)
        return cid

    # 3) blocks-dialect standard mapping (headings, text, buttons, media, …)
    mapper = STANDARD_MAP.get(atom)
    if mapper is not None:
        node = mapper({"type": atom, **props})
        if node is not None:
            node["id"] = cid
            for prop, path in bindings.items():
                node[prop] = {"path": path}
            if action_obj is not None:
                node["action"] = action_obj
            if ext_wires:
                node["wire"] = ext_wires
                ctx.extension_ids.add(cid)
            components.append(node)
            return cid

    # 4) pass-through: extension component under the atoms/state catalogs.
    node = {"id": cid, "component": atom}
    node.update(props)
    for prop, path in bindings.items():   # keep what DID resolve — a bare host
        node[prop] = {"path": path}       # ignores the rest, a state host upgrades
    if action_obj is not None:
        node["action"] = action_obj
    if ext_wires:
        node["wire"] = ext_wires
    if ext_wires or atom not in WIRED_INPUT_MAP:
        ctx.extension_ids.add(cid)
    components.append(node)
    return cid


# ── public API ─────────────────────────────────────────────────────────────────
def emit_wired_surface(payload: Dict[str, Any], surface_id: Optional[str] = None,
                       catalog_id: str = DEFAULT_CATALOG_ID,
                       state_catalog_id: str = DEFAULT_STATE_CATALOG_ID,
                       resolve_action: Optional[Callable[[Dict[str, Any]],
                                                         Dict[str, Any]]] = None
                       ) -> Dict[str, Any]:
    """Convert a catalogue *wired*-dialect payload into an A2UI v1.0
    `createSurface` message dict (see module docstring for the exact subset).

    resolve_action: optional server-side hook `(action_dict) -> {ok,data,total,
    error}` used to pre-resolve `trigger: "onLoad"` actions into the delivered
    dataModel (the emitter runs where the data lives — this is the wired
    dialect's load-on-open, done before the surface ships). Without it, onLoad
    result slots ship empty (result: []) but every pointer still resolves.
    """
    if not isinstance(payload, dict):
        raise TypeError("payload must be a dict (wired dialect)")
    if payload.get("type") != "a2ui_wired_surface" and "layout" not in payload:
        raise ValueError(
            "payload is not the wired dialect (want type: 'a2ui_wired_surface' "
            "or a top-level 'layout' list)")
    layout = payload.get("layout") or []
    if not isinstance(layout, list):
        raise ValueError("'layout' must be a list of {atom, props, wire} entries")

    ctx = _WiredContext(payload, resolve_action, state_catalog_id)
    ids = _IdGen()
    components: List[Dict[str, Any]] = []

    root_children = [_emit_layout_entry(e, components, ids, ctx) for e in layout]
    components.append({"id": "root", "component": "Column", "children": root_children})

    # reactive primitives → non-visual extension components (outside root tree)
    for pid, prim in ctx.ext_prims.items():
        node = {"id": ids.take({"id": pid, "type": prim.get("primitive", "Primitive")}),
                "component": prim.get("primitive", "Primitive")}
        node.update(prim.get("props") or {})
        if prim.get("wire"):
            node["wire"] = prim["wire"]
        components.append(node)
        ctx.extension_ids.add(node["id"])

    # dataModel: ValueStores + onLoad-resolved arrays + referenced action slots
    data_model: Dict[str, Any] = {}
    for sid, vs in ctx.value_stores.items():
        data_model[sid] = {"value": (vs.get("props") or {}).get("initialValue")}
        if (vs.get("props") or {}).get("persist"):
            ctx.notes.append(
                f"ValueStore '{sid}': persist deferred to {state_catalog_id} "
                "(server-durable progress store)")
    for aid, a in ctx.actions.items():
        if a.get("trigger") == "onLoad":
            slot: Dict[str, Any] = {"result": []}
            if resolve_action is not None:
                env = resolve_action(a) or {}
                if env.get("ok"):
                    slot["result"] = env.get("data", [])
                    if env.get("total") is not None:
                        slot["total"] = env["total"]
                else:
                    ctx.notes.append(
                        f"onLoad action '{aid}' failed to pre-resolve: "
                        f"{env.get('error', 'no envelope')}")
            data_model[aid] = slot
        elif (a.get("wire") or {}).get("trigger"):
            ctx.notes.append(
                f"action '{aid}': wire.trigger ({a['wire']['trigger']}) deferred "
                f"to {state_catalog_id} (Timer-driven actions)")
    for aid in sorted(ctx.needed_action_slots):
        data_model.setdefault(aid, {"result": []})
    data_model.update(ctx.static_embeds)

    surface_props: Dict[str, Any] = {}
    if payload.get("title"):
        surface_props["title"] = payload["title"]
    if payload.get("theme"):
        surface_props["theme"] = payload["theme"]
    if ctx.extension_ids or ctx.notes:
        surface_props["extensions"] = {
            "catalogId": state_catalog_id,
            "componentIds": sorted(ctx.extension_ids),
            "notes": ctx.notes,
        }

    surface: Dict[str, Any] = {
        "surfaceId": surface_id or _slugify(payload.get("title", "surface")),
        "catalogId": catalog_id,
        "components": components,
    }
    if data_model:
        surface["dataModel"] = data_model
    if ctx.send_data_model:
        surface["sendDataModel"] = True
    if surface_props:
        surface["surfaceProperties"] = surface_props

    return {"version": A2UI_VERSION, "createSurface": surface}


if __name__ == "__main__":               # CLI: wired payload file -> v1.0 message JSON
    import json as _json
    import sys as _sys2
    if len(_sys2.argv) < 2:
        _sys2.exit("usage: python3 renderers/a2ui_v1_wired.py <payload.json> [catalogId]")
    _payload = _json.load(open(_sys2.argv[1]))
    _catalog = _sys2.argv[2] if len(_sys2.argv) > 2 else DEFAULT_CATALOG_ID
    print(_json.dumps(emit_wired_surface(_payload, catalog_id=_catalog),
                      ensure_ascii=False, indent=2))
