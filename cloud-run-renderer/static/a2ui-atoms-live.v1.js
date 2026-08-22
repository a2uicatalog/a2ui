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

  // ─── tool_call_card controller (Phase 3) ───────────────────────────────
  // ToolCallStart/Args/End/Result. The a2ui-stream-runtime.v1.js runtime
  // itself already handles the container/slot mechanism at the ROUTING
  // level (two different toolCallIds mount two DISTINCT controller
  // instances -- proven in Phase 1's own tests) -- this controller only
  // has to be correct for ONE tool call's own lifecycle, not coordinate
  // with siblings itself.
  //
  // ToolCallArgs is handled for BOTH real shapes this codebase's own AG-
  // UI events can carry: a whole `args` object in one event (what
  // daily_agent.py's own real emitter sends today -- see ag_ui_emitter.py,
  // its own turn loop never streams args token-by-token) AND a `delta`
  // string chunk (append-mode, for a future backend that DOES stream
  // args incrementally) -- through the SAME markdown-safe-adjacent text
  // buffer streaming_text already uses, so a future streaming-args
  // backend doesn't need a second buffering implementation written for it.
  function createToolCallController(adapter) {
    const argsBuf = createSafeTextBuffer();
    let name = '';
    let ended = false;
    let hasResult = false;

    function renderArgs(force) {
      adapter.setArgs(argsBuf.flush(force));
    }

    return {
      onEvent(event) {
        if (event.type === 'ToolCallStart') {
          name = (event.payload && event.payload.toolName) || '';
          adapter.setName(name);
        } else if (event.type === 'ToolCallArgs') {
          const p = event.payload || {};
          if (typeof p.delta === 'string') {
            argsBuf.append(p.delta);
            renderArgs(false);
          } else if (p.args !== undefined) {
            // Whole-object shape -- pretty-print directly, no buffering
            // needed since it arrived complete in one event.
            adapter.setArgs(JSON.stringify(p.args, null, 2));
          }
        } else if (event.type === 'ToolCallResult') {
          hasResult = true;
          const p = event.payload || {};
          adapter.setResult(
            typeof p.result === 'string' ? p.result : JSON.stringify(p.result, null, 2),
            !!p.isError);
        }
        if (event.type === 'ToolCallEnd' || event.lifecycle === 'error') {
          ended = true;
          renderArgs(true);   // force-flush any still-buffered arg delta, same reasoning streaming_text uses
          if (!hasResult && event.lifecycle === 'error') {
            adapter.setResult('(no result — the run ended before this call completed)', true);
          }
        }
        adapter.setStatus(event.lifecycle);
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

  function mountToolCallCard(container) {
    const el = document.createElement('div');
    el.className = 'a2ui-tool-call-card';
    el.innerHTML =
      '<div class="a2ui-tool-call-name"></div>' +
      '<pre class="a2ui-tool-call-args"></pre>' +
      '<details class="a2ui-tool-call-result-wrap"><summary>Result</summary>' +
      '<pre class="a2ui-tool-call-result"></pre></details>';
    container.appendChild(el);
    const nameEl = el.querySelector('.a2ui-tool-call-name');
    const argsEl = el.querySelector('.a2ui-tool-call-args');
    const resultWrapEl = el.querySelector('.a2ui-tool-call-result-wrap');
    const resultEl = el.querySelector('.a2ui-tool-call-result');
    const adapter = {
      setName(name) { nameEl.textContent = name; },
      setArgs(text) { argsEl.textContent = text; },
      setStatus(lifecycle) { el.dataset.lifecycle = lifecycle; },
      setResult(text, isError) {
        resultEl.textContent = text;
        resultWrapEl.dataset.error = isError ? 'true' : 'false';
        // Errors auto-expand -- a human shouldn't have to click to find
        // out a real tool call failed; a clean success stays collapsed
        // by default, same "don't force-open something unremarkable"
        // reasoning a <details> element's own native semantics already
        // encode.
        if (isError) resultWrapEl.open = true;
      },
    };
    return { element: el, controller: createToolCallController(adapter) };
  }

  // ─── reasoning_trace controller ─────────────────────────────────────────
  // ReasoningStart/MessageContent/End, ReasoningEncryptedValue.
  // Visualizes the model's internal thought process / reasoning trace.
  // Buffers incoming markdown chunks safely.
  // Supports ReasoningEncryptedValue: a locked/non-expandable visual state
  // for redacted or encrypted reasoning content (as emitted by commercial
  // LLM providers).
  function createReasoningTraceController(adapter) {
    const textBuf = createSafeTextBuffer();
    let isEncrypted = false;
    let ended = false;

    function renderText(force) {
      if (!isEncrypted) {
        adapter.setText(textBuf.flush(force));
      }
    }

    return {
      onEvent(event) {
        const p = event.payload || {};
        if (event.type === 'ReasoningStart' || event.type === 'ReasoningMessageStart') {
          const title = p.title || 'Thinking...';
          adapter.setTitle(title);
          if (p.encrypted || p.isEncrypted || p.redacted || p.isRedacted || p.encryptedValue) {
            isEncrypted = true;
            adapter.setEncrypted(true, p.encryptedValue || p.signature || '');
          }
        } else if (event.type === 'ReasoningContent' || event.type === 'ReasoningMessageContent' || event.type === 'TextMessageContent') {
          if (typeof p.delta === 'string') {
            textBuf.append(p.delta);
            renderText(false);
          } else if (typeof p.text === 'string') {
            textBuf.append(p.text);
            renderText(false);
          }
        } else if (event.type === 'ReasoningEncryptedValue') {
          isEncrypted = true;
          const val = p.encryptedValue || p.value || p.signature || '';
          adapter.setEncrypted(true, val);
        }

        const isEnd = event.type === 'ReasoningEnd' || event.type === 'ReasoningMessageEnd' || event.lifecycle === 'error';
        if (isEnd) {
          ended = true;
          renderText(true);
        }
        adapter.setStatus(event.lifecycle);
      },
      destroy() {},
    };
  }

  function mountReasoningTrace(container) {
    const el = document.createElement('div');
    el.className = 'a2ui-reasoning-trace';
    el.innerHTML =
      '<details class="a2ui-reasoning-wrap" open>' +
        '<summary class="a2ui-reasoning-summary">' +
          '<span class="a2ui-reasoning-title">Thinking...</span>' +
          '<span class="a2ui-reasoning-badge"></span>' +
        '</summary>' +
        '<div class="a2ui-reasoning-body"></div>' +
      '</details>' +
      '<div class="a2ui-reasoning-locked-notice" style="display:none;">🔒 Thought process redacted by provider</div>';
    container.appendChild(el);

    const wrapEl = el.querySelector('.a2ui-reasoning-wrap');
    const summaryEl = el.querySelector('.a2ui-reasoning-summary');
    const titleEl = el.querySelector('.a2ui-reasoning-title');
    const badgeEl = el.querySelector('.a2ui-reasoning-badge');
    const bodyEl = el.querySelector('.a2ui-reasoning-body');
    const lockedNoticeEl = el.querySelector('.a2ui-reasoning-locked-notice');

    let locked = false;
    summaryEl.addEventListener('click', (e) => {
      if (locked) {
        e.preventDefault();
      }
    });

    const adapter = {
      setTitle(title) { titleEl.textContent = title; },
      setText(text) { bodyEl.textContent = text; },
      setStatus(lifecycle) { el.dataset.lifecycle = lifecycle; },
      setEncrypted(isEncrypted, details) {
        locked = !!isEncrypted;
        el.dataset.encrypted = locked ? 'true' : 'false';
        if (locked) {
          wrapEl.open = false;
          wrapEl.classList.add('a2ui-reasoning-locked');
          badgeEl.textContent = '🔒 Redacted';
          lockedNoticeEl.style.display = 'block';
          if (details) {
            lockedNoticeEl.title = String(details);
          }
        } else {
          wrapEl.classList.remove('a2ui-reasoning-locked');
          badgeEl.textContent = '';
          lockedNoticeEl.style.display = 'none';
        }
      },
    };
    return { element: el, controller: createReasoningTraceController(adapter) };
  }

  const exportsObj = {
    createStreamingTextController, createStepTrackerController, createToolCallController,
    createReasoningTraceController,
    mountToolCallCard, mountReasoningTrace,
    mountStreamingText, mountLiveStepTracker,
  };
  if (typeof module !== 'undefined' && module.exports) module.exports = exportsObj;
  else global.A2UIAtomsLive = exportsObj;
})(typeof window !== 'undefined' ? window : global);
