/* SPDX-License-Identifier: MIT */
/* AtomExport: wrapper over ClientExport (client_export.min.js, untouched, loaded on first use): maxWidth, AbortSignal,
   duration cap, PNG, optional wordmark, file names, metadata. ES2017, no deps. See docs/film_export.md. */
(function (root) {
  'use strict';
  var BASE = '';
  try { BASE = document.currentScript.src.replace(/[^/]*$/, ''); } catch (e) { BASE = '/vendors/client-export/'; }
  var NOTE = 'Video export needs a browser with WebCodecs (Chrome, Edge or recent Safari).';
  var DEF = { gif: 0.4, mp4: 1.5, png: 1 };       // the library's own scale defaults; maxWidth can only go below them
  // Hard caps: callers may ask for less, never more. Documented in docs/film_export.md.
  var LIMITS = { maxWidth: 1920, maxArea: 1920 * 1080, maxElementArea: 3840 * 2160, minWidth: 16, maxFps: 60, gifSeconds: 6, videoSeconds: 60 };
  var BUSY = 'An export is already running.';
  var MIME = { gif: 'image/gif', png: 'image/png', mp4: 'video/mp4', webm: 'video/webm' };
  /* ---- pure logic (unit-tested in node) ---- */
  function slug(a) { return String(a || '').toLowerCase().replace(/[^a-z0-9_-]+/g, '-').replace(/^-+|-+$/g, ''); }
  function scaleFor(format, W, maxWidth, H) {
    var s = DEF[format] || 1;
    if (!(W > 0)) return s;
    if (maxWidth > 0) s = Math.min(s, maxWidth / W);
    s = Math.min(s, LIMITS.maxWidth / W);
    if (H > 0) s = Math.min(s, Math.sqrt(LIMITS.maxArea / (W * H)));
    return Math.max(s, LIMITS.minWidth / W);
  }
  // After the 16 px floor the scale can break the caps again: re-check area and height, never allocate a canvas that breaks them.
  var TOO_BIG = 'This element is too large to export.';
  function fitsCaps(W, H, s) { return W * s * H * s <= LIMITS.maxArea * (1 + 1e-6) && H * s <= 16384; }
  function capDuration(dur, maxSeconds) { return maxSeconds > 0 ? Math.min(dur, maxSeconds) : dur; }
  // The cap for a format: the caller's maxSeconds if smaller, else the hard default (GIF 6 s, video 60 s). PNG has none.
  function secondsCap(format, maxSeconds) {
    if (format === 'png') return maxSeconds > 0 ? maxSeconds : 0;
    var hard = format === 'gif' ? LIMITS.gifSeconds : LIMITS.videoSeconds;
    return maxSeconds > 0 ? Math.min(maxSeconds, hard) : hard;
  }
  function clampFps(fps, def) { return fps > 0 && isFinite(fps) ? Math.max(1, Math.min(LIMITS.maxFps, fps)) : def; }
  // Raw DOMException (or anything not an Error) -> plain-text Error; AbortError stays recognisable by name.
  function wrapError(e) {
    if (e && e.name === 'AbortError') return e;
    if (e instanceof Error && !(typeof DOMException !== 'undefined' && e instanceof DOMException)) return e;
    var m = e && (e.message || e.name) ? String(e.message || e.name) : String(e);
    return new Error('Export failed: ' + m);
  }
  function fileName(atom, ext) { return (slug(atom) || 'film') + '-a2uicatalog.' + ext; }
  function metaText(atom) { var s = slug(atom); return 'Made with a2uicatalog.ai/' + (s ? 'atoms/' + s + '/' : ''); }
  function nodVisible(t, dur, on) { return !!on && dur >= 2 && t > 0 && t >= dur - 1 - 1e-9; }
  function hasWebCodecs(g) { g = g || root; return typeof g.VideoEncoder !== 'undefined' && typeof g.VideoFrame !== 'undefined'; }
  function formatsFor(env) {   // env: {clock, element, webcodecs}
    var o = [];
    if (env.clock) { if (env.webcodecs) o.push('mp4'); o.push('gif'); }
    if (env.clock || env.element) o.push('png');
    return o;
  }
  /* ---- byte helpers: metadata the encoder libraries cannot write ---- */
  function enc(s) { return new TextEncoder().encode(s); }
  function cat(parts) {
    var n = 0, i, o, p = 0;
    for (i = 0; i < parts.length; i++) n += parts[i].length;
    o = new Uint8Array(n);
    for (i = 0; i < parts.length; i++) { o.set(parts[i], p); p += parts[i].length; }
    return o;
  }
  function u32(n) { return Uint8Array.of(n >>> 24 & 255, n >>> 16 & 255, n >>> 8 & 255, n & 255); }
  function tag(s) { return Uint8Array.of(s.charCodeAt(0), s.charCodeAt(1), s.charCodeAt(2), s.charCodeAt(3)); }
  function box(type, payload) { return cat([u32(8 + payload.length), tag(type), payload]); }
  // GIF: a Comment Extension after the screen descriptor and global palette.
  function gifComment(bytes, text) {
    if (bytes.length < 13) return bytes;
    var at = 13 + ((bytes[10] & 0x80) ? 3 * (1 << ((bytes[10] & 7) + 1)) : 0), t = enc(text), parts = [Uint8Array.of(0x21, 0xfe)], i;
    for (i = 0; i < t.length; i += 255) { var c = t.subarray(i, i + 255); parts.push(Uint8Array.of(c.length), c); }
    parts.push(Uint8Array.of(0));
    return cat([bytes.subarray(0, at), cat(parts), bytes.subarray(at)]);
  }
  // MP4: moov/udta/meta/ilst with title and comment items; stco/co64 offsets move by the added length (moov precedes mdat).
  function mp4Meta(bytes, title, comment) {
    var dv = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength), moov = -1, mdat = -1, moof = false, p = 0, sz, ty;
    while (p + 8 <= bytes.length) {
      sz = dv.getUint32(p); ty = String.fromCharCode(bytes[p + 4], bytes[p + 5], bytes[p + 6], bytes[p + 7]);
      if (sz < 8 || p + sz > bytes.length) return bytes;
      if (ty === 'moov') moov = p; else if (ty === 'mdat' && mdat < 0) mdat = p; else if (ty === 'moof') moof = true;
      p += sz;
    }
    if (moov < 0) return bytes;
    // Pass 1 (read-only): every chunk-offset table must be well formed and moov must have no udta yet; otherwise return the ORIGINAL bytes.
    var tables = [], ok = true, moovEnd = moov + dv.getUint32(moov), patch = mdat > moov && !moof;
    (function scan(a, z, top) {
      while (ok && a + 8 <= z) {
        var s = dv.getUint32(a), t = String.fromCharCode(bytes[a + 4], bytes[a + 5], bytes[a + 6], bytes[a + 7]), n;
        if (s < 8 || a + s > z) { ok = false; return; }
        if (top && t === 'udta') { ok = false; return; }
        if (t === 'trak' || t === 'mdia' || t === 'minf' || t === 'stbl') scan(a + 8, a + s, false);
        else if (t === 'stco' || t === 'co64') {
          n = s >= 16 ? dv.getUint32(a + 12) : -1;
          if (n < 0 || 16 + (t === 'stco' ? 4 : 8) * n > s) { ok = false; return; }
          tables.push({ a: a, t: t, n: n });
        }
        a += s;
      }
      if (ok && a !== z) ok = false;
    })(moov + 8, moovEnd, true);
    if (!ok) return bytes;
    function item(k, v) { var t = enc(v); return box(k, box('data', cat([u32(1), u32(0), t]))); }
    var hdlr = box('hdlr', cat([u32(0), u32(0), tag('mdir'), tag('appl'), u32(0), u32(0), Uint8Array.of(0)])),
        ilst = box('ilst', cat([item('\xa9nam', title), item('\xa9cmt', comment)])),
        udta = box('udta', box('meta', cat([u32(0), hdlr, ilst]))),
        out = cat([bytes.subarray(0, moovEnd), udta, bytes.subarray(moovEnd)]),
        od = new DataView(out.buffer);
    od.setUint32(moov, moovEnd - moov + udta.length);
    if (patch) tables.forEach(function (x) {   // fragmented MP4 (moof): offsets are not in stco, leave them
      var i, q, lo;
      if (x.t === 'stco') for (i = 0; i < x.n; i++) od.setUint32(x.a + 16 + 4 * i, od.getUint32(x.a + 16 + 4 * i) + udta.length);
      else for (i = 0; i < x.n; i++) {   // 64-bit entries: add to the low word, carry into the high one
        q = x.a + 16 + 8 * i; lo = od.getUint32(q + 4) + udta.length;
        od.setUint32(q, od.getUint32(q) + (lo > 0xffffffff ? 1 : 0)); od.setUint32(q + 4, lo >>> 0);
      }
    });
    return out;
  }
  /* ---- browser side ---- */
  function abortError() {
    return new DOMException('Export aborted', 'AbortError');
  }
  function lum(d) { var s = 0, n = 0; for (var i = 0; i < d.length; i += 4) { s += 0.2126 * d[i] + 0.7152 * d[i + 1] + 0.0722 * d[i + 2]; n++; } return n ? s / n / 255 : 0; }
  function drawNod(cx, w, h) {          // bottom-right, low contrast
    var size = Math.max(9, Math.round(w * 0.017)), m = Math.round(size * 1.2), txt = 'a2uicatalog.ai', tw, dark = false;
    cx.save();
    cx.font = '600 ' + size + 'px system-ui, -apple-system, "Segoe UI", sans-serif';
    tw = cx.measureText(txt).width;
    try { dark = lum(cx.getImageData(Math.max(0, w - m - tw - 4), Math.max(0, h - m - size - 4), Math.ceil(tw + 8), size + 8).data) > 0.55; } catch (e) { }
    cx.fillStyle = dark ? 'rgba(0,0,0,0.38)' : 'rgba(255,255,255,0.42)';
    cx.textBaseline = 'alphabetic';
    cx.fillText(txt, w - m - tw, h - m);
    cx.restore();
  }
  var libP = null;
  function lib() {
    if (root.ClientExport) return Promise.resolve(root.ClientExport);
    if (!libP) libP = new Promise(function (ok, no) {
      var s = document.createElement('script');
      s.src = AtomExport.vendorUrl || BASE + 'client_export.min.js';
      s.onload = function () { root.ClientExport ? ok(root.ClientExport) : (libP = null, no(new Error('The exporter did not start.'))); };
      s.onerror = function () { libP = null; no(new Error('Could not load the exporter.')); };
      document.head.appendChild(s);
    });
    return libP;
  }
  function filmRoot(el) {
    if (!el || el.nodeType !== 1) return null;
    var r = el.classList && el.classList.contains('mt-root') ? el : el.querySelector && el.querySelector('.mt-root'), m;
    m = r && r.id && root.__a2uiMotion && root.__a2uiMotion[r.id.slice(3)];
    return m && typeof m.seek === 'function' && m.dur > 0 ? r : null;
  }
  function formats(el) {
    return formatsFor({ clock: !!filmRoot(el), element: !!(el && el.nodeType === 1), webcodecs: hasWebCodecs() });
  }
  /* A film the library can drive, steered: capped duration, abort check on every seek, canvases that draw the nod. */
  function steer(CE, el, o) {
    var film = CE.findFilm(el.ownerDocument, filmRoot(el)), dur = capDuration(film.dur, o.capSeconds), st = { t: 0 }, canv = [], doc, stage;
    function bind(t, k) { var v = t[k]; return typeof v === 'function' ? v.bind(t) : v; }
    function hook(c) {
      var gc = c.getContext;
      canv.push(c);
      c.getContext = function (type, opt) {
        var cx = gc.call(c, type, opt), d;
        if (type === '2d' && cx && !cx.__an) {
          cx.__an = 1; d = cx.drawImage;
          cx.drawImage = function () { d.apply(cx, arguments); if (nodVisible(st.t, dur, o.nod)) drawNod(cx, c.width, c.height); };
        }
        return cx;
      };
      return c;
    }
    doc = new Proxy(film.st.ownerDocument, { get: function (t, k) {
      if (k === 'createElement') return function (n) { var e = t.createElement(n); return String(n).toLowerCase() === 'canvas' ? hook(e) : e; };
      return bind(t, k);
    } });
    stage = new Proxy(film.st, { get: function (t, k) { return k === 'ownerDocument' ? doc : bind(t, k); } });
    return {
      film: { root: film.root, st: stage, W: film.W, H: film.H, w: film.w, dur: dur,
        f: { dur: dur, pause: function () { film.f.pause(); }, seek: function (t) { if ((o.signal && o.signal.aborted) || o.stopped) throw o.stopped || abortError(); film.f.seek(t); st.t = t; } } },
      W: film.W, dur: dur, canvas: function () { return hook(film.st.ownerDocument.createElement('canvas')); },
      free: function () { canv.forEach(function (c) { c.width = c.height = 0; }); canv.length = 0; }
    };
  }
  // Close any VideoEncoder opened during this export, so an abort or error leaves none running. One wrapper per run, always
  // unwrapped back to the browser's own class (never subclassing an earlier wrapper), restored on every path.
  function trackEncoders() {
    var cur = root.VideoEncoder, Orig = cur && cur.__atomOrig ? cur.__atomOrig : cur, list = [], R;
    if (!Orig) return { close: function () {}, restore: function () {} };
    R = class extends Orig { constructor(i) { super(i); list.push(this); } };
    R.__atomOrig = Orig;
    root.VideoEncoder = R;
    return {
      close: function () { list.forEach(function (e) { try { if (e.state !== 'closed') e.close(); } catch (x) { } }); list.length = 0; },
      restore: function () { if (root.VideoEncoder === R || (root.VideoEncoder && root.VideoEncoder.__atomOrig === Orig)) root.VideoEncoder = Orig; }
    };
  }
  function buf(blob) { return blob.arrayBuffer(); }
  // onProgress(fraction, phase): 'preparing' until the library reports, 'encoding', then 'finishing' (GIF palette / MP4 flush).
  function prog(o) {
    return function (d, n) {
      var f = Math.min(1, d / (n || 1));
      if (o.onProgress) { try { o.onProgress(f, f >= 1 ? 'finishing' : 'encoding'); } catch (e) { } }
    };
  }
  function phase(o, f, ph) { if (o.onProgress) { try { o.onProgress(f, ph); } catch (e) { } } }
  // The film clock before the export, put back afterwards (position from the range input; play() only if it was playing).
  function clockSnap(el) {
    var r = filmRoot(el), m = r && root.__a2uiMotion[r.id.slice(3)], rng = r && r.querySelector('.mt-rng'), v = rng ? parseFloat(rng.value) : NaN;
    return { playing: !!r && r.getAttribute('data-pl') === '1', t: isFinite(v) && m ? v / 1000 * m.dur : null, m: m };
  }
  function clockRestore(c) {
    if (!c || !c.m) return;
    try { if (c.t != null) c.m.seek(c.t); if (c.playing) c.m.play(); else c.m.pause(); } catch (e) { }
  }
  function inlineClone(el) {          // computed styles inline, canvases frozen to images
    var c = el.cloneNode(true), a = [el].concat([].slice.call(el.querySelectorAll('*'))), b = [c].concat([].slice.call(c.querySelectorAll('*'))), i, j, cs, s, im;
    for (i = 0; i < a.length; i++) {
      cs = root.getComputedStyle(a[i]); s = '';
      for (j = 0; j < cs.length; j++) s += cs[j] + ':' + cs.getPropertyValue(cs[j]) + ';';
      b[i].setAttribute('style', s);
      if (a[i].tagName === 'CANVAS') { im = el.ownerDocument.createElement('img'); try { im.src = a[i].toDataURL('image/png'); } catch (e) { continue; } im.setAttribute('style', s); b[i].replaceWith(im); }
    }
    return c;
  }
  function toBlob(canvas) { return new Promise(function (ok, no) { canvas.toBlob(function (b) { b ? ok(b) : no(new Error('PNG encoding failed.')); }, 'image/png'); }); }
  function pngBlob(CE, el, o) {
    var s, c, scale, snap;
    if (filmRoot(el)) {
      snap = clockSnap(el);
      s = steer(CE, el, o);
      scale = scaleFor('png', s.W, o.maxWidth, s.film.H);
      if (!fitsCaps(s.W, s.film.H, scale)) { s.free(); return Promise.reject(new Error(TOO_BIG)); }
      c = s.canvas();
      return CE.seekTo(s.film, typeof o.t === 'number' && isFinite(o.t) ? Math.max(0, Math.min(s.dur, o.t)) : s.dur)
        .then(function () { return CE.rasterFrame(s.film, scale, c); })
        .then(toBlob).then(function (b) { s.free(); clockRestore(snap); return b; }, function (e) { s.free(); clockRestore(snap); throw e; });
    }
    var r = el.getBoundingClientRect(), W = Math.round(r.width), H = Math.round(r.height);
    if (!(W > 0 && H > 0)) return Promise.reject(new Error('The element has no size.'));
    if (W * H > LIMITS.maxElementArea) return Promise.reject(new Error('The element is too large to export as an image (limit ' + LIMITS.maxElementArea + ' px area, about 3840 x 2160).'));
    scale = scaleFor('png', W, o.maxWidth, H);
    if (!fitsCaps(W, H, scale)) return Promise.reject(new Error(TOO_BIG));
    return CE.rasterFrame({ st: inlineClone(el), W: W, H: H, w: root }, scale, null).then(toBlob);
  }
  /* ---- guards shared by run() and png() ---- */
  var busy = false;
  function precheck(o, needFilm, format) {
    if (o.signal && o.signal.aborted) return abortError();
    if (format && (!MIME[format] || format === 'webm')) return new Error('Unknown format: ' + format);
    if (format === 'mp4' && !hasWebCodecs()) return new Error(NOTE);
    if (!o.el || o.el.nodeType !== 1) return new Error('No element to export.');
    if (needFilm && !filmRoot(o.el)) return new Error('No film clock: only PNG is possible here.');
    if (document.visibilityState === 'hidden') return new Error('Keep this tab visible during export.');
    return null;
  }
  // Listen for abort and for the tab being hidden; reject at once instead of waiting for the next animation frame.
  function watch(o, onStop) {
    function hid() { if (document.visibilityState === 'hidden') stop(new Error('Keep this tab visible during export.')); }
    function ab() { stop(abortError()); }
    function stop(e) { o.stopped = o.stopped || e; onStop(e); }
    if (o.signal && o.signal.addEventListener) o.signal.addEventListener('abort', ab);
    document.addEventListener('visibilitychange', hid);
    return function () { if (o.signal && o.signal.removeEventListener) o.signal.removeEventListener('abort', ab); document.removeEventListener('visibilitychange', hid); };
  }
  // One export at a time (module-level lock). The lock is held until the work settles, or WATCH.releaseMs after an abort/hide at most.
  // Watchdog: a library that never settles (and no signal) is cut off after capSeconds * k + baseSeconds with 'Export timed out.'.
  var WATCH = { k: 10, baseSeconds: 30, releaseMs: 3000 };
  function timeoutMs(capSeconds) { return ((capSeconds > 0 ? capSeconds : 0) * WATCH.k + WATCH.baseSeconds) * 1000; }
  function exclusive(o, job) {
    if (busy) return Promise.reject(new Error(BUSY));
    var mine = {}, released = false, ctl = {}, timer;
    busy = mine;
    function release() { if (!released) { released = true; clearTimeout(timer); if (busy === mine) busy = false; } }
    return new Promise(function (resolve, reject) {
      var stop = watch(o, function (e) { reject(e); if (ctl.close) ctl.close(); setTimeout(release, WATCH.releaseMs); });
      timer = setTimeout(function () {
        var e = new Error('Export timed out.');
        o.stopped = o.stopped || e; stop(); reject(e);
        try { if (ctl.close) ctl.close(); } catch (x) { }
        release();
      }, timeoutMs(o.capSeconds));
      Promise.resolve().then(function () { if (o.stopped) throw o.stopped; return lib(); })
        .then(function (CE) { if (o.stopped) throw o.stopped; return job(CE, ctl); })
        .then(function (v) { stop(); release(); resolve(v); }, function (e) { stop(); release(); reject(wrapError(e)); });
    });
  }
  function run(format, o) {
    o = o || {};
    var err = precheck(o, format !== 'png', format);
    if (err) return Promise.reject(err);
    if (format === 'png') return pngExport(Object.assign({}, o)).then(function (b) { return { blob: b, name: fileName(o.atom, 'png'), mime: MIME.png }; });
    var meta = metaText(o.atom);
    o = Object.assign({}, o, { capSeconds: secondsCap(format, o.maxSeconds) });
    return exclusive(o, function (CE, ctl) {
      if (o.stopped) throw o.stopped;
      var p = prog(o), s, tr, task, snap = clockSnap(o.el);
      var done = false;
      function cleanup() { if (done) return; done = true; if (s) s.free(); if (tr) { tr.close(); tr.restore(); } clockRestore(snap); }
      ctl.close = cleanup;   // an abort or a hidden tab runs the same cleanup at once
      phase(o, 0, 'preparing');
      try {
        s = steer(CE, o.el, o);
        if (!fitsCaps(s.W, s.film.H, scaleFor(format, s.W, o.maxWidth, s.film.H))) throw new Error(TOO_BIG);
        if (format === 'gif') {
          task = CE.exportGif(s.film, { fps: clampFps(o.fps, 10), scale: scaleFor('gif', s.W, o.maxWidth, s.film.H), onProgress: p })
            .then(buf).then(function (ab) { return { blob: new Blob([gifComment(new Uint8Array(ab), meta)], { type: MIME.gif }), name: fileName(o.atom, 'gif'), mime: MIME.gif }; });
        } else {
          tr = trackEncoders();
          task = CE.exportVideo(s.film, { fps: clampFps(o.fps, 30), scale: scaleFor('mp4', s.W, o.maxWidth, s.film.H), onProgress: p })
            .then(function (r) {
              phase(o, 1, 'finishing');
              return buf(r.blob).then(function (ab) {
                var b = new Uint8Array(ab), ext = r.kind === 'mp4' ? 'mp4' : 'webm';
                if (ext === 'mp4') b = mp4Meta(b, meta, meta);   // WebM: no metadata (see docs)
                return { blob: new Blob([b], { type: MIME[ext] }), name: fileName(o.atom, ext), mime: MIME[ext], width: r.W, height: r.H, fps: r.fps, frames: r.frames };
              });
            });
        }
      } catch (e) { cleanup(); throw e; }
      return task.then(function (v) { if ((o.signal && o.signal.aborted) || o.stopped) throw o.stopped || abortError(); return v; })
        .then(function (v) { cleanup(); return v; }, function (e) { cleanup(); throw e; });
    });
  }
  function pngExport(o) {
    return exclusive(o, function (CE) { if (o.stopped) throw o.stopped; phase(o, 0, 'preparing'); return pngBlob(CE, o.el, o).then(function (b) { phase(o, 1, 'finishing'); return b; }); });
  }
  function png(el, o) {
    o = Object.assign({}, o || {}, { el: el });
    var err = precheck(o, false, null);
    return err ? Promise.reject(err) : pngExport(o);
  }
  function download(r) {
    var a = document.createElement('a'), u = URL.createObjectURL(r.blob);
    a.href = u; a.download = r.name; document.body.appendChild(a); a.click(); a.remove();
    setTimeout(function () { URL.revokeObjectURL(u); }, 4000);
  }
  function atomFromLocation() { var m = /\/atoms\/([a-z0-9_-]+)\//i.exec((root.location && root.location.pathname) || ''); return m ? m[1] : ''; }
  var AtomExport = {
    formats: formats, run: run, png: png, download: download, atomFromLocation: atomFromLocation, vendorUrl: '', watchdog: WATCH, note: NOTE, limits: LIMITS,
    _pure: { scaleFor: scaleFor, capDuration: capDuration, secondsCap: secondsCap, clampFps: clampFps, fitsCaps: fitsCaps, timeoutMs: timeoutMs, wrapError: wrapError, fileName: fileName, metaText: metaText, nodVisible: nodVisible, formatsFor: formatsFor,
      gifComment: gifComment, mp4Meta: mp4Meta, slug: slug }
  };
  if (typeof module !== 'undefined' && module.exports) module.exports = AtomExport;
  if (typeof window !== 'undefined') {
    window.AtomExport = AtomExport;
    // Compat with the film's own MP4/GIF buttons (they ignore the result, so this saves the file); an existing A2UIExport wins.
    if (!window.A2UIExport) window.A2UIExport = {
      kinds: hasWebCodecs() ? ['mp4', 'gif'] : ['gif'],
      // Saves a capped export (same defaults as run(): GIF 6 s, video 60 s, 1920 px) and honours a signal passed as 4th argument.
      run: function (rootEl, kind, progress, signal) {
        return run(kind, { el: rootEl, atom: atomFromLocation(), signal: signal, onProgress: function (f) { if (progress) progress(Math.round(f * 1000), 1000); } }).then(download);
      }
    };
  }
})(typeof window !== 'undefined' ? window : globalThis);
