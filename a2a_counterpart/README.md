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
string)/`TextMessageEnd`, consumed by `streaming_text` — a future
increment could route qualifying `updateComponents` calls there for text
content, but "watch an actual picture build stroke by stroke" has no
existing live-atom consumer yet and would need real new work, not just a
mapping addition.

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

## Files

- `main.py` — the A2A server: `StatefulSurfaceExecutor` (derived state +
  AG-UI publish), `/render`, `/agui-stream`, `/demo`, static JS proxies.
- `agui_adapter.py` — the reusable translation layer (this doc's focus).
- `render.py` — renders derived state to real HTML via a2uicatalog's own
  decode+render pipeline (unrelated to the AG-UI adapter; a separate,
  earlier capability — see module docstring).
- `static/demo.html` — the live-atoms consumer page.

## Testing

`python3 -m pytest tests/test_agui_adapter.py tests/test_agui_stream_endpoint.py tests/test_a2a_counterpart.py -v`
— all local, no network, no Cloud Run. Real note from building the SSE
test: `httpx.ASGITransport` buffers an entire ASGI response body before
returning anything, so a genuinely infinite stream can't be tested through
it — drive `agui_event_lines()` directly instead (see that test file's own
docstring).
