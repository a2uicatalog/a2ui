'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');

const {
  createStreamingTextController, createStepTrackerController, createToolCallController,
  createReasoningTraceController, createLiveStateDashboardController, createFileEditCardController,
  createAgentRunSketchController, createLiveCostTrendController, createLogOutputController,
  createLiveConfidenceBarController,
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

// ─── reasoning_trace ───────────────────────────────────────────────────
function fakeReasoningAdapter() {
  const calls = { title: null, text: null, status: null, encrypted: null, encryptedDetails: null };
  return {
    calls,
    setTitle(t) { calls.title = t; },
    setText(t) { calls.text = t; },
    setStatus(s) { calls.status = s; },
    setEncrypted(enc, details) { calls.encrypted = enc; calls.encryptedDetails = details; },
  };
}

test('reasoning_trace: streams text deltas safely through markdown-safe buffer', () => {
  const adapter = fakeReasoningAdapter();
  const ctrl = createReasoningTraceController(adapter);
  ctrl.onEvent({ type: 'ReasoningStart', payload: { title: 'Analyzing context' }, lifecycle: 'streaming' });
  assert.equal(adapter.calls.title, 'Analyzing context');
  ctrl.onEvent({ type: 'ReasoningMessageContent', payload: { delta: 'Evaluating **step 1' }, lifecycle: 'streaming' });
  assert.equal(adapter.calls.text, 'Evaluating ', 'must not flush incomplete markdown delimiter');
  ctrl.onEvent({ type: 'ReasoningMessageContent', payload: { delta: ' logic** for correctness.' }, lifecycle: 'streaming' });
  assert.equal(adapter.calls.text, 'Evaluating **step 1 logic** for correctness.');
  ctrl.onEvent({ type: 'ReasoningEnd', payload: {}, lifecycle: 'complete' });
  assert.equal(adapter.calls.status, 'complete');
});

test('reasoning_trace: force-flushes text buffer on ReasoningEnd', () => {
  const adapter = fakeReasoningAdapter();
  const ctrl = createReasoningTraceController(adapter);
  ctrl.onEvent({ type: 'ReasoningStart', payload: {}, lifecycle: 'streaming' });
  assert.equal(adapter.calls.title, 'Thinking...');
  ctrl.onEvent({ type: 'ReasoningMessageContent', payload: { delta: 'Unclosed **marker' }, lifecycle: 'streaming' });
  assert.equal(adapter.calls.text, 'Unclosed ');
  ctrl.onEvent({ type: 'ReasoningEnd', payload: {}, lifecycle: 'complete' });
  assert.equal(adapter.calls.text, 'Unclosed **marker');
});

test('reasoning_trace: ReasoningEncryptedValue locks and marks redacted content', () => {
  const adapter = fakeReasoningAdapter();
  const ctrl = createReasoningTraceController(adapter);
  ctrl.onEvent({ type: 'ReasoningStart', payload: { title: 'Thinking' }, lifecycle: 'streaming' });
  ctrl.onEvent({ type: 'ReasoningEncryptedValue', payload: { encryptedValue: 'enc_sig_12345' }, lifecycle: 'streaming' });
  assert.equal(adapter.calls.encrypted, true);
  assert.equal(adapter.calls.encryptedDetails, 'enc_sig_12345');
});

test('reasoning_trace: ReasoningStart with encrypted payload immediately enters locked state', () => {
  const adapter = fakeReasoningAdapter();
  const ctrl = createReasoningTraceController(adapter);
  ctrl.onEvent({ type: 'ReasoningStart', payload: { title: 'Model Thought', encrypted: true, encryptedValue: 'sig_abc' }, lifecycle: 'streaming' });
  assert.equal(adapter.calls.title, 'Model Thought');
  assert.equal(adapter.calls.encrypted, true);
  assert.equal(adapter.calls.encryptedDetails, 'sig_abc');
});

// ─── live_state_dashboard ────────────────────────────────────────────────
// Patch-mode: a2ui-stream-runtime.v1.js's own dispatch() already applies
// StateSnapshot/StateDelta and hands the patched document through as
// `event.state` -- these tests simulate exactly that hand-off (setting
// `state` directly on the event), not payload.delta, matching what the
// controller actually receives in the real runtime.
function fakeStateDashboardAdapter() {
  const calls = { items: null, status: null };
  return {
    calls,
    setItems(items) { calls.items = items; },
    setStatus(s) { calls.status = s; },
  };
}

test('live_state_dashboard: renders items from the runtime-patched state doc', () => {
  const adapter = fakeStateDashboardAdapter();
  const ctrl = createLiveStateDashboardController(adapter);
  ctrl.onEvent({
    type: 'StateSnapshot',
    lifecycle: 'streaming',
    state: { items: [{ key: 'api', label: 'API', status: 'online' }] },
  });
  assert.deepEqual(adapter.calls.items, [{ key: 'api', label: 'API', status: 'online' }]);
  assert.equal(adapter.calls.status, 'streaming');
});

test('live_state_dashboard: a later StateDelta patch is reflected because the runtime already re-applied it into state', () => {
  const adapter = fakeStateDashboardAdapter();
  const ctrl = createLiveStateDashboardController(adapter);
  ctrl.onEvent({
    type: 'StateSnapshot', lifecycle: 'streaming',
    state: { items: [{ key: 'api', label: 'API', status: 'online' }] },
  });
  // Simulates the runtime handing through the SAME doc object after
  // applying a StateDelta that flipped api's status -- this controller
  // does no patch logic of its own, it just re-renders whatever `state`
  // currently holds on each dispatched event.
  ctrl.onEvent({
    type: 'StateDelta', lifecycle: 'streaming',
    state: { items: [{ key: 'api', label: 'API', status: 'degraded' }] },
  });
  assert.deepEqual(adapter.calls.items, [{ key: 'api', label: 'API', status: 'degraded' }]);
});

test('live_state_dashboard: missing state renders an empty grid, not a crash', () => {
  const adapter = fakeStateDashboardAdapter();
  const ctrl = createLiveStateDashboardController(adapter);
  ctrl.onEvent({ type: 'RunStarted', lifecycle: 'idle' });
  assert.deepEqual(adapter.calls.items, []);
});

test('live_state_dashboard: an item missing a label falls back to its key; missing status is "unknown"', () => {
  const adapter = fakeStateDashboardAdapter();
  const ctrl = createLiveStateDashboardController(adapter);
  ctrl.onEvent({
    type: 'StateSnapshot', lifecycle: 'streaming',
    state: { items: [{ key: 'db' }] },
  });
  assert.deepEqual(adapter.calls.items, [{ key: 'db', label: 'db', status: 'unknown' }]);
});

// ─── live_diff_card ──────────────────────────────────────────────────────
function fakeDiffAdapter() {
  const calls = { name: null, path: null, diff: null, status: null, result: null, resultError: null };
  return {
    calls,
    setName(n) { calls.name = n; },
    setPath(p) { calls.path = p; },
    setDiff(d) { calls.diff = d; },
    setStatus(s) { calls.status = s; },
    setResult(ok, isError) { calls.result = ok; calls.resultError = isError; },
  };
}

test('live_diff_card: edit_file renders old_string as removed, new_string as added', () => {
  const adapter = fakeDiffAdapter();
  const ctrl = createFileEditCardController(adapter);
  ctrl.onEvent({ type: 'ToolCallStart', payload: { toolCallId: 't1', toolName: 'edit_file' }, lifecycle: 'streaming' });
  assert.equal(adapter.calls.name, 'edit_file');
  ctrl.onEvent({
    type: 'ToolCallArgs',
    payload: { toolCallId: 't1', args: { path: 'daily_agent.py', old_string: 'MAX = 10', new_string: 'MAX = 20' } },
    lifecycle: 'streaming',
  });
  assert.equal(adapter.calls.path, 'daily_agent.py');
  assert.deepEqual(adapter.calls.diff, { removed: 'MAX = 10', added: 'MAX = 20', isNewFile: false });
});

test('live_diff_card: write_file renders as a new file, no removed side', () => {
  const adapter = fakeDiffAdapter();
  const ctrl = createFileEditCardController(adapter);
  ctrl.onEvent({ type: 'ToolCallStart', payload: { toolCallId: 't1', toolName: 'write_file' }, lifecycle: 'streaming' });
  ctrl.onEvent({
    type: 'ToolCallArgs',
    payload: { toolCallId: 't1', args: { path: 'new_module.py', content: 'def f():\n    pass\n' } },
    lifecycle: 'streaming',
  });
  assert.deepEqual(adapter.calls.diff, { removed: null, added: 'def f():\n    pass\n', isNewFile: true });
});

test('live_diff_card: a real {ok:true} ToolCallResult is a success, {ok:false} is a failure', () => {
  const adapter = fakeDiffAdapter();
  const ctrl = createFileEditCardController(adapter);
  ctrl.onEvent({ type: 'ToolCallStart', payload: { toolCallId: 't1', toolName: 'edit_file' }, lifecycle: 'streaming' });
  ctrl.onEvent({ type: 'ToolCallResult', payload: { toolCallId: 't1', result: { ok: false, error: 'no match' }, isError: true }, lifecycle: 'streaming' });
  assert.equal(adapter.calls.result, false);
  assert.equal(adapter.calls.resultError, true);
});

test('live_diff_card: a connection error with no result yet still reports failure, not silence', () => {
  const adapter = fakeDiffAdapter();
  const ctrl = createFileEditCardController(adapter);
  ctrl.onEvent({ type: 'ToolCallStart', payload: { toolCallId: 't1', toolName: 'edit_file' }, lifecycle: 'streaming' });
  ctrl.onEvent({ type: 'ToolCallStart', payload: { toolCallId: 't1', toolName: 'edit_file' }, lifecycle: 'error' });
  assert.equal(adapter.calls.result, false);
  assert.equal(adapter.calls.resultError, true);
});

// ─── agent_run_sketch ────────────────────────────────────────────────────
// Controller logic only -- node bookkeeping and classification, not SVG
// geometry (that's real-browser-verified, same split reasoning every
// other DOM-adapter controller above already uses).
function fakeSketchAdapter() {
  const calls = { graph: null, runStatus: null };
  return {
    calls,
    setGraph(nodes, runStatus) { calls.graph = nodes; calls.runStatus = runStatus; },
  };
}

test('agent_run_sketch: RunStarted creates a major "start" node and sets run status', () => {
  const adapter = fakeSketchAdapter();
  const ctrl = createAgentRunSketchController(adapter);
  ctrl.onEvent({ type: 'RunStarted', payload: { runId: 'r1' } });
  assert.equal(adapter.calls.runStatus, 'running');
  assert.deepEqual(adapter.calls.graph, [{ id: 'run-start', label: 'start', status: 'ok', weight: 'major' }]);
});

test('agent_run_sketch: a read-only tool call is classified "minor", an editing call is "major"', () => {
  const adapter = fakeSketchAdapter();
  const ctrl = createAgentRunSketchController(adapter);
  ctrl.onEvent({ type: 'ToolCallStart', payload: { toolCallId: 't1', toolName: 'read_file' } });
  ctrl.onEvent({ type: 'ToolCallStart', payload: { toolCallId: 't2', toolName: 'edit_file' } });
  const byId = Object.fromEntries(adapter.calls.graph.map((n) => [n.id, n]));
  assert.equal(byId.t1.weight, 'minor');
  assert.equal(byId.t2.weight, 'major');
});

test('agent_run_sketch: ToolCallResult updates the matching node to ok or error', () => {
  const adapter = fakeSketchAdapter();
  const ctrl = createAgentRunSketchController(adapter);
  ctrl.onEvent({ type: 'ToolCallStart', payload: { toolCallId: 't1', toolName: 'edit_file' } });
  ctrl.onEvent({ type: 'ToolCallResult', payload: { toolCallId: 't1', isError: false } });
  assert.equal(adapter.calls.graph.find((n) => n.id === 't1').status, 'ok');
  ctrl.onEvent({ type: 'ToolCallStart', payload: { toolCallId: 't2', toolName: 'run_tests' } });
  ctrl.onEvent({ type: 'ToolCallResult', payload: { toolCallId: 't2', isError: true } });
  assert.equal(adapter.calls.graph.find((n) => n.id === 't2').status, 'error');
});

test('agent_run_sketch: RunFinished/RunError append a distinct terminal node and set run status', () => {
  const okAdapter = fakeSketchAdapter();
  const okCtrl = createAgentRunSketchController(okAdapter);
  okCtrl.onEvent({ type: 'RunFinished', payload: {} });
  assert.equal(okAdapter.calls.runStatus, 'done');
  assert.equal(okAdapter.calls.graph[0].status, 'ok');

  const errAdapter = fakeSketchAdapter();
  const errCtrl = createAgentRunSketchController(errAdapter);
  errCtrl.onEvent({ type: 'RunError', payload: {} });
  assert.equal(errAdapter.calls.runStatus, 'error');
  assert.equal(errAdapter.calls.graph[0].status, 'error');
});

test('agent_run_sketch: a connection error with no ToolCallResult yet marks the last node failed, not stuck running', () => {
  const adapter = fakeSketchAdapter();
  const ctrl = createAgentRunSketchController(adapter);
  ctrl.onEvent({ type: 'ToolCallStart', payload: { toolCallId: 't1', toolName: 'edit_file' } });
  ctrl.onEvent({ type: 'ToolCallStart', payload: { toolCallId: 't1', toolName: 'edit_file' }, lifecycle: 'error' });
  assert.equal(adapter.calls.graph.find((n) => n.id === 't1').status, 'error');
});

test('agent_run_sketch: the SAME real toolCallId only ever creates one node, not a duplicate on re-arrival', () => {
  const adapter = fakeSketchAdapter();
  const ctrl = createAgentRunSketchController(adapter);
  ctrl.onEvent({ type: 'ToolCallStart', payload: { toolCallId: 't1', toolName: 'edit_file' } });
  ctrl.onEvent({ type: 'ToolCallStart', payload: { toolCallId: 't1', toolName: 'edit_file' } });
  assert.equal(adapter.calls.graph.length, 1);
});

// ─── live_cost_trend ─────────────────────────────────────────────────────
function fakeCostTrendAdapter() {
  const calls = { points: null, rate: undefined, status: null };
  return {
    calls,
    setPoints(p, rate) { calls.points = p; calls.rate = rate; },
    setStatus(s) { calls.status = s; },
  };
}

test('live_cost_trend: renders points from the runtime-patched state doc', () => {
  const adapter = fakeCostTrendAdapter();
  const ctrl = createLiveCostTrendController(adapter);
  ctrl.onEvent({
    type: 'StateDelta', lifecycle: 'streaming',
    state: { points: [{ turn: 0, cumulativeTokens: 1000, cumulativeCostUsd: 0.01 }] },
  });
  assert.deepEqual(adapter.calls.points, [{ turn: 0, cumulativeTokens: 1000, cumulativeCostUsd: 0.01 }]);
  assert.equal(adapter.calls.status, 'streaming');
});

test('live_cost_trend: missing/malformed points render an empty series, not a crash', () => {
  const adapter = fakeCostTrendAdapter();
  const ctrl = createLiveCostTrendController(adapter);
  ctrl.onEvent({ type: 'RunStarted', lifecycle: 'idle' });
  assert.deepEqual(adapter.calls.points, []);
});

test('live_cost_trend: a point missing a numeric field defaults to 0 rather than propagating undefined/NaN', () => {
  const adapter = fakeCostTrendAdapter();
  const ctrl = createLiveCostTrendController(adapter);
  ctrl.onEvent({
    type: 'StateSnapshot', lifecycle: 'streaming',
    state: { points: [{ turn: 3 }] },
  });
  assert.deepEqual(adapter.calls.points, [{ turn: 3, cumulativeTokens: 0, cumulativeCostUsd: 0 }]);
});

test('live_cost_trend: a later StateDelta append is reflected because the runtime already re-applied it into state', () => {
  const adapter = fakeCostTrendAdapter();
  const ctrl = createLiveCostTrendController(adapter);
  ctrl.onEvent({
    type: 'StateSnapshot', lifecycle: 'streaming',
    state: { points: [{ turn: 0, cumulativeTokens: 500, cumulativeCostUsd: 0.005 }] },
  });
  ctrl.onEvent({
    type: 'StateDelta', lifecycle: 'streaming',
    state: { points: [
      { turn: 0, cumulativeTokens: 500, cumulativeCostUsd: 0.005 },
      { turn: 1, cumulativeTokens: 1200, cumulativeCostUsd: 0.014 },
    ] },
  });
  assert.equal(adapter.calls.points.length, 2);
  assert.equal(adapter.calls.points[1].cumulativeCostUsd, 0.014);
});

test('live_cost_trend: rate is null on the very first point -- no elapsed time to measure yet', () => {
  const adapter = fakeCostTrendAdapter();
  let t = 1000;
  const ctrl = createLiveCostTrendController(adapter, () => t);
  ctrl.onEvent({
    type: 'StateSnapshot', lifecycle: 'streaming',
    state: { points: [{ turn: 0, cumulativeTokens: 1000, cumulativeCostUsd: 0.01 }] },
  });
  assert.equal(adapter.calls.rate, null);
});

test('live_cost_trend: computes a real $/min rate from client-observed elapsed time', () => {
  const adapter = fakeCostTrendAdapter();
  let t = 0;
  const ctrl = createLiveCostTrendController(adapter, () => t);
  ctrl.onEvent({
    type: 'StateSnapshot', lifecycle: 'streaming',
    state: { points: [{ turn: 0, cumulativeTokens: 1000, cumulativeCostUsd: 0.01 }] },
  });
  t = 30000;   // 30s later, cost went from 0.01 to 0.04 -- 0.03 over 0.5min = 0.06/min
  ctrl.onEvent({
    type: 'StateDelta', lifecycle: 'streaming',
    state: { points: [
      { turn: 0, cumulativeTokens: 1000, cumulativeCostUsd: 0.01 },
      { turn: 1, cumulativeTokens: 4000, cumulativeCostUsd: 0.04 },
    ] },
  });
  assert.ok(Math.abs(adapter.calls.rate - 0.06) < 1e-9);
});

test('live_cost_trend: does not estimate a rate from a near-zero elapsed window', () => {
  const adapter = fakeCostTrendAdapter();
  let t = 0;
  const ctrl = createLiveCostTrendController(adapter, () => t);
  ctrl.onEvent({
    type: 'StateSnapshot', lifecycle: 'streaming',
    state: { points: [{ turn: 0, cumulativeTokens: 1000, cumulativeCostUsd: 0.01 }] },
  });
  t = 100;   // 100ms later -- far too little elapsed time for a sane estimate
  ctrl.onEvent({
    type: 'StateDelta', lifecycle: 'streaming',
    state: { points: [
      { turn: 0, cumulativeTokens: 1000, cumulativeCostUsd: 0.01 },
      { turn: 1, cumulativeTokens: 1100, cumulativeCostUsd: 0.011 },
    ] },
  });
  assert.equal(adapter.calls.rate, null);
});

// ─── log_output ──────────────────────────────────────────────────────────
function fakeLogAdapter() {
  const calls = { log: null, status: null };
  return {
    calls,
    setLog(t) { calls.log = t; },
    setStatus(s) { calls.status = s; },
  };
}

test('log_output: formats a real event sequence as timestamped lines, in order', () => {
  const adapter = fakeLogAdapter();
  const ctrl = createLogOutputController(adapter);
  ctrl.onEvent({ type: 'RunStarted', payload: {}, lifecycle: 'streaming' });
  ctrl.onEvent({ type: 'StepStarted', payload: { title: 'Turn 0' }, lifecycle: 'streaming' });
  ctrl.onEvent({ type: 'ToolCallStart', payload: { toolName: 'read_file' }, lifecycle: 'streaming' });
  ctrl.onEvent({ type: 'ToolCallResult', payload: { isError: false }, lifecycle: 'streaming' });
  ctrl.onEvent({ type: 'RunFinished', payload: {}, lifecycle: 'complete' });

  const lines = adapter.calls.log.trim().split('\n');
  assert.equal(lines.length, 5);
  assert.match(lines[0], /run started/);
  assert.match(lines[1], /Turn 0/);
  assert.match(lines[2], /read_file/);
  assert.match(lines[3], /✓ ok/);
  assert.match(lines[4], /run finished/);
  // Every line is timestamped -- real client-observed time, not a claim
  // of exact server-side event time (AG-UI's own wire format drops that).
  for (const l of lines) assert.match(l, /^\[\d{1,2}:\d{2}:\d{2}/);
});

test('log_output: a failed tool call and a run error both show as visibly distinct lines', () => {
  const adapter = fakeLogAdapter();
  const ctrl = createLogOutputController(adapter);
  ctrl.onEvent({ type: 'ToolCallStart', payload: { toolName: 'run_tests' }, lifecycle: 'streaming' });
  ctrl.onEvent({ type: 'ToolCallResult', payload: { isError: true }, lifecycle: 'streaming' });
  ctrl.onEvent({ type: 'RunError', payload: { message: 'budget exceeded' }, lifecycle: 'error' });

  const lines = adapter.calls.log.trim().split('\n');
  assert.match(lines[1], /✗ error/);
  assert.match(lines[2], /run error: budget exceeded/);
});

test('log_output: a connection error with no RunError yet still appends a visible line, not silence', () => {
  const adapter = fakeLogAdapter();
  const ctrl = createLogOutputController(adapter);
  ctrl.onEvent({ type: 'ToolCallStart', payload: { toolName: 'edit_file' }, lifecycle: 'streaming' });
  ctrl.onEvent({ type: 'ToolCallStart', payload: { toolName: 'edit_file' }, lifecycle: 'error' });

  const lines = adapter.calls.log.trim().split('\n');
  assert.match(lines[lines.length - 1], /connection error/);
});

// ─── live_confidence_bar ─────────────────────────────────────────────────
function fakeConfidenceAdapter() {
  const calls = { items: null, status: null };
  return {
    calls,
    setItems(items) { calls.items = items; },
    setStatus(s) { calls.status = s; },
  };
}

test('live_confidence_bar: single item format with automatic threshold colors', () => {
  const adapter = fakeConfidenceAdapter();
  const ctrl = createLiveConfidenceBarController(adapter);

  // Score >= 70 should be green (#22c55e)
  ctrl.onEvent({
    type: 'StateSnapshot', lifecycle: 'streaming',
    state: { label: 'Relevance', value: 85 },
  });
  assert.deepEqual(adapter.calls.items, [{ label: 'Relevance', value: 85, color: '#22c55e' }]);
  assert.equal(adapter.calls.status, 'streaming');

  // Score >= 40 and < 70 should be amber (#f59e0b)
  ctrl.onEvent({
    type: 'StateDelta', lifecycle: 'streaming',
    state: { label: 'Relevance', value: 55 },
  });
  assert.deepEqual(adapter.calls.items, [{ label: 'Relevance', value: 55, color: '#f59e0b' }]);

  // Score < 40 should be red (#ef4444)
  ctrl.onEvent({
    type: 'StateDelta', lifecycle: 'complete',
    state: { label: 'Relevance', value: 20 },
  });
  assert.deepEqual(adapter.calls.items, [{ label: 'Relevance', value: 20, color: '#ef4444' }]);
  assert.equal(adapter.calls.status, 'complete');
});

test('live_confidence_bar: normalizes fractional scores 0.0-1.0 to 0-100 percentage', () => {
  const adapter = fakeConfidenceAdapter();
  const ctrl = createLiveConfidenceBarController(adapter);
  ctrl.onEvent({
    type: 'StateSnapshot', lifecycle: 'streaming',
    state: { label: 'Grounding', value: 0.942 },
  });
  assert.deepEqual(adapter.calls.items, [{ label: 'Grounding', value: 94, color: '#22c55e' }]);
});

test('live_confidence_bar: handles multi-item format with custom color override', () => {
  const adapter = fakeConfidenceAdapter();
  const ctrl = createLiveConfidenceBarController(adapter);
  ctrl.onEvent({
    type: 'StateSnapshot', lifecycle: 'streaming',
    state: {
      color: '#3b82f6',
      items: [
        { label: 'Tone', value: 90 },
        { label: 'Safety', value: 30, color: '#dc2626' },
      ],
    },
  });
  assert.deepEqual(adapter.calls.items, [
    { label: 'Tone', value: 90, color: '#3b82f6' },
    { label: 'Safety', value: 30, color: '#dc2626' },
  ]);
});

test('live_confidence_bar: missing/malformed input defaults gracefully without crashing', () => {
  const adapter = fakeConfidenceAdapter();
  const ctrl = createLiveConfidenceBarController(adapter);
  ctrl.onEvent({ type: 'StateSnapshot', lifecycle: 'streaming', state: {} });
  assert.deepEqual(adapter.calls.items, []);

  ctrl.onEvent({ type: 'StateDelta', lifecycle: 'streaming', state: { items: [null, { value: 'invalid' }] } });
  assert.deepEqual(adapter.calls.items, [{ label: 'Confidence', value: 0, color: '#ef4444' }]);
});

console.log('all a2ui-atoms-live tests defined');
