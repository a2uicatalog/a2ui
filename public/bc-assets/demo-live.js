/* Live panel (slices 3 and 4). Loaded only when the reader opens the Try it dialog (kit.js does that and owns opening, closing, the focus trap and the inert page behind it). Plain JavaScript, no libraries.
   What it does: one call from this tab to the chosen provider (Gemini, Anthropic, an OpenAI-compatible service or Vertex Express) with the reader's own key,
   then one call to our drawing service with ONLY the model's reply text. The provider list and its fixed addresses come from the manifest (the inert config block).
   Rules kept here:
   - the key goes only to the host of the selected provider, in that provider's own header; changing the provider (or the service) clears the key and the remembered key
   - every piece of dynamic text goes in with textContent; nothing is ever put in as markup
   - the picture is shown only as <img src="data:image/svg+xml;base64,..."> after a check of the prefix and the size
   - the key lives in the input field (memory). It is never put in a URL, a log or the drawing request. Storage only when the box is ticked, and only sessionStorage
   - the owner key (from the URL fragment, handed over by kit.js) is sent only as the header X-Owner-Key to the drawing service, never stored, never shown */
(function () {
  'use strict';
  var cfg, LP = null, lastSaved = null, hasResult = false, lastLedger = null, ledgerOpener = null, ledgerAutoDone = false, pending = null, owner = '', busy = false, token = '', tsWidget = null, tsState = 'off', stage = '';   // stage: '' before any call, 'model' while the provider is asked, 'draw' once it has answered
  var P = null, suggest = null, epoch = 0, modelNotes = [], mem = {}, callModel = '', callDefault = '';   // P: the selected provider (merged with its service); suggest: model ids found for the key; epoch: counts provider changes; modelNote: the retry without the thinking setting happened
  var KEYPREFIX = 'a2ui-live-key-';
  var MODEL_MS = 60000, DRAW_MS = 30000, MAX_SVG = 200 * 1024, MAX_MODEL_TEXT = 600;
  function $(id) { return document.getElementById(id); }
  function fmt(tpl, vars) { return tpl.replace(/\{([a-z_]+)\}/g, function (m, k) { return Object.prototype.hasOwnProperty.call(vars, k) ? String(vars[k]) : m; }); }
  function secs(ms) { return (ms / 1000).toFixed(1) + ' s'; }

  /* ---- Gim: each swap builds a fresh <picture> so the animation plays from the start; the still shows when reduced motion is asked for ---- */
  function setGim(mood) {
    var g = cfg.gim[mood], box = $('live-gim');
    var pic = document.createElement('picture'), src = document.createElement('source'), img = document.createElement('img');
    src.media = '(prefers-reduced-motion: reduce)'; src.srcset = g.still;
    img.src = g.anim; img.alt = g.alt; img.width = 64; img.height = 64;
    pic.appendChild(src); pic.appendChild(img);
    box.replaceChildren(pic);
    box.setAttribute('data-mood', mood);
  }
  function setStatus(text) { $('live-status').textContent = text; }
  function showPending(text) { var p = $('live-pending'); p.textContent = text; p.hidden = false; }
  function begin(q) {   // a question is on its way: the old result is gone, the view returns to the top, the empty state gives way to the question bubble and a working line
    $('live-result').hidden = true; hasResult = false; syncForm(); var th = $('live-thread'); if (th) th.scrollTop = 0;
    var ch = $('live-chips'), hint = $('live-hint'); if (ch && hint && !ch.classList.contains('chips-bar')) { ch.classList.add('chips-bar'); hint.parentNode.insertBefore(ch, hint.nextSibling); }   // the saved examples stay one tap away: the chip row leaves the empty state (which gives way to the conversation) and sits under the bar
    $('live-hello').hidden = true; var b = $('live-qbubble'); b.textContent = q; b.hidden = false; $('live-pending').hidden = true;
  }
  function syncFallback() {   // the fallback button never offers the model that is already selected
    var fb = $('live-fallback'); if (!fb.hidden && $('live-model').value.trim() === callDefault) fb.hidden = true;
  }
  function openSettings(focusKey) { $('live-settings').open = true; if (focusKey) $('live-key').focus(); }

  function hideError() {
    $('live-error').hidden = true; $('live-error-reason').hidden = true; $('live-error-model-wrap').hidden = true; $('live-fallback').hidden = true; $('live-retry').hidden = true;
    $('live-error-model').textContent = '';
  }
  function fail(text, opts) {
    opts = opts || {};
    $('live-result').hidden = true; $('live-pending').hidden = true; hasResult = false; syncForm();
    $('live-error-text').textContent = text;
    var r = $('live-error-reason'); r.hidden = !opts.reason; r.textContent = opts.reason || '';
    var w = $('live-error-model-wrap'); w.hidden = typeof opts.modelText !== 'string';
    $('live-error-model').textContent = typeof opts.modelText === 'string' ? opts.modelText.slice(0, MAX_MODEL_TEXT) : '';
    var fb = $('live-fallback');
    var fbModel = callModel || $('live-model').value.trim(), fbDefault = callDefault || P.default_model;   // the model that was asked and the default of the provider that was asked
    if (opts.fallback && fbModel !== fbDefault) { fb.hidden = false; fb.textContent = fmt(cfg.msgs.use_fallback, { fallback: fbDefault }); } else fb.hidden = true;   // the provider's default model is the one offered
    $('live-error').hidden = false;
    $('live-retry').hidden = !opts.retry; if (opts.retry) $('live-retry').textContent = cfg.msgs.retry;
    setGim('confused'); setStatus(stage ? cfg.msgs['status_failed_' + stage] : cfg.msgs.status_error);   // the status names the stage that failed
    $('live-error').focus();
    done();
  }
  function done() { busy = false; $('live-go').removeAttribute('aria-disabled'); $('live-form').removeAttribute('aria-busy'); resetTurnstile(); }

  /* ---- the key: memory only, plus sessionStorage when the box is ticked ---- */
  function keySlot() { return KEYPREFIX + P.id + (P.svc ? '-' + P.svc : ''); }   // one slot per provider (and per OpenAI-compatible service)
  function store() {
    try {
      if ($('live-remember').checked && $('live-key').value) sessionStorage.setItem(keySlot(), $('live-key').value);
      else sessionStorage.removeItem(keySlot());
    } catch (e) {}
  }
  function wipeKeys() {   // every remembered key of every provider
    try {
      var ks = [], i;
      for (i = 0; i < sessionStorage.length; i++) { var k = sessionStorage.key(i); if (k && k.indexOf(KEYPREFIX) === 0) ks.push(k); }
      ks.forEach(function (k) { sessionStorage.removeItem(k); });
    } catch (e) {}
  }
  function clearKey() {
    $('live-key').value = ''; $('live-remember').checked = false;
    wipeKeys(); syncFind();
    setStatus(cfg.msgs.status_cleared); openSettings(true);
  }

  /* ---- the providers: the selected one (merged with its service for the OpenAI-compatible entry), what the page shows for it ---- */
  function byId(list, id) { for (var i = 0; i < list.length; i++) if (list[i].id === id) return list[i]; return list[0]; }
  function current() {
    var p = byId(cfg.providers, $('live-provider').value);
    if (p.adapter !== 'openai') return { id: p.id, svc: '', adapter: p.adapter, status: p.status, label: p.label, short: p.short, base: p.base, local: false, default_model: p.default_model, models: p.models, privacy: p.privacy, note: p.note || '' };
    var s = byId(p.services, $('live-service').value);
    return { id: p.id, svc: s.id, adapter: 'openai', status: p.status, label: s.label, short: s.short, base: s.base, local: !!s.local, default_model: s.default_model, models: s.models, privacy: s.privacy, note: s.note || '' };
  }
  function optionsFor(list, value) {   // the model dropdown: the suggestions, then "Other model id"; the text field shows only for Other
    var sel = $('live-model-pick'), inList = list.indexOf(value) >= 0;
    sel.textContent = '';
    list.forEach(function (id) { var o = document.createElement('option'); o.value = id; o.textContent = id; sel.appendChild(o); });
    var other = document.createElement('option'); other.value = '__other__'; other.textContent = cfg.ui.other; sel.appendChild(other);
    sel.value = inList ? value : '__other__';
    $('live-model').value = value; $('live-model-other').hidden = inList;
  }
  function setModel(id) { optionsFor(suggest || P.models, id); setPillModel(); }
  function renderPrivacy() {
    var ul = $('live-privacy-list'), pv = cfg.privacy;
    var items = pv.sets[P.privacy].concat([pv.draw_item, (P.local ? pv.key_item_local : pv.key_item).replace(/\{provider\}/g, P.short)]);
    ul.textContent = '';
    items.forEach(function (s) { var li = document.createElement('li'); li.textContent = s; ul.appendChild(li); });
  }
  function syncFind() {   // the lookup button: only where an endpoint exists, and enabled once there is a key (a local server needs none)
    var b = $('live-find'); b.hidden = !ADAPTERS[P.adapter].list;
    b.disabled = !P.local && !$('live-key').value.trim();
    syncHints();
  }
  function hasKey() { return !!(P && P.local) || !!$('live-key').value.trim(); }
  function syncHints() { $('live-hint').textContent = hasKey() ? cfg.msgs.hint_key : cfg.msgs.hint_no_key; }   // the line under the bar says what the chips and Explain do
  function renderProvider() {
    var p = byId(cfg.providers, $('live-provider').value);
    $('live-service-wrap').hidden = p.adapter !== 'openai';
    var exp = $('live-exp-note'), pn = $('live-prov-note'), ids = [];
    exp.hidden = P.status !== 'experimental'; if (!exp.hidden) ids.push('live-exp-note');
    pn.textContent = P.note; pn.hidden = !P.note; if (P.note) ids.push('live-prov-note');
    var d = ids.join(' ');
    ['live-provider', 'live-service'].forEach(function (i) { if (d) $(i).setAttribute('aria-describedby', d); else $(i).removeAttribute('aria-describedby'); });
    $('live-key-hint').textContent = P.local ? cfg.ui.key_hint_local : cfg.ui.key_hint;
    suggest = null; $('live-find-note').hidden = true; $('live-find-note').textContent = '';
    setModel(P.default_model); renderPrivacy(); syncFind();
  }
  var AIM = { base: 'aim for 12 nodes', 9: 'aim for 9 nodes or fewer', 6: 'aim for 6 nodes' };   // Detailed is the agent's own prompt; the others swap this one phrase
  function detail() { var r = document.querySelector('input[name="live-detail"]:checked'); return r ? parseInt(r.value, 10) : 12; }
  function sysNow() { var d = detail(); return d === 12 || cfg.sys.indexOf(AIM.base) < 0 ? cfg.sys : cfg.sys.replace(AIM.base, AIM[d]); }
  function boxCount(t) { var m = {}, re = /\b([A-Za-z0-9_]+)\[/g, x; while ((x = re.exec(t))) m[x[1]] = 1; return Object.keys(m).length; }
  function syncThink() {   // the toggle only means something for adapters that have a thinking setting; for the rest it is disabled
    var has = !!(P && ADAPTERS[P.adapter] && ADAPTERS[P.adapter].thinking), f = $('live-think'); if (!f) return;
    f.disabled = !has; f.classList.toggle('is-off', !has);
  }
  function onProviderChange() {   // key safety: a new provider never receives the old key
    epoch++; mem = {}; $('live-fallback').hidden = true;
    $('live-key').value = ''; $('live-remember').checked = false; wipeKeys();
    P = current(); renderProvider(); syncThink();
    setStatus(fmt(cfg.msgs.status_provider_changed, { provider: P.label }));   // focus stays on the select that was changed
  }

  /* ---- Turnstile (only when the manifest has a public site key, only on an a2uicatalog.ai host, only after the panel is opened, never for the owner) ---- */
  function onApex() { return /(^|\.)a2uicatalog\.ai$/.test(location.hostname); }
  function setupTurnstile() {
    if (!cfg.site_key || owner) return;
    var note = $('live-ts-note');
    if (!onApex()) { tsState = 'off'; note.hidden = false; note.textContent = cfg.msgs.turnstile_preview; return; }
    tsState = 'loading';
    function blocked() { if (tsState === 'ready' && token) return; tsState = 'failed'; note.hidden = false; note.textContent = cfg.msgs.turnstile_blocked; }   // the check could not run: say so and send nothing (the drawing service would refuse a request without a token)
    function render() {
      try {
        tsWidget = window.turnstile.render($('live-turnstile'), {
          sitekey: cfg.site_key,
          callback: function (t) { token = t; tsState = 'ready'; note.hidden = true; },
          'expired-callback': function () { token = ''; tsState = 'loading'; },
          'error-callback': function () { token = ''; blocked(); }
        });
      } catch (e) { blocked(); }
    }
    setTimeout(function () { if (tsState === 'loading' && !token) blocked(); }, 15000);   // a blocked script or frame says nothing: after 15 seconds the visitor is told
    if (window.turnstile) { render(); return; }
    var s = document.createElement('script');
    s.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit';
    s.async = true; s.onload = render; s.onerror = blocked;
    document.head.appendChild(s);
  }
  function resetTurnstile() {
    if (tsWidget === null || !window.turnstile) return;
    token = ''; tsState = 'loading';
    try { window.turnstile.reset(tsWidget); } catch (e) {}
  }

  /* ---- network helpers ---- */
  function timed(url, init, ms) {
    var ctl = new AbortController(), t = setTimeout(function () { ctl.abort(); }, ms);
    init.signal = ctl.signal;
    return fetch(url, init).then(function (r) { clearTimeout(t); return r; }, function (e) { clearTimeout(t); throw e; });
  }
  function isAbort(e) { return e && e.name === 'AbortError'; }

  /* ---- the adapters: how to ask each provider and how to read its answer. One header helper per key style, so the key appears in one place per style ---- */
  function withJson(h) { h['Content-Type'] = 'application/json'; return h; }
  function googHeaders(key) { return { 'x-goog-api-key': key }; }
  function anthropicHeaders(key) { return { 'x-api-key': key, 'anthropic-version': '2023-06-01', 'anthropic-dangerous-direct-browser-access': 'true' }; }
  function bearer(key) { return key ? { 'Authorization': 'Bearer ' + key } : {}; }   // a local server may need no key: then no header at all
  function usageOf(i, o, t) { i = num(i); o = num(o); t = num(t); return i === null && o === null ? null : { in: i, out: o, think: t }; }
  function geminiBody(q, o) {
    var g = {};
    if (o.temp) g.temperature = 0.2;
    g.maxOutputTokens = 2048;
    if (o.think) g.thinkingConfig = { thinkingLevel: 'low' };
    return { systemInstruction: { parts: [{ text: sysNow() }] }, contents: [{ role: 'user', parts: [{ text: q }] }], generationConfig: g };
  }
  function parseGemini(j) {
    var c = j && j.candidates && j.candidates[0], parts = c && c.content && c.content.parts, u = j && j.usageMetadata && typeof j.usageMetadata === 'object' ? j.usageMetadata : null;
    var text = Array.isArray(parts) ? parts.filter(function (p) { return p && typeof p.text === 'string' && !p.thought; }).map(function (p) { return p.text; }).join('') : '';
    return { text: text, usage: u ? usageOf(u.promptTokenCount, u.candidatesTokenCount, u.thoughtsTokenCount) : null };
  }
  var ADAPTERS = {
    gemini: {
      thinking: true, temp: true,
      build: function (p, model, key, q, o) { return { url: p.base + '/models/' + encodeURIComponent(model) + ':generateContent', headers: withJson(googHeaders(key)), body: geminiBody(q, o) }; },
      parse: parseGemini,
      list: {
        build: function (p, key) { return { url: p.base + '/models?pageSize=200', headers: googHeaders(key) }; },
        ids: function (j) { return (j && Array.isArray(j.models) ? j.models : []).filter(function (m) { return m && typeof m.name === 'string' && Array.isArray(m.supportedGenerationMethods) && m.supportedGenerationMethods.indexOf('generateContent') >= 0; }).map(function (m) { return m.name.replace(/^models\//, ''); }); }
      }
    },
    vertex: {   // the non-streaming address is not documented for Vertex Express; this is the generateContent form of the documented streaming one, hence "experimental"
      thinking: true, temp: true,
      build: function (p, model, key, q, o) { return { url: p.base + '/publishers/google/models/' + encodeURIComponent(model) + ':generateContent', headers: withJson(googHeaders(key)), body: geminiBody(q, o) }; },
      parse: parseGemini,
      list: null
    },
    openai: {
      thinking: false, temp: true,
      build: function (p, model, key, q, o) {
        var b = { model: model, messages: [{ role: 'system', content: sysNow() }, { role: 'user', content: q }] };
        if (o.temp) b.temperature = 0.2;
        b[o.mct ? 'max_completion_tokens' : 'max_tokens'] = 2048;   // a few models take only max_completion_tokens: used after the provider says so
        return { url: p.base + '/chat/completions', headers: withJson(bearer(key)), body: b };
      },
      parse: function (j) {
        var c = j && Array.isArray(j.choices) ? j.choices[0] : null, mc = c && c.message ? c.message.content : '', u = j && j.usage && typeof j.usage === 'object' ? j.usage : null;
        var text = typeof mc === 'string' ? mc : (Array.isArray(mc) ? mc.filter(function (b) { return b && typeof b.text === 'string'; }).map(function (b) { return b.text; }).join('') : '');
        var d = u && u.completion_tokens_details && typeof u.completion_tokens_details === 'object' ? u.completion_tokens_details.reasoning_tokens : null;
        return { text: text, usage: u ? usageOf(u.prompt_tokens, u.completion_tokens, d) : null };
      },
      list: {
        build: function (p, key) { return { url: p.base + '/models', headers: bearer(key) }; },
        ids: function (j) { return (j && Array.isArray(j.data) ? j.data : []).filter(function (m) { return m && typeof m.id === 'string'; }).map(function (m) { return m.id; }); }
      }
    },
    anthropic: {
      thinking: true, temp: false,   // no temperature at all (some models reject it as deprecated); thinking is sent OFF: measured 17 Nov 2026 (Haiku, 320 calls): thinking left on was about 70 percent of the output tokens and about 60 percent of the model time, and truncated replies failed; one retry without the field if a model rejects it
      build: function (p, model, key, q, o) {
        var b = { model: model, max_tokens: 2048, system: sysNow(), messages: [{ role: 'user', content: q }] };
        if (o.think) b.thinking = { type: 'disabled' };
        return { url: p.base + '/messages', headers: withJson(anthropicHeaders(key)), body: b };
      },
      parse: function (j) {   // only the text blocks; thinking and other blocks are ignored
        var blocks = j && Array.isArray(j.content) ? j.content : [], u = j && j.usage && typeof j.usage === 'object' ? j.usage : null;
        var text = blocks.filter(function (b) { return b && b.type === 'text' && typeof b.text === 'string'; }).map(function (b) { return b.text; }).join('');
        return { text: text, usage: u ? usageOf(u.input_tokens, u.output_tokens, null) : null };
      },
      list: {
        build: function (p, key) { return { url: p.base + '/models', headers: anthropicHeaders(key) }; },
        ids: function (j) { return (j && Array.isArray(j.data) ? j.data : []).filter(function (m) { return m && typeof m.id === 'string'; }).map(function (m) { return m.id; }); }
      }
    }
  };
  var NOTE_KEY = { think: 'note_thinking', temp: 'note_temperature', mct: 'note_max_completion' };
  function errMsg(j) {   // the provider's own sentence, from any of the usual shapes
    if (!j || typeof j !== 'object') return '';
    if (typeof j.error === 'string') return j.error;
    if (j.error && typeof j.error.message === 'string') return j.error.message;
    return typeof j.message === 'string' ? j.message : '';
  }
  /* The message for a failed model call, from the status and the provider's own sentence: {text, reason, fallback, retry, settings}.
     A rejected key (401, 403, or a 400 that talks about the key) never offers the fallback model; everything else does (the button shows only when the model is not already the default). */
  function mapError(status, j, model) {
    var m = cfg.msgs, v = { provider: P.short, status: status, model: model }, msg = errMsg(j);
    if (P.adapter === 'anthropic' && status === 401 && /organi[sz]ation|zero data retention|compliance|CORS requests are not allowed/i.test(msg)) return { text: m.err_anthropic_org };   // wording from the research note (2026-11-16, Anthropic's browser-access page: such organisations get 401 "CORS requests are not allowed for this Organization")
    if (status === 401 || status === 403 || (status === 400 && /api[ _-]?key/i.test(msg))) return { text: fmt(m.err_bad_key, v), settings: true };
    if (status === 404) return { text: fmt(m.err_model_404, v), fallback: true };
    if (status === 429) return { text: fmt(m.err_quota, v), fallback: true };
    if (status >= 500) return { text: fmt(m.err_server, v), fallback: true, retry: true };
    return { text: fmt(m.err_other, v), reason: msg.slice(0, 300), fallback: true };
  }
  function blockedText() { return fmt(P.local ? cfg.msgs.err_blocked_local : cfg.msgs.err_blocked_model, { provider: P.short }); }
  function readJson(r) { return r.json().then(function (j) { return { r: r, j: j }; }, function () { return { r: r, j: null }; }); }

  function draw() {
    if (busy) return;
    var m = cfg.msgs, key = $('live-key').value.trim(), model = $('live-model').value.trim() || P.default_model, q = $('live-q').value.trim().slice(0, cfg.max_q);
    var ad = ADAPTERS[P.adapter], callEpoch = epoch, sv = !key && !P.local ? savedFor(q) : null;   // no key and exactly a stored question: the saved example, not the key prompt
    if (sv) { showSaved(sv); return; }
    hideError(); stage = '';
    if (!key && !P.local) { $('live-result').hidden = true; setGim('confused'); setStatus(m.status_need_key); $('live-error-text').textContent = fmt(m.err_no_key, { provider: P.short }); $('live-error').hidden = false; openSettings(true); return; }   // no key: the settings open with focus in the key field, nothing is sent
    if (!q) { $('live-result').hidden = true; setGim('confused'); setStatus(m.status_error); $('live-error-text').textContent = m.err_no_question; $('live-error').hidden = false; $('live-error').focus(); return; }
    if (tsState === 'failed') { fail(m.err_turnstile_blocked); return; }
    if (tsState === 'loading' || (tsState === 'ready' && !token)) { fail(m.err_turnstile_wait); return; }
    store();
    $('live-settings').open = false;   // the settings fold away once the question is on its way
    busy = true; $('live-go').setAttribute('aria-disabled', 'true'); $('live-form').setAttribute('aria-busy', 'true'); $('live-result').hidden = true;
    begin(q); stage = 'model'; setGim('thinking'); setStatus(m.status_model); showPending(m.status_model);
    var t0 = performance.now(), t1 = 0; pending = null;
    var thinkOn = !!($('live-think-on') && $('live-think-on').checked);   // the visible toggle: On leaves the provider's default thinking alone
    var mk = P.id + '|' + P.svc + '|' + model, rej = Object.assign({}, mem[mk]), o = { think: !rej.think && !thinkOn, temp: !rej.temp, mct: !!rej.mct }, retried = false;   // a setting this provider and model rejected earlier in this tab is left out from the start
    callModel = model; callDefault = P.default_model; modelNotes = [];
    ['think', 'temp', 'mct'].forEach(function (k) { if (rej[k] && !(k === 'think' && thinkOn)) modelNotes.push(NOTE_KEY[k]); });
    function nextRetry(status, msg) {   // one automatic retry per ask, only for a 400 that names a setting; a key error never retries
      if (retried || status !== 400 || /api[ _-]?key/i.test(msg)) return null;
      if (ad.thinking && o.think && /thinking/i.test(msg)) return 'think';
      if (ad.temp && o.temp && /temperature/i.test(msg)) return 'temp';
      if (P.adapter === 'openai' && !o.mct && /max_tokens/i.test(msg) && /max_completion_tokens/i.test(msg)) return 'mct';
      return null;
    }
    function send() {
      var req = ad.build(P, model, key, q, o);
      return timed(req.url, { method: 'POST', credentials: 'omit', referrerPolicy: 'no-referrer', headers: req.headers, body: JSON.stringify(req.body) }, MODEL_MS)
        .then(readJson)
        .then(function (x) {
          if (x.r.ok) { if (retried) mem[mk] = rej; if (ad.thinking && thinkOn) modelNotes.push('note_think_on'); return x; }
          var k = nextRetry(x.r.status, errMsg(x.j));
          if (!k) return x;
          retried = true; rej[k] = true; if (k === 'mct') o.mct = true; else o[k] = false;
          modelNotes.push(NOTE_KEY[k]);
          return send();
        });
    }
    send()
      .then(function (x) {
        if (!x.r.ok) {
          var e = mapError(x.r.status, x.j, model);
          fail(e.text, { fallback: !!e.fallback, retry: !!e.retry, reason: e.reason });
          if (e.settings) openSettings(false);
          return;
        }
        var got = ad.parse(x.j), text = got.text.trim();
    var dsel = document.querySelector('input[name="live-detail"]:checked'); if (dsel && detail() !== 12) modelNotes.push({ key: 'note_detail', vars: { stop: dsel.parentNode.textContent.trim(), asked: String(detail()), boxes: String(boxCount(text)) } });   // only when the default is changed
        if (!text) { fail(m.err_no_reply); return; }
        t1 = performance.now(); stage = 'draw';
        pending = { text: text, model: t1 - t0, usage: got.usage };   // kept so that Try again after a failed drawing request does not ask the provider again
        setGim('thinking'); setStatus(m.status_draw); showPending(m.status_draw);
        return sendDraw(text, t0, t1, got.usage);
      })
      .catch(function (e) {
        drawFailed(e);
      });
  }

  /* ---- "Find the models my key can use": one GET to the selected provider's own list endpoint, with the same key rules ---- */
  function findModels() {
    var ad = ADAPTERS[P.adapter], m = cfg.msgs, key = $('live-key').value.trim(), myEpoch = epoch, note = $('live-find-note'), btn = $('live-find');
    if (!ad.list || (!key && !P.local)) return;
    function say(text) { note.hidden = false; note.textContent = text; setStatus(text); }
    btn.disabled = true; say(m.find_working);
    var req = ad.list.build(P, key);
    timed(req.url, { method: 'GET', credentials: 'omit', referrerPolicy: 'no-referrer', headers: req.headers }, 30000)
      .then(readJson)
      .then(function (x) {
        if (myEpoch !== epoch) return;   // the provider changed while the list was on its way: drop the answer
        if (!x.r.ok) { say(mapError(x.r.status, x.j, '').text); return; }
        var seen = {}, ids = ad.list.ids(x.j).filter(function (id) { if (!/^[A-Za-z0-9._:\/-]{1,80}$/.test(id) || seen[id]) return false; seen[id] = 1; return true; }).sort();
        if (!ids.length) { say(m.find_none); return; }
        var shown = ids.slice(0, 60);
        suggest = shown; setModel($('live-model').value.trim() || P.default_model);
        say(ids.length > shown.length ? fmt(m.find_capped, { count: ids.length, shown: shown.length }) : fmt(m.find_done, { count: shown.length }));
      })
      .catch(function (e) { if (myEpoch === epoch) say(isAbort(e) ? m.err_timeout : blockedText()); })
      .then(function () { if (myEpoch === epoch) syncFind(); });
  }

  function drawHost() { try { return new URL(cfg.draw_url).host; } catch (e) { return cfg.draw_url; } }
  function drawFailed(e) {
    var m = cfg.msgs, inDraw = stage === 'draw' && pending;   // a failure after the provider replied keeps the model's text on screen
    var text = isAbort(e) && !inDraw ? m.err_timeout : (inDraw ? (isAbort(e) ? m.err_timeout : fmt(m.err_blocked_draw, { provider: P.short, host: drawHost() }) + (cfg.preview_note ? ' ' + cfg.preview_note : '')) : blockedText());
    fail(text, { retry: true, fallback: !inDraw, modelText: inDraw ? pending.text : undefined });   // a network failure at the model stage also offers the default model
  }
  function sendDraw(text, t0, t1, usage) {   // the one drawing request: only the model's text goes to the drawing service
    var headers = { 'Content-Type': 'application/json' };
    if (owner) headers['X-Owner-Key'] = owner;
    else if (token) headers['X-Turnstile-Token'] = token;
    return timed(cfg.draw_url, { method: 'POST', mode: 'cors', credentials: 'omit', referrerPolicy: 'no-referrer', headers: headers, body: JSON.stringify({ reply: text }) }, DRAW_MS)
      .then(function (r) { return r.json().then(function (j) { return { r: r, j: j }; }, function () { return { r: r, j: null }; }); })
      .then(function (d) { handleDraw(d.r, d.j, text, t0, t1, usage); });
  }
  function redraw() {   // Try again after a failed drawing request: redo the drawing from the SAME model text, no new Google call
    if (busy) return;
    var m = cfg.msgs; hideError(); stage = 'draw';
    if (tsState === 'failed') { fail(m.err_turnstile_blocked, { retry: true, modelText: pending.text }); return; }
    if (tsState === 'loading' || (tsState === 'ready' && !token)) { fail(m.err_turnstile_wait, { retry: true, modelText: pending.text }); return; }
    busy = true; $('live-go').setAttribute('aria-disabled', 'true'); $('live-form').setAttribute('aria-busy', 'true'); $('live-result').hidden = true;
    setGim('thinking'); setStatus(m.status_draw); showPending(m.status_draw);
    var t1 = performance.now(), t0 = t1 - pending.model;   // the first model call time is kept
    sendDraw(pending.text, t0, t1, pending.usage).catch(drawFailed);
  }

  /* ---- the latency ledger: wall times measured in this browser; the Worker's total is shown only as a floor ---- */
  function ms(m, v) { return fmt(m.value_ms, { value: Math.round(v).toLocaleString('en-GB') }); }
  function num(v) { return typeof v === 'number' && isFinite(v) && v >= 0 ? v : null; }
  function tokensText(m, u) {
    var pin = u ? num(u.in) : null, pout = u ? num(u.out) : null, think = u ? num(u.think) : null;   // u is the adapter's {in, out, think}, or null when the provider reported none
    if (pin === null && pout === null) return m.not_reported;
    var s = fmt(m.tokens_value, { in: pin === null ? m.not_reported : pin.toLocaleString('en-GB'), out: pout === null ? m.not_reported : pout.toLocaleString('en-GB') });
    return think ? s + ', ' + fmt(m.tokens_think, { think: think.toLocaleString('en-GB') }) : s;
  }
  function fillLedger(m, usage, model, draw, worker, bytes) {
    $('live-ledger-empty').hidden = true; $('live-ledger-body').hidden = false;
    $('live-t-model').textContent = ms(m, model);
    $('live-t-tokens').textContent = tokensText(m, usage);
    $('live-t-draw').textContent = ms(m, draw);
    $('live-t-worker').textContent = worker === null ? m.not_reported : ms(m, worker);
    $('live-t-net').textContent = worker === null ? m.not_reported : ms(m, Math.max(0, draw - worker));
    $('live-t-total').textContent = ms(m, model + draw);
    $('live-t-size').textContent = fmt(m.value_bytes, { bytes: bytes.toLocaleString('en-GB') });
  }
  function fillNotes(m, reps) {
    var ul = $('live-notes'); ul.textContent = '';
    $('live-notes-intro').hidden = !reps.length; var mn = $('live-notes-model'); mn.textContent = ''; mn.hidden = !modelNotes.length;
    modelNotes.forEach(function (k) { var li = document.createElement('li'); li.textContent = typeof k === 'string' ? m[k] : fmt(m[k.key], k.vars); mn.appendChild(li); });
    if (!reps.length && modelNotes.length) return;
    if (!reps.length) { var li0 = document.createElement('li'); li0.textContent = m.notes_none; ul.appendChild(li0); return; }
    reps.forEach(function (s) { var li = document.createElement('li'); li.textContent = s.slice(0, 300); ul.appendChild(li); });
  }
  function diagramText(reply) {   // the model's reply without its INTRO line (the intro is shown above the picture); the Worker refuses replies over 8 KB, so the cap only guards the page
    var lines = reply.split('\n');
    if (lines.length > 1 && /^\s*INTRO:/i.test(lines[0])) lines.shift();
    return lines.join('\n').trim().slice(0, 8192);
  }

  /* ---- copy the diagram text: the clipboard API where the page allows it, else select it and use the older copy command (same pattern as kit.js) ---- */
  function copyText() {
    var pre = $('live-mermaid'), m = cfg.msgs, tick = $('live-copy-tick');
    function ok() { tick.textContent = m.copied; clearTimeout(copyText.t); copyText.t = setTimeout(function () { tick.textContent = ''; }, 2500); }
    function sel() { var r = document.createRange(); r.selectNodeContents(pre); var s = window.getSelection(); s.removeAllRanges(); s.addRange(r); }
    function blocked() { sel(); tick.textContent = m.copy_blocked; }
    if (navigator.clipboard && window.isSecureContext) { navigator.clipboard.writeText(pre.textContent).then(ok, blocked); return; }
    sel(); var done = false;
    try { done = document.execCommand('copy'); } catch (e) {}
    if (done) ok(); else blocked();
  }

  /* ---- the Latency ledger panel (opens on the left of the window, like the explain app) ---- */
  function setLedger(on, focusBack, opener, quiet) {   // quiet: open without moving focus (the ?ledger=open start)
    if (on && opener) ledgerOpener = opener;
    $('live-ledger-panel').hidden = !on;
    ['live-ledger-btn', 'live-strip-btn'].forEach(function (id) { var b = $(id); if (b) b.setAttribute('aria-expanded', on ? 'true' : 'false'); });
    $('live-app').classList.toggle('ledger-on', on);
    if (on && !quiet) $('live-ledger-close').focus();
    else if (!on && focusBack) { var o = ledgerOpener && ledgerOpener.offsetParent !== null ? ledgerOpener : $('live-ledger-btn'); o.focus(); }
  }
  /* ---- the live page only: which form the ledger takes (the left panel, or the compact strip with a bottom sheet) and the strip's figures ---- */
  function lform() {
    if (!LP) return 'panel';
    if (LP.ledger === 'strip' || LP.ledger === 'panel') return LP.ledger;
    return LP.portrait || appW() < 700 ? 'strip' : 'panel';
  }
  function syncForm() {
    var f = lform(), s = $('live-strip'); $('live-app').setAttribute('data-lform', f);
    if (s) s.hidden = !(f === 'strip' && LP.ledger !== 'off' && hasResult);
    var hh = $('live-hint'); if (hh) hh.hidden = hasResult;   // once a result is showing the line under the bar has done its job; the diagram gets the height back
  }
  function stripTime(v) { return v < 1000 ? fmt(cfg.msgs.value_ms, { value: Math.round(v).toLocaleString('en-GB') }) : secs(v); }   // seconds with one decimal, milliseconds under one second
  function renderStrip() {
    var ul = $('live-strip-figs'); if (!ul || !(lastLedger || lastSaved)) return;
    if (lastSaved) { var S = cfg.lp, mm = cfg.msgs; stripFill(ul, [[S.strip_model, mm.not_run], [S.strip_draw, mm.not_run_saved], [S.strip_tokens, mm.not_run, 'fig-tokens'], [S.strip_picture, (savedBytes(lastSaved) / 1024).toFixed(1) + ' KB']]); return; }
    var L = cfg.lp, u = lastLedger.usage, pin = u ? num(u.in) : null, pout = u ? num(u.out) : null, figs = [[L.strip_model, stripTime(lastLedger.model)], [L.strip_draw, stripTime(lastLedger.draw)], [L.strip_total, stripTime(lastLedger.total)]];
    if (pin !== null || pout !== null) figs.push([L.strip_tokens, fmt(L.tokens_text, { in: pin === null ? cfg.msgs.not_reported : pin.toLocaleString('en-GB'), out: pout === null ? cfg.msgs.not_reported : pout.toLocaleString('en-GB') }), 'fig-tokens']);
    figs.push([L.strip_picture, (lastLedger.bytes / 1024).toFixed(1) + ' KB']);
    stripFill(ul, figs);
  }
  function stripFill(ul, figs) {
    ul.textContent = '';
    figs.forEach(function (f) {
      var li = document.createElement('li');
      if (f[2]) li.className = f[2];
      var k = document.createElement('span'), v = document.createElement('span'); k.className = 'fig-k'; v.className = 'fig-v'; k.textContent = f[0]; v.textContent = f[1];
      li.appendChild(k); li.appendChild(document.createTextNode(' ')); li.appendChild(v); ul.appendChild(li);
    });
  }
  /* ---- the diagram: Fit (default) scales it to the visible area with CSS; Actual size shows the natural pixels in a scrollable box ---- */
  var stepsAuto = false, sizeMode = 'fit', sizeChoice = '', minFont = 14, lastCw = 0, lastCh = 0, autoPending = false, autoReadable = false, PHONE_PX = 700;   // the two label thresholds (fit_min, readable) come from the manifest: try_it.diagram_scale
  function appW() { var a = $('live-app'); return a && a.clientWidth ? a.clientWidth : window.innerWidth; }   // the app's own width: the window in the dialog, the stage on the live page
  function colW() { var c = $('live-app').querySelector('.app-col'); return c && c.clientWidth ? c.clientWidth : window.innerWidth; }
  function isPhone() { return appW() < PHONE_PX; }
  function applySize() {   // fit: CSS scales the picture to the free area; readable: at least scale.readable px per label (or the width of the box if that is larger), scrollable; actual: natural pixels, scrollable
    var fig = $('live-fig'), img = $('live-img'), nw = img.naturalWidth, nh = img.naturalHeight, scroll = sizeMode !== 'fit';
    ['live-sz-fit', 'live-sz-readable', 'live-sz-actual'].forEach(function (id) { $(id).setAttribute('aria-pressed', id === 'live-sz-' + (sizeMode === 'fit' ? 'fit' : sizeMode === 'readable' ? 'readable' : 'actual') ? 'true' : 'false'); });
    fig.classList.toggle('scroll', scroll); fig.classList.toggle('actual', sizeMode === 'actual');
    if (scroll) { fig.setAttribute('tabindex', '0'); fig.setAttribute('role', 'region'); fig.setAttribute('aria-label', cfg.ui.fig_region); }
    else { fig.removeAttribute('tabindex'); fig.removeAttribute('role'); fig.removeAttribute('aria-label'); }
    $('live-fig-hint').hidden = !(scroll && (isPhone() || autoReadable));
    img.style.width = ''; img.style.height = '';
    if (sizeMode === 'readable' && nw > 0) {
      var s = Math.min(1, Math.max(cfg.scale.readable / minFont, Math.min(fig.clientWidth / nw, fig.clientHeight / nh)));   // never below the readable scale; larger only up to the scale at which the whole picture fits the box
      lastCw = fig.clientWidth; lastCh = fig.clientHeight; img.style.width = Math.round(nw * s) + 'px'; img.style.height = Math.round(nh * s) + 'px';
    }
  }
  function resetView() {   // the diagram region and the conversation area go back to the top left; the bar and the bubble are fixed and stay
    var fig = $('live-fig'), th = $('live-thread'); fig.scrollLeft = 0; fig.scrollTop = 0; if (th) th.scrollTop = 0;
  }
  function setSize(mode, chosen) { sizeMode = mode; if (chosen) { sizeChoice = mode; autoReadable = false; } applySize(); resetView(); $('live-result').scrollIntoView({ block: 'nearest' }); }
  function autoSize() {   // no choice made yet: Fit when the labels would be at least scale.fit_min px under Fit, else Readable; phones always start Readable
    var fig = $('live-fig'), img = $('live-img'), nw = img.naturalWidth, nh = img.naturalHeight;
    autoPending = false; autoReadable = false;
    if (isPhone()) { sizeMode = 'readable'; return; }
    var s = Math.min(1, fig.clientWidth / nw, fig.clientHeight / nh);
    if (minFont * s >= cfg.scale.fit_min) sizeMode = 'fit'; else { sizeMode = 'readable'; autoReadable = true; }
  }
  function noteFonts(uri) {   // the smallest label font in the drawing, read from the SVG itself
    var f = 14;
    try {
      var svg = atob(uri.split(',')[1]), re = /font-size[=:]\s*["']?([0-9.]+)/g, m, min = Infinity;
      while ((m = re.exec(svg))) { var v = parseFloat(m[1]); if (v > 0 && v < min) min = v; }
      if (isFinite(min)) f = min;
    } catch (e) {}
    minFont = f;
  }
  function layoutResult() {   // from 1000 px wide the steps are a column beside the diagram, for any diagram shape (opened for it, closed again afterwards); narrower, they are a button on the toolbar row
    var r = $('live-result'), sd = $('live-steps-d');
    if (r.hidden) return;
    var side = colW() >= 1000;   // the column the result sits in: the whole app, less the ledger panel while that pushes the content aside
    r.setAttribute('data-side', side ? '1' : '0');
    if (side && !sd.open) { sd.open = true; stepsAuto = true; }
    else if (!side && stepsAuto) { sd.open = false; stepsAuto = false; }
  }
  function imgReady() { layoutResult(); if (autoPending) autoSize(); applySize(); resetView(); }   // the picture is loaded and its box is visible: choose the size and lay the result out
  function setPillModel() { $('live-pill-model').textContent = $('live-model').value.trim() || P.default_model; }

  /* ---- saved examples: the page's three stored examples, shown inside the app with no request of any kind and no invented timing ---- */
  function savedFor(q) {   // a stored question typed exactly (trimmed, any case) is the saved example
    var s = (q || '').trim().toLowerCase();
    for (var i = 0; i < cfg.saved.length; i++) if (cfg.saved[i].question.trim().toLowerCase() === s) return cfg.saved[i];
    return null;
  }
  function reducedMotion() { return !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches); }
  function savedBytes(s) { return reducedMotion() ? s.still_bytes : s.bytes; }   // the size of the picture that is shown
  function resultPills(live) {   // the LIVE pill appears only for a real call; a saved example has its own label and the header pill steps aside
    var pill = document.querySelector('#live-result .live-result-head .pill'), head = document.querySelector('.app-pill');
    pill.textContent = live ? cfg.msgs.result_pill : cfg.msgs.saved_pill; pill.setAttribute('data-state', live ? 'live' : 'stored');
    if (head) head.hidden = !live;
    $('live-ledger-body').classList.toggle('ledger-saved', !live);
    if (live) lastSaved = null;
  }
  function showSaved(s) {   // only DOM work: no fetch, and no Turnstile reset (a reset would ask Cloudflare for a new check)
    var m = cfg.msgs, img = $('live-img'), src = reducedMotion() ? s.still : s.svg;
    hideError(); stage = ''; pending = null;
    $('live-q').value = s.question; begin(s.question); $('live-pending').hidden = true;
    minFont = 14; $('live-steps-d').open = false; stepsAuto = false; $('live-how').open = false;
    if (sizeChoice) sizeMode = sizeChoice; else { sizeMode = 'fit'; autoPending = true; }
    img.alt = s.alt; $('live-intro').textContent = s.intro; $('live-done').textContent = '';
    var ol = $('live-steps'); ol.textContent = ''; s.steps.forEach(function (x) { var li = document.createElement('li'); li.textContent = x; ol.appendChild(li); });
    $('live-mermaid').textContent = s.mermaid; $('live-copy-tick').textContent = '';
    $('live-ledger-empty').hidden = true; $('live-ledger-body').hidden = false;   // the ledger: only rows that are true, nothing timed
    $('live-t-model').textContent = m.not_run; $('live-t-tokens').textContent = m.not_run; $('live-t-draw').textContent = m.not_run_saved;
    $('live-t-size').textContent = fmt(m.value_bytes, { bytes: savedBytes(s).toLocaleString('en-GB') });
    $('live-ledger').textContent = m.saved_sentence; $('live-notes-intro').hidden = true; $('live-notes').textContent = ''; $('live-notes-model').hidden = true;
    lastSaved = s; lastLedger = null; resultPills(false); renderStrip();
    $('live-result').hidden = false; hasResult = true; syncForm(); resetView(); layoutResult();   // visible before the picture is set, so its box has a size when it loads
    var same = img.getAttribute('src') === src; img.src = src;
    if (same && img.complete && img.naturalWidth) imgReady();   // the same picture again fires no load event
    if (LP && LP.ledger === 'open' && !ledgerAutoDone) { ledgerAutoDone = true; setLedger(true, false, null, true); }
    setGim('happy'); setStatus(m.saved_bubble);
    $('live-result-h').focus();
  }

  function handleDraw(r, j, text, t0, t1, usage) {
    var m = cfg.msgs, code = j && typeof j.code === 'string' ? j.code : '';
    if (!r.ok || !j || j.ok === false) {
      var reason = j && typeof j.error === 'string' ? j.error.slice(0, 300) : '';
      switch (code) {
        case 'diagram': case 'bad_json': return fail(m.err_unparseable, { modelText: text, reason: reason ? fmt(m.err_unparseable_reason, { reason: reason }) : '' });
        case 'empty_reply': return fail(m.err_no_reply);
        case 'guard': return fail(m.err_guard, { modelText: text });
        case 'too_large': return fail(m.err_too_large, { modelText: text });
        case 'daily': return fail(m.err_daily);
        case 'rate': return fail(m.err_rate);
        case 'off': return fail(m.err_off);
        case 'busy': return fail(m.err_busy);
        case 'turnstile': return fail(m.err_turnstile);
        case 'turnstile_unavailable': return fail(m.err_turnstile_unavailable);
        case 'origin': return fail(m.err_origin);
        default: return fail(fmt(m.err_draw_other, { status: r.status, code: code || 'none' }));
      }
    }
    var uri = j.svg_data_uri;
    if (typeof uri !== 'string' || uri.indexOf('data:image/svg+xml;base64,') !== 0 || uri.length > MAX_SVG) return fail(m.err_bad_svg);
    var t2 = performance.now(), L = j.ledger && typeof j.ledger === 'object' ? j.ledger : {};
    $('live-img').alt = typeof j.alt === 'string' ? j.alt.slice(0, 600) : '';
    $('live-steps-d').open = false; stepsAuto = false; noteFonts(uri);
    if (sizeChoice) sizeMode = sizeChoice; else { sizeMode = 'fit'; autoPending = true; }   // the visitor's last choice stays for the visit (memory only); until then the size is picked automatically once the picture has loaded (autoSize)
    $('live-img').src = uri;
    $('live-intro').textContent = typeof j.intro === 'string' ? j.intro.slice(0, 400) : '';
    var ol = $('live-steps'); ol.textContent = '';
    // the drawing service numbers its steps itself, so the leading number is cut: the <ol> numbers them
    (Array.isArray(j.steps) ? j.steps.slice(0, 40) : []).forEach(function (s) { if (typeof s !== 'string') return; var li = document.createElement('li'); li.textContent = s.slice(0, 300).replace(/^\s*\d+[.)]\s+/, ''); ol.appendChild(li); });
    var bytes = typeof L.bytes === 'number' ? L.bytes : uri.length;   // the Worker's own stage times read 0.0 on Cloudflare (the clock stands still during computation), so they are never shown; only its total, labelled a floor
    $('live-done').textContent = fmt(m.result_done, { total: secs(t2 - t0) });
    $('live-ledger').textContent = fmt(m.ledger, { model: secs(t1 - t0), draw: secs(t2 - t1), total: secs(t2 - t0), bytes: bytes.toLocaleString('en-GB') });
    fillLedger(m, usage, t1 - t0, t2 - t1, typeof L.total_ms === 'number' ? L.total_ms : null, bytes);
    lastSaved = null; lastLedger = { model: t1 - t0, draw: t2 - t1, total: t2 - t0, usage: usage, bytes: bytes }; renderStrip();
    fillNotes(m, Array.isArray(j.repairs) ? j.repairs.filter(function (x) { return typeof x === 'string'; }).slice(0, 10) : []);
    $('live-mermaid').textContent = diagramText(text);
    $('live-copy-tick').textContent = '';
    $('live-pending').hidden = true;
    $('live-how').open = false;
    resultPills(true); $('live-result').hidden = false; hasResult = true; syncForm();
    resetView();
    layoutResult();
    if (LP && LP.ledger === 'open' && !ledgerAutoDone) { ledgerAutoDone = true; setLedger(true, false, null, true); }
    setGim('happy'); setStatus(m.status_done);
    done();
    $('live-result-h').focus();
  }

  function start(opts) {
    if (cfg) return;   // opened more than once: set up once
    cfg = JSON.parse($('live-config').textContent);
    owner = (opts && opts.owner) || '';
    LP = opts && opts.page ? { ledger: opts.page.ledger || '', portrait: !!opts.page.portrait } : null;   // the standalone live page's options; the dialog passes none
    syncForm();
    setGim('idle');
    P = current(); renderProvider(); syncThink();
    try { var k = sessionStorage.getItem(keySlot()); if (k) { $('live-key').value = k; $('live-remember').checked = true; syncFind(); } } catch (e) {}
    $('live-provider').addEventListener('change', onProviderChange);
    $('live-service').addEventListener('change', onProviderChange);
    $('live-find').addEventListener('click', findModels);
    $('live-model-pick').addEventListener('change', function () {   // Other model id shows the text field (focus stays on the dropdown); a listed model fills the value
      var v = $('live-model-pick').value;
      if (v === '__other__') $('live-model-other').hidden = false; else { $('live-model').value = v; $('live-model-other').hidden = true; }
      mem = {}; setPillModel(); syncFallback();
    });
    $('live-form').addEventListener('submit', function (ev) { ev.preventDefault(); draw(); });
    $('live-clear').addEventListener('click', clearKey);
    $('live-retry').addEventListener('click', function () { if (stage === 'draw' && pending) redraw(); else { hideError(); draw(); } });
    $('live-remember').addEventListener('change', store);
    $('live-key').addEventListener('input', function () { if ($('live-remember').checked) store(); syncFind(); });
    document.querySelectorAll('.live-chip').forEach(function (c) {   // a chip shows its saved example at once, with or without a key: no request of any kind
      c.addEventListener('click', function () {
        var s = null; cfg.saved.forEach(function (x) { if (x.id === c.getAttribute('data-saved')) s = x; });
        if (s && !busy) showSaved(s);
      });
    });
    $('live-q').addEventListener('keydown', function (ev) { if (ev.key === 'Enter' && !ev.shiftKey && !ev.isComposing) { ev.preventDefault(); draw(); } });
    $('live-fallback').addEventListener('click', function () {
      mem = {}; setModel(P.default_model); hideError(); setGim('idle'); setStatus(cfg.msgs.status_model_changed); $('live-go').focus();
    });
    $('live-copy').addEventListener('click', copyText);
    $('live-ledger-btn').addEventListener('click', function () { setLedger($('live-ledger-panel').hidden, true, $('live-ledger-btn')); });
    if ($('live-strip-btn')) $('live-strip-btn').addEventListener('click', function () { setLedger($('live-ledger-panel').hidden, true, $('live-strip-btn')); });
    $('live-ledger-close').addEventListener('click', function () { setLedger(false, true); });
    [['live-sz-fit', 'fit'], ['live-sz-readable', 'readable'], ['live-sz-actual', 'actual']].forEach(function (x) { $(x[0]).addEventListener('click', function () { setSize(x[1], true); }); });
    $('live-img').addEventListener('load', imgReady);
    if (typeof ResizeObserver === 'function') new ResizeObserver(function () { if (sizeMode === 'readable' && ($('live-fig').clientWidth !== lastCw || $('live-fig').clientHeight !== lastCh)) applySize(); }).observe($('live-fig'));
    window.addEventListener('resize', function () { applySize(); layoutResult(); syncForm(); });
    if (typeof ResizeObserver === 'function') new ResizeObserver(function () { layoutResult(); }).observe($('live-app').querySelector('.app-col'));
    document.addEventListener('keydown', function (ev) {   // Escape closes the ledger panel first; kit.js closes the dialog on the next press
      if (ev.key !== 'Escape') return;
      if (!$('live-ledger-panel').hidden) { ev.preventDefault(); setLedger(false, true); }
    });
    $('live-model').addEventListener('input', function () { mem = {}; setPillModel(); syncFallback(); });
    setPillModel();
    setupTurnstile();
  }
  window.A2UILive = { start: start };
})();
