/**
 * Google Apps Script Web App Renderer — atom.gs
 * Server-side V8 JavaScript engine for rendering A2UI Atom components.
 */

/**
 * Main entry point: renders an array of atom blocks to an HTML string.
 *
 * @param {Object[]} blocks - List of atom block objects (complying with schema.yaml).
 * @param {Object} [opts] - Configuration options.
 * @param {string} [opts.theme='light'] - 'light' or 'dark'.
 * @param {boolean} [opts.sidebar=false] - If true, optimized for sidebar width.
 * @returns {string} Injected HTML fragment.
 */
function renderAtoms(blocks, opts) {
  if (!blocks || !Array.isArray(blocks)) {
    return '<!-- a2ui: blocks list is empty or invalid -->';
  }
  
  opts = opts || {};
  var theme = opts.theme || 'light';
  var sidebar = !!opts.sidebar;
  
  var parts = [];
  for (var i = 0; i < blocks.length; i++) {
    var block = blocks[i];
    var btype = block.component || block.type;
    var fn = _RENDERERS[btype];
    
    if (fn) {
      try {
        parts.push(fn(block));
      } catch (err) {
        parts.push('<div class="asw-callout" style="border-left-color:var(--red);">' +
                   '<span class="asw-callout-icon">⚠️</span>' +
                   '<div class="asw-callout-content">Error rendering <strong>' + _esc(btype) + '</strong>: ' + _esc(err.message) + '</div>' +
                   '</div>');
      }
    } else {
      parts.push('<!-- a2ui: unknown or unsupported atom "' + _esc(btype) + '" -->');
    }
  }
  
  return parts.join('\n\n');
}

/**
 * Apps Script HTML Template include helper.
 * Pulls partial files (AtomStyles, AtomScripts) dynamically.
 */
function include(filename) {
  return HtmlService.createHtmlOutputFromFile(filename).getContent();
}

// ── HTML Escape Helper ────────────────────────────────────────────────────────
function _esc(str) {
  if (str === undefined || str === null) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// ── Renderers Registry ────────────────────────────────────────────────────────
var _RENDERERS = {};

// ── Category A: Static Content Renderers ──────────────────────────────────────

_RENDERERS['body'] = function(b) {
  return '<p class="asw-body">' + _markdownToHtml(b.text) + '</p>';
};

_RENDERERS['paragraph'] = function(b) {
  return '<p class="asw-paragraph">' + _markdownToHtml(b.text) + '</p>';
};

_RENDERERS['text_block'] = function(b) {
  return '<p class="asw-text-block">' + _markdownToHtml(b.text) + '</p>';
};

_RENDERERS['heading'] = function(b) {
  var level = b.level || 2;
  return '<h' + level + ' class="asw-heading">' + _esc(b.text) + '</h' + level + '>';
};

_RENDERERS['subheading'] = function(b) {
  var level = b.level || 3;
  return '<h' + level + ' class="asw-subheading">' + _esc(b.text) + '</h' + level + '>';
};

_RENDERERS['blockquote'] = function(b) {
  var cite = b.attribution ? '<cite style="display:block;margin-top:6px;font-size:0.8rem;text-align:right;">— ' + _esc(b.attribution) + '</cite>' : '';
  return '<blockquote>' + _markdownToHtml(b.text) + cite + '</blockquote>';
};

_RENDERERS['divider'] = function(b) {
  return '<hr class="asw-divider">';
};

_RENDERERS['spacer'] = function(b) {
  var height = b.height || 20;
  return '<div class="asw-spacer" style="height:' + height + 'px;"></div>';
};

_RENDERERS['callout'] = function(b) {
  var icon = b.icon || '💡';
  var color = b.color || 'var(--accent)';
  return '<div class="asw-callout" style="border-left-color:' + color + ';">' +
         '<span class="asw-callout-icon">' + icon + '</span>' +
         '<div class="asw-callout-content">' + _markdownToHtml(b.text) + '</div>' +
         '</div>';
};

_RENDERERS['alert_banner'] = function(b) {
  var variant = b.variant || 'info'; // info, success, warning, critical
  var icons = { info: 'ℹ️', success: '✅', warning: '⚠️', critical: '🚨' };
  var colors = { info: 'var(--accent)', success: 'var(--green)', warning: 'var(--orange)', critical: 'var(--red)' };
  
  return '<div class="asw-callout" style="border-left-color:' + colors[variant] + '; background:var(--surface2);">' +
         '<span class="asw-callout-icon">' + (b.icon || icons[variant]) + '</span>' +
         '<div class="asw-callout-content" style="font-weight:500;">' + _markdownToHtml(b.text) + '</div>' +
         '</div>';
};

_RENDERERS['info_card'] = function(b) {
  return '<div class="asw-native-card">' +
         (b.title ? '<div style="font-weight:700;margin-bottom:8px;font-size:0.95rem;">' + _esc(b.title) + '</div>' : '') +
         '<div style="font-size:0.88rem;color:var(--muted);">' + _markdownToHtml(b.text) + '</div>' +
         '</div>';
};

_RENDERERS['code_block'] = function(b) {
  return '<pre><code class="language-' + _esc(b.language || 'text') + '">' + _esc(b.content) + '</code></pre>';
};

_RENDERERS['code'] = function(b) {
  return '<pre><code class="language-' + _esc(b.language || 'text') + '">' + _esc(b.content) + '</code></pre>';
};

_RENDERERS['inline_code'] = function(b) {
  return '<code>' + _esc(b.text) + '</code>';
};

_RENDERERS['tag_chip'] = function(b) {
  var color = b.color || 'var(--accent)';
  return '<span class="asw-badge" style="background:rgba(26,115,232,0.1);color:' + color + ';padding:4px 8px;border-radius:12px;font-size:0.75rem;font-weight:600;margin-right:6px;">' + _esc(b.text) + '</span>';
};

_RENDERERS['badge'] = function(b) {
  var color = b.color || 'var(--muted)';
  return '<span class="asw-badge" style="border:1px solid ' + color + ';color:' + color + ';padding:2px 6px;border-radius:4px;font-size:0.7rem;font-weight:600;text-transform:uppercase;">' + _esc(b.text) + '</span>';
};

_RENDERERS['image'] = function(b) {
  var caption = b.caption ? '<div style="font-size:0.8rem;color:var(--muted);text-align:center;margin-top:6px;">' + _esc(b.caption) + '</div>' : '';
  return '<div style="margin:16px 0;text-align:center;">' +
         '<img src="' + _esc(b.url) + '" alt="' + _esc(b.alt || '') + '" style="max-width:100%;border-radius:6px;box-shadow:0 1px 3px rgba(0,0,0,0.1);">' +
         caption +
         '</div>';
};

_RENDERERS['highlighted_text'] = function(b) {
  var color = b.color || '#fef08a';
  var noteAttr = b.annotation ? ' data-note="' + _esc(b.annotation) + '"' : '';
  return '<mark class="asw-highlight" style="background:' + color + '"' + noteAttr + '>' + _esc(b.text) + '</mark>';
};

_RENDERERS['table'] = function(b) {
  var html = '<table>';
  if (b.headers && b.headers.length) {
    html += '<thead><tr>';
    for (var i = 0; i < b.headers.length; i++) {
      html += '<th>' + _esc(b.headers[i]) + '</th>';
    }
    html += '</tr></thead>';
  }
  if (b.rows && b.rows.length) {
    html += '<tbody>';
    for (var r = 0; r < b.rows.length; r++) {
      html += '<tr>';
      for (var c = 0; c < b.rows[r].length; c++) {
        html += '<td>' + _markdownToHtml(b.rows[r][c]) + '</td>';
      }
      html += '</tr>';
    }
    html += '</tbody>';
  }
  html += '</table>';
  return html;
};

_RENDERERS['bullet_list'] = function(b) {
  var html = '<ul>';
  for (var i = 0; i < b.items.length; i++) {
    var item = b.items[i];
    var lead = item.label ? '<strong>' + _esc(item.label) + ': </strong>' : '';
    html += '<li>' + lead + _markdownToHtml(item.text) + '</li>';
  }
  html += '</ul>';
  return html;
};

// ── Category B: Link / Navigation Renderers ─────────────────────────────────

_RENDERERS['link_button'] = function(b) {
  return '<div style="margin:12px 0;">' +
         '<a href="' + _esc(b.url) + '" class="asw-btn asw-btn-primary" target="_top">' + _esc(b.label) + '</a>' +
         '</div>';
};

_RENDERERS['cta_button'] = function(b) {
  return '<div style="margin:16px 0;text-align:center;">' +
         '<a href="' + _esc(b.url) + '" class="asw-btn asw-btn-primary" style="padding:10px 24px;font-size:0.85rem;" target="_top">' + _esc(b.label) + '</a>' +
         '</div>';
};

_RENDERERS['nav_link'] = function(b) {
  return '<a href="' + _esc(b.url) + '" class="asw-nav-link" style="font-size:0.88rem;font-weight:500;margin-right:12px;" target="_top">' + _esc(b.label) + '</a>';
};

_RENDERERS['lesson_nav'] = function(b) {
  var prevHtml = b.prev_url ? 
    '<a href="' + _esc(b.prev_url) + '" class="asw-lesson-nav-side" target="_top"><span class="nav-arrow">←</span><span>' + _esc(b.prev_title || 'Previous') + '</span></a>' : 
    '<span></span>';
  var nextHtml = b.next_url ? 
    '<a href="' + _esc(b.next_url) + '" class="asw-lesson-nav-side" style="justify-content:flex-end;text-align:right;" target="_top"><span>' + _esc(b.next_title || 'Next') + '</span><span class="nav-arrow">→</span></a>' : 
    '<span></span>';
  
  var moduleLabel = b.module_label ? '<div class="asw-lesson-nav-module">' + _esc(b.module_label) + '</div>' : '';
  
  var checkbox = b.show_completion ? 
    '<label class="asw-complete-row"><input type="checkbox" onchange="if(typeof localStorage !== \'undefined\'){localStorage.setItem(\'complete-\' + ' + JSON.stringify(b.current_title) + ', this.checked);}"> Mark as complete</label>' : '';

  return '<div class="asw-lesson-nav">' +
         prevHtml +
         '<div class="asw-lesson-nav-center">' + moduleLabel + '<div class="asw-lesson-nav-title">' + _esc(b.current_title) + '</div>' + checkbox + '</div>' +
         nextHtml +
         '</div>';
};

_RENDERERS['course_progress_card'] = function(b) {
  var modules = b.modules || [];
  var accent = b.accent || 'var(--accent)';
  var lessonsTotal = 0;
  var lessonsDone = 0;
  
  var modsHtml = '';
  for (var i = 0; i < modules.length; i++) {
    var m = modules[i];
    var lt = m.lessons_total || 1;
    var ld = m.lessons_done || 0;
    lessonsTotal += lt;
    lessonsDone += ld;
    var mpct = Math.min(100, Math.round((ld / lt) * 100));
    
    modsHtml += '<div class="asw-course-module">' +
                '<div class="asw-course-mod-row">' +
                '<span class="asw-course-mod-name">' + _esc(m.title) + '</span>' +
                '<span class="asw-course-mod-pct">' + ld + '/' + lt + '</span>' +
                '</div>' +
                '<div class="asw-course-bar-track">' +
                '<div class="asw-course-bar-fill" style="width:' + mpct + '%;background:' + accent + ';"></div>' +
                '</div>' +
                '</div>';
  }
  
  var overallPct = lessonsTotal ? Math.min(100, Math.round((lessonsDone / lessonsTotal) * 100)) : 0;
  
  return '<div class="asw-course-card">' +
         '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px">' +
         '<div class="asw-course-title">' + _esc(b.course_title) + '</div>' +
         '<div style="font-family:var(--mono);font-size:1.1rem;font-weight:700;color:' + accent + '">' + overallPct + '%</div>' +
         '</div>' +
         modsHtml +
         '</div>';
};

// ── Category C: Interactive Renderers ────────────────────────────────────────

_RENDERERS['quiz_question'] = function(b) {
  var options = b.options || [];
  var correctIdx = b.correct || 0;
  var explanation = b.explanation || '';
  var atomId = b.id || 'quiz-' + Math.floor(Math.random() * 100000);
  var uid = 'q' + Math.floor(Math.random() * 100000);

  var optsHtml = '';
  for (var i = 0; i < options.length; i++) {
    optsHtml += '<div class="asw-quiz-opt" id="' + uid + '-opt-' + i + '" data-idx="' + i + '">' + _esc(options[i]) + '</div>';
  }

  var expHtml = explanation ? '<div class="asw-quiz-explain" id="' + uid + '-explain">' + _markdownToHtml(explanation) + '</div>' : '';

  var initScript = '<script>(function(){ initQuiz(' + JSON.stringify(uid) + ',' + correctIdx + ',' + JSON.stringify(atomId) + '); })();</script>';

  return '<div class="asw-quiz" id="' + uid + '-quiz">' +
         '<div class="asw-quiz-label">Question</div>' +
         '<div class="asw-quiz-q">' + _esc(b.question) + '</div>' +
         '<div class="asw-quiz-opts">' + optsHtml + '</div>' +
         expHtml +
         '</div>' +
         initScript;
};

_RENDERERS['fill_in_blank'] = function(b) {
  var template = b.template || '';
  var atomId = b.id || 'fib-' + Math.floor(Math.random() * 100000);
  var uid = 'fib' + Math.floor(Math.random() * 100000);
  var hintHtml = b.hint ? '<p style="margin-top:8px;font-size:0.8rem;color:var(--muted)">💡 ' + _esc(b.hint) + '</p>' : '';

  var blankIdx = 0;
  var htmlTemplate = template.replace(/\{blank\}/g, function() {
    var i = blankIdx++;
    return '<input class="asw-fib-input" id="' + uid + '-inp-' + i + '" data-idx="' + i + '" placeholder="…" autocomplete="off">';
  });

  var initScript = '<script>(function(){ initFillInBlank(' + JSON.stringify(uid) + ',' + JSON.stringify(atomId) + '); })();</script>';

  return '<div class="asw-fib" id="' + uid + '-fib">' +
         '<div class="asw-fib-label">Fill in the blank</div>' +
         '<div style="font-size:0.9rem;line-height:2;">' + htmlTemplate + '</div>' +
         hintHtml +
         '<div class="asw-fib-actions">' +
         '<button class="asw-btn asw-btn-primary" id="' + uid + '-check">Check</button>' +
         '<button class="asw-btn asw-btn-ghost" id="' + uid + '-reset">Reset</button>' +
         '</div>' +
         '</div>' +
         initScript;
};

_RENDERERS['match_exercise'] = function(b) {
  var pairs = b.pairs || [];
  var atomId = b.id || 'match-' + Math.floor(Math.random() * 100000);
  var uid = 'match' + Math.floor(Math.random() * 100000);
  
  var lefts = [];
  var rights = [];
  var correctMap = {};
  
  for (var i = 0; i < pairs.length; i++) {
    lefts.push({ idx: i, text: pairs[i].term });
    rights.push({ idx: i, text: pairs[i].definition });
  }

  // Shuffle right side if desired
  if (b.shuffle !== false) {
    rights.sort(function() { return Math.random() - 0.5; });
  }

  // Map left idx to right side visual position idx
  for (var l = 0; l < lefts.length; l++) {
    for (var r = 0; r < rights.length; r++) {
      if (lefts[l].idx === rights[r].idx) {
        correctMap[l] = r;
      }
    }
  }

  var leftsHtml = '';
  for (var l = 0; l < lefts.length; l++) {
    leftsHtml += '<div class="asw-match-item" id="' + uid + '-l-' + l + '" data-side="left" data-idx="' + l + '">' + _esc(lefts[l].text) + '</div>';
  }

  var rightsHtml = '';
  for (var r = 0; r < rights.length; r++) {
    rightsHtml += '<div class="asw-match-item" id="' + uid + '-r-' + r + '" data-side="right" data-idx="' + r + '">' + _esc(rights[r].text) + '</div>';
  }

  var initScript = '<script>(function(){ initMatchExercise(' + JSON.stringify(uid) + ',' + JSON.stringify(atomId) + ',' + JSON.stringify(correctMap) + '); })();</script>';

  return '<div class="asw-match">' +
         '<div class="asw-match-label">Matching Exercise</div>' +
         '<div class="asw-match-sub">Click a term, then click its matching definition.</div>' +
         '<div class="asw-match-grid">' +
         '<div class="asw-match-col"><h4>Term</h4>' + leftsHtml + '</div>' +
         '<div class="asw-match-col"><h4>Definition</h4>' + rightsHtml + '</div>' +
         '</div>' +
         '<div class="asw-match-score">Matched: <strong id="' + uid + '-score">0 / ' + pairs.length + '</strong></div>' +
         '</div>' +
         initScript;
};

_RENDERERS['hint_reveal'] = function(b) {
  var accent = b.accent || 'var(--accent)';
  var label = b.label || 'Show hint';
  return '<details class="asw-hint" style="border-left-color:' + accent + ';">' +
         '<summary style="color:' + accent + ';">' + _esc(label) + '</summary>' +
         '<div class="asw-hint-body">' + _markdownToHtml(b.hint) + '</div>' +
         '</details>';
};

_RENDERERS['achievement_badge'] = function(b) {
  var icon = b.icon || '🏆';
  var color = b.color || 'var(--yellow)';
  var size = b.size || 'card';
  var locked = !!b.locked;
  
  var badgeClass = 'asw-achievement' + (locked ? ' locked' : '');
  var unlockedHtml = b.unlocked_at && !locked ? '<div class="asw-achievement-date">Unlocked ' + _esc(b.unlocked_at) + '</div>' : '';

  if (size === 'pill') {
    return '<span class="' + badgeClass + '" style="border-color:' + color + ';display:inline-flex;padding:6px 14px;align-items:center;gap:6px;margin:4px 0;">' +
           '<span class="asw-achievement-icon" style="font-size:1.1rem;line-height:1;">' + icon + '</span>' +
           '<span class="asw-achievement-title" style="color:' + color + ';margin:0;font-size:0.8rem;">' + _esc(b.title) + '</span>' +
           '</span>';
  }

  return '<div class="' + badgeClass + '" style="border-color:' + color + ';">' +
         '<div class="asw-achievement-icon">' + icon + '</div>' +
         '<div>' +
         '<div class="asw-achievement-title" style="color:' + color + '">' + _esc(b.title) + '</div>' +
         (b.description ? '<div class="asw-achievement-desc">' + _esc(b.description) + '</div>' : '') +
         unlockedHtml +
         '</div>' +
         '</div>';
};

_RENDERERS['score_summary'] = function(b) {
  var correct = b.correct || 0;
  var total = b.total || 1;
  var pct = Math.min(100, Math.round((correct / total) * 100));
  var passed = pct >= (b.pass_threshold || 60);
  var classPct = passed ? '' : ' fail';
  var label = passed ? 'Passed' : 'Failed';
  
  var timeHtml = b.time_taken ? 
    '<div class="asw-score-stat"><div class="asw-score-stat-val">' + _esc(b.time_taken) + '</div><div class="asw-score-stat-lbl">Time</div></div>' : '';
  
  var ctas = '';
  if (b.retry_label || b.continue_label) {
    var retry = b.retry_label ? '<button class="asw-btn asw-btn-ghost" onclick="if(typeof location !== \'undefined\')location.reload();">' + _esc(b.retry_label) + '</button>' : '';
    var cont = b.continue_label ? '<a href="' + _esc(b.continue_url || '#') + '" class="asw-btn asw-btn-primary" target="_top">' + _esc(b.continue_label) + '</a>' : '';
    ctas = '<div class="asw-score-ctas">' + retry + cont + '</div>';
  }

  return '<div class="asw-score">' +
         '<div class="asw-score-pct' + classPct + '">' + pct + '%</div>' +
         '<div class="asw-score-label">' + label + '</div>' +
         '<div class="asw-score-row">' +
         '<div class="asw-score-stat"><div class="asw-score-stat-val">' + correct + '/' + total + '</div><div class="asw-score-stat-lbl">Score</div></div>' +
         timeHtml +
         '</div>' +
         ctas +
         '</div>';
};

_RENDERERS['xp_bar'] = function(b) {
  var xpCurrent = b.xp_current || 0;
  var xpNext = b.xp_next || 100;
  var pct = Math.min(100, Math.round((xpCurrent / xpNext) * 100));
  var accent = b.accent || 'var(--accent)';
  
  return '<div class="asw-xp">' +
         '<div class="asw-xp-row">' +
         '<span class="asw-xp-level">' + _esc(b.level_label || 'Level 1') + '</span>' +
         '<span class="asw-xp-count">' + xpCurrent + ' / ' + xpNext + ' XP</span>' +
         '</div>' +
         '<div class="asw-xp-track">' +
         '<div class="asw-xp-fill" style="width:' + pct + '%;background:' + accent + ';"></div>' +
         '</div>' +
         '</div>';
};

// ── Category D: Workspace-Native Renderers ───────────────────────────────────

_RENDERERS['drive_file_list'] = function(b) {
  var folderId = b.folder_id;
  var maxResults = b.max_results || 10;
  var files = [];
  var errorMsg = null;
  
  // Real implementation (GAS native server code)
  if (typeof DriveApp !== 'undefined') {
    try {
      var folder = DriveApp.getFolderById(folderId);
      var fileIterator = folder.getFiles();
      var count = 0;
      while (fileIterator.hasNext() && count < maxResults) {
        var file = fileIterator.next();
        files.push({
          name: file.getName(),
          url: file.getUrl(),
          mimeType: file.getMimeType()
        });
        count++;
      }
    } catch (err) {
      errorMsg = err.message;
    }
  } else {
    // Fallback/Mock data for preview
    files = [
      { name: 'Document_1.pdf', url: '#', mimeType: 'application/pdf' },
      { name: 'Project_Sheet.xlsx', url: '#', mimeType: 'application/vnd.google-apps.spreadsheet' },
      { name: 'Slideshow.gslides', url: '#', mimeType: 'application/vnd.google-apps.presentation' }
    ];
  }

  var listHtml = '';
  if (errorMsg) {
    listHtml = '<div style="font-size:0.82rem;color:var(--red);">Unable to retrieve files: ' + _esc(errorMsg) + '</div>';
  } else if (files.length === 0) {
    listHtml = '<div style="font-size:0.82rem;color:var(--muted);">No files found in folder.</div>';
  } else {
    listHtml += '<ul class="asw-drive-list">';
    for (var i = 0; i < files.length; i++) {
      var icon = '📄';
      if (files[i].mimeType.indexOf('pdf') !== -1) icon = '📕';
      else if (files[i].mimeType.indexOf('spreadsheet') !== -1) icon = '📊';
      else if (files[i].mimeType.indexOf('presentation') !== -1) icon = '📈';
      else if (files[i].mimeType.indexOf('folder') !== -1) icon = '📁';
      
      listHtml += '<li class="asw-drive-item">' +
                  '<span class="asw-drive-icon">' + icon + '</span>' +
                  '<a href="' + _esc(files[i].url) + '" class="asw-drive-link" target="_top">' + _esc(files[i].name) + '</a>' +
                  '</li>';
    }
    listHtml += '</ul>';
  }

  return '<div class="asw-native-card">' +
         '<div class="asw-native-header"><span class="asw-native-header-icon">📁</span> Google Drive Folder</div>' +
         listHtml +
         '</div>';
};

_RENDERERS['sheet_preview'] = function(b) {
  var spreadsheetId = b.spreadsheet_id;
  var sheetName = b.sheet_name;
  var rangeStr = b.range;
  var data = [];
  var errorMsg = null;
  
  if (typeof SpreadsheetApp !== 'undefined') {
    try {
      var ss = SpreadsheetApp.openById(spreadsheetId);
      var sheet = sheetName ? ss.getSheetByName(sheetName) : ss.getSheets()[0];
      var range = sheet.getRange(rangeStr);
      data = range.getValues();
    } catch (err) {
      errorMsg = err.message;
    }
  } else {
    // Fallback/Mock data for preview
    data = [
      ['Header 1', 'Header 2', 'Header 3'],
      ['Row 1 Col 1', 'Row 1 Col 2', 'Row 1 Col 3'],
      ['Row 2 Col 1', 'Row 2 Col 2', 'Row 2 Col 3']
    ];
  }

  var tableHtml = '';
  if (errorMsg) {
    tableHtml = '<div style="font-size:0.82rem;color:var(--red);">Unable to load Sheet range: ' + _esc(errorMsg) + '</div>';
  } else {
    tableHtml += '<div class="asw-sheet-preview-wrapper"><table class="asw-sheet-table">';
    for (var r = 0; r < data.length; r++) {
      tableHtml += '<tr>';
      for (var c = 0; c < data[r].length; c++) {
        var cellText = _esc(data[r][c]);
        if (r === 0) {
          tableHtml += '<th>' + cellText + '</th>';
        } else {
          tableHtml += '<td>' + cellText + '</td>';
        }
      }
      tableHtml += '</tr>';
    }
    tableHtml += '</table></div>';
  }

  return '<div class="asw-native-card">' +
         '<div class="asw-native-header"><span class="asw-native-header-icon">📊</span> Google Sheet Live Preview (' + _esc(sheetName || 'Sheet1') + '!' + _esc(rangeStr) + ')</div>' +
         tableHtml +
         '</div>';
};

_RENDERERS['gmail_summary'] = function(b) {
  var query = b.query || 'is:unread';
  var maxResults = b.max_results || 5;
  var threads = [];
  var errorMsg = null;
  
  if (typeof GmailApp !== 'undefined') {
    try {
      var gmailThreads = GmailApp.search(query, 0, maxResults);
      for (var i = 0; i < gmailThreads.length; i++) {
        var firstMsg = gmailThreads[i].getMessages()[0];
        threads.push({
          subject: gmailThreads[i].getFirstMessageSubject(),
          from: firstMsg.getFrom(),
          date: firstMsg.getDate().toLocaleDateString()
        });
      }
    } catch (err) {
      errorMsg = err.message;
    }
  } else {
    // Fallback/Mock data for preview
    threads = [
      { from: 'Google Apps Script team <dev@google.com>', subject: 'New V8 features available', date: '6/16/2026' },
      { from: 'GitHub Notification <noreply@github.com>', subject: '[a2ui-catalogue] Pull request #4 merged', date: '6/15/2026' }
    ];
  }

  var listHtml = '';
  if (errorMsg) {
    listHtml = '<div style="font-size:0.82rem;color:var(--red);">Gmail access failed: ' + _esc(errorMsg) + '</div>';
  } else if (threads.length === 0) {
    listHtml = '<div style="font-size:0.82rem;color:var(--muted);">No messages matched query "' + _esc(query) + '".</div>';
  } else {
    listHtml += '<ul class="asw-gmail-list">';
    for (var i = 0; i < threads.length; i++) {
      listHtml += '<li class="asw-gmail-item">' +
                  '<div class="asw-gmail-meta">' +
                  '<span class="asw-gmail-from">' + _esc(threads[i].from) + '</span>' +
                  '<span class="asw-gmail-date">' + _esc(threads[i].date) + '</span>' +
                  '</div>' +
                  '<div class="asw-gmail-subject">' + _esc(threads[i].subject) + '</div>' +
                  '</li>';
    }
    listHtml += '</ul>';
  }

  return '<div class="asw-native-card">' +
         '<div class="asw-native-header"><span class="asw-native-header-icon">✉️</span> Gmail Search: "' + _esc(query) + '"</div>' +
         listHtml +
         '</div>';
};

_RENDERERS['calendar_upcoming'] = function(b) {
  var maxResults = b.max_results || 5;
  var events = [];
  var errorMsg = null;
  
  if (typeof CalendarApp !== 'undefined') {
    try {
      var cal = CalendarApp.getDefaultCalendar();
      var now = new Date();
      var end = new Date(now.getTime() + (30 * 24 * 60 * 60 * 1000)); // 30 days ahead
      var calEvents = cal.getEvents(now, end);
      
      var limit = Math.min(calEvents.length, maxResults);
      for (var i = 0; i < limit; i++) {
        var start = calEvents[i].getStartTime();
        events.push({
          title: calEvents[i].getTitle(),
          startDay: start.getDate(),
          startMonth: start.toLocaleDateString(undefined, { month: 'short' }),
          timeStr: start.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })
        });
      }
    } catch (err) {
      errorMsg = err.message;
    }
  } else {
    // Fallback/Mock data for preview
    events = [
      { title: 'A2UI Review Meeting', startDay: 18, startMonth: 'Jun', timeStr: '10:00 AM' },
      { title: 'Weekly Pair Programming', startDay: 20, startMonth: 'Jun', timeStr: '02:00 PM' }
    ];
  }

  var listHtml = '';
  if (errorMsg) {
    listHtml = '<div style="font-size:0.82rem;color:var(--red);">Calendar access failed: ' + _esc(errorMsg) + '</div>';
  } else if (events.length === 0) {
    listHtml = '<div style="font-size:0.82rem;color:var(--muted);">No upcoming events.</div>';
  } else {
    listHtml += '<ul class="asw-cal-list">';
    for (var i = 0; i < events.length; i++) {
      listHtml += '<li class="asw-cal-item">' +
                  '<div class="asw-cal-date-badge">' +
                  '<span class="day">' + events[i].startDay + '</span>' +
                  '<span class="month">' + events[i].startMonth + '</span>' +
                  '</div>' +
                  '<div class="asw-cal-details">' +
                  '<span class="asw-cal-title">' + _esc(events[i].title) + '</span>' +
                  '<span class="asw-cal-time">⏰ ' + events[i].timeStr + '</span>' +
                  '</div>' +
                  '</li>';
    }
    listHtml += '</ul>';
  }

  return '<div class="asw-native-card">' +
         '<div class="asw-native-header"><span class="asw-native-header-icon">📅</span> Calendar Schedule</div>' +
         listHtml +
         '</div>';
};

_RENDERERS['user_greeting'] = function(b) {
  var prefix = b.prefix || 'Hello';
  var email = 'curtis@example.com';
  
  if (typeof Session !== 'undefined') {
    try {
      email = Session.getActiveUser().getEmail() || email;
    } catch (err) {}
  }
  
  var initial = email.charAt(0).toUpperCase();

  return '<div class="asw-user-greeting">' +
         '<div class="asw-user-avatar">' + initial + '</div>' +
         '<div>' + _esc(prefix) + ', <span class="asw-user-email">' + _esc(email) + '</span>!</div>' +
         '</div>';
};

_RENDERERS['script_run_button'] = function(b) {
  var label = b.label || 'Run Script';
  var functionName = b.function_name || 'myFunction';
  var argument = b.argument || '';
  var btnId = 'btn-' + Math.floor(Math.random() * 100000);

  return '<div style="margin:16px 0; display:flex; align-items:center; gap:12px;">' +
         '<button id="' + btnId + '" class="asw-btn asw-btn-primary" onclick="runCustomScript(' + 
         JSON.stringify(btnId) + ',' + JSON.stringify(functionName) + ',' + JSON.stringify(argument) + ')">' +
         '<span class="asw-spinner" style="display:none;"></span>' +
         '<span class="asw-btn-label">' + _esc(label) + '</span>' +
         '</button>' +
         '<span id="' + btnId + '-status" style="font-size:0.8rem; font-weight:500;"></span>' +
         '</div>';
};

// ── Category E: Degraded Renderers ───────────────────────────────────────────

_RENDERERS['youtube'] = function(b) {
  return '<div class="asw-degraded-card">' +
         '<div class="asw-degraded-title">📹 YouTube Video Fallback</div>' +
         '<div class="asw-degraded-text">Direct iframe playback is restricted inside the Google Apps Script Web App sandbox environment.</div>' +
         '<a href="' + _esc(b.url) + '" class="asw-btn asw-btn-ghost" style="margin-top:6px;" target="_top">Watch on YouTube →</a>' +
         '</div>';
};

_RENDERERS['embed_codepen'] = _degradedLinkRenderer('CodePen sandbox embed');
_RENDERERS['embed_stackblitz'] = _degradedLinkRenderer('StackBlitz sandbox embed');
_RENDERERS['embed_gist'] = _degradedLinkRenderer('GitHub Gist widget');
_RENDERERS['embed_google_slides'] = _degradedLinkRenderer('Google Slides preview iframe');
_RENDERERS['figma_embed'] = _degradedLinkRenderer('Figma interactive canvas design preview');

function _degradedLinkRenderer(typeName) {
  return function(b) {
    var url = b.url || '#';
    return '<div class="asw-degraded-card">' +
           '<div class="asw-degraded-title">🔗 External Resource (' + typeName + ')</div>' +
           '<div class="asw-degraded-text">Interactive frames are restricted inside the Google Apps Script iframe sandbox.</div>' +
           '<a href="' + _esc(url) + '" class="asw-btn asw-btn-ghost" style="margin-top:6px;" target="_top">Open Link in New Tab →</a>' +
           '</div>';
  };
}

_RENDERERS['lottie_animation'] = function(b) {
  return b.fallback_image_url ? 
    _RENDERERS['image']({ url: b.fallback_image_url, caption: b.caption || 'Animation static preview' }) : 
    '<!-- lottie animation stripped: requires external client JS bundles -->';
};

_RENDERERS['parallax_card'] = function(b) {
  // Degrades to static card presentation
  return '<div class="asw-native-card" style="background-image:linear-gradient(rgba(0,0,0,0.05), rgba(0,0,0,0.05));">' +
         '<div style="font-weight:700;margin-bottom:8px;">' + _esc(b.title || 'Parallax Card') + '</div>' +
         '<div style="font-size:0.88rem;color:var(--muted);">' + _esc(b.subtitle || '') + '</div>' +
         '</div>';
};

_RENDERERS['embed_tweet'] = function(b) {
  return '<blockquote class="asw-twitter-degraded" style="border-left-color:#1da1f2;">' +
         '<div style="font-size:0.75rem;font-weight:700;color:#1da1f2;margin-bottom:6px;">𝕏 Tweet (Static View)</div>' +
         '<p>' + _esc(b.text || 'Tweet contents') + '</p>' +
         (b.author ? '<cite style="display:block;margin-top:4px;font-size:0.8rem;text-align:right;">— ' + _esc(b.author) + '</cite>' : '') +
         '</blockquote>';
};

_RENDERERS['social_feed_embed'] = function(b) {
  return '<div class="asw-degraded-card">' +
         '<div class="asw-degraded-title">💬 Social Media Feed</div>' +
         '<div class="asw-degraded-text">Live media feeds are disabled. Click below to view directly.</div>' +
         '<a href="' + _esc(b.url || '#') + '" class="asw-btn asw-btn-ghost" style="margin-top:6px;" target="_top">Open Social Feed →</a>' +
         '</div>';
};

_RENDERERS['image_pair'] = function(b) {
  var images = b.images || [];
  if (!images.length) {
    var url1 = b.url || b.url_1 || '';
    var url2 = b.url_2 || '';
    if (url1) {
      images = url2
        ? [{ url: url1, caption: b.caption_1 || '' }, { url: url2, caption: b.caption_2 || '' }]
        : [{ url: url1 }];
    }
  }
  var parts = [];
  var limit = Math.min(images.length, 2);
  for (var i = 0; i < limit; i++) {
    var src = _esc(images[i].url || '');
    var caption = _esc(images[i].caption || '');
    var capHtml = caption ? '<p style="font-size:0.75rem;color:var(--muted);text-align:center;margin-top:4px">' + caption + '</p>' : '';
    if (src) {
      parts.push('<div style="flex:1;min-width:0"><img src="' + src + '" alt="' + caption + '" style="width:100%;border-radius:6px">' + capHtml + '</div>');
    }
  }
  return parts.length ? '<div style="display:flex;gap:12px;flex-wrap:wrap">' + parts.join('') + '</div>' : '<!-- image_pair: no images -->';
};

_RENDERERS['diagram'] = function(b) {
  var url = b.url || b.src || '';
  var alt = _esc(b.alt || b.title || 'Diagram');
  var caption = _esc(b.caption || '');
  var capHtml = caption ? '<p style="font-size:0.75rem;color:var(--muted);text-align:center;margin-top:4px">' + caption + '</p>' : '';
  if (!url) return '<!-- diagram: no url -->';
  return '<figure style="margin:16px 0"><img src="' + _esc(url) + '" alt="' + alt + '" style="max-width:100%;border-radius:6px">' + capHtml + '</figure>';
};

_RENDERERS['video_pair'] = function(b) {
  var videos = b.videos || [];
  var parts = [];
  var limit = Math.min(videos.length, 2);
  for (var i = 0; i < limit; i++) {
    var v = videos[i];
    var vid = v.video_id || v.id || '';
    var url = v.url || (vid ? 'https://www.youtube.com/watch?v=' + vid : '#');
    var label = _esc(v.label || v.title || 'Watch video');
    parts.push(
      '<div style="flex:1;min-width:0">' +
      '<div class="asw-degraded-card" style="height:100%">' +
      '<div class="asw-degraded-title">📹 ' + label + '</div>' +
      '<a href="' + _esc(url) + '" class="asw-btn asw-btn-ghost" style="margin-top:6px;" target="_top">Watch on YouTube →</a>' +
      '</div></div>'
    );
  }
  return '<div style="display:flex;gap:12px;flex-wrap:wrap">' + parts.join('') + '</div>';
};

_RENDERERS['live_demo_embed'] = function(b) {
  var title = _esc(b.title || 'Live Demo');
  var note = _esc(b.note || 'Sandbox iframes have limited support inside Apps Script Web Apps.');
  return '<div class="asw-degraded-card">' +
         '<div class="asw-degraded-title">🧪 ' + title + '</div>' +
         '<div class="asw-degraded-text">' + note + '</div>' +
         '<a href="' + _esc(b.url || '#') + '" class="asw-btn asw-btn-ghost" style="margin-top:6px;" target="_top">Open Demo →</a>' +
         '</div>';
};

// ── Markdown Parser Stub ──────────────────────────────────────────────────────
// Custom simple parser to map bold (**), italic (*), and link syntax to HTML tags.
function _markdownToHtml(md) {
  if (!md) return '';
  var res = _esc(md);
  
  // Bold **word**
  res = res.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  
  // Italic *word*
  res = res.replace(/\*(.*?)\*/g, '<em>$1</em>');
  
  // Inline link: [text](url) - force target="_top" for GAS Web App CSP
  res = res.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_top">$1</a>');
  
  return res;
}

// ── Server-Side Handlers Stubs (Can be overridden by custom GAS apps) ─────────
function saveQuizAnswer(atomId, selectedIdx) {
  var user = Session.getActiveUser().getEmail() || 'anonymous';
  var prop = PropertiesService.getUserProperties();
  prop.setProperty('quiz_' + atomId + '_' + user, String(selectedIdx));
  return { success: true, user: user, atomId: atomId, selectedIdx: selectedIdx };
}

function checkFillInBlank(atomId, userAnswers) {
  // Stubs for validating on server. Standard checks can also be client-driven.
  // We return validation array for answers
  return { success: true, correct: userAnswers.map(function(ans) { return !!ans; }) };
}

function saveMatchResult(atomId, score) {
  var user = Session.getActiveUser().getEmail() || 'anonymous';
  return { success: true, user: user, atomId: atomId, score: score };
}

function unlockAchievement(badgeId) {
  return { success: true, badgeId: badgeId };
}

function getXP(userId) {
  return { success: true, xp: 120 };
}

function getScoreData(sessionId) {
  return { success: true, score: 80 };
}

function submitFeedback(data) {
  return { success: true };
}


// === Batch 1: Core Content Atoms ===

_RENDERERS['intro'] = function(b) {
  var parts = [];
  if (b.series_label && b.series_url) {
    parts.push('<p><em>In <a href="' + _esc(b.series_url) + '">' + _esc(b.series_label) + '</a>, ' +
               _markdownToHtml(b.continuation || 'I covered the background. This article picks up from there.') + '</em></p>');
  }
  if (b.note) parts.push('<p><em>' + _markdownToHtml(b.note) + '</em></p>');
  return parts.join('\n');
};

_RENDERERS['quote'] = function(b) {
  var cite = b.attribution ? '<footer style="font-size:0.8rem;margin-top:6px;">— ' + _esc(b.attribution) + '</footer>' : '';
  return '<blockquote><p>' + _markdownToHtml(b.text || '') + '</p>' + cite + '</blockquote>';
};

_RENDERERS['closing'] = function(b) {
  var text = b.text ? '<p>' + _markdownToHtml(b.text) + '</p>' : '';
  var tags = b.tags || [];
  var tagsHtml = tags.length ? '<p style="color:#9ca3af;font-size:0.82rem;margin-top:8px;">' +
    tags.map(function(t){ return '#' + _esc(t); }).join(' ') + '</p>' : '';
  return '<div style="margin:1.5rem 0;">' + text + tagsHtml + '</div>';
};

_RENDERERS['pipeline'] = function(b) {
  var steps = b.steps || [];
  var flow = steps.map(function(s){ return '<code>' + _esc(s) + '</code>'; }).join(' ──► ');
  return '<p style="font-family:monospace;background:#f4f4f4;padding:12px 16px;border-radius:6px;overflow-x:auto;">' + flow + '</p>';
};

_RENDERERS['repo_links'] = function(b) {
  var links = b.links || [];
  var items = links.map(function(l){
    return '<li><strong>' + _esc(l.label || '') + ':</strong> <a href="' + _esc(l.url) + '" target="_blank">' + _esc(l.url.replace('https://','')) + '</a></li>';
  }).join('');
  return '<ul style="list-style:none;padding:0;">' + items + '</ul>';
};

_RENDERERS['before_after'] = function(b) {
  var beforeLabel = b.before_label || 'Before';
  var afterLabel = b.after_label || 'After';
  var lang = b.language || '';
  var beforeCode = (b.before || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  var afterCode = (b.after || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  var caption = b.caption ? '<p style="font-size:0.82rem;opacity:0.6;margin-top:8px;text-align:center;">' + _esc(b.caption) + '</p>' : '';
  function panel(label, code, color, bg) {
    return '<div style="flex:1;min-width:0;">' +
      '<div style="background:' + color + ';color:#fff;font-size:0.72rem;font-weight:700;padding:4px 12px;border-radius:6px 6px 0 0;letter-spacing:0.08em;">' + label + '</div>' +
      '<pre style="margin:0;padding:14px;background:' + bg + ';overflow-x:auto;font-size:0.82rem;border-radius:0 0 6px 6px;"><code class="language-' + _esc(lang) + '">' + code + '</code></pre></div>';
  }
  return '<div style="margin:1.5rem 0;">' +
    '<div style="display:flex;gap:12px;align-items:flex-start;">' +
    panel(beforeLabel, beforeCode, '#dc2626', '#1e1e1e') +
    panel(afterLabel, afterCode, '#16a34a', '#1e1e1e') +
    '</div>' + caption + '</div>';
};

_RENDERERS['api_reference'] = function(b) {
  var kind = b.kind || 'function';
  var name = b.name || '';
  var sig = b.signature || '';
  var desc = b.description || b.body || '';
  var params = b.params || b.parameters || [];
  var returns = b.returns || null;
  var example = b.example || '';
  var kindColors = {
    'function': ['#e8f0fe','#1a73e8'],
    'endpoint': ['#e6f4ea','#137333'],
    'class':    ['#fef7e0','#e37400'],
    'method':   ['#f3e8fd','#8430ce']
  };
  var kc = kindColors[kind] || kindColors['function'];
  var kindHtml = '<span style="background:' + kc[0] + ';color:' + kc[1] + ';font-size:0.72rem;font-weight:700;padding:3px 10px;border-radius:100px;text-transform:uppercase;letter-spacing:0.06em;">' + _esc(kind) + '</span>';
  var sigHtml = sig ? '<code style="font-size:0.9rem;margin-left:8px;">' + _esc(sig) + '</code>' : '<strong style="font-size:0.95rem;margin-left:8px;">' + _esc(name) + '</strong>';
  var descHtml = desc ? '<p style="margin:12px 0 0;font-size:0.88rem;color:#374151;">' + _markdownToHtml(desc) + '</p>' : '';
  var paramsHtml = '';
  if (params.length) {
    var rows = params.map(function(p){
      var req = p.required ? '<span style="color:#dc2626;font-size:0.72rem;font-weight:700;">required</span>' : '<span style="color:#9ca3af;font-size:0.72rem;">optional</span>';
      return '<tr>' +
        '<td style="padding:6px 10px;font-family:monospace;color:#7c3aed;">' + _esc(p.name||'') + '</td>' +
        '<td style="padding:6px 10px;font-family:monospace;color:#2563eb;">' + _esc(p.type||'') + '</td>' +
        '<td style="padding:6px 10px;">' + req + '</td>' +
        '<td style="padding:6px 10px;font-size:0.82rem;color:#374151;">' + _esc(p.description||p.desc||'') + '</td></tr>';
    }).join('');
    paramsHtml = '<div style="margin-top:14px;font-size:0.75rem;font-weight:700;color:#6b7280;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px;">Parameters</div>' +
      '<table style="width:100%;border-collapse:collapse;font-size:0.82rem;"><thead><tr style="background:#f9fafb;">' +
      '<th style="padding:6px 10px;text-align:left;">Name</th><th style="padding:6px 10px;text-align:left;">Type</th><th style="padding:6px 10px;text-align:left;">Required</th><th style="padding:6px 10px;text-align:left;">Description</th>' +
      '</tr></thead><tbody>' + rows + '</tbody></table>';
  }
  var returnsHtml = returns ? '<div style="margin-top:12px;font-size:0.82rem;color:#374151;"><strong>Returns:</strong> <code>' + _esc(returns.type||returns||'') + '</code>' + (returns.description ? ' — ' + _esc(returns.description) : '') + '</div>' : '';
  var exampleHtml = example ? '<div style="margin-top:14px;"><div style="font-size:0.72rem;font-weight:700;color:#6b7280;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px;">Example</div>' +
    '<pre style="background:#1e1e2e;color:#cdd6f4;padding:12px;border-radius:6px;overflow-x:auto;font-size:0.8rem;"><code>' + _esc(example).replace(/&amp;/g,'&').replace(/&lt;/g,'<').replace(/&gt;/g,'>') + '</code></pre></div>' : '';
  return '<div style="border:1px solid #e5e7eb;border-radius:10px;padding:18px 20px;margin:1.5rem 0;">' +
    '<div style="display:flex;align-items:center;flex-wrap:wrap;gap:6px;">' + kindHtml + sigHtml + '</div>' +
    descHtml + paramsHtml + returnsHtml + exampleHtml + '</div>';
};

_RENDERERS['steps'] = function(b) {
  var steps = b.steps || [];
  var items = steps.map(function(s, i){
    var text = typeof s === 'string' ? s : (s.text || s.label || '');
    var detail = typeof s === 'object' ? (s.detail || s.description || '') : '';
    var detailHtml = detail ? '<div style="font-size:0.85rem;color:#5f6368;margin-top:4px;">' + _markdownToHtml(detail) + '</div>' : '';
    return '<li style="display:flex;gap:14px;align-items:flex-start;margin-bottom:16px;">' +
      '<span style="flex:0 0 28px;height:28px;border-radius:50%;background:#1a73e8;color:#fff;font-size:0.8rem;font-weight:700;display:flex;align-items:center;justify-content:center;">' + (i+1) + '</span>' +
      '<div style="padding-top:4px;">' + _markdownToHtml(text) + detailHtml + '</div></li>';
  }).join('');
  return '<ol style="list-style:none;padding:0;margin:1.2rem 0;">' + items + '</ol>';
};

_RENDERERS['key_value'] = function(b) {
  var items = b.items || [];
  var rows = items.map(function(item){
    var req = item.required ? '<span style="color:#dc2626;font-size:0.7rem;font-weight:700;margin-left:4px;">required</span>' : '';
    var def = item.default !== undefined ? '<span style="color:#9ca3af;font-size:0.7rem;margin-left:4px;">default: ' + _esc(String(item.default)) + '</span>' : '';
    return '<tr>' +
      '<td style="padding:8px 12px;font-family:monospace;font-size:0.82rem;color:#1a73e8;white-space:nowrap;border-bottom:1px solid #f3f4f6;">' + _esc(item.key||item.name||'') + req + def + '</td>' +
      '<td style="padding:8px 12px;font-size:0.82rem;color:#374151;border-bottom:1px solid #f3f4f6;">' + _markdownToHtml(item.description||item.value||'') + '</td></tr>';
  }).join('');
  return '<table style="width:100%;border-collapse:collapse;margin:1rem 0;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;">' +
    '<thead><tr style="background:#f9fafb;"><th style="padding:8px 12px;text-align:left;font-size:0.75rem;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;">Key</th><th style="padding:8px 12px;text-align:left;font-size:0.75rem;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;">Description</th></tr></thead>' +
    '<tbody>' + rows + '</tbody></table>';
};

_RENDERERS['timeline'] = function(b) {
  var events = b.events || [];
  var accent = b.accent || '#1a73e8';
  var titleHtml = b.title ? '<p style="font-weight:700;font-size:1.05rem;margin-bottom:20px;">' + _esc(b.title) + '</p>' : '';
  var items = events.map(function(ev, i){
    var isLast = i === events.length - 1;
    var date = ev.date || '';
    var label = ev.label || '';
    var text = ev.text || '';
    var tag = ev.tag || '';
    var tagHtml = tag ? '<span style="background:' + accent + '18;color:' + accent + ';font-size:0.72rem;font-weight:700;padding:2px 8px;border-radius:10px;margin-left:8px;">' + _esc(tag) + '</span>' : '';
    var connector = isLast ? '' : '<div style="width:2px;background:#e0e0e0;flex:1;min-height:24px;margin-top:4px;"></div>';
    return '<div style="display:flex;gap:0;position:relative;">' +
      '<div style="display:flex;flex-direction:column;align-items:center;width:40px;flex:0 0 40px;">' +
      '<div style="width:14px;height:14px;border-radius:50%;background:' + accent + ';border:3px solid #fff;box-shadow:0 0 0 2px ' + accent + ';flex:0 0 14px;margin-top:3px;z-index:1;"></div>' +
      connector + '</div>' +
      '<div style="padding-bottom:28px;padding-left:12px;flex:1;min-width:0;">' +
      '<div style="display:flex;align-items:baseline;flex-wrap:wrap;gap:6px;margin-bottom:4px;">' +
      '<span style="font-size:0.78rem;font-weight:600;color:' + accent + ';font-family:monospace;">' + _esc(date) + '</span>' + tagHtml + '</div>' +
      '<p style="font-weight:700;font-size:0.95rem;margin:0 0 4px;">' + _esc(label) + '</p>' +
      '<p style="color:#5f6368;font-size:0.88rem;line-height:1.6;margin:0;">' + _markdownToHtml(text) + '</p>' +
      '</div></div>';
  }).join('');
  return '<div style="margin:1.5rem 0;padding:20px 20px 0;background:#fafafa;border-radius:10px;border:1px solid #e0e0e0;">' + titleHtml + items + '</div>';
};

_RENDERERS['annotated_code'] = function(b) {
  var lang = b.language || '';
  var codeLines = (b.code || '').split('\n');
  var annotations = b.annotations || [];
  var caption = b.caption || '';
  var lineMap = {};
  annotations.forEach(function(a, i){ lineMap[a.line] = i + 1; });
  var renderedLines = codeLines.map(function(line, i){
    var n = i + 1;
    var escaped = line.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    if (lineMap[n]) {
      var num = lineMap[n];
      var badge = '<span style="display:inline-flex;align-items:center;justify-content:center;width:18px;height:18px;border-radius:50%;background:#f9ab00;color:#fff;font-size:0.7rem;font-weight:800;margin-left:8px;vertical-align:middle;">' + num + '</span>';
      return '<span style="display:block;">' + escaped + badge + '</span>';
    }
    return '<span style="display:block;">' + escaped + '</span>';
  }).join('');
  var captionHtml = caption ? '<p style="font-size:0.8rem;opacity:0.6;margin:6px 0 0;text-align:center;">' + _esc(caption) + '</p>' : '';
  var annotationItems = annotations.map(function(a, i){
    return '<li style="display:flex;gap:12px;margin-bottom:12px;align-items:flex-start;">' +
      '<span style="flex:0 0 22px;height:22px;border-radius:50%;background:#f9ab00;color:#fff;font-size:0.72rem;font-weight:800;display:flex;align-items:center;justify-content:center;">' + (i+1) + '</span>' +
      '<span style="font-size:0.88rem;color:#3c4043;line-height:1.6;padding-top:2px;">' + _markdownToHtml(a.text||'') + '</span></li>';
  }).join('');
  return '<div style="margin:1.5rem 0;">' +
    '<pre style="margin:0;padding:18px;background:#1e1e2e;border-radius:10px 10px 0 0;overflow-x:auto;font-size:0.84rem;line-height:1.7;color:#cdd6f4;">' +
    '<code class="language-' + _esc(lang) + '">' + renderedLines + '</code></pre>' +
    captionHtml +
    '<ol style="list-style:none;padding:16px 20px;margin:0;background:#fffbf0;border:1px solid #f9ab0033;border-top:none;border-radius:0 0 10px 10px;">' + annotationItems + '</ol></div>';
};

_RENDERERS['key_takeaways'] = function(b) {
  var raw = b.items || b.points || [];
  var lis = raw.map(function(p){
    var text = typeof p === 'object' ? (p.text || '') : p;
    return '<li style="margin-bottom:6px;font-size:0.88rem;color:#1e3a5f;">' + _markdownToHtml(text) + '</li>';
  }).join('');
  return '<div style="border:1px solid #bfdbfe;border-left:4px solid #2563eb;border-radius:8px;padding:16px 20px;background:#eff6ff;margin:1.2rem 0;">' +
    '<div style="font-weight:700;color:#1d4ed8;margin-bottom:10px;">🔑 Key takeaways</div>' +
    '<ul style="margin:0;padding-left:1.2em;">' + lis + '</ul></div>';
};

_RENDERERS['summary_box'] = function(b) {
  return '<div style="border:1px solid #e5e7eb;border-radius:10px;padding:18px 22px;background:#f9fafb;margin:1.2rem 0;">' +
    '<div style="font-weight:700;color:#374151;margin-bottom:8px;font-size:0.82rem;text-transform:uppercase;letter-spacing:0.08em;">Summary</div>' +
    '<p style="margin:0;color:#4b5563;font-size:0.9rem;line-height:1.6;">' + _markdownToHtml(b.text||'') + '</p></div>';
};

_RENDERERS['learning_objectives'] = function(b) {
  var objs = b.objectives || [];
  var lis = objs.map(function(o){
    return '<li style="display:flex;align-items:flex-start;gap:8px;margin-bottom:6px;font-size:0.88rem;">' +
      '<span style="color:#2563eb;flex-shrink:0;margin-top:1px;">→</span>' +
      '<span style="color:#1e3a5f;">' + _esc(o) + '</span></li>';
  }).join('');
  return '<div style="border:1px solid #bfdbfe;border-radius:10px;padding:16px 20px;background:#eff6ff;margin:1.2rem 0;">' +
    '<div style="font-weight:700;color:#1d4ed8;margin-bottom:10px;">🎯 What you\'ll learn</div>' +
    '<ul style="list-style:none;padding:0;margin:0;">' + lis + '</ul></div>';
};

_RENDERERS['changelog_entry'] = function(b) {
  var version = b.version || '';
  var date = b.date || '';
  var changes = b.changes || [];
  var tagColors = {added:'#16a34a',fixed:'#2563eb',changed:'#d97706',removed:'#dc2626',deprecated:'#7c3aed'};
  var items = changes.map(function(c){
    var type = (c.type || 'changed').toLowerCase();
    var color = tagColors[type] || '#6b7280';
    return '<div style="display:flex;gap:8px;align-items:flex-start;margin-bottom:4px;">' +
      '<span style="font-size:0.7rem;font-weight:700;padding:2px 6px;border-radius:4px;flex-shrink:0;background:' + color + '22;color:' + color + ';">' + type.toUpperCase() + '</span>' +
      '<span style="font-size:0.85rem;color:#374151;">' + _esc(c.text||'') + '</span></div>';
  }).join('');
  return '<div style="border:1px solid #e5e7eb;border-radius:10px;padding:16px 20px;margin:1.2rem 0;">' +
    '<div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">' +
    '<span style="font-family:monospace;font-weight:700;font-size:0.95rem;color:#374151;">v' + _esc(version) + '</span>' +
    (date ? '<span style="font-size:0.8rem;color:#9ca3af;">' + _esc(date) + '</span>' : '') +
    '</div>' + items + '</div>';
};

_RENDERERS['release_notes'] = function(b) {
  var title = b.title || 'Release Notes';
  function section(label, items, color) {
    if (!items || !items.length) return '';
    var lis = items.map(function(i){ return '<li style="font-size:0.85rem;color:#374151;margin-bottom:3px;">' + _esc(i) + '</li>'; }).join('');
    return '<div style="margin-bottom:14px;"><div style="font-weight:700;font-size:0.78rem;text-transform:uppercase;letter-spacing:0.08em;color:' + color + ';margin-bottom:6px;">' + label + '</div><ul style="margin:0;padding-left:1.2em;">' + lis + '</ul></div>';
  }
  return '<div style="border:1px solid #e5e7eb;border-radius:10px;padding:18px 22px;margin:1.2rem 0;">' +
    '<div style="font-weight:700;font-size:1rem;color:#111827;margin-bottom:14px;">' + _esc(title) + '</div>' +
    section('Added', b.added, '#16a34a') +
    section('Fixed', b.fixed, '#2563eb') +
    section('Changed', b.changed, '#d97706') +
    '</div>';
};

_RENDERERS['further_reading'] = function(b) {
  var links = b.links || [];
  var items = links.map(function(l){
    var annotation = l.annotation ? '<div style="font-size:0.78rem;color:#6b7280;margin-top:2px;">' + _esc(l.annotation) + '</div>' : '';
    return '<a href="' + _esc(l.url||'#') + '" target="_blank" rel="noopener" style="display:flex;align-items:flex-start;gap:10px;padding:10px 0;border-bottom:1px solid #f3f4f6;text-decoration:none;">' +
      '<span style="color:#2563eb;flex-shrink:0;margin-top:2px;">→</span>' +
      '<div><div style="font-size:0.88rem;font-weight:600;color:#1d4ed8;">' + _esc(l.title||'') + '</div>' + annotation + '</div></a>';
  }).join('');
  return '<div style="border:1px solid #e5e7eb;border-radius:10px;padding:16px 20px;margin:1.2rem 0;">' +
    '<div style="font-weight:700;color:#374151;margin-bottom:4px;">📚 Further reading</div>' + items + '</div>';
};

_RENDERERS['resources_list'] = function(b) {
  var items = b.items || [];
  var rows = items.map(function(item){
    var size = item.size ? '<span style="font-size:0.75rem;color:#9ca3af;">' + _esc(item.size) + '</span>' : '';
    var type = item.type ? '<span style="font-size:0.72rem;background:#f3f4f6;padding:2px 6px;border-radius:4px;color:#6b7280;">' + _esc(item.type.toUpperCase()) + '</span>' : '';
    return '<a href="' + _esc(item.url||'#') + '" target="_blank" rel="noopener" style="display:flex;align-items:center;justify-content:space-between;padding:10px 0;border-bottom:1px solid #f3f4f6;text-decoration:none;">' +
      '<span style="font-size:0.88rem;color:#1d4ed8;font-weight:500;">' + _esc(item.title||'') + '</span>' +
      '<div style="display:flex;align-items:center;gap:8px;">' + size + type + '</div></a>';
  }).join('');
  return '<div style="border:1px solid #e5e7eb;border-radius:10px;padding:16px 20px;margin:1.2rem 0;">' +
    '<div style="font-weight:700;color:#374151;margin-bottom:4px;">📎 Resources</div>' + rows + '</div>';
};

_RENDERERS['sidebar_note'] = function(b) {
  return '<div style="border-left:3px solid #7c3aed;border-radius:0 8px 8px 0;padding:12px 16px;background:#faf5ff;margin:1.2rem 0;">' +
    '<div style="font-weight:700;font-size:0.8rem;color:#7c3aed;margin-bottom:4px;">' + _esc(b.title||'Note') + '</div>' +
    '<p style="margin:0;font-size:0.85rem;color:#4b5563;">' + _markdownToHtml(b.content||'') + '</p></div>';
};

_RENDERERS['difficulty_badge'] = function(b) {
  var level = b.level || 'beginner';
  var cfg = {beginner:['#16a34a','#f0fdf4','Beginner','⚡'], intermediate:['#d97706','#fffbeb','Intermediate','🔧'], advanced:['#dc2626','#fef2f2','Advanced','🚀']};
  var c = cfg[level] || cfg.beginner;
  return '<span style="display:inline-flex;align-items:center;gap:5px;border:1px solid ' + c[0] + '44;border-radius:100px;padding:3px 12px;font-size:0.75rem;font-weight:700;color:' + c[0] + ';background:' + c[1] + ';">' + c[3] + ' ' + c[2] + '</span>';
};

_RENDERERS['caution_block'] = function(b) {
  return '<div style="border:1px solid #fca5a5;border-left:4px solid #ef4444;border-radius:8px;padding:14px 18px;background:#fef2f2;margin:1.2rem 0;">' +
    '<div style="font-weight:700;color:#991b1b;margin-bottom:6px;">⚠ Caution</div>' +
    '<p style="margin:0;font-size:0.88rem;color:#7f1d1d;">' + _markdownToHtml(b.message||b.text||'') + '</p></div>';
};

_RENDERERS['checklist_interactive'] = function(b) {
  var items = b.items || [];
  var lis = items.map(function(item){
    var text = typeof item === 'string' ? item : (item.text || item.label || '');
    return '<li style="display:flex;align-items:center;gap:10px;padding:6px 0;border-bottom:1px solid #f3f4f6;">' +
      '<input type="checkbox" style="width:16px;height:16px;accent-color:#7c3aed;cursor:pointer;">' +
      '<span style="font-size:0.88rem;color:#374151;">' + _esc(text) + '</span></li>';
  }).join('');
  return '<ul style="list-style:none;padding:12px 18px;margin:1.2rem 0;border:1px solid #e5e7eb;border-radius:10px;">' + lis + '</ul>';
};

_RENDERERS['glossary_inline'] = function(b) {
  var defn = (b.definition || '').replace(/"/g,'&quot;');
  return '<span style="position:relative;display:inline-block;">' +
    '<span style="border-bottom:2px dotted #7c3aed;cursor:help;color:#7c3aed;font-weight:600;" title="' + defn + '">' + _esc(b.term||'') + '</span></span>';
};

_RENDERERS['time_estimate'] = function(b) {
  return '<span style="display:inline-flex;align-items:center;gap:5px;font-size:0.78rem;color:#6b7280;background:#f3f4f6;padding:3px 10px;border-radius:100px;">🕐 ' + _esc(String(b.minutes||5)) + ' min read</span>';
};

_RENDERERS['progress_checkpoint'] = function(b) {
  var current = b.current_step || 1;
  var total = b.total_steps || 1;
  var pct = Math.round(current / total * 100);
  var steps = '';
  for (var i = 1; i <= total; i++) {
    steps += '<div style="width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:0.75rem;font-weight:700;background:' + (i < current ? '#7c3aed' : '#e5e7eb') + ';color:' + (i < current ? '#fff' : '#9ca3af') + ';">' + i + '</div>';
  }
  return '<div style="border:1px solid #e5e7eb;border-radius:10px;padding:14px 18px;margin:1.2rem 0;">' +
    '<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;flex-wrap:wrap;">' + steps + '</div>' +
    '<div style="background:#f3f4f6;border-radius:100px;height:6px;overflow:hidden;">' +
    '<div style="height:100%;background:#7c3aed;width:' + pct + '%;border-radius:100px;"></div></div>' +
    '<div style="font-size:0.78rem;color:#6b7280;margin-top:6px;">Step ' + current + ' of ' + total + '</div></div>';
};

_RENDERERS['social_share_bar'] = function(b) {
  var platforms = b.platforms || ['twitter','linkedin'];
  var url = b.url || '';
  var cfg = {
    twitter: ['#1da1f2','X / Twitter','https://twitter.com/intent/tweet?url=' + encodeURIComponent(url)],
    linkedin: ['#0a66c2','LinkedIn','https://www.linkedin.com/sharing/share-offsite/?url=' + encodeURIComponent(url)],
    facebook: ['#1877f2','Facebook','https://www.facebook.com/sharer/sharer.php?u=' + encodeURIComponent(url)],
    reddit: ['#ff4500','Reddit','https://reddit.com/submit?url=' + encodeURIComponent(url)]
  };
  var btns = platforms.filter(function(p){ return cfg[p]; }).map(function(p){
    var c = cfg[p];
    return '<a href="' + _esc(c[2]) + '" target="_blank" rel="noopener" style="display:inline-flex;align-items:center;gap:6px;padding:7px 14px;border-radius:6px;background:' + c[0] + ';color:#fff;font-size:0.8rem;font-weight:600;text-decoration:none;">' + c[1] + '</a>';
  }).join('');
  return '<div style="display:flex;flex-wrap:wrap;gap:8px;margin:1.2rem 0;">' + btns + '</div>';
};

_RENDERERS['newsletter_cta'] = function(b) {
  var headline = b.headline || 'Stay in the loop';
  var buttonLabel = b.button_label || 'Subscribe';
  return '<div style="border:1px solid #e5e7eb;border-radius:12px;padding:24px 28px;background:linear-gradient(135deg,#f9fafb,#f3f4f6);margin:1.5rem 0;text-align:center;">' +
    '<div style="font-size:1.1rem;font-weight:700;color:#111827;margin-bottom:8px;">' + _esc(headline) + '</div>' +
    '<div style="display:flex;gap:8px;max-width:400px;margin:12px auto 0;">' +
    '<input type="email" placeholder="you@example.com" style="flex:1;padding:8px 14px;border:1px solid #d1d5db;border-radius:6px;font-size:0.88rem;">' +
    '<button style="padding:8px 18px;background:#7c3aed;color:#fff;border:none;border-radius:6px;font-weight:600;font-size:0.88rem;cursor:pointer;">' + _esc(buttonLabel) + '</button>' +
    '</div></div>';
};

_RENDERERS['color_swatch_grid'] = function(b) {
  var colors = b.colors || [];
  var cols = Math.min(colors.length || 4, 6);
  var items = colors.map(function(c){
    return '<div style="display:flex;flex-direction:column;gap:4px;">' +
      '<div style="width:100%;height:40px;background:' + _esc(c.hex||'#e5e7eb') + ';border-radius:4px;"></div>' +
      '<div style="font-size:0.65rem;color:#6b7280;text-align:center;">' + _esc(c.name||'') + '</div>' +
      '<div style="font-size:0.6rem;color:#9ca3af;text-align:center;font-family:monospace;">' + _esc(c.hex||'') + '</div></div>';
  }).join('');
  return '<div style="display:grid;grid-template-columns:repeat(' + cols + ',1fr);gap:8px;margin:1rem 0;">' + items + '</div>';
};

_RENDERERS['article_hero'] = function(b) {
  var title = b.title || '';
  var subtitle = b.subtitle || b.overline || '';
  var imgUrl = b.image || b.image_url || '';
  var imgHtml = imgUrl ? '<img src="' + _esc(imgUrl) + '" alt="' + _esc(title) + '" style="width:100%;height:220px;object-fit:cover;border-radius:12px;margin-bottom:16px;display:block;">' : '';
  var subHtml = subtitle ? '<p style="margin:0 0 4px;font-size:0.78rem;font-weight:600;color:#7c3aed;text-transform:uppercase;letter-spacing:0.05em;">' + _esc(subtitle) + '</p>' : '';
  return '<div style="margin:1.5rem 0;">' + imgHtml + subHtml + '<h1 style="margin:0;font-size:2rem;font-weight:800;color:#111827;line-height:1.2;">' + _esc(title) + '</h1></div>';
};

_RENDERERS['table_of_contents'] = function(b) {
  var items = b.items || b.headings || [];
  var rows = items.map(function(item){
    var text = item.text || item.title || '';
    var level = item.level || 1;
    var indent = level > 1 ? 'padding-left:1.2rem;' : '';
    var prefix = level > 1 ? '└ ' : '';
    var size = level === 1 ? '0.9rem' : '0.85rem';
    return '<li style="margin:4px 0;' + indent + '"><a href="#" style="color:#7c3aed;text-decoration:none;font-size:' + size + ';">' + prefix + _esc(text) + '</a></li>';
  }).join('');
  return '<div style="border:1px solid #e5e7eb;border-radius:10px;padding:16px 20px;background:#f9fafb;margin:1.5rem 0;">' +
    '<div style="font-weight:700;color:#374151;margin-bottom:10px;font-size:0.85rem;">Contents</div>' +
    '<ul style="list-style:none;padding:0;margin:0;">' + rows + '</ul></div>';
};

_RENDERERS['reading_progress_bar'] = function(b) {
  var color = b.color || '#7c3aed';
  var pct = b.percentage || 45;
  return '<div style="margin:1rem 0;">' +
    '<div style="font-size:0.75rem;color:#6b7280;margin-bottom:4px;">Reading progress</div>' +
    '<div style="height:3px;background:#e5e7eb;border-radius:2px;">' +
    '<div style="height:100%;width:' + pct + '%;background:' + _esc(color) + ';border-radius:2px;"></div></div>' +
    '<div style="font-size:0.7rem;color:#9ca3af;margin-top:2px;">' + pct + '% complete</div></div>';
};

_RENDERERS['scroll_to_top'] = function(b) {
  return '<div style="margin:1rem 0;display:flex;align-items:center;gap:10px;">' +
    '<button style="width:40px;height:40px;border-radius:50%;background:#7c3aed;color:#fff;border:none;cursor:pointer;font-size:1rem;display:flex;align-items:center;justify-content:center;">↑</button>' +
    '<span style="font-size:0.8rem;color:#6b7280;">Scroll-to-top button — appears fixed bottom-right after scrolling 300px</span></div>';
};



// === Batch 2: Navigation, UI Components, Code Tools ===

_RENDERERS['tabs'] = function(b) {
  var tabList = b.tabs || [];
  if (!tabList.length) return '';
  var uid = Math.random().toString(36).substr(2,6);
  var css = '<style>';
  tabList.forEach(function(t, i){
    css += '#tb' + uid + '_' + i + ':checked ~ .tm-tab-panels-' + uid + ' .tm-tab-panel-' + uid + ':nth-child(' + (i+1) + '){display:block;}';
  });
  css += '</style>';
  var inputs = tabList.map(function(t, i){
    return '<input type="radio" id="tb' + uid + '_' + i + '" name="tab_' + uid + '" style="display:none;"' + (i===0?' checked':'') + '>';
  }).join('');
  var labels = '<div style="display:flex;flex-wrap:wrap;border-bottom:2px solid #e5e7eb;margin-bottom:0;">' +
    tabList.map(function(t, i){
      return '<label for="tb' + uid + '_' + i + '" style="padding:10px 18px;cursor:pointer;font-size:0.85rem;font-weight:600;color:#5f6368;white-space:nowrap;border-bottom:2px solid transparent;margin-bottom:-2px;transition:color 0.15s;">' + _esc(t.label||('Tab '+(i+1))) + '</label>';
    }).join('') + '</div>';
  var panels = '<div class="tm-tab-panels-' + uid + '">' +
    tabList.map(function(t, i){
      var content = '';
      if (t.blocks && t.blocks.length) {
        t.blocks.forEach(function(blk){
          var fn = _RENDERERS[blk.component || blk.type];
          if (fn) content += fn(blk);
        });
      } else if (t.content) {
        content = '<p>' + _markdownToHtml(t.content) + '</p>';
      } else if (t.code) {
        content = '<pre><code>' + _esc(t.code) + '</code></pre>';
      }
      return '<div class="tm-tab-panel-' + uid + '" style="display:none;padding:16px;">' + content + '</div>';
    }).join('') + '</div>';
  return '<div style="margin:1.5rem 0;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;">' + css + inputs + labels + panels + '</div>';
};

_RENDERERS['gallery'] = function(b) {
  var images = b.images || [];
  var cols = b.cols || 3;
  var caption = b.caption || '';
  var gid = 'g' + Math.random().toString(36).substr(2,6);
  var css = '<style>' +
    '.' + gid + '-wrap{display:grid;grid-template-columns:repeat(' + cols + ',1fr);gap:10px;margin:1.5rem 0;}' +
    '@media(max-width:600px){.' + gid + '-wrap{grid-template-columns:repeat(2,1fr);}}' +
    '.' + gid + '-item{position:relative;overflow:hidden;border-radius:8px;cursor:zoom-in;aspect-ratio:16/10;background:#f1f3f4;}' +
    '.' + gid + '-item img{width:100%;height:100%;object-fit:cover;display:block;transition:transform 0.2s ease;}' +
    '.' + gid + '-item:hover img{transform:scale(1.04);}' +
    '.' + gid + '-lb{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.92);z-index:9999;align-items:center;justify-content:center;padding:20px;}' +
    '.' + gid + '-lb:target{display:flex;}' +
    '.' + gid + '-lb img{max-width:90vw;max-height:88vh;border-radius:8px;}' +
    '.' + gid + '-lb-close{position:absolute;top:16px;right:24px;color:#fff;font-size:2rem;text-decoration:none;line-height:1;opacity:0.7;}' +
    '</style>';
  var items = images.map(function(img, i){
    var lbId = gid + '-lb' + i;
    var capHtml = img.caption ? '<figcaption style="position:absolute;bottom:0;left:0;right:0;padding:6px 10px;background:linear-gradient(transparent,rgba(0,0,0,0.6));color:#fff;font-size:0.75rem;">' + _esc(img.caption) + '</figcaption>' : '';
    return '<figure class="' + gid + '-item"><a href="#' + lbId + '" style="display:block;height:100%;"><img src="' + _esc(img.url||'') + '" alt="' + _esc(img.alt||'') + '" loading="lazy"></a>' + capHtml + '</figure>';
  }).join('');
  var lightboxes = images.map(function(img, i){
    var lbId = gid + '-lb' + i;
    return '<div id="' + lbId + '" class="' + gid + '-lb"><a href="#" class="' + gid + '-lb-close">✕</a><img src="' + _esc(img.url||'') + '" alt="' + _esc(img.alt||'') + '"></div>';
  }).join('');
  var captionHtml = caption ? '<p style="font-size:0.82rem;opacity:0.6;margin-top:10px;text-align:center;">' + _esc(caption) + '</p>' : '';
  return css + '<div class="' + gid + '-wrap">' + items + '</div>' + captionHtml + lightboxes;
};

_RENDERERS['carousel'] = function(b) {
  var slides = b.slides || [];
  if (!slides.length) return '';
  var accent = b.accent || '#1a73e8';
  var cid = 'c' + Math.random().toString(36).substr(2,6);
  var n = slides.length;
  var css = '<style>' +
    '.' + cid + '{position:relative;overflow:hidden;border-radius:12px;background:#000;margin:1.5rem 0;}' +
    '.' + cid + ' input[type=radio]{display:none;}' +
    '.' + cid + '-track{display:flex;transition:transform 0.45s cubic-bezier(0.77,0,0.175,1);width:' + (n*100) + '%;}' +
    '.' + cid + '-slide{width:' + Math.floor(100/n) + '%;flex:0 0 ' + Math.floor(100/n) + '%;position:relative;}' +
    '.' + cid + '-slide img{width:100%;display:block;max-height:480px;object-fit:cover;}' +
    '.' + cid + '-cap{position:absolute;bottom:0;left:0;right:0;padding:14px 18px;background:linear-gradient(transparent,rgba(0,0,0,0.72));color:#fff;}' +
    '.' + cid + '-dots{display:flex;justify-content:center;gap:8px;padding:12px;background:#111;}' +
    '.' + cid + '-dot{width:8px;height:8px;border-radius:50%;background:rgba(255,255,255,0.3);cursor:pointer;display:block;border:none;}' +
    '</style>';
  var perSlide = '';
  for (var i = 1; i <= n; i++) {
    var offset = (i-1) * Math.floor(100/n);
    perSlide += '<style>#' + cid + '_s' + i + ':checked ~ .' + cid + '-inner .' + cid + '-track{transform:translateX(-' + offset + '%);}</style>';
    perSlide += '<style>#' + cid + '_s' + i + ':checked ~ .' + cid + '-dots .' + cid + '-dot:nth-child(' + i + '){background:' + accent + ';transform:scale(1.25);}</style>';
  }
  var inputs = slides.map(function(s,i){ return '<input type="radio" id="' + cid + '_s' + (i+1) + '" name="' + cid + '"' + (i===0?' checked':'') + '>'; }).join('');
  var slidesHtml = slides.map(function(slide){
    var capHtml = slide.label ? '<div class="' + cid + '-cap"><strong>' + _esc(slide.label) + '</strong>' + (slide.subtitle ? '<span style="display:block;font-size:0.82rem;opacity:0.8;">' + _esc(slide.subtitle) + '</span>' : '') + '</div>' : '';
    return '<div class="' + cid + '-slide"><img src="' + _esc(slide.url||'') + '" alt="' + _esc(slide.label||'') + '" loading="lazy">' + capHtml + '</div>';
  }).join('');
  var dots = slides.map(function(s,i){ return '<label for="' + cid + '_s' + (i+1) + '" class="' + cid + '-dot"></label>'; }).join('');
  var captionHtml = b.caption ? '<p style="font-size:0.82rem;opacity:0.6;margin-top:8px;text-align:center;">' + _esc(b.caption) + '</p>' : '';
  return css + perSlide + '<div class="' + cid + '">' + inputs + '<div class="' + cid + '-inner"><div class="' + cid + '-track">' + slidesHtml + '</div></div><div class="' + cid + '-dots">' + dots + '</div></div>' + captionHtml;
};

_RENDERERS['stat_card'] = function(b) {
  var value = b.value !== undefined ? b.value : '—';
  var label = b.label || '';
  var delta = b.delta || '';
  var accent = b.accent || '#00f2ff';
  var isUp = b.is_up !== false;
  var deltaColor = isUp ? '#00ff88' : '#ff4444';
  var deltaArrow = isUp ? '▲' : '▼';
  var deltaHtml = delta ? '<span style="font-size:0.85rem;font-weight:700;color:' + deltaColor + ';margin-left:10px;">' + deltaArrow + ' ' + _esc(String(delta)) + '</span>' : '';
  return '<div style="display:inline-block;background:linear-gradient(135deg,#0d1117 0%,#1a1f2e 100%);border:1px solid ' + accent + '44;border-radius:12px;padding:24px 32px;margin:1rem 0;box-shadow:0 0 20px ' + accent + '22,inset 0 0 20px ' + accent + '08;min-width:200px;text-align:center;">' +
    '<div style="font-size:0.75rem;font-weight:700;color:' + accent + ';letter-spacing:0.12em;text-transform:uppercase;margin-bottom:8px;">' + _esc(label) + '</div>' +
    '<div style="font-size:2.8rem;font-weight:900;color:#ffffff;line-height:1;font-family:monospace;">' + _esc(String(value)) + deltaHtml + '</div></div>';
};

_RENDERERS['progress_bar'] = function(b) {
  var uid = Math.random().toString(36).substr(2,6);
  var value = Math.min(100, Math.max(0, parseInt(b.value||0)));
  var label = b.label || '';
  var accent = b.accent || '#00f2ff';
  var showPct = b.show_percent !== false;
  var caption = b.caption || '';
  var pctHtml = showPct ? '<span style="font-size:0.8rem;font-weight:700;color:' + accent + ';">' + value + '%</span>' : '';
  var captionHtml = caption ? '<p style="font-size:0.78rem;opacity:0.5;margin-top:4px;">' + _esc(caption) + '</p>' : '';
  return '<style>@keyframes pb' + uid + '-glow{0%,100%{box-shadow:0 0 6px ' + accent + '88;}50%{box-shadow:0 0 16px ' + accent + ';}}</style>' +
    '<div style="margin:1rem 0;">' +
    '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">' +
    '<span style="font-size:0.85rem;font-weight:600;">' + _esc(label) + '</span>' + pctHtml + '</div>' +
    '<div style="background:rgba(255,255,255,0.08);border-radius:100px;height:10px;overflow:hidden;">' +
    '<div style="width:' + value + '%;height:100%;border-radius:100px;background:linear-gradient(90deg,' + accent + ',' + accent + '99);animation:pb' + uid + '-glow 2s ease-in-out infinite;"></div></div>' +
    captionHtml + '</div>';
};

_RENDERERS['badge_group'] = function(b) {
  var badges = b.badges || [];
  var title = b.title || '';
  var titleHtml = title ? '<p style="font-size:0.82rem;font-weight:600;margin-bottom:8px;opacity:0.7;">' + _esc(title) + '</p>' : '';
  var colorMap = {green:['#00ff88','#003322'],cyan:['#00f2ff','#002233'],blue:['#4285f4','#001a44'],yellow:['#f9ab00','#332200'],red:['#ff4444','#330011'],purple:['#a855f7','#1a0033'],grey:['#9aa0a6','#1a1a1a']};
  var items = badges.map(function(badge){
    var colors = colorMap[badge.color||'grey'] || colorMap.grey;
    var fg = colors[0]; var bg = colors[1];
    var dot = badge.pulse ? '<span style="width:7px;height:7px;border-radius:50%;background:' + fg + ';display:inline-block;margin-right:6px;"></span>' : '';
    return '<span style="display:inline-flex;align-items:center;background:' + bg + ';color:' + fg + ';border:1px solid ' + fg + '44;border-radius:100px;padding:4px 12px;font-size:0.78rem;font-weight:700;letter-spacing:0.04em;margin:3px;">' + dot + _esc(badge.text||'') + '</span>';
  }).join('');
  return '<div style="margin:1rem 0;">' + titleHtml + '<div style="display:flex;flex-wrap:wrap;gap:4px;">' + items + '</div></div>';
};

_RENDERERS['stepper'] = function(b) {
  var steps = b.steps || [];
  var activeIdx = parseInt(b.active_index || 0);
  var color = b.color || '#38bdf8';
  var heading = b.label || b.title || '';
  var norm = steps.map(function(s){
    if (typeof s === 'string') return {label:s, description:'', state:'pending'};
    return {label:s.label||s.title||'', description:s.description||s.body||'', state:s.is_current?'active':(s.is_completed?'completed':'pending')};
  });
  var headingHtml = heading ? '<div style="font-size:0.85rem;font-weight:700;color:#64748b;letter-spacing:.07em;text-transform:uppercase;margin-bottom:16px;">' + _esc(heading) + '</div>' : '';
  var items = norm.map(function(step, i){
    var completed = step.state === 'completed' || (step.state === 'pending' && i < activeIdx);
    var active = step.state === 'active' || i === activeIdx;
    var lc, dc, indicator;
    if (completed) {
      indicator = '<div style="width:28px;height:28px;border-radius:50%;flex-shrink:0;background:' + color + '22;border:2px solid ' + color + ';display:flex;align-items:center;justify-content:center;color:' + color + ';font-size:0.8rem;">✓</div>';
      lc = '#cbd5e1'; dc = '#475569';
    } else if (active) {
      indicator = '<div style="width:28px;height:28px;border-radius:50%;flex-shrink:0;border:2px solid ' + color + ';background:' + color + '22;display:flex;align-items:center;justify-content:center;"><div style="width:8px;height:8px;border-radius:50%;background:' + color + ';"></div></div>';
      lc = '#f1f5f9'; dc = '#94a3b8';
    } else {
      indicator = '<div style="width:28px;height:28px;border-radius:50%;flex-shrink:0;border:2px solid #334155;background:#1e293b;display:flex;align-items:center;justify-content:center;"><div style="width:6px;height:6px;border-radius:50%;background:#475569;"></div></div>';
      lc = '#64748b'; dc = '#374151';
    }
    var descHtml = step.description ? '<div style="font-size:0.8rem;color:' + dc + ';margin-top:2px;">' + _esc(step.description) + '</div>' : '';
    var connector = i < norm.length - 1 ? '<div style="width:2px;height:14px;margin:3px 0 3px 13px;background:' + (completed ? color : '#1e293b') + ';border-radius:1px;"></div>' : '';
    return '<div><div style="display:flex;align-items:flex-start;gap:12px;">' + indicator + '<div style="padding-top:4px;"><div style="font-size:0.95rem;font-weight:600;color:' + lc + ';">' + _esc(step.label) + '</div>' + descHtml + '</div></div>' + connector + '</div>';
  }).join('');
  return '<div style="background:#0f172a;border:1px solid #1e293b;border-radius:14px;padding:20px 24px;margin:1rem 0;">' + headingHtml + items + '</div>';
};

_RENDERERS['faq_accordion'] = function(b) {
  var items = b.items || b.questions || [];
  var html = items.map(function(item){
    var q = item.question || item.label || '';
    var a = item.answer || item.text || item.body || '';
    return '<details style="border-bottom:1px solid #e5e7eb;">' +
      '<summary style="padding:14px 16px;cursor:pointer;font-weight:600;font-size:0.88rem;color:#111827;list-style:none;">' + _esc(q) + '</summary>' +
      '<div style="padding:0 16px 16px;font-size:0.85rem;color:#374151;line-height:1.6;">' + _markdownToHtml(a) + '</div></details>';
  }).join('');
  return '<div style="border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;margin:1.2rem 0;">' + html + '</div>';
};

_RENDERERS['footnote'] = function(b) {
  var fid = b.id || '1';
  return '<div style="margin:0.5rem 0;font-size:0.78rem;color:#6b7280;padding-left:1.2rem;border-left:2px solid #e5e7eb;"><sup style="color:#7c3aed;font-weight:600;">[' + _esc(String(fid)) + ']</sup> ' + _markdownToHtml(b.text||'') + '</div>';
};

_RENDERERS['footnote_group'] = function(b) {
  var footnotes = b.footnotes || [];
  var rows = footnotes.map(function(fn){
    return '<div style="margin:4px 0;font-size:0.78rem;color:#6b7280;padding-left:1.2rem;"><sup style="color:#7c3aed;font-weight:600;">[' + _esc(String(fn.id||'?')) + ']</sup> ' + _markdownToHtml(fn.text||'') + '</div>';
  }).join('');
  return '<div style="margin:1.5rem 0;padding:12px 16px;border-top:1px solid #e5e7eb;"><div style="font-size:0.72rem;font-weight:600;color:#9ca3af;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px;">Footnotes</div>' + rows + '</div>';
};

_RENDERERS['collapsible_panel'] = function(b) {
  var title = b.title || 'Panel';
  var blocks = b.blocks || [];
  var content = '';
  blocks.forEach(function(blk){ var fn = _RENDERERS[blk.component||blk.type]; if(fn) content += fn(blk); });
  if (!content && b.content) content = '<p>' + _markdownToHtml(b.content) + '</p>';
  return '<details style="margin:1rem 0;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;">' +
    '<summary style="padding:10px 14px;background:#f3f4f6;font-weight:600;font-size:0.85rem;color:#374151;cursor:pointer;list-style:none;">▶ ' + _esc(title) + '</summary>' +
    '<div style="padding:12px 14px;font-size:0.85rem;">' + content + '</div></details>';
};

_RENDERERS['accordion_item'] = function(b) {
  var label = b.label || b.title || '';
  var text = b.text || b.content || b.body || '';
  return '<details style="margin:0.5rem 0;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;">' +
    '<summary style="padding:10px 14px;background:#f9fafb;font-weight:600;font-size:0.85rem;color:#374151;cursor:pointer;list-style:none;">▶ ' + _esc(label) + '</summary>' +
    '<div style="padding:12px 14px;font-size:0.85rem;">' + _markdownToHtml(text) + '</div></details>';
};

_RENDERERS['hover_card'] = function(b) {
  var trigger = b.trigger || 'Hover';
  var blocks = b.blocks || [];
  var content = '';
  blocks.forEach(function(blk){ var fn = _RENDERERS[blk.component||blk.type]; if(fn) content += fn(blk); });
  if (!content && b.content) content = '<p style="font-size:0.85rem;">' + _markdownToHtml(b.content) + '</p>';
  return '<div style="margin:1rem 0;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;">' +
    '<div style="padding:10px 14px;background:#f3f4f6;font-size:0.85rem;font-weight:600;color:#374151;border-bottom:1px solid #e5e7eb;">' + _esc(trigger) + '</div>' +
    '<div style="padding:12px 14px;font-size:0.85rem;">' + content + '</div></div>';
};

_RENDERERS['tooltip'] = function(b) {
  var text = b.text || b.content || '';
  var target = b.target || b.trigger || 'hover me';
  return '<div style="margin:1rem 0;display:inline-block;position:relative;">' +
    '<span style="border-bottom:1px dashed #7c3aed;cursor:help;color:#7c3aed;">' + _esc(target) + '</span>' +
    '<div style="margin-top:6px;padding:6px 10px;background:#1f2937;color:#f9fafb;border-radius:6px;font-size:0.78rem;max-width:240px;line-height:1.4;">' + _markdownToHtml(text) + '</div></div>';
};

_RENDERERS['css_modal'] = function(b) {
  var uid = Math.random().toString(36).substr(2,6);
  var trigger = b.trigger_text || b.trigger || 'Open modal';
  var title = b.title || '';
  var description = b.description || '';
  var blocks = b.blocks || [];
  var content = '';
  blocks.forEach(function(blk){ var fn = _RENDERERS[blk.component||blk.type]; if(fn) content += fn(blk); });
  var mid = 'm' + uid;
  var titleHtml = title ? '<div style="font-size:1rem;font-weight:700;color:#f1f5f9;margin-bottom:4px;">' + _esc(title) + '</div>' : '';
  var descHtml = description ? '<p style="font-size:0.88rem;color:#94a3b8;margin:4px 0 16px;">' + _markdownToHtml(description) + '</p>' : '';
  return '<div style="margin:1rem 0;">' +
    '<style>#' + mid + '{display:none;}.' + mid + '-bd{display:none;position:fixed;inset:0;z-index:9000;align-items:center;justify-content:center;background:rgba(0,0,0,0.45);}#' + mid + ':checked~.' + mid + '-bd{display:flex!important;}</style>' +
    '<label for="' + mid + '" style="display:inline-block;padding:9px 22px;border-radius:6px;background:#1a73e8;color:#fff;font-size:0.88rem;font-weight:600;cursor:pointer;">' + _esc(trigger) + '</label>' +
    '<input type="checkbox" id="' + mid + '">' +
    '<div class="' + mid + '-bd"><div style="background:#1e293b;border-radius:12px;padding:28px 28px 20px;max-width:480px;width:90%;box-shadow:0 20px 60px rgba(0,0,0,0.5);">' +
    titleHtml + descHtml + content +
    '<div style="display:flex;gap:10px;justify-content:flex-end;margin-top:20px;">' +
    '<label for="' + mid + '" style="padding:9px 20px;border-radius:6px;border:1px solid rgba(255,255,255,0.15);background:rgba(255,255,255,0.06);color:#e2e8f0;font-size:0.88rem;cursor:pointer;">' + _esc(b.cancel_label||'Cancel') + '</label>' +
    '<label for="' + mid + '" style="padding:9px 22px;border-radius:6px;background:#3b82f6;color:#fff;font-size:0.88rem;font-weight:600;cursor:pointer;">' + _esc(b.confirm_label||'Confirm') + '</label>' +
    '</div></div></div></div>';
};

_RENDERERS['css_dropdown_menu'] = function(b) {
  var trigger = b.trigger_text || b.trigger || b.label || 'Menu';
  var items = b.menu_items || b.items || [];
  var itemsHtml = items.map(function(item){
    return '<a href="' + _esc(item.url||'#') + '" style="display:block;padding:8px 16px;font-size:0.87rem;color:#3c4043;text-decoration:none;white-space:nowrap;">' + _esc(item.label||'') + '</a>';
  }).join('');
  return '<div style="margin:1rem 0;display:inline-block;"><details style="position:relative;">' +
    '<summary style="list-style:none;display:inline-flex;align-items:center;gap:6px;padding:8px 14px;background:#fff;border:1px solid #dadce0;border-radius:6px;cursor:pointer;font-size:0.88rem;font-weight:500;color:#3c4043;">' + _esc(trigger) +
    '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M6 9l6 6 6-6"/></svg></summary>' +
    '<div style="position:absolute;top:calc(100% + 4px);left:0;z-index:20;background:#fff;border:1px solid #dadce0;border-radius:8px;box-shadow:0 4px 16px rgba(0,0,0,0.12);min-width:160px;padding:4px 0;overflow:hidden;">' + itemsHtml + '</div>' +
    '</details></div>';
};

_RENDERERS['version_badge'] = function(b) {
  var v = b.version || '';
  var status = b.status || 'stable';
  var colors = {stable:'#16a34a',beta:'#2563eb',alpha:'#d97706',rc:'#7c3aed'};
  var c = colors[status] || '#6b7280';
  var statusLabel = status !== 'stable' ? '<span style="opacity:0.7;font-weight:400;margin-left:2px;"> · ' + _esc(status) + '</span>' : '';
  return '<span style="display:inline-flex;align-items:center;gap:5px;border:1px solid ' + c + ';border-radius:100px;padding:2px 10px;font-size:0.75rem;font-weight:700;color:' + c + ';font-family:monospace;">v' + _esc(v) + statusLabel + '</span>';
};

_RENDERERS['deprecation_notice'] = function(b) {
  var alt = b.alternative || '';
  var rv = b.removal_version || '';
  var altHtml = alt ? '<div style="margin-top:4px;font-size:0.85rem;">Use instead: <code style="background:#fef2f2;padding:1px 6px;border-radius:4px;">' + _esc(alt) + '</code></div>' : '';
  var rvHtml = rv ? '<div style="margin-top:6px;font-size:0.8rem;color:#991b1b;">Removed in: <code>' + _esc(rv) + '</code></div>' : '';
  return '<div style="border:1px solid #fca5a5;border-left:4px solid #ef4444;border-radius:8px;padding:14px 18px;background:#fef2f2;margin:1.2rem 0;">' +
    '<div style="font-weight:700;color:#991b1b;margin-bottom:4px;">⚠ Deprecated</div>' + altHtml + rvHtml + '</div>';
};

_RENDERERS['experimental_banner'] = function(b) {
  var msg = b.message || b.text || '';
  return '<div style="border:1px solid #fbbf24;border-left:4px solid #f59e0b;border-radius:8px;padding:14px 18px;background:#fffbeb;margin:1.2rem 0;">' +
    '<div style="font-weight:700;color:#92400e;margin-bottom:4px;">🧪 Experimental</div>' +
    (msg ? '<p style="font-size:0.85rem;color:#78350f;margin:0;">' + _markdownToHtml(msg) + '</p>' : '') + '</div>';
};

_RENDERERS['cli_command'] = function(b) {
  var cmd = (b.command || '').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  return '<div style="display:flex;align-items:center;background:#1e1e2e;border-radius:8px;padding:10px 16px;margin:0.8rem 0;font-family:monospace;font-size:0.85rem;">' +
    '<span style="color:#a78bfa;margin-right:10px;user-select:none;">$</span>' +
    '<code style="color:#e2e8f0;flex:1;">' + cmd + '</code></div>';
};

_RENDERERS['terminal_block'] = function(b) {
  var shell = b.shell || 'bash';
  var command = (b.command || '').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  var output = (b.output || '').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  var prompt = {zsh:'%',powershell:'PS>',cmd:'>'}[shell] || '$';
  var outHtml = output ? '<div style="color:#9ca3af;white-space:pre-wrap;margin-top:8px;">' + output + '</div>' : '';
  return '<div style="background:#1e1e2e;border-radius:10px;overflow:hidden;margin:1.2rem 0;font-family:monospace;font-size:0.82rem;">' +
    '<div style="background:#2a2a3e;padding:8px 14px;display:flex;align-items:center;gap:6px;">' +
    '<span style="width:10px;height:10px;border-radius:50%;background:#ff5f56;display:inline-block;"></span>' +
    '<span style="width:10px;height:10px;border-radius:50%;background:#ffbd2e;display:inline-block;"></span>' +
    '<span style="width:10px;height:10px;border-radius:50%;background:#27c93f;display:inline-block;"></span>' +
    '<span style="margin-left:8px;color:#9ca3af;font-size:0.75rem;">' + _esc(shell) + '</span></div>' +
    '<div style="padding:14px 18px;"><span style="color:#a78bfa;">' + prompt + '</span> <span style="color:#e2e8f0;">' + command + '</span>' + outHtml + '</div></div>';
};

_RENDERERS['file_tree'] = function(b) {
  function renderNode(item, depth) {
    var indent = new Array(depth * 2 + 1).join(' ');
    var icon = item.type === 'dir' ? '📁 ' : '📄 ';
    var color = item.type === 'dir' ? '#60a5fa' : '#e2e8f0';
    var html = '<div style="padding:1px 0;color:' + color + ';font-size:0.82rem;">' + indent + icon + _esc(item.name||'') + '</div>';
    (item.children||[]).forEach(function(child){ html += renderNode(child, depth+1); });
    return html;
  }
  var nodes = b.nodes || [];
  var title = b.title || '';
  var titleHtml = title ? '<div style="font-size:0.78rem;color:#9ca3af;margin-bottom:8px;">' + _esc(title) + '</div>' : '';
  var inner = nodes.map(function(n){ return renderNode(n, 0); }).join('');
  return '<div style="background:#1e1e2e;border-radius:10px;padding:16px 20px;margin:1.2rem 0;font-family:monospace;">' + titleHtml + inner + '</div>';
};

_RENDERERS['tabbed_code'] = function(b) {
  var tabs = b.tabs || [];
  if (!tabs.length) return '';
  var uid = Math.random().toString(36).substr(2,6);
  var labels = tabs.map(function(t, i){
    return '<label for="tc_' + uid + '_' + i + '" style="padding:6px 14px;cursor:pointer;font-size:0.78rem;font-weight:600;border-bottom:2px solid ' + (i===0?'#7c3aed':'transparent') + ';color:' + (i===0?'#7c3aed':'#9ca3af') + ';">' + _esc(t.label||t.language||('Tab '+(i+1))) + '</label>';
  }).join('');
  var inputs = tabs.map(function(t,i){ return '<input type="radio" id="tc_' + uid + '_' + i + '" name="tc_' + uid + '"' + (i===0?' checked':'') + ' style="display:none;">'; }).join('');
  var perTab = tabs.map(function(t,i){
    return '<style>#tc_' + uid + '_' + i + ':checked ~ .tcp_' + uid + ' > div:nth-child(' + (i+1) + '){display:block!important;}</style>';
  }).join('');
  var panels = '<div class="tcp_' + uid + '">' + tabs.map(function(t, i){
    return '<div style="' + (i===0?'display:block':'display:none') + '"><pre style="margin:0;padding:16px;background:#1e1e2e;font-size:0.82rem;color:#e2e8f0;overflow:auto;"><code>' + _esc(t.code||'').replace(/&amp;/g,'&').replace(/&lt;/g,'<').replace(/&gt;/g,'>') + '</code></pre></div>';
  }).join('') + '</div>';
  return '<div style="border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;margin:1.2rem 0;">' +
    perTab + inputs + '<div style="display:flex;background:#f9fafb;border-bottom:1px solid #e5e7eb;">' + labels + '</div>' + panels + '</div>';
};

_RENDERERS['http_request_block'] = function(b) {
  var method = (b.method || 'GET').toUpperCase();
  var url = b.url || '';
  var headers = b.headers || {};
  var body = b.body || '';
  var colors = {GET:'#2563eb',POST:'#16a34a',PUT:'#d97706',DELETE:'#dc2626',PATCH:'#7c3aed'};
  var color = colors[method] || '#6b7280';
  var hdrsHtml = Object.keys(headers).map(function(k){ return '<div style="font-size:0.78rem;font-family:monospace;color:#374151;"><span style="color:#6b7280;">' + _esc(k) + ':</span> ' + _esc(headers[k]) + '</div>'; }).join('');
  var bodyHtml = body ? '<pre style="background:#f9fafb;border-radius:6px;padding:10px;margin-top:10px;font-size:0.78rem;overflow:auto;color:#374151;">' + _esc(body) + '</pre>' : '';
  return '<div style="border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;margin:1.2rem 0;">' +
    '<div style="padding:10px 16px;display:flex;align-items:center;gap:10px;background:#f9fafb;">' +
    '<span style="background:' + color + ';color:#fff;font-weight:700;font-size:0.75rem;padding:3px 10px;border-radius:5px;font-family:monospace;">' + method + '</span>' +
    '<span style="font-family:monospace;font-size:0.85rem;color:#374151;">' + _esc(url) + '</span></div>' +
    (hdrsHtml ? '<div style="padding:10px 16px;">' + hdrsHtml + '</div>' : '') +
    bodyHtml + '</div>';
};

_RENDERERS['env_var_list'] = function(b) {
  var variables = b.variables || [];
  var rows = variables.map(function(v){
    var req = v.required ? '<span style="color:#dc2626;font-size:0.72rem;font-weight:700;">required</span>' : '<span style="color:#9ca3af;font-size:0.72rem;">optional</span>';
    return '<tr><td style="padding:8px 12px;font-family:monospace;font-size:0.82rem;color:#7c3aed;white-space:nowrap;border-bottom:1px solid #f3f4f6;">' + _esc(v.key||'') + '</td>' +
      '<td style="padding:8px 12px;font-size:0.82rem;color:#374151;border-bottom:1px solid #f3f4f6;">' + _esc(v.description||'') + '</td>' +
      '<td style="padding:8px 12px;font-family:monospace;font-size:0.78rem;color:#6b7280;border-bottom:1px solid #f3f4f6;">' + _esc(v.default||'—') + '</td>' +
      '<td style="padding:8px 12px;border-bottom:1px solid #f3f4f6;">' + req + '</td></tr>';
  }).join('');
  return '<div style="border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;margin:1.2rem 0;">' +
    '<table style="width:100%;border-collapse:collapse;"><thead><tr style="background:#f9fafb;">' +
    '<th style="padding:8px 12px;text-align:left;font-size:0.75rem;color:#6b7280;text-transform:uppercase;">Variable</th>' +
    '<th style="padding:8px 12px;text-align:left;font-size:0.75rem;color:#6b7280;text-transform:uppercase;">Description</th>' +
    '<th style="padding:8px 12px;text-align:left;font-size:0.75rem;color:#6b7280;text-transform:uppercase;">Default</th>' +
    '<th style="padding:8px 12px;text-align:left;font-size:0.75rem;color:#6b7280;text-transform:uppercase;">Required</th>' +
    '</tr></thead><tbody>' + rows + '</tbody></table></div>';
};

_RENDERERS['keyboard_shortcut'] = function(b) {
  var keys = b.keys || [];
  var action = b.action || '';
  var keyHtml = keys.map(function(k){ return '<kbd style="display:inline-block;padding:2px 8px;font-family:monospace;font-size:0.8rem;border:1px solid #d1d5db;border-bottom:3px solid #9ca3af;border-radius:4px;background:#f9fafb;color:#374151;">' + _esc(k) + '</kbd>'; }).join(' + ');
  var actionHtml = action ? '<span style="margin-left:10px;font-size:0.85rem;color:#6b7280;">' + _esc(action) + '</span>' : '';
  return '<div style="margin:0.5rem 0;display:inline-flex;align-items:center;">' + keyHtml + actionHtml + '</div>';
};

_RENDERERS['api_param_table'] = function(b) {
  var params = b.parameters || [];
  var rows = params.map(function(p){
    var req = p.required ? '<span style="color:#dc2626;font-size:0.72rem;font-weight:700;">required</span>' : '<span style="color:#9ca3af;font-size:0.72rem;">optional</span>';
    return '<tr><td style="padding:8px 12px;font-family:monospace;font-size:0.82rem;color:#7c3aed;border-bottom:1px solid #f3f4f6;">' + _esc(p.name||'') + '</td>' +
      '<td style="padding:8px 12px;font-family:monospace;font-size:0.78rem;color:#2563eb;border-bottom:1px solid #f3f4f6;">' + _esc(p.type||'') + '</td>' +
      '<td style="padding:8px 12px;border-bottom:1px solid #f3f4f6;">' + req + '</td>' +
      '<td style="padding:8px 12px;font-family:monospace;font-size:0.78rem;color:#6b7280;border-bottom:1px solid #f3f4f6;">' + _esc(String(p.default||'—')) + '</td>' +
      '<td style="padding:8px 12px;font-size:0.82rem;color:#374151;border-bottom:1px solid #f3f4f6;">' + _esc(p.description||'') + '</td></tr>';
  }).join('');
  return '<div style="border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;margin:1.2rem 0;overflow-x:auto;">' +
    '<table style="width:100%;border-collapse:collapse;min-width:600px;"><thead><tr style="background:#f9fafb;">' +
    '<th style="padding:8px 12px;text-align:left;font-size:0.75rem;color:#6b7280;text-transform:uppercase;">Parameter</th>' +
    '<th style="padding:8px 12px;text-align:left;font-size:0.75rem;color:#6b7280;text-transform:uppercase;">Type</th>' +
    '<th style="padding:8px 12px;text-align:left;font-size:0.75rem;color:#6b7280;text-transform:uppercase;">Required</th>' +
    '<th style="padding:8px 12px;text-align:left;font-size:0.75rem;color:#6b7280;text-transform:uppercase;">Default</th>' +
    '<th style="padding:8px 12px;text-align:left;font-size:0.75rem;color:#6b7280;text-transform:uppercase;">Description</th>' +
    '</tr></thead><tbody>' + rows + '</tbody></table></div>';
};

_RENDERERS['breadcrumb'] = function(b) {
  var items = b.items || b.crumbs || [];
  var parts = items.map(function(item, i){
    var isLast = i === items.length - 1;
    var text = typeof item === 'string' ? item : (item.label || item.text || '');
    var url = typeof item === 'object' ? (item.url || '#') : '#';
    if (isLast) return '<span style="color:#374151;font-weight:600;">' + _esc(text) + '</span>';
    return '<a href="' + _esc(url) + '" style="color:#7c3aed;text-decoration:none;">' + _esc(text) + '</a>';
  });
  return '<nav style="display:flex;align-items:center;flex-wrap:wrap;gap:6px;font-size:0.82rem;margin:0.5rem 0;">' + parts.join('<span style="color:#9ca3af;">/</span>') + '</nav>';
};

_RENDERERS['pagination'] = function(b) {
  var current = b.current_page || b.current || 1;
  var total = b.total_pages || b.total || 1;
  var prev = current > 1 ? '<button style="padding:6px 12px;border:1px solid #e5e7eb;border-radius:6px;background:#fff;cursor:pointer;font-size:0.82rem;color:#374151;">← Prev</button>' : '';
  var next = current < total ? '<button style="padding:6px 12px;border:1px solid #e5e7eb;border-radius:6px;background:#fff;cursor:pointer;font-size:0.82rem;color:#374151;">Next →</button>' : '';
  var info = '<span style="font-size:0.82rem;color:#6b7280;">Page ' + current + ' of ' + total + '</span>';
  return '<div style="display:flex;align-items:center;gap:8px;margin:1rem 0;flex-wrap:wrap;">' + prev + info + next + '</div>';
};

_RENDERERS['tab_bar'] = function(b) {
  var tabs = b.tabs || [];
  var active = b.active_tab || 0;
  var tabsHtml = tabs.map(function(t, i){
    var isActive = i === active;
    var text = typeof t === 'string' ? t : (t.label || t.text || '');
    return '<div style="padding:8px 16px;font-size:0.85rem;font-weight:' + (isActive?'600':'400') + ';color:' + (isActive?'#1a73e8':'#5f6368') + ';border-bottom:2px solid ' + (isActive?'#1a73e8':'transparent') + ';cursor:pointer;white-space:nowrap;">' + _esc(text) + '</div>';
  }).join('');
  return '<div style="display:flex;border-bottom:1px solid #e5e7eb;overflow-x:auto;margin:1rem 0;">' + tabsHtml + '</div>';
};

_RENDERERS['anchor_list'] = function(b) {
  var items = b.items || b.links || [];
  var rows = items.map(function(item){
    var text = typeof item === 'string' ? item : (item.text || item.label || '');
    var href = typeof item === 'object' ? (item.url || '#' + text.toLowerCase().replace(/\s+/g,'-')) : '#';
    return '<li style="margin:4px 0;"><a href="' + _esc(href) + '" style="color:#7c3aed;text-decoration:none;font-size:0.88rem;">→ ' + _esc(text) + '</a></li>';
  }).join('');
  return '<ul style="list-style:none;padding:12px 16px;margin:1rem 0;border:1px solid #e5e7eb;border-radius:8px;background:#f9fafb;">' + rows + '</ul>';
};

_RENDERERS['glossary_term'] = function(b) {
  var term = b.term || b.name || '';
  var definition = b.definition || b.text || '';
  return '<div style="margin:0.5rem 0;padding:10px 14px;border-left:3px solid #7c3aed;background:#faf5ff;border-radius:0 6px 6px 0;">' +
    '<dt style="font-weight:700;color:#7c3aed;font-size:0.9rem;">' + _esc(term) + '</dt>' +
    '<dd style="margin:4px 0 0 0;font-size:0.85rem;color:#374151;">' + _markdownToHtml(definition) + '</dd></div>';
};

_RENDERERS['blockquote_with_avatar'] = function(b) {
  var text = b.text || b.quote || '';
  var author = b.author_name || b.author || '';
  var title = b.author_title || b.role || '';
  var initial = author ? author[0].toUpperCase() : '?';
  var avatarHtml = b.avatar_url ? '<img src="' + _esc(b.avatar_url) + '" alt="' + _esc(author) + '" style="width:40px;height:40px;border-radius:50%;object-fit:cover;flex-shrink:0;">' :
    '<div style="width:40px;height:40px;border-radius:50%;background:#e8f0fe;display:flex;align-items:center;justify-content:center;font-size:1rem;font-weight:700;color:#1a73e8;flex-shrink:0;">' + _esc(initial) + '</div>';
  return '<blockquote style="border-left:4px solid #e5e7eb;padding:14px 18px;margin:1.5rem 0;background:#f9fafb;border-radius:0 10px 10px 0;">' +
    '<p style="margin:0 0 12px;font-style:italic;color:#374151;">"' + _markdownToHtml(text) + '"</p>' +
    '<div style="display:flex;align-items:center;gap:10px;">' + avatarHtml +
    '<div><div style="font-size:0.87rem;font-weight:700;color:#111827;">' + _esc(author) + '</div>' +
    (title ? '<div style="font-size:0.78rem;color:#6b7280;">' + _esc(title) + '</div>' : '') + '</div></div></blockquote>';
};

_RENDERERS['pull_stat'] = function(b) {
  var value = b.value || b.stat || '';
  var label = b.label || '';
  var context = b.context || '';
  return '<div style="border-left:4px solid #7c3aed;padding:16px 20px;margin:1.5rem 0;background:#faf5ff;">' +
    '<div style="font-size:2.5rem;font-weight:900;color:#7c3aed;line-height:1;">' + _esc(String(value)) + '</div>' +
    (label ? '<div style="font-size:0.88rem;font-weight:600;color:#374151;margin-top:6px;">' + _esc(label) + '</div>' : '') +
    (context ? '<div style="font-size:0.78rem;color:#6b7280;margin-top:4px;">' + _esc(context) + '</div>' : '') + '</div>';
};



// === Batch 3: Social, Article, Interactive, Media Atoms ===

_RENDERERS['article_series_nav'] = function(b) {
  var title = b.title || 'This series';
  var prev = b.prev || '';
  var nxt = b.next || '';
  var url = b.url || '#';
  var nav = '';
  if (prev) nav += '<a href="#" style="color:#7c3aed;text-decoration:none;font-size:0.82rem;">← ' + _esc(prev) + '</a>';
  if (prev && nxt) nav += '<span style="margin:0 8px;color:#d1d5db;">|</span>';
  if (nxt) nav += '<a href="#" style="color:#7c3aed;text-decoration:none;font-size:0.82rem;">' + _esc(nxt) + ' →</a>';
  return '<div style="border:1px solid #ede9fe;border-radius:10px;padding:14px 18px;background:#faf5ff;margin:1.5rem 0;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">' +
    '<div style="font-weight:600;color:#7c3aed;font-size:0.85rem;">📚 <a href="' + _esc(url) + '" style="color:#7c3aed;text-decoration:none;">' + _esc(title) + '</a></div>' +
    '<div>' + nav + '</div></div>';
};

_RENDERERS['post_metadata_bar'] = function(b) {
  var parts = [];
  if (b.author) parts.push('<span style="font-weight:600;color:#374151;">✍️ ' + _esc(b.author) + '</span>');
  if (b.date) parts.push('<span style="color:#6b7280;">📅 ' + _esc(b.date) + '</span>');
  if (b.readTime) parts.push('<span style="color:#6b7280;">⏱️ ' + _esc(String(b.readTime)) + ' min read</span>');
  var inner = parts.join(' <span style="color:#e5e7eb;margin:0 8px;">|</span> ');
  return '<div style="display:flex;align-items:center;gap:8px;font-size:0.82rem;padding:8px 12px;background:#f9fafb;border:1px solid #f3f4f6;border-radius:6px;margin:1rem 0;flex-wrap:wrap;">' + inner + '</div>';
};

_RENDERERS['author_bio_card'] = function(b) {
  var name = b.name || '';
  var bio = b.bio || '';
  var avatar = b.image || b.avatar_url || b.avatar || '';
  var links = b.links || {};
  var avatarHtml = avatar ? '<img src="' + _esc(avatar) + '" alt="' + _esc(name) + '" style="width:56px;height:56px;border-radius:50%;object-fit:cover;flex-shrink:0;">' :
    '<div style="width:56px;height:56px;border-radius:50%;background:#e5e7eb;display:flex;align-items:center;justify-content:center;font-size:1.4rem;flex-shrink:0;">👤</div>';
  var linksHtml = Object.keys(links).map(function(k){ return '<a href="' + _esc(links[k]) + '" target="_blank" rel="noopener" style="font-size:0.78rem;color:#6b7280;text-decoration:none;margin-right:10px;">' + _esc(k) + '</a>'; }).join('');
  return '<div style="border:1px solid #e5e7eb;border-radius:12px;padding:18px 22px;display:flex;gap:16px;align-items:flex-start;margin:1.5rem 0;">' +
    avatarHtml + '<div>' +
    '<div style="font-weight:700;color:#111827;margin-bottom:4px;">' + _esc(name) + '</div>' +
    '<p style="margin:0 0 8px;font-size:0.85rem;color:#6b7280;line-height:1.5;">' + _markdownToHtml(bio) + '</p>' +
    (linksHtml ? '<div>' + linksHtml + '</div>' : '') + '</div></div>';
};

_RENDERERS['related_posts_grid'] = function(b) {
  var posts = b.posts || [];
  var cards = posts.map(function(p){
    var topicHtml = p.topic ? '<div style="font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#7c3aed;margin-bottom:4px;">' + _esc(p.topic) + '</div>' : '';
    return '<a href="' + _esc(p.url||'#') + '" style="display:block;border:1px solid #e5e7eb;border-radius:8px;padding:14px 16px;text-decoration:none;">' +
      topicHtml + '<div style="font-size:0.88rem;font-weight:600;color:#111827;line-height:1.4;">' + _esc(p.title||'') + '</div></a>';
  }).join('');
  return '<div style="margin:1.5rem 0;"><div style="font-size:0.78rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#6b7280;margin-bottom:10px;">Related reading</div>' +
    '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px;">' + cards + '</div></div>';
};

_RENDERERS['series_overview_card'] = function(b) {
  var name = b.series_name || b.name || '';
  var parts = b.parts || [];
  var items = parts.map(function(p, i){
    var bg = p.current ? '#7c3aed' : '#f3f4f6';
    var color = p.current ? '#fff' : '#6b7280';
    var textStyle = p.current ? 'font-weight:700;color:#7c3aed;' : 'color:#374151;';
    return '<a href="' + _esc(p.url||'#') + '" style="display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid #f3f4f6;text-decoration:none;">' +
      '<span style="width:22px;height:22px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:0.7rem;font-weight:700;flex-shrink:0;background:' + bg + ';color:' + color + ';">' + (i+1) + '</span>' +
      '<span style="font-size:0.85rem;' + textStyle + '">' + _esc(p.title||'') + '</span></a>';
  }).join('');
  return '<div style="border:1px solid #ede9fe;border-radius:10px;padding:16px 20px;background:#faf5ff;margin:1.2rem 0;">' +
    '<div style="font-weight:700;color:#7c3aed;margin-bottom:10px;">📖 ' + _esc(name) + '</div>' + items + '</div>';
};

_RENDERERS['reaction_group'] = function(b) {
  var emojisMap = {thumbs_up:'👍',heart:'❤️',rocket:'🚀',mind_blown:'🤯'};
  var enabled = b.enabled_emojis || Object.keys(emojisMap);
  var btns = enabled.filter(function(e){ return emojisMap[e]; }).map(function(e){
    return '<button onclick="var s=this.querySelector(\'span\');s.textContent=String(parseInt(s.textContent)+1);" style="display:inline-flex;align-items:center;gap:4px;padding:6px 12px;border:1px solid #e5e7eb;border-radius:100px;background:#f9fafb;cursor:pointer;font-size:0.88rem;">' +
      emojisMap[e] + ' <span style="font-size:0.78rem;color:#6b7280;">0</span></button>';
  }).join('');
  return '<div style="display:flex;flex-wrap:wrap;gap:8px;margin:1rem 0;">' + btns + '</div>';
};

_RENDERERS['share_quote'] = function(b) {
  var text = b.text || '';
  var author = b.author || '';
  var tweetText = (text.substring(0,200) + (author ? ' — ' + author : '')).replace(/ /g,'+');
  return '<div style="border-left:4px solid #7c3aed;padding:16px 20px;background:#faf5ff;border-radius:0 10px 10px 0;margin:1.5rem 0;">' +
    '<p style="font-size:1rem;font-style:italic;color:#1e1b4b;line-height:1.6;margin:0 0 10px;">"' + _esc(text) + '"</p>' +
    (author ? '<div style="font-size:0.8rem;color:#7c3aed;font-weight:600;">— ' + _esc(author) + '</div>' : '') +
    '<a href="https://twitter.com/intent/tweet?text=' + tweetText + '" target="_blank" rel="noopener" style="display:inline-flex;align-items:center;gap:5px;font-size:0.75rem;color:#6b7280;text-decoration:none;margin-top:8px;">Share this →</a></div>';
};

_RENDERERS['follow_cta'] = function(b) {
  var msg = b.message || 'Follow for more';
  var links = b.platform_links || {};
  var btns = Object.keys(links).map(function(k){ return '<a href="' + _esc(links[k]) + '" target="_blank" rel="noopener" style="padding:8px 18px;border:1px solid #d1d5db;border-radius:6px;font-size:0.85rem;font-weight:600;color:#374151;text-decoration:none;">' + _esc(k) + '</a>'; }).join('');
  return '<div style="border:1px solid #e5e7eb;border-radius:12px;padding:20px 24px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;margin:1.5rem 0;background:#f9fafb;">' +
    '<span style="font-size:0.95rem;font-weight:600;color:#111827;">' + _esc(msg) + '</span>' +
    '<div style="display:flex;gap:8px;flex-wrap:wrap;">' + btns + '</div></div>';
};

_RENDERERS['follow_button'] = function(b) {
  var handle = b.target_handle || '';
  var platform = b.platform || 'twitter';
  var urls = {twitter:'https://twitter.com/'+handle, github:'https://github.com/'+handle, linkedin:'https://linkedin.com/in/'+handle};
  var url = urls[platform] || '#';
  return '<a href="' + _esc(url) + '" target="_blank" rel="noopener" style="display:inline-flex;align-items:center;gap:6px;padding:8px 18px;border:1px solid #d1d5db;border-radius:6px;font-size:0.85rem;font-weight:600;color:#374151;text-decoration:none;background:#f9fafb;">Follow @' + _esc(handle) + '</a>';
};

_RENDERERS['notification_badge'] = function(b) {
  var text = b.text || '';
  var color = b.color || '#ef4444';
  return '<div style="position:relative;display:inline-block;padding:8px;background:#f3f4f6;border-radius:8px;">' +
    '<svg style="width:24px;height:24px;color:#4b5563;" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"></path></svg>' +
    '<span style="position:absolute;top:0;right:0;transform:translate(25%,-25%);background:' + color + ';color:#fff;font-size:0.7rem;font-weight:700;border-radius:9999px;padding:2px 6px;line-height:1;min-width:16px;text-align:center;box-shadow:0 0 0 2px #fff;">' + _esc(String(text)) + '</span></div>';
};

_RENDERERS['expandable_list'] = function(b) {
  function renderNode(node) {
    var text = node.text || '';
    var children = node.children || [];
    if (children.length) {
      var childHtml = children.map(function(c){ return '<div style="margin-left:16px;">' + renderNode(c) + '</div>'; }).join('');
      return '<details style="margin:4px 0;font-size:0.9rem;"><summary style="cursor:pointer;font-weight:500;color:#1f2937;list-style:none;"><span style="margin-right:4px;">▶</span>' + _esc(text) + '</summary><div style="padding-left:12px;border-left:1px dashed #d1d5db;margin-top:2px;">' + childHtml + '</div></details>';
    }
    return '<div style="margin:4px 0;color:#4b5563;font-size:0.9rem;padding-left:14px;">• ' + _esc(text) + '</div>';
  }
  var items = b.items || [];
  var inner = items.map(renderNode).join('');
  return '<div style="padding:12px;border:1px solid #e5e7eb;border-radius:8px;background:#fff;margin:1rem 0;">' + inner + '</div>';
};

_RENDERERS['poll_block'] = function(b) {
  var question = b.question || 'Question';
  var options = b.options || [];
  var totalVotes = options.reduce(function(sum, o){ return sum + (o.votes||0); }, 0) || 1;
  var optsHtml = options.map(function(opt){
    var pct = ((opt.votes||0) / totalVotes * 100).toFixed(1);
    return '<div style="margin-bottom:12px;">' +
      '<div style="display:flex;justify-content:space-between;font-size:0.85rem;font-weight:500;color:#374151;margin-bottom:4px;">' +
      '<span>' + _esc(opt.text||'') + '</span><span>' + (opt.votes||0) + ' votes (' + pct + '%)</span></div>' +
      '<div style="height:24px;background:#f3f4f6;border-radius:6px;overflow:hidden;border:1px solid #e5e7eb;">' +
      '<div style="width:' + pct + '%;height:100%;background:#7c3aed;opacity:0.15;border-radius:5px;"></div></div></div>';
  }).join('');
  return '<div style="padding:16px;border:1px solid #ede9fe;border-radius:12px;background:#fff;margin:1.2rem 0;">' +
    '<h4 style="margin:0 0 16px;font-size:1rem;font-weight:700;color:#111827;">📊 ' + _esc(question) + '</h4>' + optsHtml + '</div>';
};

_RENDERERS['abbr_tooltip'] = function(b) {
  var text = b.text || '';
  var title = b.title || b.definition || '';
  return '<abbr title="' + _esc(title) + '" style="text-decoration:underline dotted #7c3aed;text-underline-offset:4px;cursor:help;font-weight:600;color:#4338ca;">' + _esc(text) + '</abbr>';
};

_RENDERERS['copy_to_clipboard'] = function(b) {
  var text = b.text || '';
  var val = (b.value || text).replace(/'/g,"\\'");
  return '<span style="display:inline-flex;align-items:center;gap:6px;background:#f3f4f6;border:1px solid #e5e7eb;padding:4px 10px;border-radius:6px;font-family:monospace;font-size:0.85rem;color:#1f2937;">' +
    '<span>' + _esc(text) + '</span>' +
    '<button onclick="navigator.clipboard.writeText(\'' + val + '\');this.textContent=\'✓\';setTimeout(function(){this.textContent=\'📋\';}.bind(this),1000)" style="border:none;background:none;cursor:pointer;font-size:0.85rem;padding:0;">📋</button></span>';
};

_RENDERERS['copy_code_button'] = function(b) {
  var text = (b.text_to_copy || '').replace(/'/g,"\\'").replace(/</g,'&lt;').replace(/>/g,'&gt;');
  return '<div style="display:inline-block;margin:0.5rem 0;"><button onclick="navigator.clipboard.writeText(\'' + text + '\')" style="display:inline-flex;align-items:center;gap:6px;padding:6px 14px;border:1px solid #d1d5db;border-radius:6px;background:#f9fafb;cursor:pointer;font-size:0.82rem;color:#374151;">' +
    '<svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><path d="M0 6.75C0 5.784.784 5 1.75 5h1.5a.75.75 0 0 1 0 1.5h-1.5a.25.25 0 0 0-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 0 0 .25-.25v-1.5a.75.75 0 0 1 1.5 0v1.5A1.75 1.75 0 0 1 9.25 16h-7.5A1.75 1.75 0 0 1 0 14.25Z"/><path d="M5 1.75C5 .784 5.784 0 6.75 0h7.5C15.216 0 16 .784 16 1.75v7.5A1.75 1.75 0 0 1 14.25 11h-7.5A1.75 1.75 0 0 1 5 9.25Zm1.75-.25a.25.25 0 0 0-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 0 0 .25-.25v-7.5a.25.25 0 0 0-.25-.25Z"/></svg>Copy</button></div>';
};

_RENDERERS['log_output'] = function(b) {
  var logs = (b.logs||'').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  return '<div style="background:#0d1117;border-radius:8px;padding:14px 18px;margin:1.2rem 0;max-height:300px;overflow-y:auto;">' +
    '<pre style="margin:0;font-family:monospace;font-size:0.78rem;color:#9ca3af;white-space:pre-wrap;word-break:break-all;">' + logs + '</pre></div>';
};

_RENDERERS['json_tree_viewer'] = function(b) {
  var raw = b.data || b.json || '';
  var pretty = raw;
  try { pretty = JSON.stringify(JSON.parse(raw), null, 2); } catch(e) {}
  var escaped = pretty.replace(/</g,'&lt;').replace(/>/g,'&gt;');
  return '<div style="background:#1e1e2e;border-radius:10px;padding:16px;margin:1.2rem 0;max-height:400px;overflow:auto;">' +
    '<pre style="margin:0;font-family:monospace;font-size:0.8rem;color:#e2e8f0;">' + escaped + '</pre></div>';
};

_RENDERERS['star_rating_input'] = function(b) {
  var uid = Math.random().toString(36).substr(2,6);
  var name = b.name || 'rating';
  var maxS = parseInt(b.max_stars || 5);
  var initial = parseInt(b.initial_rating || 0);
  var label = b.label || '';
  var inputs = '';
  var labels = '';
  for (var i = maxS; i >= 1; i--) {
    inputs += '<input type="radio" id="sr' + uid + '_' + i + '" name="sr' + uid + '" value="' + i + '"' + (i===initial?' checked':'') + ' style="display:none;">';
    labels += '<label for="sr' + uid + '_' + i + '" title="' + i + ' star' + (i>1?'s':'') + '" style="font-size:1.7rem;cursor:pointer;color:#d1d5db;transition:color .1s;">★</label>';
  }
  return '<style>.sr' + uid + ' input:checked~label,.sr' + uid + ' label:hover,.sr' + uid + ' label:hover~label{color:#facc15;}</style>' +
    '<div style="margin:1rem 0;">' +
    (label ? '<div style="font-size:0.83rem;font-weight:600;color:#3c4043;margin-bottom:6px;">' + _esc(label) + '</div>' : '') +
    '<div class="sr' + uid + '" style="display:flex;flex-direction:row-reverse;justify-content:flex-end;gap:2px;">' + inputs + labels + '</div></div>';
};

_RENDERERS['segmented_control'] = function(b) {
  var uid = Math.random().toString(36).substr(2,6);
  var options = b.options || [];
  var selected = b.selected_value || b.selected || '';
  var name = b.name || 'seg';
  var label = b.label || '';
  var norm = options.map(function(o){ return typeof o === 'string' ? {value:o,label:o} : o; });
  if (!selected && norm.length) selected = norm[0].value;
  var items = norm.map(function(o){
    return '<input type="radio" id="sgc' + uid + '_' + o.value + '" name="' + name + '_' + uid + '" value="' + _esc(o.value) + '"' + (o.value===selected?' checked':'') + ' style="display:none;">' +
      '<label for="sgc' + uid + '_' + o.value + '" style="padding:7px 16px;font-size:0.85rem;font-weight:500;cursor:pointer;color:#5f6368;border-right:1px solid #dadce0;white-space:nowrap;">' + _esc(o.label) + '</label>';
  }).join('');
  return '<style>.sgc' + uid + ' input:checked+label{background:#e8f0fe;color:#1a73e8;font-weight:600;}</style>' +
    '<div style="margin:1rem 0;">' +
    (label ? '<div style="font-size:0.83rem;font-weight:600;color:#3c4043;margin-bottom:6px;">' + _esc(label) + '</div>' : '') +
    '<div class="sgc' + uid + '" style="display:inline-flex;border:1px solid #dadce0;border-radius:8px;overflow:hidden;background:#fff;">' + items + '</div></div>';
};

_RENDERERS['zoomable_image'] = function(b) {
  var uid = Math.random().toString(36).substr(2,6);
  var url = b.image_url || b.url || '';
  var alt = b.alt_text || b.alt || '';
  var factor = b.zoom_factor || 1.5;
  return '<style>.zi' + uid + '{overflow:hidden;border-radius:10px;cursor:zoom-in;border:1px solid #e5e7eb;}.zi' + uid + ' img{width:100%;display:block;transition:transform .4s ease;}.zi' + uid + ':hover img{transform:scale(' + factor + ');}</style>' +
    '<div style="margin:1rem 0;"><div class="zi' + uid + '"><img src="' + _esc(url) + '" alt="' + _esc(alt) + '"></div>' +
    '<div style="font-size:0.75rem;color:#9ca3af;text-align:center;margin-top:4px;">Hover to zoom</div></div>';
};

_RENDERERS['custom_checkbox_group'] = function(b) {
  var uid = Math.random().toString(36).substr(2,6);
  var label = b.group_label || b.label || '';
  var name = b.name || 'chk';
  var options = b.options || b.items || [];
  var checkSvg = '<svg width="11" height="9" viewBox="0 0 11 9" fill="none"><polyline points="1,4.5 4,8 10,1" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  var items = options.map(function(opt, i){
    var val = opt.value || opt.label || '';
    var lbl = opt.label || val;
    var checked = opt.is_checked || opt.checked ? ' checked' : '';
    var cid = 'ccg' + uid + '_' + i;
    return '<div><input type="checkbox" id="' + cid + '" name="' + _esc(name) + '" value="' + _esc(val) + '"' + checked + ' style="display:none;">' +
      '<label for="' + cid + '" style="display:flex;align-items:center;gap:10px;cursor:pointer;padding:10px 14px;border:1px solid #e5e7eb;border-radius:8px;background:#fff;font-size:0.88rem;color:#374151;">' +
      '<span class="box' + uid + '" style="width:18px;height:18px;border:2px solid #dadce0;border-radius:4px;flex-shrink:0;display:flex;align-items:center;justify-content:center;">' + checkSvg + '</span>' + _esc(lbl) + '</label></div>';
  }).join('');
  return '<style>.ccg' + uid + ' input:checked+label{border-color:#1a73e8;background:#f0f4ff;color:#1a73e8;}.ccg' + uid + ' input:checked+label .box' + uid + '{border-color:#1a73e8;background:#1a73e8;}</style>' +
    '<div class="ccg' + uid + '" style="margin:1rem 0;">' +
    (label ? '<div style="font-size:0.83rem;font-weight:600;color:#3c4043;margin-bottom:8px;">' + _esc(label) + '</div>' : '') +
    '<div style="display:flex;flex-direction:column;gap:6px;">' + items + '</div></div>';
};

_RENDERERS['css_slide_panel'] = function(b) {
  var trigger = b.trigger_text || 'Open panel';
  var blocks = b.blocks || [];
  var content = '';
  blocks.forEach(function(blk){ var fn = _RENDERERS[blk.component||blk.type]; if(fn) content += fn(blk); });
  if (!content && b.content) content = '<p>' + _markdownToHtml(b.content) + '</p>';
  return '<div style="margin:1rem 0;display:flex;gap:12px;align-items:flex-start;">' +
    '<button style="padding:8px 14px;background:#374151;color:#fff;border:none;border-radius:6px;font-size:0.82rem;cursor:pointer;white-space:nowrap;">' + _esc(trigger) + ' →</button>' +
    '<div style="flex:1;padding:12px;border:1px solid #e5e7eb;border-radius:8px;background:#fff;border-left:3px solid #374151;font-size:0.85rem;">' + content + '</div></div>';
};

_RENDERERS['testimonial_card'] = function(b) {
  var text = b.text || b.quote || '';
  var authorName = b.author_name || b.author || '';
  var authorTitle = b.author_title || b.company || b.role || '';
  var avatarUrl = b.author_avatar_url || b.avatar || '';
  var rating = parseInt(b.rating || 0);
  var starsHtml = rating ? '<div style="margin-bottom:12px;">' + '★'.repeat(rating).split('').map(function(){ return '<span style="color:#facc15;font-size:1rem;">★</span>'; }).join('') + '★'.repeat(5-rating).split('').map(function(){ return '<span style="color:#d1d5db;font-size:1rem;">★</span>'; }).join('') + '</div>' : '';
  var avatarHtml = avatarUrl ? '<img src="' + _esc(avatarUrl) + '" alt="' + _esc(authorName) + '" style="width:40px;height:40px;border-radius:50%;object-fit:cover;flex-shrink:0;">' :
    (authorName ? '<div style="width:40px;height:40px;border-radius:50%;background:#e8f0fe;display:flex;align-items:center;justify-content:center;font-size:1rem;font-weight:700;color:#1a73e8;flex-shrink:0;">' + _esc(authorName[0]) + '</div>' : '');
  return '<div style="margin:1rem 0;background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:20px 22px;">' +
    starsHtml +
    '<blockquote style="margin:0 0 16px;font-size:0.93rem;color:#374151;line-height:1.65;font-style:italic;">&ldquo;' + _esc(text) + '&rdquo;</blockquote>' +
    '<div style="display:flex;align-items:center;gap:10px;">' + avatarHtml +
    '<div><div style="font-size:0.87rem;font-weight:700;color:#111827;">' + _esc(authorName) + '</div>' +
    (authorTitle ? '<div style="font-size:0.78rem;color:#6b7280;">' + _esc(authorTitle) + '</div>' : '') + '</div></div></div>';
};

_RENDERERS['star_rating_display'] = function(b) {
  var rating = parseFloat(b.rating || b.value || 0);
  var maxRating = parseInt(b.max_rating || 5);
  var reviewCount = b.review_count || b.count || null;
  var full = Math.floor(rating);
  var half = (rating - full) >= 0.5 ? 1 : 0;
  var empty = maxRating - full - half;
  var stars = '★'.repeat(full).split('').map(function(){ return '<span style="color:#facc15;font-size:1.2rem;">★</span>'; }).join('');
  if (half) stars += '<span style="color:#facc15;font-size:1.2rem;opacity:0.55;">★</span>';
  stars += '★'.repeat(empty).split('').map(function(){ return '<span style="color:#d1d5db;font-size:1.2rem;">★</span>'; }).join('');
  var countHtml = reviewCount !== null ? '<span style="font-size:0.82rem;color:#6b7280;margin-left:6px;">(' + reviewCount.toLocaleString() + ' reviews)</span>' : '';
  return '<div style="margin:0.5rem 0;display:flex;align-items:center;gap:4px;">' + stars + '<span style="font-size:0.93rem;font-weight:600;color:#374151;margin-left:4px;">' + rating + '</span>' + countHtml + '</div>';
};

_RENDERERS['code_diff'] = function(b) {
  var oldCode = b.old_code || b.old_text || '';
  var newCode = b.new_code || b.new_text || '';
  var label = b.label || '';
  var language = b.language || '';
  var showLn = b.show_line_numbers !== false;
  var oldLines = oldCode.split('\n');
  var newLines = newCode.split('\n');
  var rows = [];
  var oldLn = 0; var newLn = 0;
  var i = 0; var j = 0;
  while (i < oldLines.length || j < newLines.length) {
    var ol = oldLines[i]; var nl = newLines[j];
    if (i < oldLines.length && j < newLines.length && ol === nl) {
      oldLn++; newLn++;
      var escaped = ol.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
      var ln = showLn ? '<span style="min-width:28px;display:inline-block;color:#374151;user-select:none;padding-right:10px;">' + newLn + '</span>' : '';
      rows.push('<div style="padding:1px 14px;display:flex;">' + ln + '<span style="color:#94a3b8;white-space:pre;flex:1;">' + escaped + '</span></div>');
      i++; j++;
    } else if (j >= newLines.length || (i < oldLines.length && (j >= newLines.length || ol < nl))) {
      oldLn++;
      var escaped2 = ol.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
      var ln2 = showLn ? '<span style="min-width:28px;display:inline-block;color:#7f1d1d;user-select:none;padding-right:10px;">' + oldLn + '</span>' : '';
      rows.push('<div style="padding:1px 14px;display:flex;background:#7f1d1d2a;border-left:3px solid #ef4444;">' + ln2 + '<span style="color:#fca5a5;white-space:pre;flex:1;">- ' + escaped2 + '</span></div>');
      i++;
    } else {
      newLn++;
      var escaped3 = nl.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
      var ln3 = showLn ? '<span style="min-width:28px;display:inline-block;color:#064e3b;user-select:none;padding-right:10px;">' + newLn + '</span>' : '';
      rows.push('<div style="padding:1px 14px;display:flex;background:#0640261f;border-left:3px solid #34d399;">' + ln3 + '<span style="color:#6ee7b7;white-space:pre;flex:1;">+ ' + escaped3 + '</span></div>');
      j++;
    }
  }
  var header = (label || language) ? '<div style="display:flex;align-items:center;justify-content:space-between;padding:10px 14px;border-bottom:1px solid #1e293b;">' +
    (label ? '<span style="font-size:13px;font-weight:600;color:#94a3b8;">' + _esc(label) + '</span>' : '') +
    (language ? '<span style="font-size:11px;color:#64748b;background:#1e293b;padding:2px 8px;border-radius:4px;">' + _esc(language) + '</span>' : '') + '</div>' : '';
  return '<div style="background:#0a0f1d;border:1px solid #1e293b;border-radius:12px;margin:1rem 0;overflow:hidden;font-family:monospace;font-size:0.82rem;">' + header + '<div style="padding:6px 0;">' + rows.join('') + '</div></div>';
};

_RENDERERS['flip_card'] = function(b) {
  var front = '';
  var back = '';
  (b.front_blocks||[]).forEach(function(blk){ var fn = _RENDERERS[blk.component||blk.type]; if(fn) front += fn(blk); });
  (b.back_blocks||[]).forEach(function(blk){ var fn = _RENDERERS[blk.component||blk.type]; if(fn) back += fn(blk); });
  return '<div style="margin:1rem 0;display:grid;grid-template-columns:1fr 1fr;gap:8px;">' +
    '<div style="padding:12px;border:2px solid #7c3aed;border-radius:8px;background:#faf5ff;">' +
    '<div style="font-size:0.7rem;font-weight:600;color:#7c3aed;margin-bottom:6px;text-transform:uppercase;">Front</div>' + front + '</div>' +
    '<div style="padding:12px;border:1px solid #e5e7eb;border-radius:8px;background:#f9fafb;">' +
    '<div style="font-size:0.7rem;font-weight:600;color:#6b7280;margin-bottom:6px;text-transform:uppercase;">Back (flipped)</div>' + back + '</div></div>';
};

_RENDERERS['image_with_caption'] = function(b) {
  var url = b.url || b.image_url || '';
  var alt = b.alt || b.alt_text || '';
  var caption = b.caption || b.text || '';
  return '<figure style="margin:1.2rem 0;text-align:center;">' +
    '<img src="' + _esc(url) + '" alt="' + _esc(alt) + '" style="max-width:100%;border-radius:8px;display:block;margin:0 auto;">' +
    (caption ? '<figcaption style="font-size:0.82rem;color:#6b7280;margin-top:8px;font-style:italic;">' + _esc(caption) + '</figcaption>' : '') + '</figure>';
};

_RENDERERS['framed_screenshot'] = function(b) {
  var url = b.url || b.image_url || '';
  var alt = b.alt || b.caption || '';
  var frame = b.frame || 'browser';
  var header = '<div style="padding:8px 14px;background:#f3f4f6;border-bottom:1px solid #e5e7eb;display:flex;align-items:center;gap:6px;">' +
    '<span style="width:10px;height:10px;border-radius:50%;background:#ff5f56;display:inline-block;"></span>' +
    '<span style="width:10px;height:10px;border-radius:50%;background:#ffbd2e;display:inline-block;"></span>' +
    '<span style="width:10px;height:10px;border-radius:50%;background:#27c93f;display:inline-block;"></span>' +
    (alt ? '<span style="flex:1;background:#fff;border-radius:4px;padding:2px 8px;font-size:0.72rem;color:#6b7280;">' + _esc(alt) + '</span>' : '') + '</div>';
  return '<div style="margin:1.2rem 0;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;">' + header + '<img src="' + _esc(url) + '" alt="' + _esc(alt) + '" style="width:100%;display:block;"></div>';
};

_RENDERERS['video_thumbnail'] = function(b) {
  var url = b.url || b.thumbnail_url || '';
  var title = b.title || '';
  var link = b.video_url || b.link || '#';
  return '<a href="' + _esc(link) + '" target="_blank" rel="noopener" style="display:block;position:relative;margin:1rem 0;border-radius:8px;overflow:hidden;">' +
    (url ? '<img src="' + _esc(url) + '" alt="' + _esc(title) + '" style="width:100%;display:block;">' : '<div style="width:100%;height:180px;background:#1e293b;display:flex;align-items:center;justify-content:center;"></div>') +
    '<div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;">' +
    '<div style="width:60px;height:60px;border-radius:50%;background:rgba(0,0,0,0.7);display:flex;align-items:center;justify-content:center;"><span style="color:#fff;font-size:1.5rem;margin-left:4px;">▶</span></div></div>' +
    (title ? '<div style="position:absolute;bottom:0;left:0;right:0;padding:8px 12px;background:linear-gradient(transparent,rgba(0,0,0,0.8));color:#fff;font-size:0.85rem;font-weight:600;">' + _esc(title) + '</div>' : '') + '</a>';
};

_RENDERERS['video_card'] = function(b) {
  var url = b.url || b.thumbnail_url || '';
  var title = b.title || '';
  var description = b.description || '';
  var link = b.video_url || b.link || '#';
  return '<div style="border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;margin:1rem 0;">' +
    '<a href="' + _esc(link) + '" target="_blank" rel="noopener" style="display:block;position:relative;">' +
    (url ? '<img src="' + _esc(url) + '" alt="' + _esc(title) + '" style="width:100%;height:180px;object-fit:cover;display:block;">' : '<div style="width:100%;height:180px;background:#1e293b;"></div>') +
    '<div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;"><div style="width:48px;height:48px;border-radius:50%;background:rgba(0,0,0,0.7);display:flex;align-items:center;justify-content:center;"><span style="color:#fff;font-size:1.2rem;margin-left:4px;">▶</span></div></div></a>' +
    '<div style="padding:12px 14px;">' +
    (title ? '<div style="font-size:0.9rem;font-weight:700;color:#111827;margin-bottom:4px;">' + _esc(title) + '</div>' : '') +
    (description ? '<div style="font-size:0.82rem;color:#6b7280;">' + _esc(description) + '</div>' : '') + '</div></div>';
};

_RENDERERS['audio_player'] = function(b) {
  var url = b.url || b.src_url || '';
  var title = b.title || b.label || '';
  return '<div style="border:1px solid #e5e7eb;border-radius:8px;padding:12px 16px;margin:1rem 0;background:#f9fafb;">' +
    (title ? '<div style="font-size:0.85rem;font-weight:600;color:#374151;margin-bottom:8px;">🎵 ' + _esc(title) + '</div>' : '') +
    (url ? '<audio controls style="width:100%;"><source src="' + _esc(url) + '"></audio>' : '<div style="color:#9ca3af;font-size:0.85rem;">No audio source</div>') + '</div>';
};

_RENDERERS['audio_link'] = function(b) {
  var url = b.url || '';
  var label = b.label || b.title || 'Audio file';
  return '<a href="' + _esc(url) + '" target="_blank" rel="noopener" style="display:inline-flex;align-items:center;gap:6px;padding:6px 14px;border:1px solid #e5e7eb;border-radius:6px;font-size:0.85rem;color:#374151;text-decoration:none;background:#f9fafb;">🎵 ' + _esc(label) + '</a>';
};

_RENDERERS['pdf_preview'] = function(b) {
  var url = b.url || '';
  var title = b.title || 'PDF Document';
  return '<a href="' + _esc(url) + '" target="_blank" rel="noopener" style="display:flex;align-items:center;gap:12px;padding:14px 16px;border:1px solid #e5e7eb;border-radius:8px;text-decoration:none;margin:1rem 0;">' +
    '<div style="width:40px;height:48px;background:#ef4444;border-radius:4px;display:flex;align-items:center;justify-content:center;color:#fff;font-size:0.7rem;font-weight:700;flex-shrink:0;">PDF</div>' +
    '<div><div style="font-size:0.9rem;font-weight:600;color:#111827;">' + _esc(title) + '</div><div style="font-size:0.75rem;color:#6b7280;margin-top:2px;">Click to open PDF</div></div></a>';
};

_RENDERERS['document_link'] = function(b) {
  var url = b.url || '';
  var title = b.title || b.label || 'Document';
  var type = (b.type || 'doc').toUpperCase();
  return '<a href="' + _esc(url) + '" target="_blank" rel="noopener" style="display:inline-flex;align-items:center;gap:6px;padding:7px 14px;border:1px solid #e5e7eb;border-radius:6px;font-size:0.85rem;color:#374151;text-decoration:none;background:#f9fafb;">📄 ' + _esc(title) + ' <span style="font-size:0.7rem;color:#9ca3af;">[' + _esc(type) + ']</span></a>';
};

_RENDERERS['code_snippet_pair'] = function(b) {
  var snippets = b.snippets || b.items || [];
  if (!snippets.length && (b.before || b.code1)) snippets = [{label:b.label1||'Snippet 1',code:b.code1||b.before,language:b.language||''},{label:b.label2||'Snippet 2',code:b.code2||b.after,language:b.language||''}];
  var cols = snippets.map(function(s){
    return '<div style="flex:1;min-width:0;"><div style="font-size:0.72rem;font-weight:700;color:#6b7280;margin-bottom:4px;text-transform:uppercase;letter-spacing:0.06em;">' + _esc(s.label||'') + '</div>' +
      '<pre style="margin:0;padding:12px;background:#1e1e2e;border-radius:8px;overflow-x:auto;font-size:0.8rem;color:#e2e8f0;"><code>' + _esc(s.code||'').replace(/&amp;/g,'&').replace(/&lt;/g,'<').replace(/&gt;/g,'>') + '</code></pre></div>';
  }).join('');
  return '<div style="display:flex;gap:12px;margin:1.2rem 0;flex-wrap:wrap;">' + cols + '</div>';
};

_RENDERERS['toast_notification'] = function(b) {
  var message = b.message || b.text || '';
  var type = b.type || 'info';
  var icons = {info:'ℹ️',success:'✅',warning:'⚠️',error:'❌'};
  var colors = {info:'#2563eb',success:'#16a34a',warning:'#d97706',error:'#dc2626'};
  return '<div style="display:flex;align-items:center;gap:10px;padding:10px 16px;border-radius:8px;border:1px solid ' + (colors[type]||'#6b7280') + '44;background:#fff;box-shadow:0 4px 12px rgba(0,0,0,0.08);margin:1rem 0;">' +
    '<span>' + (icons[type]||'📢') + '</span>' +
    '<span style="font-size:0.85rem;color:#374151;">' + _esc(message) + '</span></div>';
};

_RENDERERS['loading_skeleton'] = function(b) {
  var lines = b.lines || 3;
  var html = '';
  for (var i = 0; i < lines; i++) {
    var width = i === 0 ? '100%' : (i === lines-1 ? '60%' : '85%');
    html += '<div style="height:14px;background:#e5e7eb;border-radius:4px;margin-bottom:8px;width:' + width + ';animation:pulse 1.5s ease-in-out infinite alternate;"></div>';
  }
  return '<style>@keyframes pulse{from{opacity:1}to{opacity:0.4}}</style>' +
    '<div style="margin:1rem 0;padding:16px;border:1px solid #e5e7eb;border-radius:8px;">' + html + '</div>';
};

_RENDERERS['empty_state'] = function(b) {
  var icon = b.icon || '📭';
  var title = b.title || b.heading || 'Nothing here yet';
  var message = b.message || b.text || '';
  var action = b.action_label || '';
  return '<div style="text-align:center;padding:40px 20px;margin:1rem 0;">' +
    '<div style="font-size:3rem;margin-bottom:12px;">' + icon + '</div>' +
    '<div style="font-weight:700;color:#111827;margin-bottom:6px;">' + _esc(title) + '</div>' +
    (message ? '<p style="font-size:0.88rem;color:#6b7280;">' + _esc(message) + '</p>' : '') +
    (action ? '<button style="margin-top:12px;padding:8px 20px;background:#7c3aed;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:0.85rem;font-weight:600;">' + _esc(action) + '</button>' : '') + '</div>';
};

_RENDERERS['spinner'] = function(b) {
  var uid = Math.random().toString(36).substr(2,6);
  var color = b.color || '#7c3aed';
  var size = b.size || '32px';
  return '<style>@keyframes sp' + uid + '{to{transform:rotate(360deg)}}</style>' +
    '<div style="display:inline-flex;align-items:center;gap:10px;margin:0.5rem 0;">' +
    '<div style="width:' + size + ';height:' + size + ';border:3px solid #e5e7eb;border-top-color:' + _esc(color) + ';border-radius:50%;animation:sp' + uid + ' 0.8s linear infinite;"></div>' +
    (b.label ? '<span style="font-size:0.85rem;color:#6b7280;">' + _esc(b.label) + '</span>' : '') + '</div>';
};

_RENDERERS['status_pill'] = function(b) {
  var label = b.label || b.status || b.text || '';
  var status = b.status || 'active';
  var colors = {active:['#059669','#d1fae5'],inactive:['#6b7280','#f3f4f6'],error:['#dc2626','#fee2e2'],pending:['#ca8a04','#fef9c3'],'in-progress':['#2563eb','#dbeafe']};
  var c = colors[status] || ['#6b7280','#f3f4f6'];
  var dot = b.dot !== false ? '<span style="width:7px;height:7px;border-radius:50%;background:' + c[0] + ';display:inline-block;margin-right:5px;"></span>' : '';
  return '<span style="display:inline-flex;align-items:center;background:' + c[1] + ';color:' + c[0] + ';font-size:0.75rem;font-weight:600;padding:3px 10px;border-radius:100px;">' + dot + _esc(label) + '</span>';
};

_RENDERERS['inline_feedback_message'] = function(b) {
  var type = b.type || 'info';
  var message = b.message || b.text || '';
  var colors = {info:'#2563eb',success:'#16a34a',warning:'#d97706',error:'#dc2626'};
  var color = colors[type] || '#6b7280';
  return '<div style="display:flex;align-items:flex-start;gap:6px;margin:0.5rem 0;font-size:0.82rem;color:' + color + ';">' +
    '<span>' + (type==='error'?'✕':type==='success'?'✓':type==='warning'?'⚠':'ℹ') + '</span>' +
    '<span>' + _esc(message) + '</span></div>';
};

_RENDERERS['rating_stars'] = function(b) {
  var rating = parseFloat(b.rating || b.value || 0);
  var maxRating = parseInt(b.max_rating || 5);
  var label = b.label || '';
  var full = Math.min(Math.floor(rating), maxRating);
  var stars = Array(full).fill('<span style="color:#facc15;">★</span>').join('') +
    Array(maxRating-full).fill('<span style="color:#d1d5db;">★</span>').join('');
  return '<div style="margin:0.5rem 0;">' +
    (label ? '<div style="font-size:0.83rem;font-weight:600;color:#3c4043;margin-bottom:4px;">' + _esc(label) + '</div>' : '') +
    '<div>' + stars + '<span style="font-size:0.85rem;color:#374151;margin-left:6px;">' + rating + '</span></div></div>';
};

_RENDERERS['progress_circle'] = function(b) {
  var uid = Math.random().toString(36).substr(2,6);
  var value = Math.min(100, Math.max(0, parseInt(b.value||0)));
  var label = b.label || '';
  var color = b.color || '#38bdf8';
  var r = 36;
  var circ = parseFloat((2 * Math.PI * r).toFixed(2));
  var offset = parseFloat((circ * (1 - value/100)).toFixed(2));
  return '<style>.pc' + uid + '{stroke-dasharray:' + circ + ';stroke-dashoffset:' + circ + ';animation:pca' + uid + ' 1.2s ease-out forwards;}@keyframes pca' + uid + '{to{stroke-dashoffset:' + offset + ';}}</style>' +
    '<div style="display:inline-flex;flex-direction:column;align-items:center;margin:1rem 0;">' +
    '<div style="position:relative;width:120px;height:120px;">' +
    '<svg width="120" height="120" viewBox="0 0 100 100" style="transform:rotate(-90deg);display:block;">' +
    '<circle cx="50" cy="50" r="' + r + '" fill="none" stroke="#1e293b" stroke-width="9"/>' +
    '<circle class="pc' + uid + '" cx="50" cy="50" r="' + r + '" fill="none" stroke="' + color + '" stroke-width="9" stroke-linecap="round"/>' +
    '</svg>' +
    '<div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:20px;font-weight:700;color:#f1f5f9;font-family:monospace;">' + value + '%</div></div>' +
    (label ? '<div style="font-size:0.8rem;color:#94a3b8;margin-top:6px;text-align:center;">' + _esc(label) + '</div>' : '') + '</div>';
};

// Stub atoms for comparison/ecommerce category
['action_required_card','feature_matrix','pricing_tier_card','pricing_tier_group','pros_cons_list','side_by_side_spec','product_spec_table','comparison_grid','versus_block','rating_comparison','capability_checklist','toggle_switch','expandable_text','image_hotspots','avatar_group','contributor_list','customer_logo_grid','social_proof_banner','media_mention_card','expert_endorsement','review_callout'].forEach(function(name) {
  _RENDERERS[name] = function(b) {
    var label = b.label || b.title || b.name || '';
    var text = b.text || b.content || b.value || '';
    var inner = (label ? '<strong>' + _esc(label) + '</strong><br>' : '') + (text ? _markdownToHtml(text) : '<em style="color:#999;">[ ' + name + ' ]</em>');
    return '<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">' + inner + '</div>';
  };
});



// === Batch 4: Form Atoms + Modal + Feature Comparison ===

_RENDERERS['form'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6);
  var action = b.action || '';
  var method = b.method || 'post';
  var submitLabel = b.submit_label || 'Submit';
  var blocks = b.blocks || [];

  var innerHtml = '';
  for (var i = 0; i < blocks.length; i++) {
    var blk = blocks[i];
    var type = blk.component || blk.type;
    if (type && _RENDERERS[type]) {
      innerHtml += _RENDERERS[type](blk);
    }
  }

  var actionAttr = action ? ' action="' + _esc(action) + '"' : '';

  return '<style>' +
    '.form-wrap-' + uid + '{background:#fff;border-radius:12px;padding:24px;box-shadow:0 1px 4px rgba(0,0,0,0.08);margin:1rem 0;}' +
    '.form-wrap-' + uid + ' .form-submit-btn{display:inline-block;background:#7c3aed;color:#fff;border:none;border-radius:8px;padding:10px 28px;font-size:15px;font-weight:600;cursor:pointer;margin-top:16px;transition:background 0.15s;}' +
    '.form-wrap-' + uid + ' .form-submit-btn:hover{background:#6d28d9;}' +
    '</style>' +
    '<div class="form-wrap-' + uid + '">' +
    '<form' + actionAttr + ' method="' + _esc(method) + '">' +
    innerHtml +
    '<div style="margin-top:8px;"><button type="submit" class="form-submit-btn">' + _esc(submitLabel) + '</button></div>' +
    '</form>' +
    '</div>';
};

_RENDERERS['form_input'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6);
  var label = b.label || '';
  var name = b.name || ('input_' + uid);
  var placeholder = b.placeholder || '';
  var value = b.value || '';
  var type = b.type || 'text';
  var required = b.required ? ' required' : '';
  var hint = b.hint || '';
  var error = b.error || '';

  var validTypes = ['text', 'email', 'number', 'url', 'password'];
  if (validTypes.indexOf(type) === -1) type = 'text';

  return '<style>' +
    '.fi-wrap-' + uid + '{margin-bottom:16px;}' +
    '.fi-wrap-' + uid + ' .fi-label{display:block;font-size:14px;font-weight:600;color:#374151;margin-bottom:4px;}' +
    '.fi-wrap-' + uid + ' .fi-input{display:block;width:100%;box-sizing:border-box;border:1.5px solid #d1d5db;border-radius:8px;padding:9px 12px;font-size:15px;color:#111827;background:#fff;outline:none;transition:border-color 0.15s;}' +
    '.fi-wrap-' + uid + ' .fi-input:focus{border-color:#7c3aed;box-shadow:0 0 0 3px rgba(124,58,237,0.12);}' +
    '.fi-wrap-' + uid + ' .fi-hint{font-size:13px;color:#6b7280;margin-top:4px;}' +
    '.fi-wrap-' + uid + ' .fi-error{font-size:13px;color:#dc2626;margin-top:4px;}' +
    '</style>' +
    '<div class="fi-wrap-' + uid + '">' +
    (label ? '<label class="fi-label" for="fi-' + uid + '">' + _esc(label) + (b.required ? ' <span style="color:#dc2626">*</span>' : '') + '</label>' : '') +
    '<input class="fi-input" id="fi-' + uid + '" type="' + _esc(type) + '" name="' + _esc(name) + '"' +
    ' placeholder="' + _esc(placeholder) + '" value="' + _esc(value) + '"' + required + '>' +
    (hint ? '<div class="fi-hint">' + _esc(hint) + '</div>' : '') +
    (error ? '<div class="fi-error">' + _esc(error) + '</div>' : '') +
    '</div>';
};

_RENDERERS['form_select'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6);
  var label = b.label || '';
  var name = b.name || ('select_' + uid);
  var options = b.options || [];
  var selectedValue = b.selected_value || '';
  var placeholder = b.placeholder || '';

  var optionsHtml = '';
  if (placeholder) {
    optionsHtml += '<option value="" disabled' + (selectedValue === '' ? ' selected' : '') + '>' + _esc(placeholder) + '</option>';
  }
  for (var i = 0; i < options.length; i++) {
    var opt = options[i];
    var val, lbl;
    if (typeof opt === 'string') {
      val = opt; lbl = opt;
    } else {
      val = opt.value || '';
      lbl = opt.label || val;
    }
    var sel = (val === selectedValue) ? ' selected' : '';
    optionsHtml += '<option value="' + _esc(val) + '"' + sel + '>' + _esc(lbl) + '</option>';
  }

  return '<style>' +
    '.fs-wrap-' + uid + '{margin-bottom:16px;position:relative;}' +
    '.fs-wrap-' + uid + ' .fs-label{display:block;font-size:14px;font-weight:600;color:#374151;margin-bottom:4px;}' +
    '.fs-wrap-' + uid + ' .fs-select-wrap{position:relative;}' +
    '.fs-wrap-' + uid + ' .fs-select{display:block;width:100%;box-sizing:border-box;border:1.5px solid #d1d5db;border-radius:8px;padding:9px 36px 9px 12px;font-size:15px;color:#111827;background:#fff;appearance:none;-webkit-appearance:none;outline:none;cursor:pointer;transition:border-color 0.15s;}' +
    '.fs-wrap-' + uid + ' .fs-select:focus{border-color:#7c3aed;box-shadow:0 0 0 3px rgba(124,58,237,0.12);}' +
    '.fs-wrap-' + uid + ' .fs-arrow{pointer-events:none;position:absolute;right:12px;top:50%;transform:translateY(-50%);color:#6b7280;font-size:12px;}' +
    '</style>' +
    '<div class="fs-wrap-' + uid + '">' +
    (label ? '<label class="fs-label" for="fs-' + uid + '">' + _esc(label) + '</label>' : '') +
    '<div class="fs-select-wrap">' +
    '<select class="fs-select" id="fs-' + uid + '" name="' + _esc(name) + '">' +
    optionsHtml +
    '</select>' +
    '<span class="fs-arrow">&#9660;</span>' +
    '</div>' +
    '</div>';
};

_RENDERERS['form_radio_group'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6);
  var label = b.label || '';
  var name = b.name || ('radio_' + uid);
  var options = b.options || [];
  var selectedValue = b.selected_value || '';

  var optionsHtml = '';
  for (var i = 0; i < options.length; i++) {
    var opt = options[i];
    var val, lbl;
    if (typeof opt === 'string') {
      val = opt; lbl = opt;
    } else {
      val = opt.value || '';
      lbl = opt.label || val;
    }
    var rid = 'r-' + uid + '-' + i;
    var chk = (val === selectedValue) ? ' checked' : '';
    optionsHtml +=
      '<div class="frg-item-' + uid + '">' +
      '<input type="radio" id="' + rid + '" name="' + _esc(name) + '" value="' + _esc(val) + '"' + chk + ' class="frg-input-' + uid + '">' +
      '<label for="' + rid + '" class="frg-label-' + uid + '">' +
      '<span class="frg-dot-' + uid + '"></span>' +
      _esc(lbl) +
      '</label>' +
      '</div>';
  }

  return '<style>' +
    '.frg-wrap-' + uid + '{margin-bottom:16px;}' +
    '.frg-group-label-' + uid + '{display:block;font-size:14px;font-weight:600;color:#374151;margin-bottom:8px;}' +
    '.frg-item-' + uid + '{margin-bottom:8px;}' +
    '.frg-input-' + uid + '{position:absolute;opacity:0;width:0;height:0;}' +
    '.frg-label-' + uid + '{display:flex;align-items:center;gap:10px;cursor:pointer;font-size:15px;color:#111827;user-select:none;}' +
    '.frg-dot-' + uid + '{width:18px;height:18px;border-radius:50%;border:2px solid #d1d5db;display:inline-flex;align-items:center;justify-content:center;flex-shrink:0;background:#fff;transition:border-color 0.15s,background 0.15s;}' +
    '.frg-input-' + uid + ':checked + .frg-label-' + uid + ' .frg-dot-' + uid + '{border-color:#7c3aed;background:#7c3aed;box-shadow:inset 0 0 0 4px #fff;}' +
    '.frg-label-' + uid + ':hover .frg-dot-' + uid + '{border-color:#7c3aed;}' +
    '</style>' +
    '<div class="frg-wrap-' + uid + '">' +
    (label ? '<span class="frg-group-label-' + uid + '">' + _esc(label) + '</span>' : '') +
    optionsHtml +
    '</div>';
};

_RENDERERS['form_checkbox_group'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6);
  var label = b.label || '';
  var name = b.name || ('cb_' + uid);
  var options = b.options || [];

  var optionsHtml = '';
  for (var i = 0; i < options.length; i++) {
    var opt = options[i];
    var val, lbl, checked;
    if (typeof opt === 'string') {
      val = opt; lbl = opt; checked = false;
    } else {
      val = opt.value || '';
      lbl = opt.label || val;
      checked = !!opt.checked;
    }
    var cid = 'cb-' + uid + '-' + i;
    var chk = checked ? ' checked' : '';
    optionsHtml +=
      '<div class="fcb-item-' + uid + '">' +
      '<input type="checkbox" id="' + cid + '" name="' + _esc(name) + '" value="' + _esc(val) + '"' + chk + ' class="fcb-input-' + uid + '">' +
      '<label for="' + cid + '" class="fcb-label-' + uid + '">' +
      '<span class="fcb-box-' + uid + '"><span class="fcb-check-' + uid + '">&#10003;</span></span>' +
      _esc(lbl) +
      '</label>' +
      '</div>';
  }

  return '<style>' +
    '.fcb-wrap-' + uid + '{margin-bottom:16px;}' +
    '.fcb-group-label-' + uid + '{display:block;font-size:14px;font-weight:600;color:#374151;margin-bottom:8px;}' +
    '.fcb-item-' + uid + '{margin-bottom:8px;}' +
    '.fcb-input-' + uid + '{position:absolute;opacity:0;width:0;height:0;}' +
    '.fcb-label-' + uid + '{display:flex;align-items:center;gap:10px;cursor:pointer;font-size:15px;color:#111827;user-select:none;}' +
    '.fcb-box-' + uid + '{width:18px;height:18px;border-radius:4px;border:2px solid #d1d5db;display:inline-flex;align-items:center;justify-content:center;flex-shrink:0;background:#fff;transition:border-color 0.15s,background 0.15s;}' +
    '.fcb-check-' + uid + '{color:#fff;font-size:12px;line-height:1;display:none;}' +
    '.fcb-input-' + uid + ':checked + .fcb-label-' + uid + ' .fcb-box-' + uid + '{border-color:#7c3aed;background:#7c3aed;}' +
    '.fcb-input-' + uid + ':checked + .fcb-label-' + uid + ' .fcb-check-' + uid + '{display:block;}' +
    '.fcb-label-' + uid + ':hover .fcb-box-' + uid + '{border-color:#7c3aed;}' +
    '</style>' +
    '<div class="fcb-wrap-' + uid + '">' +
    (label ? '<span class="fcb-group-label-' + uid + '">' + _esc(label) + '</span>' : '') +
    optionsHtml +
    '</div>';
};

_RENDERERS['form_switch_group'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6);
  var label = b.label || '';
  var name = b.name || ('sw_' + uid);
  var options = b.options || [];

  var optionsHtml = '';
  for (var i = 0; i < options.length; i++) {
    var opt = options[i];
    var val = opt.value || '';
    var lbl = opt.label || val;
    var enabled = !!opt.enabled;
    var sid = 'sw-' + uid + '-' + i;
    var chk = enabled ? ' checked' : '';
    optionsHtml +=
      '<div class="fsw-item-' + uid + '">' +
      '<input type="checkbox" id="' + sid + '" name="' + _esc(name) + '" value="' + _esc(val) + '"' + chk + ' class="fsw-input-' + uid + '">' +
      '<label for="' + sid + '" class="fsw-row-' + uid + '">' +
      '<span class="fsw-track-' + uid + '"><span class="fsw-thumb-' + uid + '"></span></span>' +
      '<span class="fsw-text-' + uid + '">' + _esc(lbl) + '</span>' +
      '</label>' +
      '</div>';
  }

  return '<style>' +
    '.fsw-wrap-' + uid + '{margin-bottom:16px;}' +
    '.fsw-group-label-' + uid + '{display:block;font-size:14px;font-weight:600;color:#374151;margin-bottom:8px;}' +
    '.fsw-item-' + uid + '{margin-bottom:10px;}' +
    '.fsw-input-' + uid + '{position:absolute;opacity:0;width:0;height:0;}' +
    '.fsw-row-' + uid + '{display:flex;align-items:center;gap:10px;cursor:pointer;user-select:none;}' +
    '.fsw-track-' + uid + '{position:relative;width:44px;height:24px;border-radius:12px;background:#d1d5db;display:inline-block;flex-shrink:0;transition:background 0.2s;}' +
    '.fsw-thumb-' + uid + '{position:absolute;top:3px;left:3px;width:18px;height:18px;border-radius:50%;background:#fff;box-shadow:0 1px 3px rgba(0,0,0,0.2);transition:left 0.2s;}' +
    '.fsw-input-' + uid + ':checked + .fsw-row-' + uid + ' .fsw-track-' + uid + '{background:#7c3aed;}' +
    '.fsw-input-' + uid + ':checked + .fsw-row-' + uid + ' .fsw-thumb-' + uid + '{left:23px;}' +
    '.fsw-text-' + uid + '{font-size:15px;color:#111827;}' +
    '</style>' +
    '<div class="fsw-wrap-' + uid + '">' +
    (label ? '<span class="fsw-group-label-' + uid + '">' + _esc(label) + '</span>' : '') +
    optionsHtml +
    '</div>';
};

_RENDERERS['form_slider'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6);
  var label = b.label || '';
  var name = b.name || ('slider_' + uid);
  var min = (b.min !== undefined) ? b.min : 0;
  var max = (b.max !== undefined) ? b.max : 100;
  var step = (b.step !== undefined) ? b.step : 1;
  var value = (b.value !== undefined) ? b.value : Math.round((min + max) / 2);
  var unit = b.unit || '';

  return '<style>' +
    '.fsl-wrap-' + uid + '{margin-bottom:16px;}' +
    '.fsl-header-' + uid + '{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;}' +
    '.fsl-label-' + uid + '{font-size:14px;font-weight:600;color:#374151;}' +
    '.fsl-value-' + uid + '{font-size:14px;font-weight:700;color:#7c3aed;}' +
    '.fsl-range-' + uid + '{width:100%;-webkit-appearance:none;appearance:none;height:6px;border-radius:3px;background:#e5e7eb;outline:none;cursor:pointer;}' +
    '.fsl-range-' + uid + '::-webkit-slider-thumb{-webkit-appearance:none;appearance:none;width:20px;height:20px;border-radius:50%;background:#7c3aed;cursor:pointer;box-shadow:0 1px 3px rgba(0,0,0,0.2);}' +
    '.fsl-range-' + uid + '::-moz-range-thumb{width:20px;height:20px;border-radius:50%;background:#7c3aed;cursor:pointer;border:none;box-shadow:0 1px 3px rgba(0,0,0,0.2);}' +
    '.fsl-minmax-' + uid + '{display:flex;justify-content:space-between;font-size:12px;color:#9ca3af;margin-top:4px;}' +
    '</style>' +
    '<div class="fsl-wrap-' + uid + '">' +
    '<div class="fsl-header-' + uid + '">' +
    (label ? '<span class="fsl-label-' + uid + '">' + _esc(label) + '</span>' : '<span></span>') +
    '<span class="fsl-value-' + uid + '" id="fsl-val-' + uid + '">' + _esc(String(value)) + _esc(unit) + '</span>' +
    '</div>' +
    '<input type="range" class="fsl-range-' + uid + '" name="' + _esc(name) + '" min="' + _esc(String(min)) + '" max="' + _esc(String(max)) + '" step="' + _esc(String(step)) + '" value="' + _esc(String(value)) + '" oninput="document.getElementById(\'fsl-val-' + uid + '\').textContent=this.value+\'' + _esc(unit) + '\'">' +
    '<div class="fsl-minmax-' + uid + '"><span>' + _esc(String(min)) + _esc(unit) + '</span><span>' + _esc(String(max)) + _esc(unit) + '</span></div>' +
    '</div>';
};

_RENDERERS['form_date_picker'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6);
  var label = b.label || '';
  var name = b.name || ('date_' + uid);
  var value = b.value || '';
  var minDate = b.min_date || '';
  var maxDate = b.max_date || '';

  var minAttr = minDate ? ' min="' + _esc(minDate) + '"' : '';
  var maxAttr = maxDate ? ' max="' + _esc(maxDate) + '"' : '';
  var valAttr = value ? ' value="' + _esc(value) + '"' : '';

  return '<style>' +
    '.fdp-wrap-' + uid + '{margin-bottom:16px;}' +
    '.fdp-label-' + uid + '{display:block;font-size:14px;font-weight:600;color:#374151;margin-bottom:4px;}' +
    '.fdp-input-' + uid + '{display:block;width:100%;box-sizing:border-box;border:1.5px solid #d1d5db;border-radius:8px;padding:9px 12px;font-size:15px;color:#111827;background:#fff;outline:none;cursor:pointer;transition:border-color 0.15s;}' +
    '.fdp-input-' + uid + ':focus{border-color:#7c3aed;box-shadow:0 0 0 3px rgba(124,58,237,0.12);}' +
    '</style>' +
    '<div class="fdp-wrap-' + uid + '">' +
    (label ? '<label class="fdp-label-' + uid + '" for="fdp-' + uid + '">' + _esc(label) + '</label>' : '') +
    '<input type="date" class="fdp-input-' + uid + '" id="fdp-' + uid + '" name="' + _esc(name) + '"' + valAttr + minAttr + maxAttr + '>' +
    '</div>';
};

_RENDERERS['modal'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6);
  var triggerLabel = b.trigger_label || 'Open';
  var title = b.title || '';
  var closeLabel = b.close_label || 'Close';
  var blocks = b.blocks || [];

  var innerHtml = '';
  for (var i = 0; i < blocks.length; i++) {
    var blk = blocks[i];
    var type = blk.component || blk.type;
    if (type && _RENDERERS[type]) {
      innerHtml += _RENDERERS[type](blk);
    }
  }

  return '<style>' +
    '#modal-' + uid + '{display:none;}' +
    '.modal-trigger-btn-' + uid + '{display:inline-block;background:#7c3aed;color:#fff;border:none;border-radius:8px;padding:10px 22px;font-size:15px;font-weight:600;cursor:pointer;text-decoration:none;}' +
    '.modal-trigger-btn-' + uid + ':hover{background:#6d28d9;}' +
    '#modal-backdrop-' + uid + '{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:9999;align-items:center;justify-content:center;}' +
    '#modal-' + uid + ':checked ~ #modal-backdrop-' + uid + '{display:flex!important;}' +
    '.modal-card-' + uid + '{background:#fff;border-radius:12px;max-width:560px;width:90%;padding:24px;max-height:80vh;overflow-y:auto;position:relative;box-shadow:0 8px 32px rgba(0,0,0,0.2);}' +
    '.modal-header-' + uid + '{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:16px;}' +
    '.modal-title-' + uid + '{font-size:18px;font-weight:700;color:#111827;margin:0;}' +
    '.modal-close-btn-' + uid + '{display:inline-block;background:none;border:none;font-size:24px;color:#6b7280;cursor:pointer;line-height:1;padding:0 4px;text-decoration:none;font-weight:300;}' +
    '.modal-close-btn-' + uid + ':hover{color:#111827;}' +
    '.modal-footer-' + uid + '{margin-top:20px;text-align:right;}' +
    '.modal-close-label-btn-' + uid + '{display:inline-block;background:#f3f4f6;color:#374151;border:none;border-radius:8px;padding:8px 20px;font-size:14px;font-weight:600;cursor:pointer;text-decoration:none;}' +
    '.modal-close-label-btn-' + uid + ':hover{background:#e5e7eb;}' +
    '</style>' +
    '<input type="checkbox" id="modal-' + uid + '">' +
    '<label for="modal-' + uid + '" class="modal-trigger-btn-' + uid + '">' + _esc(triggerLabel) + '</label>' +
    '<div id="modal-backdrop-' + uid + '">' +
    '<div class="modal-card-' + uid + '">' +
    '<div class="modal-header-' + uid + '">' +
    (title ? '<h2 class="modal-title-' + uid + '">' + _esc(title) + '</h2>' : '<span></span>') +
    '<label for="modal-' + uid + '" class="modal-close-btn-' + uid + '">&#215;</label>' +
    '</div>' +
    '<div class="modal-body-' + uid + '">' + innerHtml + '</div>' +
    '<div class="modal-footer-' + uid + '">' +
    '<label for="modal-' + uid + '" class="modal-close-label-btn-' + uid + '">' + _esc(closeLabel) + '</label>' +
    '</div>' +
    '</div>' +
    '</div>';
};

_RENDERERS['follow_up_chips'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6);
  var chips = b.chips || [];

  var chipsHtml = '';
  for (var i = 0; i < chips.length; i++) {
    var chip = chips[i];
    var text, action;
    if (typeof chip === 'string') {
      text = chip; action = null;
    } else {
      text = chip.text || '';
      action = chip.action || null;
    }
    var onclick = '';
    if (action) {
      onclick = ' onclick="google.script.run.withFailureHandler(function(){}).withSuccessHandler(function(){}).handleChipAction(' + JSON.stringify(action) + ')"';
    }
    chipsHtml += '<button class="fuc-chip-' + uid + '"' + onclick + (action ? ' style="cursor:pointer;"' : '') + '>' + _esc(text) + '</button>';
  }

  return '<style>' +
    '.fuc-wrap-' + uid + '{display:flex;flex-wrap:wrap;gap:8px;margin:1rem 0;}' +
    '.fuc-chip-' + uid + '{display:inline-block;background:#fff;border:1.5px solid #d1d5db;border-radius:9999px;padding:7px 16px;font-size:14px;color:#374151;cursor:default;font-family:inherit;transition:border-color 0.15s,background 0.15s,color 0.15s;}' +
    '.fuc-chip-' + uid + ':hover{border-color:#7c3aed;background:#faf5ff;color:#7c3aed;}' +
    '</style>' +
    '<div class="fuc-wrap-' + uid + '">' + chipsHtml + '</div>';
};

_RENDERERS['choicebox_group'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6);
  var question = b.question || '';
  var name = b.name || ('choice_' + uid);
  var options = b.options || [];

  var optionsHtml = '';
  for (var i = 0; i < options.length; i++) {
    var opt = options[i];
    var val = opt.value || String(i);
    var lbl = opt.label || '';
    var desc = opt.description || '';
    var icon = opt.icon || '';
    var cid = 'cbox-' + uid + '-' + i;

    optionsHtml +=
      '<div class="cbg-item-wrap-' + uid + '">' +
      '<input type="radio" id="' + cid + '" name="' + _esc(name) + '" value="' + _esc(val) + '" class="cbg-input-' + uid + '">' +
      '<label for="' + cid + '" class="cbg-card-' + uid + '">' +
      (icon ? '<span class="cbg-icon-' + uid + '">' + _esc(icon) + '</span>' : '') +
      '<span class="cbg-text-' + uid + '">' +
      '<span class="cbg-label-' + uid + '">' + _esc(lbl) + '</span>' +
      (desc ? '<span class="cbg-desc-' + uid + '">' + _esc(desc) + '</span>' : '') +
      '</span>' +
      '</label>' +
      '</div>';
  }

  return '<style>' +
    '.cbg-wrap-' + uid + '{margin:1rem 0;}' +
    '.cbg-question-' + uid + '{font-size:16px;font-weight:700;color:#111827;margin-bottom:12px;}' +
    '.cbg-grid-' + uid + '{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px;}' +
    '.cbg-input-' + uid + '{position:absolute;opacity:0;width:0;height:0;}' +
    '.cbg-card-' + uid + '{display:flex;align-items:flex-start;gap:12px;padding:16px;border:2px solid #e5e7eb;border-radius:10px;background:#fff;cursor:pointer;transition:border-color 0.15s,background 0.15s;}' +
    '.cbg-card-' + uid + ':hover{border-color:#c4b5fd;background:#faf5ff;}' +
    '.cbg-input-' + uid + ':checked + .cbg-card-' + uid + '{border-color:#7c3aed;background:#faf5ff;}' +
    '.cbg-icon-' + uid + '{font-size:22px;flex-shrink:0;line-height:1.3;}' +
    '.cbg-text-' + uid + '{display:flex;flex-direction:column;gap:3px;}' +
    '.cbg-label-' + uid + '{font-size:15px;font-weight:600;color:#111827;}' +
    '.cbg-desc-' + uid + '{font-size:13px;color:#6b7280;}' +
    '</style>' +
    '<div class="cbg-wrap-' + uid + '">' +
    (question ? '<div class="cbg-question-' + uid + '">' + _esc(question) + '</div>' : '') +
    '<div class="cbg-grid-' + uid + '">' + optionsHtml + '</div>' +
    '</div>';
};

_RENDERERS['feedback_prompt'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6);
  var promptText = b.prompt_text || 'Was this helpful?';
  var mode = b.mode || 'thumbs';
  var name = b.name || ('feedback_' + uid);

  if (mode === 'stars') {
    // Row-reverse trick: render star inputs in reverse order (5 down to 1)
    // so CSS sibling selectors work for "fill all stars up to selected"
    var starsHtml = '';
    for (var s = 5; s >= 1; s--) {
      var sid = 'star-' + uid + '-' + s;
      starsHtml +=
        '<input type="radio" id="' + sid + '" name="' + _esc(name) + '" value="' + s + '" class="fp-star-input-' + uid + '">' +
        '<label for="' + sid + '" class="fp-star-label-' + uid + '" title="' + s + ' star' + (s > 1 ? 's' : '') + '">&#9733;</label>';
    }

    return '<style>' +
      '.fp-wrap-' + uid + '{margin:1rem 0;padding:16px;background:#fff;border-radius:10px;border:1px solid #e5e7eb;display:inline-block;}' +
      '.fp-prompt-' + uid + '{font-size:15px;font-weight:600;color:#374151;margin-bottom:10px;}' +
      '.fp-stars-' + uid + '{display:flex;flex-direction:row-reverse;gap:4px;justify-content:flex-end;}' +
      '.fp-star-input-' + uid + '{position:absolute;opacity:0;width:0;height:0;}' +
      '.fp-star-label-' + uid + '{font-size:28px;color:#d1d5db;cursor:pointer;transition:color 0.1s;}' +
      '.fp-star-label-' + uid + ':hover,.fp-star-label-' + uid + ':hover ~ .fp-star-label-' + uid + '{color:#f59e0b;}' +
      '.fp-star-input-' + uid + ':checked ~ .fp-star-label-' + uid + '{color:#f59e0b;}' +
      '.fp-thankyou-' + uid + '{display:none;font-size:14px;color:#7c3aed;font-weight:600;margin-top:8px;}' +
      '.fp-star-input-' + uid + ':checked ~ .fp-thankyou-' + uid + '{display:block;}' +
      '</style>' +
      '<div class="fp-wrap-' + uid + '">' +
      '<div class="fp-prompt-' + uid + '">' + _esc(promptText) + '</div>' +
      '<div class="fp-stars-' + uid + '">' +
      starsHtml +
      '<span class="fp-thankyou-' + uid + '">Thanks for your rating!</span>' +
      '</div>' +
      '</div>';
  }

  // Thumbs mode
  var upId = 'fp-up-' + uid;
  var downId = 'fp-down-' + uid;

  return '<style>' +
    '.fp-wrap-' + uid + '{margin:1rem 0;padding:16px;background:#fff;border-radius:10px;border:1px solid #e5e7eb;display:inline-block;}' +
    '.fp-prompt-' + uid + '{font-size:15px;font-weight:600;color:#374151;margin-bottom:10px;}' +
    '.fp-thumbs-' + uid + '{display:flex;gap:12px;align-items:center;}' +
    '.fp-thumb-input-' + uid + '{position:absolute;opacity:0;width:0;height:0;}' +
    '.fp-thumb-label-' + uid + '{font-size:26px;cursor:pointer;padding:6px 10px;border-radius:8px;border:2px solid transparent;transition:background 0.15s,border-color 0.15s;}' +
    '.fp-thumb-label-' + uid + ':hover{background:#f3f4f6;}' +
    '#' + upId + ':checked ~ .fp-thumbs-' + uid + ' .fp-thumb-up-' + uid + '{background:#dcfce7;border-color:#16a34a;}' +
    '#' + downId + ':checked ~ .fp-thumbs-' + uid + ' .fp-thumb-down-' + uid + '{background:#fee2e2;border-color:#dc2626;}' +
    '.fp-thankyou-' + uid + '{display:none;font-size:14px;color:#7c3aed;font-weight:600;margin-left:8px;}' +
    '#' + upId + ':checked ~ .fp-thumbs-' + uid + ' .fp-thankyou-' + uid + '{display:inline;}' +
    '#' + downId + ':checked ~ .fp-thumbs-' + uid + ' .fp-thankyou-' + uid + '{display:inline;}' +
    '</style>' +
    '<div class="fp-wrap-' + uid + '">' +
    '<div class="fp-prompt-' + uid + '">' + _esc(promptText) + '</div>' +
    '<input type="radio" id="' + upId + '" name="' + _esc(name) + '" value="up" class="fp-thumb-input-' + uid + '">' +
    '<input type="radio" id="' + downId + '" name="' + _esc(name) + '" value="down" class="fp-thumb-input-' + uid + '">' +
    '<div class="fp-thumbs-' + uid + '">' +
    '<label for="' + upId + '" class="fp-thumb-label-' + uid + ' fp-thumb-up-' + uid + '" title="Helpful">&#128077;</label>' +
    '<label for="' + downId + '" class="fp-thumb-label-' + uid + ' fp-thumb-down-' + uid + '" title="Not helpful">&#128078;</label>' +
    '<span class="fp-thankyou-' + uid + '">Thanks for your feedback!</span>' +
    '</div>' +
    '</div>';
};

// === Comparison / Feature Atoms ===

_RENDERERS['pros_cons_list'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6);
  var title = b.title || '';
  var pros = b.pros || [];
  var cons = b.cons || [];

  var prosHtml = '';
  for (var i = 0; i < pros.length; i++) {
    prosHtml += '<li class="pcl-pro-item-' + uid + '"><span class="pcl-pro-icon-' + uid + '">&#10003;</span><span>' + _esc(pros[i]) + '</span></li>';
  }

  var consHtml = '';
  for (var j = 0; j < cons.length; j++) {
    consHtml += '<li class="pcl-con-item-' + uid + '"><span class="pcl-con-icon-' + uid + '">&#10007;</span><span>' + _esc(cons[j]) + '</span></li>';
  }

  return '<style>' +
    '.pcl-wrap-' + uid + '{margin:1rem 0;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;}' +
    '.pcl-title-' + uid + '{font-size:16px;font-weight:700;color:#111827;padding:14px 16px;border-bottom:1px solid #e5e7eb;background:#f9fafb;}' +
    '.pcl-cols-' + uid + '{display:grid;grid-template-columns:1fr 1fr;}' +
    '.pcl-col-' + uid + '{padding:16px;}' +
    '.pcl-col-pros-' + uid + '{border-right:1px solid #e5e7eb;background:#f0fdf4;}' +
    '.pcl-col-cons-' + uid + '{background:#fff5f5;}' +
    '.pcl-col-header-' + uid + '{font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:10px;}' +
    '.pcl-col-pros-' + uid + ' .pcl-col-header-' + uid + '{color:#16a34a;}' +
    '.pcl-col-cons-' + uid + ' .pcl-col-header-' + uid + '{color:#dc2626;}' +
    '.pcl-list-' + uid + '{list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:8px;}' +
    '.pcl-pro-item-' + uid + ',.pcl-con-item-' + uid + '{display:flex;align-items:flex-start;gap:8px;font-size:14px;color:#374151;}' +
    '.pcl-pro-icon-' + uid + '{color:#16a34a;font-weight:700;flex-shrink:0;margin-top:1px;}' +
    '.pcl-con-icon-' + uid + '{color:#dc2626;font-weight:700;flex-shrink:0;margin-top:1px;}' +
    '</style>' +
    '<div class="pcl-wrap-' + uid + '">' +
    (title ? '<div class="pcl-title-' + uid + '">' + _esc(title) + '</div>' : '') +
    '<div class="pcl-cols-' + uid + '">' +
    '<div class="pcl-col-' + uid + ' pcl-col-pros-' + uid + '">' +
    '<div class="pcl-col-header-' + uid + '">Pros</div>' +
    '<ul class="pcl-list-' + uid + '">' + prosHtml + '</ul>' +
    '</div>' +
    '<div class="pcl-col-' + uid + ' pcl-col-cons-' + uid + '">' +
    '<div class="pcl-col-header-' + uid + '">Cons</div>' +
    '<ul class="pcl-list-' + uid + '">' + consHtml + '</ul>' +
    '</div>' +
    '</div>' +
    '</div>';
};

_RENDERERS['pricing_tier_card'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6);
  var name = b.name || '';
  var price = b.price || '';
  var period = b.period || '';
  var description = b.description || '';
  var features = b.features || [];
  var ctaLabel = b.cta_label || 'Get Started';
  var isRecommended = !!b.is_recommended;

  var featuresHtml = '';
  for (var i = 0; i < features.length; i++) {
    featuresHtml += '<li class="ptc-feat-' + uid + '"><span class="ptc-check-' + uid + '">&#10003;</span><span>' + _esc(features[i]) + '</span></li>';
  }

  return '<style>' +
    '.ptc-wrap-' + uid + '{position:relative;background:#fff;border-radius:12px;border:2px solid ' + (isRecommended ? '#7c3aed' : '#e5e7eb') + ';padding:24px;display:flex;flex-direction:column;gap:12px;' + (isRecommended ? 'box-shadow:0 4px 20px rgba(124,58,237,0.15);' : '') + '}' +
    '.ptc-badge-' + uid + '{position:absolute;top:-12px;left:50%;transform:translateX(-50%);background:#7c3aed;color:#fff;font-size:12px;font-weight:700;padding:3px 14px;border-radius:9999px;letter-spacing:0.05em;text-transform:uppercase;white-space:nowrap;}' +
    '.ptc-name-' + uid + '{font-size:18px;font-weight:700;color:#111827;}' +
    '.ptc-price-row-' + uid + '{display:flex;align-items:baseline;gap:4px;}' +
    '.ptc-price-' + uid + '{font-size:32px;font-weight:800;color:#111827;}' +
    '.ptc-period-' + uid + '{font-size:14px;color:#6b7280;}' +
    '.ptc-desc-' + uid + '{font-size:14px;color:#6b7280;}' +
    '.ptc-divider-' + uid + '{border:none;border-top:1px solid #e5e7eb;margin:4px 0;}' +
    '.ptc-feats-' + uid + '{list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:8px;flex:1;}' +
    '.ptc-feat-' + uid + '{display:flex;align-items:flex-start;gap:8px;font-size:14px;color:#374151;}' +
    '.ptc-check-' + uid + '{color:#7c3aed;font-weight:700;flex-shrink:0;}' +
    '.ptc-cta-' + uid + '{display:block;text-align:center;background:' + (isRecommended ? '#7c3aed' : '#f3f4f6') + ';color:' + (isRecommended ? '#fff' : '#374151') + ';border:none;border-radius:8px;padding:11px 20px;font-size:15px;font-weight:600;cursor:pointer;text-decoration:none;margin-top:8px;transition:background 0.15s;}' +
    '.ptc-cta-' + uid + ':hover{background:' + (isRecommended ? '#6d28d9' : '#e5e7eb') + ';}' +
    '</style>' +
    '<div class="ptc-wrap-' + uid + '">' +
    (isRecommended ? '<div class="ptc-badge-' + uid + '">Recommended</div>' : '') +
    '<div class="ptc-name-' + uid + '">' + _esc(name) + '</div>' +
    '<div class="ptc-price-row-' + uid + '"><span class="ptc-price-' + uid + '">' + _esc(price) + '</span>' + (period ? '<span class="ptc-period-' + uid + '">/' + _esc(period) + '</span>' : '') + '</div>' +
    (description ? '<div class="ptc-desc-' + uid + '">' + _esc(description) + '</div>' : '') +
    '<hr class="ptc-divider-' + uid + '">' +
    '<ul class="ptc-feats-' + uid + '">' + featuresHtml + '</ul>' +
    '<button class="ptc-cta-' + uid + '">' + _esc(ctaLabel) + '</button>' +
    '</div>';
};

_RENDERERS['pricing_tier_group'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6);
  var tiers = b.tiers || [];

  var tiersHtml = '';
  for (var i = 0; i < tiers.length; i++) {
    if (_RENDERERS['pricing_tier_card']) {
      tiersHtml += '<div class="ptg-tier-' + uid + '">' + _RENDERERS['pricing_tier_card'](tiers[i]) + '</div>';
    }
  }

  return '<style>' +
    '.ptg-wrap-' + uid + '{margin:1rem 0;display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:20px;align-items:stretch;}' +
    '.ptg-tier-' + uid + '{display:flex;flex-direction:column;}' +
    '.ptg-tier-' + uid + ' > div{flex:1;}' +
    '</style>' +
    '<div class="ptg-wrap-' + uid + '">' + tiersHtml + '</div>';
};

_RENDERERS['versus_block'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6);
  var left = b.left || {};
  var right = b.right || {};
  var metricLabel = b.metric_label || '';

  var leftTitle = left.title || '';
  var rightTitle = right.title || '';
  var leftItems = left.items || [];
  var rightItems = right.items || [];

  var leftHtml = '';
  for (var i = 0; i < leftItems.length; i++) {
    leftHtml += '<li class="vb-item-' + uid + '">' + _esc(leftItems[i]) + '</li>';
  }

  var rightHtml = '';
  for (var j = 0; j < rightItems.length; j++) {
    rightHtml += '<li class="vb-item-' + uid + '">' + _esc(rightItems[j]) + '</li>';
  }

  return '<style>' +
    '.vb-wrap-' + uid + '{margin:1rem 0;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;}' +
    (metricLabel ? '.vb-metric-' + uid + '{text-align:center;font-size:13px;font-weight:600;color:#6b7280;background:#f9fafb;padding:8px;border-bottom:1px solid #e5e7eb;text-transform:uppercase;letter-spacing:0.04em;}' : '') +
    '.vb-cols-' + uid + '{display:grid;grid-template-columns:1fr auto 1fr;}' +
    '.vb-col-' + uid + '{padding:20px;}' +
    '.vb-col-left-' + uid + '{background:#eff6ff;}' +
    '.vb-col-right-' + uid + '{background:#fdf4ff;}' +
    '.vb-col-title-' + uid + '{font-size:16px;font-weight:700;color:#111827;margin-bottom:12px;}' +
    '.vb-list-' + uid + '{list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:6px;}' +
    '.vb-item-' + uid + '{font-size:14px;color:#374151;padding:4px 0;border-bottom:1px solid rgba(0,0,0,0.05);}' +
    '.vb-vs-' + uid + '{display:flex;align-items:center;justify-content:center;padding:0 12px;background:#fff;border-left:1px solid #e5e7eb;border-right:1px solid #e5e7eb;}' +
    '.vb-vs-text-' + uid + '{font-size:16px;font-weight:800;color:#9ca3af;writing-mode:vertical-lr;letter-spacing:0.1em;}' +
    '</style>' +
    '<div class="vb-wrap-' + uid + '">' +
    (metricLabel ? '<div class="vb-metric-' + uid + '">' + _esc(metricLabel) + '</div>' : '') +
    '<div class="vb-cols-' + uid + '">' +
    '<div class="vb-col-' + uid + ' vb-col-left-' + uid + '">' +
    '<div class="vb-col-title-' + uid + '">' + _esc(leftTitle) + '</div>' +
    '<ul class="vb-list-' + uid + '">' + leftHtml + '</ul>' +
    '</div>' +
    '<div class="vb-vs-' + uid + '"><span class="vb-vs-text-' + uid + '">VS</span></div>' +
    '<div class="vb-col-' + uid + ' vb-col-right-' + uid + '">' +
    '<div class="vb-col-title-' + uid + '">' + _esc(rightTitle) + '</div>' +
    '<ul class="vb-list-' + uid + '">' + rightHtml + '</ul>' +
    '</div>' +
    '</div>' +
    '</div>';
};

_RENDERERS['feature_matrix'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6);
  var tiers = b.tiers || [];
  var features = b.features || [];

  var headerHtml = '<th class="fm-th-' + uid + ' fm-th-feat-' + uid + '">Feature</th>';
  for (var t = 0; t < tiers.length; t++) {
    headerHtml += '<th class="fm-th-' + uid + '">' + _esc(tiers[t]) + '</th>';
  }

  var rowsHtml = '';
  for (var i = 0; i < features.length; i++) {
    var feat = features[i];
    var featName = feat.name || '';
    var tierVals = feat.tiers || {};
    var rowHtml = '<td class="fm-td-' + uid + ' fm-td-feat-' + uid + '">' + _esc(featName) + '</td>';
    for (var j = 0; j < tiers.length; j++) {
      var tierName = tiers[j];
      var val = tierVals[tierName];
      var cell;
      if (val === true || val === 'true') {
        cell = '<span class="fm-yes-' + uid + '">&#10003;</span>';
      } else if (val === false || val === 'false' || val === undefined || val === null) {
        cell = '<span class="fm-no-' + uid + '">&#10007;</span>';
      } else {
        cell = '<span class="fm-val-' + uid + '">' + _esc(String(val)) + '</span>';
      }
      rowHtml += '<td class="fm-td-' + uid + ' fm-td-center-' + uid + '">' + cell + '</td>';
    }
    rowsHtml += '<tr class="fm-tr-' + uid + '">' + rowHtml + '</tr>';
  }

  return '<style>' +
    '.fm-wrap-' + uid + '{margin:1rem 0;overflow-x:auto;border-radius:10px;border:1px solid #e5e7eb;}' +
    '.fm-table-' + uid + '{width:100%;border-collapse:collapse;font-size:14px;}' +
    '.fm-th-' + uid + '{background:#7c3aed;color:#fff;padding:11px 16px;text-align:center;font-weight:700;font-size:13px;}' +
    '.fm-th-feat-' + uid + '{text-align:left;background:#6d28d9;}' +
    '.fm-td-' + uid + '{padding:11px 16px;border-bottom:1px solid #f3f4f6;color:#374151;}' +
    '.fm-td-center-' + uid + '{text-align:center;}' +
    '.fm-td-feat-' + uid + '{font-weight:600;color:#111827;}' +
    '.fm-tr-' + uid + ':last-child td{border-bottom:none;}' +
    '.fm-tr-' + uid + ':hover td{background:#faf5ff;}' +
    '.fm-yes-' + uid + '{color:#16a34a;font-weight:700;font-size:16px;}' +
    '.fm-no-' + uid + '{color:#dc2626;font-size:16px;}' +
    '.fm-val-' + uid + '{color:#374151;}' +
    '</style>' +
    '<div class="fm-wrap-' + uid + '">' +
    '<table class="fm-table-' + uid + '">' +
    '<thead><tr>' + headerHtml + '</tr></thead>' +
    '<tbody>' + rowsHtml + '</tbody>' +
    '</table>' +
    '</div>';
};

_RENDERERS['side_by_side_spec'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6);
  var left = b.left || {};
  var right = b.right || {};

  var leftTitle = left.title || '';
  var rightTitle = right.title || '';
  var leftSpecs = left.specs || [];
  var rightSpecs = right.specs || [];

  function renderSpecs(specs, side) {
    var html = '';
    for (var i = 0; i < specs.length; i++) {
      var s = specs[i];
      html += '<tr class="sbs-tr-' + uid + '">' +
        '<td class="sbs-td-label-' + uid + '">' + _esc(s.label || '') + '</td>' +
        '<td class="sbs-td-val-' + uid + '">' + _esc(s.value || '') + '</td>' +
        '</tr>';
    }
    return html;
  }

  return '<style>' +
    '.sbs-wrap-' + uid + '{margin:1rem 0;display:grid;grid-template-columns:1fr 1fr;gap:0;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;}' +
    '.sbs-col-' + uid + '{padding:0;}' +
    '.sbs-col-right-' + uid + '{border-left:1px solid #e5e7eb;}' +
    '.sbs-col-title-' + uid + '{font-size:15px;font-weight:700;color:#fff;background:#7c3aed;padding:12px 16px;}' +
    '.sbs-table-' + uid + '{width:100%;border-collapse:collapse;font-size:14px;}' +
    '.sbs-tr-' + uid + ':nth-child(even){background:#f9fafb;}' +
    '.sbs-td-label-' + uid + '{padding:9px 16px;color:#6b7280;font-weight:500;width:45%;border-bottom:1px solid #f3f4f6;}' +
    '.sbs-td-val-' + uid + '{padding:9px 16px;color:#111827;font-weight:600;border-bottom:1px solid #f3f4f6;}' +
    '</style>' +
    '<div class="sbs-wrap-' + uid + '">' +
    '<div class="sbs-col-' + uid + '">' +
    '<div class="sbs-col-title-' + uid + '">' + _esc(leftTitle) + '</div>' +
    '<table class="sbs-table-' + uid + '"><tbody>' + renderSpecs(leftSpecs, 'left') + '</tbody></table>' +
    '</div>' +
    '<div class="sbs-col-' + uid + ' sbs-col-right-' + uid + '">' +
    '<div class="sbs-col-title-' + uid + '">' + _esc(rightTitle) + '</div>' +
    '<table class="sbs-table-' + uid + '"><tbody>' + renderSpecs(rightSpecs, 'right') + '</tbody></table>' +
    '</div>' +
    '</div>';
};

_RENDERERS['product_spec_table'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6);
  var specs = b.specs || [];
  var title = b.title || '';

  var rowsHtml = '';
  for (var i = 0; i < specs.length; i++) {
    var s = specs[i];
    var note = s.note || '';
    rowsHtml +=
      '<tr class="pst-tr-' + uid + '">' +
      '<td class="pst-td-label-' + uid + '">' + _esc(s.label || '') + '</td>' +
      '<td class="pst-td-val-' + uid + '">' +
      _esc(s.value || '') +
      (note ? '<span class="pst-note-' + uid + '"> &mdash; ' + _esc(note) + '</span>' : '') +
      '</td>' +
      '</tr>';
  }

  return '<style>' +
    '.pst-wrap-' + uid + '{margin:1rem 0;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;}' +
    (title ? '.pst-title-' + uid + '{font-size:15px;font-weight:700;color:#111827;background:#f9fafb;padding:12px 16px;border-bottom:1px solid #e5e7eb;}' : '') +
    '.pst-table-' + uid + '{width:100%;border-collapse:collapse;font-size:14px;}' +
    '.pst-tr-' + uid + ':nth-child(even){background:#f9fafb;}' +
    '.pst-td-label-' + uid + '{padding:10px 16px;color:#6b7280;font-weight:600;width:40%;border-bottom:1px solid #f3f4f6;vertical-align:top;}' +
    '.pst-td-val-' + uid + '{padding:10px 16px;color:#111827;border-bottom:1px solid #f3f4f6;vertical-align:top;}' +
    '.pst-note-' + uid + '{color:#9ca3af;font-size:12px;}' +
    '.pst-tr-' + uid + ':last-child td{border-bottom:none;}' +
    '</style>' +
    '<div class="pst-wrap-' + uid + '">' +
    (title ? '<div class="pst-title-' + uid + '">' + _esc(title) + '</div>' : '') +
    '<table class="pst-table-' + uid + '"><tbody>' + rowsHtml + '</tbody></table>' +
    '</div>';
};

_RENDERERS['comparison_grid'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6);
  var items = b.items || [];
  var title = b.title || '';

  var itemsHtml = '';
  for (var i = 0; i < items.length; i++) {
    var item = items[i];
    var name = item.name || '';
    var value = item.value || '';
    var highlight = !!item.highlight;
    itemsHtml +=
      '<div class="cg-item-' + uid + (highlight ? ' cg-item-hl-' + uid : '') + '">' +
      '<div class="cg-item-value-' + uid + '">' + _esc(value) + '</div>' +
      '<div class="cg-item-name-' + uid + '">' + _esc(name) + '</div>' +
      '</div>';
  }

  return '<style>' +
    '.cg-wrap-' + uid + '{margin:1rem 0;}' +
    (title ? '.cg-title-' + uid + '{font-size:16px;font-weight:700;color:#111827;margin-bottom:12px;}' : '') +
    '.cg-grid-' + uid + '{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:12px;}' +
    '.cg-item-' + uid + '{padding:16px;border:1.5px solid #e5e7eb;border-radius:10px;background:#fff;text-align:center;transition:border-color 0.15s;}' +
    '.cg-item-hl-' + uid + '{border-color:#7c3aed;background:#faf5ff;}' +
    '.cg-item-value-' + uid + '{font-size:22px;font-weight:800;color:#7c3aed;margin-bottom:4px;}' +
    '.cg-item-name-' + uid + '{font-size:13px;color:#6b7280;font-weight:500;}' +
    '</style>' +
    '<div class="cg-wrap-' + uid + '">' +
    (title ? '<div class="cg-title-' + uid + '">' + _esc(title) + '</div>' : '') +
    '<div class="cg-grid-' + uid + '">' + itemsHtml + '</div>' +
    '</div>';
};



// === Batch 5: SVG Chart & Data Viz Atoms ===

// Helper for linear scale (local to this batch)
function _linScale(val, domMin, domMax, rangeMin, rangeMax) {
  if (domMax === domMin) return rangeMin;
  return rangeMin + (val - domMin) / (domMax - domMin) * (rangeMax - rangeMin);
}

// Default color palette for charts
var _CHART_PALETTE = ['#6366f1','#22d3ee','#34d399','#fb923c','#f472b6','#a78bfa','#facc15','#818cf8','#e879f9','#2dd4bf'];

// ─────────────────────────────────────────────────────────
// 1. chartjs_bar — SVG horizontal or vertical bar chart
// ─────────────────────────────────────────────────────────
_RENDERERS['chartjs_bar'] = function(b) {
  var data        = b.data || [];
  var title       = b.title || '';
  var orientation = b.orientation || 'vertical';
  var height      = parseInt(b.height) || 220;
  var width       = parseInt(b.width)  || 560;
  var showVals    = b.show_values === true || b.show_values === 'true';
  var barColor    = b.bar_color || '#6366f1';

  if (!data.length) return '<div class="a2ui-chart-empty">No data</div>';

  var vals   = data.map(function(d){ return parseFloat(d.value) || 0; });
  var maxVal = Math.max.apply(null, vals);
  if (maxVal === 0) maxVal = 1;

  var svg = '';

  if (orientation === 'horizontal') {
    // Horizontal bars
    var padL = 120, padR = 60, padT = 30, padB = 20;
    var barH     = 22;
    var barGap   = 10;
    var totalH   = padT + data.length * (barH + barGap) + padB;
    var chartW   = width - padL - padR;

    svg += '<svg viewBox="0 0 ' + width + ' ' + totalH + '" width="100%" preserveAspectRatio="xMidYMid meet">';
    if (title) svg += '<text x="' + (width/2) + '" y="18" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">' + _esc(title) + '</text>';

    // Gridlines
    for (var g = 0; g <= 4; g++) {
      var gx = padL + (g / 4) * chartW;
      var gv = Math.round(maxVal * g / 4);
      svg += '<line x1="' + gx + '" y1="' + padT + '" x2="' + gx + '" y2="' + (totalH - padB) + '" stroke="#e2e8f0" stroke-width="1"/>';
      svg += '<text x="' + gx + '" y="' + (padT - 5) + '" text-anchor="middle" font-size="9" fill="#94a3b8">' + gv + '</text>';
    }

    data.forEach(function(d, i) {
      var val   = parseFloat(d.value) || 0;
      var bw    = _linScale(val, 0, maxVal, 0, chartW);
      var y     = padT + i * (barH + barGap);
      var color = d.color || barColor;
      svg += '<text x="' + (padL - 6) + '" y="' + (y + barH/2 + 4) + '" text-anchor="end" font-size="11" fill="#334155">' + _esc((d.label||'').substr(0,16)) + '</text>';
      svg += '<rect x="' + padL + '" y="' + y + '" width="' + bw + '" height="' + barH + '" rx="3" fill="' + _esc(color) + '"/>';
      if (showVals) {
        svg += '<text x="' + (padL + bw + 4) + '" y="' + (y + barH/2 + 4) + '" font-size="10" fill="#475569">' + val + '</text>';
      }
    });

    svg += '</svg>';
  } else {
    // Vertical bars
    var padL = 45, padR = 15, padT = 30, padB = 38;
    var chartH = height - padT - padB;
    var chartW = width  - padL - padR;
    var barW   = Math.max(8, (chartW / data.length) * 0.6);
    var barSpacing = chartW / data.length;

    svg += '<svg viewBox="0 0 ' + width + ' ' + height + '" width="100%" preserveAspectRatio="xMidYMid meet">';
    if (title) svg += '<text x="' + (width/2) + '" y="18" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">' + _esc(title) + '</text>';

    // Horizontal gridlines
    for (var g = 0; g <= 4; g++) {
      var gy = padT + (1 - g/4) * chartH;
      var gv = Math.round(maxVal * g / 4);
      svg += '<line x1="' + padL + '" y1="' + gy + '" x2="' + (width - padR) + '" y2="' + gy + '" stroke="#e2e8f0" stroke-width="1"/>';
      svg += '<text x="' + (padL - 4) + '" y="' + (gy + 4) + '" text-anchor="end" font-size="9" fill="#94a3b8">' + gv + '</text>';
    }

    // Baseline
    svg += '<line x1="' + padL + '" y1="' + (padT + chartH) + '" x2="' + (width - padR) + '" y2="' + (padT + chartH) + '" stroke="#cbd5e1" stroke-width="1.5"/>';

    data.forEach(function(d, i) {
      var val   = parseFloat(d.value) || 0;
      var bh    = _linScale(val, 0, maxVal, 0, chartH);
      var cx    = padL + (i + 0.5) * barSpacing;
      var x     = cx - barW / 2;
      var y     = padT + chartH - bh;
      var color = d.color || barColor;
      svg += '<rect x="' + x + '" y="' + y + '" width="' + barW + '" height="' + bh + '" rx="3" fill="' + _esc(color) + '"/>';
      if (showVals && bh > 12) {
        svg += '<text x="' + cx + '" y="' + (y - 3) + '" text-anchor="middle" font-size="9" fill="#475569">' + val + '</text>';
      }
      var lbl = (d.label||'').substr(0,10);
      svg += '<text x="' + cx + '" y="' + (padT + chartH + 14) + '" text-anchor="middle" font-size="10" fill="#64748b">' + _esc(lbl) + '</text>';
    });

    svg += '</svg>';
  }

  return '<div class="a2ui-chartjs-bar">' + svg + '</div>';
};

// ─────────────────────────────────────────────────────────
// 2. chartjs_line — SVG line/area chart
// ─────────────────────────────────────────────────────────
_RENDERERS['chartjs_line'] = function(b) {
  var title      = b.title || '';
  var height     = parseInt(b.height) || 260;
  var width      = parseInt(b.width)  || 560;
  var smooth     = b.smooth === true || b.smooth === 'true';
  var showPts    = b.show_points !== false && b.show_points !== 'false';
  var areaFill   = b.area_fill === true || b.area_fill === 'true';

  // Normalise to multi-dataset form
  var datasets, labels;
  if (b.datasets) {
    datasets = b.datasets;
    labels   = b.labels || datasets[0].data.map(function(_, i){ return String(i); });
  } else if (b.data) {
    labels   = b.data.map(function(d){ return d.label || ''; });
    datasets = [{ label: title, data: b.data.map(function(d){ return parseFloat(d.value)||0; }), color: '#6366f1' }];
    title    = '';
  } else {
    return '<div class="a2ui-chart-empty">No data</div>';
  }

  var padL = 50, padR = 20, padT = 36, padB = 50;
  var chartH = height - padT - padB;
  var chartW = width  - padL - padR;

  // Compute global min/max
  var allVals = [];
  datasets.forEach(function(ds){ ds.data.forEach(function(v){ allVals.push(parseFloat(v)||0); }); });
  var minVal = Math.min.apply(null, allVals);
  var maxVal = Math.max.apply(null, allVals);
  if (maxVal === minVal) { maxVal += 1; minVal -= 1; }

  var n = labels.length;

  function px(i)  { return padL + (n > 1 ? i / (n - 1) : 0.5) * chartW; }
  function py(v)  { return padT + (1 - (v - minVal) / (maxVal - minVal)) * chartH; }

  var svg = '<svg viewBox="0 0 ' + width + ' ' + height + '" width="100%" preserveAspectRatio="xMidYMid meet">';
  if (title) svg += '<text x="' + (width/2) + '" y="20" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">' + _esc(title) + '</text>';

  // Gridlines
  for (var g = 0; g <= 4; g++) {
    var gy = padT + (g / 4) * chartH;
    var gv = maxVal - (maxVal - minVal) * g / 4;
    svg += '<line x1="' + padL + '" y1="' + gy + '" x2="' + (width - padR) + '" y2="' + gy + '" stroke="#e2e8f0" stroke-width="1"/>';
    svg += '<text x="' + (padL - 4) + '" y="' + (gy + 4) + '" text-anchor="end" font-size="9" fill="#94a3b8">' + Math.round(gv) + '</text>';
  }

  // X-axis labels
  labels.forEach(function(lbl, i) {
    if (n <= 12 || i % Math.ceil(n / 10) === 0) {
      svg += '<text x="' + px(i) + '" y="' + (padT + chartH + 14) + '" text-anchor="middle" font-size="9" fill="#64748b">' + _esc((lbl||'').substr(0,8)) + '</text>';
    }
  });

  // Datasets
  datasets.forEach(function(ds, di) {
    var color = ds.color || _CHART_PALETTE[di % _CHART_PALETTE.length];
    var pts   = ds.data.map(function(v, i){ return { x: px(i), y: py(parseFloat(v)||0) }; });
    if (!pts.length) return;

    // Build path
    var pathD = '';
    if (smooth && pts.length > 2) {
      pathD = 'M ' + pts[0].x + ' ' + pts[0].y;
      for (var i = 0; i < pts.length - 1; i++) {
        var cp1x = pts[i].x + (pts[i+1].x - pts[i].x) / 3;
        var cp1y = pts[i].y;
        var cp2x = pts[i+1].x - (pts[i+1].x - pts[i].x) / 3;
        var cp2y = pts[i+1].y;
        pathD += ' C ' + cp1x + ' ' + cp1y + ' ' + cp2x + ' ' + cp2y + ' ' + pts[i+1].x + ' ' + pts[i+1].y;
      }
    } else {
      pathD = pts.map(function(p, i){ return (i ? 'L' : 'M') + p.x + ' ' + p.y; }).join(' ');
    }

    // Area fill
    if (areaFill || ds.fill) {
      var areaD = pathD + ' L ' + pts[pts.length-1].x + ' ' + (padT + chartH) + ' L ' + pts[0].x + ' ' + (padT + chartH) + ' Z';
      svg += '<path d="' + areaD + '" fill="' + _esc(color) + '" fill-opacity="0.18" stroke="none"/>';
    }

    svg += '<path d="' + pathD + '" fill="none" stroke="' + _esc(color) + '" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>';

    if (showPts) {
      pts.forEach(function(p) {
        svg += '<circle cx="' + p.x + '" cy="' + p.y + '" r="3.5" fill="' + _esc(color) + '" stroke="#fff" stroke-width="1.5"/>';
      });
    }
  });

  // Legend
  if (datasets.length > 1 || (datasets.length === 1 && datasets[0].label)) {
    var legY = padT + chartH + 28;
    var legX = padL;
    datasets.forEach(function(ds, di) {
      var color = ds.color || _CHART_PALETTE[di % _CHART_PALETTE.length];
      svg += '<rect x="' + legX + '" y="' + (legY - 7) + '" width="12" height="3" rx="1.5" fill="' + _esc(color) + '"/>';
      svg += '<text x="' + (legX + 16) + '" y="' + legY + '" font-size="10" fill="#64748b">' + _esc(ds.label||'') + '</text>';
      legX += 80;
    });
  }

  svg += '</svg>';
  return '<div class="a2ui-chartjs-line">' + svg + '</div>';
};

// ─────────────────────────────────────────────────────────
// 3. chartjs_pie — SVG pie/donut chart
// ─────────────────────────────────────────────────────────
_RENDERERS['chartjs_pie'] = function(b) {
  var data       = b.data || [];
  var title      = b.title || '';
  var donut      = b.donut === true || b.donut === 'true';
  var innerLabel = b.inner_label || '';
  var height     = parseInt(b.height) || 260;

  if (!data.length) return '<div class="a2ui-chart-empty">No data</div>';

  var total = data.reduce(function(s, d){ return s + (parseFloat(d.value)||0); }, 0);
  if (!total) return '<div class="a2ui-chart-empty">No data</div>';

  var width  = height;
  var cx     = width / 2;
  var cy     = height / 2 - 10;
  var r      = Math.min(cx, cy) - 10;

  var svg = '<svg viewBox="0 0 ' + width + ' ' + (height + 30) + '" width="100%" preserveAspectRatio="xMidYMid meet">';
  if (title) svg += '<text x="' + cx + '" y="14" text-anchor="middle" font-size="12" font-weight="bold" fill="#1e293b">' + _esc(title) + '</text>';

  var startAngle = -Math.PI / 2;
  var colors = _CHART_PALETTE;

  data.forEach(function(d, i) {
    var val      = parseFloat(d.value) || 0;
    var pct      = val / total;
    var endAngle = startAngle + pct * 2 * Math.PI;
    var x1       = cx + r * Math.cos(startAngle);
    var y1       = cy + r * Math.sin(startAngle);
    var x2       = cx + r * Math.cos(endAngle);
    var y2       = cy + r * Math.sin(endAngle);
    var largeArc = pct > 0.5 ? 1 : 0;
    var color    = d.color || colors[i % colors.length];

    var pathD = 'M ' + cx + ' ' + cy + ' L ' + x1 + ' ' + y1 +
                ' A ' + r + ' ' + r + ' 0 ' + largeArc + ' 1 ' + x2 + ' ' + y2 + ' Z';
    svg += '<path d="' + pathD + '" fill="' + _esc(color) + '" stroke="#fff" stroke-width="1.5"/>';
    startAngle = endAngle;
  });

  // Donut hole
  if (donut) {
    var ir = r * 0.55;
    svg += '<circle cx="' + cx + '" cy="' + cy + '" r="' + ir + '" fill="#fff"/>';
    if (innerLabel) {
      svg += '<text x="' + cx + '" y="' + (cy + 5) + '" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">' + _esc(innerLabel) + '</text>';
    }
  }

  // Legend below
  var legCols = Math.min(data.length, 3);
  var legW    = width / legCols;
  data.forEach(function(d, i) {
    var color = d.color || colors[i % colors.length];
    var lx    = (i % legCols) * legW + 4;
    var ly    = height + Math.floor(i / legCols) * 16 + 8;
    svg += '<rect x="' + lx + '" y="' + (ly - 8) + '" width="10" height="10" rx="2" fill="' + _esc(color) + '"/>';
    svg += '<text x="' + (lx + 13) + '" y="' + ly + '" font-size="9" fill="#64748b">' + _esc((d.label||'').substr(0,14)) + '</text>';
  });

  svg += '</svg>';
  return '<div class="a2ui-chartjs-pie">' + svg + '</div>';
};

// ─────────────────────────────────────────────────────────
// 4. benchmark_comparison — horizontal bar comparison
// ─────────────────────────────────────────────────────────
_RENDERERS['benchmark_comparison'] = function(b) {
  var items = b.benchmarks || [];
  var title = b.title || '';

  if (!items.length) return '<div class="a2ui-chart-empty">No benchmarks</div>';

  var vals   = items.map(function(d){ return parseFloat(d.value)||0; });
  var globalMax = Math.max.apply(null, vals);

  var padL = 130, padR = 80, padT = 30, rowH = 36, rowGap = 4;
  var width  = 560;
  var totalH = padT + items.length * (rowH + rowGap) + 20;
  var chartW = width - padL - padR;

  var svg = '<svg viewBox="0 0 ' + width + ' ' + totalH + '" width="100%" preserveAspectRatio="xMidYMid meet">';
  if (title) svg += '<text x="' + (width/2) + '" y="20" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">' + _esc(title) + '</text>';

  items.forEach(function(d, i) {
    var val    = parseFloat(d.value) || 0;
    var maxV   = parseFloat(d.max_value) || globalMax || 1;
    var pct    = Math.min(val / maxV, 1);
    var bw     = pct * chartW;
    var y      = padT + i * (rowH + rowGap);
    var color  = d.color || _CHART_PALETTE[i % _CHART_PALETTE.length];
    var unit   = d.unit || '';

    // Alternating row bg
    if (i % 2 === 0) {
      svg += '<rect x="0" y="' + y + '" width="' + width + '" height="' + rowH + '" fill="#f8fafc" rx="2"/>';
    }

    // Label
    svg += '<text x="' + (padL - 8) + '" y="' + (y + rowH/2 + 4) + '" text-anchor="end" font-size="11" fill="#334155">' + _esc((d.name||'').substr(0,18)) + '</text>';

    // Bar track
    svg += '<rect x="' + padL + '" y="' + (y + 8) + '" width="' + chartW + '" height="' + (rowH - 16) + '" rx="4" fill="#e2e8f0"/>';
    // Bar fill
    if (bw > 0) {
      svg += '<rect x="' + padL + '" y="' + (y + 8) + '" width="' + bw + '" height="' + (rowH - 16) + '" rx="4" fill="' + _esc(color) + '"/>';
    }

    // Value
    svg += '<text x="' + (padL + chartW + 6) + '" y="' + (y + rowH/2 + 4) + '" font-size="11" font-weight="600" fill="#1e293b">' + _esc(String(val) + (unit ? ' '+unit : '')) + '</text>';
  });

  svg += '</svg>';
  return '<div class="a2ui-benchmark-comparison">' + svg + '</div>';
};

// ─────────────────────────────────────────────────────────
// 5. data_table_sortable — styled data table
// ─────────────────────────────────────────────────────────
_RENDERERS['data_table_sortable'] = function(b) {
  var columns = b.columns || [];
  var rows    = b.rows    || [];
  var title   = b.title   || '';
  var striped = b.striped === true || b.striped === 'true';
  var compact = b.compact === true || b.compact === 'true';
  var uid     = Math.random().toString(36).substr(2,6);

  if (!columns.length && rows.length) {
    columns = Object.keys(rows[0]).map(function(k){ return { key: k, label: k }; });
  }
  if (!columns.length) return '<div class="a2ui-chart-empty">No columns defined</div>';

  var cellPad = compact ? '4px 8px' : '8px 12px';

  var html = '';
  if (title) html += '<div class="a2ui-table-title">' + _esc(title) + '</div>';

  html += '<div class="a2ui-table-wrap" style="overflow-x:auto;">';
  html += '<table id="tbl-' + uid + '" class="a2ui-data-table' + (striped ? ' striped' : '') + '" style="width:100%;border-collapse:collapse;font-size:13px;">';

  // Header
  html += '<thead><tr>';
  columns.forEach(function(col) {
    var align = col.type === 'number' ? 'right' : 'left';
    html += '<th data-key="' + _esc(col.key||'') + '" style="background:#1e293b;color:#f1f5f9;padding:' + cellPad + ';text-align:' + align + ';cursor:pointer;user-select:none;white-space:nowrap;" onclick="(function(th){var tbl=th.closest(\'table\');var idx=Array.from(th.parentNode.children).indexOf(th);var asc=th.dataset.asc!==\'1\';th.dataset.asc=asc?\'1\':\'\';Array.from(tbl.querySelectorAll(\'th\')).forEach(function(t){t.textContent=t.textContent.replace(/ [▲▼]$/,\'\');});th.textContent+=(asc?\' ▲\':\' ▼\');var tbody=tbl.querySelector(\'tbody\');var rowsArr=Array.from(tbody.querySelectorAll(\'tr\'));rowsArr.sort(function(a,b){var av=a.cells[idx]?a.cells[idx].textContent:\'\',bv=b.cells[idx]?b.cells[idx].textContent:\'\';var an=parseFloat(av),bn=parseFloat(bv);if(!isNaN(an)&&!isNaN(bn))return asc?an-bn:bn-an;return asc?av.localeCompare(bv):bv.localeCompare(av);});rowsArr.forEach(function(r){tbody.appendChild(r);});})(this)">';
    html += _esc(col.label || col.key || '');
    html += '</th>';
  });
  html += '</tr></thead>';

  // Body
  html += '<tbody>';
  rows.forEach(function(row, ri) {
    var bg = '';
    if (striped && ri % 2 === 1) bg = 'background:#f8fafc;';
    html += '<tr style="' + bg + '">';
    columns.forEach(function(col) {
      var val   = row[col.key];
      var align = col.type === 'number' ? 'right' : 'left';
      var disp  = (val === null || val === undefined) ? '' : String(val);
      html += '<td style="padding:' + cellPad + ';text-align:' + align + ';border-bottom:1px solid #f1f5f9;color:#334155;">' + _esc(disp) + '</td>';
    });
    html += '</tr>';
  });
  html += '</tbody></table></div>';

  return '<div class="a2ui-data-table-sortable">' + html + '</div>';
};

// ─────────────────────────────────────────────────────────
// 6. metric_comparison_card — compare two metrics
// ─────────────────────────────────────────────────────────
_RENDERERS['metric_comparison_card'] = function(b) {
  var baseline   = b.baseline   || {};
  var comparison = b.comparison || {};
  var title      = b.title || '';
  var higherBetter = b.higher_is_better !== false && b.higher_is_better !== 'false';

  var bVal  = parseFloat(baseline.value)   || 0;
  var cVal  = parseFloat(comparison.value) || 0;
  var delta = bVal !== 0 ? ((cVal - bVal) / Math.abs(bVal)) * 100 : 0;
  var better = higherBetter ? (cVal >= bVal) : (cVal <= bVal);
  var deltaColor = better ? '#16a34a' : '#dc2626';
  var arrow      = cVal >= bVal ? '↑' : '↓';
  var deltaTxt   = (delta >= 0 ? '+' : '') + delta.toFixed(1) + '%';

  var html = '<div class="a2ui-metric-comparison">';
  if (title) html += '<div class="a2ui-metric-cmp-title">' + _esc(title) + '</div>';
  html += '<div class="a2ui-metric-cmp-body">';

  // Baseline
  html += '<div class="a2ui-metric-cmp-col">';
  html += '<div class="a2ui-metric-cmp-lbl">' + _esc(baseline.label || 'Baseline') + '</div>';
  html += '<div class="a2ui-metric-cmp-val">' + _esc(String(bVal)) + (baseline.unit ? ' <span class="a2ui-metric-unit">' + _esc(baseline.unit) + '</span>' : '') + '</div>';
  html += '</div>';

  // Delta badge
  html += '<div class="a2ui-metric-cmp-delta" style="color:' + deltaColor + ';border-color:' + deltaColor + ';">' + arrow + ' ' + _esc(deltaTxt) + '</div>';

  // Comparison
  html += '<div class="a2ui-metric-cmp-col">';
  html += '<div class="a2ui-metric-cmp-lbl">' + _esc(comparison.label || 'Comparison') + '</div>';
  html += '<div class="a2ui-metric-cmp-val">' + _esc(String(cVal)) + (comparison.unit ? ' <span class="a2ui-metric-unit">' + _esc(comparison.unit) + '</span>' : '') + '</div>';
  html += '</div>';

  html += '</div></div>';
  return html;
};

// ─────────────────────────────────────────────────────────
// 7. mini_sparkline_set — multiple tiny sparklines
// ─────────────────────────────────────────────────────────
_RENDERERS['mini_sparkline_set'] = function(b) {
  var sparklines = b.sparklines || [];
  if (!sparklines.length) return '<div class="a2ui-chart-empty">No sparklines</div>';

  var html = '<div class="a2ui-sparkline-set">';

  sparklines.forEach(function(sp) {
    var data  = (sp.data || []).map(function(v){ return parseFloat(v)||0; });
    var color = sp.color || '#6366f1';
    var label = sp.label || '';
    var unit  = sp.unit  || '';
    var last  = data.length ? data[data.length-1] : 0;

    var svgW = 80, svgH = 30;
    var minV = Math.min.apply(null, data);
    var maxV = Math.max.apply(null, data);
    if (maxV === minV) { maxV += 1; }
    var n    = data.length;

    var pts = data.map(function(v, i) {
      var x = n > 1 ? (i / (n-1)) * svgW : svgW/2;
      var y = _linScale(v, minV, maxV, svgH - 2, 2);
      return x + ',' + y;
    }).join(' ');

    var sparkSvg = '<svg viewBox="0 0 ' + svgW + ' ' + svgH + '" width="' + svgW + '" height="' + svgH + '" style="display:inline-block;vertical-align:middle;">';
    if (data.length > 1) {
      sparkSvg += '<polyline points="' + pts + '" fill="none" stroke="' + _esc(color) + '" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round"/>';
    }
    sparkSvg += '</svg>';

    html += '<div class="a2ui-sparkline-row">';
    html += '<span class="a2ui-sparkline-label">' + _esc(label) + '</span>';
    html += sparkSvg;
    html += '<span class="a2ui-sparkline-val" style="color:' + _esc(color) + ';">' + _esc(String(last)) + (unit ? ' '+_esc(unit) : '') + '</span>';
    html += '</div>';
  });

  html += '</div>';
  return html;
};

// ─────────────────────────────────────────────────────────
// 8. donut_stat — large donut with center stat
// ─────────────────────────────────────────────────────────
_RENDERERS['donut_stat'] = function(b) {
  var value = Math.min(100, Math.max(0, parseFloat(b.value) || 0));
  var label = b.label || '';
  var color = b.color || '#22d3ee';
  var size  = parseInt(b.size) || 160;
  var unit  = b.unit !== undefined ? String(b.unit) : '%';
  var uid   = Math.random().toString(36).substr(2,6);

  var r         = size / 2 - 14;
  var cx        = size / 2;
  var cy        = size / 2;
  var circ      = 2 * Math.PI * r;
  var dashOffset = circ * (1 - value / 100);

  var html = '';
  html += '<style>@keyframes donut-spin-' + uid + '{from{stroke-dashoffset:' + circ.toFixed(2) + '}to{stroke-dashoffset:' + dashOffset.toFixed(2) + '}}</style>';
  html += '<div class="a2ui-donut-stat" style="display:inline-block;text-align:center;">';
  html += '<svg viewBox="0 0 ' + size + ' ' + size + '" width="' + size + '" height="' + size + '">';
  // Track
  html += '<circle cx="' + cx + '" cy="' + cy + '" r="' + r + '" fill="none" stroke="#e2e8f0" stroke-width="12"/>';
  // Arc
  html += '<circle cx="' + cx + '" cy="' + cy + '" r="' + r + '" fill="none" stroke="' + _esc(color) + '" stroke-width="12" stroke-linecap="round"' +
          ' stroke-dasharray="' + circ.toFixed(2) + '"' +
          ' stroke-dashoffset="' + circ.toFixed(2) + '"' +
          ' transform="rotate(-90 ' + cx + ' ' + cy + ')"' +
          ' style="animation:donut-spin-' + uid + ' 1s ease-out forwards;"/>';
  // Center text
  html += '<text x="' + cx + '" y="' + (cy - 4) + '" text-anchor="middle" font-size="' + Math.round(size*0.18) + '" font-weight="bold" fill="#1e293b">' + _esc(String(Math.round(value))) + '</text>';
  html += '<text x="' + cx + '" y="' + (cy + Math.round(size*0.14)) + '" text-anchor="middle" font-size="' + Math.round(size*0.1) + '" fill="#64748b">' + _esc(unit) + '</text>';
  html += '</svg>';
  if (label) html += '<div class="a2ui-donut-label" style="margin-top:4px;font-size:13px;color:#64748b;">' + _esc(label) + '</div>';
  html += '</div>';
  return html;
};

// ─────────────────────────────────────────────────────────
// 9. status_dashboard — grid of status items
// ─────────────────────────────────────────────────────────
_RENDERERS['status_dashboard'] = function(b) {
  var title = b.title || 'System Status';
  var items = b.items || [];

  var statusColors = {
    operational:  '#22c55e',
    degraded:     '#f59e0b',
    outage:       '#ef4444',
    maintenance:  '#6366f1'
  };
  var statusLabels = {
    operational: 'Operational',
    degraded:    'Degraded',
    outage:      'Outage',
    maintenance: 'Maintenance'
  };

  // Overall status
  var hasOutage      = items.some(function(i){ return i.status === 'outage'; });
  var hasDegraded    = items.some(function(i){ return i.status === 'degraded'; });
  var hasMaintenance = items.some(function(i){ return i.status === 'maintenance'; });
  var overallStatus  = hasOutage ? 'outage' : hasDegraded ? 'degraded' : hasMaintenance ? 'maintenance' : 'operational';
  var overallMessages = {
    operational: 'All systems operational',
    degraded:    'Some systems are experiencing degraded performance',
    outage:      'One or more systems are experiencing an outage',
    maintenance: 'Scheduled maintenance in progress'
  };

  var html = '<div class="a2ui-status-dashboard">';
  html += '<div class="a2ui-status-header" style="background:' + statusColors[overallStatus] + ';">';
  html += '<span class="a2ui-status-dot-lg" style="background:#fff;opacity:0.9;"></span>';
  html += '<div>';
  if (title) html += '<div class="a2ui-status-title">' + _esc(title) + '</div>';
  html += '<div class="a2ui-status-overall">' + _esc(overallMessages[overallStatus]) + '</div>';
  html += '</div></div>';

  html += '<div class="a2ui-status-list">';
  items.forEach(function(item) {
    var st    = item.status || 'operational';
    var color = statusColors[st] || '#94a3b8';
    var stLbl = statusLabels[st] || st;
    html += '<div class="a2ui-status-item">';
    html += '<span class="a2ui-status-dot" style="background:' + color + ';"></span>';
    html += '<div class="a2ui-status-info">';
    html += '<span class="a2ui-status-name">' + _esc(item.name || '') + '</span>';
    if (item.description) html += '<span class="a2ui-status-desc">' + _esc(item.description) + '</span>';
    html += '</div>';
    html += '<span class="a2ui-status-pill" style="background:' + color + '20;color:' + color + ';border:1px solid ' + color + '40;">' + _esc(stLbl) + '</span>';
    html += '</div>';
  });
  html += '</div></div>';
  return html;
};

// ─────────────────────────────────────────────────────────
// 10. uptime_timeline — horizontal uptime bar
// ─────────────────────────────────────────────────────────
_RENDERERS['uptime_timeline'] = function(b) {
  var label   = b.label || '';
  var pct     = parseFloat(b.uptime_percent) || 100;
  var period  = b.period || '';
  var days    = b.days || [];

  function dayColor(d) {
    var s = typeof d === 'object' ? (d.status !== undefined ? d.status : 1) : d;
    var v = parseFloat(s);
    if (v >= 1)   return '#22c55e';
    if (v >= 0.5) return '#f59e0b';
    return '#ef4444';
  }
  function dayTitle(d, i) {
    if (typeof d === 'object' && d.date) return d.date;
    return 'Day ' + (i+1);
  }

  var blockW = days.length > 0 ? Math.max(2, Math.min(8, Math.floor(480 / days.length))) : 6;
  var blockH = 24;
  var gap    = 1;
  var padL   = 10, padR = 70, padT = 20;
  var width  = 560;
  var svgW   = width - padL - padR;

  var html = '<div class="a2ui-uptime-row">';

  var svg = '<svg viewBox="0 0 ' + width + ' ' + (blockH + padT + 10) + '" width="100%" preserveAspectRatio="xMidYMid meet">';
  if (label) svg += '<text x="' + padL + '" y="14" font-size="12" font-weight="600" fill="#334155">' + _esc(label) + '</text>';

  var x = padL;
  days.forEach(function(d, i) {
    var color = dayColor(d);
    var ttl   = _esc(dayTitle(d, i));
    svg += '<rect x="' + x + '" y="' + padT + '" width="' + (blockW - gap) + '" height="' + blockH + '" rx="1.5" fill="' + color + '"><title>' + ttl + '</title></rect>';
    x += blockW;
  });

  // Fill remaining space gray if blocks don't fill width
  if (days.length === 0) {
    svg += '<rect x="' + padL + '" y="' + padT + '" width="' + svgW + '" height="' + blockH + '" rx="3" fill="#e2e8f0"/>';
  }

  // Uptime badge
  var badgeColor = pct >= 99 ? '#22c55e' : pct >= 95 ? '#f59e0b' : '#ef4444';
  var bx = width - padR + 4;
  svg += '<text x="' + bx + '" y="' + (padT + blockH/2 + 5) + '" font-size="12" font-weight="700" fill="' + badgeColor + '">' + pct.toFixed(2) + '%</text>';
  if (period) svg += '<text x="' + bx + '" y="' + (padT + blockH + 10) + '" font-size="9" fill="#94a3b8">' + _esc(period) + '</text>';

  svg += '</svg>';
  html += svg + '</div>';
  return html;
};

// ─────────────────────────────────────────────────────────
// 11. command_palette — searchable command list
// ─────────────────────────────────────────────────────────
_RENDERERS['command_palette'] = function(b) {
  var commands    = b.commands || [];
  var placeholder = b.placeholder || 'Search commands…';
  var uid         = Math.random().toString(36).substr(2,6);

  // Group by category
  var groups = {};
  var order  = [];
  commands.forEach(function(cmd) {
    var cat = cmd.category || 'General';
    if (!groups[cat]) { groups[cat] = []; order.push(cat); }
    groups[cat].push(cmd);
  });

  var html = '<div class="a2ui-cmd-palette" id="cp-' + uid + '">';
  html += '<div class="a2ui-cmd-search-wrap">';
  html += '<svg class="a2ui-cmd-search-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>';
  html += '<input class="a2ui-cmd-input" type="text" placeholder="' + _esc(placeholder) + '"' +
          ' oninput="(function(v){var items=document.querySelectorAll(\'#cp-' + uid + ' .a2ui-cmd-item\');var cats=document.querySelectorAll(\'#cp-' + uid + ' .a2ui-cmd-cat\');' +
          'items.forEach(function(el){var t=el.textContent.toLowerCase();el.style.display=t.indexOf(v.toLowerCase())>-1?\'\':\'none\';});' +
          'cats.forEach(function(cat){var anyVis=false;var next=cat.nextElementSibling;while(next&&!next.classList.contains(\'a2ui-cmd-cat\')){if(next.classList.contains(\'a2ui-cmd-item\')&&next.style.display!==\'none\')anyVis=true;next=next.nextElementSibling;}cat.style.display=anyVis?\'\':\'none\';});' +
          '})(this.value)"/>';
  html += '</div>';
  html += '<div class="a2ui-cmd-list">';

  order.forEach(function(cat) {
    html += '<div class="a2ui-cmd-cat">' + _esc(cat) + '</div>';
    groups[cat].forEach(function(cmd) {
      html += '<div class="a2ui-cmd-item">';
      html += '<span class="a2ui-cmd-name">' + _esc(cmd.name || '') + '</span>';
      if (cmd.description) html += '<span class="a2ui-cmd-desc">' + _esc(cmd.description) + '</span>';
      if (cmd.shortcut) html += '<kbd class="a2ui-cmd-shortcut">' + _esc(cmd.shortcut) + '</kbd>';
      html += '</div>';
    });
  });

  html += '</div></div>';
  return html;
};

// ─────────────────────────────────────────────────────────
// 12. search_result_card — Google-style search result
// ─────────────────────────────────────────────────────────
_RENDERERS['search_result_card'] = function(b) {
  var title      = b.title || '';
  var url        = b.url   || '#';
  var description= b.description || '';
  var breadcrumb = b.breadcrumb || [];
  var date       = b.date || '';
  var faviconUrl = b.favicon_url || '';

  var html = '<div class="a2ui-search-result">';

  // URL / breadcrumb row
  html += '<div class="a2ui-sr-url-row">';
  if (faviconUrl) {
    html += '<img src="' + _esc(faviconUrl) + '" class="a2ui-sr-favicon" width="16" height="16" onerror="this.style.display=\'none\'"/>';
  }
  if (breadcrumb.length) {
    html += '<span class="a2ui-sr-breadcrumb">' + breadcrumb.map(function(p){ return _esc(p); }).join(' › ') + '</span>';
  } else {
    html += '<span class="a2ui-sr-breadcrumb">' + _esc(url) + '</span>';
  }
  html += '</div>';

  // Title
  html += '<a class="a2ui-sr-title" href="' + _esc(url) + '" target="_blank" rel="noopener">' + _esc(title) + '</a>';

  // Meta (date)
  if (date) html += '<span class="a2ui-sr-date">' + _esc(date) + ' — </span>';

  // Description
  if (description) html += '<p class="a2ui-sr-desc">' + _esc(description) + '</p>';

  html += '</div>';
  return html;
};

// ─────────────────────────────────────────────────────────
// 13. punch_card — day-of-week × hour heatmap
// ─────────────────────────────────────────────────────────
_RENDERERS['punch_card'] = function(b) {
  var data  = b.data  || [];
  var title = b.title || '';

  var dayLabels  = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
  var hourLabels = ['0','','','','','','6','','','','','','12','','','','','','18','','','','','23'];

  // Build lookup
  var counts = {};
  var maxCount = 0;
  data.forEach(function(d) {
    var key = d.day + '-' + d.hour;
    counts[key] = (d.count || 0);
    if (d.count > maxCount) maxCount = d.count;
  });
  if (!maxCount) maxCount = 1;

  var cellW  = 18, cellH = 18, cellG = 3;
  var padL   = 36, padT = 30, padR = 10, padB = 10;
  var svgW   = padL + 24 * (cellW + cellG) + padR;
  var svgH   = padT + 7  * (cellH + cellG) + padB;

  var svg = '<svg viewBox="0 0 ' + svgW + ' ' + svgH + '" width="100%" preserveAspectRatio="xMidYMid meet">';
  if (title) svg += '<text x="' + (svgW/2) + '" y="14" text-anchor="middle" font-size="12" font-weight="bold" fill="#1e293b">' + _esc(title) + '</text>';

  // Hour labels
  for (var h = 0; h < 24; h++) {
    if (hourLabels[h]) {
      svg += '<text x="' + (padL + h*(cellW+cellG) + cellW/2) + '" y="' + (padT-4) + '" text-anchor="middle" font-size="8" fill="#94a3b8">' + hourLabels[h] + '</text>';
    }
  }
  // Day labels
  for (var d = 0; d < 7; d++) {
    svg += '<text x="' + (padL-4) + '" y="' + (padT + d*(cellH+cellG) + cellH/2 + 3) + '" text-anchor="end" font-size="9" fill="#64748b">' + dayLabels[d] + '</text>';
  }

  for (var day = 0; day < 7; day++) {
    for (var hour = 0; hour < 24; hour++) {
      var cnt = counts[day+'-'+hour] || 0;
      var opacity = cnt / maxCount;
      var r = 70 + Math.round(opacity * 115);
      var g = 50 + Math.round(opacity * 10);
      var bv = 200 + Math.round(opacity * 51);
      // Purple scale: light (#e9d5ff) to dark (#581c87)
      var fill = cnt === 0 ? '#f1f5f9' : 'rgb(' + Math.round(233 - opacity*152) + ',' + Math.round(213 - opacity*157) + ',' + Math.round(255 - opacity*130) + ')';
      var cx = padL + hour*(cellW+cellG);
      var cy = padT + day*(cellH+cellG);
      svg += '<rect x="' + cx + '" y="' + cy + '" width="' + cellW + '" height="' + cellH + '" rx="2" fill="' + fill + '"><title>' + dayLabels[day] + ' ' + hour + ':00 — ' + cnt + '</title></rect>';
    }
  }

  svg += '</svg>';
  return '<div class="a2ui-punch-card">' + svg + '</div>';
};

// ─────────────────────────────────────────────────────────
// 14. sankey_flow — simple flow diagram (HTML table style)
// ─────────────────────────────────────────────────────────
_RENDERERS['sankey_flow'] = function(b) {
  var nodes = b.nodes || [];
  var links = b.links || [];
  var title = b.title || '';

  // Build node label lookup
  var nodeMap = {};
  nodes.forEach(function(n){ nodeMap[n.id] = n.label || n.id; });

  // Group links by source
  var groups = {};
  var srcOrder = [];
  links.forEach(function(lk) {
    var src = lk.source;
    if (!groups[src]) { groups[src] = []; srcOrder.push(src); }
    groups[src].push(lk);
  });

  var html = '<div class="a2ui-sankey">';
  if (title) html += '<div class="a2ui-sankey-title">' + _esc(title) + '</div>';
  html += '<div class="a2ui-sankey-rows">';

  srcOrder.forEach(function(src) {
    var lks  = groups[src];
    var total = lks.reduce(function(s, l){ return s + (parseFloat(l.value)||0); }, 0);
    html += '<div class="a2ui-sankey-group">';
    html += '<div class="a2ui-sankey-src-hdr">' + _esc(nodeMap[src] || src) + ' <span class="a2ui-sankey-total">Total: ' + total.toLocaleString() + '</span></div>';
    lks.forEach(function(lk) {
      var pct = total > 0 ? ((lk.value / total) * 100).toFixed(1) : '0';
      html += '<div class="a2ui-sankey-link">';
      html += '<span class="a2ui-sankey-from">' + _esc(nodeMap[src] || src) + '</span>';
      html += '<span class="a2ui-sankey-arrow">→</span>';
      html += '<div class="a2ui-sankey-bar-wrap"><div class="a2ui-sankey-bar" style="width:' + pct + '%;"></div></div>';
      html += '<span class="a2ui-sankey-val">' + Number(lk.value).toLocaleString() + '</span>';
      html += '<span class="a2ui-sankey-arrow">→</span>';
      html += '<span class="a2ui-sankey-to">' + _esc(nodeMap[lk.target] || lk.target) + '</span>';
      html += '</div>';
    });
    html += '</div>';
  });

  html += '</div></div>';
  return html;
};

// ─────────────────────────────────────────────────────────
// 15. cohort_retention — retention grid
// ─────────────────────────────────────────────────────────
_RENDERERS['cohort_retention'] = function(b) {
  var cohorts = b.cohorts || [];
  var title   = b.title   || '';

  if (!cohorts.length) return '<div class="a2ui-chart-empty">No cohort data</div>';

  var maxCols = 0;
  cohorts.forEach(function(c){ if ((c.data||[]).length > maxCols) maxCols = c.data.length; });

  var html = '<div class="a2ui-cohort-retention">';
  if (title) html += '<div class="a2ui-cohort-title">' + _esc(title) + '</div>';
  html += '<div style="overflow-x:auto;"><table class="a2ui-cohort-table" style="border-collapse:collapse;font-size:12px;width:100%;">';

  // Header
  html += '<thead><tr><th class="a2ui-cohort-th">Cohort</th>';
  for (var w = 0; w < maxCols; w++) {
    html += '<th class="a2ui-cohort-th">Week ' + w + '</th>';
  }
  html += '</tr></thead><tbody>';

  cohorts.forEach(function(cohort) {
    html += '<tr>';
    html += '<td class="a2ui-cohort-label">' + _esc(cohort.label || '') + '</td>';
    var data = cohort.data || [];
    for (var w = 0; w < maxCols; w++) {
      var val = data[w] !== undefined ? parseFloat(data[w]) : null;
      if (val === null) {
        html += '<td class="a2ui-cohort-cell" style="background:#f8fafc;"></td>';
      } else {
        var pct = Math.min(100, Math.max(0, val));
        var alpha = pct / 100;
        // purple: rgb(99,102,241) deep to light
        var r = Math.round(237 - alpha * 138);
        var g = Math.round(233 - alpha * 131);
        var bv = Math.round(254 - alpha * 13);
        var bg = 'rgb(' + r + ',' + g + ',' + bv + ')';
        var fg = pct > 60 ? '#fff' : '#334155';
        html += '<td class="a2ui-cohort-cell" style="background:' + bg + ';color:' + fg + ';">' + pct.toFixed(0) + '%</td>';
      }
    }
    html += '</tr>';
  });

  html += '</tbody></table></div></div>';
  return html;
};

// ─────────────────────────────────────────────────────────
// 16. heatmap — generic 2D heatmap
// ─────────────────────────────────────────────────────────
_RENDERERS['heatmap'] = function(b) {
  var rowLabels   = b.rows  || [];
  var colLabels   = b.cols  || [];
  var data        = b.data  || [];
  var title       = b.title || '';
  var colorScheme = b.color_scheme || 'purple';

  if (!rowLabels.length || !colLabels.length) return '<div class="a2ui-chart-empty">No heatmap data</div>';

  // Color schemes: [lightR,lightG,lightB, darkR,darkG,darkB]
  var schemes = {
    purple: [237,233,254, 88,28,135],
    blue:   [219,234,254, 30,58,138],
    green:  [220,252,231, 22,101,52],
    red:    [254,226,226, 127,29,29]
  };
  var cs = schemes[colorScheme] || schemes.purple;

  // Flatten to find min/max
  var allVals = [];
  data.forEach(function(row){ row.forEach(function(v){ allVals.push(parseFloat(v)||0); }); });
  var minV = Math.min.apply(null, allVals);
  var maxV = Math.max.apply(null, allVals);
  if (maxV === minV) maxV += 1;

  var padL = 80, padT = 30, cellW = Math.min(60, Math.max(28, Math.floor(480/colLabels.length))), cellH = 28;
  var svgW = padL + colLabels.length * cellW + 10;
  var svgH = padT + rowLabels.length * cellH + 16;

  var svg = '<svg viewBox="0 0 ' + svgW + ' ' + svgH + '" width="100%" preserveAspectRatio="xMidYMid meet">';
  if (title) svg += '<text x="' + (svgW/2) + '" y="16" text-anchor="middle" font-size="12" font-weight="bold" fill="#1e293b">' + _esc(title) + '</text>';

  // Column labels
  colLabels.forEach(function(cl, ci) {
    svg += '<text x="' + (padL + ci*cellW + cellW/2) + '" y="' + (padT - 4) + '" text-anchor="middle" font-size="9" fill="#64748b">' + _esc(String(cl).substr(0,8)) + '</text>';
  });

  // Rows
  rowLabels.forEach(function(rl, ri) {
    svg += '<text x="' + (padL - 4) + '" y="' + (padT + ri*cellH + cellH/2 + 4) + '" text-anchor="end" font-size="9" fill="#64748b">' + _esc(String(rl).substr(0,12)) + '</text>';
    var rowData = data[ri] || [];
    colLabels.forEach(function(cl, ci) {
      var val   = parseFloat(rowData[ci]) || 0;
      var alpha = (val - minV) / (maxV - minV);
      var r = Math.round(cs[0] + alpha * (cs[3] - cs[0]));
      var g = Math.round(cs[1] + alpha * (cs[4] - cs[1]));
      var bv= Math.round(cs[2] + alpha * (cs[5] - cs[2]));
      var bg = 'rgb(' + r + ',' + g + ',' + bv + ')';
      var fg = alpha > 0.55 ? '#fff' : '#334155';
      var cx = padL + ci * cellW;
      var cy = padT + ri * cellH;
      svg += '<rect x="' + cx + '" y="' + cy + '" width="' + (cellW-1) + '" height="' + (cellH-1) + '" fill="' + bg + '"><title>' + _esc(String(rl)) + ' / ' + _esc(String(cl)) + ': ' + val + '</title></rect>';
      if (cellW > 30) {
        svg += '<text x="' + (cx+cellW/2) + '" y="' + (cy+cellH/2+4) + '" text-anchor="middle" font-size="9" fill="' + fg + '">' + val + '</text>';
      }
    });
  });

  svg += '</svg>';
  return '<div class="a2ui-heatmap">' + svg + '</div>';
};

// ─────────────────────────────────────────────────────────
// 17. github_activity_grid — contribution graph
// ─────────────────────────────────────────────────────────
_RENDERERS['github_activity_grid'] = function(b) {
  var weeks = b.weeks || [];
  var title = b.title || '';
  var year  = b.year  || '';

  var cellS = 11, cellG = 2;
  var padL  = 24, padT = 24, padR = 6, padB = 6;
  var colors = ['#161b22','#0e4429','#006d32','#26a641','#39d353'];
  // 0 commits = light grey in our light-mode rendering
  var emptyColor = '#ebedf0';

  var dayLabels = {1:'Mon', 3:'Wed', 5:'Fri'};
  var svgW = padL + (weeks.length || 53) * (cellS + cellG) + padR;
  var svgH = padT + 7 * (cellS + cellG) + padB;

  var svg = '<svg viewBox="0 0 ' + svgW + ' ' + svgH + '" width="100%" preserveAspectRatio="xMidYMid meet" style="background:#fff;">';
  if (title || year) svg += '<text x="' + padL + '" y="14" font-size="11" font-weight="600" fill="#24292e">' + _esc(title + (year ? ' '+year : '')) + '</text>';

  // Day labels (left)
  [1,3,5].forEach(function(d) {
    svg += '<text x="' + (padL-2) + '" y="' + (padT + d*(cellS+cellG) + cellS/2 + 3) + '" text-anchor="end" font-size="8" fill="#57606a">' + dayLabels[d] + '</text>';
  });

  // Month labels (top) — detect first day of each month from data
  var lastMonth = '';
  weeks.forEach(function(week, wi) {
    if (week && week[0] && week[0].date) {
      var mo = week[0].date.substr(0,7); // YYYY-MM
      if (mo !== lastMonth) {
        var monthNames = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
        var mIdx = parseInt(mo.substr(5,2)) - 1;
        svg += '<text x="' + (padL + wi*(cellS+cellG)) + '" y="' + (padT-4) + '" font-size="8" fill="#57606a">' + (monthNames[mIdx]||'') + '</text>';
        lastMonth = mo;
      }
    }
  });

  // All data — find max count for quartile
  var allCounts = [];
  weeks.forEach(function(week){ (week||[]).forEach(function(d){ if(d) allCounts.push(d.count||0); }); });
  allCounts.sort(function(a,b){return a-b;});
  var q = allCounts.length;
  function getLevel(count) {
    if (!count) return 0;
    var rank = allCounts.indexOf(count);
    if (rank < 0) rank = allCounts.filter(function(c){return c<=count;}).length - 1;
    var pct = rank / (q-1||1);
    return pct < 0.25 ? 1 : pct < 0.5 ? 2 : pct < 0.75 ? 3 : 4;
  }

  weeks.forEach(function(week, wi) {
    (week||[]).forEach(function(day, di) {
      if (!day) return;
      var cnt   = day.count || 0;
      var lvl   = getLevel(cnt);
      var color = cnt === 0 ? emptyColor : colors[lvl];
      var cx    = padL + wi*(cellS+cellG);
      var cy    = padT + di*(cellS+cellG);
      var ttl   = (day.date || ('Week '+(wi+1)+' Day '+(di+1))) + ': ' + cnt + ' contribution' + (cnt!==1?'s':'');
      svg += '<rect x="' + cx + '" y="' + cy + '" width="' + cellS + '" height="' + cellS + '" rx="2" fill="' + color + '"><title>' + _esc(ttl) + '</title></rect>';
    });
  });

  svg += '</svg>';
  return '<div class="a2ui-github-grid">' + svg + '</div>';
};

// ─────────────────────────────────────────────────────────
// 18. entity_list — structured entity/person list
// ─────────────────────────────────────────────────────────
_RENDERERS['entity_list'] = function(b) {
  var entities = b.entities || [];
  var title    = b.title    || '';

  var typeColors = {
    person:       '#6366f1',
    organization: '#22d3ee',
    location:     '#34d399',
    product:      '#fb923c',
    event:        '#f472b6'
  };

  var html = '<div class="a2ui-entity-list">';
  if (title) html += '<div class="a2ui-entity-list-title">' + _esc(title) + '</div>';
  html += '<div class="a2ui-entity-grid">';

  entities.forEach(function(entity) {
    var typeColor = typeColors[(entity.type||'').toLowerCase()] || '#94a3b8';
    var item = '';

    if (entity.link) {
      item += '<a class="a2ui-entity-card" href="' + _esc(entity.link) + '" target="_blank" rel="noopener" style="text-decoration:none;">';
    } else {
      item += '<div class="a2ui-entity-card">';
    }

    // Avatar
    item += '<div class="a2ui-entity-avatar">';
    if (entity.avatar_url) {
      item += '<img src="' + _esc(entity.avatar_url) + '" width="40" height="40" style="border-radius:50%;object-fit:cover;" onerror="this.style.display=\'none\';this.nextSibling.style.display=\'flex\'"/>';
      item += '<div class="a2ui-entity-initials" style="display:none;background:' + typeColor + ';">' + _esc((entity.name||'?').charAt(0).toUpperCase()) + '</div>';
    } else {
      item += '<div class="a2ui-entity-initials" style="background:' + typeColor + ';">' + _esc((entity.name||'?').charAt(0).toUpperCase()) + '</div>';
    }
    item += '</div>';

    // Info
    item += '<div class="a2ui-entity-info">';
    item += '<div class="a2ui-entity-name">' + _esc(entity.name || '') + '</div>';
    if (entity.type) item += '<span class="a2ui-entity-type" style="background:' + typeColor + '20;color:' + typeColor + ';border:1px solid ' + typeColor + '40;">' + _esc(entity.type) + '</span>';
    if (entity.description) item += '<div class="a2ui-entity-desc">' + _esc(entity.description) + '</div>';
    if (entity.meta) item += '<div class="a2ui-entity-meta">' + _esc(entity.meta) + '</div>';
    item += '</div>';

    item += entity.link ? '</a>' : '</div>';
    html += item;
  });

  html += '</div></div>';
  return html;
};



// === Batch 6: Misc Atoms + Animation Degraded Fallbacks ===

_RENDERERS['markdown_block'] = function(b) {
  var content = b.content || '';
  var html = _markdownToHtml(content);
  return '<div class="asw-markdown-block">' + html + '</div>';
};

_RENDERERS['bento_grid'] = function(b) {
  var items = b.items || [];
  var cols = b.cols || 3;
  var uid = Math.random().toString(36).substr(2, 6);
  var id = 'bento-' + uid;
  var colorSchemes = [
    {bg:'#f3f0ff',border:'#ede9fe'},
    {bg:'#fdf4ff',border:'#fae8ff'},
    {bg:'#f0fdf4',border:'#dcfce7'},
    {bg:'#eff6ff',border:'#dbeafe'},
    {bg:'#fff7ed',border:'#fed7aa'},
    {bg:'#fafafa',border:'#e5e7eb'}
  ];
  var itemsHtml = '';
  for (var i = 0; i < items.length; i++) {
    var item = items[i];
    var span = Math.min(Math.max(parseInt(item.span) || 1, 1), cols);
    var scheme = colorSchemes[i % colorSchemes.length];
    if (item.color_scheme === 'purple') { scheme = {bg:'#f3f0ff',border:'#ede9fe'}; }
    else if (item.color_scheme === 'green') { scheme = {bg:'#f0fdf4',border:'#dcfce7'}; }
    else if (item.color_scheme === 'blue') { scheme = {bg:'#eff6ff',border:'#dbeafe'}; }
    else if (item.color_scheme === 'orange') { scheme = {bg:'#fff7ed',border:'#fed7aa'}; }
    var iconHtml = item.icon ? '<div style="font-size:1.8rem;margin-bottom:8px;">' + _esc(item.icon) + '</div>' : '';
    var titleHtml = item.title ? '<div style="font-weight:700;font-size:1rem;color:#111827;margin-bottom:6px;">' + _esc(item.title) + '</div>' : '';
    var bodyHtml = item.body ? '<div style="font-size:0.875rem;color:#4b5563;line-height:1.5;">' + _esc(item.body) + '</div>' : '';
    itemsHtml += '<div style="grid-column:span ' + span + ';background:' + scheme.bg + ';border:1px solid ' + scheme.border + ';border-radius:14px;padding:20px;box-sizing:border-box;">' + iconHtml + titleHtml + bodyHtml + '</div>';
  }
  return '<div id="' + id + '" style="display:grid;grid-template-columns:repeat(' + cols + ',1fr);gap:14px;margin:1rem 0;">' + itemsHtml + '</div>';
};

_RENDERERS['cta_section'] = function(b) {
  var headline = b.headline || '';
  var subheadline = b.subheadline || '';
  var primaryLabel = b.primary_label || '';
  var primaryUrl = b.primary_url || '#';
  var secondaryLabel = b.secondary_label || '';
  var secondaryUrl = b.secondary_url || '#';
  var alignment = b.alignment === 'left' ? 'left' : 'center';
  var btnPrimary = primaryLabel ? '<a href="' + _esc(primaryUrl) + '" style="display:inline-block;background:#7c3aed;color:#fff;font-weight:600;padding:12px 28px;border-radius:8px;text-decoration:none;font-size:0.95rem;margin:6px;">' + _esc(primaryLabel) + '</a>' : '';
  var btnSecondary = secondaryLabel ? '<a href="' + _esc(secondaryUrl) + '" style="display:inline-block;background:transparent;color:#7c3aed;font-weight:600;padding:11px 27px;border-radius:8px;text-decoration:none;font-size:0.95rem;border:1.5px solid #7c3aed;margin:6px;">' + _esc(secondaryLabel) + '</a>' : '';
  return '<div style="background:linear-gradient(135deg,#f5f3ff,#faf5ff);border:1px solid #ede9fe;border-radius:16px;padding:40px 32px;margin:1rem 0;text-align:' + alignment + ';">'
    + (headline ? '<h2 style="margin:0 0 12px;font-size:1.75rem;font-weight:800;color:#111827;">' + _esc(headline) + '</h2>' : '')
    + (subheadline ? '<p style="margin:0 0 24px;font-size:1.05rem;color:#4b5563;">' + _esc(subheadline) + '</p>' : '')
    + '<div>' + btnPrimary + btnSecondary + '</div>'
    + '</div>';
};

_RENDERERS['lozenge'] = function(b) {
  var text = b.text || '';
  var color = b.color || 'default';
  var colorMap = {
    'default': {bg:'#f3f4f6',fg:'#374151'},
    'success':  {bg:'#dcfce7',fg:'#166534'},
    'warning':  {bg:'#fef3c7',fg:'#92400e'},
    'danger':   {bg:'#fee2e2',fg:'#991b1b'},
    'info':     {bg:'#dbeafe',fg:'#1d4ed8'}
  };
  var c = colorMap[color] || colorMap['default'];
  return '<span style="display:inline-block;background:' + c.bg + ';color:' + c.fg + ';font-size:0.78rem;font-weight:600;padding:3px 10px;border-radius:999px;letter-spacing:0.02em;">' + _esc(text) + '</span>';
};

_RENDERERS['task_list'] = function(b) {
  var items = b.items || [];
  var priorityColors = {high:'#ef4444', medium:'#f59e0b', low:'#9ca3af'};
  var rows = '';
  for (var i = 0; i < items.length; i++) {
    var item = items[i];
    var dot = item.priority ? '<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:' + (priorityColors[item.priority] || '#9ca3af') + ';margin-right:8px;flex-shrink:0;"></span>' : '';
    var textStyle = item.done ? 'text-decoration:line-through;color:#9ca3af;' : 'color:#111827;';
    var checkIcon = item.done
      ? '<svg width="16" height="16" viewBox="0 0 16 16" style="flex-shrink:0;"><circle cx="8" cy="8" r="7" fill="#7c3aed"/><polyline points="4,8 7,11 12,5" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
      : '<svg width="16" height="16" viewBox="0 0 16 16" style="flex-shrink:0;"><circle cx="8" cy="8" r="7" fill="none" stroke="#d1d5db" stroke-width="1.5"/></svg>';
    rows += '<li style="display:flex;align-items:center;gap:8px;padding:8px 0;border-bottom:1px solid #f3f4f6;">'
      + checkIcon
      + '<span style="' + textStyle + 'flex:1;font-size:0.9rem;">' + _esc(item.text || '') + '</span>'
      + dot
      + '</li>';
  }
  return '<ul style="list-style:none;margin:0.5rem 0;padding:0;">' + rows + '</ul>';
};

_RENDERERS['vote_button_group'] = function(b) {
  var options = b.options || [];
  var question = b.question || '';
  var uid = Math.random().toString(36).substr(2, 6);
  var rows = '';
  for (var i = 0; i < options.length; i++) {
    var opt = options[i];
    var id = 'vote-' + uid + '-' + i;
    rows += '<label for="' + id + '" style="display:flex;align-items:center;gap:12px;padding:12px 16px;border:1.5px solid #e5e7eb;border-radius:10px;cursor:pointer;background:#fff;transition:border-color 0.15s;">'
      + '<input type="radio" name="vote-' + uid + '" id="' + id + '" value="' + i + '" style="accent-color:#7c3aed;">'
      + '<span style="flex:1;font-size:0.9rem;color:#111827;font-weight:500;">' + _esc(opt.label || '') + '</span>'
      + '<span style="font-size:0.82rem;color:#6b7280;background:#f3f4f6;padding:2px 8px;border-radius:999px;">' + (opt.votes || 0) + ' votes</span>'
      + '</label>';
  }
  return '<div style="margin:1rem 0;">'
    + (question ? '<p style="margin:0 0 12px;font-weight:700;color:#111827;font-size:1rem;">' + _esc(question) + '</p>' : '')
    + '<div style="display:flex;flex-direction:column;gap:8px;">' + rows + '</div>'
    + '</div>';
};

_RENDERERS['sprint_board'] = function(b) {
  var columns = b.columns || [];
  var colsHtml = '';
  var priorityColors = {high:'#ef4444', medium:'#f59e0b', low:'#10b981', null:'#d1d5db'};
  for (var c = 0; c < columns.length; c++) {
    var col = columns[c];
    var items = col.items || [];
    var cardsHtml = '';
    for (var i = 0; i < items.length; i++) {
      var item = items[i];
      var pcolor = priorityColors[item.priority] || '#d1d5db';
      var assigneeHtml = item.assignee ? '<div style="width:24px;height:24px;border-radius:50%;background:#7c3aed;color:#fff;font-size:0.7rem;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0;">' + _esc(item.assignee.charAt(0).toUpperCase()) + '</div>' : '';
      var labelsHtml = '';
      if (item.labels && item.labels.length) {
        for (var l = 0; l < item.labels.length; l++) {
          labelsHtml += '<span style="background:#ede9fe;color:#5b21b6;font-size:0.7rem;padding:1px 6px;border-radius:999px;">' + _esc(item.labels[l]) + '</span>';
        }
      }
      cardsHtml += '<div style="background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:12px;margin-bottom:8px;">'
        + '<div style="display:flex;align-items:flex-start;gap:8px;">'
        + '<div style="width:8px;height:8px;border-radius:50%;background:' + pcolor + ';flex-shrink:0;margin-top:5px;"></div>'
        + '<div style="flex:1;">'
        + (item.id ? '<div style="font-size:0.72rem;color:#9ca3af;margin-bottom:3px;">' + _esc(item.id) + '</div>' : '')
        + '<div style="font-size:0.87rem;font-weight:600;color:#111827;">' + _esc(item.title || '') + '</div>'
        + (labelsHtml ? '<div style="display:flex;flex-wrap:wrap;gap:4px;margin-top:6px;">' + labelsHtml + '</div>' : '')
        + '</div>'
        + assigneeHtml
        + '</div>'
        + '</div>';
    }
    colsHtml += '<div style="flex:1;min-width:200px;background:#f9fafb;border-radius:12px;padding:14px;">'
      + '<div style="font-weight:700;font-size:0.85rem;color:#374151;margin-bottom:12px;text-transform:uppercase;letter-spacing:0.05em;">' + _esc(col.title || '') + ' <span style="background:#e5e7eb;color:#6b7280;border-radius:999px;padding:1px 7px;font-size:0.75rem;">' + items.length + '</span></div>'
      + cardsHtml
      + '</div>';
  }
  return '<div style="display:flex;gap:12px;overflow-x:auto;margin:1rem 0;padding-bottom:4px;">' + colsHtml + '</div>';
};

_RENDERERS['jira_ticket'] = function(b) {
  var typeIcons = {bug:'🐛', story:'📖', task:'✅', epic:'⚡'};
  var typeColors = {bug:'#fee2e2', story:'#dbeafe', task:'#f0fdf4', epic:'#faf5ff'};
  var statusColors = {
    'To Do':'#f3f4f6','In Progress':'#dbeafe','Done':'#dcfce7',
    'Blocked':'#fee2e2','Review':'#fef3c7'
  };
  var type = b.type || 'task';
  var status = b.status || 'To Do';
  var icon = typeIcons[type] || '📋';
  var bgColor = typeColors[type] || '#f9fafb';
  var statusBg = statusColors[status] || '#f3f4f6';
  var labelsHtml = '';
  if (b.labels && b.labels.length) {
    for (var l = 0; l < b.labels.length; l++) {
      labelsHtml += '<span style="background:#ede9fe;color:#5b21b6;font-size:0.72rem;padding:2px 8px;border-radius:999px;">' + _esc(b.labels[l]) + '</span>';
    }
  }
  var assigneeHtml = b.assignee ? '<div style="display:flex;align-items:center;gap:6px;font-size:0.82rem;color:#6b7280;"><div style="width:22px;height:22px;border-radius:50%;background:#7c3aed;color:#fff;font-size:0.7rem;font-weight:700;display:flex;align-items:center;justify-content:center;">' + _esc(b.assignee.charAt(0).toUpperCase()) + '</div>' + _esc(b.assignee) + '</div>' : '';
  return '<div style="border:1px solid #e5e7eb;border-radius:12px;padding:18px;margin:0.75rem 0;background:#fff;box-shadow:0 1px 4px rgba(0,0,0,0.06);">'
    + '<div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">'
    + '<span style="font-size:1.2rem;background:' + bgColor + ';padding:6px;border-radius:8px;">' + icon + '</span>'
    + '<span style="font-size:0.82rem;font-weight:700;color:#6b7280;font-family:monospace;">' + _esc(b.key || '') + '</span>'
    + '<span style="margin-left:auto;background:' + statusBg + ';font-size:0.78rem;font-weight:600;padding:3px 10px;border-radius:999px;color:#374151;">' + _esc(status) + '</span>'
    + '</div>'
    + '<div style="font-size:1rem;font-weight:600;color:#111827;margin-bottom:10px;">' + _esc(b.summary || '') + '</div>'
    + (labelsHtml ? '<div style="display:flex;flex-wrap:wrap;gap:5px;margin-bottom:10px;">' + labelsHtml + '</div>' : '')
    + (assigneeHtml ? '<div style="margin-top:8px;">' + assigneeHtml + '</div>' : '')
    + '</div>';
};

_RENDERERS['feature_grid'] = function(b) {
  var features = b.features || [];
  var cols = b.cols || 3;
  var cardsHtml = '';
  for (var i = 0; i < features.length; i++) {
    var f = features[i];
    cardsHtml += '<div style="background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:20px;">'
      + (f.icon ? '<div style="font-size:2rem;margin-bottom:12px;">' + _esc(f.icon) + '</div>' : '')
      + (f.title ? '<div style="font-weight:700;font-size:1rem;color:#111827;margin-bottom:8px;">' + _esc(f.title) + '</div>' : '')
      + (f.description ? '<div style="font-size:0.875rem;color:#4b5563;line-height:1.6;">' + _esc(f.description) + '</div>' : '')
      + '</div>';
  }
  return '<div style="display:grid;grid-template-columns:repeat(' + cols + ',1fr);gap:14px;margin:1rem 0;">' + cardsHtml + '</div>';
};

_RENDERERS['navigation_menu'] = function(b) {
  var items = b.items || [];
  var itemsHtml = '';
  for (var i = 0; i < items.length; i++) {
    var item = items[i];
    var iconHtml = item.icon ? '<span style="margin-right:6px;">' + _esc(item.icon) + '</span>' : '';
    if (item.children && item.children.length) {
      var subItems = '';
      for (var j = 0; j < item.children.length; j++) {
        var child = item.children[j];
        subItems += '<li><a href="' + _esc(child.url || '#') + '" style="display:block;padding:8px 16px;font-size:0.875rem;color:#374151;text-decoration:none;white-space:nowrap;">' + _esc(child.label || '') + '</a></li>';
      }
      itemsHtml += '<li style="position:relative;">'
        + '<details style="display:inline;">'
        + '<summary style="display:flex;align-items:center;gap:4px;padding:8px 12px;font-size:0.9rem;font-weight:500;color:#111827;cursor:pointer;list-style:none;border-radius:6px;">' + iconHtml + _esc(item.label || '') + ' <span style="font-size:0.7rem;">▾</span></summary>'
        + '<ul style="position:absolute;top:100%;left:0;background:#fff;border:1px solid #e5e7eb;border-radius:10px;box-shadow:0 4px 16px rgba(0,0,0,0.1);list-style:none;margin:4px 0 0;padding:6px 0;min-width:180px;z-index:10;">' + subItems + '</ul>'
        + '</details>'
        + '</li>';
    } else {
      itemsHtml += '<li><a href="' + _esc(item.url || '#') + '" style="display:flex;align-items:center;padding:8px 12px;font-size:0.9rem;font-weight:500;color:#111827;text-decoration:none;border-radius:6px;">' + iconHtml + _esc(item.label || '') + '</a></li>';
    }
  }
  return '<nav style="margin:0.75rem 0;"><ul style="display:flex;list-style:none;margin:0;padding:8px;background:#f9fafb;border:1px solid #e5e7eb;border-radius:12px;gap:4px;flex-wrap:wrap;">' + itemsHtml + '</ul></nav>';
};

_RENDERERS['order_status_card'] = function(b) {
  var steps = ['Placed', 'Processing', 'Shipped', 'Delivered'];
  var statusIndex = {placed:0, processing:1, shipped:2, delivered:3, cancelled:-1};
  var currentStep = statusIndex[b.status] !== undefined ? statusIndex[b.status] : 0;
  var cancelled = b.status === 'cancelled';
  var stepperHtml = '<div style="display:flex;align-items:center;margin:16px 0 24px;">';
  for (var s = 0; s < steps.length; s++) {
    var done = !cancelled && s <= currentStep;
    var active = !cancelled && s === currentStep;
    var dotBg = cancelled ? '#fee2e2' : (done ? '#7c3aed' : '#e5e7eb');
    var dotColor = cancelled ? '#991b1b' : (done ? '#fff' : '#9ca3af');
    stepperHtml += '<div style="display:flex;flex-direction:column;align-items:center;flex:1;">'
      + '<div style="width:28px;height:28px;border-radius:50%;background:' + dotBg + ';color:' + dotColor + ';font-size:0.75rem;font-weight:700;display:flex;align-items:center;justify-content:center;">' + (done && !active ? '✓' : (s + 1)) + '</div>'
      + '<div style="font-size:0.72rem;margin-top:4px;color:' + (active ? '#7c3aed' : '#6b7280') + ';font-weight:' + (active ? '700' : '400') + ';text-align:center;">' + steps[s] + '</div>'
      + '</div>';
    if (s < steps.length - 1) {
      stepperHtml += '<div style="flex:1;height:2px;background:' + (!cancelled && s < currentStep ? '#7c3aed' : '#e5e7eb') + ';margin-bottom:16px;"></div>';
    }
  }
  stepperHtml += '</div>';
  var itemsHtml = '';
  var items = b.items || [];
  for (var i = 0; i < items.length; i++) {
    var item = items[i];
    itemsHtml += '<tr><td style="padding:8px 4px;font-size:0.875rem;color:#111827;">' + _esc(item.name || '') + '</td><td style="padding:8px 4px;font-size:0.875rem;color:#6b7280;text-align:center;">×' + (item.qty || 1) + '</td><td style="padding:8px 4px;font-size:0.875rem;color:#111827;text-align:right;">' + _esc(item.price || '') + '</td></tr>';
  }
  return '<div style="border:1px solid #e5e7eb;border-radius:14px;padding:20px;margin:1rem 0;background:#fff;">'
    + '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">'
    + '<span style="font-weight:700;color:#111827;font-size:1rem;">Order ' + _esc(b.order_id || '') + '</span>'
    + (cancelled ? '<span style="background:#fee2e2;color:#991b1b;font-size:0.78rem;font-weight:600;padding:3px 10px;border-radius:999px;">Cancelled</span>' : '')
    + '</div>'
    + stepperHtml
    + '<table style="width:100%;border-collapse:collapse;border-top:1px solid #f3f4f6;">' + itemsHtml + '</table>'
    + '<div style="display:flex;justify-content:space-between;padding-top:10px;border-top:1px solid #e5e7eb;margin-top:8px;font-weight:700;color:#111827;">'
    + '<span>Total</span><span>' + _esc(b.total || '') + '</span>'
    + '</div>'
    + (b.estimated_delivery ? '<div style="margin-top:10px;font-size:0.82rem;color:#6b7280;">Estimated delivery: <strong style="color:#111827;">' + _esc(b.estimated_delivery) + '</strong></div>' : '')
    + '</div>';
};

_RENDERERS['roadmap_card'] = function(b) {
  var statusColors = {
    'planned':     {bg:'#f3f4f6',fg:'#374151'},
    'in-progress': {bg:'#dbeafe',fg:'#1d4ed8'},
    'done':        {bg:'#dcfce7',fg:'#166534'},
    'deferred':    {bg:'#fef3c7',fg:'#92400e'}
  };
  var sc = statusColors[b.status] || statusColors['planned'];
  var itemsHtml = '';
  if (b.items && b.items.length) {
    for (var i = 0; i < b.items.length; i++) {
      itemsHtml += '<li style="font-size:0.875rem;color:#374151;padding:3px 0;">• ' + _esc(b.items[i]) + '</li>';
    }
  }
  return '<div style="border:1px solid #e5e7eb;border-radius:14px;padding:20px;margin:0.75rem 0;background:#fff;">'
    + '<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">'
    + (b.quarter ? '<span style="font-size:0.82rem;font-weight:700;color:#7c3aed;background:#f3f0ff;padding:3px 10px;border-radius:999px;">' + _esc(b.quarter) + '</span>' : '')
    + '<span style="background:' + sc.bg + ';color:' + sc.fg + ';font-size:0.78rem;font-weight:600;padding:3px 10px;border-radius:999px;">' + _esc(b.status || '') + '</span>'
    + '</div>'
    + (b.title ? '<div style="font-weight:700;font-size:1.05rem;color:#111827;margin-bottom:8px;">' + _esc(b.title) + '</div>' : '')
    + (b.description ? '<p style="font-size:0.875rem;color:#4b5563;margin:0 0 12px;line-height:1.5;">' + _esc(b.description) + '</p>' : '')
    + (itemsHtml ? '<ul style="list-style:none;margin:0;padding:0;">' + itemsHtml + '</ul>' : '')
    + '</div>';
};

_RENDERERS['notification_stack'] = function(b) {
  var notifications = b.notifications || [];
  var typeConfig = {
    info:    {bg:'#eff6ff',border:'#93c5fd',icon:'ℹ️',color:'#1d4ed8'},
    success: {bg:'#f0fdf4',border:'#86efac',icon:'✅',color:'#166534'},
    warning: {bg:'#fffbeb',border:'#fcd34d',icon:'⚠️',color:'#92400e'},
    error:   {bg:'#fef2f2',border:'#fca5a5',icon:'❌',color:'#991b1b'}
  };
  var html = '<div style="display:flex;flex-direction:column;gap:8px;margin:1rem 0;">';
  for (var i = 0; i < notifications.length; i++) {
    var n = notifications[i];
    var tc = typeConfig[n.type] || typeConfig['info'];
    html += '<div style="background:' + tc.bg + ';border:1px solid ' + tc.border + ';border-radius:10px;padding:14px 16px;display:flex;gap:12px;align-items:flex-start;">'
      + '<span style="font-size:1rem;flex-shrink:0;">' + tc.icon + '</span>'
      + '<div style="flex:1;">'
      + (n.title ? '<div style="font-weight:700;font-size:0.875rem;color:#111827;">' + _esc(n.title) + '</div>' : '')
      + (n.body ? '<div style="font-size:0.82rem;color:#374151;margin-top:2px;">' + _esc(n.body) + '</div>' : '')
      + '</div>'
      + (n.time ? '<span style="font-size:0.72rem;color:#9ca3af;flex-shrink:0;">' + _esc(n.time) + '</span>' : '')
      + '<button style="background:none;border:none;cursor:pointer;color:#9ca3af;font-size:1rem;padding:0;line-height:1;flex-shrink:0;" aria-label="Dismiss">×</button>'
      + '</div>';
  }
  html += '</div>';
  return html;
};

_RENDERERS['inline_alert'] = function(b) {
  var typeConfig = {
    info:    {bg:'#eff6ff',border:'#3b82f6',fg:'#1d4ed8',icon:'ℹ️'},
    success: {bg:'#f0fdf4',border:'#22c55e',fg:'#166534',icon:'✅'},
    warning: {bg:'#fffbeb',border:'#f59e0b',fg:'#92400e',icon:'⚠️'},
    error:   {bg:'#fef2f2',border:'#ef4444',fg:'#991b1b',icon:'❌'}
  };
  var tc = typeConfig[b.type] || typeConfig['info'];
  return '<div style="display:flex;align-items:flex-start;gap:10px;background:' + tc.bg + ';border-left:4px solid ' + tc.border + ';border-radius:0 8px 8px 0;padding:12px 16px;margin:0.75rem 0;">'
    + '<span style="font-size:0.95rem;flex-shrink:0;">' + tc.icon + '</span>'
    + '<div style="flex:1;font-size:0.875rem;color:' + tc.fg + ';">' + _esc(b.message || '') + '</div>'
    + (b.dismissible ? '<button style="background:none;border:none;cursor:pointer;color:#9ca3af;font-size:1rem;padding:0;line-height:1;" aria-label="Dismiss">×</button>' : '')
    + '</div>';
};

_RENDERERS['source_citation'] = function(b) {
  var authorsHtml = '';
  if (b.authors && b.authors.length) {
    var escapedAuthors = [];
    for (var i = 0; i < b.authors.length; i++) {
      escapedAuthors.push(_esc(b.authors[i]));
    }
    authorsHtml = '<span style="font-size:0.82rem;color:#374151;">' + escapedAuthors.join(', ') + '</span>';
    if (b.year) { authorsHtml += '<span style="font-size:0.82rem;color:#6b7280;"> (' + _esc(b.year) + ')</span>'; }
  }
  var titleHtml = b.url
    ? '<a href="' + _esc(b.url) + '" style="font-weight:600;color:#1d4ed8;text-decoration:none;font-size:0.9rem;">' + _esc(b.title || '') + '</a>'
    : '<span style="font-weight:600;color:#111827;font-size:0.9rem;">' + _esc(b.title || '') + '</span>';
  return '<div style="border:1px solid #e5e7eb;border-radius:10px;padding:14px 16px;margin:0.75rem 0;background:#fafafa;display:flex;gap:12px;">'
    + '<div style="width:28px;height:28px;border-radius:50%;background:#7c3aed;color:#fff;font-size:0.78rem;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0;">①</div>'
    + '<div>'
    + titleHtml
    + (authorsHtml ? '<div style="margin-top:3px;">' + authorsHtml + '</div>' : '')
    + (b.publisher ? '<div style="font-size:0.8rem;color:#6b7280;margin-top:2px;font-style:italic;">' + _esc(b.publisher) + '</div>' : '')
    + (b.note ? '<div style="font-size:0.8rem;color:#4b5563;margin-top:5px;background:#f3f4f6;padding:5px 8px;border-radius:6px;">' + _esc(b.note) + '</div>' : '')
    + '</div>'
    + '</div>';
};

_RENDERERS['llm_comparison_table'] = function(b) {
  var models = b.models || [];
  var title = b.title || 'Model Comparison';
  var rows = '';
  for (var i = 0; i < models.length; i++) {
    var m = models[i];
    var strengths = m.strengths ? m.strengths.join(', ') : '';
    var weaknesses = m.weaknesses ? m.weaknesses.join(', ') : '';
    var rowBg = i % 2 === 0 ? '#fff' : '#f9fafb';
    rows += '<tr style="background:' + rowBg + ';">'
      + '<td style="padding:10px 12px;font-weight:600;color:#111827;font-size:0.875rem;">' + _esc(m.name || '') + '</td>'
      + '<td style="padding:10px 12px;font-size:0.82rem;color:#374151;">' + _esc(m.params || '—') + '</td>'
      + '<td style="padding:10px 12px;font-size:0.82rem;color:#374151;">' + _esc(m.context_window ? String(m.context_window) : '—') + '</td>'
      + '<td style="padding:10px 12px;font-size:0.82rem;color:#374151;">' + _esc(m.price_per_1m_tokens ? String(m.price_per_1m_tokens) : '—') + '</td>'
      + '<td style="padding:10px 12px;font-size:0.78rem;color:#166534;">' + _esc(strengths) + '</td>'
      + '<td style="padding:10px 12px;font-size:0.78rem;color:#991b1b;">' + _esc(weaknesses) + '</td>'
      + '</tr>';
  }
  return '<div style="margin:1rem 0;overflow-x:auto;">'
    + (title ? '<div style="font-weight:700;font-size:1rem;color:#111827;margin-bottom:10px;">' + _esc(title) + '</div>' : '')
    + '<table style="width:100%;border-collapse:collapse;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;font-size:0.875rem;">'
    + '<thead><tr style="background:#f3f4f6;"><th style="padding:10px 12px;text-align:left;font-size:0.78rem;font-weight:700;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;">Model</th><th style="padding:10px 12px;text-align:left;font-size:0.78rem;font-weight:700;color:#6b7280;text-transform:uppercase;">Params</th><th style="padding:10px 12px;text-align:left;font-size:0.78rem;font-weight:700;color:#6b7280;text-transform:uppercase;">Context</th><th style="padding:10px 12px;text-align:left;font-size:0.78rem;font-weight:700;color:#6b7280;text-transform:uppercase;">$/1M tokens</th><th style="padding:10px 12px;text-align:left;font-size:0.78rem;font-weight:700;color:#6b7280;text-transform:uppercase;">Strengths</th><th style="padding:10px 12px;text-align:left;font-size:0.78rem;font-weight:700;color:#6b7280;text-transform:uppercase;">Weaknesses</th></tr></thead>'
    + '<tbody>' + rows + '</tbody>'
    + '</table></div>';
};

_RENDERERS['confidence_bar'] = function(b) {
  var value = Math.min(Math.max(parseFloat(b.value) || 0, 0), 1);
  var pct = Math.round(value * 100);
  var color = b.color || '#7c3aed';
  var uid = Math.random().toString(36).substr(2, 6);
  return '<div style="margin:0.75rem 0;">'
    + '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">'
    + '<span style="font-size:0.875rem;font-weight:500;color:#374151;">' + _esc(b.label || '') + '</span>'
    + '<span style="font-size:0.875rem;font-weight:700;color:' + color + ';">' + pct + '%</span>'
    + '</div>'
    + '<div style="background:#f3f4f6;border-radius:999px;height:8px;overflow:hidden;">'
    + '<div style="width:' + pct + '%;height:100%;background:' + color + ';border-radius:999px;transition:width 0.6s ease;"></div>'
    + '</div>'
    + '</div>';
};

_RENDERERS['token_budget_meter'] = function(b) {
  var used = parseInt(b.used) || 0;
  var total = parseInt(b.total) || 1;
  var unit = b.unit || 'tokens';
  var pct = Math.min(Math.round((used / total) * 100), 100);
  var color = pct < 70 ? '#22c55e' : (pct < 90 ? '#f59e0b' : '#ef4444');
  var label = pct < 70 ? 'On track' : (pct < 90 ? 'Nearing limit' : 'Critical');
  return '<div style="margin:0.75rem 0;">'
    + '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">'
    + '<span style="font-size:0.875rem;font-weight:600;color:#374151;">Token Budget</span>'
    + '<span style="font-size:0.82rem;color:#6b7280;">' + used.toLocaleString() + ' / ' + total.toLocaleString() + ' ' + _esc(unit) + '</span>'
    + '</div>'
    + '<div style="background:#f3f4f6;border-radius:999px;height:10px;overflow:hidden;">'
    + '<div style="width:' + pct + '%;height:100%;background:' + color + ';border-radius:999px;transition:width 0.6s ease;"></div>'
    + '</div>'
    + '<div style="display:flex;justify-content:space-between;margin-top:5px;">'
    + '<span style="font-size:0.72rem;color:' + color + ';font-weight:600;">' + label + '</span>'
    + '<span style="font-size:0.72rem;color:#6b7280;">' + pct + '% used</span>'
    + '</div>'
    + '</div>';
};

_RENDERERS['text_callout'] = function(b) {
  var text = b.text || '';
  var style = b.style || 'highlight';
  if (style === 'quote') {
    return '<blockquote style="border-left:4px solid #7c3aed;padding:12px 16px;margin:1rem 0;color:#4b5563;font-style:italic;background:#fafafa;border-radius:0 8px 8px 0;">' + _esc(text) + '</blockquote>';
  } else if (style === 'bold') {
    return '<div style="font-weight:700;color:#7c3aed;font-size:1.05rem;margin:0.75rem 0;">' + _esc(text) + '</div>';
  } else {
    return '<mark style="background:#fef9c3;color:#111827;padding:2px 6px;border-radius:4px;">' + _esc(text) + '</mark>';
  }
};

_RENDERERS['tag_block'] = function(b) {
  var tags = b.tags || [];
  var pillsHtml = '';
  for (var i = 0; i < tags.length; i++) {
    var tag = tags[i];
    var text, color, url;
    if (typeof tag === 'string') {
      text = tag; color = null; url = null;
    } else {
      text = tag.text || ''; color = tag.color || null; url = tag.url || null;
    }
    var bg = color || '#f3f4f6';
    var fg = color ? '#fff' : '#374151';
    var pill = '<span style="display:inline-flex;align-items:center;background:' + _esc(bg) + ';color:' + fg + ';font-size:0.78rem;font-weight:500;padding:4px 12px;border-radius:999px;white-space:nowrap;">' + _esc(text) + '</span>';
    if (url) {
      pillsHtml += '<a href="' + _esc(url) + '" style="text-decoration:none;">' + pill + '</a>';
    } else {
      pillsHtml += pill;
    }
  }
  return '<div style="display:flex;flex-wrap:wrap;gap:6px;margin:0.5rem 0;">' + pillsHtml + '</div>';
};

_RENDERERS['variant_selector'] = function(b) {
  var label = b.label || '';
  var variants = b.variants || [];
  var uid = Math.random().toString(36).substr(2, 6);
  var variantsHtml = '';
  for (var i = 0; i < variants.length; i++) {
    var v = variants[i];
    var id = 'variant-' + uid + '-' + i;
    if (v.color) {
      variantsHtml += '<label for="' + id + '" title="' + _esc(v.label || v.value || '') + '" style="cursor:pointer;">'
        + '<input type="radio" name="variant-' + uid + '" id="' + id + '" value="' + _esc(v.value || '') + '" style="display:none;"' + (v.disabled ? ' disabled' : '') + '>'
        + '<span style="display:inline-block;width:28px;height:28px;border-radius:50%;background:' + _esc(v.color) + ';border:2px solid #fff;box-shadow:0 0 0 2px #d1d5db;' + (v.disabled ? 'opacity:0.4;' : '') + '"></span>'
        + '</label>';
    } else {
      variantsHtml += '<label for="' + id + '" style="cursor:pointer;">'
        + '<input type="radio" name="variant-' + uid + '" id="' + id + '" value="' + _esc(v.value || '') + '" style="display:none;"' + (v.disabled ? ' disabled' : '') + '>'
        + '<span style="display:inline-block;padding:6px 14px;border:1.5px solid #e5e7eb;border-radius:8px;font-size:0.82rem;font-weight:500;color:#374151;' + (v.disabled ? 'opacity:0.4;' : '') + '">' + _esc(v.label || v.value || '') + '</span>'
        + '</label>';
    }
  }
  return '<div style="margin:0.75rem 0;">'
    + (label ? '<div style="font-size:0.875rem;font-weight:600;color:#111827;margin-bottom:10px;">' + _esc(label) + '</div>' : '')
    + '<div style="display:flex;flex-wrap:wrap;gap:8px;">' + variantsHtml + '</div>'
    + '</div>';
};

_RENDERERS['shortcut_legend'] = function(b) {
  var shortcuts = b.shortcuts || [];
  var rows = '';
  for (var i = 0; i < shortcuts.length; i++) {
    var sc = shortcuts[i];
    var keys = sc.keys || [];
    var keysHtml = '';
    for (var k = 0; k < keys.length; k++) {
      if (k > 0) { keysHtml += '<span style="color:#9ca3af;font-size:0.8rem;margin:0 3px;">+</span>'; }
      keysHtml += '<kbd style="display:inline-block;background:#fff;border:1px solid #d1d5db;border-bottom:2px solid #9ca3af;border-radius:5px;padding:2px 7px;font-size:0.78rem;font-family:monospace;color:#111827;box-shadow:0 1px 0 rgba(0,0,0,0.1);">' + _esc(keys[k]) + '</kbd>';
    }
    rows += '<tr style="' + (i % 2 === 0 ? '' : 'background:#f9fafb;') + '">'
      + '<td style="padding:9px 12px;">' + keysHtml + '</td>'
      + '<td style="padding:9px 12px;font-size:0.875rem;color:#374151;">' + _esc(sc.description || '') + '</td>'
      + '</tr>';
  }
  return '<div style="margin:1rem 0;overflow-x:auto;">'
    + '<table style="width:100%;border-collapse:collapse;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;">'
    + '<thead><tr style="background:#f3f4f6;"><th style="padding:9px 12px;text-align:left;font-size:0.78rem;font-weight:700;color:#6b7280;text-transform:uppercase;">Shortcut</th><th style="padding:9px 12px;text-align:left;font-size:0.78rem;font-weight:700;color:#6b7280;text-transform:uppercase;">Description</th></tr></thead>'
    + '<tbody>' + rows + '</tbody>'
    + '</table></div>';
};

_RENDERERS['rating_summary_bar'] = function(b) {
  var overall = parseFloat(b.overall) || 0;
  var totalReviews = b.total_reviews || 0;
  var dist = b.distribution || {};
  var starsHtml = '';
  var fullStars = Math.floor(overall);
  var halfStar = (overall - fullStars) >= 0.5;
  for (var s = 1; s <= 5; s++) {
    if (s <= fullStars) { starsHtml += '★'; }
    else if (s === fullStars + 1 && halfStar) { starsHtml += '½'; }
    else { starsHtml += '☆'; }
  }
  var barsHtml = '';
  for (var r = 5; r >= 1; r--) {
    var count = dist[String(r)] || 0;
    var pct = totalReviews > 0 ? Math.round((count / totalReviews) * 100) : 0;
    barsHtml += '<div style="display:flex;align-items:center;gap:8px;margin-bottom:5px;">'
      + '<span style="font-size:0.78rem;color:#6b7280;width:10px;">' + r + '</span>'
      + '<span style="color:#f59e0b;font-size:0.78rem;">★</span>'
      + '<div style="flex:1;background:#f3f4f6;border-radius:999px;height:8px;overflow:hidden;">'
      + '<div style="width:' + pct + '%;height:100%;background:#f59e0b;border-radius:999px;"></div>'
      + '</div>'
      + '<span style="font-size:0.72rem;color:#6b7280;width:28px;text-align:right;">' + count + '</span>'
      + '</div>';
  }
  return '<div style="display:flex;gap:24px;align-items:flex-start;border:1px solid #e5e7eb;border-radius:14px;padding:20px;margin:1rem 0;background:#fff;">'
    + '<div style="text-align:center;min-width:80px;">'
    + '<div style="font-size:2.5rem;font-weight:800;color:#111827;line-height:1;">' + overall.toFixed(1) + '</div>'
    + '<div style="color:#f59e0b;font-size:1.1rem;letter-spacing:2px;">' + starsHtml + '</div>'
    + '<div style="font-size:0.78rem;color:#6b7280;margin-top:4px;">' + totalReviews.toLocaleString() + ' reviews</div>'
    + '</div>'
    + '<div style="flex:1;">' + barsHtml + '</div>'
    + '</div>';
};

_RENDERERS['model_card'] = function(b) {
  var metricsHtml = '';
  if (b.metrics && b.metrics.length) {
    for (var i = 0; i < b.metrics.length; i++) {
      var m = b.metrics[i];
      metricsHtml += '<div style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;padding:10px;text-align:center;">'
        + '<div style="font-size:1.1rem;font-weight:700;color:#7c3aed;">' + _esc(m.value || '') + '</div>'
        + '<div style="font-size:0.72rem;color:#6b7280;margin-top:2px;">' + _esc(m.label || '') + '</div>'
        + '</div>';
    }
  }
  var tagsHtml = '';
  if (b.tags && b.tags.length) {
    for (var t = 0; t < b.tags.length; t++) {
      tagsHtml += '<span style="background:#ede9fe;color:#5b21b6;font-size:0.72rem;padding:2px 8px;border-radius:999px;">' + _esc(b.tags[t]) + '</span>';
    }
  }
  return '<div style="border:1px solid #e5e7eb;border-radius:14px;padding:20px;margin:1rem 0;background:#fff;">'
    + '<div style="display:flex;align-items:flex-start;gap:12px;margin-bottom:14px;">'
    + '<div style="flex:1;">'
    + (b.name ? '<div style="font-weight:800;font-size:1.1rem;color:#111827;">' + _esc(b.name) + (b.version ? ' <span style="font-size:0.78rem;color:#6b7280;font-weight:400;">v' + _esc(b.version) + '</span>' : '') + '</div>' : '')
    + (b.type ? '<div style="font-size:0.8rem;color:#7c3aed;font-weight:600;margin-top:2px;">' + _esc(b.type) + '</div>' : '')
    + '</div>'
    + (b.license ? '<span style="background:#f3f4f6;color:#374151;font-size:0.72rem;padding:3px 8px;border-radius:6px;">' + _esc(b.license) + '</span>' : '')
    + '</div>'
    + (b.description ? '<p style="font-size:0.875rem;color:#4b5563;margin:0 0 14px;line-height:1.6;">' + _esc(b.description) + '</p>' : '')
    + (metricsHtml ? '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(100px,1fr));gap:8px;margin-bottom:14px;">' + metricsHtml + '</div>' : '')
    + (tagsHtml ? '<div style="display:flex;flex-wrap:wrap;gap:5px;margin-bottom:12px;">' + tagsHtml + '</div>' : '')
    + (b.link ? '<a href="' + _esc(b.link) + '" style="font-size:0.82rem;color:#7c3aed;text-decoration:none;font-weight:600;">View model →</a>' : '')
    + '</div>';
};

_RENDERERS['conversation_snippet'] = function(b) {
  var messages = b.messages || [];
  var html = '<div style="display:flex;flex-direction:column;gap:10px;margin:1rem 0;">';
  for (var i = 0; i < messages.length; i++) {
    var msg = messages[i];
    var role = msg.role || 'user';
    if (role === 'system') {
      html += '<div style="background:#f3f4f6;border-radius:8px;padding:8px 14px;font-size:0.8rem;color:#6b7280;font-style:italic;text-align:center;">' + _esc(msg.content || '') + '</div>';
    } else if (role === 'user') {
      html += '<div style="display:flex;justify-content:flex-end;">'
        + '<div style="background:#ede9fe;color:#111827;border-radius:16px 16px 4px 16px;padding:10px 14px;max-width:75%;font-size:0.875rem;">' + _esc(msg.content || '') + '</div>'
        + '</div>';
    } else {
      html += '<div style="display:flex;justify-content:flex-start;">'
        + '<div style="background:#fff;border:1px solid #e5e7eb;color:#111827;border-radius:16px 16px 16px 4px;padding:10px 14px;max-width:75%;font-size:0.875rem;">' + _esc(msg.content || '') + '</div>'
        + '</div>';
    }
  }
  html += '</div>';
  return html;
};

_RENDERERS['prompt_template'] = function(b) {
  var template = b.template || '';
  var variables = b.variables || [];
  var highlighted = _esc(template).replace(/\{\{([^}]+)\}\}/g, '<mark style="background:#fef9c3;color:#92400e;border-radius:3px;padding:1px 4px;">{{$1}}</mark>');
  var varsHtml = '';
  for (var i = 0; i < variables.length; i++) {
    var v = variables[i];
    varsHtml += '<tr style="' + (i % 2 === 0 ? '' : 'background:#f9fafb;') + '">'
      + '<td style="padding:8px 10px;font-family:monospace;font-size:0.82rem;color:#7c3aed;white-space:nowrap;">{{' + _esc(v.name || '') + '}}</td>'
      + '<td style="padding:8px 10px;font-size:0.82rem;color:#374151;">' + _esc(v.description || '') + '</td>'
      + '<td style="padding:8px 10px;font-size:0.78rem;color:#6b7280;font-style:italic;">' + _esc(v.example || '') + '</td>'
      + '</tr>';
  }
  return '<div style="border:1px solid #e5e7eb;border-radius:14px;overflow:hidden;margin:1rem 0;">'
    + '<div style="background:#f9fafb;border-bottom:1px solid #e5e7eb;padding:12px 16px;display:flex;justify-content:space-between;align-items:center;">'
    + '<span style="font-weight:700;font-size:0.9rem;color:#111827;">' + _esc(b.title || 'Prompt Template') + '</span>'
    + (b.use_case ? '<span style="font-size:0.78rem;color:#6b7280;">' + _esc(b.use_case) + '</span>' : '')
    + '</div>'
    + '<pre style="margin:0;padding:16px;background:#1e1e2e;color:#cdd6f4;font-size:0.82rem;line-height:1.6;white-space:pre-wrap;overflow-x:auto;"><code>' + highlighted + '</code></pre>'
    + (varsHtml ? '<div style="padding:14px 16px;border-top:1px solid #e5e7eb;"><div style="font-size:0.8rem;font-weight:700;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px;">Variables</div><table style="width:100%;border-collapse:collapse;font-size:0.82rem;"><thead><tr style="background:#f3f4f6;"><th style="padding:7px 10px;text-align:left;font-size:0.75rem;color:#6b7280;">Variable</th><th style="padding:7px 10px;text-align:left;font-size:0.75rem;color:#6b7280;">Description</th><th style="padding:7px 10px;text-align:left;font-size:0.75rem;color:#6b7280;">Example</th></tr></thead><tbody>' + varsHtml + '</tbody></table></div>' : '')
    + '</div>';
};

// === Animation degraded fallbacks ===

function _animFallback(atomName, label) {
  return '<div style="border:1px dashed #d1d5db;border-radius:10px;padding:16px;margin:1rem 0;background:#fafafa;text-align:center;color:#9ca3af;font-size:0.82rem;">⚡ [' + atomName + ' — not available in this surface]' + (label ? '<br><strong style=\'color:#374151;\'>' + _esc(label) + '</strong>' : '') + '</div>';
}

_RENDERERS['animated_beam'] = function(b) {
  return _animFallback('animated beam', b.title || b.label || b.text || '');
};

_RENDERERS['animated_border_card'] = function(b) {
  return _animFallback('animated border card', b.title || b.label || b.text || '');
};

_RENDERERS['aurora_background'] = function(b) {
  return _animFallback('aurora background', b.title || b.label || b.text || '');
};

_RENDERERS['blur_fade_in'] = function(b) {
  return _animFallback('blur fade-in', b.title || b.label || b.text || '');
};

_RENDERERS['card_stack'] = function(b) {
  return _animFallback('card stack', b.title || b.label || b.text || '');
};

_RENDERERS['countdown_timer'] = function(b) {
  var label = b.title || b.label || b.text || '';
  var extra = b.target_date ? '<br><span style="font-size:0.78rem;color:#6b7280;">Target: ' + _esc(b.target_date) + '</span>' : '';
  return '<div style="border:1px dashed #d1d5db;border-radius:10px;padding:16px;margin:1rem 0;background:#fafafa;text-align:center;color:#9ca3af;font-size:0.82rem;">⚡ [countdown timer — not available in this surface]' + (label ? '<br><strong style=\'color:#374151;\'>' + _esc(label) + '</strong>' : '') + extra + '</div>';
};

_RENDERERS['dot_grid_background'] = function(b) {
  return _animFallback('dot grid background', b.title || b.label || b.text || '');
};

_RENDERERS['effect_overlay'] = function(b) {
  return _animFallback('effect overlay', b.title || b.label || b.text || '');
};

_RENDERERS['encrypted_reveal'] = function(b) {
  return _animFallback('encrypted reveal', b.title || b.label || b.text || '');
};

_RENDERERS['glow_button'] = function(b) {
  var label = b.text || b.label || b.title || 'Action';
  return '<div style="margin:1rem 0;text-align:center;">'
    + '<button style="background:#7c3aed;color:#fff;font-weight:700;font-size:0.95rem;padding:12px 28px;border:none;border-radius:10px;cursor:pointer;box-shadow:0 0 16px rgba(124,58,237,0.5),0 0 32px rgba(124,58,237,0.25);letter-spacing:0.02em;">' + _esc(label) + '</button>'
    + '</div>';
};

_RENDERERS['gradient_text'] = function(b) {
  var text = b.text || b.label || b.title || '';
  return '<span style="background:linear-gradient(135deg,#6366f1,#a855f7,#ec4899);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;font-weight:700;font-size:1.5rem;">' + _esc(text) + '</span>';
};

_RENDERERS['meteor_shower'] = function(b) {
  return _animFallback('meteor shower', b.title || b.label || b.text || '');
};

_RENDERERS['number_odometer'] = function(b) {
  return _animFallback('number odometer', b.title || b.label || b.text || '');
};

_RENDERERS['reveal_on_scroll'] = function(b) {
  return _animFallback('reveal on scroll', b.title || b.label || b.text || '');
};

_RENDERERS['shimmer_button'] = function(b) {
  var label = b.text || b.label || b.title || 'Action';
  var uid = Math.random().toString(36).substr(2, 6);
  return '<div style="margin:1rem 0;text-align:center;">'
    + '<style>.shimmer-btn-' + uid + '{position:relative;overflow:hidden;background:#7c3aed;color:#fff;font-weight:700;font-size:0.95rem;padding:12px 28px;border:none;border-radius:10px;cursor:pointer;}.shimmer-btn-' + uid + '::after{content:\'\';position:absolute;top:0;left:-100%;width:60%;height:100%;background:linear-gradient(90deg,transparent,rgba(255,255,255,0.25),transparent);animation:shimmer-' + uid + ' 1.8s infinite;transform:skewX(-20deg);}@keyframes shimmer-' + uid + '{0%{left:-100%;}100%{left:160%;}}</style>'
    + '<button class="shimmer-btn-' + uid + '">' + _esc(label) + '</button>'
    + '</div>';
};

_RENDERERS['skeleton_stage_card'] = function(b) {
  return _animFallback('skeleton stage card', b.title || b.label || b.text || '');
};

_RENDERERS['sonar_pulse'] = function(b) {
  return _animFallback('sonar pulse', b.title || b.label || b.text || '');
};

_RENDERERS['svg_path_draw'] = function(b) {
  return _animFallback('SVG path draw', b.title || b.label || b.text || '');
};

_RENDERERS['typewriter'] = function(b) {
  var text = b.text || b.content || b.label || '';
  return '<div style="border:1px solid #e5e7eb;border-radius:10px;padding:16px;margin:1rem 0;background:#1e1e2e;">'
    + '<pre style="margin:0;font-family:\'Courier New\',Courier,monospace;font-size:0.875rem;color:#cdd6f4;white-space:pre-wrap;line-height:1.6;">' + _esc(text) + '<span style="display:inline-block;width:2px;height:1em;background:#a855f7;vertical-align:text-bottom;animation:blink 1s step-end infinite;margin-left:2px;"></span></pre>'
    + '<style>@keyframes blink{0%,100%{opacity:1;}50%{opacity:0;}}</style>'
    + '</div>';
};

_RENDERERS['typewriter_text'] = function(b) {
  var text = b.text || b.content || b.label || '';
  return '<div style="border:1px solid #e5e7eb;border-radius:10px;padding:16px;margin:1rem 0;background:#1e1e2e;">'
    + '<pre style="margin:0;font-family:\'Courier New\',Courier,monospace;font-size:0.875rem;color:#cdd6f4;white-space:pre-wrap;line-height:1.6;">' + _esc(text) + '<span style="display:inline-block;width:2px;height:1em;background:#a855f7;vertical-align:text-bottom;animation:blink 1s step-end infinite;margin-left:2px;"></span></pre>'
    + '<style>@keyframes blink{0%,100%{opacity:1;}50%{opacity:0;}}</style>'
    + '</div>';
};

_RENDERERS['typing_indicator'] = function(b) {
  return _animFallback('typing indicator', b.title || b.label || b.text || '');
};

_RENDERERS['word_flip'] = function(b) {
  return _animFallback('word flip', b.title || b.label || b.text || '');
};

_RENDERERS['word_scramble'] = function(b) {
  return _animFallback('word scramble', b.title || b.label || b.text || '');
};

_RENDERERS['animated_counter'] = function(b) {
  var value = b.value !== undefined ? b.value : (b.end !== undefined ? b.end : '');
  var label = b.label || b.title || '';
  return '<div style="border:1px dashed #d1d5db;border-radius:10px;padding:16px;margin:1rem 0;background:#fafafa;text-align:center;color:#9ca3af;font-size:0.82rem;">⚡ [animated counter — not available in this surface]<br><strong style="color:#7c3aed;font-size:1.5rem;">' + _esc(String(value)) + '</strong>' + (label ? '<br><span style="color:#374151;">' + _esc(label) + '</span>' : '') + '</div>';
};

_RENDERERS['parallax_section'] = function(b) {
  return _animFallback('parallax section', b.title || b.label || b.text || '');
};

_RENDERERS['scroll_trigger'] = function(b) {
  return _animFallback('scroll trigger', b.title || b.label || b.text || '');
};

_RENDERERS['floating_particles'] = function(b) {
  return _animFallback('floating particles', b.title || b.label || b.text || '');
};

_RENDERERS['confetti_burst'] = function(b) {
  return _animFallback('confetti burst', b.title || b.label || b.text || '');
};

_RENDERERS['glitch_text'] = function(b) {
  return _animFallback('glitch text', b.title || b.label || b.text || '');
};

_RENDERERS['neon_glow'] = function(b) {
  return _animFallback('neon glow', b.title || b.label || b.text || '');
};

_RENDERERS['tilt_card'] = function(b) {
  return _animFallback('tilt card', b.title || b.label || b.text || '');
};

_RENDERERS['magnetic_button'] = function(b) {
  return _animFallback('magnetic button', b.title || b.label || b.text || '');
};

_RENDERERS['linkedin_post_image'] = function(b) {
  var mode   = b.mode || 'conviction_card';
  var accent = b.accent || '#7c3aed';
  var uid    = 'li' + Math.random().toString(36).slice(2, 8);

  // Hint bar shown below every card
  var hint = '<div style="margin-top:8px;text-align:center;font-size:0.72rem;color:#9aa0a6;">' +
    'LinkedIn post image &mdash; screenshot at 1.91:1 ratio</div>';

  // ── conviction_card ─────────────────────────────────────────────────────────
  if (mode === 'conviction_card') {
    var quote = b.quote || '';
    var attr  = b.attribution || '';
    var attrHtml = attr
      ? '<div style="margin-top:20px;font-size:0.82rem;letter-spacing:0.06em;' +
        'font-family:monospace;color:' + _esc(accent) + ';">' + _esc(attr) + '</div>'
      : '';
    return '<div id="' + uid + '" style="aspect-ratio:1.91/1;background:#0f172a;border-radius:12px;' +
      'display:flex;align-items:center;justify-content:center;padding:48px;' +
      'position:relative;overflow:hidden;margin:1.5rem 0;">' +
      '<div style="position:absolute;bottom:0;left:0;right:0;height:4px;' +
      'background:linear-gradient(90deg,' + _esc(accent) + ',#3b82f6);"></div>' +
      '<div style="text-align:center;max-width:80%;">' +
      '<div style="font-size:clamp(1rem,3vw,1.7rem);color:#f1f5f9;font-weight:700;' +
      'line-height:1.45;font-style:italic;">“' + _esc(quote) + '”</div>' +
      attrHtml + '</div></div>' + hint;
  }

  // ── split_screenshot ────────────────────────────────────────────────────────
  if (mode === 'split_screenshot') {
    var left    = b.left  || {};
    var right   = b.right || {};
    var caption = b.caption || '';
    function _panel(side, borderRight) {
      var label = side.label || '';
      var url   = side.url   || '';
      var br    = borderRight ? 'border-right:1px solid #e0e0e0;' : '';
      var lbl   = label
        ? '<div style="padding:7px 12px;font-size:0.68rem;font-weight:700;' +
          'color:#5f6368;background:#f1f3f4;border-bottom:1px solid #e0e0e0;' +
          'letter-spacing:0.05em;text-transform:uppercase;">' + _esc(label) + '</div>'
        : '';
      var img = url
        ? '<img src="' + _esc(url) + '" style="width:100%;height:100%;object-fit:cover;' +
          'object-position:top;display:block;"/>'
        : '<div style="flex:1;display:flex;align-items:center;justify-content:center;' +
          'background:#f8f9fa;color:#9aa0a6;font-size:0.8rem;">screenshot</div>';
      return '<div style="flex:1;display:flex;flex-direction:column;' + br + 'overflow:hidden;">' +
        lbl + img + '</div>';
    }
    var cap = caption
      ? '<div style="padding:10px 16px;font-size:0.78rem;color:#5f6368;text-align:center;' +
        'border-top:1px solid #e0e0e0;background:#f8f9fa;">' + _esc(caption) + '</div>'
      : '';
    return '<div style="aspect-ratio:1.91/1;border:1px solid #e0e0e0;border-radius:12px;' +
      'overflow:hidden;display:flex;flex-direction:column;margin:1.5rem 0;' +
      'box-shadow:0 2px 8px rgba(0,0,0,0.08);">' +
      '<div style="flex:1;display:flex;overflow:hidden;">' +
      _panel(left, true) + _panel(right, false) + '</div>' + cap + '</div>' + hint;
  }

  // ── architecture_diagram ────────────────────────────────────────────────────
  if (mode === 'architecture_diagram') {
    var inputs  = b.inputs  || [];
    var runtime = b.runtime || 'Runtime';
    var outputs = b.outputs || [];
    var caption = b.caption || '';
    function _boxes(items, fill, border, color) {
      return '<div style="display:flex;gap:10px;justify-content:center;flex-wrap:wrap;">' +
        items.map(function(i) {
          return '<div style="background:' + fill + ';border:1.5px solid ' + border + ';' +
            'border-radius:8px;padding:9px 16px;font-size:0.78rem;font-weight:600;' +
            'color:' + color + ';text-align:center;white-space:nowrap;">' + _esc(i.label || '') + '</div>';
        }).join('') + '</div>';
    }
    var arrow = '<div style="text-align:center;color:#9aa0a6;font-size:1.1rem;margin:6px 0;">↓</div>';
    var runtimeBox = '<div style="background:#1e40af;border:2px solid #3b82f6;border-radius:10px;' +
      'padding:12px 24px;font-size:0.88rem;font-weight:700;color:#fff;' +
      'text-align:center;margin:0 auto;max-width:340px;">' + _esc(runtime) + '</div>';
    var capHtml = caption
      ? '<div style="font-size:0.75rem;color:#5f6368;text-align:center;margin-top:14px;' +
        'font-style:italic;">' + _esc(caption) + '</div>'
      : '';
    return '<div style="aspect-ratio:1.91/1;background:#f8f9fa;border:1px solid #e0e0e0;' +
      'border-radius:12px;display:flex;flex-direction:column;align-items:center;' +
      'justify-content:center;padding:32px;margin:1.5rem 0;">' +
      _boxes(inputs, '#e8f0fe', '#4285f4', '#1967d2') +
      arrow + runtimeBox + arrow +
      _boxes(outputs, '#e6f4ea', '#34a853', '#1e7e34') +
      capHtml + '</div>' + hint;
  }

  // ── pipeline ────────────────────────────────────────────────────────────────
  if (mode === 'pipeline') {
    var steps   = b.steps   || [];
    var arrows  = b.arrows  || [];
    var caption = b.caption || '';
    var parts = [];
    steps.forEach(function(step, i) {
      var sublabel = step.sublabel ? '<div style="font-size:0.65rem;font-weight:400;color:' + _esc(accent) + ';margin-top:4px;letter-spacing:0.03em;">' + _esc(step.sublabel) + '</div>' : '';
      parts.push(
        '<div style="flex:1;min-width:0;background:#fff;border:2px solid ' + _esc(accent) + ';border-radius:10px;' +
        'padding:14px 12px;text-align:center;">' +
        '<div style="font-size:0.82rem;font-weight:700;color:#0f172a;line-height:1.3;">' + _esc(step.label || '') + '</div>' +
        sublabel + '</div>'
      );
      if (i < steps.length - 1) {
        var arrowLabel = arrows[i] ? '<div style="font-size:0.6rem;color:#9aa0a6;margin-top:3px;white-space:nowrap;">' + _esc(arrows[i]) + '</div>' : '';
        parts.push(
          '<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;' +
          'padding:0 4px;flex-shrink:0;">' +
          '<div style="font-size:1.4rem;color:' + _esc(accent) + ';line-height:1;">→</div>' +
          arrowLabel + '</div>'
        );
      }
    });
    var capHtml = caption
      ? '<div style="font-size:0.75rem;color:#5f6368;text-align:center;margin-top:16px;font-style:italic;">' + _esc(caption) + '</div>'
      : '';
    return (
      '<div style="aspect-ratio:1.91/1;background:#f8f9fa;border:1px solid #e0e0e0;border-radius:12px;' +
      'display:flex;flex-direction:column;align-items:center;justify-content:center;padding:40px 32px;margin:1.5rem 0;">' +
      '<div style="display:flex;align-items:center;gap:6px;width:100%;">' + parts.join('') + '</div>' +
      capHtml + '</div>' + hint
    );
  }

  return '<div style="color:#9aa0a6;font-style:italic;padding:12px;">Unknown linkedin_post_image mode: ' + _esc(mode) + '</div>';
};

