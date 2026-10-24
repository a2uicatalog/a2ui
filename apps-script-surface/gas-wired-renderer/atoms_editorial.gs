/**
 * Editorial atom renderers for a2ui.
 * Byte-for-byte twins of the Python web_article renderers (I136: these ten had no Apps Script renderer).
 */

_RENDERERS['verdict_checklist'] = function(b) {
  b = _c136Obj(b);
  var title = _esc(_c136Txt(b.title));
  var rawItems = _c136List(b.items, 200);
  var verdictStyle = {
    'yes':     { mark: '\u2713', bg: '#e6f4ea', fg: '#34a853' },
    'partial': { mark: '~', bg: '#fef7e0', fg: '#e37400' },
    'no':      { mark: '\u2717', bg: '#fce8e6', fg: '#c5221f' }
  };
  var rows = '';
  for (var i = 0; i < rawItems.length; i++) {
    var rawIt = rawItems[i];
    if (!rawIt || typeof rawIt !== 'object' || Array.isArray(rawIt)) {
      continue;
    }
    var it = _c136Obj(rawIt);
    var v = _c136Txt(it.verdict).trim().toLowerCase();
    var style = verdictStyle.hasOwnProperty(v) ? verdictStyle[v] : verdictStyle['no'];
    var label = _md_inline(_c136Txt(it.label));
    var noteTxt = _c136Txt(it.note);
    var note = noteTxt ? _md_inline(noteTxt) : '';
    var noteHtml = note ? '<div style="color:#5f6368;font-size:0.85rem;margin-top:2px;">' + note + '</div>' : '';
    rows += '<li style="display:flex;gap:12px;align-items:flex-start;padding:8px 0;border-bottom:1px solid #e8eaed;">' +
      '<span style="flex:0 0 22px;height:22px;border-radius:50%;background:' + style.bg + ';color:' + style.fg + ';' +
      'display:flex;align-items:center;justify-content:center;font-weight:700;font-size:0.8rem;">' +
      style.mark + '</span>' +
      '<div style="line-height:1.5;"><span style="color:#202124;">' + label + '</span>' +
      noteHtml + '</div></li>';
  }
  var titleHtml = title ? '<div style="font-weight:700;margin-bottom:8px;color:#202124;">' + title + '</div>' : '';
  return '<div style="margin:1.5rem 0;">' + titleHtml +
    '<ul style="list-style:none;padding:0;margin:0;">' + rows + '</ul></div>';
};

_RENDERERS['constraint_fix_triad'] = function(b) {
  b = _c136Obj(b);
  var constraint = _md_inline(_c136Txt(b.constraint));
  var breaks = _md_inline(_c136Txt(b.breaks));
  var fix = _md_inline(_c136Txt(b.fix));
  function renderRow(label, color, bg, text) {
    return '<div style="display:flex;gap:10px;padding:10px 14px;background:' + bg + ';' +
      'border-left:3px solid ' + color + ';margin-bottom:6px;border-radius:0 6px 6px 0;">' +
      '<span style="font-weight:700;color:' + color + ';flex:0 0 auto;font-size:0.8rem;' +
      'text-transform:uppercase;letter-spacing:0.04em;padding-top:2px;">' + label + '</span>' +
      '<span style="color:#202124;line-height:1.5;">' + text + '</span></div>';
  }
  return '<div style="margin:1.5rem 0;">' +
    renderRow('Constraint', '#c5221f', '#fce8e6', constraint) +
    renderRow('Breaks', '#e37400', '#fef7e0', breaks) +
    renderRow('Fix', '#137333', '#e6f4ea', fix) +
    '</div>';
};

_RENDERERS['incident_finding'] = function(b) {
  b = _c136Obj(b);
  var headline = _md_inline(_c136Txt(b.headline));
  var detail = _md_inline(_c136Txt(b.detail));
  var synthesisTxt = _c136Txt(b.synthesis);
  var synthesis = synthesisTxt ? _md_inline(synthesisTxt) : '';
  var synthesisHtml = synthesis ?
    '<div style="margin-top:12px;padding:10px 14px;background:#e8f0fe;border-radius:6px;border-radius:var(--a2ui-radius-sm,6px);' +
    'color:#1a73e8;font-size:0.9rem;line-height:1.5;">' + synthesis + '</div>' : '';
  return '<div style="margin:1.5rem 0;padding:14px 18px;border-left:3px solid #ea4335;' +
    'background:#fafafa;border-radius:0 8px 8px 0;">' +
    '<div style="font-weight:700;color:#202124;margin-bottom:6px;">' + headline + '</div>' +
    '<div style="color:#3c4043;line-height:1.6;">' + detail + '</div>' +
    synthesisHtml + '</div>';
};

_RENDERERS['wrong_vs_right'] = function(b) {
  b = _c136Obj(b);
  var title = _esc(_c136Txt(b.title));
  var rawPairs = _c136List(b.pairs, 200);
  var rows = '';
  for (var i = 0; i < rawPairs.length; i++) {
    var rawP = rawPairs[i];
    if (!rawP || typeof rawP !== 'object' || Array.isArray(rawP)) {
      continue;
    }
    var p = _c136Obj(rawP);
    var wrong = _md_inline(_c136Txt(p.wrong));
    var right = _md_inline(_c136Txt(p.right));
    rows += '<li style="display:flex;gap:10px;align-items:center;padding:6px 0;font-size:0.92rem;">' +
      '<span style="color:#c5221f;text-decoration:line-through;text-decoration-color:#ea4335;">' +
      wrong + '</span>' +
      '<span style="color:#9aa0a6;">\u2192</span>' +
      '<span style="color:#137333;font-weight:600;">' + right + '</span></li>';
  }
  var titleHtml = title ? '<div style="font-weight:700;margin-bottom:8px;color:#202124;">' + title + '</div>' : '';
  return '<div style="margin:1.5rem 0;">' + titleHtml +
    '<ul style="list-style:none;padding:0;margin:0;">' + rows + '</ul></div>';
};

_RENDERERS['agent_demo_card'] = function(b) {
  b = _c136Obj(b);
  var name = _esc(_c136Txt(b.name));
  var description = _md_inline(_c136Txt(b.description));
  var rawPrimitives = _c136List(b.primitives_used, 100);
  var chips = '';
  for (var i = 0; i < rawPrimitives.length; i++) {
    var p = _c136Txt(rawPrimitives[i]);
    if (p) {
      chips += '<span style="display:inline-block;background:#e8f0fe;color:#1558b4;font-size:0.78rem;' +
        'font-family:ui-monospace,\'SF Mono\',Consolas,monospace;padding:3px 10px;border-radius:12px;border-radius:var(--a2ui-radius,12px);' +
        'margin:3px 4px 0 0;">' + _esc(p) + '</span>';
    }
  }
  return '<div style="margin:1.5rem 0;padding:16px 20px;border:1px solid #e8eaed;border-radius:10px;">' +
    '<div style="font-weight:700;color:#202124;margin-bottom:4px;">' + name + '</div>' +
    '<div style="color:#5f6368;line-height:1.5;margin-bottom:10px;">' + description + '</div>' +
    '<div>' + chips + '</div></div>';
};

_RENDERERS['wishlist_panel'] = function(b) {
  b = _c136Obj(b);
  var title = _esc(_c136Txt(b.title));
  var rawGroups = _c136List(b.groups, 50);
  var groupHtml = '';
  for (var i = 0; i < rawGroups.length; i++) {
    var rawG = rawGroups[i];
    if (!rawG || typeof rawG !== 'object' || Array.isArray(rawG)) {
      continue;
    }
    var g = _c136Obj(rawG);
    var heading = _esc(_c136Txt(g.heading));
    var rawItems = _c136List(g.items, 100);
    var li = '';
    for (var j = 0; j < rawItems.length; j++) {
      var s = _c136Txt(rawItems[j]);
      if (!s) {
        continue;
      }
      var idx = s.indexOf(':');
      var content = '';
      if (idx > 0 && idx <= 80 && (idx === s.length - 1 || s.charAt(idx + 1) === ' ' || s.charAt(idx + 1) === '\t' || s.charAt(idx + 1) === '\n')) {
        content = '<strong style="color:#202124;">' + _md_inline(s.substring(0, idx)) + ':</strong>' + _md_inline(s.substring(idx + 1));
      } else {
        content = _md_inline(s);
      }
      li += '<li style="margin-bottom:6px;line-height:1.5;color:#3c4043;">' + content + '</li>';
    }
    groupHtml += '<div style="margin-bottom:14px;">' +
      '<div style="font-weight:700;font-size:0.85rem;text-transform:uppercase;' +
      'letter-spacing:0.04em;color:#5f6368;margin-bottom:6px;">' + heading + '</div>' +
      '<ul style="margin:0;padding-left:1.2rem;">' + li + '</ul></div>';
  }
  var titleHtml = title ? '<div style="font-weight:700;font-size:1.05rem;margin-bottom:12px;color:#202124;">' + title + '</div>' : '';
  return '<div style="margin:1.5rem 0;">' + titleHtml + groupHtml + '</div>';
};

_RENDERERS['trace_step'] = function(b) {
  b = _c136Obj(b);
  var stepNumber = _esc(_c136Txt(b.step_number));
  var title = _md_inline(_c136Txt(b.title));
  var body = _md_inline(_c136Txt(b.body));
  var code = _c136Txt(b.code);
  var codeHtml = code ?
    '<pre style="background:#0d1117;color:#cdd6f4;padding:12px 14px;border-radius:6px;border-radius:var(--a2ui-radius-sm,6px);' +
    'font-family:ui-monospace,\'SF Mono\',Consolas,monospace;font-size:0.85rem;' +
    'overflow-x:auto;margin-top:8px;">' + _esc(code) + '</pre>' : '';
  return '<div style="display:flex;gap:16px;margin:1.2rem 0;align-items:flex-start;">' +
    '<span style="flex:0 0 28px;height:28px;background:#1a73e8;color:white;border-radius:50%;' +
    'display:flex;align-items:center;justify-content:center;font-weight:700;font-size:0.85rem;">' +
    stepNumber + '</span>' +
    '<div style="flex:1;padding-top:3px;"><strong style="color:#202124;">' + title + '</strong>' +
    '<div style="color:#3c4043;line-height:1.6;margin-top:4px;">' + body + '</div>' + codeHtml + '</div></div>';
};

_RENDERERS['stat_inline_badge'] = function(b) {
  b = _c136Obj(b);
  var value = _esc(_c136Txt(b.value));
  var label = _esc(_c136Txt(b.label));
  return '<span style="display:inline-flex;align-items:baseline;gap:5px;background:#e8f0fe;' +
    'padding:3px 12px;border-radius:12px;border-radius:var(--a2ui-radius,12px);margin:0 2px;">' +
    '<strong style="color:#1a73e8;font-size:1.02em;">' + value + '</strong>' +
    '<span style="color:#3c4043;font-size:0.88em;">' + label + '</span></span>';
};

_RENDERERS['problem_chapter'] = function(b) {
  b = _c136Obj(b);
  var number = _esc(_c136Txt(b.number));
  var headline = _md_inline(_c136Txt(b.headline));
  var body = _md_inline(_c136Txt(b.body));
  var angleLabelTxt = _c136Txt(b.angle_label) || 'Takeaway';
  var angleLabel = _esc(angleLabelTxt);
  var angleText = _md_inline(_c136Txt(b.angle_text));
  return '<div style="margin:2rem 0;">' +
    '<div style="font-size:0.8rem;font-weight:700;color:#9aa0a6;text-transform:uppercase;' +
    'letter-spacing:0.06em;margin-bottom:4px;">Problem ' + number + '</div>' +
    '<h3 style="margin:0 0 10px;color:#202124;">' + headline + '</h3>' +
    '<div style="color:#3c4043;line-height:1.7;">' + body + '</div>' +
    '<div style="margin-top:12px;padding:10px 14px;background:#e6f4ea;border-radius:6px;' +
    'color:#137333;font-size:0.9rem;line-height:1.5;">' +
    '<strong>' + angleLabel + ':</strong> ' + angleText + '</div></div>';
};

_RENDERERS['resource_link_row'] = function(b) {
  b = _c136Obj(b);
  var label = _esc(_c136Txt(b.label));
  var rawUrl = _c136Txt(b.url);
  var noteTxt = _c136Txt(b.note);
  var note = noteTxt ? _md_inline(noteTxt) : '';
  var noteHtml = note ? '<span style="color:#5f6368;font-size:0.85rem;margin-left:8px;">' + note + '</span>' : '';
  var linkHtml = '';
  if (_hrefIsSafe(rawUrl)) {
    rawUrl = _hrefIsSafe(rawUrl);
    linkHtml = '<a href="' + _esc(rawUrl) + '" target="_blank" rel="noopener noreferrer" ' +
      'style="color:#1a73e8;font-weight:600;text-decoration:none;">' + label + '</a>';
  } else {
    linkHtml = '<span style="font-weight:600;">' + label + '</span>';
  }
  return '<div style="display:flex;align-items:baseline;padding:8px 0;border-bottom:1px solid #e8eaed;">' +
    linkHtml + noteHtml + '</div>';
};
