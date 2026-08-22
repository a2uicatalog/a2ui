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

  // ─── agent_run_sketch controller ────────────────────────────────────────
  // A hand-drawn-style live node graph of an agent's own run, not a bar or
  // a list. Sketched in launch/agentic-realtime-streaming-brief.md (a2ui-
  // private) §4b as the first "agentic-loopback" candidate: the FINAL
  // static frame is strictly LESS informative than watching it get drawn
  // (a settled bar communicates nothing about the shape of exploration
  // that produced it; a settled graph still shows that shape).
  //
  // Consumes the UNION of RunStarted/Finished/Error and ToolCallStart/
  // Result as ONE shared graph -- deliberately NOT one controller per
  // routing key like every other atom above. a2ui-stream-runtime.v1.js's
  // own dispatch() mounts one controller per (family, key) pair, which
  // fits an atom that only cares about ITS OWN key; this atom wants the
  // union across every key in the run. The real fix lives at the PAGE
  // level (see agent-tail-demo.html's own mountAtom): a single shared
  // controller instance is created once per connection and every
  // lifecycle/tool_call event is forwarded to it in ADDITION to whatever
  // per-key controller the page already mounts for that family -- this
  // controller does its own internal per-id bookkeeping (toolCallId/
  // node id), so it doesn't need the runtime's per-key isolation, it
  // wants the union the runtime's own model doesn't provide.
  //
  // Node "weight": a tool call classified as read-only (a fixed, honestly
  // non-exhaustive set -- read_file/search_files/list_files/list_atoms/
  // get_atom_detail/check_agent_readiness) draws as a small satellite
  // dot; anything else (edit_file/write_file/run_tests/finish/unknown)
  // draws as a larger node. This is a rendering heuristic only, not a
  // protocol concept -- its entire point is making the real, already-
  // observed failure mode (a run exploring for 60 turns and never
  // calling write_file, named in daily_agent.py's own system prompt)
  // visible as a long chain of small dots with no large one, at a glance.
  const AGENT_RUN_SKETCH_READ_ONLY_TOOLS = new Set([
    'read_file', 'search_files', 'list_files', 'list_atoms',
    'get_atom_detail', 'check_agent_readiness',
  ]);

  function createAgentRunSketchController(adapter) {
    const nodes = [];             // [{id, label, status, weight}]
    const nodeIndexById = new Map();
    let runStatus = 'idle';

    function upsertNode(id, label, weight) {
      if (!nodeIndexById.has(id)) {
        nodeIndexById.set(id, nodes.length);
        nodes.push({ id, label, status: 'running', weight });
      }
      return nodes[nodeIndexById.get(id)];
    }

    function render() {
      // A fresh array/objects each render -- the DOM adapter (or a test's
      // fake one) must never be handed this controller's own live
      // internal node objects to mutate.
      adapter.setGraph(nodes.map((n) => Object.assign({}, n)), runStatus);
    }

    return {
      onEvent(event) {
        const p = event.payload || {};
        if (event.type === 'RunStarted') {
          runStatus = 'running';
          upsertNode('run-start', 'start', 'major').status = 'ok';
        } else if (event.type === 'ToolCallStart') {
          const id = p.toolCallId || ('call-' + nodes.length);
          const name = p.toolName || 'call';
          const weight = AGENT_RUN_SKETCH_READ_ONLY_TOOLS.has(name) ? 'minor' : 'major';
          upsertNode(id, name, weight);
        } else if (event.type === 'ToolCallResult') {
          const id = p.toolCallId;
          if (id && nodeIndexById.has(id)) {
            nodes[nodeIndexById.get(id)].status = p.isError ? 'error' : 'ok';
          }
        } else if (event.type === 'RunFinished') {
          runStatus = 'done';
          upsertNode('run-end', 'finished', 'major').status = 'ok';
        } else if (event.type === 'RunError') {
          runStatus = 'error';
          upsertNode('run-end', 'error', 'major').status = 'error';
        }
        // A connection error with no ToolCallResult yet -- same honesty
        // rule tool_call_card/live_diff_card already apply: a call left
        // hanging mid-stream must show as failed, not silently "running"
        // forever.
        if (event.lifecycle === 'error' && event.type !== 'RunError') {
          const last = nodes[nodes.length - 1];
          if (last && last.status === 'running') last.status = 'error';
        }
        render();
      },
      destroy() {},
    };
  }

  // Deterministic string->[0,1) hash (FNV-1a) -- the "sketch" jitter must
  // be stable across re-renders of the SAME node id, or the drawing
  // visibly jumps every time a new node is added and the whole graph
  // re-paints. No RNG, no seed state to manage.
  function agentRunSketchHash(str) {
    let h = 2166136261;
    for (let i = 0; i < str.length; i++) {
      h ^= str.charCodeAt(i);
      h = Math.imul(h, 16777619);
    }
    return (h >>> 0) / 4294967295;
  }

  function agentRunSketchWobblyPath(x1, y1, x2, y2, seed) {
    const midX = (x1 + x2) / 2 + (seed - 0.5) * 16;
    const midY = (y1 + y2) / 2 + (seed - 0.5) * 8;
    return 'M ' + x1 + ' ' + y1 + ' Q ' + midX + ' ' + midY + ' ' + x2 + ' ' + y2;
  }

  const SVG_NS = 'http://www.w3.org/2000/svg';

  function mountAgentRunSketch(container) {
    const wrap = document.createElement('div');
    wrap.className = 'a2ui-run-sketch';
    const svg = document.createElementNS(SVG_NS, 'svg');
    svg.setAttribute('class', 'a2ui-run-sketch-svg');
    wrap.appendChild(svg);
    container.appendChild(wrap);

    const STEP_Y = 40;
    const JITTER_X = 10;
    const CENTER_X = 70;

    const adapter = {
      setGraph(nodes, runStatus) {
        wrap.dataset.runStatus = runStatus;
        while (svg.firstChild) svg.removeChild(svg.firstChild);

        const positions = nodes.map((n, i) => {
          const seed = agentRunSketchHash(n.id);
          return { x: CENTER_X + (seed - 0.5) * 2 * JITTER_X, y: 20 + i * STEP_Y, seed };
        });
        const height = Math.max(48, 40 + nodes.length * STEP_Y);
        svg.setAttribute('viewBox', '0 0 140 ' + height);
        svg.setAttribute('height', String(height));

        for (let i = 1; i < nodes.length; i++) {
          const a = positions[i - 1];
          const b = positions[i];
          const path = document.createElementNS(SVG_NS, 'path');
          path.setAttribute('d', agentRunSketchWobblyPath(a.x, a.y, b.x, b.y, a.seed));
          path.setAttribute('class', 'a2ui-run-sketch-edge');
          svg.appendChild(path);
        }

        nodes.forEach((n, i) => {
          const pos = positions[i];
          const circle = document.createElementNS(SVG_NS, 'circle');
          circle.setAttribute('cx', String(pos.x));
          circle.setAttribute('cy', String(pos.y));
          circle.setAttribute('r', String(n.weight === 'major' ? 7 : 4));
          circle.setAttribute('class', 'a2ui-run-sketch-node');
          circle.dataset.status = n.status;
          circle.dataset.weight = n.weight;
          const title = document.createElementNS(SVG_NS, 'title');
          title.textContent = n.label + ' (' + n.status + ')';
          circle.appendChild(title);
          svg.appendChild(circle);
        });
      },
    };
    return { element: wrap, controller: createAgentRunSketchController(adapter) };
  }

  // ─── live_cost_trend controller ─────────────────────────────────────────
  // Patch-mode, same shape as live_state_dashboard: the runtime already
  // applies StateSnapshot/StateDelta and hands the patched doc through as
  // `event.state` -- this controller renders whatever `event.state.points`
  // currently holds, no patch logic of its own.
  //
  // The FIRST atom in this pack whose live signal is provable against a
  // REAL production run today, not just synthetic events: daily_agent.py's
  // own _run_loop already tracks cumulativeTokens/cumulativeCostUsd for
  // its own real budget enforcement (see MAX_CUMULATIVE_TOKENS/
  // run_budget_usd in that file) and now emits a real StateDelta per
  // resolved turn appending {turn, cumulativeTokens, cumulativeCostUsd}
  // to a `points` array (ag_ui_emitter.py's own state_delta, wired into
  // _run_loop 2026-08-22). Watching real spend accrue during a real run,
  // not a static end-of-run total buried in a trace file.
  // `now` is injectable (defaults to Date.now) so the rate calculation
  // below is deterministically testable, matching this file's own
  // existing pattern for injectable time/frame sources elsewhere.
  function createLiveCostTrendController(adapter, now) {
    now = now || Date.now;
    let firstReceivedAtMs = null;
    let firstCostUsd = null;

    return {
      onEvent(event) {
        const state = event.state || {};
        const points = Array.isArray(state.points) ? state.points : [];
        const cleaned = points.map((p) => ({
          turn: p && typeof p.turn === 'number' ? p.turn : 0,
          cumulativeTokens: p && typeof p.cumulativeTokens === 'number' ? p.cumulativeTokens : 0,
          cumulativeCostUsd: p && typeof p.cumulativeCostUsd === 'number' ? p.cumulativeCostUsd : 0,
        }));

        // A live spend RATE, not just the running total -- real feedback,
        // 2026-08-22: "make it human relatable and feel real time."
        // Honestly a CLIENT-observed rate: the wire format carries no
        // server-side timestamp (ag_ui_emitter.py's own _emit drops it
        // before the event ever reaches a client -- see live_diff_card's
        // own docstring for the same limitation applied elsewhere), so
        // this measures wall-clock time on THIS machine since the first
        // point arrived, not exact server-side elapsed time.
        let ratePerMin = null;
        if (cleaned.length > 0) {
          const nowMs = now();
          if (firstReceivedAtMs === null) {
            firstReceivedAtMs = nowMs;
            firstCostUsd = cleaned[0].cumulativeCostUsd;
          }
          const elapsedMin = (nowMs - firstReceivedAtMs) / 60000;
          if (elapsedMin > 1 / 60) {   // at least ~1s elapsed -- avoid a wild divide-by-near-zero estimate
            const last = cleaned[cleaned.length - 1];
            ratePerMin = (last.cumulativeCostUsd - firstCostUsd) / elapsedMin;
          }
        }

        adapter.setPoints(cleaned, ratePerMin);
        adapter.setStatus(event.lifecycle);
      },
      destroy() {},
    };
  }

  function mountLiveCostTrend(container) {
    const el = document.createElement('div');
    el.className = 'a2ui-cost-trend';
    el.innerHTML =
      '<div class="a2ui-cost-trend-header">' +
        '<span class="a2ui-cost-trend-live-dot"></span>' +
        '<span class="a2ui-cost-trend-value"></span>' +
      '</div>' +
      '<div class="a2ui-cost-trend-rate"></div>' +
      '<svg class="a2ui-cost-trend-svg" viewBox="0 0 160 44" preserveAspectRatio="none"></svg>';
    container.appendChild(el);
    const valueEl = el.querySelector('.a2ui-cost-trend-value');
    const rateEl = el.querySelector('.a2ui-cost-trend-rate');
    const svg = el.querySelector('.a2ui-cost-trend-svg');
    let lastRenderedCost = null;

    const adapter = {
      setPoints(points, ratePerMin) {
        while (svg.firstChild) svg.removeChild(svg.firstChild);
        if (points.length === 0) {
          valueEl.textContent = '$0.0000';
          rateEl.textContent = '';
          return;
        }
        const last = points[points.length - 1];
        valueEl.textContent = '$' + last.cumulativeCostUsd.toFixed(4)
          + ' · ' + last.cumulativeTokens.toLocaleString() + ' tokens';
        rateEl.textContent = ratePerMin !== null && ratePerMin > 0
          ? '≈ $' + ratePerMin.toFixed(4) + ' / min right now'
          : '';

        // Flash on a genuinely NEW value, not every render -- real
        // feedback, 2026-08-22: "make it feel real time... maybe
        // flashing in between updates." Re-triggering a CSS animation
        // needs a real reflow between removing and re-adding the class,
        // or a second update in quick succession would silently not
        // replay it.
        if (lastRenderedCost !== null && last.cumulativeCostUsd !== lastRenderedCost) {
          valueEl.classList.remove('a2ui-cost-trend-pulse');
          void valueEl.offsetWidth;
          valueEl.classList.add('a2ui-cost-trend-pulse');
        }
        lastRenderedCost = last.cumulativeCostUsd;

        // Cost is monotonically non-decreasing over a real run -- the
        // scale is simply [0, last value], no need to track a running
        // max separately from "the most recent point."
        const maxCost = Math.max(last.cumulativeCostUsd, 0.0001);
        const w = 160;
        const h = 44;
        const stepX = points.length > 1 ? w / (points.length - 1) : 0;
        const coords = points.map((p, i) => {
          const x = points.length > 1 ? i * stepX : w;
          const y = h - (p.cumulativeCostUsd / maxCost) * (h - 4) - 2;
          return x + ',' + y;
        });
        const polyline = document.createElementNS(SVG_NS, 'polyline');
        polyline.setAttribute('points', coords.join(' '));
        polyline.setAttribute('class', 'a2ui-cost-trend-line');
        svg.appendChild(polyline);

        // Emphasize the endpoint -- the CURRENT spend, the number that
        // actually matters while a run is still going. A soft expanding
        // "ping" ring behind the solid dot, CSS-animated (see the
        // matching .a2ui-cost-trend-ping keyframes), reinforces "this is
        // live" even in the quiet seconds between real updates.
        const [lastX, lastY] = coords[coords.length - 1].split(',');
        const ping = document.createElementNS(SVG_NS, 'circle');
        ping.setAttribute('cx', lastX);
        ping.setAttribute('cy', lastY);
        ping.setAttribute('r', '3');
        ping.setAttribute('class', 'a2ui-cost-trend-ping');
        svg.appendChild(ping);
        const dot = document.createElementNS(SVG_NS, 'circle');
        dot.setAttribute('cx', lastX);
        dot.setAttribute('cy', lastY);
        dot.setAttribute('r', '3');
        dot.setAttribute('class', 'a2ui-cost-trend-dot');
        svg.appendChild(dot);
      },
      setStatus(lifecycle) { el.dataset.lifecycle = lifecycle; },
    };
    return { element: el, controller: createLiveCostTrendController(adapter) };
  }

  // ─── token_budget_meter (compact variant of live_cost_trend) ───────────
  // NOT a separate controller -- the brief's own §4a originally scoped
  // token_budget_meter as its own "patch-mode, StateDelta ticking a live
  // number" atom, but that's mechanically identical to what
  // live_cost_trend already does with the SAME real state.points signal;
  // building a second controller for it would just be the same logic
  // twice. This is what the brief's own "compact/expanded/timeline
  // variants of what's already working" scaling framing actually means
  // in practice: the EXISTING, already-tested createLiveCostTrendController
  // reused unchanged, with a minimal DOM adapter that renders only the
  // current number -- no sparkline, no endpoint dot. A real demonstration
  // of the scaling claim, not just an assertion of it.
  function mountTokenBudgetMeter(container) {
    const el = document.createElement('div');
    el.className = 'a2ui-token-budget-meter';
    el.textContent = '$0.0000';
    container.appendChild(el);
    const adapter = {
      setPoints(points) {
        const last = points[points.length - 1];
        el.textContent = last ? '$' + last.cumulativeCostUsd.toFixed(4) : '$0.0000';
      },
      setStatus(lifecycle) { el.dataset.lifecycle = lifecycle; },
    };
    return { element: el, controller: createLiveCostTrendController(adapter) };
  }

  // ─── log_output controller (live variant) ───────────────────────────────
  // Append-mode: extends the static log_output atom (a dark terminal-style
  // box, renderers/web_article.py's own _render_log_output) with a live
  // transcript of the SAME real lifecycle/tool_call events every other
  // atom in this pack already consumes -- one formatted line per real
  // event, not raw stdout (daily_agent.py's own tool calls don't emit
  // free-form log lines; ToolCallResult's real shape is a structured
  // dict). Honest about what it actually shows: an observer's own
  // running commentary of the real event stream, client-timestamped
  // (AG-UI's own wire format drops the server-side timestamp -- see
  // ag_ui_emitter.py's _emit and this runtime's own SSE parser, neither
  // forwards it), not a claim of exact server-side event time.
  function createLogOutputController(adapter) {
    // NOT createSafeTextBuffer -- that buffer exists to hold back an
    // INCOMPLETE markdown delimiter mid-stream (a partial ```` ``` ````
    // or unclosed `**bold`). Every line here arrives already complete
    // (one real event = one whole formatted line), so there's nothing
    // partial to guard against -- plain string accumulation is the
    // honest tool for this job, not a mismatched reuse of the other one.
    let text = '';
    let ended = false;

    function line(msg) {
      const stamp = new Date().toLocaleTimeString();
      text += '[' + stamp + '] ' + msg + '\n';
      adapter.setLog(text);
    }

    return {
      onEvent(event) {
        const p = event.payload || {};
        if (event.type === 'RunStarted') line('▶ run started');
        else if (event.type === 'StepStarted') line('· ' + (p.title || 'step started'));
        else if (event.type === 'ToolCallStart') line('→ ' + (p.toolName || 'tool_call'));
        else if (event.type === 'ToolCallResult') {
          line(p.isError ? '  ✗ error' : '  ✓ ok');
        } else if (event.type === 'RunFinished') { line('■ run finished'); ended = true; }
        else if (event.type === 'RunError') { line('✗ run error: ' + (p.message || '')); ended = true; }
        if (event.lifecycle === 'error' && !ended && event.type !== 'RunError') {
          line('✗ connection error');
          ended = true;
        }
        adapter.setStatus(event.lifecycle);
      },
      destroy() {},
    };
  }

  function mountLogOutput(container) {
    const el = document.createElement('div');
    el.className = 'a2ui-log-output';
    el.innerHTML = '<pre class="a2ui-log-output-pre"></pre>';
    container.appendChild(el);
    const preEl = el.querySelector('.a2ui-log-output-pre');
    const adapter = {
      setLog(text) {
        preEl.textContent = text;
        preEl.scrollTop = preEl.scrollHeight;   // auto-follow the tail, like a real terminal
      },
      setStatus(lifecycle) { el.dataset.lifecycle = lifecycle; },
    };
    return { element: el, controller: createLogOutputController(adapter) };
  }

  // ─── live_confidence_bar controller ─────────────────────────────────────
  // Patch-mode and event-driven probability/confidence bar controller.
  // Extends the static confidence_bar atom (renderers/web_article.py)
  // for live streaming agent evaluations and classifier scoring.
  // Handles single-item ({label, value}) and multi-item ({items: [...]})
  // state shapes, normalizes scores (0-100), and calculates standard
  // threshold colors (>=70 green, >=40 amber, <40 red) unless overridden.
  function createLiveConfidenceBarController(adapter) {
    function computeColor(pct, override) {
      if (override) return override;
      if (pct >= 70) return '#22c55e';
      if (pct >= 40) return '#f59e0b';
      return '#ef4444';
    }

    function normalizeItem(raw, globalColor) {
      if (!raw || typeof raw !== 'object') return null;
      let val = Number(raw.value);
      if (isNaN(val)) val = 0;
      // If provided as a fraction 0.0 - 1.0 (and > 0), scale to 0-100
      if (val > 0 && val <= 1 && !raw.isPercent) {
        val = val * 100;
      }
      val = Math.max(0, Math.min(100, Math.round(val)));
      const label = raw.label != null ? String(raw.label) : 'Confidence';
      const color = computeColor(val, raw.color || globalColor);
      return { label, value: val, color };
    }

    return {
      onEvent(event) {
        const src = event.state || event.payload || {};
        const globalColor = src.color || '';
        let items = [];

        if (Array.isArray(src.items)) {
          for (const raw of src.items) {
            const item = normalizeItem(raw, globalColor);
            if (item) items.push(item);
          }
        } else if (src.value !== undefined || src.label !== undefined) {
          const item = normalizeItem(src, globalColor);
          if (item) items.push(item);
        }

        adapter.setItems(items);
        adapter.setStatus(event.lifecycle);
      },
      destroy() {},
    };
  }

  function mountLiveConfidenceBar(container) {
    const el = document.createElement('div');
    el.className = 'a2ui-confidence-bar';
    container.appendChild(el);

    const adapter = {
      setItems(items) {
        el.innerHTML = '';
        for (const it of items) {
          const row = document.createElement('div');
          row.className = 'a2ui-confidence-row';
          row.style.marginBottom = '8px';

          const header = document.createElement('div');
          header.className = 'a2ui-confidence-header';
          header.style.cssText = 'display:flex;justify-content:space-between;font-size:0.78rem;color:#374151;margin-bottom:3px;';

          const lbl = document.createElement('span');
          lbl.textContent = it.label;
          const pct = document.createElement('span');
          pct.style.fontWeight = '700';
          pct.style.color = it.color;
          pct.textContent = it.value + '%';

          header.appendChild(lbl);
          header.appendChild(pct);

          const track = document.createElement('div');
          track.className = 'a2ui-confidence-track';
          track.style.cssText = 'background:#f3f4f6;border-radius:4px;height:8px;overflow:hidden;';

          const fill = document.createElement('div');
          fill.className = 'a2ui-confidence-fill';
          fill.style.cssText = 'width:' + it.value + '%;height:100%;background:' + it.color + ';border-radius:4px;transition:width .4s;';

          track.appendChild(fill);
          row.appendChild(header);
          row.appendChild(track);
          el.appendChild(row);
        }
      },
      setStatus(lifecycle) { el.dataset.lifecycle = lifecycle; },
    };
    return { element: el, controller: createLiveConfidenceBarController(adapter) };
  }

  function mountCompactConfidenceBar(container) {
    const el = document.createElement('div');
    el.className = 'a2ui-confidence-compact';
    el.style.cssText = 'display:inline-flex;align-items:center;gap:6px;font-size:0.8rem;padding:2px 8px;border-radius:12px;background:#f3f4f6;font-family:ui-monospace,monospace;';
    container.appendChild(el);

    const adapter = {
      setItems(items) {
        if (!items || items.length === 0) {
          el.textContent = '--%';
          el.style.color = '#6b7280';
          return;
        }
        const first = items[0];
        el.textContent = (items.length === 1 ? first.label + ': ' : '') + first.value + '%';
        el.style.color = first.color;
        el.style.fontWeight = '700';
      },
      setStatus(lifecycle) { el.dataset.lifecycle = lifecycle; },
    };
    return { element: el, controller: createLiveConfidenceBarController(adapter) };
  }

  const exportsObj = {
    createStreamingTextController, createStepTrackerController, createToolCallController,
    createReasoningTraceController, createLiveStateDashboardController, createFileEditCardController,
    createAgentRunSketchController, createLiveCostTrendController, createLogOutputController,
    createLiveConfidenceBarController,
    mountToolCallCard, mountReasoningTrace, mountLiveStateDashboard, mountFileEditCard,
    mountAgentRunSketch, mountLiveCostTrend, mountTokenBudgetMeter, mountLogOutput,
    mountLiveConfidenceBar, mountCompactConfidenceBar,
    mountStreamingText, mountLiveStepTracker,
  };
  if (typeof module !== 'undefined' && module.exports) module.exports = exportsObj;
  else global.A2UIAtomsLive = exportsObj;
})(typeof window !== 'undefined' ? window : global);
