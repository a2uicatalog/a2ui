'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');

const {
  A2UIStreamRuntime, jsonPatchApply, createSafeTextBuffer,
  createSseParser, createBatcher, LIFECYCLE,
} = require(path.join(__dirname, '..', 'cloud-run-renderer', 'static', 'a2ui-stream-runtime.v1.js'));

// ─── SSE parsing ────────────────────────────────────────────────────────
test('SSE parser: dispatches on blank-line-terminated blocks', () => {
  const records = [];
  const p = createSseParser((r) => records.push(r));
  p.push('event: ToolCallStart\ndata: {"a":1}\n\n');
  assert.equal(records.length, 1);
  assert.equal(records[0].event, 'ToolCallStart');
  assert.equal(records[0].data, '{"a":1}');
});

test('SSE parser: handles a chunk arriving split across two push() calls', () => {
  const records = [];
  const p = createSseParser((r) => records.push(r));
  p.push('event: X\ndata: {"a"');
  assert.equal(records.length, 0, 'must not dispatch a partial record');
  p.push(':1}\n\n');
  assert.equal(records.length, 1);
});

test('SSE parser: multi-line data: joins with newline', () => {
  const records = [];
  const p = createSseParser((r) => records.push(r));
  p.push('data: line1\ndata: line2\n\n');
  assert.equal(records[0].data, 'line1\nline2');
});

// ─── JSON Patch ─────────────────────────────────────────────────────────
test('jsonPatchApply: add/replace/remove on a nested object', () => {
  const doc = { a: { b: 1 } };
  jsonPatchApply(doc, [
    { op: 'replace', path: '/a/b', value: 2 },
    { op: 'add', path: '/a/c', value: 3 },
  ]);
  assert.deepEqual(doc, { a: { b: 2, c: 3 } });
  jsonPatchApply(doc, [{ op: 'remove', path: '/a/c' }]);
  assert.deepEqual(doc, { a: { b: 2 } });
});

test('jsonPatchApply: array append via "-"', () => {
  const doc = { items: [1, 2] };
  jsonPatchApply(doc, [{ op: 'add', path: '/items/-', value: 3 }]);
  assert.deepEqual(doc.items, [1, 2, 3]);
});

test('jsonPatchApply: test op throws on mismatch', () => {
  const doc = { a: 1 };
  assert.throws(() => jsonPatchApply(doc, [{ op: 'test', path: '/a', value: 2 }]));
});

// ─── Markdown-safe append buffer ────────────────────────────────────────
test('safe text buffer: holds back an unclosed code fence', () => {
  const buf = createSafeTextBuffer();
  buf.append('Here is some code:\n```python\nprint(1)');
  const safe = buf.flush(false);
  assert.ok(!safe.includes('```python'), 'must not emit the unclosed fence yet');
  assert.equal(safe, 'Here is some code:\n');
});

test('safe text buffer: releases the fenced block once closed', () => {
  const buf = createSafeTextBuffer();
  buf.append('code:\n```python\nprint(1)\n```\nmore text');
  const safe = buf.flush(false);
  assert.equal(safe, 'code:\n```python\nprint(1)\n```\nmore text');
});

test('safe text buffer: holds back an unclosed **bold** run', () => {
  const buf = createSafeTextBuffer();
  buf.append('This is **very impor');
  const safe = buf.flush(false);
  assert.equal(safe, 'This is ');
});

test('safe text buffer: force flush at stream End emits everything regardless', () => {
  const buf = createSafeTextBuffer();
  buf.append('unclosed **bold and ```fence');
  const forced = buf.flush(true);
  assert.equal(forced, buf.raw());
});

// ─── RAF batching ────────────────────────────────────────────────────────
test('batcher: coalesces multiple push() calls into one flush per frame', () => {
  let scheduled = null;
  const raf = (fn) => { scheduled = fn; return 1; };
  const caf = () => {};
  const flushes = [];
  const b = createBatcher(raf, caf, (batch) => flushes.push(batch));
  b.push('a'); b.push('b'); b.push('c');
  assert.equal(flushes.length, 0, 'must not flush before the frame fires');
  scheduled();
  assert.equal(flushes.length, 1);
  assert.deepEqual(flushes[0], ['a', 'b', 'c']);
});

test('batcher: cancel() clears a pending frame so it never fires', () => {
  let canceled = false;
  const raf = () => 1;
  const caf = () => { canceled = true; };
  const flushes = [];
  const b = createBatcher(raf, caf, (batch) => flushes.push(batch));
  b.push('x');
  b.cancel();
  assert.ok(canceled);
  assert.equal(flushes.length, 0);
});

// ─── Runtime: composite routing / container-slot mounting ───────────────
function makeRuntimeHarness() {
  const mounted = [];
  const events = [];
  let scheduledFrame = null;
  const runtime = A2UIStreamRuntime({
    container: {},
    mountAtom(family, key, firstEvent) {
      mounted.push({ family, key });
      return {
        onEvent(e) { events.push({ key, event: e }); },
        destroy() {},
      };
    },
    raf: (fn) => { scheduledFrame = fn; return 1; },
    caf: () => { scheduledFrame = null; },
  });
  return { runtime, mounted, events, flush: () => { const f = scheduledFrame; scheduledFrame = null; if (f) f(); } };
}

test('runtime: two parallel tool calls mount two DISTINCT controllers, not one', () => {
  const h = makeRuntimeHarness();
  h.runtime._ingestRawChunk(
    'event: ToolCallStart\ndata: {"toolCallId":"t1","toolName":"search"}\n\n' +
    'event: ToolCallStart\ndata: {"toolCallId":"t2","toolName":"fetch"}\n\n');
  h.flush();
  assert.equal(h.mounted.length, 2, 'two different tool_call_ids must mount two controllers');
  assert.notEqual(h.mounted[0].key, h.mounted[1].key);
});

test('runtime: chunks for the SAME tool_call_id route to the SAME controller', () => {
  const h = makeRuntimeHarness();
  h.runtime._ingestRawChunk(
    'event: ToolCallStart\ndata: {"toolCallId":"t1"}\n\n' +
    'event: ToolCallArgs\ndata: {"toolCallId":"t1","delta":"{\\"q\\":"}\n\n' +
    'event: ToolCallEnd\ndata: {"toolCallId":"t1"}\n\n');
  h.flush();
  assert.equal(h.mounted.length, 1, 'the same tool_call_id must reuse one controller across its whole lifecycle');
  assert.equal(h.events.length, 3);
});

// ─── Runtime: lifecycle state machine ────────────────────────────────────
test('runtime: lifecycle goes idle -> streaming -> complete for a tool call', () => {
  const h = makeRuntimeHarness();
  h.runtime._ingestRawChunk('event: ToolCallStart\ndata: {"toolCallId":"t1"}\n\n');
  h.flush();
  assert.equal(h.events[0].event.lifecycle, LIFECYCLE.STREAMING);
  h.runtime._ingestRawChunk('event: ToolCallResult\ndata: {"toolCallId":"t1","result":"ok"}\n\n');
  h.flush();
  assert.equal(h.events[1].event.lifecycle, LIFECYCLE.COMPLETE);
});

test('runtime: a RunError transitions ALL active controllers to error, none left hanging', () => {
  const h = makeRuntimeHarness();
  h.runtime._ingestRawChunk(
    'event: ToolCallStart\ndata: {"toolCallId":"t1"}\n\n' +
    'event: ToolCallStart\ndata: {"toolCallId":"t2"}\n\n');
  h.flush();
  h.runtime._onConnectionError(new Error('stream reset'));
  const lifecycles = h.events.slice(-2).map((e) => e.event.lifecycle);
  assert.deepEqual(lifecycles, [LIFECYCLE.ERROR, LIFECYCLE.ERROR]);
});

// ─── Runtime: state snapshot/delta, hard-reset semantics ─────────────────
test('runtime: StateDelta patches accumulate onto the routing key\'s doc', () => {
  const h = makeRuntimeHarness();
  h.runtime._ingestRawChunk(
    'event: StateSnapshot\ndata: {"runId":"r1","snapshot":{"count":0}}\n\n' +
    'event: StateDelta\ndata: {"runId":"r1","delta":[{"op":"replace","path":"/count","value":1}]}\n\n');
  h.flush();
  assert.equal(h.events[1].event.state.count, 1);
});

test('runtime: a state-only atom moves to STREAMING on its first event, never stuck at idle', () => {
  // Regression test for a real bug caught in the browser harness,
  // 2026-08-22: StateSnapshot/StateDelta have no Start/End framing in
  // AG-UI's own taxonomy, so they fell through nextLifecycleState's
  // start/end checks entirely and a live_state_dashboard-style atom
  // stayed labeled "idle" forever while genuinely receiving live data.
  const h = makeRuntimeHarness();
  h.runtime._ingestRawChunk('event: StateSnapshot\ndata: {"runId":"r1","snapshot":{"count":0}}\n\n');
  h.flush();
  assert.equal(h.events[0].event.lifecycle, LIFECYCLE.STREAMING);
});

test('runtime: a NEW StateSnapshot is a hard reset, not a merge with prior deltas', () => {
  const h = makeRuntimeHarness();
  h.runtime._ingestRawChunk(
    'event: StateSnapshot\ndata: {"runId":"r1","snapshot":{"count":0,"stale":"x"}}\n\n' +
    'event: StateDelta\ndata: {"runId":"r1","delta":[{"op":"replace","path":"/count","value":5}]}\n\n' +
    'event: StateSnapshot\ndata: {"runId":"r1","snapshot":{"count":0}}\n\n');
  h.flush();
  const last = h.events[h.events.length - 1].event.state;
  assert.deepEqual(last, { count: 0 }, 'the fresh snapshot must fully replace the doc, not merge onto it');
});

// ─── Runtime: a misbehaving controller never takes the whole runtime down ─
test('runtime: one controller throwing does not stop other controllers or the parser', () => {
  // Real requestAnimationFrame is ALWAYS deferred to the next paint,
  // never synchronous — a mock that invokes its callback inline (as an
  // earlier version of this test did) creates an interleaving that
  // cannot happen in a real browser and produces a false failure here.
  // Reusing makeRuntimeHarness's own capture-and-manually-fire pattern
  // instead, which correctly separates "frame scheduled" from "frame
  // fired" the same way a real RAF does.
  let scheduledFrame = null;
  const events = [];
  const runtime = A2UIStreamRuntime({
    container: {},
    mountAtom(family, key) {
      return {
        onEvent(e) { if (key.endsWith('bad')) throw new Error('boom'); events.push(key); },
        destroy() {},
      };
    },
    raf: (fn) => { scheduledFrame = fn; return 1; },
    caf: () => { scheduledFrame = null; },
  });
  runtime._ingestRawChunk(
    'event: ToolCallStart\ndata: {"toolCallId":"bad"}\n\n' +
    'event: ToolCallStart\ndata: {"toolCallId":"good"}\n\n');
  const f = scheduledFrame; scheduledFrame = null; if (f) f();
  assert.deepEqual(events, ['tool_call:good']);
});

// ─── High-frequency burst: RAF batching must coalesce, not thrash ────────
test('runtime: 200 rapid-fire text chunks in one tick coalesce into ONE flush, not 200', () => {
  const h = makeRuntimeHarness();
  let chunk = 'event: TextMessageStart\ndata: {"messageId":"m1"}\n\n';
  for (let i = 0; i < 200; i++) {
    chunk += 'event: TextMessageContent\ndata: {"messageId":"m1","delta":"x"}\n\n';
  }
  h.runtime._ingestRawChunk(chunk);
  // Before the frame fires, nothing has been dispatched to the controller yet.
  assert.equal(h.events.length, 0, 'must not dispatch synchronously ahead of the batched frame');
  h.flush();
  // One flush() call processes the whole queued batch — the controller
  // receives all 201 events, but only ONE animation frame was consumed
  // getting there (h.flush fires exactly one scheduled frame).
  assert.equal(h.events.length, 201);
  assert.equal(h.mounted.length, 1, 'still one controller for the whole message, not one per chunk');
});

// ─── disconnect()/connection error via the REAL connect() path ──────────
test('runtime: a ReadableStream read() rejection mid-stream transitions active controllers to error, not a hang', async () => {
  const events = [];
  let scheduledFrame = null;
  const runtime = A2UIStreamRuntime({
    container: {},
    mountAtom() {
      return { onEvent(e) { events.push(e.lifecycle); }, destroy() {} };
    },
    raf: (fn) => { scheduledFrame = fn; return 1; },
    caf: () => { scheduledFrame = null; },
    fetch: async () => ({
      body: {
        getReader() {
          let call = 0;
          return {
            async read() {
              call++;
              if (call === 1) {
                return { done: false, value: new TextEncoder().encode(
                  'event: ToolCallStart\ndata: {"toolCallId":"t1"}\n\n') };
              }
              throw new Error('simulated connection reset');
            },
          };
        },
      },
    }),
  });
  await runtime.connect('https://example.invalid/stream');
  // No manual frame fire needed here — _onConnectionError flushes any
  // still-queued (not yet painted) events itself before marking
  // controllers ERROR, precisely so the ToolCallStart that arrived just
  // before the connection died isn't silently dropped (a real bug this
  // exact test caught: an earlier version of _onConnectionError iterated
  // `controllers` before the queued ToolCallStart had ever been flushed,
  // so it found nothing to mark). By the time connect()'s own await
  // resolves, the controller must already show STREAMING then ERROR —
  // never left hanging in STREAMING forever, and never silently skipped.
  assert.deepEqual(events, [runtime.LIFECYCLE.STREAMING, runtime.LIFECYCLE.ERROR]);
});

console.log('all a2ui-stream-runtime tests defined');
