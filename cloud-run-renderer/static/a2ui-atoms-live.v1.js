/**
 * a2ui-atoms-live — PHASE 2 of launch/agentic-realtime-streaming-brief.md
 * (a2ui-private): the two simplest real atom controllers wired to
 * a2ui-stream-runtime.v1.js, one per update mode, proving the runtime
 * against real atoms before Phase 3's harder ones (parallel tool calls,
 * redacted reasoning, patch-mode state deltas).
 *
 * Each controller here takes a DOM-ADAPTER object, not a raw DOM element
 * directly — a small, explicit set of methods (setText, setStepStatus,
 * etc.) rather than direct element manipulation. This keeps the actual
 * update LOGIC (buffering, lifecycle interpretation, step-state
 * tracking) fully unit-testable in plain Node, with zero DOM/jsdom
 * dependency, matching how a2ui-stream-runtime.v1.js's own tests already
 * work. A real page wires a thin adapter over real DOM elements (see
 * mountStreamingText/mountLiveStepTracker below for the reference
 * adapter this repo actually uses).
 */
(function (global) {
  'use strict';

  const RuntimeMod = (typeof module !== 'undefined' && module.exports)
    ? require('./a2ui-stream-runtime.v1.js')
    : global.A2UIStream;
  const createSafeTextBuffer = RuntimeMod.createSafeTextBuffer;

  // ─── streaming_text controller ─────────────────────────────────────────
  // TextMessageStart/Content/End. Append-mode: buffers incoming deltas
  // through the runtime's own markdown-safe buffer (never renders a
  // dangling code fence or unclosed emphasis run), shows a typing cursor
  // while streaming, settles to the full text (force-flushed, so even a
  // stream that ends mid-delimiter doesn't hide its own tail forever) on
  // TextMessageEnd or RunError.
  function createStreamingTextController(adapter) {
    const buf = createSafeTextBuffer();
    let ended = false;
    return {
      onEvent(event) {
        if (event.type === 'TextMessageContent') {
          const delta = event.payload && event.payload.delta;
          if (typeof delta === 'string') buf.append(delta);
        }
        const isEnd = event.type === 'TextMessageEnd' || event.lifecycle === 'error';
        if (isEnd) ended = true;
        adapter.setText(buf.flush(ended));
        adapter.setCursorVisible(!ended && event.lifecycle === 'streaming');
        adapter.setStatus(event.lifecycle);
      },
      destroy() {},
    };
  }

  // ─── live_step_tracker controller ──────────────────────────────────────
  // RunStarted/Finished/Error, StepStarted/Finished. Tracks the RUN's own
  // overall status plus a per-step status list, in STEP ORDER OF FIRST
  // APPEARANCE (not alphabetical, not by id) -- the order steps actually
  // arrive in an agent's own run is meaningful and must survive to the
  // display.
  function createStepTrackerController(adapter) {
    let runStatus = 'idle';
    const stepOrder = [];
    const stepStatus = new Map(); // stepId -> 'pending' | 'running' | 'done' | 'error'

    function stepIdOf(event) {
      const p = event.payload || {};
      return p.stepId || p.step_id || 'default';
    }

    return {
      onEvent(event) {
        if (event.type === 'RunStarted') runStatus = 'running';
        else if (event.type === 'RunFinished') runStatus = 'done';
        else if (event.type === 'RunError') runStatus = 'error';

        if (event.type === 'StepStarted' || event.type === 'StepFinished') {
          const id = stepIdOf(event);
          if (!stepStatus.has(id)) {
            stepOrder.push(id);
            stepStatus.set(id, 'pending');
          }
          stepStatus.set(id, event.type === 'StepStarted' ? 'running' : 'done');
        }
        if (event.lifecycle === 'error' && event.type !== 'RunError') {
          // A run-level error surfacing through a DIFFERENT event's own
          // lifecycle field (e.g. this controller's routing key itself
          // errored via _onConnectionError) still needs to mark
          // whatever step was in flight, not just the run banner.
          const lastId = stepOrder[stepOrder.length - 1];
          if (lastId !== undefined) stepStatus.set(lastId, 'error');
        }

        adapter.setRunStatus(runStatus);
        adapter.setSteps(stepOrder.map((id) => ({ id, status: stepStatus.get(id) })));
      },
      destroy() {},
    };
  }

  // ─── Reference DOM adapters (real page wiring, not unit-tested here — ──
  // the LOGIC above is; this is thin, deliberately dumb glue) ─────────────
  function mountStreamingText(container) {
    const el = document.createElement('div');
    el.className = 'a2ui-streaming-text';
    el.innerHTML = '<span class="a2ui-streaming-text-body"></span><span class="a2ui-streaming-cursor">▍</span>';
    container.appendChild(el);
    const bodyEl = el.querySelector('.a2ui-streaming-text-body');
    const cursorEl = el.querySelector('.a2ui-streaming-cursor');
    const adapter = {
      setText(text) { bodyEl.textContent = text; },
      setCursorVisible(visible) { cursorEl.style.display = visible ? 'inline' : 'none'; },
      setStatus(lifecycle) { el.dataset.lifecycle = lifecycle; },
    };
    return { element: el, controller: createStreamingTextController(adapter) };
  }

  function mountLiveStepTracker(container) {
    const el = document.createElement('div');
    el.className = 'a2ui-step-tracker';
    el.innerHTML = '<div class="a2ui-run-status"></div><ol class="a2ui-step-list"></ol>';
    container.appendChild(el);
    const runStatusEl = el.querySelector('.a2ui-run-status');
    const listEl = el.querySelector('.a2ui-step-list');
    const adapter = {
      setRunStatus(status) { runStatusEl.textContent = 'Run: ' + status; runStatusEl.dataset.status = status; },
      setSteps(steps) {
        listEl.innerHTML = '';
        for (const s of steps) {
          const li = document.createElement('li');
          li.textContent = s.id + ' — ' + s.status;
          li.dataset.status = s.status;
          listEl.appendChild(li);
        }
      },
    };
    return { element: el, controller: createStepTrackerController(adapter) };
  }

  const exportsObj = {
    createStreamingTextController, createStepTrackerController,
    mountStreamingText, mountLiveStepTracker,
  };
  if (typeof module !== 'undefined' && module.exports) module.exports = exportsObj;
  else global.A2UIAtomsLive = exportsObj;
})(typeof window !== 'undefined' ? window : global);
