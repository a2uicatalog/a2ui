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

  // ─── live_diff_card controller ──────────────────────────────────────────
  // A SPECIALIZATION of the tool_call family for file-editing calls, not a
  // new event family -- it consumes the exact same ToolCallStart/Args/End/
  // Result sequence tool_call_card does, mounted instead of the generic
  // card at ROUTING time (see the demo page's own mountAtom: it inspects
  // the first event's toolName and picks this controller for edit_file/
  // write_file, the generic one for everything else). The point: watching
  // an agent's real code edits render as an actual diff, not a raw JSON
  // args dump -- genuinely new agentic-loopback utility, and provable
  // against a REAL backend today (unlike reasoning_trace/live_state_
  // dashboard) because daily_agent.py's own real tool-calling loop already
  // calls edit_file/write_file on every real run that ships a fix.
  //
  // NOT a general-purpose diff algorithm (no LCS, nothing from a diff
  // library) -- deliberately matches what these two REAL tools actually
  // do: edit_file is an exact old_string -> new_string replacement
  // (daily_agent_tools.py's own Workspace.edit_file contract), so showing
  // old_string as removed and new_string as added IS the real, complete
  // diff, not an approximation of one. write_file is for brand-new files
  // only (same module's own docstring) -- its content is shown entirely
  // as added, no removed side.
  function createFileEditCardController(adapter) {
    let name = '';
    let ended = false;
    let hasResult = false;

    return {
      onEvent(event) {
        const p = event.payload || {};
        if (event.type === 'ToolCallStart') {
          name = p.toolName || '';
          adapter.setName(name);
        } else if (event.type === 'ToolCallArgs' && p.args !== undefined) {
          const args = p.args || {};
          adapter.setPath(args.path || '');
          if (name === 'write_file') {
            adapter.setDiff({ removed: null, added: args.content || '', isNewFile: true });
          } else {
            // edit_file (or anything else routed here, defensively treated
            // the same way -- old_string/new_string absent just renders
            // as empty removed/added blocks, not a crash).
            adapter.setDiff({ removed: args.old_string || '', added: args.new_string || '', isNewFile: false });
          }
        } else if (event.type === 'ToolCallResult') {
          hasResult = true;
          const ok = p.result && typeof p.result === 'object' && 'ok' in p.result
            ? !!p.result.ok : !p.isError;
          adapter.setResult(ok, !!p.isError);
        }
        if (event.type === 'ToolCallEnd' || event.lifecycle === 'error') {
          ended = true;
          if (!hasResult && event.lifecycle === 'error') adapter.setResult(false, true);
        }
        adapter.setStatus(event.lifecycle);
      },
      destroy() {},
    };
  }

  function mountFileEditCard(container) {
    const el = document.createElement('div');
    el.className = 'a2ui-file-edit-card';
    el.innerHTML =
      '<div class="a2ui-file-edit-name"></div>' +
      '<div class="a2ui-file-edit-path"></div>' +
      '<div class="a2ui-file-edit-newfile-badge" style="display:none;">NEW FILE</div>' +
      '<pre class="a2ui-file-edit-removed"></pre>' +
      '<pre class="a2ui-file-edit-added"></pre>' +
      '<div class="a2ui-file-edit-result"></div>';
    container.appendChild(el);
    const nameEl = el.querySelector('.a2ui-file-edit-name');
    const pathEl = el.querySelector('.a2ui-file-edit-path');
    const badgeEl = el.querySelector('.a2ui-file-edit-newfile-badge');
    const removedEl = el.querySelector('.a2ui-file-edit-removed');
    const addedEl = el.querySelector('.a2ui-file-edit-added');
    const resultEl = el.querySelector('.a2ui-file-edit-result');

    function toDiffLines(text, prefix) {
      // Plain text content, rendered via textContent per-line (never
      // innerHTML) -- real file content streamed from a live agent run
      // is untrusted input and must never be interpreted as markup.
      return String(text).split('\n').map((line) => prefix + line).join('\n');
    }

    const adapter = {
      setName(n) { nameEl.textContent = n; },
      setPath(path) { pathEl.textContent = path; },
      setDiff(diff) {
        badgeEl.style.display = diff.isNewFile ? 'block' : 'none';
        removedEl.style.display = diff.removed ? 'block' : 'none';
        removedEl.textContent = diff.removed ? toDiffLines(diff.removed, '- ') : '';
        addedEl.textContent = diff.added ? toDiffLines(diff.added, '+ ') : '';
      },
      setStatus(lifecycle) { el.dataset.lifecycle = lifecycle; },
      setResult(ok, isError) {
        resultEl.textContent = isError ? 'failed' : (ok ? 'ok' : 'failed');
        resultEl.dataset.ok = (!isError && ok) ? 'true' : 'false';
      },
    };
    return { element: el, controller: createFileEditCardController(adapter) };
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

  // ─── live_state_dashboard controller ────────────────────────────────────
  // StateSnapshot + StateDelta (JSON Patch), patch-mode. Extends
  // status_dashboard's own key/status-grid shape (see renderers/
  // web_article.py's _render_status_dashboard for the static precedent)
  // with live updates. Unlike every append-mode controller above, this one
  // does NOT apply patches itself -- a2ui-stream-runtime.v1.js's own
  // dispatch() already maintains the patched document per routing key
  // (StateSnapshot is a hard reset, StateDelta merges via jsonPatchApply)
  // and hands it through as `event.state` on every dispatched event. This
  // controller's entire job is rendering whatever `event.state` currently
  // holds -- proving that patch-mode genuinely needs zero atom-specific
  // patch logic, exactly as the brief's own §3 design claims.
  // Expected state shape: `{ items: [{ key, label, status }, ...] }`.
  // `status` is a free-form string (e.g. "online"/"degraded"/"offline") --
  // rendering maps it to a data-attribute for CSS, not a hardcoded enum,
  // so a page can style whatever status vocabulary its own backend emits.
  function createLiveStateDashboardController(adapter) {
    return {
      onEvent(event) {
        const state = event.state || {};
        const items = Array.isArray(state.items) ? state.items : [];
        adapter.setItems(items.map((it) => {
          const key = it && it.key != null ? String(it.key) : '';
          return {
            key,
            label: it && it.label != null ? String(it.label) : key,
            status: it && it.status != null ? String(it.status) : 'unknown',
          };
        }));
        adapter.setStatus(event.lifecycle);
      },
      destroy() {},
    };
  }

  function mountLiveStateDashboard(container) {
    const el = document.createElement('div');
    el.className = 'a2ui-state-dashboard';
    el.innerHTML = '<div class="a2ui-state-dashboard-grid"></div>';
    container.appendChild(el);
    const gridEl = el.querySelector('.a2ui-state-dashboard-grid');
    const adapter = {
      setItems(items) {
        gridEl.innerHTML = '';
        for (const it of items) {
          const cell = document.createElement('div');
          cell.className = 'a2ui-state-dashboard-item';
          cell.dataset.status = it.status;
          cell.dataset.key = it.key;
          const dot = document.createElement('span');
          dot.className = 'a2ui-state-dashboard-dot';
          cell.appendChild(dot);
          cell.appendChild(document.createTextNode(it.label + ': ' + it.status));
          gridEl.appendChild(cell);
        }
      },
      setStatus(lifecycle) { el.dataset.lifecycle = lifecycle; },
    };
    return { element: el, controller: createLiveStateDashboardController(adapter) };
  }

  const exportsObj = {
    createStreamingTextController, createStepTrackerController, createToolCallController,
    createReasoningTraceController, createLiveStateDashboardController, createFileEditCardController,
    mountToolCallCard, mountReasoningTrace, mountLiveStateDashboard, mountFileEditCard,
    mountStreamingText, mountLiveStepTracker,
  };
  if (typeof module !== 'undefined' && module.exports) module.exports = exportsObj;
  else global.A2UIAtomsLive = exportsObj;
})(typeof window !== 'undefined' ? window : global);
