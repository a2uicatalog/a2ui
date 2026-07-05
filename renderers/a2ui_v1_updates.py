"""a2ui_v1_updates — A2UI protocol v1.0 server-to-client INCREMENTAL messages
(updateComponents / updateDataModel / deleteSurface) + the reference client-state
applier + a channel abstraction (poll-compliant + push).

This is A2UI conformance track C2. Two capabilities:
  1. COMPLIANCE for what we already have — `poll_result_to_update()` turns a
     polled action envelope ({ok,data,total,error}) into a conformant
     `updateDataModel` message, so the wired renderer's `live_refresh` polling
     speaks the protocol instead of an ad-hoc shape.
  2. PUSH — the same messages, delivered over a real server->client channel.
     `Channel` is the transport-agnostic contract; `PollChannel` wraps the
     existing pull-on-a-timer model, `FirestorePushChannel` enqueues messages to
     Firestore for a client onSnapshot subscriber (true push).

`apply_update()` is the REFERENCE receive semantics (RFC 6901 JSON-pointer patch,
component upsert-by-id, surface teardown) — a client SHOULD behave identically.

Exact shapes: https://a2ui.org/specification/v1.0-a2ui/ (server-to-client messages).
"""
import copy
from typing import Any, Dict, List, Optional, Callable

from renderers.a2ui_v1 import A2UI_VERSION

_OMITTED = object()   # sentinel: distinguishes "no value" (delete at path) from value=None


# ── emit: the three incremental messages ───────────────────────────────────────
def update_components(surface_id: str, components: List[Dict[str, Any]]) -> Dict[str, Any]:
    """v1.0 updateComponents — upsert-by-id a list of components into a surface."""
    return {"version": A2UI_VERSION,
            "updateComponents": {"surfaceId": surface_id, "components": components}}


def update_data_model(surface_id: str, value: Any = _OMITTED, path: str = "/") -> Dict[str, Any]:
    """v1.0 updateDataModel — replace the value at `path` (JSON Pointer). path='/'
    replaces the whole data model; omitting `value` REMOVES the key at `path`."""
    inner: Dict[str, Any] = {"surfaceId": surface_id, "path": path}
    if value is not _OMITTED:
        inner["value"] = value
    return {"version": A2UI_VERSION, "updateDataModel": inner}


def delete_surface(surface_id: str) -> Dict[str, Any]:
    """v1.0 deleteSurface — remove a surface and all its components + data."""
    return {"version": A2UI_VERSION, "deleteSurface": {"surfaceId": surface_id}}


# ── compliance adapter: make our polling speak the protocol ─────────────────────
def poll_result_to_update(surface_id: str, envelope: Dict[str, Any], path: str) -> Dict[str, Any]:
    """Adapt a polled action envelope ({ok,data,total,error}) — what the wired
    renderer's live_refresh timer receives — into a conformant updateDataModel.
    On ok, patches the fresh data at `path`; on failure, patches an error object
    (so the surface can render the failure honestly rather than go stale)."""
    if envelope.get("ok"):
        value: Any = envelope.get("data")
        if envelope.get("total") is not None and isinstance(value, list):
            value = {"items": value, "total": envelope["total"]}
        return update_data_model(surface_id, value=value, path=path)
    return update_data_model(surface_id,
                             value={"error": envelope.get("error", "error")}, path=path)


# ── reference client-state + applier (RFC 6901) ─────────────────────────────────
def surface_state_from_create(msg: Dict[str, Any]) -> Dict[str, Any]:
    """Build the mutable client registry a receiver maintains, from a createSurface
    message: components as an id->component map, plus the data model + surfaceId."""
    cs = msg["createSurface"]
    return {
        "surfaceId": cs["surfaceId"],
        "catalogId": cs.get("catalogId"),
        "components": {c["id"]: dict(c) for c in cs.get("components", [])},
        # deep-copy: later pointer-patches must not mutate the source createSurface
        "dataModel": copy.deepcopy(cs.get("dataModel", {})),
        "deleted": False,
    }


def _pointer_tokens(path: str) -> List[str]:
    if path in ("", "/"):
        return []
    return [t.replace("~1", "/").replace("~0", "~") for t in path.lstrip("/").split("/")]


def _pointer_set(root: Dict[str, Any], path: str, value: Any) -> Dict[str, Any]:
    toks = _pointer_tokens(path)
    if not toks:                        # path '/' -> replace whole model
        return value if isinstance(value, dict) else {"": value}
    node = root
    for t in toks[:-1]:
        nxt = node.get(t)
        if not isinstance(nxt, dict):
            nxt = {}
            node[t] = nxt
        node = nxt
    node[toks[-1]] = value
    return root


def _pointer_remove(root: Dict[str, Any], path: str) -> Dict[str, Any]:
    toks = _pointer_tokens(path)
    if not toks:
        return {}
    node = root
    for t in toks[:-1]:
        node = node.get(t)
        if not isinstance(node, dict):
            return root                 # nothing to remove
    node.pop(toks[-1], None)
    return root


def apply_update(state: Dict[str, Any], msg: Dict[str, Any]) -> Dict[str, Any]:
    """Apply one incremental message to a client `state` (from
    surface_state_from_create). Returns the same (mutated) state. Reference
    semantics a conformant client MUST match."""
    if "updateComponents" in msg:
        uc = msg["updateComponents"]
        _guard(state, uc)
        for comp in uc.get("components", []):
            state["components"][comp["id"]] = dict(comp)   # upsert by id
    elif "updateDataModel" in msg:
        ud = msg["updateDataModel"]
        _guard(state, ud)
        path = ud.get("path", "/")
        if "value" in ud:
            state["dataModel"] = _pointer_set(state["dataModel"], path, ud["value"])
        else:
            state["dataModel"] = _pointer_remove(state["dataModel"], path)
    elif "deleteSurface" in msg:
        _guard(state, msg["deleteSurface"])
        state["deleted"] = True
        state["components"] = {}
        state["dataModel"] = {}
    else:
        raise ValueError("not an incremental update message: " + ", ".join(msg))
    return state


def _guard(state: Dict[str, Any], inner: Dict[str, Any]) -> None:
    sid = inner.get("surfaceId")
    if sid is not None and state.get("surfaceId") is not None and sid != state["surfaceId"]:
        raise ValueError(f"surfaceId mismatch: message {sid} != state {state['surfaceId']}")


# ── channel abstraction: transport-agnostic delivery ────────────────────────────
class Channel:
    """Transport contract: something that DELIVERS incremental messages for a
    surface. Subclasses implement how (pull vs push); callers emit() the same
    protocol messages regardless."""
    def emit(self, msg: Dict[str, Any]) -> None:            # pragma: no cover - interface
        raise NotImplementedError


class PollChannel(Channel):
    """Compliance wrapper for the EXISTING pull-on-a-timer model. The client polls
    a named action on a timer (live_refresh); each poll result is adapted to an
    updateDataModel via poll_result_to_update. Not push, but protocol-compliant —
    covers dashboards/feedback pools where poll latency is fine."""
    def __init__(self, surface_id: str, path: str = "/") -> None:
        self.surface_id, self.path, self.buffer = surface_id, path, []

    def from_poll(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        msg = poll_result_to_update(self.surface_id, envelope, self.path)
        self.buffer.append(msg)
        return msg

    def emit(self, msg: Dict[str, Any]) -> None:
        self.buffer.append(msg)


class FirestorePushChannel(Channel):
    """TRUE push: the server enqueues incremental messages to Firestore under
    surface_updates/<surfaceId>; a client onSnapshot subscriber receives them in
    real time and applies them. The Firestore write is INJECTED (a writer callable
    that persists one message) so this is unit-testable and reusable across the
    server surfaces that already hold Firestore (e.g. the trade bot). The
    client-side subscription (JS onSnapshot in the deployed surface) is the live
    transport half — see A2UIState.html wiring; it needs deploy verification."""
    COLLECTION = "surface_updates"

    def __init__(self, surface_id: str, writer: Callable[[str, Dict[str, Any]], Any]) -> None:
        self.surface_id = surface_id
        self._writer = writer            # writer(collection_path, message) -> persists

    def emit(self, msg: Dict[str, Any]) -> None:
        # one document per message, ordered by the caller's own append order
        self._writer(f"{self.COLLECTION}/{self.surface_id}", msg)
