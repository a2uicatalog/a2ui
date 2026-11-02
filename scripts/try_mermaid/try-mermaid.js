/* Mermaid / D2 to film window: window.TryMermaid.mount(el, {compact, workerUrl, bundleUrl}).
 * The text is converted by a Web Worker on this page (scripts/mermaid_arch, no network) into a motion_timeline film payload, which is handed
 * with postMessage to the site's own MCP Apps renderer in an iframe on a separate origin (play.a2uicatalog.ai). Text from the user, the worker or the frame is
 * only ever put into the page with textContent (no HTML parsing of any kind). Messages from the frame are accepted only from that frame and that origin. */
(function () {
  'use strict';
  var MAX_CHARS = 20000, MAX_LINE = 500, MAX_NODES = 12, MAX_EDGES = 16, KILL_MS = 5000, DEBOUNCE_MS = 300, WAIT_MS = 10000;
  var EXAMPLES = {
    flow: { mode: 'mermaid', label: 'Flowchart: agent to screen', text: 'flowchart LR\n  user([User]) -->|asks| agent[Agent]\n  agent -->|looks up| catalogue[(Trusted catalogue)]\n  catalogue -->|returns atoms| agent\n  agent -->|sends payload| renderer[A2UI renderer]\n  renderer -->|draws| screen[Native screen]\n' },
    d2: { mode: 'd2', label: 'D2: web app', text: 'browser: Browser\napi: API\ndb: Database {shape: cylinder}\nbrowser -> api: request\napi -> db: query\ndb -> api: rows\napi -> browser: response\n' },
    seq: { mode: 'mermaid', label: 'Sequence diagram (not supported yet)', text: 'sequenceDiagram\n  User->>Agent: asks\n  Agent->>Renderer: payload\n  Renderer-->>User: screen\n' }
  };
  function el(tag, attrs, kids) {
    var n = document.createElement(tag);
    if (attrs) Object.keys(attrs).forEach(function (k) { if (k === 'text') n.textContent = attrs[k]; else if (k === 'class') n.className = attrs[k]; else n.setAttribute(k, attrs[k]); });
    (kids || []).forEach(function (c) { if (c) n.appendChild(c); });
    return n;
  }
  function fmt(n) { return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ','); }
  var uid = 0;

  function mount(root, opts) {
    opts = opts || {};
    var ds = root.dataset || {};
    var workerUrl = opts.workerUrl || ds.worker || '/try-mermaid/convert.worker.js';
    var bundleUrl = opts.bundleUrl || ds.bundle || 'https://play.a2uicatalog.ai/renderer-bundle';
    var origin; try { origin = new URL(bundleUrl, location.href).origin; } catch (e) { return null; }
    var verified = (opts.noUpload !== undefined ? opts.noUpload : ds.noupload === '1');
    var n = ++uid, id = function (s) { return 'tm' + n + '-' + s; };
    var mode = 'mermaid', worker = null, jobId = 0, killTimer = null, debounce = null, last = null, frame = null, ready = false, waitTimer = null, veil = null, paused = false, focused = false;
    root.textContent = '';
    root.classList.add('tm'); if (opts.compact || ds.compact === '1') root.classList.add('tm-compact');

    // ---- controls
    var bMer = el('button', { type: 'button', 'aria-pressed': 'true', text: 'Mermaid' }), bD2 = el('button', { type: 'button', 'aria-pressed': 'false', text: 'D2' });
    var seg = el('div', { class: 'tm-seg', role: 'group', 'aria-label': 'Input language' }, [bMer, bD2]);
    var exSel = el('select', { class: 'tm-select', id: id('ex'), 'aria-label': 'Load an example' }, [el('option', { value: '', text: 'Examples…' })]);
    Object.keys(EXAMPLES).forEach(function (k) { exSel.appendChild(el('option', { value: k, text: EXAMPLES[k].label })); });
    var ta = el('textarea', { class: 'tm-ta', id: id('src'), spellcheck: 'false', autocapitalize: 'off', autocomplete: 'off', autocorrect: 'off', 'aria-describedby': id('count') + ' ' + id('status') });
    var lab = el('label', { class: 'tm-sr', for: id('src'), text: 'Mermaid or D2 source' });
    var cChars = el('span'), cNodes = el('span', { text: 'nodes: –' }), cEdges = el('span', { text: 'edges: –' });
    var counter = el('div', { class: 'tm-counter', id: id('count') }, [cChars, cNodes, cEdges]);
    var cbRel = el('input', { type: 'checkbox', id: id('rel') }), selPace = el('select', { class: 'tm-select', id: id('pace') }), selDir = el('select', { class: 'tm-select', id: id('dir') });
    [['normal', 'Normal pace'], ['slow', 'Slow pace'], ['fast', 'Fast pace']].forEach(function (p) { selPace.appendChild(el('option', { value: p[0], text: p[1] })); });
    [['', 'Layout: automatic'], ['LR', 'Left to right'], ['TB', 'Top to bottom']].forEach(function (p) { selDir.appendChild(el('option', { value: p[0], text: p[1] })); });
    selPace.setAttribute('aria-label', 'Pace'); selDir.setAttribute('aria-label', 'Layout');
    var opt = el('div', { class: 'tm-opts' }, [el('label', { for: id('rel') }, [cbRel, el('span', { text: 'Show relation column' })]), selPace, selDir]);
    var status = el('p', { class: 'tm-status', id: id('status'), role: 'status', 'aria-live': 'polite' });
    var errs = el('ul', { class: 'tm-errs', 'aria-label': 'Problems with the input' }); errs.hidden = true;
    var warns = el('ul', { class: 'tm-warns', 'aria-label': 'Notes about the drawing' }); warns.hidden = true;
    var controls = el('div', { class: 'tm-controls' }, [el('div', { class: 'tm-panel' }, [
      el('div', { class: 'tm-row' }, [seg, exSel]), opt, lab, ta, counter, status, errs, warns])]);

    // ---- stage
    var empty = el('div', { class: 'tm-empty', text: 'Paste a diagram on the right. The film appears here.' });
    var close = el('button', { type: 'button', class: 'tm-btn tm-close', text: 'Close', 'aria-keyshortcuts': 'Escape', title: 'Close (Escape). Escape works while focus is outside the film; from inside it, Shift+Tab reaches Close.' });
    var box = el('div', { class: 'tm-box' }, [empty, close]);
    var bPause = el('button', { type: 'button', class: 'tm-btn', 'aria-pressed': 'false', text: 'Pause' });
    var bFocus = el('button', { type: 'button', class: 'tm-btn', text: 'Focus' }); bFocus.setAttribute('aria-label', 'Focus: enlarge the film');
    var bCopy = el('button', { type: 'button', class: 'tm-btn tm-primary', text: 'Copy payload' }), bDown = el('button', { type: 'button', class: 'tm-btn', text: 'Download JSON' });
    [bPause, bFocus, bCopy, bDown].forEach(function (b) { b.disabled = true; });
    var bar = el('div', { class: 'tm-bar', role: 'group', 'aria-label': 'Film controls' }, [bPause, bFocus, el('div', { class: 'tm-out' }, [bCopy, bDown])]);
    var stepsBody = el('tbody'), msgBody = el('tbody');
    var stepsTable = el('table', null, [el('caption', { text: 'Steps' }), el('thead', null, [el('tr', null, [el('th', { scope: 'col', text: 'Step' }), el('th', { scope: 'col', text: 'Activity' })])]), stepsBody]);
    var msgTable = el('table', null, [el('caption', { text: 'Messages' }), el('thead', null, [el('tr', null, [el('th', { scope: 'col', text: 'Step' }), el('th', { scope: 'col', text: 'Message' }), el('th', { scope: 'col', text: 'Direction' })])]), msgBody]);
    var details = el('details', { class: 'tm-steps' }, [el('summary', { text: 'Steps and messages as text' }), el('div', { class: 'tm-scroll' }, [stepsTable, msgTable])]);
    details.hidden = true;
    var foot = el('p', { class: 'tm-foot' });
    foot.textContent = (verified ? 'Runs in your browser. Your diagram is not uploaded. ' : '') + 'Copy the payload to use it on any atom page or with an agent. MP4 and GIF of your own film are not available here yet.';
    var backdrop = el('div', { class: 'tm-backdrop' }); backdrop.hidden = true;
    var stage = el('div', { class: 'tm-stage' }, [box, bar, details, foot, backdrop]);
    root.appendChild(controls); root.appendChild(stage);

    // ---- helpers
    function say(msg, cls) { status.textContent = msg || ''; status.className = 'tm-status' + (cls ? ' ' + cls : ''); }
    function showList(ul, items) { ul.textContent = ''; items.forEach(function (t) { t = String(t); ul.appendChild(el('li', { text: t.charAt(0).toUpperCase() + t.slice(1) })); }); ul.hidden = !items.length; }
    function tally(counts) {
      var len = ta.value.length;
      cChars.textContent = fmt(len) + ' / ' + fmt(MAX_CHARS) + ' characters'; cChars.className = len > MAX_CHARS ? 'tm-over' : '';
      cNodes.textContent = 'nodes: ' + (counts ? counts.nodes + ' of ' + MAX_NODES : '–'); cNodes.className = counts && counts.nodes > MAX_NODES ? 'tm-over' : '';
      cEdges.textContent = 'edges: ' + (counts ? counts.edges + ' of ' + MAX_EDGES : '–'); cEdges.className = counts && counts.edges > MAX_EDGES ? 'tm-over' : '';
    }
    function setMode(m) { mode = m; bMer.setAttribute('aria-pressed', String(m === 'mermaid')); bD2.setAttribute('aria-pressed', String(m === 'd2')); }
    function theme() { var t = document.documentElement.getAttribute('data-theme'); return t === 'dark' || t === 'light' ? t : (window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'); }

    // ---- worker
    function killWorker() { if (worker) { try { worker.terminate(); } catch (e) {} worker = null; } clearTimeout(killTimer); }
    function convert() {
      var text = ta.value;
      showList(errs, []); ta.setAttribute('aria-invalid', 'false');
      tally(null);
      if (!text.trim()) { showList(warns, []); say('Paste a diagram to start.'); clearFilm(); return; }
      if (text.length > MAX_CHARS) { fail(['The input is ' + fmt(text.length) + ' characters; the limit is ' + fmt(MAX_CHARS) + '.'], null); return; }
      var rows = text.split('\n');
      for (var i = 0; i < rows.length; i++) if (rows[i].length > MAX_LINE) { fail(['line ' + (i + 1) + ' is ' + fmt(rows[i].length) + ' characters; the limit is ' + MAX_LINE + ' per line.'], null); return; }
      if (!window.Worker) { say('This browser cannot run the converter (no Web Worker support).', 'tm-err'); return; }
      var my = ++jobId; say('Converting…');
      try { if (!worker) { worker = new Worker(workerUrl); worker.onmessage = onResult; worker.onerror = function () { killWorker(); say('The converter could not start. Reload the page and try again.', 'tm-err'); }; } } catch (e) { say('The converter could not start.', 'tm-err'); return; }
      clearTimeout(killTimer);
      killTimer = setTimeout(function () { if (my === jobId) { killWorker(); jobId++; fail(['Converting took longer than ' + (KILL_MS / 1000) + ' seconds, so it was stopped. Try a smaller diagram.'], null); } }, KILL_MS);
      worker.postMessage({ id: my, mode: mode, text: text, relation: cbRel.checked, pace: selPace.value, direction: selDir.value });
    }
    function onResult(ev) {
      var r = ev.data; if (!r || r.id !== jobId) return;
      clearTimeout(killTimer);
      if (r.counts) tally(r.counts);
      showList(warns, Array.isArray(r.warnings) ? r.warnings.map(String).slice(0, 8) : []);
      if (!r.ok) { fail((r.errors || []).map(String), r.counts); return; }
      var secs = typeof r.durationSeconds === 'number' ? ' (' + Math.round(r.durationSeconds) + ' s film)' : '';
      say('Converted' + secs + '. Playing it now.', ''); last = r;
      fillText(r); setAspect(r.payload.blocks[0]); show(r.payload.blocks);
      [bFocus, bCopy, bDown, bPause].forEach(function (b) { b.disabled = false; });
    }
    function fail(list, counts) {
      if (counts) tally(counts);
      ta.setAttribute('aria-invalid', 'true'); showList(errs, list.slice(0, 20)); say(list.length > 1 ? list.length + ' problems found. The last good film stays on screen.' : 'There is a problem with the input. The last good film stays on screen.', 'tm-err');
    }
    function fillText(r) {
      stepsBody.textContent = ''; msgBody.textContent = '';
      (r.steps || []).forEach(function (s) { stepsBody.appendChild(el('tr', null, [el('td', { text: String(s.step) }), el('td', { text: s.activity })])); });
      (r.messages || []).forEach(function (m) { msgBody.appendChild(el('tr', null, [el('td', { text: String(m.step) }), el('td', { text: m.text }), el('td', { text: m.from + ' to ' + m.to })])); });
      stepsTable.hidden = !(r.steps || []).length; msgTable.hidden = !(r.messages || []).length; details.hidden = stepsTable.hidden && msgTable.hidden;
    }

    // ---- renderer frame (MCP Apps host side, same protocol and checks as the atom page's payload editor)
    function post(m) { if (frame && frame.contentWindow) frame.contentWindow.postMessage(m, origin); }
    function deliver() {
      if (!frame || !ready || !last) return;
      post({ jsonrpc: '2.0', method: 'ui/notifications/tool-result', params: { content: [{ type: 'text', text: 'Rendered A2UI atoms.' }], structuredContent: { theme: theme(), blocks: last.payload.blocks } } });
      clearTimeout(waitTimer);
    }
    window.addEventListener('message', function (ev) {
      if (!frame || ev.source !== frame.contentWindow || ev.origin !== origin) return;
      var m = ev.data;
      if (!m || typeof m !== 'object' || m.jsonrpc !== '2.0' || typeof m.method !== 'string') return;
      var hasId = typeof m.id === 'number' || (typeof m.id === 'string' && m.id.length < 64);
      if (m.method === 'ui/initialize' && hasId) post({ jsonrpc: '2.0', id: m.id, result: { protocolVersion: '2026-01-26', hostContext: { theme: theme(), displayMode: 'inline' }, capabilities: { logging: {} } } });
      else if (m.method === 'ui/notifications/initialized') { ready = true; deliver(); }
      else if (m.method === 'ui/notifications/size-changed') unveil();   // never used for sizing: the box is fixed and the frame scrolls inside it (feeding the height back grew the frame without end)
      else if (hasId) post({ jsonrpc: '2.0', id: m.id, error: { code: -32601, message: 'not available from this page' } });
    });
    function unveil() { if (veil && veil.parentNode) veil.parentNode.removeChild(veil); veil = null; }
    function addVeil() { unveil(); veil = el('div', { class: 'tm-veil', 'aria-hidden': 'true' }, [el('span', { class: 'tm-spin' }), el('span', { text: 'Drawing the film…' })]); box.appendChild(veil); setTimeout(unveil, 2500); }
    function setAspect(b) {
      // the box takes the film's own aspect ratio (as large as the height cap allows), so any film is shown whole, never cropped; a film wider or taller than 2.5:1 is clamped and scrolls
      var m = b && typeof b.aspect === 'string' ? /^(\d{1,3}):(\d{1,3})$/.exec(b.aspect) : null, ar = m && +m[2] ? +m[1] / +m[2] : 0;
      if (!(ar > 0)) { box.classList.remove('has-film'); return; }
      box.style.setProperty('--tm-ar', String(Math.min(2.5, Math.max(0.4, ar)))); box.classList.add('has-film');
    }
    function clearFilm() { box.classList.remove('has-film'); clearTimeout(waitTimer); unveil(); if (frame && frame.parentNode) frame.parentNode.removeChild(frame); frame = null; ready = false; last = null; [bFocus, bCopy, bDown, bPause].forEach(function (b) { b.disabled = true; }); details.hidden = true; if (!empty.parentNode) box.insertBefore(empty, close); }
    function startFrame() {
      ready = false; addVeil();
      frame = el('iframe', { class: 'tm-frame', title: 'Your diagram as a film (scrolls if taller than the box)', tabindex: '0', referrerpolicy: 'no-referrer', loading: 'eager', sandbox: 'allow-scripts allow-same-origin allow-popups allow-popups-to-escape-sandbox' });
      box.insertBefore(frame, close); frame.src = bundleUrl;
      clearTimeout(waitTimer);
      waitTimer = setTimeout(function () { if (!ready) { unveil(); say('The renderer did not answer. Check your connection and edit the text to try again.', 'tm-err'); } }, WAIT_MS);
    }
    function show() {
      if (empty.parentNode) empty.parentNode.removeChild(empty);
      if (paused) setPausedState(false);
      if (frame && frame.parentNode) { addVeil(); deliver(); return; }
      startFrame();
    }
    var pausedNote = null;
    function setPausedState(on) {
      paused = on; bPause.setAttribute('aria-pressed', String(on)); bPause.textContent = on ? 'Paused' : 'Pause';
      if (on) {
        // The renderer has no pause message and a frame on another origin cannot be reached: Pause removes the frame, Play builds it again (the film restarts).
        clearTimeout(waitTimer); unveil(); ready = false; if (frame && frame.parentNode) frame.parentNode.removeChild(frame); frame = null;
        pausedNote = el('div', { class: 'tm-paused', role: 'group', 'aria-label': 'Paused' }, [el('strong', { text: 'Paused' }), el('span', { text: 'The film is not running. Press Paused again to run it from the start.' })]);
        box.insertBefore(pausedNote, close);
      } else { if (pausedNote && pausedNote.parentNode) pausedNote.parentNode.removeChild(pausedNote); pausedNote = null; }
    }
    bPause.addEventListener('click', function () { var on = !paused; setPausedState(on); if (!on && last) startFrame(); });

    // ---- focus (enlarge)
    // While the film is enlarged everything else on the page is made inert (every sibling on the way up from the box, except the backdrop that closes it), so Tab can only
    // reach Close and the film frame (a frame on another origin sends no key events, so a key handler could not trap focus inside it).
    var inerted = [];
    function inertOthers(on) {
      if (!on) { inerted.forEach(function (n) { n.inert = false; }); inerted = []; return; }
      var node = box;
      while (node && node !== document.body && node.parentNode) {
        Array.prototype.forEach.call(node.parentNode.children, function (sib) { if (sib !== node && sib !== backdrop && sib.tagName !== 'SCRIPT' && !sib.inert) { sib.inert = true; inerted.push(sib); } });
        node = node.parentNode;
      }
    }
    function setFocus(on) {
      if (on === focused) return; focused = on;
      stage.classList.toggle('is-focus', on); backdrop.hidden = !on; document.body.classList.toggle('tm-locked', on); inertOthers(on);
      bFocus.setAttribute('aria-expanded', String(on));
      if (on) close.focus(); else bFocus.focus();
    }
    bFocus.addEventListener('click', function () { setFocus(true); }); close.addEventListener('click', function () { setFocus(false); }); backdrop.addEventListener('click', function () { setFocus(false); });
    document.addEventListener('keydown', function (e) { if (focused && e.key === 'Escape') { e.preventDefault(); setFocus(false); } });

    // ---- copy / download
    bCopy.addEventListener('click', function () {
      if (!last) return; var s = JSON.stringify(last.payload, null, 2);
      var done = function () { say('Payload copied. Paste it into the payload editor on any atom page.', ''); };
      var fall = function () { say('Your browser blocked copying. Use Download JSON instead.', 'tm-err'); };
      try { navigator.clipboard.writeText(s).then(done, fall); } catch (e) { fall(); }
    });
    bDown.addEventListener('click', function () {
      if (!last) return;
      try { var a = el('a', { href: URL.createObjectURL(new Blob([JSON.stringify(last.payload, null, 2)], { type: 'application/json' })), download: 'diagram-film.json' }); document.body.appendChild(a); a.click(); setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 500); } catch (e) { say('Your browser blocked the download.', 'tm-err'); }
    });

    // ---- inputs
    function schedule() { tally(null); clearTimeout(debounce); debounce = setTimeout(convert, DEBOUNCE_MS); }
    ta.addEventListener('input', schedule);
    [cbRel, selPace, selDir].forEach(function (c) { c.addEventListener('change', schedule); });
    bMer.addEventListener('click', function () { setMode('mermaid'); schedule(); }); bD2.addEventListener('click', function () { setMode('d2'); schedule(); });
    exSel.addEventListener('change', function () { var x = EXAMPLES[exSel.value]; if (!x) return; setMode(x.mode); ta.value = x.text; exSel.value = ''; ta.focus(); schedule(); });
    var start = EXAMPLES[opts.example || ds.example || 'flow'] || EXAMPLES.flow;
    setMode(start.mode); ta.value = start.text; tally(null); say('Converting…'); debounce = setTimeout(convert, 50);
    return { convert: convert, setText: function (t) { ta.value = t; schedule(); } };
  }
  window.TryMermaid = { mount: mount, limits: { chars: MAX_CHARS, line: MAX_LINE, nodes: MAX_NODES, edges: MAX_EDGES } };
})();
