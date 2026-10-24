/* A2UI Catalog film captions: WebVTT from a motion_timeline film. Port of scripts/film_vtt.py (I88); the two must
   produce identical text (tests/test_film_vtt_js.py). filmToVtt(film, C): film = the motion_timeline block (or a payload
   whose blocks hold one), C = the player config `var C={W,H,dur,poster,tg:[...]}` the renderer hands the player. */
(function (root) {
  'use strict';
  var STEP = 0.05, MIN_CUE = 0.2, P_SHOWN = 0.5, OPACITY_SHOWN = 0.5;

  function bez(a, b, t) { var u = 1 - t; return 3 * u * u * t * a + 3 * u * t * t * b + t * t * t; }
  function ez(e, u) {
    if (u <= 0) return 0;
    if (u >= 1) return 1;
    if (!e) return u;
    if (e === 1) return 0;
    var lo = 0, hi = 1, t = u;
    for (var i = 0; i < 28; i++) { t = (lo + hi) / 2; if (bez(e[0], e[2], t) < u) lo = t; else hi = t; }
    return bez(e[1], e[3], t);
  }
  function valueAt(keys, t) {
    if (t <= keys[0][0]) return keys[0][1];
    if (t >= keys[keys.length - 1][0]) return keys[keys.length - 1][1];
    for (var i = 1; i < keys.length; i++) {
      if (t <= keys[i][0]) {
        var a = keys[i - 1], b = keys[i];
        return a[1] + (b[1] - a[1]) * ez(b.length > 2 ? b[2] : null, (t - a[0]) / (b[0] - a[0]));
      }
    }
    return keys[keys.length - 1][1];
  }
  function pad(n, w) { n = String(n); while (n.length < w) n = '0' + n; return n; }
  function ts(sec) {
    var ms = Math.round(Math.max(0, sec) * 1000);
    return pad(Math.floor(ms / 3600000), 2) + ':' + pad(Math.floor(ms / 60000) % 60, 2) + ':' + pad(Math.floor(ms / 1000) % 60, 2) + '.' + pad(ms % 1000, 3);
  }
  function esc(s) { return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
  function plain(text) {
    var s = (text === undefined || text === null || text === false || text === 0) ? '' : String(text);
    return s.split('*').join('').replace(/\s+/g, ' ').trim();
  }
  function walk(blocks, chain, out) {
    if (!Array.isArray(blocks)) return;
    blocks.forEach(function (b) {
      if (!b || typeof b !== 'object' || Array.isArray(b)) return;
      out.push([b, chain]);
      walk(b.blocks, b.id ? chain.concat([b.id]) : chain, out);
    });
  }
  function intervals(flags, dur) {
    var out = [], start = null;
    for (var i = 0; i < flags.length; i++) {
      var t = i * STEP;
      if (flags[i] && start === null) start = t;
      else if (!flags[i] && start !== null) { out.push([start, t]); start = null; }
    }
    if (start !== null) out.push([start, dur]);
    return out.map(function (x) { return [x[0], Math.min(x[1], dur)]; }).filter(function (x) { return x[1] - x[0] >= MIN_CUE; });
  }

  function filmToVtt(film, C) {
    if (!film || film.type !== 'motion_timeline') {
      var f = ((film && film.blocks) || []).filter(function (b) { return b && b.type === 'motion_timeline'; })[0];
      if (!f) throw new Error('no motion_timeline in payload');
      film = f;
    }
    var dur = Number(C.dur), tracks = {};
    C.tg.forEach(function (g) {
      var m = tracks[g.i] || (tracks[g.i] = {});
      Object.keys(g.p).forEach(function (k) { if (g.p[k] && g.p[k].length) m[k] = g.p[k]; });
    });
    var times = [], n = Math.floor(dur / STEP) + 1;
    for (var i = 0; i < n; i++) times.push(i * STEP);

    function onScreen(chain, gate) {
      return times.map(function (t) {
        for (var j = 0; j < chain.length; j++) {
          var k = (tracks[chain[j]] || {}).opacity;
          if (k && valueAt(k, t) < OPACITY_SHOWN) return false;
        }
        return gate ? gate(t) : true;
      });
    }
    var items = [], cues = [];
    walk(film.blocks, [], items);
    items.forEach(function (it, order) {
      var b = it[0], anc = it[1], bid = b.id, mine = (bid && tracks[bid]) || {};
      var chain = bid ? anc.concat([bid]) : anc;
      var shown = function (t) { return mine.p === undefined || valueAt(mine.p, t) >= P_SHOWN; };
      if (b.type === 'motion_text' && plain(b.text)) {
        intervals(onScreen(chain, shown), dur).forEach(function (r) { cues.push([r[0], r[1], order, bid, esc(plain(b.text))]); });
      } else if (b.type === 'demo_caption' && Array.isArray(b.lines)) {
        b.lines.slice(0, 12).forEach(function (line, li) {
          line = (line && typeof line === 'object' && !Array.isArray(line)) ? line : { text: line };
          var text = plain(line.text);
          if (!text) return;
          var st = mine.step;
          var atLine = function (t) { return st ? Math.abs(valueAt(st, t) - li) < 0.5 : li === 0; };
          var who = plain(line.who) || 'agent';
          intervals(onScreen(chain, atLine), dur).forEach(function (r) {
            cues.push([r[0], r[1], order * 100 + li, bid, '<v ' + esc(who) + '>' + esc(text) + '</v>']);
          });
        });
      }
    });
    cues.sort(function (a, b) { return (a[0] - b[0]) || (a[1] - b[1]) || (a[2] - b[2]); });
    var out = ['WEBVTT', ''], seen = {};
    cues.forEach(function (c) {
      var ident = c[3] || 'cue';
      seen[ident] = (seen[ident] || 0) + 1;
      if (seen[ident] > 1) ident += '.' + seen[ident];
      out.push(ident, ts(c[0]) + ' --> ' + ts(c[1]), c[4], '');
    });
    return out.join('\n');
  }
  // The player config is a JS object literal inside the rendered film's inline script; read it the way film_still.py does.
  function configFromScripts(doc) {
    var ss = doc.querySelectorAll('script');
    for (var i = 0; i < ss.length; i++) {
      var m = /var C=(\{[\s\S]*?\});var root=/.exec(ss[i].textContent || '');
      if (m) return JSON.parse(m[1].replace(/([{,])([A-Za-z_]\w*):/g, '$1"$2":'));
    }
    return null;
  }
  var api = { filmToVtt: filmToVtt, configFromScripts: configFromScripts };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.FilmVtt = api;
})(typeof window !== 'undefined' ? window : this);
