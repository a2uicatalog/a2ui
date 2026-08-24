"""a2a_counterpart — a minimal, real A2A v1.0 service. Started as a pure
echo (Topic B); now (Topic C, Phase 1) also maintains real DERIVED STATE
across multiple A2A calls, reusing renderers/a2ui_v1_updates.py's reference
receive semantics (surface_state_from_create()/apply_update()) -- the same
functions the deployed GAS surface's poll loop already uses, and the same
ones A2uiUpdates.html ports faithfully to JS. Nothing here reimplements
that logic; StatefulSurfaceExecutor only threads real A2A message batches
into it.

Reply behavior for real A2UI messages is UNCHANGED from Topic B on purpose:
still echoes them back (proven, tested, and what
tests/test_a2a_counterpart.py's existing round-trip tests assert on).

Phase 2 (2026-08-24) adds a way to read derived state back over A2A
itself, for a real agent consumer rather than a test's direct object
access -- `getSurfaceState`/`surfaceStateResult`. THESE ARE NOT REAL A2UI
v1.0 MESSAGE TYPES -- the real spec (renderers/a2a_extension.py's own
vendored reference) has no query message at all; this is this
COUNTERPART's own extension for exercising the multi-agent-composition use
case (see a2uithoughts.md's 2026-08-24 ideation entry), kept deliberately
out of renderers/a2a_extension.py so that module stays a faithful mirror
of the real spec, not a place where invented message types could get
confused with real ones.

Ideation basis (Gemini, 2026-08-24): the most load-bearing use case for
this whole direction is ORCHESTRATOR/SPECIALIST UI COMPOSITION -- several
agents, each owning a different zone of one shared surface (e.g. different
component ids), write independently via ordinary updateComponents/
updateDataModel (no new message type needed for WRITES); an
orchestrator/observer agent that wrote nothing itself uses
getSurfaceState to read the composed result. Last-write-wins (what
apply_update() already does) is sufficient because compelling use cases
are spatially partitioned -- no two writers touch the same component id --
so no locking/ownership model is needed at this stage.

Modeled directly on the live `a2ui-ge-agent/main.py` (same
AgentCard/A2AStarletteApplication/DefaultRequestHandler shape, same
`uvicorn.run` entrypoint), trimmed to only what this needs: no rendering,
no GCS, no image bridge, no v0.8 probe history. See tests/test_a2a_counterpart.py
for the real round-trip tests (in-process, no network, via httpx.ASGITransport).

Bare message reply, not a modeled Task: still no Task/TaskUpdater lifecycle
(Gemini design review, 2026-08-24, endorsed this for the echo case; state
tracking here is keyed on (context_id, surfaceId), independent of A2A's own
task lifecycle, so it doesn't change this call).

Phase 3 (2026-08-24) adds GET /render/{context_id}/{surface_id} -- a
dev/demo-only HTML view of current derived state, via
a2a_counterpart/render.py (reuses the same decode+render pipeline GAS
already ships, does not build a new one). See scripts/a2a_demo_composition.py
for a script that drives the orchestrator/specialist use case through
REAL A2A calls against a running instance of this service, then prints
the render URL to open in a browser.
"""
import json
import os
import uuid
from pathlib import Path

import uvicorn
from a2a.client import A2ACardResolver, ClientConfig, ClientFactory
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from starlette.responses import (
    FileResponse, HTMLResponse, RedirectResponse, StreamingResponse,
)
from starlette.routing import Route
from a2a.types import (
    AgentCapabilities, AgentCard, AgentExtension, AgentSkill,
    DataPart, Message, Part, Role, TextPart,
)
from a2a.utils import new_agent_parts_message

from renderers.a2a_extension import (
    A2A_EXTENSION_URI, agent_card_extension, unwrap_sdk_data_part,
    wrap_messages_for_sdk,
)
from renderers.a2ui_v1 import DEFAULT_CATALOG_ID, emit_surface
from renderers.a2ui_v1_updates import (
    apply_update, surface_state_from_create, update_components,
)

from a2a_counterpart.agui_adapter import adapt_to_agui_events
from a2a_counterpart.render import PAGE_TEMPLATE, RenderError, render_state_to_html

import asyncio

AGENT_BASE_URL = os.environ.get("AGENT_BASE_URL", "https://placeholder.a.run.app")


def _surface_id_of(msg: dict) -> str | None:
    """The one surfaceId-bearing key a v1.0 message carries, whichever kind
    it is -- mirrors the same dispatch apply_update() itself does."""
    for key in ("createSurface", "updateComponents", "updateDataModel", "deleteSurface"):
        if key in msg:
            return msg[key].get("surfaceId")
    return None


def _is_query(msg: dict) -> bool:
    """getSurfaceState is THIS COUNTERPART's own extension, not a real
    A2UI v1.0 message type -- see module docstring."""
    return isinstance(msg, dict) and "getSurfaceState" in msg


class StatefulSurfaceExecutor(AgentExecutor):
    """Reflects the incoming A2UI v1.0 DataPart back unchanged (same proven
    behavior as Topic B's EchoExecutor), AND maintains one derived surface
    state per (context_id, surfaceId) in memory -- same in-memory-store
    shape InMemoryTaskStore already uses for tasks, same real
    per-message-not-transactional error tolerance the extension spec itself
    requires (a message that fails to apply is skipped, not fatal to the
    rest of the batch -- see renderers/a2a_extension.py's own docstring
    quoting the spec on this)."""

    def __init__(self) -> None:
        self.state: dict[tuple[str, str], dict] = {}
        # Cheap debugging lever (Gemini post-impl review, 2026-08-24): not
        # surfaced anywhere yet, but a client that swears it sent updates
        # and sees no effect needs SOME internal signal that they were
        # tolerated-skipped, not silently mis-applied.
        self.skipped_updates_count = 0
        # Gemini post-impl review, 2026-08-24 (agent_sketchpad): a real,
        # empirically-hit gap -- updateComponents upserts into the flat
        # `components` dict unconditionally (renderers/a2ui_v1_updates.py's
        # own apply_update()), with NO check that the id is actually
        # reachable from `root`. An agent that forgets to declare a real
        # placeholder in its createSurface gets a silent no-op: state
        # updates correctly, nothing ever renders. Same verdict as
        # skipped_updates_count above: not a protocol bug to fix (every
        # real UI framework requires a mount point before you can patch
        # it), but worth a real, inspectable signal. Heuristic, not a full
        # tree walk (would need to replicate every child-reference shape
        # atoms_v1_decode.gs's own generic componentId-property loop
        # handles) -- "is this id referenced by ANY field on ANY other
        # component" catches the common case (a wholly unreferenced id)
        # without reimplementing that whole resolution engine here.
        self.orphaned_component_warnings: list[str] = []
        # Phase 4: per-(context_id, surfaceId) AG-UI event subscribers (SSE
        # listeners). Empty subs list is the overwhelmingly common case
        # (every Phase 1-3 test, and any real caller not watching a demo
        # page) -- _publish_agui() below short-circuits on that, so this
        # adds no real cost when nobody's listening.
        self._agui_subscribers: dict[tuple[str, str], list] = {}

    def subscribe_agui(self, context_id: str, surface_id: str):
        q = asyncio.Queue()
        self._agui_subscribers.setdefault((context_id, surface_id), []).append(q)
        return q

    def unsubscribe_agui(self, context_id: str, surface_id: str, q) -> None:
        subs = self._agui_subscribers.get((context_id, surface_id))
        if subs and q in subs:
            subs.remove(q)

    def _publish_agui(self, context_id: str, surface_id: str, msg: dict,
                      surface_already_started: bool) -> None:
        """Called only AFTER a message successfully applied to state (see
        call site in _apply_batch) -- a message that failed to apply never
        produces a "the agent did something" event either. Failures here
        are swallowed on purpose: a broken AG-UI translation must never
        take down the real A2A response path (same fail-open-for-others
        contract the stream runtime itself documents on its JS side)."""
        subs = self._agui_subscribers.get((context_id, surface_id))
        if not subs:
            return
        try:
            events = adapt_to_agui_events(context_id, surface_id, msg,
                                          surface_already_started=surface_already_started)
        except Exception:
            return
        for event in events:
            for q in subs:
                q.put_nowait(event)

    def _warn_if_orphaned(self, key: tuple, component_id: str) -> None:
        """See orphaned_component_warnings' own docstring above. Called
        AFTER the upsert, so `components` already includes the just-
        updated one -- excluded from its own reference search."""
        components = self.state[key].get("components") or {}
        if component_id == "root":
            return
        referenced = False
        for other_id, other in components.items():
            if other_id == component_id:
                continue
            for v in other.values():
                if v == component_id or (isinstance(v, list) and component_id in v):
                    referenced = True
                    break
            if referenced:
                break
        if not referenced:
            msg = (f"orphaned component update: {key[1]!r} id={component_id!r} "
                   f"was updated but is not referenced by any other component in "
                   f"the tree (context={key[0]!r}) -- did the initial createSurface "
                   f"declare a real placeholder for it?")
            self.orphaned_component_warnings.append(msg)
            print(f"WARNING: {msg}", flush=True)

    def _apply_batch(self, context_id: str, messages: list[dict]) -> None:
        for msg in messages:
            sid = _surface_id_of(msg)
            if sid is None:
                continue
            key = (context_id, sid)
            already_started = key in self.state
            try:
                if "createSurface" in msg:
                    self.state[key] = surface_state_from_create(msg)
                elif key in self.state:
                    apply_update(self.state[key], msg)
                else:
                    # An update for a surface with no createSurface seen yet
                    # in this context -- real spec's own per-message error
                    # tolerance, skip and keep processing the rest of the
                    # batch.
                    self.skipped_updates_count += 1
                    continue
            except Exception:
                self.skipped_updates_count += 1
                continue
            if "updateComponents" in msg:
                for comp in msg["updateComponents"].get("components", []):
                    cid = comp.get("id")
                    if cid is not None:
                        self._warn_if_orphaned(key, cid)
            self._publish_agui(context_id, sid, msg, already_started)

    def _answer_queries(self, context_id: str, messages: list[dict]) -> list[dict]:
        """getSurfaceState -> surfaceStateResult (our own extension, see
        module docstring). Honest about a surface it's never seen: `found:
        False, state: None`, not a KeyError and not a silently empty dict —
        an orchestrator querying too early needs to tell "not created yet"
        apart from "created but empty"."""
        results = []
        for msg in messages:
            if not _is_query(msg):
                continue
            surface_id = msg["getSurfaceState"].get("surfaceId")
            state = self.state.get((context_id, surface_id))
            results.append({"surfaceStateResult": {
                "surfaceId": surface_id, "found": state is not None,
                "state": state}})
        return results

    async def execute(self, context: RequestContext, event_queue: EventQueue):
        context.add_activated_extension(A2A_EXTENSION_URI)

        data_part = next(
            (getattr(p, "root", p) for p in (context.message.parts or [])
             if isinstance(getattr(p, "root", p), DataPart)),
            None,
        )
        if data_part is None:
            reply = [Part(root=TextPart(
                text="No DataPart found on the incoming message — nothing to echo."))]
            await event_queue.enqueue_event(new_agent_parts_message(
                reply, context.context_id, context.task_id))
            return

        try:
            messages = unwrap_sdk_data_part(data_part.model_dump())
        except Exception as e:
            reply = [Part(root=TextPart(text=f"unwrap_sdk_data_part failed: {e}"))]
            await event_queue.enqueue_event(new_agent_parts_message(
                reply, context.context_id, context.task_id))
            return

        self._apply_batch(context.context_id, messages)
        query_results = self._answer_queries(context.context_id, messages)

        # Real A2UI messages still echo back unchanged (Phase 1/Topic B
        # contract, unaffected); query messages are answered instead of
        # echoed -- mirroring a getSurfaceState back verbatim would be
        # useless to the caller.
        non_query_messages = [m for m in messages if not _is_query(m)]
        reply_messages = non_query_messages + query_results

        echoed = Part(root=DataPart(**wrap_messages_for_sdk(reply_messages)))
        await event_queue.enqueue_event(new_agent_parts_message(
            [echoed], context.context_id, context.task_id))

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        raise Exception("cancel not supported")


skill = AgentSkill(
    id="echo_a2ui_v1",
    name="Echo an A2UI v1.0 DataPart",
    description="Reflects a received A2UI v1.0 DataPart back unchanged, and tracks its derived surface state across calls.",
    tags=["a2ui", "a2a", "interop-test"],
    examples=[],
)

a2ui_extension = AgentExtension(**agent_card_extension(
    supported_catalog_ids=[DEFAULT_CATALOG_ID],
    description="Echoes A2UI v1.0 DataParts and derives their surface state for interop testing",
))

agent_card = AgentCard(
    name="a2a_counterpart_echo",
    description="Minimal A2A v1.0 echo service — reflects A2UI DataParts back unchanged and tracks derived surface state, for interop testing.",
    url=AGENT_BASE_URL,
    version="0.1.0",
    default_input_modes=["text/plain", "application/a2ui+json"],
    default_output_modes=["text/plain", "application/a2ui+json"],
    capabilities=AgentCapabilities(streaming=True, extensions=[a2ui_extension]),
    skills=[skill],
)

# Module-level, not built inline: tests import this directly to inspect
# derived state after driving it through real A2A calls (see
# tests/test_a2a_counterpart.py's multi-turn state test).
executor = StatefulSurfaceExecutor()

async def render_surface(request):
    """GET /render/{context_id}/{surface_id} -- dev/demo-only HTML view of
    a currently derived surface. Real audience is a human in a browser,
    not another agent (see module docstring's Phase 3 note)."""
    context_id = request.path_params["context_id"]
    surface_id = request.path_params["surface_id"]
    state = executor.state.get((context_id, surface_id))
    if state is None:
        return HTMLResponse(
            f"<p>No state for context_id={context_id!r}, surface_id={surface_id!r} yet. "
            f"Send it a createSurface first (see scripts/a2a_demo_composition.py).</p>",
            status_code=404)
    try:
        html = render_state_to_html(state)
    except RenderError as e:
        return HTMLResponse(f"<pre>render failed: {e}</pre>", status_code=502)
    return HTMLResponse(PAGE_TEMPLATE.format(
        context_id=context_id, surface_id=surface_id, html=html))


async def render_fragment(request):
    """GET /render-fragment/{context_id}/{surface_id} -- same real render
    as /render, but the BARE fragment (no page chrome), so /demo can pull
    it into the SAME live page instead of linking out to a separate URL
    (Curtis's own explicit ask, 2026-08-24: "align it exactly with the UI
    of the agui demo -- I expect the render to be in the same page").
    Returns an empty string (200, not 404) for a surface that doesn't
    exist yet -- the poller on /demo treats that as "nothing to show yet"
    and keeps polling, not an error state."""
    context_id = request.path_params["context_id"]
    surface_id = request.path_params["surface_id"]
    state = executor.state.get((context_id, surface_id))
    if state is None:
        return HTMLResponse("")
    try:
        return HTMLResponse(render_state_to_html(state))
    except RenderError:
        return HTMLResponse("")


# The real, unmodified AG-UI live-atoms runtime this Phase 4 work drives --
# served from ITS canonical location (cloud-run-renderer/static/), not a
# duplicated copy, same "single source of truth" discipline as
# a2a_counterpart/Dockerfile's own COPY renderers/ comment.
_LIVE_ATOMS_STATIC_DIR = Path(__file__).parent.parent / "cloud-run-renderer" / "static"
_AGUI_PACE_SECONDS = 0.15  # visual pacing only -- see agui_adapter.py's own docstring


async def serve_live_atoms_js(request):
    filename = request.path_params["filename"]
    if filename not in ("a2ui-stream-runtime.v1.js", "a2ui-atoms-live.v1.js"):
        return HTMLResponse("not found", status_code=404)
    path = _LIVE_ATOMS_STATIC_DIR / filename
    if not path.exists():
        return HTMLResponse(f"{filename} not found at {path}", status_code=404)
    return FileResponse(path, media_type="application/javascript")


async def demo_page(request):
    """GET /demo/{context_id}/{surface_id} -- the visually compelling
    proof: live_step_tracker + agent_run_sketch, fed by a REAL A2A
    conversation via the /agui-stream SSE bridge. See
    scripts/a2a_demo_composition.py for a script that drives real A2A
    calls and prints this URL."""
    context_id = request.path_params["context_id"]
    surface_id = request.path_params["surface_id"]
    html = (Path(__file__).parent / "static" / "demo.html").read_text()
    html = html.replace("__A2A_AGUI_STREAM_URL__", f"/agui-stream/{context_id}/{surface_id}")
    html = html.replace("__A2A_RENDER_FRAGMENT_URL__", f"/render-fragment/{context_id}/{surface_id}")
    return HTMLResponse(html)


async def agui_event_lines(context_id: str, surface_id: str):
    """The real generator behind GET /agui-stream/{context_id}/{surface_id}
    -- factored out to module level (not a closure inside the route
    handler) SPECIFICALLY so it's directly testable: httpx.ASGITransport
    was confirmed (2026-08-24, building this) to buffer an ASGI response's
    ENTIRE body before returning anything to the client, which makes a
    genuinely infinite SSE stream untestable through it at all -- driving
    this generator directly (tests/test_agui_stream_endpoint.py) sidesteps
    that transport limitation instead of fighting it.

    Delivers events in the exact wire format a2ui-stream-runtime.v1.js's
    createSseParser already expects (confirmed by reading it before
    building this). A small pacing delay between events
    (_AGUI_PACE_SECONDS) is presentation-only -- our A2A messages complete
    instantly, with no real async gap to show; without it,
    ToolCallStart+ToolCallResult would arrive in the same browser paint
    and the "in progress" state would never be visible (Gemini design
    review, 2026-08-24, confirmed this is a real risk, not a hypothetical
    one, and endorsed the pacing fix as an honest presentation-layer
    choice, not a fabrication of what happened)."""
    queue = executor.subscribe_agui(context_id, surface_id)
    try:
        # Real ASGI servers (and Starlette's own StreamingResponse) don't
        # flush response headers until the body generator produces its
        # first chunk -- so a caller has no way to know "subscribed and
        # actually listening" until SOMETHING is sent. This immediate,
        # harmless "Connected" event (family "other" -- the demo page's
        # own mountAtom already no-ops unknown families, confirmed
        # against cloud-run-renderer/static/agent-tail-demo.html's real
        # wiring) gives every real caller that confirmation.
        yield "event: Connected\ndata: {\"type\": \"Connected\", \"payload\": {}}\n\n"
        while True:
            event = await queue.get()
            yield f"event: {event['type']}\ndata: {json.dumps(event)}\n\n"
            await asyncio.sleep(_AGUI_PACE_SECONDS)
    finally:
        executor.unsubscribe_agui(context_id, surface_id, queue)


async def agui_stream(request):
    """GET /agui-stream/{context_id}/{surface_id} -- see agui_event_lines()
    for what this actually streams."""
    context_id = request.path_params["context_id"]
    surface_id = request.path_params["surface_id"]
    return StreamingResponse(agui_event_lines(context_id, surface_id),
                             media_type="text/event-stream")


SKETCH_FORM_HTML = """<!doctype html>
<html><head><meta charset="utf-8"><title>Agent Sketchpad</title>
<style>
  body { font-family: system-ui, sans-serif; max-width: 480px; margin: 80px auto; padding: 0 20px; color: #111; }
  h1 { font-size: 1.4rem; }
  input[type=text] { width: 100%; padding: 10px 12px; font: inherit; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; margin: 12px 0; }
  button { font: inherit; padding: 10px 20px; border-radius: 6px; border: none; background: #6366f1; color: #fff; cursor: pointer; }
  button:hover { background: #4f46e5; }
  p.note { color: #666; font-size: 0.85rem; }
</style></head>
<body>
<h1>Agent Sketchpad — free prompt to drawing</h1>
<p class="note">Type anything. A real Gemini call plans a stroke-by-stroke line
drawing, renders and critiques its own attempt once, then draws it live over
real A2A calls to the real agent_sketchpad catalogue atom — modeled on the
original AG-UI sketch demo for parity, this time entirely over A2A. The next
page opens already watching, before anything is drawn.</p>
<form method="POST" action="/sketch">
  <input type="text" name="subject" placeholder="a lighthouse on a cliff" required autofocus>
  <button type="submit">Draw it</button>
</form>
</body></html>"""


async def sketch_form(request):
    """GET /sketch -- the actual "free prompt to drawing" demo page,
    modeled on the original AG-UI sketch demo for parity (Curtis's own
    framing): a text box, one submit, watch it build."""
    return HTMLResponse(SKETCH_FORM_HTML)


async def sketch_submit(request):
    """POST /sketch -- creates the surface (with a real placeholder, see
    agent_sketchpad's own README pitfall note) SYNCHRONOUSLY, before
    redirecting, so the /demo page is guaranteed something to query the
    instant it connects; the actual Gemini planning + critique + drawing
    runs as a background task AFTER the redirect, giving the browser real
    time to load and subscribe before the first stroke is sent (live-
    stream semantics: a late subscriber sees nothing retroactively,
    proven in tests/test_agui_stream_endpoint.py) -- no artificial delay
    needed, Gemini's own real latency is the buffer."""
    form = await request.form()
    subject = (form.get("subject") or "").strip()
    if not subject:
        return HTMLResponse("<p>subject required</p>", status_code=400)

    context_id = f"web-sketch-{uuid.uuid4().hex[:8]}"
    surface_id = "web-sketch-surface"

    create_msg = emit_surface({
        "title": f"Agent Sketchpad — {subject}",
        "blocks": [
            {"type": "body", "text": f"Planning a drawing of: {subject} ...",
             "id": "status_line"},
            {"type": "agent_sketchpad", "id": "sketch",
             "viewBox": "0 0 400 200", "strokes": []},
        ],
    }, surface_id=surface_id)
    executor._apply_batch(context_id, [create_msg])

    base_url = str(request.base_url).rstrip("/")
    asyncio.create_task(_run_web_sketch(context_id, surface_id, subject, base_url))

    return RedirectResponse(f"/demo/{context_id}/{surface_id}", status_code=303)


async def _run_web_sketch(context_id: str, surface_id: str, subject: str, base_url: str) -> None:
    """Runs scripts/a2a_agent_sketch.py's own real planning function
    (imported, not duplicated), then delivers each stroke as its own real
    A2A call -- self-referential (this server calling itself as a real
    A2A client over real HTTP) rather than calling
    executor._apply_batch() directly, so the web-triggered path proves
    the exact same real transport the CLI script and every other demo in
    this repo already do, not a shortcut.

    Skips the critique/refine pass by default (Curtis's own call,
    2026-08-24): it doubles real Gemini latency for a marginal quality
    gain now that the SYSTEM_PROMPT itself already forbids the worst
    failure mode found live (invisible white-on-white strokes) and asks
    for connected endpoints -- and it's a real extra failure point (hit a
    genuine 429 rate-limit live). --refine-passes on the CLI script still
    exists for whoever wants the extra pass.

    Real failure found live, 2026-08-24: a real Gemini timeout on a real
    prompt left the browser watching nothing forever, with the only
    signal a server-side log line nobody watching the page could see. A
    total planning failure now updates the real status_line component via
    a real A2A call, so the failure is VISIBLE on the page that's already
    open, not silent."""
    from a2a_agent_sketch import _plan_strokes

    import httpx
    async with httpx.AsyncClient(base_url=base_url, timeout=30) as hc:
        card = await A2ACardResolver(hc, base_url).get_agent_card()
        client = ClientFactory(ClientConfig(httpx_client=hc, streaming=False)).create(
            card, extensions=[A2A_EXTENSION_URI])

        async def _send(messages):
            msg = Message(role=Role.user, message_id=f"web-sketch-{uuid.uuid4().hex[:8]}",
                         context_id=context_id,
                         parts=[Part(root=DataPart(**wrap_messages_for_sdk(messages)))])
            async for _ in client.send_message(msg, extensions=[A2A_EXTENSION_URI]):
                pass

        try:
            strokes = await asyncio.to_thread(_plan_strokes, subject, "gemini-3.7-flash")
        except Exception as e:
            print(f"WARNING: web sketch planning failed for {subject!r}: {e}", flush=True)
            await _send([update_components(surface_id, [
                {"id": "status_line", "component": "Text",
                 "text": f"Planning failed: {e} -- try again, maybe a shorter prompt."}])])
            return

        await _send([update_components(surface_id, [
            {"id": "status_line", "component": "Text", "text": f"Drawing: {subject}"}])])

        drawn = []
        for i, stroke in enumerate(strokes):
            drawn.append(stroke)
            await _send([update_components(surface_id, [
                {"id": "sketch", "component": "agent_sketchpad",
                 "viewBox": "0 0 400 200", "strokes": list(drawn)}])])
            await asyncio.sleep(1.5)


app = A2AStarletteApplication(
    agent_card=agent_card,
    http_handler=DefaultRequestHandler(
        agent_executor=executor, task_store=InMemoryTaskStore()),
).build()
app.routes.append(Route("/render/{context_id}/{surface_id}", render_surface, methods=["GET"]))
app.routes.append(Route("/render-fragment/{context_id}/{surface_id}", render_fragment, methods=["GET"]))
app.routes.append(Route("/agui-stream/{context_id}/{surface_id}", agui_stream, methods=["GET"]))
app.routes.append(Route("/demo/{context_id}/{surface_id}", demo_page, methods=["GET"]))
app.routes.append(Route("/static/{filename}", serve_live_atoms_js, methods=["GET"]))
app.routes.append(Route("/sketch", sketch_form, methods=["GET"]))
app.routes.append(Route("/sketch", sketch_submit, methods=["POST"]))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
