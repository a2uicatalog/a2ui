/* The standalone live page (published as demo-livepage.js). It runs the SAME app as the Try it dialog: demo-live.js and demo-kit.css are loaded as they are, and this
   small script only sets the page up around it. It never reads or writes a key.
   Recording parameters (parsed once, every value checked against a fixed list; anything else is ignored):
     frame=16x9|4x5|1x1|9x16   size=large   theme=light|dark   q=<text>   clean=1   guides=1   ledger=open|strip|panel|off
   The only secret accepted is the #owner=KEY fragment, read into memory and removed from the address bar at once (as in the dialog). A key, apikey or token query
   parameter is never read: it is removed from the address bar and used nowhere. Copy link rebuilds the address from the checked values only, so it never carries
   the fragment or a key. */
(function () {
  'use strict';
  var FRAMES = ['16x9', '4x5', '1x1', '9x16'], PORTRAIT = { '4x5': 1, '1x1': 1, '9x16': 1 }, LEDGERS = ['open', 'strip', 'panel', 'off'];
  var NAMES_TO_DROP = /^(key|apikey|api_key|api-key|token|owner|secret|access_token)$/i;
  var stage = document.getElementById('live-stage');
  if (!stage) return;
  var qs = new URLSearchParams(location.search), keep = {};
  function pick(name, allowed) { var v = qs.get(name); return v !== null && allowed.indexOf(v) >= 0 ? v : ''; }
  var frame = pick('frame', FRAMES), size = pick('size', ['large']), theme = pick('theme', ['light', 'dark']), clean = pick('clean', ['1']), guides = pick('guides', ['1']), ledger = pick('ledger', LEDGERS);
  var q = (qs.get('q') || '').replace(/[\u0000-\u001f\u007f-\u009f\u2028\u2029]/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 500);
  if (frame) { keep.frame = frame; stage.setAttribute('data-frame', frame); }
  if (size) { keep.size = size; stage.setAttribute('data-size', size); document.documentElement.style.fontSize = '125%'; }
  if (theme) { keep.theme = theme; document.documentElement.setAttribute('data-theme', theme); }   // forced for this view only: nothing is stored
  if (clean) { keep.clean = clean; stage.setAttribute('data-clean', '1'); }
  if (guides) { keep.guides = guides; stage.setAttribute('data-guides', '1'); }
  if (ledger) keep.ledger = ledger;
  if (q) keep.q = q;
  /* the owner fragment and any key-like query parameter leave the address bar at once; nothing is stored */
  var owner = '', om = /(?:^#|&)owner=([^&]*)/.exec(location.hash), dirty = !!om;
  if (om) { try { owner = decodeURIComponent(om[1]); } catch (e) { owner = om[1]; } }
  var clear = new URLSearchParams(location.search);
  qs.forEach(function (v, k) { if (NAMES_TO_DROP.test(k)) { clear.delete(k); dirty = true; } });
  if (dirty) { try { history.replaceState(null, '', location.pathname + (clear.toString() ? '?' + clear.toString() : '')); } catch (e) {} }

  function say(text) { var s = document.getElementById('live-link-status'); if (!s) return; s.textContent = ''; setTimeout(function () { s.textContent = text; }, 40); }
  function shareUrl() {
    var u = new URLSearchParams(); Object.keys(keep).forEach(function (k) { u.set(k, keep[k]); });
    return location.origin + location.pathname + (u.toString() ? '?' + u.toString() : '');
  }
  function copyLink(cfg) {   // the clipboard API where the page allows it, else select the text and use the older copy command (the pattern in kit.js)
    var url = shareUrl(), L = cfg.lp;
    function ok() { say(L.link_copied); }
    function blocked() { say(L.link_copy_failed); }
    if (navigator.clipboard && window.isSecureContext) { navigator.clipboard.writeText(url).then(ok, blocked); return; }
    var ta = document.createElement('textarea'); ta.value = url; ta.setAttribute('readonly', ''); ta.style.cssText = 'position:fixed;top:0;left:0;opacity:0';
    document.body.appendChild(ta); ta.select(); var done = false;
    try { done = document.execCommand('copy'); } catch (e) {}
    document.body.removeChild(ta); if (done) ok(); else blocked();
  }

  function go() {
    var cfg = JSON.parse(document.getElementById('live-config').textContent);
    window.A2UILive.start({ owner: owner, page: { ledger: ledger, portrait: !!PORTRAIT[frame] } });
    owner = '';
    var box = document.getElementById('live-q');
    if (q && box) box.value = q.slice(0, Math.min(500, cfg.max_q || 500));   // the DOM value property: the text is never markup, and the question is never sent from here
    var b = document.getElementById('live-copylink'); if (b) b.addEventListener('click', function () { copyLink(cfg); });
  }
  if (window.A2UILive) go(); else window.addEventListener('load', go);
})();
