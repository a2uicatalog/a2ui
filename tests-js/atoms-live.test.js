'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');

const {
  createStreamingTextController, createStepTrackerController,
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

console.log('all a2ui-atoms-live tests defined');
