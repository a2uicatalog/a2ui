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
// Layout CSS + JS: generated from the Python twin's _PLATE_CSS / _PLATE_JS (renderers/web_article.py) -- keep them identical.
var _PP_CSS = "\n" +
  "<style>\n" +
  "/* Follows the HOST page's own theme tokens (--text/--surface/--accent/...,\n" +
  "   the indigo-277/cyan-202 pair) rather than a standalone palette — the\n" +
  "   parchment/codex look this atom started from read as a beige island next\n" +
  "   to the rest of the site (design feedback, 2026-07-25). */\n" +
  ".pp-wrap{margin:1.4rem 0;}\n" +
  ".pp-head{display:flex;align-items:baseline;gap:14px;margin-bottom:4px;flex-wrap:wrap;}\n" +
  ".pp-head h4{font-size:1.4rem;font-weight:700;margin:0;color:var(--text,#1f2328);}\n" +
  ".pp-kind{font-family:ui-monospace,\"SF Mono\",Menlo,Consolas,monospace;font-size:.68rem;\n" +
  "  letter-spacing:.1em;text-transform:uppercase;color:var(--accent-2,var(--accent,#1a73e8));\n" +
  "  border:1px solid var(--accent-2,var(--accent,#1a73e8));border-radius:3px;padding:2px 8px;}\n" +
  ".pp-chat{display:inline-flex;align-items:center;gap:5px;font-size:.72rem;font-weight:600;\n" +
  "  border-radius:999px;padding:3px 10px 3px 8px;cursor:help;}\n" +
  ".pp-chat-yes{color:#1a7f37;background:#dafbe1;}\n" +
  ".pp-chat-partial{color:#9a6700;background:#fff3c4;}\n" +
  ".pp-chat-no{color:var(--text-muted,#5f6368);background:var(--surface,#f1f3f5);}\n" +
  ":root[data-theme=\"dark\"] .pp-chat-yes{color:#7ee2a8;background:#0d2818;}\n" +
  ":root[data-theme=\"dark\"] .pp-chat-partial{color:#e3b341;background:#2b2111;}\n" +
  "@media (prefers-color-scheme:dark){:root:not([data-theme=\"light\"]) .pp-chat-yes{color:#7ee2a8;background:#0d2818;}\n" +
  ":root:not([data-theme=\"light\"]) .pp-chat-partial{color:#e3b341;background:#2b2111;}}\n" +
  ".pp-caption{color:var(--text-muted,#5f6368);max-width:64ch;margin:6px 0 18px;font-size:.94rem;}\n" +
  ".pp-toggles{display:flex;gap:6px;margin-bottom:14px;flex-wrap:wrap;}\n" +
  ".pp-toggles input{position:absolute;opacity:0;width:1px;height:1px;margin:0;}\n" +
  ".pp-toggles label{font-family:ui-monospace,monospace;font-size:.72rem;padding:6px 14px;\n" +
  "  border:1px solid var(--border,#e0e0e0);border-radius:999px;cursor:pointer;color:var(--text-muted,#5f6368);\n" +
  "  transition:all .15s;}\n" +
  ".pp-toggles input:checked + label{color:var(--accent,#1a73e8);border-color:var(--accent,#1a73e8);font-weight:600;}\n" +
  ".pp-state{display:none;}\n" +
  ".pp-plate{display:flex;align-items:flex-start;gap:0;background:var(--surface-2,#f8f9fa);\n" +
  "  border:1px solid var(--border,#e0e0e0);border-radius:10px;padding:24px;position:relative;}\n" +
  ".pp-imgwrap{position:relative;flex:0 0 auto;}\n" +
  ".pp-imgwrap img{display:block;width:100%;height:auto;border:1px solid var(--border,#e0e0e0);border-radius:8px;}\n" +
  ".pp-imgwrap svg{position:absolute;inset:0;width:100%;height:100%;overflow:visible;}\n" +
  ".pp-pin{position:absolute;transform:translate(-50%,-50%);width:22px;height:22px;border-radius:50%;\n" +
  "  background:var(--surface,#fff);border:1.4px solid var(--accent,#1a73e8);color:var(--accent,#1a73e8);\n" +
  "  font-family:ui-monospace,monospace;font-size:.66rem;font-weight:700;display:flex;\n" +
  "  align-items:center;justify-content:center;box-shadow:0 1px 2px rgba(0,0,0,.25);}\n" +
  ".pp-pin-advance{width:30px;height:30px;background:var(--accent,#1a73e8);color:var(--surface,#fff);\n" +
  "  cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,.35);transition:transform .15s;}\n" +
  ".pp-pin-advance:hover{transform:translate(-50%,-50%) scale(1.12);}\n" +
  ".pp-badge{font-family:ui-monospace,monospace;font-size:.6rem;font-weight:700;letter-spacing:.02em;\n" +
  "  border-radius:999px;padding:1px 7px;margin-left:6px;text-transform:uppercase;vertical-align:middle;}\n" +
  ".pp-badge-round-trip{color:#9a3412;background:#ffedd5;}\n" +
  ".pp-badge-client-only{color:#1a7f37;background:#dafbe1;}\n" +
  ":root[data-theme=\"dark\"] .pp-badge-round-trip{color:#fdba74;background:#431407;}\n" +
  ":root[data-theme=\"dark\"] .pp-badge-client-only{color:#7ee2a8;background:#0d2818;}\n" +
  "@media (prefers-color-scheme:dark){:root:not([data-theme=\"light\"]) .pp-badge-round-trip{color:#fdba74;background:#431407;}\n" +
  ":root:not([data-theme=\"light\"]) .pp-badge-client-only{color:#7ee2a8;background:#0d2818;}}\n" +
  ".pp-repo{font-family:ui-monospace,monospace;font-size:.72rem;color:var(--text-muted,#5f6368);\n" +
  "  text-decoration:none;border:1px solid var(--border,#e0e0e0);border-radius:999px;padding:2px 10px;\n" +
  "  margin-left:auto;}\n" +
  ".pp-repo:hover{color:var(--accent,#1a73e8);border-color:var(--accent,#1a73e8);}\n" +
  ".pp-repo-placeholder{opacity:.55;cursor:not-allowed;}\n" +
  ".pp-repo-placeholder:hover{color:var(--text-muted,#5f6368);border-color:var(--border,#e0e0e0);}\n" +
  ".pp-gap-side{flex:0 0 64px;position:relative;}\n" +
  ".pp-gap-side svg{position:absolute;top:0;left:0;}\n" +
  ".pp-labels-side{flex:1 1 0;position:relative;min-width:200px;}\n" +
  ".pp-label{position:absolute;left:0;right:0;top:0;padding-left:2px;visibility:hidden;}\n" +
  ".pp-label.pp-placed{visibility:visible;}\n" +
  ".pp-label .pp-num{font-family:ui-monospace,monospace;color:var(--accent,#1a73e8);font-weight:700;\n" +
  "  font-size:.72rem;margin-right:6px;}\n" +
  ".pp-label .pp-field{font-family:ui-monospace,monospace;font-size:.72rem;color:var(--accent-2,var(--accent,#1a73e8));\n" +
  "  display:block;letter-spacing:.02em;margin-bottom:2px;overflow-wrap:anywhere;}\n" +
  ".pp-label .pp-note{font-size:.86rem;color:var(--text,#1f2328);display:block;line-height:1.35;overflow-wrap:anywhere;}\n" +
  ".pp-label .pp-note.pp-chrome{color:var(--text-muted,#5f6368);font-style:italic;}\n" +
  "/* Left column mirrors the right: text hugs the image side (right edge of\n" +
  "   this column), padding switches sides to match -- everything else\n" +
  "   (num/field/note styling) is shared. */\n" +
  ".pp-labels-side.left .pp-label{left:auto;right:0;padding-left:0;padding-right:2px;text-align:right;}\n" +
  "@media (max-width:860px){\n" +
  "  .pp-plate{flex-direction:column;}\n" +
  "  .pp-gap-side{display:none;}\n" +
  "  .pp-labels-side{min-width:0;position:static;}\n" +
  "  .pp-labels-side.left .pp-label{text-align:left;}\n" +
  "  .pp-label{position:static !important;margin:14px 0;padding-left:14px;padding-right:0;\n" +
  "    border-left:2px solid var(--accent,#1a73e8);visibility:visible;}\n" +
  "}\n" +
  "<\/style>\n" +
  "";

var _PP_JS = "\n" +
  "<script>\n" +
  "(function(){\n" +
  "  if (window.__a2uiPlateLayout) return;\n" +
  "  window.__a2uiPlateLayout = function(root) {\n" +
  "    if (window.matchMedia('(max-width:860px)').matches) return;\n" +
  "    (root || document).querySelectorAll('.pp-plate').forEach(function(plate){\n" +
  "      var imgwrap = plate.querySelector('.pp-imgwrap');\n" +
  "      var pins = [].slice.call(plate.querySelectorAll('.pp-pin'));\n" +
  "      if (!pins.length) return;\n" +
  "      var plateRect = plate.getBoundingClientRect();\n" +
  "      // Shared lookup by data-pin-idx (2026-09-11, two-sided layout): a\n" +
  "      // label's line always targets ITS OWN pin's real position, however\n" +
  "      // many sides exist and whichever one that label landed in --\n" +
  "      // replaces the old same-index-both-arrays assumption, which broke\n" +
  "      // the moment there could be two independent label columns instead\n" +
  "      // of one.\n" +
  "      var pinYByIdx = {};\n" +
  "      pins.forEach(function(p){\n" +
  "        var r = p.getBoundingClientRect();\n" +
  "        pinYByIdx[p.getAttribute('data-pin-idx')] = (r.top + r.height / 2) - plateRect.top;\n" +
  "      });\n" +
  "\n" +
  "      ['left', 'right'].forEach(function(side){\n" +
  "        var labelsBox = plate.querySelector('.pp-labels-side.' + side);\n" +
  "        var gap = plate.querySelector('.pp-gap-side[data-side=\"' + side + '\"]');\n" +
  "        if (!labelsBox || !gap) return; // that side has zero pins -- collapsed server-side, nothing to lay out\n" +
  "        var labels = [].slice.call(labelsBox.querySelectorAll('.pp-label'));\n" +
  "        if (!labels.length) return;\n" +
  "        var pinYs = labels.map(function(l){ return pinYByIdx[l.getAttribute('data-pin-idx')]; });\n" +
  "\n" +
  "        labels.forEach(function(l){ l.style.top = '0px'; l.style.visibility = 'hidden'; });\n" +
  "        var heights = labels.map(function(l){ return l.getBoundingClientRect().height; });\n" +
  "        // Stack in CURRENT pin-Y order, not DOM/original-index order\n" +
  "        // (fixed 2026-09-11, same reasoning as the shared lookup above --\n" +
  "        // a dragged/repositioned pin must not leave its label stranded in\n" +
  "        // its old rank). Sort by actual pinY, scatter computed tops back\n" +
  "        // to each label's own original index.\n" +
  "        var GAP = 14;\n" +
  "        var order = pinYs.map(function(_, i){ return i; });\n" +
  "        order.sort(function(a, b){ return pinYs[a] - pinYs[b]; });\n" +
  "        var tops = new Array(pinYs.length);\n" +
  "        var prevBottom = null;\n" +
  "        order.forEach(function(idx){\n" +
  "          var top = pinYs[idx] - heights[idx] / 2;\n" +
  "          if (prevBottom !== null) top = Math.max(top, prevBottom + GAP);\n" +
  "          tops[idx] = top;\n" +
  "          prevBottom = top + heights[idx];\n" +
  "        });\n" +
  "        tops.forEach(function(top, i){\n" +
  "          labels[i].style.top = top + 'px';\n" +
  "          labels[i].style.visibility = 'visible';\n" +
  "          labels[i].classList.add('pp-placed');\n" +
  "        });\n" +
  "        var imgRect = imgwrap.getBoundingClientRect();\n" +
  "        var totalH = Math.max(imgRect.height, prevBottom);\n" +
  "        labelsBox.style.minHeight = totalH + 'px';\n" +
  "        gap.style.minHeight = totalH + 'px';\n" +
  "\n" +
  "        var gapRect = gap.getBoundingClientRect();\n" +
  "        var svgNS = 'http://www.w3.org/2000/svg';\n" +
  "        var existing = gap.querySelector('svg');\n" +
  "        if (existing) existing.remove();\n" +
  "        var svg = document.createElementNS(svgNS, 'svg');\n" +
  "        svg.setAttribute('width', gapRect.width);\n" +
  "        svg.setAttribute('height', totalH);\n" +
  "        svg.setAttribute('viewBox', '0 0 ' + gapRect.width + ' ' + totalH);\n" +
  "        // Mirrored for the left side: starts at the gap's RIGHT edge\n" +
  "        // (touching the image's LEFT edge) instead of its left edge.\n" +
  "        var fromX = side === 'left' ? gapRect.width : 0;\n" +
  "        var toX = side === 'left' ? 0 : gapRect.width;\n" +
  "        var nearLabelX = side === 'left' ? 6 : gapRect.width - 6;\n" +
  "        var midX = gapRect.width * 0.5;\n" +
  "        pinYs.forEach(function(y, i){\n" +
  "          var labelCenterY = tops[i] + heights[i] / 2;\n" +
  "          var path = document.createElementNS(svgNS, 'path');\n" +
  "          path.setAttribute('d', 'M' + fromX.toFixed(1) + ',' + y.toFixed(1) +\n" +
  "            ' L' + midX.toFixed(1) + ',' + y.toFixed(1) +\n" +
  "            ' L' + nearLabelX.toFixed(1) + ',' + labelCenterY.toFixed(1) +\n" +
  "            ' L' + toX.toFixed(1) + ',' + labelCenterY.toFixed(1));\n" +
  "          path.setAttribute('fill', 'none');\n" +
  "          path.setAttribute('stroke', 'var(--accent,#1a73e8)');\n" +
  "          path.setAttribute('stroke-width', '1');\n" +
  "          path.setAttribute('opacity', '0.75');\n" +
  "          svg.appendChild(path);\n" +
  "          var dot = document.createElementNS(svgNS, 'circle');\n" +
  "          dot.setAttribute('cx', fromX);\n" +
  "          dot.setAttribute('cy', y.toFixed(1));\n" +
  "          dot.setAttribute('r', 2.4);\n" +
  "          dot.setAttribute('fill', 'var(--accent,#1a73e8)');\n" +
  "          svg.appendChild(dot);\n" +
  "        });\n" +
  "        gap.appendChild(svg);\n" +
  "      });\n" +
  "    });\n" +
  "  };\n" +
  "  function runAll(){ requestAnimationFrame(function(){ window.__a2uiPlateLayout(document); }); }\n" +
  "  // Wait for the WHOLE document to finish parsing before the first run —\n" +
  "  // querying '.pp-imgwrap img' from whichever plate's own inline <script>\n" +
  "  // happens to run first only sees plates parsed so far. An early decode()\n" +
  "  // resolving mid-parse raced ahead and hit a later plate's '.pp-labels'\n" +
  "  // before that div existed, throwing null on querySelectorAll (2026-07-25).\n" +
  "  if (document.readyState === 'loading') {\n" +
  "    document.addEventListener('DOMContentLoaded', runAll);\n" +
  "  } else {\n" +
  "    runAll();\n" +
  "  }\n" +
  "  window.addEventListener('load', runAll); // catches any images that were still loading\n" +
  "  document.addEventListener('change', function(e){\n" +
  "    if (e.target && e.target.matches('.pp-toggles input')) runAll();\n" +
  "  });\n" +
  "  var t;\n" +
  "  window.addEventListener('resize', function(){ clearTimeout(t); t = setTimeout(runAll, 150); });\n" +
  "})();\n" +
  "<\/script>\n" +
  "";

var _ppCounter = 0;

_RENDERERS['primitive_plate'] = function(b) {
  _ppCounter += 1;
  var uid = 'pp' + _ppCounter;
  var title = _esc(b.title || '');
  var kind = _esc(b.kind || '');
  var caption = b.caption || '';
  var width = (b.width !== undefined && b.width !== null) ? b.width : 460;
  var states = (Array.isArray(b.states) ? b.states : []).filter(function(s) { return s && typeof s === 'object'; });
  if (!states.length) return '';

  var nStates = states.length;
  function pinNum(v) { var n = Number(v); return isFinite(n) ? n : 0; }

  function stateBody(state, idx) {
    var pins = state.pins || [];
    var img = state.image || '';

    var lines = '';
    for (var i = 0; i < pins.length; i++) {
      var p = pins[i];
      if (p.connector === 'continuous') {
        var px = (p.x !== undefined && p.x !== null) ? p.x : 0;
        var py = (p.y !== undefined && p.y !== null) ? p.y : 0;
        lines += '<line x1="' + pinNum(px) + '" y1="' + pinNum(py) + '" x2="100" y2="' + pinNum(py) + '" ' +
          'stroke="var(--accent,#1a73e8)" stroke-width="0.4"/>';
      }
    }

    var orderIndices = [];
    for (var i = 0; i < pins.length; i++) {
      orderIndices.push(i);
    }
    orderIndices.sort(function(a, b) {
      var ya = (pins[a].y !== undefined && pins[a].y !== null) ? pins[a].y : 0;
      var yb = (pins[b].y !== undefined && pins[b].y !== null) ? pins[b].y : 0;
      return ya - yb;
    });

    var displayNum = {};
    for (var n = 0; n < orderIndices.length; n++) {
      displayNum[orderIndices[n]] = n + 1;
    }

    var markers = '';
    for (var i = 0; i < pins.length; i++) {
      var p = pins[i];
      var advance = p.advance && (idx + 1 < nStates);
      var advCls = advance ? ' pp-pin-advance' : '';
      var advAttr = advance ?
        (' role="button" tabindex="0" onclick="var r=document.getElementById(\'' + uid + '_t' + (idx + 1) + '\');' +
         'if(r){r.checked=true;r.dispatchEvent(new Event(\'change\',{bubbles:true}));}"') : '';
      var px = (p.x !== undefined && p.x !== null) ? p.x : 0;
      var py = (p.y !== undefined && p.y !== null) ? p.y : 0;
      markers += '<div class="pp-pin' + advCls + '" data-pin-idx="' + _esc(String(i)) + '" ' +
        'style="top:' + pinNum(py) + '%;left:' + pinNum(px) + '%;"' + advAttr + '>' +
        displayNum[i] + '</div>';
    }

    var leftLabels = [];
    var rightLabels = [];
    for (var i = 0; i < pins.length; i++) {
      var p = pins[i];
      var chromeCls = p.chrome ? ' pp-chrome' : '';
      var field = _markdownToHtml(p.field || '');
      var note = _markdownToHtml(p.note || '');
      var badge = p.badge;
      var badgeHtml = badge ? ('<span class="pp-badge pp-badge-' + _esc(badge) + '">' + _esc(String(badge).replace(/-/g, ' ')) + '</span>') : '';
      var fieldSize = p.field_size ? _safe_css(p.field_size, '') : '';
      var fieldStyle = fieldSize ? (' style="font-size:' + _esc(fieldSize) + '"') : '';
      var noteSize = p.note_size ? _safe_css(p.note_size, '') : '';
      var noteStyle = noteSize ? (' style="font-size:' + _esc(noteSize) + '"') : '';
      var labelHtml = '<div class="pp-label" data-pin-idx="' + _esc(String(i)) + '">' +
        '<span class="pp-field"' + fieldStyle + '>' + field + badgeHtml + '</span>' +
        '<span class="pp-note' + chromeCls + '"' + noteStyle + '><span class="pp-num">' + displayNum[i] + '.</span> ' + note + '</span>' +
        '</div>';

      var px = (p.x !== undefined && p.x !== null) ? p.x : 0;
      if (px < 50) {
        leftLabels.push(labelHtml);
      } else {
        rightLabels.push(labelHtml);
      }
    }

    var leftSideHtml = leftLabels.length ? (
      '<div class="pp-labels-side left">' + leftLabels.join('') + '</div>' +
      '<div class="pp-gap-side" data-side="left"></div>'
    ) : '';

    var rightSideHtml = rightLabels.length ? (
      '<div class="pp-gap-side" data-side="right"></div>' +
      '<div class="pp-labels-side right">' + rightLabels.join('') + '</div>'
    ) : '';

    var active = (idx === 0) ? ' active' : '';
    var display = (idx === 0) ? 'display:block;' : 'display:none;';
    var stateK = state.id || state.label || state.name || ('State ' + (idx + 1));
    var altText = state.alt ? _esc(state.alt) : (title + ' — captured UI state');

    return '<div data-cb="node" data-key="' + _esc(String(stateK)) + '" class="pp-state' + active + '" data-state="' + uid + '_' + _esc(String(idx)) + '" style="' + display + '">' +
      '<div class="pp-plate">' +
      leftSideHtml +
      '<div class="pp-imgwrap" style="width:' + width + 'px;">' +
      '<img src="' + _esc(img) + '" alt="' + altText + '">' +
      '<svg viewBox="0 0 100 100" preserveAspectRatio="none">' + lines + '</svg>' +
      markers +
      '</div>' +
      rightSideHtml +
      '</div>' +
      '</div>';
  }

  var togglesHtml = '';
  if (states.length > 1) {
    var pairs = '';
    for (var i = 0; i < states.length; i++) {
      var s = states[i];
      var stateK = s.id || s.label || s.name || ('State ' + (i + 1));
      pairs += '<input type="radio" name="' + uid + '_toggle" id="' + uid + '_t' + _esc(String(i)) + '"' +
        (i === 0 ? ' checked' : '') + ' ' +
        'onchange="document.querySelectorAll(\'[data-state^=\\\'' + uid + '_\\\']\').forEach(function(el){' +
        'el.style.display = (el.dataset.state === \'' + uid + '_' + _esc(String(i)) + '\') ? \'block\' : \'none\';});">' +
        '<label data-cb="label" data-key="' + _esc(String(stateK)) + '" for="' + uid + '_t' + _esc(String(i)) + '">' + _esc(s.label || ('State ' + (i + 1))) + '</label>';
    }
    togglesHtml = '<div class="pp-toggles">' + pairs + '</div>';
  }

  var statesHtml = '';
  for (var i = 0; i < states.length; i++) {
    statesHtml += stateBody(states[i], i);
  }

  var captionHtml = caption ? ('<p class="pp-caption">' + _markdownToHtml(caption) + '</p>') : '';
  var kindHtml = kind ? ('<span class="pp-kind">' + kind + '</span>') : '';

  var equiv = b.equivalent_in || b.chat_equivalent;
  var chatHtml = '';
  if (equiv) {
    var status = equiv.status || 'no';
    var icon = ({yes: '✓', partial: '~', no: '✗'})[status] || '?';
    var cls = 'pp-chat-' + _esc(status);
    var surface = equiv.surface ? _esc(equiv.surface) : 'Chat Cards v2';
    var note = equiv.note ? _esc(equiv.note) : '';
    var titleAttr = note ? (' title="' + note + '"') : '';
    chatHtml = '<span class="pp-chat ' + cls + '"' + titleAttr + '>' + surface + ' ' + icon + '</span>';
  }

  var repoHtml = '';
  if (b.repo_url !== undefined && b.repo_url !== null) {
    var repoUrl = b.repo_url || '';
    var placeholder = !repoUrl;
    var href = repoUrl || '#';
    var placeholderCls = placeholder ? ' pp-repo-placeholder' : '';
    var repoTitleAttr = placeholder ? ' title="Repo not yet public"' : '';
    repoHtml = '<a class="pp-repo' + placeholderCls + '" href="' + _esc(href) + '" target="_blank" rel="noopener noreferrer"' + repoTitleAttr + '>GitHub ↗</a>';
  }

  return _PP_CSS + _PP_JS +
    '<div class="pp-wrap" id="' + _esc(b.id || uid) + '">' +
    '<div class="pp-head"><h4>' + title + '</h4>' + kindHtml + chatHtml + repoHtml + '</div>' +
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
    'window.__a2uiSpyIds = (window.__a2uiSpyIds || []).concat(' + _jsJson(ids) + ');' +
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
    '.sg-nav{flex:0 0 190px;position:sticky;top:70px;display:flex;flex-direction:column;gap:14px;' +
    'border-right:1px solid var(--border,#e0e0e0);padding-right:18px;max-height:calc(100vh - 94px);overflow-y:auto;}' +
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
