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
         '<button id="' + btnId + '" class="asw-btn asw-btn-primary"' +
         ' data-fn="' + _esc(functionName) + '" data-arg="' + _esc(argument) + '"' +
         ' onclick="runCustomScript(this.id,this.dataset.fn,this.dataset.arg)">' +
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
  css += '.tm-tab-panel-' + uid + '{display:none;padding:16px;}';
  css += '.tm-tab-lbl-' + uid + '{padding:10px 18px;cursor:pointer;font-size:0.85rem;font-weight:600;color:#5f6368;white-space:nowrap;border-bottom:2px solid transparent;margin-bottom:-2px;transition:color 0.15s;}';
  tabList.forEach(function(t, i){
    css += '#tb' + uid + '_' + i + ':checked ~ .tm-tab-labels-' + uid + ' .tm-tab-lbl-' + uid + ':nth-child(' + (i+1) + '){color:#1a73e8;border-bottom-color:#1a73e8;}';
    css += '#tb' + uid + '_' + i + ':checked ~ .tm-tab-panels-' + uid + ' .tm-tab-panel-' + uid + ':nth-child(' + (i+1) + '){display:block;}';
  });
  css += '</style>';
  var inputs = tabList.map(function(t, i){
    return '<input type="radio" id="tb' + uid + '_' + i + '" name="tab_' + uid + '" style="display:none;"' + (i===0?' checked':'') + '>';
  }).join('');
  var labels = '<div class="tm-tab-labels-' + uid + '" style="display:flex;flex-wrap:wrap;border-bottom:2px solid #e5e7eb;margin-bottom:0;">' +
    tabList.map(function(t, i){
      return '<label for="tb' + uid + '_' + i + '" class="tm-tab-lbl-' + uid + '">' + _esc(t.label||('Tab '+(i+1))) + '</label>';
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
      return '<div class="tm-tab-panel-' + uid + '">' + content + '</div>';
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
  var uid    = Math.random().toString(36).substr(2, 6);
  var height = b.height   || '220px';
  var accent = b.accent   || '#6366f1';
  var frontBg = b.front_bg || 'var(--bg)';
  var backBg  = b.back_bg  || accent;

  var frontHtml = '', backHtml = '';
  (b.front_blocks || []).forEach(function(blk) { var fn = _RENDERERS[blk.component||blk.type]; if (fn) frontHtml += fn(blk); });
  (b.back_blocks  || []).forEach(function(blk) { var fn = _RENDERERS[blk.component||blk.type]; if (fn) backHtml  += fn(blk); });
  if (!frontHtml && b.front) frontHtml = '<p style="margin:0">' + _esc(b.front) + '</p>';
  if (!backHtml  && b.back)  backHtml  = '<p style="margin:0">' + _esc(b.back)  + '</p>';

  return '<style>'
    + '#fco' + uid + '{perspective:1000px;margin:1.5rem 0;}'
    + '#fci' + uid + '{position:relative;width:100%;height:' + height + ';transform-style:preserve-3d;transform:rotateY(0deg);transition:transform 0.65s cubic-bezier(0.4,0.2,0.2,1);cursor:pointer;}'
    + '#fco' + uid + '.flp #fci' + uid + '{transform:rotateY(180deg);}'
    + '.fcf' + uid + ',.fcb' + uid + '{position:absolute;inset:0;backface-visibility:hidden;-webkit-backface-visibility:hidden;border-radius:12px;padding:20px;box-sizing:border-box;overflow:hidden;}'
    + '.fcf' + uid + '{background:' + frontBg + ';border:2px solid ' + accent + '33;}'
    + '.fcb' + uid + '{background:' + backBg + ';color:#fff;transform:rotateY(180deg);}'
    + '.fch' + uid + '{position:absolute;bottom:10px;right:14px;font-size:0.62rem;opacity:0.45;pointer-events:none;}'
    + '</style>'
    + '<div id="fco' + uid + '" onclick="this.classList.toggle(\'flp\')">'
    + '<div id="fci' + uid + '">'
    + '<div class="fcf' + uid + '">' + frontHtml + '<span class="fch' + uid + '">tap to flip ↺</span></div>'
    + '<div class="fcb' + uid + '">' + backHtml  + '<span class="fch' + uid + '">tap to flip ↺</span></div>'
    + '</div></div>';
};

// World land outlines — Natural Earth 110m, RDP-simplified at 1.5°, coords ×10
// 46 rings, 543 pts, ~6KB. Format: [[lon10, lat10], ...]
var _GW = '[[[-452,-780],[-433,-800],[-542,-806],[-452,-780]],[[-1256,-735],[-1240,-739],[-1273,-735],[-1256,-735]],[[-990,-719],[-962,-725],[-1023,-719],[-990,-719]],[[-685,-710],[-750,-717],[-703,-689],[-685,-710]],[[-1800,-847],[-1431,-850],[-1536,-837],[-1529,-820],[-1568,-811],[-1464,-803],[-1584,-769],[-1449,-752],[-689,-730],[-673,-669],[-578,-633],[-657,-680],[-608,-737],[-772,-767],[-737,-779],[-780,-792],[-582,-832],[-286,-803],[-358,-783],[-69,-709],[386,-698],[545,-658],[689,-679],[679,-719],[699,-723],[880,-662],[1198,-673],[1351,-653],[1712,-717],[1636,-762],[1670,-788],[1598,-809],[1783,-845],[-1800,-847]],[[-678,-538],[-651,-547],[-692,-555],[-747,-528],[-678,-538]],[[1454,-408],[1483,-409],[1479,-432],[1460,-435],[1454,-408]],[[1730,-409],[1731,-439],[1667,-462],[1730,-409]],[[1746,-362],[1785,-377],[1752,-417],[1726,-345],[1746,-362]],[[501,-136],[471,-249],[440,-250],[444,-162],[492,-120],[501,-136]],[[1436,-138],[1531,-261],[1500,-374],[1406,-380],[1382,-344],[1368,-353],[1378,-329],[1360,-349],[1313,-315],[1150,-342],[1141,-218],[1209,-197],[1257,-142],[1296,-150],[1324,-111],[1365,-119],[1355,-150],[1402,-177],[1425,-107],[1436,-138]],[[1086,-68],[1157,-84],[1054,-69],[1086,-68]],[[1341,-12],[1355,-34],[1383,-17],[1446,-39],[1507,-106],[1447,-76],[1376,-84],[1379,-54],[1305,-9],[1341,-12]],[[1252,14],[1202,2],[1233,-6],[1215,-19],[1232,-53],[1210,-26],[1194,-54],[1200,6],[1252,14]],[[1058,-59],[953,55],[1038,1],[1058,-59]],[[1179,18],[1161,-40],[1102,-29],[1091,-5],[1167,69],[1192,54],[1179,18]],[[1264,84],[1254,56],[1219,72],[1254,98],[1264,84]],[[1185,93],[1172,84],[1195,114],[1185,93]],[[1213,185],[1241,125],[1201,150],[1213,185]],[[-726,199],[-683,186],[-745,183],[-726,199]],[[-797,228],[-742,203],[-850,219],[-797,228]],[[1410,371],[1358,335],[1310,339],[1302,314],[1294,333],[1357,355],[1414,414],[1410,371]],[[1439,442],[1455,433],[1400,416],[1420,456],[1439,442]],[[-561,507],[-531,467],[-593,476],[-561,507]],[[1436,507],[1447,490],[1421,460],[1422,542],[1436,507]],[[-68,523],[-100,518],[-97,539],[-67,552],[-68,523]],[[-30,586],[14,513],[-52,500],[-29,540],[-62,568],[-30,586]],[[-852,657],[-801,637],[-872,635],[-852,657]],[[-145,665],[-136,651],[-187,635],[-243,656],[-145,665]],[[-1800,690],[-1699,660],[-1730,643],[-1799,659],[1800,650],[1774,646],[1792,623],[1635,599],[1621,549],[1568,510],[1559,568],[1645,626],[1567,614],[1550,591],[1422,590],[1351,547],[1414,522],[1382,463],[1275,398],[1291,351],[1265,344],[1253,396],[1211,389],[1216,409],[1180,392],[1224,375],[1192,349],[1217,282],[1159,228],[1059,198],[1093,134],[1052,86],[1001,134],[992,92],[1042,13],[983,78],[972,169],[942,160],[914,228],[803,159],[775,80],[726,214],[705,209],[664,254],[574,257],[480,300],[518,240],[564,264],[598,223],[553,172],[435,126],[349,295],[339,276],[324,299],[427,117],[510,106],[392,-47],[408,-147],[348,-198],[355,-241],[282,-328],[196,-348],[118,-181],[137,-107],[88,-11],[94,37],[43,63],[-90,48],[-166,122],[-170,219],[-59,358],[95,374],[103,338],[191,303],[215,328],[338,310],[362,367],[276,367],[262,395],[417,420],[367,452],[391,473],[339,444],[307,466],[277,426],[288,411],[226,403],[240,377],[225,364],[195,417],[131,457],[126,441],[185,402],[161,380],[89,444],[31,431],[-21,367],[-89,369],[-94,430],[-14,440],[-46,487],[81,535],[85,571],[106,577],[109,540],[197,544],[216,574],[241,570],[233,592],[291,600],[213,607],[215,632],[254,651],[222,657],[178,627],[188,601],[159,561],[129,554],[104,595],[57,586],[59,626],[245,710],[411,675],[332,666],[370,639],[440,661],[435,686],[463,667],[606,699],[685,681],[667,710],[726,728],[724,662],[751,678],[731,714],[747,728],[815,717],[805,736],[1044,777],[1141,758],[1094,742],[1270,736],[1313,708],[1405,728],[1609,694],[1786,694]],[[-905,695],[-873,672],[-855,699],[-826,697],[-813,676],[-932,620],[-947,589],[-923,571],[-823,551],[-799,512],[-798,547],[-765,565],[-781,623],[-738,624],[-677,582],[-646,603],[-557,521],[-664,502],[-711,468],[-651,492],[-645,462],[-598,459],[-654,435],[-644,453],[-671,451],[-759,372],[-764,391],[-757,356],[-813,314],[-804,252],[-841,301],[-966,283],[-963,193],[-920,187],[-871,215],[-889,159],[-834,153],[-838,111],[-814,88],[-768,86],[-718,124],[-717,91],[-699,122],[-619,107],[-571,60],[-513,42],[-504,-1],[-400,-29],[-347,-73],[-409,-219],[-476,-249],[-538,-344],[-584,-339],[-568,-369],[-651,-411],[-635,-426],[-673,-456],[-660,-481],[-710,-538],[-749,-523],[-756,-466],[-727,-424],[-743,-432],[-702,-198],[-813,-61],[-809,-11],[-771,38],[-782,83],[-809,72],[-875,133],[-1035,183],[-1148,318],[-1094,232],[-1122,247],[-1244,403],[-1247,482],[-1226,471],[-1228,490],[-1341,581],[-1471,609],[-1517,592],[-1506,613],[-1648,544],[-1570,589],[-1620,587],[-1661,615],[-1608,648],[-1681,657],[-1617,661],[-1668,684],[-1566,714],[-1089,674],[-961,673],[-942,691],[-965,701],[-952,719],[-905,695]],[[-1142,731],[-1065,731],[-1010,700],[-1133,685],[-1173,700],[-1124,704],[-1194,716],[-1142,731]],[[-866,732],[-722,716],[-619,669],[-639,650],[-680,663],[-647,634],[-688,637],[-662,619],[-777,642],[-729,677],[-899,712],[-866,732]],[[-1004,738],[-967,717],[-1025,725],[-1004,738]],[[-932,728],[-960,734],[-905,739],[-932,728]],[[-1205,714],[-1259,719],[-1249,743],[-1155,735],[-1205,714]],[[-985,767],[-982,750],[-1025,756],[-985,767]],[[-1082,762],[-1057,755],[-1177,752],[-1082,762]],[[575,707],[515,720],[556,751],[689,765],[585,743],[554,724],[575,707]],[[-947,771],[-798,749],[-971,768],[-947,771]],[[183,797],[215,790],[159,768],[104,797],[183,797]],[[254,804],[274,801],[174,803],[254,804]],[[999,789],[912,803],[959,813],[999,789]],[[-870,797],[-908,782],[-967,802],[-870,797]],[[-685,831],[-619,826],[-769,793],[-754,785],[-806,762],[-895,765],[-850,775],[-880,784],[-851,793],[-869,803],[-818,805],[-916,819],[-685,831]],[[-271,835],[-208,827],[-319,822],[-122,813],[-200,802],[-177,801],[-197,788],[-185,770],[-217,766],[-194,743],[-248,723],[-218,707],[-264,702],[-223,701],[-398,655],[-434,601],[-516,636],[-540,672],[-509,699],[-547,696],[-514,706],[-558,717],[-586,755],[-733,780],[-626,818],[-271,835]]]';

_RENDERERS['globe_3d'] = function(b) {
  var uid   = Math.random().toString(36).substr(2, 6);
  var size  = b.size  || 300;
  var color = b.color || '#6366f1';
  var speed = b.speed !== undefined ? b.speed : 0.006;
  var lines = b.lines || 10;
  var theme = b.theme || 'wire';   // 'wire' | 'earth'
  var dots  = JSON.stringify(b.dots || []);
  var arcs  = JSON.stringify(b.arcs || []);

  // Theme gradient stops and optional land polygon drawing — resolved at render time
  var gradStops = theme === 'earth'
    ? 'g.addColorStop(0,"#1e3a8a");g.addColorStop(0.7,"#0c1a4a");g.addColorStop(1,"#000");'
    : 'g.addColorStop(0,col+"1a");g.addColorStop(1,col+"06");';

  // Land masses: drawn after sphere fill, clipped to sphere circle, only in earth theme
  var landCode = theme === 'earth'
    ? 'ctx.save();'
    + 'ctx.beginPath();ctx.arc(cx,cy,R,0,Math.PI*2);ctx.clip();'
    + 'ctx.beginPath();'
    + '_WD.forEach(function(ring){'
    +   'var go=false;'
    +   'for(var i=0;i<ring.length;i++){'
    +     'var pt=ring[i],p=projVec(toVec(pt[1]/10,pt[0]/10));'
    +     'if(p.z<0){go=false;continue;}'
    +     'go?ctx.lineTo(p.sx,p.sy):ctx.moveTo(p.sx,p.sy);go=true;'
    +   '}'
    + '});'
    + 'ctx.fillStyle="#1a4a3a";ctx.fill();'
    + 'ctx.restore();'
    : '';

  return '<div style="overflow:visible;display:flex;justify-content:center;margin:1.5rem auto;">'
    + '<canvas id="gl' + uid + '" width="' + (size*2) + '" height="' + (size*2) + '" style="display:block;cursor:grab;flex-shrink:0;transform-origin:center center;width:' + size + 'px;height:' + size + 'px;"></canvas>'
    + '</div>'
    + '<script>(function(){'
    + 'var c=document.getElementById("gl' + uid + '");'
    + 'var ctx=c.getContext("2d");ctx.scale(2,2);'
    + 'var W=c.width/2,H=c.height/2,baseR=W*0.42,R=baseR,cx=W/2,cy=H/2;'
    + 'var aY=0,aX=0,spd=' + speed + ',n=' + lines + ',col="' + color + '",S=60;'
    + 'var dots=' + dots + ',arcs=' + arcs + ';'
    + 'var _WD=' + _GW + ';'
    + 'var drag=false,lx=0,ly=0,vx=0,vy=0;'
    + 'var zoom=1,tzoom=1;'
    // projVec: rotate a unit vector {x,y,z} and project to screen
    + 'function projVec(v){'
    +   'var x1=v.x*Math.cos(aY)+v.z*Math.sin(aY),z1=-v.x*Math.sin(aY)+v.z*Math.cos(aY);'
    +   'var y2=v.y*Math.cos(aX)-z1*Math.sin(aX),z2=v.y*Math.sin(aX)+z1*Math.cos(aX);'
    +   'return{sx:cx+x1*R,sy:cy-y2*R,z:z2};'
    + '}'
    // proj: lat/lon (radians) → screen
    + 'function proj(lat,lon){'
    +   'return projVec({x:Math.cos(lat)*Math.sin(lon),y:Math.sin(lat),z:Math.cos(lat)*Math.cos(lon)});'
    + '}'
    // toVec: lat/lon degrees → unit vector (unrotated, for slerp input)
    + 'function toVec(lat,lon){'
    +   'var la=lat*Math.PI/180,lo=lon*Math.PI/180;'
    +   'return{x:Math.cos(la)*Math.sin(lo),y:Math.sin(la),z:Math.cos(la)*Math.cos(lo)};'
    + '}'
    // slerp: spherical linear interpolation between two unit vectors
    + 'function slerp(a,b,t){'
    +   'var dot=Math.max(-1,Math.min(1,a.x*b.x+a.y*b.y+a.z*b.z));'
    +   'var om=Math.acos(dot);'
    +   'if(om<0.0001)return{x:a.x+(b.x-a.x)*t,y:a.y+(b.y-a.y)*t,z:a.z+(b.z-a.z)*t};'
    +   'var s=Math.sin(om),fa=Math.sin((1-t)*om)/s,fb=Math.sin(t*om)/s;'
    +   'return{x:a.x*fa+b.x*fb,y:a.y*fa+b.y*fb,z:a.z*fa+b.z*fb};'
    + '}'
    // h2: number 0-255 → 2-digit hex (for alpha in strokeStyle)
    + 'function h2(v){return("0"+Math.round(Math.max(0,Math.min(255,v))).toString(16)).slice(-2);}'
    + 'function draw(){'
    +   'ctx.clearRect(0,0,W,H);'
    // Lerped zoom via CSS transform — canvas stays fixed, pixels scale outward
    +   'zoom+=(tzoom-zoom)*0.1;c.style.transform="scale("+zoom.toFixed(3)+")";'
    // Inertia + auto-rotate (heavier 0.94 friction for physical globe weight)
    +   'if(!drag){aY+=spd+vx;aX+=vy;vx*=0.94;vy*=0.94;}'
    // Sphere fill
    +   'var g=ctx.createRadialGradient(cx-R*0.28,cy-R*0.28,R*0.05,cx,cy,R);'
    +   gradStops
    +   'ctx.beginPath();ctx.arc(cx,cy,R,0,Math.PI*2);ctx.fillStyle=g;ctx.fill();'
    +   landCode
    // Limb darkening — radial overlay from transparent centre to dark edge, fakes 3D curvature
    +   'var limb=ctx.createRadialGradient(cx,cy,R*0.6,cx,cy,R);'
    +   'limb.addColorStop(0,"rgba(0,0,0,0)");limb.addColorStop(1,"rgba(0,4,18,0.9)");'
    +   'ctx.beginPath();ctx.arc(cx,cy,R,0,Math.PI*2);ctx.fillStyle=limb;ctx.fill();'
    +   'ctx.beginPath();ctx.arc(cx,cy,R,0,Math.PI*2);ctx.strokeStyle=col+"55";ctx.lineWidth=1.5;ctx.stroke();'
    // Wireframe grid: back pass (dashed, faint) then front pass (solid)
    +   '[false,true].forEach(function(front){'
    +     'ctx.lineWidth=front?1:0.6;ctx.setLineDash(front?[]:[3,3]);var al=front?"bb":"22";'
    +     'for(var i=1;i<n;i++){'
    +       'var lat=(i/n)*Math.PI-Math.PI/2;ctx.beginPath();var go=false;'
    +       'for(var j=0;j<=S;j++){var p=proj(lat,(j/S)*Math.PI*2);if((p.z>=0)!==front){go=false;continue;}go?ctx.lineTo(p.sx,p.sy):ctx.moveTo(p.sx,p.sy);go=true;}'
    +       'ctx.strokeStyle=col+al;ctx.stroke();'
    +     '}'
    +     'for(var i=0;i<n;i++){'
    +       'var lon=(i/n)*Math.PI*2;ctx.beginPath();var go=false;'
    +       'for(var j=0;j<=S;j++){var p=proj((j/S)*Math.PI-Math.PI/2,lon);if((p.z>=0)!==front){go=false;continue;}go?ctx.lineTo(p.sx,p.sy):ctx.moveTo(p.sx,p.sy);go=true;}'
    +       'ctx.strokeStyle=col+al;ctx.stroke();'
    +     '}'
    +   '});'
    +   'ctx.setLineDash([]);'
    // Great-circle arcs via slerp — clipped at horizon, animated dot
    +   'var now=Date.now();'
    +   'arcs.forEach(function(arc,ai){'
    +     'var v1=toVec(arc.start[0],arc.start[1]),v2=toVec(arc.end[0],arc.end[1]);'
    +     'var segs=arc.segments||50,acol=arc.color||col;'
    +     'ctx.beginPath();var go=false;'
    +     'for(var i=0;i<=segs;i++){'
    +       'var sv=slerp(v1,v2,i/segs),p=projVec(sv);'
    +       'if(p.z<0){go=false;continue;}'
    +       'go?ctx.lineTo(p.sx,p.sy):ctx.moveTo(p.sx,p.sy);go=true;'
    +     '}'
    +     'ctx.strokeStyle=acol+"cc";ctx.lineWidth=1.5;ctx.stroke();'
    // Animated dot travelling along the arc (staggered per arc by 1/3 cycle)
    +     'var prog=((now/2500)+(ai*0.33))%1;'
    +     'var sp=slerp(v1,v2,prog),pp=projVec(sp);'
    +     'if(pp.z>0){'
    +       'ctx.beginPath();ctx.arc(pp.sx,pp.sy,4,0,Math.PI*2);ctx.fillStyle=acol;ctx.fill();'
    +       'ctx.beginPath();ctx.arc(pp.sx,pp.sy,8,0,Math.PI*2);ctx.strokeStyle=acol+"66";ctx.lineWidth=1;ctx.stroke();'
    +     '}'
    +   '});'
    // Dot markers — depth-based globalAlpha so edge dots fade in, golden-ratio pulse stagger
    +   'dots.forEach(function(d,i){'
    +     'var p=proj(d.lat*Math.PI/180,d.lon*Math.PI/180);'
    +     'if(p.z<-0.1)return;'
    +     'ctx.globalAlpha=Math.max(0.25,Math.min(1,p.z+0.5));'
    +     'var phase=((now/1400)+(i*0.618))%1;'
    +     'ctx.beginPath();ctx.arc(p.sx,p.sy,phase*18,0,Math.PI*2);'
    +     'ctx.strokeStyle=col+h2((1-phase)*160);ctx.lineWidth=1;ctx.stroke();'
    +     'ctx.beginPath();ctx.arc(p.sx,p.sy,4,0,Math.PI*2);ctx.fillStyle=col;ctx.fill();'
    +     'if(d.label){ctx.font="bold 11px sans-serif";ctx.fillStyle=col;ctx.fillText(d.label,p.sx+7,p.sy+4);}'
    +   '});'
    +   'ctx.globalAlpha=1;'
    +   'requestAnimationFrame(draw);'
    + '}'
    // Scroll-to-zoom (lerped, clamped 0.5×–2.5×)
    + 'c.addEventListener("wheel",function(e){e.preventDefault();tzoom=Math.max(0.5,Math.min(2.5,tzoom-e.deltaY*0.001));},{passive:false});'
    // Mouse drag
    + 'c.addEventListener("mousedown",function(e){drag=true;lx=e.clientX;ly=e.clientY;c.style.cursor="grabbing";});'
    + 'document.addEventListener("mouseup",function(){drag=false;c.style.cursor="grab";});'
    + 'document.addEventListener("mousemove",function(e){'
    +   'if(!drag)return;'
    +   'vx=(e.clientX-lx)*0.012/zoom;vy=(e.clientY-ly)*0.012/zoom;'
    +   'aY+=vx;aX+=vy;aX=Math.max(-1.4,Math.min(1.4,aX));'
    +   'lx=e.clientX;ly=e.clientY;'
    + '});'
    // Touch drag
    + 'c.addEventListener("touchstart",function(e){e.preventDefault();drag=true;lx=e.touches[0].clientX;ly=e.touches[0].clientY;},{passive:false});'
    + 'document.addEventListener("touchend",function(){drag=false;});'
    + 'c.addEventListener("touchmove",function(e){'
    +   'e.preventDefault();if(!drag)return;'
    +   'vx=(e.touches[0].clientX-lx)*0.012/zoom;vy=(e.touches[0].clientY-ly)*0.012/zoom;'
    +   'aY+=vx;aX+=vy;aX=Math.max(-1.4,Math.min(1.4,aX));'
    +   'lx=e.touches[0].clientX;ly=e.touches[0].clientY;'
    + '},{passive:false});'
    + 'draw();'
    + '})();<\/script>';
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

_RENDERERS['globe_3d'] = function(b) {
  var uid   = Math.random().toString(36).substr(2, 6);
  var size  = b.size  || 300;
  var color = b.color || '#6366f1';
  var speed = b.speed !== undefined ? b.speed : 0.006;
  var lines = b.lines || 10;
  var theme = b.theme || 'wire';   // 'wire' | 'earth'
  var dots  = JSON.stringify(b.dots || []);
  var arcs  = JSON.stringify(b.arcs || []);

  // Theme gradient stops and optional land polygon drawing — resolved at render time
  var gradStops = theme === 'earth'
    ? 'g.addColorStop(0,"#1e3a8a");g.addColorStop(0.7,"#0c1a4a");g.addColorStop(1,"#000");'
    : 'g.addColorStop(0,col+"1a");g.addColorStop(1,col+"06");';

  // Land masses: drawn after sphere fill, clipped to sphere circle, only in earth theme
  var landCode = theme === 'earth'
    ? 'ctx.save();'
    + 'ctx.beginPath();ctx.arc(cx,cy,R,0,Math.PI*2);ctx.clip();'
    + 'ctx.beginPath();'
    + '_WD.forEach(function(ring){'
    +   'var go=false;'
    +   'for(var i=0;i<ring.length;i++){'
    +     'var pt=ring[i],p=projVec(toVec(pt[1]/10,pt[0]/10));'
    +     'if(p.z<0){go=false;continue;}'
    +     'go?ctx.lineTo(p.sx,p.sy):ctx.moveTo(p.sx,p.sy);go=true;'
    +   '}'
    + '});'
    + 'ctx.fillStyle="#1a4a3a";ctx.fill();'
    + 'ctx.restore();'
    : '';

  return '<div style="overflow:visible;display:flex;justify-content:center;margin:1.5rem auto;">'
    + '<canvas id="gl' + uid + '" width="' + (size*2) + '" height="' + (size*2) + '" style="display:block;cursor:grab;flex-shrink:0;transform-origin:center center;width:' + size + 'px;height:' + size + 'px;"></canvas>'
    + '</div>'
    + '<script>(function(){'
    + 'var c=document.getElementById("gl' + uid + '");'
    + 'var ctx=c.getContext("2d");ctx.scale(2,2);'
    + 'var W=c.width/2,H=c.height/2,baseR=W*0.42,R=baseR,cx=W/2,cy=H/2;'
    + 'var aY=0,aX=0,spd=' + speed + ',n=' + lines + ',col="' + color + '",S=60;'
    + 'var dots=' + dots + ',arcs=' + arcs + ';'
    + 'var _WD=' + _GW + ';'
    + 'var drag=false,lx=0,ly=0,vx=0,vy=0;'
    + 'var zoom=1,tzoom=1;'
    // projVec: rotate a unit vector {x,y,z} and project to screen
    + 'function projVec(v){'
    +   'var x1=v.x*Math.cos(aY)+v.z*Math.sin(aY),z1=-v.x*Math.sin(aY)+v.z*Math.cos(aY);'
    +   'var y2=v.y*Math.cos(aX)-z1*Math.sin(aX),z2=v.y*Math.sin(aX)+z1*Math.cos(aX);'
    +   'return{sx:cx+x1*R,sy:cy-y2*R,z:z2};'
    + '}'
    // proj: lat/lon (radians) → screen
    + 'function proj(lat,lon){'
    +   'return projVec({x:Math.cos(lat)*Math.sin(lon),y:Math.sin(lat),z:Math.cos(lat)*Math.cos(lon)});'
    + '}'
    // toVec: lat/lon degrees → unit vector (unrotated, for slerp input)
    + 'function toVec(lat,lon){'
    +   'var la=lat*Math.PI/180,lo=lon*Math.PI/180;'
    +   'return{x:Math.cos(la)*Math.sin(lo),y:Math.sin(la),z:Math.cos(la)*Math.cos(lo)};'
    + '}'
    // slerp: spherical linear interpolation between two unit vectors
    + 'function slerp(a,b,t){'
    +   'var dot=Math.max(-1,Math.min(1,a.x*b.x+a.y*b.y+a.z*b.z));'
    +   'var om=Math.acos(dot);'
    +   'if(om<0.0001)return{x:a.x+(b.x-a.x)*t,y:a.y+(b.y-a.y)*t,z:a.z+(b.z-a.z)*t};'
    +   'var s=Math.sin(om),fa=Math.sin((1-t)*om)/s,fb=Math.sin(t*om)/s;'
    +   'return{x:a.x*fa+b.x*fb,y:a.y*fa+b.y*fb,z:a.z*fa+b.z*fb};'
    + '}'
    // h2: number 0-255 → 2-digit hex (for alpha in strokeStyle)
    + 'function h2(v){return("0"+Math.round(Math.max(0,Math.min(255,v))).toString(16)).slice(-2);}'
    + 'function draw(){'
    +   'ctx.clearRect(0,0,W,H);'
    // Lerped zoom via CSS transform — canvas stays fixed, pixels scale outward
    +   'zoom+=(tzoom-zoom)*0.1;c.style.transform="scale("+zoom.toFixed(3)+")";'
    // Inertia + auto-rotate (heavier 0.94 friction for physical globe weight)
    +   'if(!drag){aY+=spd+vx;aX+=vy;vx*=0.94;vy*=0.94;}'
    // Sphere fill
    +   'var g=ctx.createRadialGradient(cx-R*0.28,cy-R*0.28,R*0.05,cx,cy,R);'
    +   gradStops
    +   'ctx.beginPath();ctx.arc(cx,cy,R,0,Math.PI*2);ctx.fillStyle=g;ctx.fill();'
    +   landCode
    // Limb darkening — radial overlay from transparent centre to dark edge, fakes 3D curvature
    +   'var limb=ctx.createRadialGradient(cx,cy,R*0.6,cx,cy,R);'
    +   'limb.addColorStop(0,"rgba(0,0,0,0)");limb.addColorStop(1,"rgba(0,4,18,0.9)");'
    +   'ctx.beginPath();ctx.arc(cx,cy,R,0,Math.PI*2);ctx.fillStyle=limb;ctx.fill();'
    +   'ctx.beginPath();ctx.arc(cx,cy,R,0,Math.PI*2);ctx.strokeStyle=col+"55";ctx.lineWidth=1.5;ctx.stroke();'
    // Wireframe grid: back pass (dashed, faint) then front pass (solid)
    +   '[false,true].forEach(function(front){'
    +     'ctx.lineWidth=front?1:0.6;ctx.setLineDash(front?[]:[3,3]);var al=front?"bb":"22";'
    +     'for(var i=1;i<n;i++){'
    +       'var lat=(i/n)*Math.PI-Math.PI/2;ctx.beginPath();var go=false;'
    +       'for(var j=0;j<=S;j++){var p=proj(lat,(j/S)*Math.PI*2);if((p.z>=0)!==front){go=false;continue;}go?ctx.lineTo(p.sx,p.sy):ctx.moveTo(p.sx,p.sy);go=true;}'
    +       'ctx.strokeStyle=col+al;ctx.stroke();'
    +     '}'
    +     'for(var i=0;i<n;i++){'
    +       'var lon=(i/n)*Math.PI*2;ctx.beginPath();var go=false;'
    +       'for(var j=0;j<=S;j++){var p=proj((j/S)*Math.PI-Math.PI/2,lon);if((p.z>=0)!==front){go=false;continue;}go?ctx.lineTo(p.sx,p.sy):ctx.moveTo(p.sx,p.sy);go=true;}'
    +       'ctx.strokeStyle=col+al;ctx.stroke();'
    +     '}'
    +   '});'
    +   'ctx.globalAlpha=1;'
    +   'requestAnimationFrame(draw);'
    + '}'
    // Scroll-to-zoom (lerped, clamped 0.5×–2.5×)
    + 'c.addEventListener("wheel",function(e){e.preventDefault();tzoom=Math.max(0.5,Math.min(2.5,tzoom-e.deltaY*0.001));},{passive:false});'
    // Mouse drag
    + 'c.addEventListener("mousedown",function(e){drag=true;lx=e.clientX;ly=e.clientY;c.style.cursor="grabbing";});'
    + 'document.addEventListener("mouseup",function(){drag=false;c.style.cursor="grab";});'
    + 'document.addEventListener("mousemove",function(e){'
    +   'if(!drag)return;'
    +   'vx=(e.clientX-lx)*0.012/zoom;vy=(e.clientY-ly)*0.012/zoom;'
    +   'aY+=vx;aX+=vy;aX=Math.max(-1.4,Math.min(1.4,aX));'
    +   'lx=e.clientX;ly=e.clientY;'
    + '});'
    // Touch drag
    + 'c.addEventListener("touchstart",function(e){e.preventDefault();drag=true;lx=e.touches[0].clientX;ly=e.touches[0].clientY;},{passive:false});'
    + 'document.addEventListener("touchend",function(){drag=false;});'
    + 'c.addEventListener("touchmove",function(e){'
    +   'e.preventDefault();if(!drag)return;'
    +   'vx=(e.touches[0].clientX-lx)*0.012/zoom;vy=(e.touches[0].clientY-ly)*0.012/zoom;'
    +   'aY+=vx;aX+=vy;aX=Math.max(-1.4,Math.min(1.4,aX));'
    +   'lx=e.touches[0].clientX;ly=e.touches[0].clientY;'
    + '},{passive:false});'
    + 'draw();'
    + '})();<\/script>';
};

_RENDERERS['linkedin_post_image'] = function(b) {
  var mode   = b.mode || 'conviction_card';
  var accent = b.accent || '#7c3aed';

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
    return '<div style="aspect-ratio:1.91/1;background:#0f172a;border-radius:12px;' +
      'display:flex;align-items:center;justify-content:center;padding:48px;' +
      'position:relative;overflow:hidden;margin:1.5rem 0;">' +
      '<div style="position:absolute;bottom:0;left:0;right:0;height:4px;' +
      'background:linear-gradient(90deg,' + _esc(accent) + ',#3b82f6);"></div>' +
      '<div style="text-align:center;max-width:80%;">' +
      '<div style="font-size:clamp(1rem,3vw,1.7rem);color:#f1f5f9;font-weight:700;' +
      'line-height:1.45;font-style:italic;">"' + _esc(quote) + '"</div>' +
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

// ── Visual / Beauty ──────────────────────────────────────────────────────────

_RENDERERS['gradient_hero'] = function(b) {
  var uid      = Math.random().toString(36).substr(2, 6);
  var accent   = b.accent || '#6366f1';
  var accent2  = b.accent2 || '#8b5cf6';
  var gradient = b.gradient || ('linear-gradient(135deg,' + accent + '22 0%,' + accent2 + '18 60%,#fff8 100%)');
  var align    = b.align === 'center' ? 'center' : 'left';
  return '<style>' +
    '.gh-' + uid + '{padding:48px 32px;border-radius:16px;background:' + gradient + ';margin:0 0 1.5rem;text-align:' + align + ';}' +
    '.gh-badge-' + uid + '{display:inline-block;background:' + accent + ';color:#fff;border-radius:99px;padding:3px 14px;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:14px;}' +
    '.gh-title-' + uid + '{font-size:36px;font-weight:900;line-height:1.15;color:#111827;margin-bottom:12px;letter-spacing:-0.02em;}' +
    '.gh-sub-' + uid + '{font-size:17px;color:#4b5563;line-height:1.6;margin-bottom:20px;max-width:600px;' + (align==='center'?'margin-left:auto;margin-right:auto;':'') + '}' +
    '.gh-cta-' + uid + '{display:inline-block;background:' + accent + ';color:#fff;border-radius:10px;padding:12px 28px;font-size:15px;font-weight:700;text-decoration:none;}' +
    '</style>' +
    '<div class="gh-' + uid + '">' +
    (b.badge ? '<div class="gh-badge-' + uid + '">' + _esc(b.badge) + '</div>' : '') +
    '<div class="gh-title-' + uid + '">' + _md(b.title || b.heading || '') + '</div>' +
    (b.subtitle || b.subtext ? '<div class="gh-sub-' + uid + '">' + _md(b.subtitle || b.subtext) + '</div>' : '') +
    (b.cta_label && b.cta_url ? '<a class="gh-cta-' + uid + '" href="' + _esc(b.cta_url) + '">' + _esc(b.cta_label) + '</a>' : '') +
    '</div>';
};

_RENDERERS['icon_list'] = function(b) {
  var uid   = Math.random().toString(36).substr(2, 6);
  var items = b.items || [];
  var size  = b.size || 'md';
  var iconSize = size === 'lg' ? '42px' : size === 'sm' ? '28px' : '36px';
  var fontSize = size === 'lg' ? '15px' : size === 'sm' ? '13px' : '14px';
  var rowsHtml = items.map(function(item) {
    var color = item.color || b.accent || '#6366f1';
    var icon  = item.icon || '•';
    return '<div style="display:flex;gap:14px;align-items:flex-start;margin-bottom:14px;">' +
      '<div style="flex:0 0 ' + iconSize + ';height:' + iconSize + ';border-radius:50%;background:' + color + '18;display:flex;align-items:center;justify-content:center;font-size:' + (size==='lg'?'20px':size==='sm'?'13px':'16px') + ';">' + _esc(icon) + '</div>' +
      '<div style="flex:1;padding-top:' + (size==='lg'?'10px':'6px') + ';">' +
      (item.label ? '<div style="font-size:' + fontSize + ';font-weight:700;color:#111827;margin-bottom:2px;">' + _esc(item.label) + '</div>' : '') +
      (item.text ? '<div style="font-size:' + fontSize + ';color:#4b5563;line-height:1.5;">' + _md(item.text) + '</div>' : '') +
      '</div></div>';
  }).join('');
  return (b.title ? '<div style="font-size:16px;font-weight:700;color:#111827;margin-bottom:14px;">' + _esc(b.title) + '</div>' : '') +
    '<div style="margin:1rem 0;">' + rowsHtml + '</div>';
};

_RENDERERS['highlight_box'] = function(b) {
  var uid    = Math.random().toString(36).substr(2, 6);
  var accent = b.accent || '#6366f1';
  var style  = b.style || 'gradient';
  var bg = style === 'gradient'
    ? ('linear-gradient(135deg,' + accent + '18 0%,' + accent + '08 100%)')
    : style === 'solid' ? accent + '12'
    : '#fff';
  var border = style === 'outline' ? '2px solid ' + accent : '1px solid ' + accent + '30';
  return '<style>' +
    '.hb-' + uid + '{background:' + bg + ';border:' + border + ';border-radius:12px;padding:24px 28px;margin:1.5rem 0;}' +
    '.hb-icon-' + uid + '{font-size:28px;margin-bottom:10px;display:block;}' +
    '.hb-title-' + uid + '{font-size:18px;font-weight:800;color:#111827;margin-bottom:8px;}' +
    '.hb-text-' + uid + '{font-size:14px;color:#374151;line-height:1.65;}' +
    '</style>' +
    '<div class="hb-' + uid + '">' +
    (b.icon ? '<span class="hb-icon-' + uid + '">' + _esc(b.icon) + '</span>' : '') +
    (b.title ? '<div class="hb-title-' + uid + '">' + _md(b.title) + '</div>' : '') +
    '<div class="hb-text-' + uid + '">' + _md(b.text || '') + '</div>' +
    '</div>';
};

_RENDERERS['two_tone_card'] = function(b) {
  var uid    = Math.random().toString(36).substr(2, 6);
  var accent = b.accent || '#6366f1';
  var dark   = b.header_theme === 'dark';
  var headerBg = dark ? '#0f172a' : accent;
  var headerTc = '#fff';
  return '<style>' +
    '.ttc-' + uid + '{border-radius:14px;overflow:hidden;border:1px solid #e5e7eb;margin:1rem 0;}' +
    '.ttc-head-' + uid + '{background:' + headerBg + ';padding:20px 24px;}' +
    '.ttc-head-icon-' + uid + '{font-size:24px;margin-bottom:8px;display:block;}' +
    '.ttc-head-title-' + uid + '{font-size:18px;font-weight:800;color:' + headerTc + ';margin-bottom:4px;}' +
    '.ttc-head-sub-' + uid + '{font-size:13px;color:' + (dark?'#94a3b8':'rgba(255,255,255,0.8)') + ';}' +
    '.ttc-body-' + uid + '{background:#fff;padding:20px 24px;}' +
    '</style>' +
    '<div class="ttc-' + uid + '">' +
    '<div class="ttc-head-' + uid + '">' +
    (b.icon ? '<span class="ttc-head-icon-' + uid + '">' + _esc(b.icon) + '</span>' : '') +
    '<div class="ttc-head-title-' + uid + '">' + _esc(b.title || '') + '</div>' +
    (b.subtitle ? '<div class="ttc-head-sub-' + uid + '">' + _esc(b.subtitle) + '</div>' : '') +
    '</div>' +
    '<div class="ttc-body-' + uid + '">' + renderAtoms(b.blocks || b.content || []) + '</div>' +
    '</div>';
};

_RENDERERS['metric_row'] = function(b) {
  var uid     = Math.random().toString(36).substr(2, 6);
  var metrics = b.metrics || b.items || [];
  var cols    = Math.min(metrics.length, b.cols || 4);
  var metricsHtml = metrics.map(function(m) {
    var accent = m.accent || m.color || b.accent || '#6366f1';
    var trend  = m.trend === 'up' ? '↑' : m.trend === 'down' ? '↓' : '';
    var trendC = m.trend === 'up' ? '#16a34a' : m.trend === 'down' ? '#dc2626' : '#6b7280';
    return '<div style="text-align:center;padding:16px 8px;">' +
      '<div style="font-size:32px;font-weight:900;color:' + accent + ';line-height:1;margin-bottom:4px;">' +
      (m.prefix ? '<span style="font-size:18px;">' + _esc(m.prefix) + '</span>' : '') +
      _esc(m.value || '') +
      (m.suffix ? '<span style="font-size:18px;">' + _esc(m.suffix) + '</span>' : '') +
      (trend ? '<span style="font-size:16px;color:' + trendC + ';margin-left:4px;">' + trend + '</span>' : '') +
      '</div>' +
      '<div style="font-size:12px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.04em;">' + _esc(m.label || '') + '</div>' +
      (m.sub ? '<div style="font-size:11px;color:#9ca3af;margin-top:2px;">' + _esc(m.sub) + '</div>' : '') +
      '</div>';
  }).join('<div style="width:1px;background:#e5e7eb;margin:12px 0;"></div>');
  return '<div style="display:grid;grid-template-columns:repeat(' + cols + ',1fr);border:1px solid #e5e7eb;border-radius:12px;overflow:hidden;margin:1.5rem 0;background:#fff;">' +
    metricsHtml + '</div>';
};

_RENDERERS['numbered_list'] = function(b) {
  var uid   = Math.random().toString(36).substr(2, 6);
  var items = b.items || [];
  var style = b.style || 'large';
  var accent = b.accent || '#6366f1';
  var rowsHtml = items.map(function(item, i) {
    var num = i + 1;
    var numEl = style === 'large'
      ? '<div style="font-size:48px;font-weight:900;color:' + accent + '20;line-height:1;position:absolute;top:-8px;left:0;">' + num + '</div>'
      : '<div style="flex:0 0 28px;height:28px;border-radius:50%;background:' + accent + ';color:#fff;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:800;">' + num + '</div>';
    var wrap = style === 'large'
      ? 'position:relative;padding-left:44px;margin-bottom:28px;'
      : 'display:flex;gap:14px;align-items:flex-start;margin-bottom:20px;';
    return '<div style="' + wrap + '">' + numEl +
      '<div' + (style==='large'?' style="padding-top:4px;"':'') + '>' +
      (item.label ? '<div style="font-size:15px;font-weight:700;color:#111827;margin-bottom:3px;">' + _esc(item.label) + '</div>' : '') +
      (item.text  ? '<div style="font-size:14px;color:#4b5563;line-height:1.6;">' + _md(item.text) + '</div>' : '') +
      '</div></div>';
  }).join('');
  return (b.title ? '<div style="font-size:16px;font-weight:700;color:#111827;margin-bottom:16px;">' + _esc(b.title) + '</div>' : '') +
    '<div style="margin:1rem 0;">' + rowsHtml + '</div>';
};

// ── Page structure ───────────────────────────────────────────────────────────

_RENDERERS['page_header'] = function(b) {
  var uid    = Math.random().toString(36).substr(2, 6);
  var accent = b.accent || '#6366f1';
  var dark   = b.theme === 'dark';
  var bg     = dark ? '#0f172a' : (b.background || 'linear-gradient(135deg,' + accent + '18 0%,#fff 60%)');
  var tc     = dark ? '#f8fafc' : '#111827';
  var sc     = dark ? '#94a3b8' : '#6b7280';
  return '<style>' +
    '.ph-' + uid + '{padding:32px 28px 24px;margin:0 0 1.5rem;border-radius:14px;background:' + bg + ';border-bottom:3px solid ' + accent + ';}' +
    '.ph-icon-' + uid + '{font-size:36px;margin-bottom:10px;display:block;}' +
    '.ph-title-' + uid + '{font-size:28px;font-weight:800;color:' + tc + ';line-height:1.2;margin-bottom:6px;}' +
    '.ph-sub-' + uid + '{font-size:15px;color:' + sc + ';line-height:1.5;margin-bottom:10px;}' +
    '.ph-tag-' + uid + '{display:inline-block;background:' + accent + ';color:#fff;border-radius:99px;padding:2px 12px;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;}' +
    '</style>' +
    '<div class="ph-' + uid + '">' +
    (b.icon ? '<span class="ph-icon-' + uid + '">' + _esc(b.icon) + '</span>' : '') +
    '<div class="ph-title-' + uid + '">' + _md(b.title || '') + '</div>' +
    (b.subtitle ? '<div class="ph-sub-' + uid + '">' + _md(b.subtitle) + '</div>' : '') +
    (b.tag ? '<span class="ph-tag-' + uid + '">' + _esc(b.tag) + '</span>' : '') +
    '</div>';
};

_RENDERERS['back_button'] = function(b) {
  var uid    = Math.random().toString(36).substr(2, 6);
  var label  = b.label || '← Back';
  var accent = b.accent || '#6366f1';
  var style  = b.style || 'ghost';
  var href   = b.url ? 'href="' + _esc(b.url) + '"' : (b.nav_slug ? 'href="?nav=' + _esc(b.nav_slug) + '"' : 'href="javascript:history.back()"');
  var css = style === 'outline'
    ? 'border:1.5px solid ' + accent + ';color:' + accent + ';background:#fff;border-radius:8px;padding:6px 16px;'
    : style === 'text'
    ? 'color:' + accent + ';background:none;padding:4px 0;'
    : 'background:' + accent + '14;color:' + accent + ';border-radius:8px;padding:6px 16px;';
  return '<div style="margin:0.5rem 0 1rem;">' +
    '<a ' + href + ' style="display:inline-flex;align-items:center;gap:6px;font-size:14px;font-weight:600;text-decoration:none;' + css + '">' + _esc(label) + '</a>' +
    '</div>';
};

_RENDERERS['section_break'] = function(b) {
  var uid    = Math.random().toString(36).substr(2, 6);
  var accent = b.accent || '#e5e7eb';
  var style  = b.style || 'line';
  var label  = b.label || '';
  var borderStyle = style === 'dashed' ? 'dashed' : style === 'dots' ? 'dotted' : 'solid';
  if (!label) {
    return '<hr style="border:none;border-top:1px ' + borderStyle + ' ' + accent + ';margin:2rem 0;" />';
  }
  return '<div style="display:flex;align-items:center;gap:12px;margin:2rem 0;">' +
    '<div style="flex:1;border-top:1px ' + borderStyle + ' ' + accent + ';"></div>' +
    '<span style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#9ca3af;white-space:nowrap;">' + _esc(label) + '</span>' +
    '<div style="flex:1;border-top:1px ' + borderStyle + ' ' + accent + ';"></div>' +
    '</div>';
};

_RENDERERS['chip_group'] = function(b) {
  var uid    = Math.random().toString(36).substr(2, 6);
  var scroll = b.layout === 'scroll';
  var chips  = b.chips || [];
  var chipsHtml = chips.map(function(c) {
    var bg     = c.active ? (c.color || '#6366f1') : (c.color ? c.color + '18' : '#f3f4f6');
    var tc     = c.active ? '#fff' : (c.color || '#374151');
    var tag    = c.url ? 'a href="' + _esc(c.url) + '"' : 'span';
    var endTag = c.url ? 'a' : 'span';
    return '<' + tag + ' style="display:inline-flex;align-items:center;background:' + bg + ';color:' + tc + ';border-radius:99px;padding:4px 14px;font-size:12px;font-weight:500;text-decoration:none;white-space:nowrap;cursor:' + (c.url ? 'pointer' : 'default') + ';">' + _esc(c.label || '') + '</' + endTag + '>';
  }).join('');
  var wrap = scroll
    ? 'display:flex;flex-wrap:nowrap;overflow-x:auto;gap:8px;padding-bottom:4px;scrollbar-width:none;'
    : 'display:flex;flex-wrap:wrap;gap:8px;';
  return (b.label ? '<div style="font-size:12px;font-weight:600;color:#6b7280;margin-bottom:6px;">' + _esc(b.label) + '</div>' : '') +
    '<div style="' + wrap + 'margin:0.75rem 0;">' + chipsHtml + '</div>';
};

// ── Layout ────────────────────────────────────────────────────────────────────

_RENDERERS['columns'] = function(b) {
  var uid  = Math.random().toString(36).substr(2, 6);
  var cols = Math.min(6, Math.max(2, parseInt(b.cols || b.columns || 2)));
  var gap  = _esc(b.gap || '1.5rem');
  var alignMap = { top: 'flex-start', center: 'center', stretch: 'stretch' };
  var align = alignMap[b.align] || 'flex-start';
  var items = b.items || [];
  var colsHtml = '';
  for (var i = 0; i < items.length; i++) {
    var colBlocks = items[i].blocks || items[i].content || [];
    colsHtml += '<div class="col-col-' + uid + '">' + renderAtoms(colBlocks) + '</div>';
  }
  return '<style>' +
    '.col-wrap-' + uid + '{display:grid;grid-template-columns:repeat(' + cols + ',1fr);gap:' + gap + ';align-items:' + align + ';margin:1.5rem 0;}' +
    '@media(max-width:600px){.col-wrap-' + uid + '{grid-template-columns:1fr;}}' +
    '.col-col-' + uid + '{min-width:0;}' +
    '</style>' +
    '<div class="col-wrap-' + uid + '">' + colsHtml + '</div>';
};

// ── People ────────────────────────────────────────────────────────────────────

_RENDERERS['person_card'] = function(b) {
  var uid    = Math.random().toString(36).substr(2, 6);
  var accent = b.accent || '#6366f1';
  var photo  = b.photo_url || b.photo || '';
  var tags   = b.tags || [];
  var tagsHtml = tags.map(function(t) {
    return '<span style="background:#f3f4f6;color:#374151;border-radius:99px;padding:2px 10px;font-size:11px;font-weight:500;">' + _esc(t) + '</span>';
  }).join('');
  var linksHtml = '';
  if (b.email)    linksHtml += '<a href="mailto:' + _esc(b.email) + '" style="color:' + accent + ';font-size:12px;text-decoration:none;">✉ ' + _esc(b.email) + '</a>';
  if (b.linkedin) linksHtml += '<a href="' + _esc(b.linkedin) + '" target="_blank" style="color:' + accent + ';font-size:12px;text-decoration:none;margin-left:10px;">in LinkedIn</a>';
  return '<style>' +
    '.pc-' + uid + '{border:1px solid #e5e7eb;border-radius:12px;padding:20px;display:flex;gap:16px;align-items:flex-start;margin:0.5rem 0;background:#fff;}' +
    '.pc-avatar-' + uid + '{flex:0 0 56px;height:56px;border-radius:50%;object-fit:cover;background:' + accent + ';display:flex;align-items:center;justify-content:center;color:#fff;font-size:22px;font-weight:700;overflow:hidden;}' +
    '.pc-body-' + uid + '{flex:1;min-width:0;}' +
    '.pc-name-' + uid + '{font-size:16px;font-weight:700;color:#111827;margin-bottom:2px;}' +
    '.pc-role-' + uid + '{font-size:13px;color:#6b7280;margin-bottom:8px;}' +
    '.pc-bio-' + uid + '{font-size:13px;color:#374151;line-height:1.5;margin-bottom:8px;}' +
    '.pc-tags-' + uid + '{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px;}' +
    '</style>' +
    '<div class="pc-' + uid + '">' +
    '<div class="pc-avatar-' + uid + '">' + (photo ? '<img src="' + _esc(photo) + '" style="width:56px;height:56px;object-fit:cover;" />' : _esc((b.name || '?').charAt(0).toUpperCase())) + '</div>' +
    '<div class="pc-body-' + uid + '">' +
    '<div class="pc-name-' + uid + '">' + _esc(b.name || '') + '</div>' +
    (b.role ? '<div class="pc-role-' + uid + '">' + _esc(b.role) + '</div>' : '') +
    (b.bio  ? '<div class="pc-bio-'  + uid + '">' + _md(b.bio) + '</div>' : '') +
    (tagsHtml ? '<div class="pc-tags-' + uid + '">' + tagsHtml + '</div>' : '') +
    (linksHtml ? '<div>' + linksHtml + '</div>' : '') +
    '</div></div>';
};

// ── Agenda ────────────────────────────────────────────────────────────────────

_RENDERERS['agenda_block'] = function(b) {
  var uid    = Math.random().toString(36).substr(2, 6);
  var accent = b.accent || '#6366f1';
  var slots  = b.slots || [];
  var typeColors = { break: '#f3f4f6', keynote: '#ede9fe', workshop: '#dbeafe', panel: '#d1fae5', social: '#fef3c7' };
  var slotsHtml = slots.map(function(s) {
    var bg = typeColors[s.type] || '#fff';
    return '<div style="display:flex;gap:0;border-bottom:1px solid #f3f4f6;">' +
      '<div style="flex:0 0 72px;padding:12px 8px;font-size:12px;font-weight:600;color:' + accent + ';border-right:2px solid ' + accent + ';text-align:right;">' + _esc(s.time || '') + '</div>' +
      '<div style="flex:1;padding:10px 14px;background:' + bg + ';">' +
      '<div style="font-size:14px;font-weight:600;color:#111827;">' + _esc(s.title || '') + '</div>' +
      (s.speaker  ? '<div style="font-size:12px;color:#6b7280;margin-top:2px;">👤 ' + _esc(s.speaker) + '</div>' : '') +
      (s.location ? '<div style="font-size:12px;color:#6b7280;margin-top:2px;">📍 ' + _esc(s.location) + '</div>' : '') +
      (s.description ? '<div style="font-size:12px;color:#374151;margin-top:4px;">' + _esc(s.description) + '</div>' : '') +
      (s.type ? '<div style="font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;color:#9ca3af;margin-top:4px;">' + _esc(s.type) + '</div>' : '') +
      '</div></div>';
  }).join('');
  return '<style>.ag-' + uid + '{border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;margin:1.5rem 0;}</style>' +
    '<div class="ag-' + uid + '">' +
    (b.title || b.date ? '<div style="padding:12px 16px;background:#f9fafb;border-bottom:1px solid #e5e7eb;display:flex;justify-content:space-between;align-items:center;">' +
      (b.title ? '<span style="font-size:15px;font-weight:700;color:#111827;">' + _esc(b.title) + '</span>' : '<span></span>') +
      (b.date  ? '<span style="font-size:12px;color:#6b7280;">' + _esc(b.date) + '</span>' : '') +
      '</div>' : '') +
    slotsHtml + '</div>';
};

// ── Risk & Actions ────────────────────────────────────────────────────────────

_RENDERERS['risk_flag'] = function(b) {
  var uid  = Math.random().toString(36).substr(2, 6);
  var risks = b.risks || [];
  var levelCfg = {
    critical: { bg: '#fef2f2', border: '#ef4444', badge: '#ef4444', label: 'Critical' },
    high:     { bg: '#fff7ed', border: '#f97316', badge: '#f97316', label: 'High' },
    medium:   { bg: '#fefce8', border: '#eab308', badge: '#eab308', label: 'Medium' },
    low:      { bg: '#f0fdf4', border: '#22c55e', badge: '#22c55e', label: 'Low' }
  };
  var rowsHtml = risks.map(function(r) {
    var cfg = levelCfg[r.level] || levelCfg.medium;
    return '<div style="border-left:4px solid ' + cfg.border + ';background:' + cfg.bg + ';border-radius:0 8px 8px 0;padding:12px 16px;margin-bottom:10px;">' +
      '<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">' +
      '<span style="background:' + cfg.badge + ';color:#fff;border-radius:4px;padding:1px 8px;font-size:10px;font-weight:700;text-transform:uppercase;">' + cfg.label + '</span>' +
      '<span style="font-size:14px;font-weight:600;color:#111827;">' + _esc(r.title || '') + '</span>' +
      '</div>' +
      (r.description ? '<div style="font-size:13px;color:#374151;line-height:1.5;">' + _md(r.description) + '</div>' : '') +
      (r.mitigation  ? '<div style="font-size:12px;color:#6b7280;margin-top:6px;">💡 <em>' + _esc(r.mitigation) + '</em></div>' : '') +
      '</div>';
  }).join('');
  return (b.title ? '<div style="font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;color:#6b7280;margin-bottom:8px;">' + _esc(b.title) + '</div>' : '') + rowsHtml;
};

_RENDERERS['action_items'] = function(b) {
  var uid   = Math.random().toString(36).substr(2, 6);
  var items = b.items || [];
  var statusCfg = {
    done:        { icon: '✅', color: '#16a34a', bg: '#f0fdf4' },
    in_progress: { icon: '🔄', color: '#2563eb', bg: '#eff6ff' },
    open:        { icon: '⭕', color: '#9ca3af', bg: '#fff' }
  };
  var rowsHtml = items.map(function(item, i) {
    var cfg = statusCfg[item.status] || statusCfg.open;
    return '<tr style="background:' + (i % 2 === 0 ? '#fff' : '#f9fafb') + ';">' +
      '<td style="padding:10px 14px;font-size:13px;color:#111827;">' + _md(item.action || '') + '</td>' +
      '<td style="padding:10px 14px;font-size:12px;color:#6b7280;white-space:nowrap;">' + _esc(item.owner || '—') + '</td>' +
      '<td style="padding:10px 14px;font-size:12px;color:#6b7280;white-space:nowrap;">' + _esc(item.due || '—') + '</td>' +
      '<td style="padding:10px 14px;text-align:center;white-space:nowrap;"><span style="font-size:12px;color:' + cfg.color + ';background:' + cfg.bg + ';border-radius:99px;padding:2px 10px;font-weight:600;">' + cfg.icon + ' ' + _esc(item.status || 'open') + '</span></td>' +
      '</tr>';
  }).join('');
  return '<div style="margin:1.5rem 0;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;">' +
    (b.title ? '<div style="padding:10px 16px;background:#f9fafb;border-bottom:1px solid #e5e7eb;font-size:14px;font-weight:700;color:#111827;">' + _esc(b.title) + '</div>' : '') +
    '<table style="width:100%;border-collapse:collapse;">' +
    '<thead><tr style="background:#f3f4f6;">' +
    '<th style="padding:8px 14px;text-align:left;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;color:#6b7280;">Action</th>' +
    '<th style="padding:8px 14px;text-align:left;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;color:#6b7280;">Owner</th>' +
    '<th style="padding:8px 14px;text-align:left;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;color:#6b7280;">Due</th>' +
    '<th style="padding:8px 14px;text-align:left;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;color:#6b7280;">Status</th>' +
    '</tr></thead>' +
    '<tbody>' + rowsHtml + '</tbody></table></div>';
};


