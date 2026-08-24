# a2a_counterpart

A minimal, real A2A v1.0 service that does two things: (1) proves
`renderers/a2a_extension.py`'s wire-format wrap/unwrap against a real
`a2a-sdk` client/server pair, not just unit tests; and (2) demonstrates
that A2A traffic can drive real, existing UI — both a2uicatalog's own
declarative renderer (`/render`) and a completely separate, AG-UI-native
"live atoms" runtime that ships elsewhere in this repo (`/demo`), via a
small, reusable translation layer: **`agui_adapter.py`**.

Everything here is local-first and free to run — no Cloud Run, no billed
infra, until you deploy it yourself (see `ops/project-ops.yaml`'s
`a2a-counterpart-deploy` process in the sibling `a2ui-private` repo).

## Quickstart

```bash
AGENT_BASE_URL=http://localhost:8091 uvicorn a2a_counterpart.main:app --port 8091
```

In another terminal:

```bash
python3 scripts/a2a_demo_composition.py --url http://localhost:8091
```

It drives a real multi-agent scenario over real A2A calls — an
"orchestrator" creates a surface, two "specialists" each populate a
different part of it — and prints two URLs: a static HTML snapshot
(`/render`) and a live-updating page (`/demo`) that shows the same
scenario building in real time via `agui_adapter.py`.

## `agui_adapter.py` — the reusable part

**The problem it solves**: A2A's own task lifecycle is coarse by design —
five checkpoint states (`submitted`/`working`/`input-required`/
`completed`/`failed`). If you want a genuinely LIVE-feeling UI driven by
an A2A agent — not just "it's working... now it's done" — you need
finer-grained events. Meanwhile, a completely separate, unrelated
workstream in this repo already built a real, tested, AG-UI-native
streaming UI runtime (`cloud-run-renderer/static/a2ui-stream-runtime.v1.js`
+ `a2ui-atoms-live.v1.js`) with real components — a turn-by-turn status
tracker, a live node-graph of activity, a cost/token meter — that already
solve the "live-feeling UI" problem, just for AG-UI's own event
vocabulary, not A2A's.

`agui_adapter.py` translates real A2UI v1.0 messages (the same ones any
A2A agent speaking this estate's `renderers/a2a_extension.py` binding
already sends) into that SAME AG-UI event vocabulary, so those already-
built components render from real A2A traffic. It reuses AG-UI's exact
event names (`RunStarted`, `StepStarted`, `ToolCallStart`,
`ToolCallResult`, `RunFinished`) rather than inventing a parallel one —
the honesty about what's actually happening lives in this module's own
name and docs, not in a renamed event type.

**This is semantic compatibility for UI reuse, not a claim of 1:1
fidelity with a native AG-UI stream.** Don't chase full parity with it —
that fight isn't worth it (see `~/.claude/plans/` history for the
reasoning, or just: A2A's real audience is agent-to-agent, not
agent-to-browser; a UI that feels live is enough).

### Public API

```python
from a2a_counterpart.agui_adapter import adapt_to_agui_events

events = adapt_to_agui_events(
    context_id,       # A2A context/run id
    surface_id,       # the A2UI surfaceId this message targets
    a2ui_message,      # one real v1.0 message: createSurface / updateComponents / updateDataModel / deleteSurface
    surface_already_started=...,  # caller's own knowledge of whether RunStarted/StepStarted already fired for this (context_id, surface_id)
)
# -> list[dict], each {"type": "<AG-UI event name>", "payload": {...}}, possibly empty
```

Pure, synchronous, no I/O, no state of its own — `surface_already_started`
is passed in rather than tracked internally, so this function is trivially
unit-testable (`tests/test_agui_adapter.py`) and safe to call from
whatever executor/transport you're already using.

### Current mapping

| A2UI v1.0 message | AG-UI event(s) emitted | Powers |
|---|---|---|
| `createSurface` (first time per surface) | `RunStarted` + `StepStarted` | `live_step_tracker` |
| `updateComponents` | `ToolCallStart` + `ToolCallResult` per touched component id | `live_step_tracker`, `agent_run_sketch` |
| `updateComponents` with a string `text` field | ALSO `TextMessageStart` + `TextMessageContent` + `TextMessageEnd` (one self-contained "typing burst" per update — see below) | `streaming_text` |
| `deleteSurface` | `RunFinished` | `live_step_tracker`, `agent_run_sketch` |
| `updateDataModel` | `StateDelta` (one real RFC 6902 JSON Patch op — `remove` if `value` is `None`, else `replace`) | `live_cost_trend`, `mountTokenBudgetMeter` |

**On the text mapping (Phase 5.3)**: this is deliberately NOT true
character-by-character LLM streaming. Each real A2A `updateComponents`
call becomes its own self-contained burst — one message, one full-text
delta, immediately started and ended. Considered and rejected: computing
an incremental delta by diffing against a component's previous text (so
repeated updates to the same component would read as one continuous
stream) — `TextMessageEnd` must fire exactly once, on the true last
chunk, and the adapter has no honest way to know which update is "last"
without new state tracking or an invented wire convention. The
self-contained-burst design sidesteps that: every burst has a real,
unambiguous start and end, at the cost of not showing token-by-token
typing. Good enough for "watch real text arrive live," not a claim of
more than that.

The adapter makes no claim about what the data model *contains* — an
agent can put step counts, token/cost tracking, anything at all. It's a
generic, content-agnostic translator; the agent author decides what winds
up on screen. `scripts/a2a_demo_composition.py` demonstrates this with an
illustrative (not real-LLM) token/cost trend, shaped exactly like
`live_cost_trend`'s own real, verified field names
(`turn`/`cumulativeTokens`/`cumulativeCostUsd`).

An earlier idea to map progressive-drawing atoms (`svg_path_draw`) via an
invented `ContentDelta` event was checked against the real runtime source
and dropped — no such event or consumer exists anywhere in
`a2ui-atoms-live.v1.js` today. The real progressive-content mechanism
that DOES exist is `TextMessageStart`/`TextMessageContent`(`delta`
string)/`TextMessageEnd`, consumed by `streaming_text`.

"Watch an actual picture build stroke by stroke" was later built anyway
(see **Free-prompt sketch demo** below) — not by inventing a new AG-UI
event, but by having the SAME `ToolCallResult` that already drives
`agent_run_sketch`/`live_step_tracker` also trigger a fetch of the real,
server-rendered `agent_sketchpad` fragment. `agent_sketchpad` is a real
a2uicatalog catalogue atom (`atoms/schema.yaml`), not an AG-UI live-atom
— it has no client-side streaming controller, so there's nothing to add
to `a2ui-atoms-live.v1.js`. This keeps the adapter itself unchanged: it's
still a generic `A2UI message -> AG-UI event` translator that knows
nothing about drawing.

### Wiring it into your own A2A executor

See `main.py`'s `StatefulSurfaceExecutor` for the reference integration:
after a message successfully applies to your own derived state, call the
adapter and publish the resulting events to whatever transport you use to
reach a browser (this repo's reference uses an in-memory
`asyncio.Queue` per `(context_id, surface_id)`, streamed as SSE via
`agui_event_lines()` — swap that for your own transport freely, the
adapter itself has no opinion on delivery).

### Consuming the events in a browser

Load the real, unmodified runtime + atoms scripts and use the SAME
`mountAtom` pattern `cloud-run-renderer/static/agent-tail-demo.html`
already proves works (mirrored in `static/demo.html`):

```html
<script src=".../a2ui-stream-runtime.v1.js"></script>
<script src=".../a2ui-atoms-live.v1.js"></script>
<script>
  const runtime = A2UIStream.A2UIStreamRuntime({
    container: yourContainer,
    mountAtom(family, key, event) { /* see static/demo.html for the real shared-controller pattern */ },
  });
  runtime.connect(yourSseUrl);
</script>
```

## Free-prompt sketch demo

`GET /sketch` serves a one-field form; `POST /sketch` (subject=...)
creates a surface SYNCHRONOUSLY with real wired placeholders (`status_line`,
`sketch`) via a direct `executor._apply_batch()` call, then 303-redirects
to `/demo/{context_id}/{surface_id}` **before** the slow Gemini work
starts — the redirect target is already renderable the instant the
browser lands on it. A background `asyncio.create_task()` then plans the
drawing (`scripts/a2a_agent_sketch.py`'s `_plan_strokes()`, real Gemini
call against `gemini-3.7-flash` via Vertex Express Mode — see that
script's own `--model` help for why plain IAM/ADC 404s on this model) and
delivers each stroke as its own real A2A message, paced 1.5s apart, over
a real self-referential A2A client (the server calling itself over real
HTTP — same transport as every other demo script here).

The critique/revise pass (`critique_and_revise()` in
`a2a_agent_sketch.py`, a real multimodal self-critique loop: render to
PNG, send back to Gemini alongside the original strokes, ask for a
revision) exists and is unit-exercised, but the WEB path
(`main.py`'s `_run_web_sketch`) deliberately skips it — Curtis's own call
after live testing: it roughly doubled latency to first-stroke for a
quality gain that didn't clearly justify it on a live demo page. The CLI
script still defaults `--refine-passes` to 0 for the same reason but can
opt back in per-run.

**Rendering happens in the same page**, not a separate `/render` tab —
`GET /render-fragment/{context_id}/{surface_id}` returns the bare
server-rendered HTML fragment (empty string + 200, not 404, if the
surface doesn't exist yet, so client polling-on-event can treat "not
created yet" as "keep trying"). `static/demo.html`'s `refreshLiveDrawing()`
fetches it every time a `ToolCallResult` event arrives over the AG-UI
stream — reusing the real `renderers/web_article.py` renderer server-side
rather than duplicating SVG-generation logic in the browser.

The same page also mounts `log_output` (the real static atom's live
controller, `mountLogOutput`) as a shared controller forwarded every
event regardless of routing key, matching
`cloud-run-renderer/static/agent-tail-demo.html`'s own format — one
formatted transcript line per real event.

## A real pitfall: orphaned component updates

`updateComponents` upserts into a flat `components` dict — nothing checks
that the id is actually reachable from `root`. If your `createSurface`
doesn't declare a real placeholder for a component before you `update`
it, the state updates correctly and **nothing ever renders** — a silent
no-op (the exact bug hit building `scripts/a2a_demo_sketch.py`). This
isn't a protocol bug to fix; every real UI framework requires a mount
point before you can patch it. `StatefulSurfaceExecutor.orphaned_component_warnings`
(and a `WARNING:` line in server logs) flags it — a heuristic ("is this
id referenced by any field on any other component"), not a full tree
walk, but it catches the common case.

## Files

- `main.py` — the A2A server: `StatefulSurfaceExecutor` (derived state +
  AG-UI publish), `/render`, `/render-fragment`, `/agui-stream`, `/demo`,
  `/sketch`, static JS proxies.
- `agui_adapter.py` — the reusable translation layer (this doc's focus).
- `render.py` — renders derived state to real HTML via a2uicatalog's own
  decode+render pipeline (unrelated to the AG-UI adapter; a separate,
  earlier capability — see module docstring).
- `static/demo.html` — the live-atoms consumer page (step tracker, live
  drawing, run sketch, cost trend, streaming text, log output).
- `../scripts/a2a_agent_sketch.py` — free-prompt-to-drawing CLI: plans
  strokes via Gemini, optionally critiques/revises, sends over real A2A.
- `../scripts/vertex_gemini.py` — vendored REST client for Vertex AI
  Gemini calls (plain IAM/ADC and Express Mode auth paths).

## Testing

`python3 -m pytest tests/test_agui_adapter.py tests/test_agui_stream_endpoint.py tests/test_a2a_counterpart.py -v`
— all local, no network, no Cloud Run. Real note from building the SSE
test: `httpx.ASGITransport` buffers an entire ASGI response body before
returning anything, so a genuinely infinite stream can't be tested through
it — drive `agui_event_lines()` directly instead (see that test file's own
docstring).
