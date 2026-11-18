/* Demo kit prototype: plain JavaScript, no libraries. All text is already in the HTML; this only adds behaviour.
   - copy buttons (hidden until this script runs, so there are no dead buttons) with one shared status region
   - copy is disabled while a box still holds a placeholder, so nobody pastes it
   - a "service URL" field that fills the agent card, then enables its copy button
   - details[name=host]: one open at a time (fallback for browsers without the name attribute), remembered in the URL hash and localStorage
   - the demo screen's example chips (first view and developer section), route switch (?route=custom preselects the custom route) and replay button
   - the Try it dialog: opened by the .try-open button, #try or #owner=KEY; the page behind is inert, focus is trapped, Escape and Close return focus to the opener */
(function () {
  var selfScript = document.currentScript;
  document.documentElement.classList.add('js');
  var status = document.getElementById('kit-status');
  function say(msg) { status.textContent = ''; setTimeout(function () { status.textContent = msg; }, 60); }

  /* ---- copy buttons ---- */
  document.querySelectorAll('.copy-btn').forEach(function (b) {
    var box = document.getElementById(b.dataset.copy), tick = b.parentNode.querySelector('.tick'), name = b.dataset.name;
    function ready() { return !box.hasAttribute('data-placeholder') && box.value.trim() !== ''; }
    b.refresh = function () { b.disabled = !ready(); };
    b.refresh();
    b.addEventListener('click', function () {
      if (!ready()) return;
      function ok() { tick.textContent = 'Copied'; say(name + ' copied to clipboard.'); clearTimeout(b._t); b._t = setTimeout(function () { tick.textContent = ''; }, 2500); }
      function fail() { box.focus(); box.select(); say('Copy was blocked. The ' + name + ' is selected: press Control+C, or Command+C on a Mac.'); }
      if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(box.value).then(ok, fail);
      else {   // plain http or an old browser: select the box and use the older copy command, and only say "blocked" if that fails too
        box.focus(); box.select(); var done = false;
        try { done = document.execCommand('copy'); } catch (e) {}
        if (done) ok(); else fail();
      }
    });
  });

  /* ---- agent card: fill in the reader's own service URL ---- */
  var svc = document.getElementById('svc-url'), card = document.getElementById('c-card');
  if (svc && card) {
    var tpl = card.getAttribute('data-template');
    var btn = document.querySelector('.copy-btn[data-copy="c-card"]');
    function fill() {
      var v = svc.value.trim();
      if (/^https:\/\/[^\s"\\]+$/.test(v)) { card.value = tpl.replace('https://YOUR-SERVICE-URL', v.replace(/\/$/, '')); card.removeAttribute('data-placeholder'); }
      else { card.value = tpl; card.setAttribute('data-placeholder', ''); }
      btn.refresh();
    }
    svc.addEventListener('input', fill); fill();
  }

  /* ---- host sections ---- */
  var hosts = [].slice.call(document.querySelectorAll('details[name="host"]')), native = 'name' in HTMLDetailsElement.prototype;
  function openHost(id) { var d = document.getElementById(id); if (d && hosts.indexOf(d) > -1) { d.open = true; return true; } return false; }
  if (!(location.hash && openHost(location.hash.slice(1)))) { try { var s = localStorage.getItem('a2ui-kit-host'); if (s) openHost(s); } catch (e) {} }
  hosts.forEach(function (d) {
    d.addEventListener('toggle', function () {
      if (!d.open) return;
      if (!native) hosts.forEach(function (o) { if (o !== d) o.open = false; });
      try { localStorage.setItem('a2ui-kit-host', d.id); } catch (e) {}
      history.replaceState(null, '', '#' + d.id);
    });
  });

  /* ---- demo page: replay the drawing (the animated SVG plays once when it loads, so a new URL plays it again) ---- */
  var rp = document.getElementById('replay');
  if (rp) rp.addEventListener('click', function () { var im = document.getElementById('demo-img'); im.src = im.src.split('?')[0] + '?' + Date.now(); say('The drawing is playing again.'); });

  /* ---- demo screen: examples, routes and the replay button. Everything the reader sees is already in the HTML; this only switches. ---- */
  var reduced = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var dd = document.getElementById('demo-data');
  if (dd) {
    var data = JSON.parse(dd.textContent), keys = Object.keys(data), cur = keys[0];
    var img = document.getElementById('demo-img'), src = document.getElementById('demo-src'), frame = document.getElementById('atom-frame');
    var steps = document.getElementById('steps'), mer = document.getElementById('mermaid'), intro = document.getElementById('ex-intro');
    var hImg = document.getElementById('hero-img'), hSrc = document.getElementById('hero-src'), hSteps = document.getElementById('hero-steps'), hIntro = document.getElementById('hero-intro');
    var hQ = document.getElementById('hero-q'), hCode = document.getElementById('hero-code');
    var basic = document.getElementById('route-basic'), custom = document.getElementById('route-custom');
    var radios = [].slice.call(document.querySelectorAll('input[name="route"]'));
    function route() { var r = radios.filter(function (x) { return x.checked; })[0]; return r ? r.value : 'basic'; }
    function codeLines(m) { var ls = m.trim().split('\n'); return ls.slice(0, 6).join('\n') + (ls.length > 6 ? '\n...' : ''); }
    function listInto(ol, items) { if (!ol) return; ol.innerHTML = ''; items.forEach(function (s) { var li = document.createElement('li'); li.textContent = s; ol.appendChild(li); }); }
    function freshHero(d) {   // a new <img> element with a new address, so the finite animation plays from the start
      var n = document.createElement('img'); n.id = 'hero-img'; n.alt = d.alt; n.width = 1004; n.height = 341; n.src = d.svg + '?' + Date.now();
      hImg.replaceWith(n); hImg = n;
    }
    var howData = (function () { var e = document.getElementById('how-data'); return e ? JSON.parse(e.textContent) : null; })(), howStatus = document.getElementById('how-status');
    function fillHow(id) {   // the four steps follow the chosen example: text only, from the generated data
      if (!howData) return; var h = howData[id];
      [].forEach.call(document.querySelectorAll('.step-d[data-k]'), function (el) {
        var k = el.getAttribute('data-k');
        if (k === 'model') { el.querySelector('.step-code').textContent = h.code; el.querySelector('.step-more').textContent = h.more; } else el.textContent = h[k];
      });
    }
    function playSteps() {   // the 4-step highlight, once (CSS for a and b; the stage counter for c); reduced motion: nothing moves, all four stay shown
      if (reduced) return;
      [].forEach.call(document.querySelectorAll('.steps-strip, .steps-line'), function (el) { el.classList.remove('play'); void el.offsetWidth; el.classList.add('play'); });
      var sy = document.querySelector('.story');
      if (sy) { sy.setAttribute('data-stage', '0'); [1, 2, 3, 4].forEach(function (n) { setTimeout(function () { sy.setAttribute('data-stage', String(n)); }, n * 900); }); }
    }
    function heroVisible() { var r = hImg.getBoundingClientRect(); return r.top >= 0 && r.bottom <= window.innerHeight; }
    function bringIntoView(wasVisible) {   // a diagram that was fully visible is never scrolled; otherwise the block holding the diagram and the strip is brought into view (the diagram alone when the block is taller than the window). The focus is never moved.
      var blk = document.querySelector('.fv-how, .fv-show, .story');
      if (!blk || !hImg || wasVisible) return;
      var target = blk.getBoundingClientRect().height > window.innerHeight ? hImg : blk;
      target.scrollIntoView({ block: 'nearest', behavior: reduced ? 'auto' : 'smooth' });
    }
    function show() {
      var d = data[cur];
      src.srcset = d.still; img.src = d.svg; img.alt = d.alt;
      listInto(steps, d.steps); mer.textContent = d.mermaid; intro.textContent = d.intro;
      if (hImg) { hSrc.srcset = d.still; freshHero(d); listInto(hSteps, d.steps); if (hIntro) hIntro.textContent = d.intro; if (hQ) hQ.textContent = d.question; if (hCode) hCode.textContent = codeLines(d.mermaid); }
      var r = route(); basic.hidden = r !== 'basic'; custom.hidden = r !== 'custom';
      if (r === 'custom' && frame.getAttribute('src') !== d.atom) frame.setAttribute('src', d.atom);
    }
    document.querySelectorAll('.chip[data-ex]').forEach(function (c) {
      c.addEventListener('click', function () {
        cur = c.dataset.ex;
        document.querySelectorAll('.chip[data-ex]').forEach(function (o) { o.setAttribute('aria-pressed', o.dataset.ex === cur ? 'true' : 'false'); });
        var wasVisible = hImg ? heroVisible() : true;
        show(); fillHow(cur); playSteps(); bringIntoView(wasVisible);
        if (howStatus) { howStatus.textContent = ''; setTimeout(function () { howStatus.textContent = howData ? howData[cur].announce : ''; }, 60); }
        else say('Showing the example: ' + data[cur].title + '.');
      });
    });
    function replayHero() { if (hImg) hImg.src = hImg.src.split('?')[0] + '?' + Date.now(); }   // the animated SVG plays once when it loads, so a new URL plays it again
    /* layout A: the four steps play through (CSS, about 4 s), then the diagram plays again so the strip ends on it */
    if (document.querySelector('.steps-strip') && !reduced) setTimeout(replayHero, 3800);
    /* layout C: each step that scrolls into view adds a stage to the panel beside it (question, lines, drawing); without the observer, or with reduced motion, every stage is shown */
    var story = document.querySelector('.story');
    if (story && !reduced && 'IntersectionObserver' in window) {
      var stage = 0; story.setAttribute('data-stage', '0');
      var io = new IntersectionObserver(function (es) {
        es.forEach(function (en) {
          var n = parseInt(en.target.getAttribute('data-step'), 10);
          if (en.isIntersecting && n > stage) { stage = n; story.setAttribute('data-stage', String(stage)); if (n === 3) replayHero(); }
        });
      }, { rootMargin: '0px 0px -30% 0px', threshold: 0.3 });
      [].forEach.call(story.querySelectorAll('.story-step'), function (li) { io.observe(li); });
    }
    radios.forEach(function (r) {
      r.addEventListener('change', function () {
        show();
        try { history.replaceState(null, '', route() === 'custom' ? '?route=custom' : location.pathname); } catch (e) {}
        say(route() === 'basic' ? 'Showing it as a Basic catalog Image.' : 'Showing it as a custom catalog atom.');
      });
    });
    function fit() {   // fit the frame to the drawing (the frame runs no script, so allow-same-origin is safe); a hidden frame measures 0, so this also runs when the custom route is shown
      try { var b = frame.contentDocument.body, r = b.getBoundingClientRect(), h = Math.ceil(r.height + r.top); if (h > 80) frame.style.height = h + 'px'; } catch (e) {}
    }
    frame.addEventListener('load', fit);
    radios.forEach(function (r) { r.addEventListener('change', fit); });
    var want = /[?&]route=custom(&|$)/.test(location.search);
    if (want) { radios.forEach(function (r) { r.checked = r.value === 'custom'; }); var dr = document.getElementById('dev-routes'); if (dr) dr.open = true; }
    var dr2 = document.getElementById('dev-routes'); if (dr2) dr2.addEventListener('toggle', function () { if (dr2.open) fit(); });
    show();
  }

  /* ---- the Try it dialog: nothing runs and nothing is fetched until the reader opens it ---- */
  var ov = document.getElementById('try');
  if (ov) {
    /* The owner key arrives as a URL fragment (#owner=KEY). Read it once into this closure, remove it from the address bar at once, never show or store it.
       It is handed to the live script only when the dialog is opened. #try opens the dialog; both together (#try&owner=KEY or #owner=KEY&try) work. */
    var ownerKey = '', opener = null, isOpen = false, loaded = false, inerted = [], savedY = 0;
    var hash = location.hash, om = /(?:^#|&)owner=([^&]*)/.exec(hash), wantTry = /(?:^#|&)try(?:&|$)/.test(hash);
    if (om) {
      try { ownerKey = decodeURIComponent(om[1]); } catch (e) { ownerKey = om[1]; }
      try { history.replaceState(null, '', location.pathname + location.search); } catch (e) {}
    }
    function start() {
      if (loaded) return; loaded = true;
      var s = document.createElement('script');
      s.src = selfScript && selfScript.src ? selfScript.src.replace(/demo-kit\.js(\?.*)?$/, 'demo-live.js') : '/bc-assets/demo-live.js';
      s.onload = function () { window.A2UILive.start({ owner: ownerKey }); ownerKey = ''; };
      s.onerror = function () { loaded = false; say('The live panel script could not be loaded.'); };
      document.head.appendChild(s);
    }
    function setInert(on) {   // while the dialog is open the rest of the page is inert: not focusable, not clickable, hidden from assistive technology
      if (!on) { inerted.forEach(function (c) { c.inert = false; }); inerted = []; return; }
      var n = ov;
      while (n && n.parentNode && n !== document.body) {
        var p = n.parentNode;
        [].forEach.call(p.children, function (c) { if (c !== n && !c.inert && c.tagName !== 'SCRIPT') { c.inert = true; inerted.push(c); } });
        n = p;
      }
    }
    function openTry(from) {
      if (isOpen) return; isOpen = true;
      opener = from || document.activeElement; savedY = window.scrollY;   // closing puts the page back exactly where it was
      ov.hidden = false; document.documentElement.classList.add('try-on'); setInert(true); ov.focus({ preventScroll: true }); var th = document.getElementById('live-thread'); if (th) th.scrollTop = 0; start();
    }
    function closeTry() {
      if (!isOpen) return; isOpen = false;
      ov.hidden = true; document.documentElement.classList.remove('try-on'); setInert(false); window.scrollTo({ top: savedY, left: 0, behavior: 'instant' });
      if (/(?:^#|&)try(?:&|$)/.test(location.hash)) { try { history.replaceState(null, '', location.pathname + location.search); } catch (e) {} }
      if (opener && document.contains(opener) && !opener.hidden) opener.focus({ preventScroll: true }); else { var b = document.getElementById('try-open'); if (b) b.focus({ preventScroll: true }); }
      window.scrollTo({ top: savedY, left: 0, behavior: 'instant' });
    }
    function focusables() {
      var seenRadio = {};
      return [].filter.call(ov.querySelectorAll('a[href],button,input,select,textarea,summary,[tabindex]'), function (x) {
        if (x.type === 'radio' && x.name) {   // a radio group is ONE tab stop (the checked one, else the first): listing every radio would make the trap's last stop one the browser never reaches
          var chk = ov.querySelector('input[type=radio][name="' + x.name + '"]:checked');
          if (chk ? x !== chk : seenRadio[x.name]) return false;
          seenRadio[x.name] = 1;
        }
        if (x.disabled || x.getAttribute('tabindex') === '-1' || !x.getClientRects().length || getComputedStyle(x).visibility === 'hidden') return false;
        for (var d = x.parentNode; d && d !== ov; d = d.parentNode) if (d.tagName === 'DETAILS' && !d.open && !(x.tagName === 'SUMMARY' && x.parentNode === d)) return false;   // the inside of a closed disclosure is not a tab stop
        return true;
      });
    }
    [].forEach.call(document.querySelectorAll('.try-open'), function (b) { b.addEventListener('click', function () { openTry(b); }); });
    var closeBtn = document.getElementById('try-close'); if (closeBtn) closeBtn.addEventListener('click', closeTry);
    document.addEventListener('keydown', function (ev) {
      if (!isOpen) return;
      if (ev.key === 'Escape') {   // the Latency ledger panel closes first (live.js does that); the dialog closes on the next press
        var lp = document.getElementById('live-ledger-panel');
        if (lp && !lp.hidden) return;
        ev.preventDefault(); closeTry(); return;
      }
      if (ev.key !== 'Tab') return;
      var f = focusables(); if (!f.length) { ev.preventDefault(); ov.focus(); return; }
      var first = f[0], last = f[f.length - 1], a = document.activeElement;
      if (!ov.contains(a) || a === ov) { ev.preventDefault(); (ev.shiftKey ? last : first).focus(); }
      else if (ev.shiftKey && a === first) { ev.preventDefault(); last.focus(); }
      else if (!ev.shiftKey && a === last) { ev.preventDefault(); first.focus(); }
      else setTimeout(function () { if (isOpen && !ov.contains(document.activeElement)) (ev.shiftKey ? last : first).focus(); }, 0);   // the page behind is inert, so a Tab past the last stop would land on the document: bring it back
    });
    window.addEventListener('hashchange', function () { if (/(?:^#|&)try(?:&|$)/.test(location.hash)) openTry(document.getElementById('try-open')); });
    if (om || wantTry) { window.scrollTo(0, 0); openTry(document.getElementById('try-open')); }   // opened by address: the page behind sits at the top of the first view
  }
})();
