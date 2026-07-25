// atoms_gallery.gs — field-guide gallery atoms (a2ui-gallery-v1)
//
// Origin: the "De Primitivis" anatomy-plate pitch (2026-07-25) — a real UI
// capture, pin-annotated, where each pin is a declarative {x, y, field, note}
// coordinate (0-100, percent of the image), never a hand-drawn illustration.
// Python source of truth: renderers/web_article.py's _render_primitive_plate
// / _render_scroll_gallery — keep this file in parity with that one.

var _PP_ROMAN = ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix', 'x',
                 'xi', 'xii', 'xiii', 'xiv', 'xv', 'xvi', 'xvii', 'xviii', 'xix', 'xx'];
function _ppRoman(n) {
  return (n >= 1 && n <= _PP_ROMAN.length) ? _PP_ROMAN[n - 1] : String(n);
}

// Follows the HOST page's own theme tokens (--text/--surface/--accent/...,
// the indigo-277/cyan-202 pair) rather than a standalone palette — the
// parchment/codex look this atom started from read as a beige island next
// to the rest of the site (design feedback, 2026-07-25).
var _PP_CSS = '<style>' +
  '.pp-wrap{margin:1.4rem 0;}' +
  '.pp-head{display:flex;align-items:baseline;gap:14px;margin-bottom:4px;flex-wrap:wrap;}' +
  '.pp-head h4{font-size:1.4rem;font-weight:700;margin:0;color:var(--text,#1f2328);}' +
  '.pp-kind{font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace;font-size:.68rem;' +
  'letter-spacing:.1em;text-transform:uppercase;color:var(--accent-2,var(--accent,#1a73e8));' +
  'border:1px solid var(--accent-2,var(--accent,#1a73e8));border-radius:3px;padding:2px 8px;}' +
  '.pp-caption{color:var(--text-muted,#5f6368);max-width:64ch;margin:6px 0 18px;font-size:.94rem;}' +
  '.pp-toggles{display:flex;gap:6px;margin-bottom:14px;flex-wrap:wrap;}' +
  '.pp-toggles input{display:none;}' +
  '.pp-toggles label{font-family:ui-monospace,monospace;font-size:.72rem;padding:6px 14px;' +
  'border:1px solid var(--border,#e0e0e0);border-radius:999px;cursor:pointer;color:var(--text-muted,#5f6368);' +
  'transition:all .15s;}' +
  '.pp-toggles input:checked + label{color:var(--accent,#1a73e8);border-color:var(--accent,#1a73e8);font-weight:600;}' +
  '.pp-state{display:none;}' +
  '.pp-plate{display:flex;align-items:flex-start;gap:0;background:var(--surface-2,#f8f9fa);' +
  'border:1px solid var(--border,#e0e0e0);border-radius:10px;padding:24px;position:relative;}' +
  '.pp-imgwrap{position:relative;flex:0 0 auto;}' +
  '.pp-imgwrap img{display:block;width:100%;height:auto;border:1px solid var(--border,#e0e0e0);border-radius:8px;}' +
  '.pp-imgwrap svg{position:absolute;inset:0;width:100%;height:100%;overflow:visible;}' +
  '.pp-pin{position:absolute;transform:translate(-50%,-50%);width:22px;height:22px;border-radius:50%;' +
  'background:var(--surface,#fff);border:1.4px solid var(--accent,#1a73e8);color:var(--accent,#1a73e8);' +
  'font-family:ui-monospace,monospace;font-size:.66rem;font-weight:700;display:flex;' +
  'align-items:center;justify-content:center;box-shadow:0 1px 2px rgba(0,0,0,.25);}' +
  '.pp-gap{flex:0 0 64px;position:relative;}' +
  '.pp-gap svg{position:absolute;top:0;left:0;}' +
  '.pp-labels{flex:1 1 auto;position:relative;min-width:240px;}' +
  '.pp-label{position:absolute;left:0;right:0;top:0;padding-left:2px;visibility:hidden;}' +
  '.pp-label.pp-placed{visibility:visible;}' +
  '.pp-label .pp-num{font-family:ui-monospace,monospace;color:var(--accent,#1a73e8);font-weight:700;' +
  'font-size:.72rem;margin-right:6px;}' +
  '.pp-label .pp-field{font-family:ui-monospace,monospace;font-size:.72rem;color:var(--accent-2,var(--accent,#1a73e8));' +
  'display:block;letter-spacing:.02em;margin-bottom:2px;}' +
  '.pp-label .pp-note{font-size:.86rem;color:var(--text,#1f2328);display:block;line-height:1.35;}' +
  '.pp-label .pp-note.pp-chrome{color:var(--text-muted,#5f6368);font-style:italic;}' +
  '@media (max-width:860px){' +
  '.pp-plate{flex-direction:column;}' +
  '.pp-gap{display:none;}' +
  '.pp-labels{min-width:0;position:static;}' +
  '.pp-label{position:static !important;margin:14px 0;padding-left:14px;' +
  'border-left:2px solid var(--accent,#1a73e8);visibility:visible;}' +
  '}' +
  '</style>';

var _PP_JS = '<script>' +
  '(function(){' +
  '  if (window.__a2uiPlateLayout) return;' +
  '  window.__a2uiPlateLayout = function(root) {' +
  '    if (window.matchMedia("(max-width:860px)").matches) return;' +
  '    (root || document).querySelectorAll(".pp-plate").forEach(function(plate){' +
  '      var imgwrap = plate.querySelector(".pp-imgwrap");' +
  '      var pins = [].slice.call(plate.querySelectorAll(".pp-pin"));' +
  '      var gap = plate.querySelector(".pp-gap");' +
  '      var labelsBox = plate.querySelector(".pp-labels");' +
  '      var labels = [].slice.call(labelsBox.querySelectorAll(".pp-label"));' +
  '      if (!pins.length || !labels.length) return;' +
  '      var plateRect = plate.getBoundingClientRect();' +
  '      var imgRect = imgwrap.getBoundingClientRect();' +
  '      var pinYs = pins.map(function(p){' +
  '        var r = p.getBoundingClientRect();' +
  '        return (r.top + r.height / 2) - plateRect.top;' +
  '      });' +
  '      labels.forEach(function(l){ l.style.top = "0px"; l.style.visibility = "hidden"; });' +
  '      var heights = labels.map(function(l){ return l.getBoundingClientRect().height; });' +
  '      var GAP = 14, tops = [];' +
  '      pinYs.forEach(function(y, i){' +
  '        var top = y - heights[i] / 2;' +
  '        if (i > 0) top = Math.max(top, tops[i - 1] + heights[i - 1] + GAP);' +
  '        tops.push(top);' +
  '      });' +
  '      tops.forEach(function(top, i){' +
  '        labels[i].style.top = top + "px";' +
  '        labels[i].style.visibility = "visible";' +
  '        labels[i].classList.add("pp-placed");' +
  '      });' +
  '      var totalH = Math.max(imgRect.height, tops[tops.length - 1] + heights[heights.length - 1]);' +
  '      labelsBox.style.minHeight = totalH + "px";' +
  '      gap.style.minHeight = totalH + "px";' +
  '      var gapRect = gap.getBoundingClientRect();' +
  '      var svgNS = "http://www.w3.org/2000/svg";' +
  '      var svg = gap.querySelector("svg");' +
  '      if (svg) svg.remove();' +
  '      svg = document.createElementNS(svgNS, "svg");' +
  '      svg.setAttribute("width", gapRect.width);' +
  '      svg.setAttribute("height", totalH);' +
  '      svg.setAttribute("viewBox", "0 0 " + gapRect.width + " " + totalH);' +
  '      pinYs.forEach(function(y, i){' +
  '        var labelCenterY = tops[i] + heights[i] / 2;' +
  '        var midX = gapRect.width * 0.5;' +
  '        var path = document.createElementNS(svgNS, "path");' +
  '        path.setAttribute("d", "M0," + y.toFixed(1) + " L" + midX.toFixed(1) + "," + y.toFixed(1) +' +
  '          " L" + (gapRect.width - 6).toFixed(1) + "," + labelCenterY.toFixed(1) +' +
  '          " L" + gapRect.width + "," + labelCenterY.toFixed(1));' +
  '        path.setAttribute("fill", "none");' +
  '        path.setAttribute("stroke", "var(--accent,#1a73e8)");' +
  '        path.setAttribute("stroke-width", "1");' +
  '        path.setAttribute("opacity", "0.75");' +
  '        svg.appendChild(path);' +
  '        var dot = document.createElementNS(svgNS, "circle");' +
  '        dot.setAttribute("cx", 0);' +
  '        dot.setAttribute("cy", y.toFixed(1));' +
  '        dot.setAttribute("r", 2.4);' +
  '        dot.setAttribute("fill", "var(--accent,#1a73e8)");' +
  '        svg.appendChild(dot);' +
  '      });' +
  '      gap.appendChild(svg);' +
  '    });' +
  '  };' +
  '  function runAll(){ requestAnimationFrame(function(){ window.__a2uiPlateLayout(document); }); }' +
  '  if (document.readyState === "loading") {' +
  '    document.addEventListener("DOMContentLoaded", runAll);' +
  '  } else {' +
  '    runAll();' +
  '  }' +
  '  window.addEventListener("load", runAll);' +
  '  document.addEventListener("change", function(e){' +
  '    if (e.target && e.target.matches(".pp-toggles input")) runAll();' +
  '  });' +
  '  var t;' +
  '  window.addEventListener("resize", function(){ clearTimeout(t); t = setTimeout(runAll, 150); });' +
  '})();' +
  '</script>';

var _ppCounter = 0;

_RENDERERS['primitive_plate'] = function(b) {
  _ppCounter += 1;
  var uid = 'pp' + _ppCounter;
  var title = _esc(b.title || '');
  var kind = _esc(b.kind || '');
  var caption = b.caption || '';
  var width = b.width || 460;
  var states = b.states || [];
  if (!states.length) return '';

  function stateBody(state, idx) {
    var pins = state.pins || [];
    var img = state.image || '';
    var lines = pins.map(function(p) {
      return '<line x1="' + (p.x || 0) + '" y1="' + (p.y || 0) + '" x2="100" y2="' + (p.y || 0) +
        '" stroke="var(--accent,#1a73e8)" stroke-width="0.4"/>';
    }).join('');
    var markers = pins.map(function(p, i) {
      return '<div class="pp-pin" style="top:' + (p.y || 0) + '%;left:' + (p.x || 0) + '%;">' +
        _ppRoman(i + 1) + '</div>';
    }).join('');
    var labelDivs = pins.map(function(p, i) {
      var chromeCls = p.chrome ? ' pp-chrome' : '';
      var field = _esc(p.field || '');
      var note = _markdownToHtml(p.note || '');
      return '<div class="pp-label"><span class="pp-field">' + field + '</span>' +
        '<span class="pp-note' + chromeCls + '"><span class="pp-num">' + _ppRoman(i + 1) + '.</span> ' +
        note + '</span></div>';
    }).join('');
    var display = (idx === 0) ? 'display:block;' : 'display:none;';
    return '<div class="pp-state' + (idx === 0 ? ' active' : '') + '" data-state="' + uid + '_' + idx +
      '" style="' + display + '">' +
      '<div class="pp-plate">' +
      '<div class="pp-imgwrap" style="width:' + width + 'px;">' +
      '<img src="' + img + '" alt="' + title + ' primitive rendering in Gemini Enterprise">' +
      '<svg viewBox="0 0 100 100" preserveAspectRatio="none">' + lines + '</svg>' +
      markers +
      '</div>' +
      '<div class="pp-gap"></div>' +
      '<div class="pp-labels">' + labelDivs + '</div>' +
      '</div>' +
      '</div>';
  }

  var togglesHtml = '';
  if (states.length > 1) {
    var inputs = states.map(function(s, i) {
      return '<input type="radio" name="' + uid + '_toggle" id="' + uid + '_t' + i + '"' +
        (i === 0 ? ' checked' : '') + ' ' +
        'onchange="document.querySelectorAll(\'[data-state^=\\\'' + uid + '_\\\']\').forEach(function(el){' +
        'el.style.display = (el.dataset.state === \'' + uid + '_' + i + '\') ? \'block\' : \'none\';});">';
    }).join('');
    var toggleLabels = states.map(function(s, i) {
      return '<label for="' + uid + '_t' + i + '">' + _esc(s.label || ('State ' + (i + 1))) + '</label>';
    }).join('');
    togglesHtml = '<div class="pp-toggles">' + inputs + toggleLabels + '</div>';
  }

  var statesHtml = states.map(function(s, i) { return stateBody(s, i); }).join('');
  var captionHtml = caption ? '<p class="pp-caption">' + _markdownToHtml(caption) + '</p>' : '';
  var kindHtml = kind ? '<span class="pp-kind">' + kind + '</span>' : '';

  return _PP_CSS + _PP_JS +
    '<div class="pp-wrap" id="' + _esc(b.id || uid) + '">' +
    '<div class="pp-head"><h4>' + title + '</h4>' + kindHtml + '</div>' +
    captionHtml + togglesHtml + statesHtml +
    '</div>';
};

var _sgCounter = 0;

function _sgAnchor(text, uid, idx, subIdx) {
  var base = String(text).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
  return (subIdx !== undefined && subIdx !== null) ?
    (uid + '_' + idx + '_' + subIdx + '_' + base) : (uid + '_' + idx + '_' + base);
}

function _scrollspyScript(ids) {
  return '<script>' +
    '(function(){' +
    'window.__a2uiSpyIds = (window.__a2uiSpyIds || []).concat(' + JSON.stringify(ids) + ');' +
    'if (window.__a2uiSpyInit) return;' +
    'window.__a2uiSpyInit = true;' +
    'document.addEventListener("DOMContentLoaded", function(){' +
    '  var ids = window.__a2uiSpyIds || [];' +
    '  var targets = ids.map(function(id){ return document.getElementById(id); }).filter(Boolean);' +
    '  if (!targets.length) return;' +
    '  var current = null;' +
    '  function setActive(id){' +
    '    if (id === current) return;' +
    '    current = id;' +
    '    document.querySelectorAll(".sg-active-link").forEach(function(el){ el.classList.remove("sg-active-link"); });' +
    '    if (!id) return;' +
    '    document.querySelectorAll(\'a[href="#\' + id + \'"]\').forEach(function(el){ el.classList.add("sg-active-link"); });' +
    '  }' +
    '  var io = new IntersectionObserver(function(entries){' +
    '    var visible = entries.filter(function(e){ return e.isIntersecting; });' +
    '    if (!visible.length) return;' +
    '    visible.sort(function(a,b){ return a.boundingClientRect.top - b.boundingClientRect.top; });' +
    '    setActive(visible[0].target.id);' +
    '  }, {rootMargin: "-15% 0px -70% 0px", threshold: 0});' +
    '  targets.forEach(function(t){ io.observe(t); });' +
    '});' +
    '})();' +
    '</script>';
}

_RENDERERS['scroll_gallery'] = function(b) {
  _sgCounter += 1;
  var uid = 'sg' + _sgCounter;
  var sections = b.sections || [];
  if (!sections.length) return '';

  var navItems = [];
  var sectionHtmls = [];
  var spyIds = [];
  sections.forEach(function(section, si) {
    var label = section.label || ('Section ' + (si + 1));
    var blocks = section.blocks || [];
    var secAnchor = _sgAnchor(label, uid, si);
    var subLinks = [];
    blocks.forEach(function(blk, bi) {
      var subTitle = blk.title || blk.label;
      if (subTitle) {
        var subAnchor = blk.id || _sgAnchor(subTitle, uid, si, bi);
        if (!blk.id) blk.id = subAnchor;
        subLinks.push('<a class="sg-sub" href="#' + subAnchor + '">' + _esc(subTitle) + '</a>');
        spyIds.push(subAnchor);
      }
    });
    navItems.push(
      '<div class="sg-navsection">' +
      '<a class="sg-navhead" href="#' + secAnchor + '"><span class="sg-navnum">' +
      ('0' + (si + 1)).slice(-2) + '</span>' + _esc(label) + '</a>' +
      subLinks.join('') +
      '</div>'
    );
    var body = blocks.map(function(blk) {
      var fn = _RENDERERS[blk.type] || function(){ return ''; };
      return fn(blk);
    }).join('');
    sectionHtmls.push(
      '<section class="sg-section" id="' + secAnchor + '">' +
      '<h3 class="sg-sechead"><span class="sg-navnum">' + ('0' + (si + 1)).slice(-2) + '</span>' +
      _esc(label) + '</h3>' + body + '</section>'
    );
  });

  return '<style>' +
    '.sg-layout{display:flex;gap:36px;align-items:flex-start;margin:1.4rem auto;max-width:90%;}' +
    '.sg-nav{flex:0 0 190px;position:sticky;top:24px;display:flex;flex-direction:column;gap:14px;' +
    'border-right:1px solid var(--border,#e0e0e0);padding-right:18px;max-height:calc(100vh - 48px);overflow-y:auto;}' +
    '.sg-navsection{display:flex;flex-direction:column;gap:2px;}' +
    '.sg-navhead{display:flex;align-items:baseline;gap:8px;color:var(--text,#1f2328);' +
    'text-decoration:none;font-weight:600;font-size:.86rem;padding:4px 0;}' +
    '.sg-navnum{font-family:ui-monospace,monospace;font-size:.68rem;color:var(--accent-2,var(--accent,#1a73e8));}' +
    '.sg-sub{display:block;color:var(--text-muted,#5f6368);text-decoration:none;font-size:.78rem;' +
    'padding:3px 0 3px 22px;}' +
    '.sg-sub:hover{color:var(--accent,#1a73e8);}' +
    '.sg-sechead{display:flex;align-items:baseline;gap:10px;font-size:1.3rem;font-weight:700;' +
    'color:var(--text,#1f2328);border-bottom:1px solid var(--border,#e0e0e0);' +
    'padding-bottom:10px;margin:0 0 22px;}' +
    '.sg-section{margin-bottom:64px;scroll-margin-top:24px;flex:1 1 auto;min-width:0;}' +
    '@media (max-width:860px){.sg-layout{flex-direction:column;}' +
    '.sg-nav{position:static;flex-direction:row;flex-wrap:wrap;border-right:none;' +
    'border-bottom:1px solid var(--border,#e0e0e0);padding:0 0 14px;max-height:none;width:100%;}}' +
    '.sg-sub.sg-active-link{color:var(--accent,#1a73e8);font-weight:700;}' +
    'a.sg-active-link{color:var(--accent,#1a73e8);font-weight:700;}' +
    'tr:has(a.sg-active-link){background:var(--surface-2,#f8f9fa);}' +
    '</style>' +
    '<div class="sg-layout"><nav class="sg-nav">' + navItems.join('') + '</nav>' +
    '<div>' + sectionHtmls.join('') + '</div></div>' +
    _scrollspyScript(spyIds);
};
