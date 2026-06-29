// atoms_ai.gs — AI-native atoms powered by Vertex AI (Gemini)
//
// Config (set once in Apps Script → Project Settings → Script Properties):
//   VERTEX_PROJECT_ID  — your GCP project ID
//   VERTEX_LOCATION    — optional, defaults to us-central1
//   VERTEX_MODEL       — optional, defaults to gemini-2.0-flash-001
//
// Auth uses ScriptApp.getOAuthToken() — no API key required.

// ── Server-side Vertex AI helper ──────────────────────────────────────────────
function _vertexGenerate(userPrompt, bodyText, opts) {
  opts = opts || {};
  var props      = PropertiesService.getScriptProperties();
  var projectId  = props.getProperty('VERTEX_PROJECT_ID');
  if (!projectId) throw new Error('VERTEX_PROJECT_ID not set in Script Properties');

  var location   = props.getProperty('VERTEX_LOCATION') || opts.location || 'us-central1';
  var model      = props.getProperty('VERTEX_MODEL')    || opts.model    || 'gemini-2.0-flash-001';
  var maxTokens  = opts.maxTokens  || 1024;
  var temperature = opts.temperature !== undefined ? opts.temperature : 0.2;

  var endpoint = 'https://' + location + '-aiplatform.googleapis.com/v1/projects/' +
                 projectId + '/locations/' + location +
                 '/publishers/google/models/' + model + ':generateContent';

  var payload = {
    contents: [{ role: 'user', parts: [{ text: userPrompt + (bodyText ? '\n\n' + bodyText : '') }] }],
    generationConfig: { maxOutputTokens: maxTokens, temperature: temperature }
  };

  var response = UrlFetchApp.fetch(endpoint, {
    method: 'post',
    headers: { 'Authorization': 'Bearer ' + ScriptApp.getOAuthToken() },
    contentType: 'application/json',
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  });

  var result = JSON.parse(response.getContentText());
  if (result.error) throw new Error(result.error.message);
  return result.candidates[0].content.parts[0].text;
}

// ── Simple markdown → HTML (for AI output rendering) ─────────────────────────
function _mdToHtml(text) {
  if (!text) return '';
  var lines = text.split('\n');
  var html  = '';
  var inList = false;

  for (var i = 0; i < lines.length; i++) {
    var line = lines[i];

    // Headings
    if (/^### /.test(line)) {
      if (inList) { html += '</ul>'; inList = false; }
      html += '<div style="font-size:0.82rem;font-weight:700;color:var(--text);margin:10px 0 4px;">' + _esc(line.replace(/^### /, '')) + '</div>';
      continue;
    }
    if (/^## /.test(line)) {
      if (inList) { html += '</ul>'; inList = false; }
      html += '<div style="font-size:0.88rem;font-weight:700;color:var(--text);margin:12px 0 4px;">' + _esc(line.replace(/^## /, '')) + '</div>';
      continue;
    }
    if (/^# /.test(line)) {
      if (inList) { html += '</ul>'; inList = false; }
      html += '<div style="font-size:0.95rem;font-weight:800;color:var(--text);margin:14px 0 6px;">' + _esc(line.replace(/^# /, '')) + '</div>';
      continue;
    }

    // Bullet points (•, -, *)
    if (/^[\•\-\*]\s+/.test(line)) {
      if (!inList) { html += '<ul style="margin:4px 0 4px 0;padding:0;list-style:none;">'; inList = true; }
      var item = line.replace(/^[\•\-\*]\s+/, '');
      html += '<li style="display:flex;gap:8px;padding:3px 0;font-size:0.82rem;color:var(--text);">' +
              '<span style="color:var(--accent,#6366f1);flex-shrink:0;">▸</span>' +
              '<span>' + _inlineMd(_esc(item)) + '</span></li>';
      continue;
    }

    // Checkbox-style action items
    if (/^\[\s*\]\s+/.test(line) || /^☐\s+/.test(line)) {
      if (!inList) { html += '<ul style="margin:4px 0 4px 0;padding:0;list-style:none;">'; inList = true; }
      var item = line.replace(/^\[\s*\]\s+/, '').replace(/^☐\s+/, '');
      html += '<li style="display:flex;gap:8px;align-items:flex-start;padding:3px 0;font-size:0.82rem;color:var(--text);">' +
              '<span style="flex-shrink:0;margin-top:1px;">☐</span>' +
              '<span>' + _inlineMd(_esc(item)) + '</span></li>';
      continue;
    }

    if (inList) { html += '</ul>'; inList = false; }

    // Blank line
    if (line.trim() === '') {
      html += '<div style="height:6px;"></div>';
      continue;
    }

    // Normal paragraph
    html += '<p style="font-size:0.82rem;color:var(--text);margin:3px 0;line-height:1.55;">' + _inlineMd(_esc(line)) + '</p>';
  }

  if (inList) html += '</ul>';
  return html;
}

function _inlineMd(escaped) {
  // **bold** and *italic* on already-escaped text
  return escaped
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>');
}

// ── doc_ai_summary ────────────────────────────────────────────────────────────
// Opens a Google Doc, sends its text to Vertex AI Gemini, renders the response.
// Fields:
//   doc_id        — Google Doc ID (required in GAS; mock shown without it)
//   prompt        — instruction sent to Gemini before the doc text
//   title         — override card title (defaults to doc name)
//   model         — Gemini model override (defaults to VERTEX_MODEL property)
//   max_chars     — max doc characters sent to Gemini (default 12000)
//   accent        — colour accent
//   show_meta     — show word count + link (default true)
_RENDERERS['doc_ai_summary'] = function(b) {
  var docId    = b.doc_id   || '';
  var prompt   = b.prompt   || 'Summarise this document. Lead with the 3 most important points as bullet points, then list any action items you can identify. Be concise.';
  var accent   = b.accent   || 'var(--accent,#6366f1)';
  var maxChars = b.max_chars || 12000;
  var showMeta = b.show_meta !== false;

  var cardTitle = '', summary = '', docUrl = '', wordCount = 0;
  var errorMsg  = null;

  if (typeof DocumentApp !== 'undefined' && docId) {
    try {
      var doc   = DocumentApp.openById(docId);
      cardTitle = b.title || doc.getName();
      docUrl    = doc.getUrl();
      var text  = doc.getBody().getText();
      wordCount = text.split(/\s+/).filter(function(w) { return w.length > 0; }).length;
      var body  = text.length > maxChars ? text.substring(0, maxChars) + '\n[document truncated]' : text;
      summary   = _vertexGenerate(prompt, body, { model: b.model });
    } catch (err) { errorMsg = err.message; }
  } else {
    cardTitle = b.title || 'Q3 Strategy Brief';
    docUrl    = '#';
    wordCount = 2847;
    summary   = '**Key Points:**\n• Revenue target set at €2.4M with three product lines launching in July\n• Engineering focus shifts to reliability — 99.9% uptime SLA commitment\n• Headcount freeze lifted; 4 new hires approved for Q3\n\n**Action Items:**\n- [ ] CEO sign-off on headcount plan by June 30\n- [ ] Design to deliver mockups by July 5\n- [ ] Finance to update projections in shared sheet';
  }

  var readMins = Math.max(1, Math.round(wordCount / 200));

  var metaHtml = '';
  if (showMeta && !errorMsg) {
    metaHtml = '<div style="display:flex;align-items:center;gap:12px;margin-top:12px;padding-top:10px;border-top:1px solid var(--border,#e2e8f0);">' +
               '<span style="font-size:0.72rem;color:var(--muted);">📄 ' + wordCount.toLocaleString() + ' words · ~' + readMins + ' min read</span>' +
               (docUrl && docUrl !== '#' ? '<a href="' + _esc(docUrl) + '" target="_top" style="margin-left:auto;font-size:0.72rem;color:' + _esc(accent) + ';text-decoration:none;font-weight:600;">Open doc →</a>' : '') +
               '</div>';
  }

  var body = errorMsg
    ? '<div style="font-size:0.82rem;color:var(--red);margin-top:8px;">Error: ' + _esc(errorMsg) + '</div>'
    : '<div style="margin-top:10px;">' + _mdToHtml(summary) + '</div>';

  return '<div class="asw-native-card">' +
         '<div class="asw-native-header">' +
         '<span class="asw-native-header-icon">🤖</span> ' +
         _esc(cardTitle) +
         '<span style="margin-left:auto;font-size:0.7rem;font-weight:400;color:var(--muted);background:var(--border,#e2e8f0);padding:2px 7px;border-radius:99px;">Vertex AI</span>' +
         '</div>' +
         body +
         metaHtml +
         '</div>';
};

// ── ai_build_trace ────────────────────────────────────────────────────────────
// Provenance footer injected into every AI-built page by callGemini().
// Fields:
//   model           — Gemini model ID used (e.g. "gemini-2.5-flash")
//   prompt_tokens   — input token count
//   thinking_tokens — internal reasoning tokens (Gemini 2.5 hybrid thinking)
//   output_tokens   — response token count (excludes thinking)
//   total_tokens    — prompt + thinking + output
_RENDERERS['ai_build_trace'] = function(b) {
  var model    = b.model          || 'gemini';
  var pin      = b.prompt_tokens  || 0;
  var pthink   = b.thinking_tokens || 0;
  var pout     = b.output_tokens  || 0;
  var ptotal   = b.total_tokens   || 0;

  function fmt(n) { return n.toLocaleString ? n.toLocaleString() : String(n); }

  // Stacked bar: prompt | thinking | output (each as % of total)
  var pctIn    = ptotal > 0 ? Math.round((pin    / ptotal) * 100) : 0;
  var pctThink = ptotal > 0 ? Math.round((pthink / ptotal) * 100) : 0;
  var pctOut   = ptotal > 0 ? Math.max(0, 100 - pctIn - pctThink) : 0;

  var bar = '';
  if (pctIn > 0)    bar += '<div style="width:' + pctIn    + '%;height:100%;background:#6366f1;"></div>';
  if (pctThink > 0) bar += '<div style="width:' + pctThink + '%;height:100%;background:#a78bfa;"></div>';
  if (pctOut > 0)   bar += '<div style="width:' + pctOut   + '%;height:100%;background:#38bdf8;"></div>';

  var chips = _aiBuildChip('in', fmt(pin), '#6366f1');
  if (pthink > 0) chips += _aiBuildChip('thinking', fmt(pthink), '#a78bfa');
  chips += _aiBuildChip('out', fmt(pout), '#38bdf8');
  chips += _aiBuildChip('total', fmt(ptotal), 'var(--muted,#94a3b8)');

  return '<div style="margin-top:32px;padding:14px 16px;background:rgba(99,102,241,0.04);' +
         'border:1px solid rgba(99,102,241,0.12);border-radius:10px;">' +

         // Row 1: icon + model + bar legend
         '<div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">' +
         '<div style="width:24px;height:24px;background:linear-gradient(135deg,#6366f1,#38bdf8);' +
         'border-radius:5px;display:flex;align-items:center;justify-content:center;font-size:12px;flex-shrink:0;">⬡</div>' +
         '<div style="font-size:0.72rem;font-weight:700;color:var(--text,#1e293b);letter-spacing:0.04em;">' + _esc(model) + '</div>' +
         '<div style="font-size:0.65rem;color:var(--muted,#94a3b8);">Built with Vertex AI</div>' +
         '<div style="margin-left:auto;width:100px;height:5px;background:rgba(99,102,241,0.1);border-radius:3px;overflow:hidden;display:flex;">' + bar + '</div>' +
         '</div>' +

         // Row 2: token chips
         '<div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:10px;">' + chips + '</div>' +

         '</div>';
};

function _aiBuildChip(label, val, color) {
  return '<div style="padding:3px 9px;background:rgba(255,255,255,0.45);border:1px solid rgba(99,102,241,0.12);' +
         'border-radius:5px;font-size:0.68rem;color:var(--muted,#94a3b8);font-family:\'Courier New\',monospace;">' +
         '<span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:' + color + ';margin-right:4px;vertical-align:middle;"></span>' +
         label + ' <strong style="color:var(--text,#1e293b);">' + val + '</strong></div>';
}

// ── gemini_prompt ─────────────────────────────────────────────────────────────
// Inline AI page builder — embeds the builder UI as an atom in any page.
// Calls server-side callGemini() via google.script.run.
// Fields:
//   label        — heading above the textarea (optional)
//   placeholder  — textarea hint text (optional)
//   accent       — button/border accent colour (optional, default indigo)
_RENDERERS['gemini_prompt'] = function(b) {
  var label  = b.label       || 'Build a page with AI';
  var hint   = b.placeholder || 'Describe the page you want to build…';
  var accent = b.accent      || '#6366f1';

  var uid = 'gp' + Math.random().toString(36).slice(2, 8);

  return '<div style="background:rgba(99,102,241,0.04);border:1px solid rgba(99,102,241,0.14);' +
         'border-radius:12px;padding:20px 22px;margin:4px 0;">' +

         '<div style="display:flex;align-items:center;gap:8px;margin-bottom:14px;">' +
         '<div style="width:22px;height:22px;background:linear-gradient(135deg,#6366f1,#38bdf8);' +
         'border-radius:5px;display:flex;align-items:center;justify-content:center;font-size:11px;">⬡</div>' +
         '<span style="font-size:0.82rem;font-weight:700;color:var(--text,#1e293b);letter-spacing:0.03em;">' +
         _esc(label) + '</span>' +
         '<span style="margin-left:auto;font-size:0.65rem;color:var(--muted,#94a3b8);background:rgba(99,102,241,0.08);' +
         'padding:2px 7px;border-radius:99px;font-weight:500;">Vertex AI · gemini-2.5-flash</span>' +
         '</div>' +

         '<textarea id="' + uid + 't" rows="4" placeholder="' + _esc(hint) + '"' +
         ' style="width:100%;background:rgba(255,255,255,0.6);border:1px solid rgba(99,102,241,0.2);' +
         'border-radius:8px;padding:10px 12px;font-size:0.82rem;font-family:inherit;' +
         'color:var(--text,#1e293b);resize:vertical;outline:none;box-sizing:border-box;"></textarea>' +

         '<div style="display:flex;align-items:center;gap:10px;margin-top:10px;">' +
         '<button id="' + uid + 'b" onclick="_gpGenerate(\'' + uid + '\')"' +
         ' style="background:linear-gradient(135deg,' + _esc(accent) + ',#38bdf8);color:#fff;' +
         'border:none;border-radius:7px;padding:9px 18px;font-size:0.82rem;font-weight:600;' +
         'cursor:pointer;font-family:inherit;">Generate →</button>' +
         '<span id="' + uid + 's" style="font-size:0.78rem;color:var(--muted,#94a3b8);"></span>' +
         '</div>' +

         '<div id="' + uid + 'r" style="display:none;margin-top:12px;">' +
         '<div id="' + uid + 'rchips" style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px;"></div>' +
         '<a id="' + uid + 'rlink" href="#" target="_top"' +
         ' style="display:block;background:rgba(56,189,248,0.08);border:1px solid rgba(56,189,248,0.25);' +
         'border-radius:7px;padding:10px 14px;font-size:0.8rem;color:#0ea5e9;' +
         'text-decoration:none;font-weight:600;text-align:center;">Open Generated Page →</a>' +
         '</div>' +

         '<div id="' + uid + 'e" style="display:none;margin-top:10px;padding:10px 12px;' +
         'background:rgba(239,68,68,0.06);border:1px solid rgba(239,68,68,0.2);' +
         'border-radius:7px;font-size:0.78rem;color:#ef4444;"></div>' +

         '</div>';
};

// ── multi_doc_ai_brief ────────────────────────────────────────────────────────
// Array of doc IDs → one AI summary card per doc. For meeting prep / briefing packs.
// Fields:
//   docs          — array of { doc_id, title?, prompt? }
//   default_prompt — fallback prompt for docs without their own
//   accent        — colour accent
_RENDERERS['multi_doc_ai_brief'] = function(b) {
  var docs          = b.docs || [];
  var defaultPrompt = b.default_prompt || 'In 2-3 sentences, summarise what this document is about and the single most important point.';
  var accent        = b.accent || 'var(--accent,#6366f1)';

  if (!docs.length) {
    return '<div class="asw-native-card"><div style="font-size:0.82rem;color:var(--muted);">No documents provided.</div></div>';
  }

  var cards = '';
  for (var i = 0; i < docs.length; i++) {
    var d         = docs[i];
    var docId     = d.doc_id || '';
    var prompt    = d.prompt || defaultPrompt;
    var cardTitle = d.title  || docId;
    var summary   = '';
    var docUrl    = '';
    var errorMsg  = null;

    if (typeof DocumentApp !== 'undefined' && docId) {
      try {
        var doc   = DocumentApp.openById(docId);
        cardTitle = d.title || doc.getName();
        docUrl    = doc.getUrl();
        var text  = doc.getBody().getText();
        var body  = text.length > 8000 ? text.substring(0, 8000) + '\n[truncated]' : text;
        summary   = _vertexGenerate(prompt, body, { model: b.model, maxTokens: 256 });
      } catch (err) { errorMsg = err.message; }
    } else {
      cardTitle = d.title || 'Document ' + (i + 1);
      summary   = 'This document covers the key strategic decisions for the upcoming quarter, focusing on growth and operational efficiency.';
    }

    cards += '<div style="padding:12px 0;' + (i > 0 ? 'border-top:1px solid var(--border,#e2e8f0);' : '') + '">' +
             '<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">' +
             '<span style="font-size:0.85rem;font-weight:700;color:var(--text);">' + _esc(cardTitle) + '</span>' +
             (docUrl ? '<a href="' + _esc(docUrl) + '" target="_top" style="margin-left:auto;font-size:0.7rem;color:' + _esc(accent) + ';text-decoration:none;white-space:nowrap;">Open →</a>' : '') +
             '</div>' +
             (errorMsg
               ? '<div style="font-size:0.78rem;color:var(--red);">Error: ' + _esc(errorMsg) + '</div>'
               : '<div style="font-size:0.8rem;color:var(--muted);line-height:1.55;">' + _inlineMd(_esc(summary)) + '</div>') +
             '</div>';
  }

  return '<div class="asw-native-card">' +
         '<div class="asw-native-header"><span class="asw-native-header-icon">📚</span> Document Brief<span style="margin-left:auto;font-size:0.7rem;font-weight:400;color:var(--muted);background:var(--border,#e2e8f0);padding:2px 7px;border-radius:99px;">Vertex AI</span></div>' +
         cards +
         '</div>';
};
