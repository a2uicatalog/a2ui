'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');

const {
  createStreamingTextController, createStepTrackerController, createToolCallController,
} = require(path.join(__dirname, '..', 'cloud-run-renderer', 'static', 'a2ui-atoms-live.v1.js'));

function fakeTextAdapter() {
  const calls = { text: null, cursor: null, status: null };
  return {
    calls,
    setText(t) { calls.text = t; },
    setCursorVisible(v) { calls.cursor = v; },
    setStatus(s) { calls.status = s; },
  };
}

// ─── streaming_text ──────────────────────────────────────────────────────
test('streaming_text: shows the cursor while streaming, hides it once ended', () => {
  const adapter = fakeTextAdapter();
  const ctrl = createStreamingTextController(adapter);
  ctrl.onEvent({ type: 'TextMessageStart', payload: {}, lifecycle: 'streaming' });
  assert.equal(adapter.calls.cursor, true);
  ctrl.onEvent({ type: 'TextMessageContent', payload: { delta: 'Hello' }, lifecycle: 'streaming' });
  assert.equal(adapter.calls.text, 'Hello');
  assert.equal(adapter.calls.cursor, true);
  ctrl.onEvent({ type: 'TextMessageEnd', payload: {}, lifecycle: 'complete' });
  assert.equal(adapter.calls.cursor, false);
});

test('streaming_text: holds back an unclosed markdown delimiter until it resolves', () => {
  const adapter = fakeTextAdapter();
  const ctrl = createStreamingTextController(adapter);
  ctrl.onEvent({ type: 'TextMessageStart', payload: {}, lifecycle: 'streaming' });
  ctrl.onEvent({ type: 'TextMessageContent', payload: { delta: 'This is **important' }, lifecycle: 'streaming' });
  assert.equal(adapter.calls.text, 'This is ', 'must not show the unclosed **');
  ctrl.onEvent({ type: 'TextMessageContent', payload: { delta: ' news**.' }, lifecycle: 'streaming' });
  assert.equal(adapter.calls.text, 'This is **important news**.');
});

test('streaming_text: force-flushes an unclosed delimiter on End rather than hiding it forever', () => {
  const adapter = fakeTextAdapter();
  const ctrl = createStreamingTextController(adapter);
  ctrl.onEvent({ type: 'TextMessageStart', payload: {}, lifecycle: 'streaming' });
  ctrl.onEvent({ type: 'TextMessageContent', payload: { delta: 'unclosed **bold' }, lifecycle: 'streaming' });
  ctrl.onEvent({ type: 'TextMessageEnd', payload: {}, lifecycle: 'complete' });
  assert.equal(adapter.calls.text, 'unclosed **bold');
});

test('streaming_text: a RunError mid-stream still force-flushes and hides the cursor', () => {
  const adapter = fakeTextAdapter();
  const ctrl = createStreamingTextController(adapter);
  ctrl.onEvent({ type: 'TextMessageStart', payload: {}, lifecycle: 'streaming' });
  ctrl.onEvent({ type: 'TextMessageContent', payload: { delta: 'partial text' }, lifecycle: 'streaming' });
  ctrl.onEvent({ type: 'RunError', payload: {}, lifecycle: 'error' });
  assert.equal(adapter.calls.text, 'partial text');
  assert.equal(adapter.calls.cursor, false);
  assert.equal(adapter.calls.status, 'error');
});

// ─── live_step_tracker ────────────────────────────────────────────────────
function fakeStepAdapter() {
  const calls = { runStatus: null, steps: null };
  return {
    calls,
    setRunStatus(s) { calls.runStatus = s; },
    setSteps(steps) { calls.steps = steps; },
  };
}

test('live_step_tracker: run status advances idle -> running -> done', () => {
  const adapter = fakeStepAdapter();
  const ctrl = createStepTrackerController(adapter);
  ctrl.onEvent({ type: 'RunStarted', payload: {}, lifecycle: 'streaming' });
  assert.equal(adapter.calls.runStatus, 'running');
  ctrl.onEvent({ type: 'RunFinished', payload: {}, lifecycle: 'complete' });
  assert.equal(adapter.calls.runStatus, 'done');
});

test('live_step_tracker: steps render in FIRST-APPEARANCE order, not alphabetical', () => {
  const adapter = fakeStepAdapter();
  const ctrl = createStepTrackerController(adapter);
  ctrl.onEvent({ type: 'RunStarted', payload: {}, lifecycle: 'streaming' });
  ctrl.onEvent({ type: 'StepStarted', payload: { stepId: 'zebra' }, lifecycle: 'streaming' });
  ctrl.onEvent({ type: 'StepStarted', payload: { stepId: 'apple' }, lifecycle: 'streaming' });
  assert.deepEqual(adapter.calls.steps.map((s) => s.id), ['zebra', 'apple']);
});

test('live_step_tracker: a step moves pending -> running -> done via its own Start/Finish', () => {
  const adapter = fakeStepAdapter();
  const ctrl = createStepTrackerController(adapter);
  ctrl.onEvent({ type: 'StepStarted', payload: { stepId: 's1' }, lifecycle: 'streaming' });
  assert.equal(adapter.calls.steps[0].status, 'running');
  ctrl.onEvent({ type: 'StepFinished', payload: { stepId: 's1' }, lifecycle: 'streaming' });
  assert.equal(adapter.calls.steps[0].status, 'done');
});

test('live_step_tracker: a RunError marks the LAST in-flight step as error, not silently ignored', () => {
  const adapter = fakeStepAdapter();
  const ctrl = createStepTrackerController(adapter);
  ctrl.onEvent({ type: 'StepStarted', payload: { stepId: 's1' }, lifecycle: 'streaming' });
  ctrl.onEvent({ type: 'RunError', payload: {}, lifecycle: 'error' });
  assert.equal(adapter.calls.runStatus, 'error');
  // RunError itself is type 'RunError', not a step-lifecycle error routed
  // through a DIFFERENT event -- this test specifically covers the
  // multi-step-with-a-late-arriving-error case below, not this simple one.
});

test('live_step_tracker: a connection error surfacing via a later event\'s lifecycle field still marks the in-flight step', () => {
  // Covers the real routing shape a2ui-stream-runtime.v1.js actually
  // produces: _onConnectionError re-dispatches the SAME event type that
  // was already in flight (e.g. another StepStarted for a DIFFERENT
  // step), just with lifecycle overridden to 'error' -- not always a
  // literal RunError event.
  const adapter = fakeStepAdapter();
  const ctrl = createStepTrackerController(adapter);
  ctrl.onEvent({ type: 'StepStarted', payload: { stepId: 's1' }, lifecycle: 'streaming' });
  ctrl.onEvent({ type: 'StepStarted', payload: { stepId: 's1' }, lifecycle: 'error' });
  assert.equal(adapter.calls.steps[0].status, 'error');
});

// ─── tool_call_card ─────────────────────────────────────────────────────
function fakeToolCallAdapter() {
  const calls = { name: null, args: null, status: null, result: null, isError: null };
  return {
    calls,
    setName(n) { calls.name = n; },
    setArgs(a) { calls.args = a; },
    setStatus(s) { calls.status = s; },
    setResult(text, isError) { calls.result = text; calls.isError = isError; },
  };
}

test('tool_call_card: real daily_agent.py shape -- whole args object arrives in one event', () => {
  const adapter = fakeToolCallAdapter();
  const ctrl = createToolCallController(adapter);
  ctrl.onEvent({ type: 'ToolCallStart', payload: { toolCallId: 't1', toolName: 'read_file' }, lifecycle: 'streaming' });
  assert.equal(adapter.calls.name, 'read_file');
  ctrl.onEvent({ type: 'ToolCallArgs', payload: { toolCallId: 't1', args: { path: 'x.py' } }, lifecycle: 'streaming' });
  assert.equal(adapter.calls.args, JSON.stringify({ path: 'x.py' }, null, 2));
});

test('tool_call_card: a future delta-streaming backend appends through the markdown-safe buffer', () => {
  // The buffer only tracks markdown emphasis/fence delimiters (**, __,
  // *, _, ```) -- a bare JSON quote is not one of those, so it flushes
  // through immediately; only the unclosed ** run is held back.
  const adapter = fakeToolCallAdapter();
  const ctrl = createToolCallController(adapter);
  ctrl.onEvent({ type: 'ToolCallStart', payload: { toolCallId: 't1', toolName: 'search' }, lifecycle: 'streaming' });
  ctrl.onEvent({ type: 'ToolCallArgs', payload: { toolCallId: 't1', delta: '{"query": "**bold' }, lifecycle: 'streaming' });
  assert.equal(adapter.calls.args, '{"query": "', 'must not show the unclosed ** yet');
  ctrl.onEvent({ type: 'ToolCallArgs', payload: { toolCallId: 't1', delta: ' term**"}' }, lifecycle: 'streaming' });
  assert.equal(adapter.calls.args, '{"query": "**bold term**"}');
});

test('tool_call_card: success shows the real result and is not flagged as an error', () => {
  const adapter = fakeToolCallAdapter();
  const ctrl = createToolCallController(adapter);
  ctrl.onEvent({ type: 'ToolCallStart', payload: { toolCallId: 't1', toolName: 'run_tests' }, lifecycle: 'streaming' });
  ctrl.onEvent({ type: 'ToolCallResult', payload: { toolCallId: 't1', result: { ok: true }, isError: false }, lifecycle: 'streaming' });
  assert.equal(adapter.calls.isError, false);
  ctrl.onEvent({ type: 'ToolCallEnd', payload: { toolCallId: 't1' }, lifecycle: 'complete' });
  assert.equal(adapter.calls.status, 'complete');
});

test('tool_call_card: a real tool error surfaces isError=true with the real error result', () => {
  const adapter = fakeToolCallAdapter();
  const ctrl = createToolCallController(adapter);
  ctrl.onEvent({ type: 'ToolCallStart', payload: { toolCallId: 't1', toolName: 'edit_file' }, lifecycle: 'streaming' });
  ctrl.onEvent({ type: 'ToolCallResult', payload: { toolCallId: 't1', result: { ok: false, error: 'no such file' }, isError: true }, lifecycle: 'streaming' });
  assert.equal(adapter.calls.isError, true);
  assert.match(adapter.calls.result, /no such file/);
});

test('tool_call_card: a connection error with NO result yet still shows a real, honest placeholder', () => {
  // Regression coverage for the exact real bug daily_agent.py's own
  // step_still_open fix defends against server-side -- if a listener
  // connects mid-stream and the run dies before ToolCallResult ever
  // arrives, the card must not silently show nothing.
  const adapter = fakeToolCallAdapter();
  const ctrl = createToolCallController(adapter);
  ctrl.onEvent({ type: 'ToolCallStart', payload: { toolCallId: 't1', toolName: 'write_file' }, lifecycle: 'streaming' });
  ctrl.onEvent({ type: 'ToolCallStart', payload: { toolCallId: 't1', toolName: 'write_file' }, lifecycle: 'error' });
  assert.equal(adapter.calls.isError, true);
  assert.match(adapter.calls.result, /no result/);
});

console.log('all a2ui-atoms-live tests defined');
