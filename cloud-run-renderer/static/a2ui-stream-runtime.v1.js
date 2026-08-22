/**
 * a2ui-stream-runtime — the shared client runtime for live/streaming a2ui
 * atoms, driven by AG-UI protocol events over SSE.
 *
 * PHASE 1 of launch/agentic-realtime-streaming-brief.md (a2ui-private):
 * this file is the runtime CORE — event ingestion, composite routing,
 * container/slot dynamic mounting, the shared lifecycle state machine,
 * JSON-Patch state application, markdown-safe append-mode buffering, and
 * RAF-batched dispatch. It does NOT know how any specific atom renders —
 * that's an "atom controller" an individual atom type registers, built in
 * Phase 2/3. This file is loaded via a plain <script> tag (no bundler, no
 * build step — consistent with the rest of this repo's server-rendered-
 * HTML-page model) ONLY on pages containing at least one streaming-capable
 * atom; every atom must still render correctly from a static snapshot
 * alone with this script entirely absent (progressive enhancement, not a
 * hard requirement — see the brief's own §3).
 *
 * VERSIONED FILENAME (v1) deliberately, not a bare a2ui-stream-runtime.js
 * — cache-busting for a runtime fix must not require guessing whether an
 * edge/CDN cache is still serving stale JS against newly generated atom
 * HTML (found on Gemini review of the design, 2026-08-22, before any code
 * was written).
 *
 * TRANSPORT: SSE via fetch()+ReadableStream, NOT the native EventSource
 * API — found on the SAME review pass: EventSource is GET-only and
 * cannot send custom headers (auth, session/stream routing), which this
 * runtime's own connect() signature already assumes it can do. Parsing
 * the SSE wire format by hand here (data:/event:/id: lines, blank-line
 * dispatch) is the real, if small, cost of that choice.
 *
 * SCOPE NOTE on markdown-safety: this implements delimiter-balance
 * tracking for triple-backtick code fences and single/double
 * asterisk/underscore emphasis only — holding back an unclosed tail
 * until it resolves rather than a full incremental CommonMark parser.
 * Real, tested, and sufficient for the common streaming-LLM-text case;
 * NOT a complete markdown implementation. Documented here so a future
 * reader doesn't assume more coverage than exists.
 */
(function (global) {
  'use strict';

  // ─── SSE wire-format parsing ──────────────────────────────────────────
  // Buffers raw text chunks and yields {event, data, id} records once a
  // full "\n\n"-terminated block has arrived. `event` defaults to
  // "message" per the SSE spec when no `event:` line is present.
  function createSseParser(onRecord) {
    let buffer = '';
    return {
      push(chunk) {
        buffer += chunk;
        let idx;
        while ((idx = buffer.indexOf('\n\n')) !== -1) {
          const block = buffer.slice(0, idx);
          buffer = buffer.slice(idx + 2);
          const record = { event: 'message', data: '', id: null };
          const dataLines = [];
          for (const line of block.split('\n')) {
            if (line.startsWith('event:')) record.event = line.slice(6).trim();
            else if (line.startsWith('data:')) dataLines.push(line.slice(5).trim());
            else if (line.startsWith('id:')) record.id = line.slice(3).trim();
            // comment lines (":") and unrecognized fields are ignored, per spec
          }
          record.data = dataLines.join('\n');
          if (record.data !== '') onRecord(record);
        }
      },
    };
  }

  // ─── JSON Patch (RFC 6902), the subset AG-UI's own StateDelta uses ────
  // add / replace / remove / move / copy / test — dependency-free rather
  // than pulling in a library for ~40 real lines.
  function jsonPatchApply(doc, patch) {
    for (const op of patch) {
      const path = parsePointer(op.path);
      switch (op.op) {
        case 'add':
        case 'replace':
          setAtPointer(doc, path, op.value);
          break;
        case 'remove':
          removeAtPointer(doc, path);
          break;
        case 'move': {
          const val = getAtPointer(doc, parsePointer(op.from));
          removeAtPointer(doc, parsePointer(op.from));
          setAtPointer(doc, path, val);
          break;
        }
        case 'copy': {
          const val = getAtPointer(doc, parsePointer(op.from));
          setAtPointer(doc, path, val);
          break;
        }
        case 'test': {
          const val = getAtPointer(doc, path);
          if (JSON.stringify(val) !== JSON.stringify(op.value)) {
            throw new Error('JSON Patch test failed at ' + op.path);
          }
          break;
        }
        default:
          throw new Error('Unsupported JSON Patch op: ' + op.op);
      }
    }
    return doc;
  }

  function parsePointer(pointer) {
    if (pointer === '' || pointer === '/') return [];
    return pointer.split('/').slice(1).map((seg) =>
      seg.replace(/~1/g, '/').replace(/~0/g, '~'));
  }

  function getAtPointer(doc, path) {
    let cur = doc;
    for (const seg of path) cur = cur == null ? undefined : cur[seg];
    return cur;
  }

  function setAtPointer(doc, path, value) {
    if (path.length === 0) throw new Error('Cannot replace document root via patch');
    let cur = doc;
    for (let i = 0; i < path.length - 1; i++) {
      const seg = path[i];
      if (cur[seg] === undefined) cur[seg] = /^\d+$/.test(path[i + 1]) ? [] : {};
      cur = cur[seg];
    }
    const last = path[path.length - 1];
    if (Array.isArray(cur) && last === '-') cur.push(value);
    else cur[last] = value;
  }

  function removeAtPointer(doc, path) {
    let cur = doc;
    for (let i = 0; i < path.length - 1; i++) cur = cur[path[i]];
    const last = path[path.length - 1];
    if (Array.isArray(cur)) cur.splice(Number(last), 1);
    else delete cur[last];
  }

  // ─── Markdown-safe incremental text buffer ────────────────────────────
  // Tracks unclosed ``` fences and unclosed */_ emphasis runs; returns the
  // longest PREFIX of the accumulated text that is safe to render (no
  // dangling delimiter), holding the rest back until it resolves or
  // flush(force=true) is called at stream End.
  function createSafeTextBuffer() {
    let raw = '';
    function safePrefixLength(text) {
      const fenceMatches = text.match(/```/g);
      const openFence = fenceMatches ? fenceMatches.length % 2 === 1 : false;
      if (openFence) {
        const lastFence = text.lastIndexOf('```');
        return lastFence; // hold back from the start of the unclosed fence
      }
      // Unclosed **bold** / *italic* / __bold__ / _italic_ — find the
      // last UNPAIRED run of a given delimiter and hold back from there.
      let cut = text.length;
      for (const delim of ['**', '__', '*', '_']) {
        const count = countNonOverlapping(text, delim);
        if (count % 2 === 1) {
          const lastIdx = text.lastIndexOf(delim);
          if (lastIdx !== -1) cut = Math.min(cut, lastIdx);
        }
      }
      return cut;
    }
    function countNonOverlapping(text, needle) {
      let count = 0, i = 0;
      while ((i = text.indexOf(needle, i)) !== -1) { count++; i += needle.length; }
      return count;
    }
    return {
      append(chunk) { raw += chunk; },
      /** Returns the text currently safe to render. `force`=true (stream
       * End) returns everything, unclosed delimiters and all — a
       * genuinely malformed stream shouldn't hang the last bit of text
       * forever. */
      flush(force) {
        return force ? raw : raw.slice(0, safePrefixLength(raw));
      },
      raw() { return raw; },
    };
  }

  // ─── RAF batching ──────────────────────────────────────────────────────
  // Coalesces rapid dispatch() calls into one flush per animation frame.
  // Injectable requestAnimationFrame/cancelAnimationFrame so this is
  // testable under Node/jsdom without a real browser paint loop.
  function createBatcher(raf, caf, onFlush) {
    let pending = [];
    let frame = null;
    return {
      push(item) {
        pending.push(item);
        if (frame === null) {
          frame = raf(() => {
            frame = null;
            const batch = pending;
            pending = [];
            onFlush(batch);
          });
        }
      },
      /** Cancels any pending frame — MUST be called on disconnect/unmount
       * so a leaked RAF never fires after the runtime is torn down. */
      cancel() {
        if (frame !== null) { caf(frame); frame = null; }
        pending = [];
      },
      /** Processes whatever's currently queued RIGHT NOW, without waiting
       * for the next animation frame — needed on a connection error:
       * content that already arrived (even if its frame hasn't painted
       * yet) must still reach its controller before that controller gets
       * marked ERROR, or a genuine chunk that DID arrive would be
       * silently dropped instead of shown-then-errored. Found live,
       * 2026-08-22: a test simulating a connection dying immediately
       * after one chunk arrived proved the queued chunk's own mount
       * never happened, so the error path had no controller left to
       * mark. */
      flushNow() {
        if (frame !== null) { caf(frame); frame = null; }
        if (pending.length === 0) return;
        const batch = pending;
        pending = [];
        onFlush(batch);
      },
    };
  }

  // ─── Lifecycle state machine ───────────────────────────────────────────
  // idle -> streaming -> complete | error. Shared shape every atom
  // controller can rely on rather than reimplementing per atom.
  const LIFECYCLE = Object.freeze({ IDLE: 'idle', STREAMING: 'streaming',
                                    COMPLETE: 'complete', ERROR: 'error' });

  function nextLifecycleState(current, eventType) {
    const startEvents = new Set(['RunStarted', 'StepStarted', 'TextMessageStart',
      'ToolCallStart', 'ReasoningStart', 'ReasoningMessageStart']);
    const endEvents = new Set(['RunFinished', 'StepFinished', 'TextMessageEnd',
      'ToolCallEnd', 'ToolCallResult', 'ReasoningEnd', 'ReasoningMessageEnd']);
    const errorEvents = new Set(['RunError']);
    // StateSnapshot/StateDelta have no Start/End framing in AG-UI's own
    // taxonomy at all — they're point signals, not part of a
    // request/response sequence. Found live in the browser harness,
    // 2026-08-22: without this, a live_state_dashboard atom stayed
    // labeled "idle" FOREVER while actively receiving real deltas —
    // honestly misleading for something that's genuinely live. Treated
    // as an implicit "this key is live" signal: the first state event
    // moves idle -> streaming, same as any other start event.
    //
    // KNOWN, DEFERRED GAP (not solved here): a pure state-family atom has
    // no explicit END tied to its owning run, because RunFinished/
    // RunError route under the LIFECYCLE family's own key
    // (lifecycle:<runId>), not the state family's (state:<runId>) — they
    // share a correlation id but are two separate mounted controllers.
    // Cross-family lifecycle propagation (so a state atom also settles
    // to complete when its run finishes) is real, out of scope for
    // proving the core mechanism, and worth a real design pass before
    // live_state_dashboard ships for real in Phase 3.
    const stateEvents = new Set(['StateSnapshot', 'StateDelta']);
    if (errorEvents.has(eventType)) return LIFECYCLE.ERROR;
    if (startEvents.has(eventType)) return LIFECYCLE.STREAMING;
    if (endEvents.has(eventType)) return LIFECYCLE.COMPLETE;
    if (stateEvents.has(eventType) && current === LIFECYCLE.IDLE) return LIFECYCLE.STREAMING;
    return current; // content/delta/chunk events don't otherwise change lifecycle state
  }

  // ─── Composite routing key ─────────────────────────────────────────────
  // AG-UI events carry different id fields depending on type — this is
  // the one place that knows how to build a stable routing key from any
  // of them, per the brief's own "composite key, not a bare stream_id"
  // correction.
  function routingKeyFor(event) {
    const d = event.payload || {};
    const corr = d.toolCallId || d.tool_call_id || d.messageId || d.message_id
               || d.stepId || d.step_id || d.runId || d.run_id || '_run';
    return String(event.type_family || 'unknown') + ':' + String(corr);
  }

  function typeFamily(eventType) {
    if (eventType.startsWith('Run') || eventType.startsWith('Step')) return 'lifecycle';
    if (eventType.startsWith('TextMessage')) return 'text';
    if (eventType.startsWith('ToolCall')) return 'tool_call';
    if (eventType === 'StateSnapshot' || eventType === 'StateDelta' || eventType === 'MessagesSnapshot') return 'state';
    if (eventType.startsWith('Activity')) return 'activity';
    if (eventType.startsWith('Reasoning')) return 'reasoning';
    return 'other';
  }

  // ─── The runtime itself ────────────────────────────────────────────────
  /**
   * @param {Object} opts
   * @param {Element} opts.container - DOM element new child atoms mount into
   * @param {Function} opts.mountAtom - (typeFamily, routingKey, firstEvent) => controller
   *   controller: { onEvent(event), destroy() } — Phase 2/3 supplies real ones.
   * @param {Function} [opts.raf] - injectable requestAnimationFrame, for tests
   * @param {Function} [opts.caf] - injectable cancelAnimationFrame, for tests
   */
  function A2UIStreamRuntime(opts) {
    const container = opts.container;
    const mountAtom = opts.mountAtom;
    const raf = opts.raf || (typeof requestAnimationFrame !== 'undefined'
      ? requestAnimationFrame.bind(global) : (fn) => setTimeout(fn, 16));
    const caf = opts.caf || (typeof cancelAnimationFrame !== 'undefined'
      ? cancelAnimationFrame.bind(global) : clearTimeout);

    const controllers = new Map(); // routingKey -> { controller, lifecycle }
    const stateDocs = new Map();   // routingKey -> current state object (patch-mode)
    let abortController = null;
    let closed = false;

    const batcher = createBatcher(raf, caf, (batch) => {
      for (const event of batch) dispatch(event);
    });

    function dispatch(event) {
      if (closed) return;
      const family = typeFamily(event.type);
      event.type_family = family;
      const key = routingKeyFor(event);

      // Snapshot events are a HARD RESET for their routing key, per the
      // brief's own correction — overrides any in-flight delta sequence,
      // never merges with it.
      if (event.type === 'StateSnapshot' || event.type === 'MessagesSnapshot') {
        stateDocs.set(key, event.payload && event.payload.snapshot !== undefined
          ? event.payload.snapshot : (event.payload || {}));
      } else if (event.type === 'StateDelta') {
        const doc = stateDocs.get(key) || {};
        jsonPatchApply(doc, event.payload && event.payload.delta || []);
        stateDocs.set(key, doc);
      }

      let entry = controllers.get(key);
      if (!entry) {
        const controller = mountAtom(family, key, event, container);
        entry = { controller, lifecycle: LIFECYCLE.IDLE };
        controllers.set(key, entry);
      }
      entry.lifecycle = nextLifecycleState(entry.lifecycle, event.type);
      const snapshotDoc = stateDocs.get(key);
      try {
        entry.controller.onEvent(Object.assign({}, event, {
          lifecycle: entry.lifecycle,
          state: snapshotDoc,
        }));
      } catch (e) {
        // A misbehaving atom controller must not take the whole runtime
        // down — matches the fail-open-for-the-OTHER-atoms, fail-visible-
        // for-this-one shape the rest of this event's own error handling
        // already uses.
        entry.lifecycle = LIFECYCLE.ERROR;
        if (global.console) console.error('a2ui-stream-runtime: atom controller threw', key, e);
      }

      // Terminal states get their controller cleaned up but stay resolvable
      // (no re-mount) — a late-arriving duplicate End event must not crash.
    }

    const sseParser = createSseParser((record) => {
      let event;
      try {
        const data = JSON.parse(record.data);
        event = { type: record.event !== 'message' ? record.event : data.type, payload: data };
      } catch (e) {
        if (global.console) console.error('a2ui-stream-runtime: unparseable SSE record', record, e);
        return;
      }
      batcher.push(event);
    });

    return {
      LIFECYCLE,
      /** Opens the SSE connection via fetch()+ReadableStream (NOT
       * EventSource — see this file's own header comment for why). */
      async connect(url, fetchOpts) {
        abortController = (typeof AbortController !== 'undefined') ? new AbortController() : null;
        const init = Object.assign({}, fetchOpts, abortController ? { signal: abortController.signal } : {});
        let resp;
        try {
          resp = await (opts.fetch || global.fetch)(url, init);
        } catch (e) {
          this._onConnectionError(e);
          return;
        }
        if (!resp.body) { this._onConnectionError(new Error('no response body / streaming not supported')); return; }
        const reader = resp.body.getReader();
        const decoder = new TextDecoder();
        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            sseParser.push(decoder.decode(value, { stream: true }));
          }
        } catch (e) {
          this._onConnectionError(e);
        }
      },
      /** Every disconnect path — normal close, abort, or a stream error —
       * must never leave an active controller spinning forever, and must
       * cancel the batcher's own RAF loop so nothing fires after
       * teardown. Flushes any still-queued (not yet painted) events
       * FIRST — content that genuinely arrived must still reach its
       * controller before that controller is marked ERROR, or it would
       * be silently dropped instead of shown-then-errored. */
      _onConnectionError(e) {
        batcher.flushNow();
        for (const [, entry] of controllers) {
          entry.lifecycle = LIFECYCLE.ERROR;
          try { entry.controller.onEvent({ type: 'RunError', payload: { message: String(e) }, lifecycle: LIFECYCLE.ERROR }); }
          catch (err) { if (global.console) console.error(err); }
        }
      },
      disconnect() {
        closed = true;
        if (abortController) abortController.abort();
        batcher.cancel();
        for (const [, entry] of controllers) { try { entry.controller.destroy(); } catch (e) {} }
        controllers.clear();
        stateDocs.clear();
      },
      /** Test/harness hook — feeds one already-decoded SSE text chunk
       * directly, bypassing the network. */
      _ingestRawChunk(chunk) { sseParser.push(chunk); },
      _debugControllers() { return controllers; },
    };
  }

  const exportsObj = {
    A2UIStreamRuntime, jsonPatchApply, createSafeTextBuffer,
    createSseParser, createBatcher, LIFECYCLE, nextLifecycleState,
    routingKeyFor, typeFamily,
  };
  if (typeof module !== 'undefined' && module.exports) module.exports = exportsObj;
  else global.A2UIStream = exportsObj;
})(typeof window !== 'undefined' ? window : global);
