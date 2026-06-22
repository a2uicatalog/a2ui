# A2UI GAS Renderer — Full Source

**Deployment ID:** `YOUR_DEPLOYMENT_ID`

**Generator URL:** `https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/exec`

**Deploy command:** `./deploy.sh "description"`

**How it works:** `?p=BASE64` → `Code.js` decodes → `renderAtoms()` in `atom.gs` → `AtomPage.html` shell → rendered page

---

## Code.js — doGet / doPost / base64 decode / entry point

```javascript
/**
 * A2UI Gem Renderer
 *
 * Three modes:
 *   GET  ?p=BASE64   — decode base64 payload, render atoms (small schemas, shareable URL)
 *   POST ?p=JSON     — read raw JSON from form field (large schemas, no URL limit)
 *   GET  (no params) — serve the helper UI for pasting / encoding JSON
 */

function doGet(e) {
  var p = e && e.parameter && e.parameter.p;
  if (p) return _renderFromParam(p);
  return HtmlService.createHtmlOutputFromFile('Index')
    .setTitle('A2UI — Page Generator')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

function doPost(e) {
  var raw = e.parameter && e.parameter.p;
  if (!raw && e.postData) raw = e.postData.contents;
  if (!raw) return doGet(e);
  try {
    var payload = JSON.parse(raw);
    return _renderFromPayload(payload);
  } catch (err) {
    // Fallback: treat as base64
    return _renderFromParam(raw);
  }
}

function _renderFromParam(encoded) {
  try {
    var bytes   = Utilities.base64Decode(encoded, Utilities.Charset.UTF_8);
    var json    = Utilities.newBlob(bytes).getDataAsString();
    return _renderFromPayload(JSON.parse(json));
  } catch (err) {
    return _errorPage(err.message);
  }
}

function _renderFromPayload(payload) {
  try {
    var blocks  = Array.isArray(payload) ? payload : (payload.blocks || []);
    var title   = (Array.isArray(payload) ? '' : payload.title) || 'A2UI Page';
    var theme   = (Array.isArray(payload) ? 'light' : payload.theme) || 'light';
    var content = renderAtoms(blocks, { theme: theme });
    var tmpl       = HtmlService.createTemplateFromFile('AtomPage');
    tmpl.title     = title;
    tmpl.content   = content;
    tmpl.theme     = theme;
    tmpl.sidebar   = false;
    tmpl.schemaJson = JSON.stringify(payload).replace(/<\//g, '<\\/');
    return tmpl.evaluate()
      .setTitle(title)
      .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
  } catch (err) {
    return _errorPage(err.message);
  }
}

function _errorPage(msg) {
  return HtmlService.createHtmlOutput(
    '<body style="font-family:monospace;padding:40px;background:#0a0f1e;color:#ef4444">' +
    '<h2>Render error</h2><pre>' + msg + '</pre>' +
    '<p><a href="' + ScriptApp.getService().getUrl() + '" style="color:#60a5fa">← Back to generator</a></p>' +
    '</body>'
  ).setTitle('Render error');
}

/** Called by AtomPage.html to include partial files. */
function include(filename) {
  return HtmlService.createHtmlOutputFromFile(filename).getContent();
}

/**
 * Export the renderer script to the deployer's Drive under "a2ui apps script exports",
 * shared with anyone-with-link so users can open it and File > Make a copy.
 * Returns { url, name } on success or { error } on failure.
 */
function exportScript() {
  try {
    var folderName = 'a2ui apps script exports';
    var copyName   = 'A2UI Schema Renderer';

    // Get or create the exports folder
    var fi = DriveApp.getFoldersByName(folderName);
    var folder = fi.hasNext() ? fi.next() : DriveApp.createFolder(folderName);

    // Reuse existing copy if already exported (avoid duplicates)
    var existing = folder.getFilesByName(copyName);
    var copy = existing.hasNext() ? existing.next() : DriveApp.getFileById(ScriptApp.getScriptId()).makeCopy(copyName, folder);

    // Share with anyone who has the link (view only — they can File > Make a copy)
    copy.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);

    return { url: copy.getUrl(), name: copyName };
  } catch (e) {
    return { error: e.toString() };
  }
}
```

---

## Index.html — generator UI (paste JSON → get URL)

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <base target="_top">
  <title>A2UI — Page Generator</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after { box-sizing:border-box; margin:0; padding:0; }
    :root {
      --bg:     #04060f;
      --bg2:    #090d1a;
      --bg3:    #0f1626;
      --border: rgba(255,255,255,0.08);
      --text:   #e2e8f0;
      --muted:  #64748b;
      --cyan:   #00f2ff;
      --green:  #34d399;
      --red:    #f87171;
      --mono:   'JetBrains Mono', monospace;
    }
    html, body {
      height:100%; background:var(--bg); color:var(--text);
      font-family:'Inter',system-ui,sans-serif;
    }
    .page {
      max-width:780px; margin:0 auto; padding:48px 24px 80px;
    }

    /* ── Header ── */
    .eyebrow {
      font-size:10px; font-weight:700; letter-spacing:0.2em;
      text-transform:uppercase; color:var(--muted); margin-bottom:14px;
    }
    h1 {
      font-size:clamp(28px,5vw,44px); font-weight:800; line-height:1.15;
      margin-bottom:12px;
    }
    h1 span { color:var(--cyan); }
    .sub {
      font-size:15px; color:var(--muted); line-height:1.7; max-width:560px;
      margin-bottom:40px;
    }

    /* ── Step pills ── */
    .steps {
      display:flex; gap:10px; flex-wrap:wrap; margin-bottom:36px;
    }
    .step {
      display:flex; align-items:center; gap:8px;
      background:var(--bg2); border:1px solid var(--border);
      border-radius:8px; padding:8px 14px;
      font-size:12px; font-weight:500; color:var(--muted);
    }
    .step-num {
      width:20px; height:20px; border-radius:50%;
      background:rgba(0,242,255,0.12); color:var(--cyan);
      font-size:10px; font-weight:800; display:flex;
      align-items:center; justify-content:center; flex-shrink:0;
    }

    /* ── Textarea section ── */
    .section-label {
      font-size:11px; font-weight:700; letter-spacing:0.12em;
      text-transform:uppercase; color:var(--muted); margin-bottom:8px;
    }
    textarea {
      width:100%; height:280px;
      background:var(--bg2); border:1px solid var(--border);
      border-radius:10px; padding:16px; color:var(--text);
      font-family:var(--mono); font-size:12px; line-height:1.6;
      resize:vertical; outline:none; transition:border-color .15s;
    }
    textarea:focus { border-color:rgba(0,242,255,0.4); }
    textarea::placeholder { color:var(--muted); }

    /* ── Buttons ── */
    .btn-row { display:flex; gap:10px; margin-top:12px; flex-wrap:wrap; }
    .btn {
      padding:10px 22px; border-radius:8px; font-size:13px; font-weight:600;
      cursor:pointer; border:none; font-family:inherit; transition:all .15s;
    }
    .btn-primary {
      background:var(--cyan); color:#04060f;
    }
    .btn-primary:hover { opacity:.88; }
    .btn-ghost {
      background:transparent; color:var(--muted);
      border:1px solid var(--border);
    }
    .btn-ghost:hover { color:var(--text); border-color:rgba(255,255,255,0.2); }

    /* ── URL output ── */
    #url-row { display:none; margin-top:16px; }
    .url-box {
      display:flex; align-items:center; gap:8px;
      background:var(--bg3); border:1px solid rgba(0,242,255,0.25);
      border-radius:8px; padding:10px 14px;
    }
    .url-text {
      flex:1; font-family:var(--mono); font-size:11px;
      color:var(--cyan); overflow:hidden; text-overflow:ellipsis;
      white-space:nowrap;
    }
    .copy-btn {
      padding:4px 12px; border-radius:5px; background:rgba(0,242,255,0.1);
      border:1px solid rgba(0,242,255,0.3); color:var(--cyan);
      font-size:11px; font-weight:600; cursor:pointer; font-family:inherit;
      flex-shrink:0; transition:all .15s;
    }
    .copy-btn:hover { background:rgba(0,242,255,0.2); }
    .open-btn {
      padding:4px 12px; border-radius:5px; background:var(--cyan);
      border:none; color:#04060f;
      font-size:11px; font-weight:700; cursor:pointer; font-family:inherit;
      flex-shrink:0; text-decoration:none; display:inline-block;
    }

    /* ── Error ── */
    #error-msg {
      display:none; margin-top:10px; padding:10px 14px;
      background:rgba(248,113,113,0.1); border:1px solid rgba(248,113,113,0.3);
      border-radius:8px; color:var(--red); font-size:12px; font-family:var(--mono);
    }

    /* ── Divider ── */
    hr { border:none; border-top:1px solid var(--border); margin:40px 0; }

    /* ── Gem tip ── */
    .tip-card {
      background:var(--bg2); border:1px solid var(--border);
      border-radius:12px; padding:20px 24px;
    }
    .tip-card h3 { font-size:13px; font-weight:700; margin-bottom:10px; color:var(--text); }
    .tip-card p  { font-size:12px; color:var(--muted); line-height:1.7; margin-bottom:8px; }
    .tip-card code {
      font-family:var(--mono); font-size:11px;
      background:var(--bg3); border:1px solid var(--border);
      padding:1px 6px; border-radius:3px; color:var(--cyan);
    }
    .gem-link {
      display:inline-flex; align-items:center; gap:6px;
      margin-top:12px; padding:7px 16px; border-radius:7px;
      background:rgba(0,242,255,0.08); border:1px solid rgba(0,242,255,0.2);
      color:var(--cyan); font-size:12px; font-weight:600;
      text-decoration:none; transition:all .15s;
    }
    .gem-link:hover { background:rgba(0,242,255,0.14); }

    /* ── Sample ── */
    .sample-toggle {
      font-size:11px; color:var(--muted); cursor:pointer;
      border:none; background:none; font-family:inherit; padding:0;
      text-decoration:underline; text-decoration-style:dotted;
      margin-top:6px; display:block;
    }
    .sample-toggle:hover { color:var(--text); }
  </style>
</head>
<body>
<div class="page">

  <div class="eyebrow">A2UI · Page Generator</div>
  <h1>Paste blocks.<br><span>Get a page.</span></h1>
  <p class="sub">
    Use the A2UI Gemini Gem to describe a page in plain language.
    Copy the JSON it generates, paste it below, and click <strong style="color:var(--text)">Generate</strong>
    to get a shareable URL.
  </p>

  <div class="steps">
    <div class="step"><span class="step-num">1</span> Open the A2UI Gem in Gemini</div>
    <div class="step"><span class="step-num">2</span> Describe the page you want</div>
    <div class="step"><span class="step-num">3</span> Copy the JSON output</div>
    <div class="step"><span class="step-num">4</span> Paste below → Generate</div>
  </div>

  <div class="section-label">Your A2UI JSON</div>
  <textarea id="json-input" placeholder='{
  "title": "My Page",
  "theme": "light",
  "blocks": [
    { "type": "heading", "level": 1, "text": "Hello World" },
    { "type": "body", "text": "This page was generated by **A2UI**." },
    { "type": "callout", "icon": "💡", "text": "Paste your Gem output here." }
  ]
}'></textarea>

  <button class="sample-toggle" onclick="loadSample()">Load a sample →</button>

  <div class="btn-row">
    <button class="btn btn-primary" onclick="generate()">Generate Page</button>
    <button class="btn btn-ghost"   onclick="clearAll()">Clear</button>
    <button class="btn btn-ghost"   onclick="exportScript()" id="export-btn">Export to Drive ↗</button>
  </div>

  <div id="export-row" style="display:none;margin-top:12px;">
    <div class="url-box">
      <span class="url-text" id="export-text"></span>
      <a class="open-btn" id="export-link" href="#" target="_top">Open in Apps Script →</a>
    </div>
    <p style="font-size:11px;color:var(--muted);margin-top:8px;">
      In Apps Script: <strong style="color:var(--text)">File → Make a copy</strong> to save the renderer to your own Drive.
    </p>
  </div>

  <div id="error-msg"></div>

  <div id="url-row">
    <div class="url-box">
      <span class="url-text" id="url-text"></span>
      <button class="copy-btn" onclick="copyUrl()">Copy</button>
      <a class="open-btn" id="open-link" href="#" target="_top">Open →</a>
    </div>
  </div>

  <hr>

  <div class="tip-card">
    <h3>🤖 Don't have the Gem yet?</h3>
    <p>
      The <strong style="color:var(--text)">A2UI Page Builder</strong> Gem knows the full atom schema.
      Ask it to build any page in plain language — it returns a JSON block list ready to paste here.
    </p>
    <p>
      Try: <code>"a 3-module ITIL 5 learning summary with a quiz and an XP bar"</code>
    </p>
    <a class="gem-link" href="https://gemini.google.com/gems/view/a2ui-page-builder" target="_top">
      ✦ Open A2UI Gem in Gemini →
    </a>
  </div>

</div>

<script>
  var BASE_URL = 'https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/exec';
  var URL_LIMIT = 6000; // chars — stay well under GAS query string limit

  function generate() {
    var raw = document.getElementById('json-input').value.trim();
    var err = document.getElementById('error-msg');
    err.style.display = 'none';

    if (!raw) { showError('Paste your JSON first.'); return; }

    var sanitized = raw.replace(/"(?:[^"\\]|\\.)*"/g, function(m) {
      return m.replace(/\n/g, '\\n').replace(/\r/g, '\\r').replace(/\t/g, '\\t');
    });

    var parsed;
    try {
      parsed = JSON.parse(sanitized);
    } catch (e) {
      showError('Invalid JSON: ' + e.message); return;
    }

    try {
      var clean   = JSON.stringify(parsed);
      var encoded = btoa(unescape(encodeURIComponent(clean)));
      var url     = BASE_URL + '?p=' + encodeURIComponent(encoded);

      if (url.length <= URL_LIMIT) {
        // Small schema — shareable URL
        showUrl(url, true);
      } else {
        // Large schema — POST to avoid URL length limit
        showUrl(null, false);
        _postRender(clean);
      }
    } catch (e) {
      showError('Encoding failed: ' + e.message);
    }
  }

  function _postRender(json) {
    var form = document.createElement('form');
    form.method = 'post';
    form.action = BASE_URL;
    form.target = '_blank';
    var inp = document.createElement('input');
    inp.type = 'hidden';
    inp.name = 'p';
    inp.value = json;
    form.appendChild(inp);
    document.body.appendChild(form);
    form.submit();
    document.body.removeChild(form);
  }

  function showUrl(url, shareable) {
    var row = document.getElementById('url-row');
    if (url) {
      document.getElementById('url-text').textContent = url;
      document.getElementById('open-link').href = url;
      document.getElementById('open-link').style.display = 'inline-block';
      document.querySelector('.copy-btn').style.display = 'inline-block';
    } else {
      document.getElementById('url-text').textContent = 'Large schema — opening via POST (not shareable as URL)';
      document.getElementById('open-link').style.display = 'none';
      document.querySelector('.copy-btn').style.display = 'none';
    }
    row.style.display = 'block';
    row.scrollIntoView({ behavior: 'smooth' });
  }

  function copyUrl() {
    var url = document.getElementById('url-text').textContent;
    navigator.clipboard.writeText(url).then(function() {
      var btn = document.querySelector('.copy-btn');
      btn.textContent = 'Copied!';
      setTimeout(function() { btn.textContent = 'Copy'; }, 1500);
    });
  }

  function showError(msg) {
    var el = document.getElementById('error-msg');
    el.textContent = msg;
    el.style.display = 'block';
  }

  function clearAll() {
    document.getElementById('json-input').value = '';
    document.getElementById('url-row').style.display = 'none';
    document.getElementById('error-msg').style.display = 'none';
  }

  var SAMPLE = JSON.stringify({
    "title": "Cloud Certification Prep",
    "theme": "light",
    "blocks": [
      { "type": "heading", "level": 1, "text": "GCP Professional Cloud Architect" },
      { "type": "body", "text": "A structured **5-day sprint** to clear the certification. Focus on high-weight domains first." },
      { "type": "alert_banner", "variant": "info", "text": "Exam is 2 hours · 60 questions · 70% to pass" },
      { "type": "xp_bar", "level_label": "Week 1 — Core Infrastructure", "xp_current": 3, "xp_next": 5 },
      { "type": "bullet_list", "items": [
          { "label": "Day 1", "text": "Compute Engine, GKE, Cloud Run — know when to use each" },
          { "label": "Day 2", "text": "VPC, firewall rules, load balancing, Cloud Armor" },
          { "label": "Day 3", "text": "Storage: GCS, Bigtable, Spanner, Firestore decision tree" },
          { "label": "Day 4", "text": "IAM, service accounts, org policies, CMEK" },
          { "label": "Day 5", "text": "Case studies — practice all 4 official ones" }
      ]},
      { "type": "quiz_question",
        "question": "A client needs a relational database that scales horizontally across regions with strong consistency. Which product?",
        "options": ["Cloud SQL", "Bigtable", "Cloud Spanner", "Firestore"],
        "correct": 2,
        "explanation": "Cloud Spanner is the only globally distributed, strongly consistent relational database on GCP." },
      { "type": "hint_reveal", "label": "Remember the decision tree", "hint": "SQL + global + strong consistency = Spanner. SQL + regional = Cloud SQL. NoSQL + wide column = Bigtable. NoSQL + document = Firestore." },
      { "type": "achievement_badge", "title": "Domain 1 Complete", "icon": "🏗️", "color": "#1a73e8", "description": "Core infrastructure foundations locked in" },
      { "type": "cta_button", "label": "Take the practice exam →", "url": "https://cloud.google.com/certification/cloud-architect" }
    ]
  }, null, 2);

  function loadSample() {
    document.getElementById('json-input').value = SAMPLE;
    document.getElementById('url-row').style.display = 'none';
    document.getElementById('error-msg').style.display = 'none';
  }

  function exportScript() {
    var btn = document.getElementById('export-btn');
    btn.textContent = 'Exporting…';
    btn.disabled = true;
    google.script.run
      .withSuccessHandler(function(res) {
        btn.textContent = 'Export to Drive ↗';
        btn.disabled = false;
        if (res.error) { showError('Export failed: ' + res.error); return; }
        var row = document.getElementById('export-row');
        document.getElementById('export-text').textContent = 'Saved to "a2ui apps script exports" → ' + res.name;
        document.getElementById('export-link').href = res.url;
        row.style.display = 'block';
        row.scrollIntoView({ behavior: 'smooth' });
      })
      .withFailureHandler(function(err) {
        btn.textContent = 'Export to Drive ↗';
        btn.disabled = false;
        showError('Export failed: ' + err.message);
      })
      .exportScript();
  }
</script>
</body>
</html>
```

---

## AtomPage.html — rendered page shell template

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <base target="_top">
  <title><?= title ?></title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;600;700&family=Google+Sans+Mono&display=swap" rel="stylesheet">
  <?!= include('AtomStyles') ?>
</head>
<body class="<?= theme === 'dark' ? 'asw-dark-theme' : '' ?>">
  <div class="asw-page <?= sidebar ? 'sidebar' : '' ?>">
    <? if (title) { ?>
      <h1><?= title ?></h1>
    <? } ?>
    
    <!-- Rendered Atom Components Content -->
    <?!= content ?>
  </div>

  <?!= include('AtomScripts') ?>
  <script>
    window.__A2UI_SCHEMA__ = <?!= schemaJson ?>;
    setTheme(<?= JSON.stringify(theme || 'light') ?>);
  </script>
</body>
</html>
```

---

## AtomStyles.html — CSS partial

```html
<style>
  :root {
    --bg: #ffffff;
    --surface: #f8f9fa;
    --surface2: #f1f3f4;
    --border: #e0e0e0;
    --text: #202124;
    --muted: #5f6368;
    --accent: #1a73e8;
    --accent2: #4285f4;
    --green: #34a853;
    --red: #ea4335;
    --yellow: #fbbc04;
    --orange: #fa7b17;
    --font: 'Google Sans', 'Segoe UI', system-ui, sans-serif;
    --mono: 'Google Sans Mono', 'JetBrains Mono', monospace;
    --highlight-bg: rgba(251, 188, 4, 0.3);
  }

  body.asw-dark-theme {
    --bg: #1c1c1e;
    --surface: #2c2c2e;
    --surface2: #3a3a3c;
    --border: #3a3a3c;
    --text: #f2f2f7;
    --muted: #8e8e93;
    --accent: #0a84ff;
    --accent2: #64d2ff;
    --green: #30d158;
    --red: #ff453a;
    --yellow: #ffd60a;
    --orange: #ff9f0a;
    --highlight-bg: rgba(255, 214, 10, 0.2);
  }

  *, *::before, *::after {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }

  html, body {
    background: var(--bg);
    color: var(--text);
    font-family: var(--font);
    font-size: 15px;
    line-height: 1.65;
    transition: background-color 0.3s, color 0.3s;
  }

  .asw-page {
    max-width: 860px;
    margin: 0 auto;
    padding: 32px 20px 64px;
  }

  .asw-page.sidebar {
    max-width: 380px;
    padding: 16px 14px 32px;
  }

  /* Typography */
  h1 { font-size: 1.6rem; font-weight: 700; margin-bottom: 20px; color: var(--text); }
  h2 { font-size: 1.2rem; font-weight: 600; margin: 28px 0 8px; color: var(--text); }
  h3 { font-size: 1rem; font-weight: 600; margin: 20px 0 6px; color: var(--text); }
  p  { color: var(--muted); margin-bottom: 12px; font-size: 0.9rem; }
  a  { color: var(--accent); text-decoration: none; }
  a:hover { text-decoration: underline; }
  code { font-family: var(--mono); font-size: 0.85em; background: var(--surface2); padding: 2px 5px; border-radius: 4px; }
  pre { background: var(--surface2); padding: 12px; border-radius: 6px; overflow-x: auto; margin-bottom: 16px; }
  pre code { padding: 0; background: transparent; }
  hr { border: none; border-top: 1px solid var(--border); margin: 24px 0; }
  blockquote { border-left: 4px solid var(--accent); padding-left: 16px; margin: 16px 0; color: var(--muted); font-style: italic; }

  /* Callouts & Banners */
  .asw-callout {
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 4px solid var(--accent);
    border-radius: 8px;
    padding: 14px 18px;
    margin: 16px 0;
    display: flex;
    gap: 12px;
  }
  .asw-callout-icon { font-size: 1.2rem; flex-shrink: 0; }
  .asw-callout-content { font-size: 0.9rem; color: var(--text); }

  /* Lists */
  ul, ol { margin-bottom: 16px; padding-left: 20px; }
  li { margin-bottom: 6px; font-size: 0.9rem; color: var(--muted); }
  li strong { color: var(--text); }

  /* Tables */
  table { width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 0.88rem; }
  th, td { border: 1px solid var(--border); padding: 10px 12px; text-align: left; }
  th { background: var(--surface2); color: var(--text); font-weight: 600; }
  tr:nth-child(even) td { background: var(--surface); }

  /* Form Elements & Buttons */
  .asw-btn {
    padding: 8px 18px;
    border-radius: 6px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: .04em;
    cursor: pointer;
    font-family: var(--font);
    border: none;
    transition: all .15s;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    text-decoration: none !important;
  }
  .asw-btn-primary { background: var(--accent); color: #fff; }
  .asw-btn-primary:hover { opacity: .88; }
  .asw-btn-ghost { background: var(--surface2); color: var(--muted); }
  .asw-btn-ghost:hover { color: var(--text); }

  /* Interactive / Training Atoms */
  .asw-quiz { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 20px; margin: 20px 0; }
  .asw-quiz-label { font-size: 0.65rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; color: var(--accent); margin-bottom: 8px; }
  .asw-quiz-q { font-size: 0.95rem; font-weight: 600; margin-bottom: 14px; }
  .asw-quiz-opts { display: flex; flex-direction: column; gap: 7px; }
  .asw-quiz-opt { padding: 10px 14px; border: 1px solid var(--border); border-radius: 7px; cursor: pointer; font-size: 0.85rem; color: var(--muted); transition: all .15s; display: flex; align-items: center; gap: 8px; user-select: none; }
  .asw-quiz-opt::before { content: "○"; color: var(--border); }
  .asw-quiz-opt:hover { border-color: var(--accent); color: var(--text); }
  .asw-quiz-opt.selected { border-color: var(--accent); background: var(--surface2); color: var(--text); }
  .asw-quiz-opt.selected::before { content: "●"; color: var(--accent); }
  .asw-quiz-opt.correct { border-color: var(--green); background: rgba(52, 168, 83, 0.1); color: var(--green); }
  .asw-quiz-opt.correct::before { content: "✓"; color: var(--green); }
  .asw-quiz-opt.wrong { border-color: var(--red); background: rgba(234, 67, 53, 0.1); color: var(--red); }
  .asw-quiz-opt.wrong::before { content: "✗"; color: var(--red); }
  .asw-quiz-explain { display: none; margin-top: 12px; padding: 10px 12px; background: var(--surface2); border-radius: 6px; font-size: 0.82rem; color: var(--muted); }

  .asw-fib { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 20px; margin: 20px 0; }
  .asw-fib-label { font-size: 0.65rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; color: var(--accent); margin-bottom: 10px; }
  .asw-fib input { border: 1px solid var(--border); border-radius: 4px; padding: 4px 8px; font-family: var(--mono); font-size: 0.82rem; background: var(--bg); color: var(--text); width: 130px; text-align: center; outline: none; }
  .asw-fib input:focus { border-color: var(--accent); }
  .asw-fib input.correct { border-color: var(--green); background: rgba(52, 168, 83, 0.1); color: var(--green); }
  .asw-fib input.wrong   { border-color: var(--red);   background: rgba(234, 67, 53, 0.1); color: var(--red); }
  .asw-fib-actions { margin-top: 10px; display: flex; gap: 8px; }

  .asw-match { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 20px; margin: 20px 0; }
  .asw-match-label { font-size: 0.65rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; color: var(--accent); margin-bottom: 4px; }
  .asw-match-sub { font-size: 0.82rem; color: var(--muted); margin-bottom: 12px; }
  .asw-match-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
  .asw-match-col h4 { font-size: 0.65rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: var(--muted); margin-bottom: 7px; }
  .asw-match-item { padding: 8px 12px; border: 1px solid var(--border); border-radius: 6px; font-size: 0.82rem; cursor: pointer; transition: all .15s; color: var(--muted); user-select: none; }
  .asw-match-item:hover { border-color: var(--accent); color: var(--text); }
  .asw-match-item.selected { border-color: var(--accent2); background: var(--surface2); color: var(--text); }
  .asw-match-item.matched { border-color: var(--green); background: rgba(52, 168, 83, 0.1); color: var(--green); cursor: default; }
  .asw-match-score { font-size: 0.78rem; color: var(--muted); margin-top: 10px; text-align: right; }

  details.asw-hint { background: var(--surface); border: 1px solid var(--border); border-left: 3px solid var(--accent); border-radius: 8px; margin: 12px 0; }
  details.asw-hint summary { padding: 10px 14px; font-size: 0.83rem; font-weight: 600; color: var(--accent); cursor: pointer; list-style: none; display: flex; align-items: center; gap: 7px; }
  details.asw-hint summary::before { content: "💡"; }
  details.asw-hint summary::-webkit-details-marker { display: none; }
  details.asw-hint[open] summary { border-bottom: 1px solid var(--border); }
  details.asw-hint .asw-hint-body { padding: 12px 14px; font-size: 0.84rem; color: var(--muted); }

  .asw-achievement { display: flex; align-items: center; gap: 14px; background: var(--surface); border: 1px solid var(--yellow); border-radius: 10px; padding: 16px 20px; margin: 20px 0; }
  .asw-achievement.locked { filter: grayscale(.8); opacity: .6; }
  .asw-achievement-icon { font-size: 1.8rem; flex-shrink: 0; }
  .asw-achievement-title { font-size: 0.9rem; font-weight: 700; color: var(--yellow); margin-bottom: 2px; }
  .asw-achievement-desc  { font-size: 0.8rem; color: var(--muted); }
  .asw-achievement-date  { font-size: 0.7rem; color: var(--muted); margin-top: 3px; }

  .asw-score { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 24px; margin: 20px 0; text-align: center; }
  .asw-score-pct { font-family: var(--mono); font-size: 2.8rem; font-weight: 800; color: var(--green); line-height: 1; margin-bottom: 4px; }
  .asw-score-pct.fail { color: var(--red); }
  .asw-score-label { font-size: 0.68rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; color: var(--muted); margin-bottom: 14px; }
  .asw-score-row { display: flex; justify-content: center; gap: 20px; }
  .asw-score-stat-val { font-size: 1.1rem; font-weight: 700; color: var(--text); }
  .asw-score-stat-lbl { font-size: 0.63rem; color: var(--muted); text-transform: uppercase; letter-spacing: .07em; }
  .asw-score-ctas { display: flex; justify-content: center; gap: 10px; margin-top: 16px; }

  .asw-xp { margin: 20px 0; }
  .asw-xp-row { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 6px; font-size: 0.82rem; }
  .asw-xp-level { font-weight: 600; color: var(--text); }
  .asw-xp-count { color: var(--muted); font-family: var(--mono); font-size: 0.75rem; }
  .asw-xp-track { background: var(--surface2); border-radius: 4px; height: 8px; overflow: hidden; }
  .asw-xp-fill  { height: 100%; border-radius: 4px; background: var(--accent); transition: width .6s cubic-bezier(.16,1,.3,1); }

  .asw-lesson-nav { display: flex; align-items: center; justify-content: space-between; border: 1px solid var(--border); border-radius: 10px; padding: 14px 18px; margin: 20px 0; gap: 12px; }
  .asw-lesson-nav-side { font-size: 0.82rem; color: var(--muted); text-decoration: none; display: flex; align-items: center; gap: 5px; min-width: 0; }
  .asw-lesson-nav-side:hover { color: var(--accent); }
  .asw-lesson-nav-side .nav-arrow { color: var(--accent); font-size: 1rem; flex-shrink: 0; }
  .asw-lesson-nav-center { text-align: center; flex: 1; min-width: 0; }
  .asw-lesson-nav-module { font-size: 0.65rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: var(--muted); margin-bottom: 3px; }
  .asw-lesson-nav-title { font-size: 0.88rem; font-weight: 600; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .asw-complete-row { display: flex; align-items: center; justify-content: center; gap: 6px; margin-top: 8px; font-size: 0.78rem; color: var(--muted); cursor: pointer; }

  .asw-course-card { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 20px; margin: 20px 0; }
  .asw-course-title { font-size: 1rem; font-weight: 700; margin-bottom: 14px; }
  .asw-course-module { margin-bottom: 12px; }
  .asw-course-mod-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; font-size: 0.82rem; }
  .asw-course-mod-name { color: var(--text); font-weight: 500; }
  .asw-course-mod-pct  { color: var(--muted); font-family: var(--mono); font-size: 0.75rem; }
  .asw-course-bar-track { background: var(--surface2); border-radius: 3px; height: 5px; overflow: hidden; }
  .asw-course-bar-fill  { height: 100%; border-radius: 3px; background: var(--accent); }

  .asw-highlight { background: var(--highlight-bg); border-radius: 2px; padding: 0 2px; position: relative; cursor: default; color: var(--text); }
  .asw-highlight[data-note]:hover::after {
    content: attr(data-note); position: absolute; bottom: 100%; left: 0; background: var(--yellow); color: var(--bg); padding: 4px 8px; border-radius: 5px; font-size: 0.75rem; white-space: nowrap; z-index: 10; margin-bottom: 4px; box-shadow: 0 2px 8px rgba(0,0,0,.15); pointer-events: none;
  }

  /* Workspace-Native Atoms (Category D) */
  .asw-native-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px 20px;
    margin: 20px 0;
  }
  .asw-native-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .08em;
    color: var(--accent);
    margin-bottom: 12px;
  }
  .asw-native-header-icon { font-size: 1.1rem; }

  /* Drive File List */
  .asw-drive-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; }
  .asw-drive-item { display: flex; align-items: center; gap: 10px; font-size: 0.88rem; padding: 6px 8px; border-radius: 6px; }
  .asw-drive-item:hover { background: var(--surface2); }
  .asw-drive-icon { font-size: 1.1rem; }
  .asw-drive-link { color: var(--text); font-weight: 500; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .asw-drive-link:hover { color: var(--accent); text-decoration: none; }

  /* Sheet Preview */
  .asw-sheet-preview-wrapper { overflow-x: auto; max-width: 100%; margin: 8px 0; border: 1px solid var(--border); border-radius: 6px; }
  .asw-sheet-table { width: 100%; border-collapse: collapse; margin: 0; font-size: 0.8rem; }
  .asw-sheet-table td, .asw-sheet-table th { border: 1px solid var(--border); padding: 6px 8px; }
  .asw-sheet-table th { background: var(--surface2); font-weight: 600; text-align: center; }

  /* Gmail Summary */
  .asw-gmail-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 10px; }
  .asw-gmail-item { display: flex; flex-direction: column; padding: 8px 10px; border-radius: 6px; border-left: 3px solid var(--accent); background: var(--surface2); }
  .asw-gmail-meta { display: flex; justify-content: space-between; font-size: 0.72rem; color: var(--muted); margin-bottom: 3px; }
  .asw-gmail-from { font-weight: 600; color: var(--text); }
  .asw-gmail-subject { font-size: 0.84rem; font-weight: 500; color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

  /* Calendar Upcoming */
  .asw-cal-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; }
  .asw-cal-item { display: flex; align-items: flex-start; gap: 12px; padding: 8px; border-radius: 6px; }
  .asw-cal-item:hover { background: var(--surface2); }
  .asw-cal-date-badge { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 42px; height: 42px; background: var(--surface2); border-radius: 6px; border: 1px solid var(--border); font-family: var(--mono); line-height: 1.1; }
  .asw-cal-date-badge .day { font-size: 1.1rem; font-weight: 700; color: var(--accent); }
  .asw-cal-date-badge .month { font-size: 0.55rem; text-transform: uppercase; color: var(--muted); }
  .asw-cal-details { flex: 1; display: flex; flex-direction: column; gap: 2px; }
  .asw-cal-title { font-size: 0.88rem; font-weight: 600; color: var(--text); }
  .asw-cal-time { font-size: 0.75rem; color: var(--muted); }

  /* User Greeting */
  .asw-user-greeting { display: flex; align-items: center; gap: 10px; padding: 12px 16px; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; font-size: 0.95rem; margin: 16px 0; }
  .asw-user-avatar { width: 32px; height: 32px; border-radius: 50%; background: var(--accent2); color: white; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.9rem; }
  .asw-user-email { font-weight: 600; color: var(--text); }

  /* Degraded / Fallbacks */
  .asw-degraded-card {
    border: 1px dashed var(--border);
    border-radius: 8px;
    padding: 14px 18px;
    background: var(--surface);
    margin: 16px 0;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .asw-degraded-title { font-weight: 600; font-size: 0.85rem; color: var(--text); display: flex; align-items: center; gap: 6px; }
  .asw-degraded-text { font-size: 0.8rem; color: var(--muted); }

  /* Script Run Button Spinner */
  .asw-spinner {
    display: inline-block;
    width: 12px;
    height: 12px;
    border: 2px solid rgba(255,255,255,.3);
    border-radius: 50%;
    border-top-color: #fff;
    animation: asw-spin 1s ease-in-out infinite;
  }
  .asw-btn-ghost .asw-spinner { border-top-color: var(--muted); border-bottom-color: rgba(0,0,0,.1); }
  @keyframes asw-spin { to { transform: rotate(360deg); } }

  /* === Batch-ported atom CSS === */
  All styles for Batch 4 atoms are scoped inline using uid-prefixed class names
  and emitted inside <style> blocks within each renderer's return value.
  No shared global CSS is needed — each atom is fully self-contained.

.a2ui-chart-empty {
  padding: 24px;
  text-align: center;
  color: #94a3b8;
  font-size: 13px;
  font-style: italic;
}

.a2ui-chartjs-bar,
.a2ui-chartjs-line,
.a2ui-chartjs-pie {
  width: 100%;
  overflow: hidden;
}

.a2ui-benchmark-comparison {
  width: 100%;
}

.a2ui-data-table-sortable {
  width: 100%;
}
.a2ui-table-title {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 8px;
}
.a2ui-data-table th:hover {
  background: #334155 !important;
}
.a2ui-data-table tr:hover td {
  background: #f0f9ff;
}

.a2ui-metric-comparison {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 20px;
  display: inline-block;
  min-width: 260px;
}
.a2ui-metric-cmp-title {
  font-size: 13px;
  font-weight: 600;
  color: #64748b;
  margin-bottom: 14px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.a2ui-metric-cmp-body {
  display: flex;
  align-items: center;
  gap: 16px;
}
.a2ui-metric-cmp-col {
  flex: 1;
  text-align: center;
}
.a2ui-metric-cmp-lbl {
  font-size: 11px;
  color: #94a3b8;
  margin-bottom: 4px;
}
.a2ui-metric-cmp-val {
  font-size: 28px;
  font-weight: 700;
  color: #1e293b;
  line-height: 1.1;
}
.a2ui-metric-unit {
  font-size: 14px;
  font-weight: 400;
  color: #64748b;
}
.a2ui-metric-cmp-delta {
  font-size: 18px;
  font-weight: 700;
  padding: 6px 12px;
  border-radius: 8px;
  border: 1.5px solid;
  white-space: nowrap;
}

.a2ui-sparkline-set {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 8px 0;
}
.a2ui-sparkline-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.a2ui-sparkline-label {
  font-size: 12px;
  color: #64748b;
  width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.a2ui-sparkline-val {
  font-size: 13px;
  font-weight: 600;
  min-width: 48px;
}

.a2ui-donut-stat {
  padding: 8px;
}
.a2ui-donut-label {
  font-size: 13px;
  color: #64748b;
  text-align: center;
}

.a2ui-status-dashboard {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
  font-size: 13px;
}
.a2ui-status-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  color: #fff;
}
.a2ui-status-dot-lg {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  display: inline-block;
  flex-shrink: 0;
}
.a2ui-status-title {
  font-size: 15px;
  font-weight: 700;
}
.a2ui-status-overall {
  font-size: 12px;
  opacity: 0.9;
  margin-top: 1px;
}
.a2ui-status-list {
  background: #fff;
}
.a2ui-status-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 18px;
  border-bottom: 1px solid #f1f5f9;
}
.a2ui-status-item:last-child {
  border-bottom: none;
}
.a2ui-status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}
.a2ui-status-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1px;
}
.a2ui-status-name {
  font-weight: 600;
  color: #1e293b;
}
.a2ui-status-desc {
  font-size: 11px;
  color: #94a3b8;
}
.a2ui-status-pill {
  font-size: 11px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 999px;
  white-space: nowrap;
}

.a2ui-uptime-row {
  width: 100%;
}

.a2ui-cmd-palette {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  overflow: hidden;
  background: #fff;
  box-shadow: 0 4px 16px rgba(0,0,0,0.07);
  max-width: 560px;
}
.a2ui-cmd-search-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-bottom: 1px solid #f1f5f9;
}
.a2ui-cmd-search-icon {
  flex-shrink: 0;
}
.a2ui-cmd-input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 14px;
  color: #1e293b;
  background: transparent;
  font-family: inherit;
}
.a2ui-cmd-list {
  max-height: 320px;
  overflow-y: auto;
}
.a2ui-cmd-cat {
  padding: 6px 14px;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #94a3b8;
  background: #f8fafc;
  border-bottom: 1px solid #f1f5f9;
}
.a2ui-cmd-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 14px;
  border-bottom: 1px solid #f8fafc;
  cursor: default;
}
.a2ui-cmd-item:hover {
  background: #f0f9ff;
}
.a2ui-cmd-name {
  font-size: 13px;
  font-weight: 500;
  color: #1e293b;
  flex-shrink: 0;
}
.a2ui-cmd-desc {
  font-size: 12px;
  color: #94a3b8;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.a2ui-cmd-shortcut {
  font-size: 11px;
  background: #f1f5f9;
  color: #475569;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  padding: 1px 5px;
  font-family: monospace;
  flex-shrink: 0;
}

.a2ui-search-result {
  padding: 14px 0;
  border-bottom: 1px solid #f1f5f9;
  max-width: 600px;
}
.a2ui-sr-url-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 3px;
}
.a2ui-sr-favicon {
  width: 16px;
  height: 16px;
  border-radius: 2px;
}
.a2ui-sr-breadcrumb {
  font-size: 12px;
  color: #1a7f37;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.a2ui-sr-title {
  display: block;
  font-size: 18px;
  color: #1a0dab;
  text-decoration: none;
  margin-bottom: 3px;
  line-height: 1.3;
}
.a2ui-sr-title:hover {
  text-decoration: underline;
}
.a2ui-sr-date {
  font-size: 13px;
  color: #70757a;
}
.a2ui-sr-desc {
  font-size: 13px;
  color: #4d5156;
  margin: 0;
  line-height: 1.5;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.a2ui-punch-card {
  width: 100%;
  overflow-x: auto;
}

.a2ui-sankey {
  font-size: 13px;
}
.a2ui-sankey-title {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 12px;
}
.a2ui-sankey-rows {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.a2ui-sankey-group {
  background: #f8fafc;
  border-radius: 8px;
  padding: 10px 14px;
  border: 1px solid #e2e8f0;
}
.a2ui-sankey-src-hdr {
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 8px;
  font-size: 13px;
}
.a2ui-sankey-total {
  font-size: 11px;
  font-weight: 400;
  color: #94a3b8;
  margin-left: 6px;
}
.a2ui-sankey-link {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
  font-size: 12px;
  color: #334155;
}
.a2ui-sankey-arrow {
  color: #94a3b8;
  font-size: 14px;
}
.a2ui-sankey-from,
.a2ui-sankey-to {
  min-width: 80px;
}
.a2ui-sankey-from {
  color: #6366f1;
  font-weight: 500;
}
.a2ui-sankey-to {
  color: #22d3ee;
  font-weight: 500;
}
.a2ui-sankey-val {
  min-width: 60px;
  text-align: right;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
.a2ui-sankey-bar-wrap {
  flex: 1;
  height: 8px;
  background: #e2e8f0;
  border-radius: 4px;
  overflow: hidden;
  min-width: 60px;
}
.a2ui-sankey-bar {
  height: 100%;
  background: linear-gradient(90deg, #6366f1, #22d3ee);
  border-radius: 4px;
  min-width: 2px;
}

.a2ui-cohort-retention {
  width: 100%;
}
.a2ui-cohort-title {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 8px;
}
.a2ui-cohort-table th,
.a2ui-cohort-table td {
  min-width: 56px;
  text-align: center;
  padding: 6px 8px;
  border: 1px solid #e2e8f0;
}
.a2ui-cohort-th {
  background: #1e293b;
  color: #f1f5f9;
  font-weight: 600;
  font-size: 11px;
}
.a2ui-cohort-label {
  font-size: 12px;
  font-weight: 500;
  color: #334155;
  text-align: left !important;
  white-space: nowrap;
  background: #f8fafc;
}
.a2ui-cohort-cell {
  font-size: 11px;
  font-weight: 600;
}

.a2ui-heatmap {
  width: 100%;
  overflow-x: auto;
}

.a2ui-github-grid {
  width: 100%;
  overflow-x: auto;
  background: #fff;
  border-radius: 8px;
  padding: 8px;
  border: 1px solid #e2e8f0;
}

.a2ui-entity-list {
  width: 100%;
}
.a2ui-entity-list-title {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 12px;
}
.a2ui-entity-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.a2ui-entity-card {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 14px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  transition: box-shadow 0.15s;
  color: inherit;
}
.a2ui-entity-card:hover {
  box-shadow: 0 2px 10px rgba(0,0,0,0.08);
  border-color: #c7d2fe;
}
.a2ui-entity-avatar {
  flex-shrink: 0;
}
.a2ui-entity-initials {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 700;
  color: #fff;
}
.a2ui-entity-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.a2ui-entity-name {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}
.a2ui-entity-type {
  font-size: 10px;
  font-weight: 600;
  padding: 1px 7px;
  border-radius: 999px;
  display: inline-block;
  text-transform: capitalize;
  letter-spacing: 0.02em;
}
.a2ui-entity-desc {
  font-size: 12px;
  color: #475569;
  margin-top: 2px;
  line-height: 1.4;
}
.a2ui-entity-meta {
  font-size: 11px;
  color: #94a3b8;
}
.asw-markdown-block p { margin: 0 0 0.75rem; }
.asw-markdown-block h1,.asw-markdown-block h2,.asw-markdown-block h3 { margin: 1.2rem 0 0.5rem; }
.asw-markdown-block ul,.asw-markdown-block ol { margin: 0 0 0.75rem; padding-left: 1.5rem; }
.asw-markdown-block li { margin: 0.25rem 0; }
.asw-markdown-block blockquote { border-left:3px solid #7c3aed;padding-left:12px;margin:1rem 0;color:#6b7280; }
.asw-markdown-block code { background:#f3f4f6;padding:1px 5px;border-radius:3px;font-family:monospace;font-size:0.88em; }

</style>
```

---

## AtomScripts.html — client JS partial

```html
<script>
  // Client-Side Logic & Event Listeners for A2UI Apps Script Web App

  // ── Theme Management ──
  function setTheme(theme) {
    if (theme === 'dark') {
      document.body.classList.add('asw-dark-theme');
    } else {
      document.body.classList.remove('asw-dark-theme');
    }
  }

  // ── Quiz Question (Interactive) ──
  function initQuiz(uid, correctIdx, atomId) {
    var opts = document.querySelectorAll('[id^="' + uid + '-opt-"]');
    opts.forEach(function(el) {
      el.addEventListener('click', function() {
        var idx = parseInt(el.dataset.idx);
        opts.forEach(function(o) {
          o.classList.remove('selected', 'correct', 'wrong');
        });
        el.classList.add('selected');
        
        // Show correct / wrong state
        var isCorrect = idx === correctIdx;
        el.classList.add(isCorrect ? 'correct' : 'wrong');
        
        // Reveal explanation
        var exp = document.getElementById(uid + '-explain');
        if (exp) exp.style.display = 'block';

        // Call server to persist answer
        if (typeof google !== 'undefined' && google.script && google.script.run) {
          google.script.run
            .withSuccessHandler(function(res) {
              console.log('Quiz progress saved:', res);
            })
            .withFailureHandler(function(err) {
              console.error('Failed to save quiz progress:', err);
            })
            .saveQuizAnswer(atomId, idx);
        }
      });
    });
  }

  // ── Fill In the Blank (Interactive) ──
  function initFillInBlank(uid, atomId) {
    var checkBtn = document.getElementById(uid + '-check');
    var resetBtn = document.getElementById(uid + '-reset');
    var inputs = document.querySelectorAll('#' + uid + '-fib .asw-fib-input');

    if (checkBtn) {
      checkBtn.addEventListener('click', function() {
        var userAnswers = [];
        inputs.forEach(function(inp) {
          userAnswers.push(inp.value.trim());
        });

        if (typeof google !== 'undefined' && google.script && google.script.run) {
          google.script.run
            .withSuccessHandler(function(results) {
              // results should be an object/array indicating correctness: e.g. [true, false]
              inputs.forEach(function(inp, i) {
                inp.classList.remove('correct', 'wrong');
                var ok = Array.isArray(results) ? results[i] : (results.correct && results.correct[i]);
                inp.classList.add(ok ? 'correct' : 'wrong');
              });
            })
            .withFailureHandler(function(err) {
              console.error('Failed to validate answers:', err);
            })
            .checkFillInBlank(atomId, userAnswers);
        }
      });
    }

    if (resetBtn) {
      resetBtn.addEventListener('click', function() {
        inputs.forEach(function(inp) {
          inp.value = '';
          inp.classList.remove('correct', 'wrong');
        });
      });
    }
  }

  // ── Match Exercise (Interactive) ──
  function initMatchExercise(uid, atomId, correctMap) {
    var selLeft = null;
    var selRight = null;
    var matchedCount = 0;
    var totalPairs = Object.keys(correctMap).length;

    function getEl(side, idx) {
      return document.getElementById(uid + '-' + side + '-' + idx);
    }

    function clearSel() {
      if (selLeft !== null) {
        getEl('l', selLeft).classList.remove('selected');
        selLeft = null;
      }
      if (selRight !== null) {
        getEl('r', selRight).classList.remove('selected');
        selRight = null;
      }
    }

    function pick(side, idx) {
      var el = getEl(side, idx);
      if (el.classList.contains('matched')) return;

      if (side === 'left') {
        if (selLeft === idx) {
          clearSel();
          return;
        }
        if (selLeft !== null) getEl('l', selLeft).classList.remove('selected');
        selLeft = idx;
        el.classList.add('selected');
      } else {
        if (selRight === idx) {
          clearSel();
          return;
        }
        if (selRight !== null) getEl('r', selRight).classList.remove('selected');
        selRight = idx;
        el.classList.add('selected');
      }

      if (selLeft !== null && selRight !== null) {
        var isMatch = correctMap[selLeft] === selRight;
        if (isMatch) {
          getEl('l', selLeft).classList.add('matched');
          getEl('r', selRight).classList.add('matched');
          matchedCount++;
          var scoreEl = document.getElementById(uid + '-score');
          if (scoreEl) scoreEl.textContent = matchedCount + ' / ' + totalPairs;

          if (matchedCount === totalPairs) {
            // Log result to server
            if (typeof google !== 'undefined' && google.script && google.script.run) {
              google.script.run.saveMatchResult(atomId, matchedCount);
            }
          }
        }
        clearSel();
      }
    }

    document.querySelectorAll('[id^="' + uid + '-"]').forEach(function(el) {
      if (el.dataset.side && el.dataset.idx !== undefined) {
        el.addEventListener('click', function() {
          pick(el.dataset.side, parseInt(el.dataset.idx));
        });
      }
    });
  }

  // ── Custom Script Run Button ──
  function runCustomScript(btnId, functionName, arg) {
    var btn = document.getElementById(btnId);
    if (!btn) return;
    
    var spinner = btn.querySelector('.asw-spinner');
    var status = document.getElementById(btnId + '-status');

    btn.disabled = true;
    if (spinner) spinner.style.display = 'inline-block';
    if (status) {
      status.textContent = ' Running...';
      status.style.color = 'var(--muted)';
    }

    if (typeof google !== 'undefined' && google.script && google.script.run) {
      var runner = google.script.run
        .withSuccessHandler(function(result) {
          btn.disabled = false;
          if (spinner) spinner.style.display = 'none';
          if (status) {
            status.textContent = ' Success: ' + String(result);
            status.style.color = 'var(--green)';
          }
        })
        .withFailureHandler(function(err) {
          btn.disabled = false;
          if (spinner) spinner.style.display = 'none';
          if (status) {
            status.textContent = ' Error: ' + String(err.message || err);
            status.style.color = 'var(--red)';
          }
        });

      if (typeof runner[functionName] === 'function') {
        runner[functionName](arg);
      } else {
        btn.disabled = false;
        if (spinner) spinner.style.display = 'none';
        if (status) {
          status.textContent = ' Function ' + functionName + ' not found on server.';
          status.style.color = 'var(--red)';
        }
      }
    } else {
      // Offline/preview fallback simulation
      setTimeout(function() {
        btn.disabled = false;
        if (spinner) spinner.style.display = 'none';
        if (status) {
          status.textContent = ' Preview: Function "' + functionName + '" called with "' + arg + '"';
          status.style.color = 'var(--accent)';
        }
      }, 1000);
    }
  }
</script>
```

---

## atom.gs — main renderer (all atoms)

```javascript
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



```

---

## atoms_globe.gs — globe_3d atom + world data

```javascript
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

```

---

## atoms_charts.gs — SVG chart atoms

```javascript
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

// === Animation atoms — GAS-native implementations ===
// All use CSS @keyframes or inline <script> vanilla JS. No external CDN required.

// Keep fallback only for atoms that genuinely need canvas/physics engines
function _animFallback(atomName, label) {
  return '<div style="border:1px dashed #d1d5db;border-radius:10px;padding:16px;margin:1rem 0;background:#fafafa;text-align:center;color:#9ca3af;font-size:0.82rem;">[' + atomName + ' — requires canvas/physics engine]' + (label ? '<br><strong style=\'color:#374151;\'>' + _esc(label) + '</strong>' : '') + '</div>';
}

// ── CSS @keyframes only ──────────────────────────────────────────────────────

_RENDERERS['sonar_pulse'] = function(b) {
  var label = b.label || b.title || b.text || 'Live';
  var color = b.color || '#22c55e';
  var uid = Math.random().toString(36).substr(2, 6);
  return '<style>'
    + '.sp-wrap-' + uid + '{display:flex;flex-direction:column;align-items:center;padding:32px;margin:1rem 0;}'
    + '.sp-dot-' + uid + '{position:relative;width:16px;height:16px;border-radius:50%;background:' + _esc(color) + ';}'
    + '.sp-ring-' + uid + '{position:absolute;border-radius:50%;border:2px solid ' + _esc(color) + ';opacity:0;top:50%;left:50%;transform:translate(-50%,-50%);animation:sp-' + uid + ' 2s ease-out infinite;}'
    + '.sp-ring-' + uid + ':nth-child(2){animation-delay:0.65s;}'
    + '.sp-ring-' + uid + ':nth-child(3){animation-delay:1.3s;}'
    + '@keyframes sp-' + uid + '{0%{width:16px;height:16px;opacity:0.9;}100%{width:90px;height:90px;opacity:0;}}'
    + '</style>'
    + '<div class="sp-wrap-' + uid + '">'
    + '<div class="sp-dot-' + uid + '">'
    + '<div class="sp-ring-' + uid + '"></div><div class="sp-ring-' + uid + '"></div><div class="sp-ring-' + uid + '"></div>'
    + '</div>'
    + (label ? '<div style="margin-top:22px;font-size:0.85rem;font-weight:600;color:' + _esc(color) + ';">' + _esc(label) + '</div>' : '')
    + '</div>';
};

_RENDERERS['typing_indicator'] = function(b) {
  var label = b.label || b.text || '';
  var uid = Math.random().toString(36).substr(2, 6);
  return '<style>'
    + '.ti-wrap-' + uid + '{display:inline-flex;align-items:center;gap:6px;background:#f3f4f6;border-radius:18px;padding:10px 16px;}'
    + '.ti-dot-' + uid + '{width:8px;height:8px;border-radius:50%;background:#9ca3af;animation:ti-' + uid + ' 1.2s ease-in-out infinite;}'
    + '.ti-dot-' + uid + ':nth-child(2){animation-delay:0.2s;}'
    + '.ti-dot-' + uid + ':nth-child(3){animation-delay:0.4s;}'
    + '@keyframes ti-' + uid + '{0%,60%,100%{transform:translateY(0);}30%{transform:translateY(-7px);}}'
    + '</style>'
    + '<div style="margin:1rem 0;display:flex;align-items:center;gap:10px;">'
    + '<div class="ti-wrap-' + uid + '"><div class="ti-dot-' + uid + '"></div><div class="ti-dot-' + uid + '"></div><div class="ti-dot-' + uid + '"></div></div>'
    + (label ? '<span style="font-size:0.85rem;color:#6b7280;">' + _esc(label) + '</span>' : '')
    + '</div>';
};

_RENDERERS['blur_fade_in'] = function(b) {
  var text = b.text || b.content || '';
  var title = b.title || '';
  var delay = parseFloat(b.delay || 0);
  var uid = Math.random().toString(36).substr(2, 6);
  return '<style>@keyframes bfi-' + uid + '{from{opacity:0;filter:blur(10px);transform:translateY(14px);}to{opacity:1;filter:blur(0);transform:translateY(0);}}</style>'
    + '<div style="margin:1rem 0;animation:bfi-' + uid + ' 0.9s ease-out ' + delay + 's both;">'
    + (title ? '<div style="font-size:1.1rem;font-weight:700;color:#111827;margin-bottom:8px;">' + _esc(title) + '</div>' : '')
    + (text ? '<div style="color:#374151;line-height:1.7;">' + _markdownToHtml(text) + '</div>' : '')
    + '</div>';
};

_RENDERERS['dot_grid_background'] = function(b) {
  var title = b.title || '';
  var text = b.text || b.content || '';
  var color = b.color || '#6366f1';
  var bg = b.bg || '#0f172a';
  return '<div style="position:relative;border-radius:16px;overflow:hidden;padding:40px 32px;margin:1rem 0;background:' + _esc(bg) + ';background-image:radial-gradient(' + _esc(color) + '33 1.5px,transparent 1.5px);background-size:22px 22px;">'
    + (title ? '<div style="position:relative;z-index:1;font-size:1.25rem;font-weight:700;color:#fff;margin-bottom:10px;">' + _esc(title) + '</div>' : '')
    + (text ? '<div style="position:relative;z-index:1;color:rgba(255,255,255,0.8);line-height:1.7;">' + _markdownToHtml(text) + '</div>' : '')
    + '</div>';
};
_RENDERERS['pattern_background'] = _RENDERERS['dot_grid_background'];

_RENDERERS['animated_border_card'] = function(b) {
  var title = b.title || '';
  var text = b.text || b.content || '';
  var uid = Math.random().toString(36).substr(2, 6);
  return '<style>'
    + '.abc-' + uid + '{position:relative;border-radius:16px;padding:2px;margin:1rem 0;}'
    + '.abc-' + uid + '::before{content:"";position:absolute;inset:-2px;border-radius:16px;background:conic-gradient(from 0deg,#6366f1,#a855f7,#ec4899,#f59e0b,#6366f1);z-index:0;animation:abc-spin-' + uid + ' 3s linear infinite;}'
    + '.abc-inner-' + uid + '{position:relative;z-index:1;background:#fff;border-radius:14px;padding:24px;}'
    + '@keyframes abc-spin-' + uid + '{to{transform:rotate(360deg);}}'
    + '</style>'
    + '<div class="abc-' + uid + '"><div class="abc-inner-' + uid + '">'
    + (title ? '<div style="font-size:1rem;font-weight:700;color:#111827;margin-bottom:8px;">' + _esc(title) + '</div>' : '')
    + (text ? '<div style="color:#374151;font-size:0.9rem;line-height:1.6;">' + _markdownToHtml(text) + '</div>' : '')
    + '</div></div>';
};

_RENDERERS['aurora_background'] = function(b) {
  var title = b.title || '';
  var text = b.text || b.content || '';
  var uid = Math.random().toString(36).substr(2, 6);
  return '<style>'
    + '.aur-' + uid + '{position:relative;border-radius:20px;overflow:hidden;padding:44px 36px;margin:1rem 0;background:#060617;}'
    + '.aur-' + uid + '::before{content:"";position:absolute;width:360px;height:360px;top:-80px;left:-80px;border-radius:50%;background:radial-gradient(circle,#6366f188,#a855f744);filter:blur(60px);animation:aur-a-' + uid + ' 9s ease-in-out infinite alternate;}'
    + '.aur-' + uid + '::after{content:"";position:absolute;width:300px;height:300px;bottom:-60px;right:-60px;border-radius:50%;background:radial-gradient(circle,#ec489944,#3b82f666);filter:blur(60px);animation:aur-a-' + uid + ' 9s ease-in-out infinite alternate-reverse;}'
    + '@keyframes aur-a-' + uid + '{from{transform:translate(0,0);}to{transform:translate(70px,50px);}}'
    + '</style>'
    + '<div class="aur-' + uid + '"><div style="position:relative;z-index:1;">'
    + (title ? '<div style="font-size:1.4rem;font-weight:800;color:#fff;margin-bottom:12px;">' + _esc(title) + '</div>' : '')
    + (text ? '<div style="color:rgba(255,255,255,0.82);line-height:1.75;">' + _markdownToHtml(text) + '</div>' : '')
    + '</div></div>';
};
_RENDERERS['ambient_gradient'] = _RENDERERS['aurora_background'];

_RENDERERS['card_stack'] = function(b) {
  var cards = b.cards || b.items || [];
  var title = b.title || (cards[0] && cards[0].title) || '';
  var text  = b.text  || (cards[0] && cards[0].text)  || '';
  var count = cards.length || b.count || 1;
  var uid = Math.random().toString(36).substr(2, 6);
  return '<style>'
    + '.cs-' + uid + '{position:relative;margin:1rem 0;padding-bottom:18px;}'
    + '.cs-bg2-' + uid + '{position:absolute;bottom:0;left:16px;right:16px;height:56px;background:#e5e7eb;border-radius:12px;}'
    + '.cs-bg1-' + uid + '{position:absolute;bottom:8px;left:8px;right:8px;height:56px;background:#f3f4f6;border-radius:12px;}'
    + '.cs-front-' + uid + '{position:relative;z-index:2;background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:22px;box-shadow:0 4px 16px rgba(0,0,0,0.07);}'
    + '.cs-badge-' + uid + '{display:inline-block;margin-bottom:10px;background:#6366f1;color:#fff;font-size:0.72rem;font-weight:700;padding:2px 10px;border-radius:20px;}'
    + '</style>'
    + '<div class="cs-' + uid + '">'
    + (count > 1 ? '<div class="cs-bg2-' + uid + '"></div><div class="cs-bg1-' + uid + '"></div>' : '')
    + '<div class="cs-front-' + uid + '">'
    + (count > 1 ? '<div class="cs-badge-' + uid + '">' + count + ' items</div>' : '')
    + (title ? '<div style="font-size:1rem;font-weight:700;color:#111827;margin-bottom:8px;">' + _esc(title) + '</div>' : '')
    + (text  ? '<div style="font-size:0.875rem;color:#6b7280;line-height:1.6;">' + _markdownToHtml(text) + '</div>' : '')
    + '</div></div>';
};
_RENDERERS['depth_stack'] = _RENDERERS['card_stack'];

_RENDERERS['shimmer_button'] = function(b) {
  var label = b.text || b.label || b.title || 'Action';
  var uid = Math.random().toString(36).substr(2, 6);
  return '<style>'
    + '.sb-' + uid + '{position:relative;overflow:hidden;background:#7c3aed;color:#fff;font-weight:700;font-size:0.95rem;padding:12px 28px;border:none;border-radius:10px;cursor:pointer;}'
    + '.sb-' + uid + '::after{content:"";position:absolute;top:0;left:-100%;width:60%;height:100%;background:linear-gradient(90deg,transparent,rgba(255,255,255,0.28),transparent);transform:skewX(-20deg);animation:sb-shine-' + uid + ' 2s infinite;}'
    + '@keyframes sb-shine-' + uid + '{0%{left:-100%;}100%{left:160%;}}'
    + '</style>'
    + '<div style="margin:1rem 0;text-align:center;"><button class="sb-' + uid + '">' + _esc(label) + '</button></div>';
};

_RENDERERS['glow_button'] = function(b) {
  var label = b.text || b.label || b.title || 'Action';
  var color = b.color || '#7c3aed';
  return '<div style="margin:1rem 0;text-align:center;">'
    + '<button style="background:' + _esc(color) + ';color:#fff;font-weight:700;font-size:0.95rem;padding:12px 28px;border:none;border-radius:10px;cursor:pointer;box-shadow:0 0 16px ' + _esc(color) + '88,0 0 36px ' + _esc(color) + '44;letter-spacing:0.02em;">' + _esc(label) + '</button>'
    + '</div>';
};

_RENDERERS['gradient_text'] = function(b) {
  var text = b.text || b.label || b.title || '';
  var grad = b.gradient || 'linear-gradient(135deg,#6366f1,#a855f7,#ec4899)';
  return '<div style="margin:0.5rem 0;"><span style="background:' + _esc(grad) + ';-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;font-weight:800;font-size:' + _esc(b.size || '1.5rem') + ';">' + _esc(text) + '</span></div>';
};

_RENDERERS['glitch_text'] = function(b) {
  var text = b.text || b.title || b.label || '';
  var size = b.size || '2rem';
  var uid = Math.random().toString(36).substr(2, 6);
  return '<style>'
    + '.gl-' + uid + '{position:relative;font-size:' + _esc(size) + ';font-weight:800;color:#22d3ee;display:inline-block;letter-spacing:0.04em;}'
    + '.gl-' + uid + '::before{content:attr(data-t);position:absolute;top:0;left:-2px;color:#f43f5e;clip-path:polygon(0 0,100% 0,100% 38%,0 38%);animation:gl-a-' + uid + ' 3.5s infinite;}'
    + '.gl-' + uid + '::after{content:attr(data-t);position:absolute;top:0;left:2px;color:#3b82f6;clip-path:polygon(0 62%,100% 62%,100% 100%,0 100%);animation:gl-b-' + uid + ' 3.5s infinite;}'
    + '@keyframes gl-a-' + uid + '{0%,88%,100%{transform:none;}89%{transform:translateX(-3px);}92%{transform:translateX(3px);}95%{transform:translateX(-1px);}}'
    + '@keyframes gl-b-' + uid + '{0%,88%,100%{transform:none;}89%{transform:translateX(3px);}92%{transform:translateX(-3px);}95%{transform:translateX(1px);}}'
    + '</style>'
    + '<div style="margin:1rem 0;"><span class="gl-' + uid + '" data-t="' + _esc(text) + '">' + _esc(text) + '</span></div>';
};

_RENDERERS['neon_glow'] = function(b) {
  var text = b.text || b.title || b.label || '';
  var color = b.color || '#22d3ee';
  var size  = b.size  || '2rem';
  var uid = Math.random().toString(36).substr(2, 6);
  return '<style>'
    + '.ng-' + uid + '{font-size:' + _esc(size) + ';font-weight:800;color:' + _esc(color) + ';text-shadow:0 0 8px ' + _esc(color) + ',0 0 24px ' + _esc(color) + ';animation:ng-pulse-' + uid + ' 2.2s ease-in-out infinite alternate;display:inline-block;}'
    + '@keyframes ng-pulse-' + uid + '{from{text-shadow:0 0 4px ' + _esc(color) + ',0 0 10px ' + _esc(color) + ';}to{text-shadow:0 0 10px ' + _esc(color) + ',0 0 32px ' + _esc(color) + ',0 0 64px ' + _esc(color) + ';opacity:0.88;}}'
    + '</style>'
    + '<div style="background:#090909;border-radius:12px;padding:28px;text-align:center;margin:1rem 0;"><span class="ng-' + uid + '">' + _esc(text) + '</span></div>';
};

_RENDERERS['skeleton_stage_card'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6);
  return '<style>@keyframes sk-' + uid + '{0%,100%{opacity:0.4;}50%{opacity:1;}}</style>'
    + '<div style="border:1px solid #e5e7eb;border-radius:12px;padding:20px;margin:1rem 0;background:#fff;">'
    + ['100%','80%','90%','60%'].map(function(w, i) {
        return '<div style="height:' + (i===0?'18px':'13px') + ';width:' + w + ';background:#e5e7eb;border-radius:6px;margin-bottom:10px;animation:sk-' + uid + ' 1.4s ease-in-out ' + (i*0.15) + 's infinite;"></div>';
      }).join('')
    + '</div>';
};

_RENDERERS['svg_path_draw'] = function(b) {
  var path  = b.path  || 'M10 50 Q 100 10 190 50 T 380 50';
  var label = b.label || b.title || '';
  var color = b.color || '#6366f1';
  var uid = Math.random().toString(36).substr(2, 6);
  return '<div style="margin:1rem 0;">'
    + '<style>@keyframes draw-' + uid + '{to{stroke-dashoffset:0;}}</style>'
    + (label ? '<div style="font-size:0.85rem;font-weight:600;color:#6b7280;margin-bottom:8px;">' + _esc(label) + '</div>' : '')
    + '<svg viewBox="0 0 400 80" style="width:100%;height:80px;" xmlns="http://www.w3.org/2000/svg">'
    + '<path d="' + _esc(path) + '" stroke="' + _esc(color) + '" stroke-width="3" fill="none" stroke-linecap="round" stroke-dasharray="1000" stroke-dashoffset="1000" style="animation:draw-' + uid + ' 2s ease-out 0.2s forwards;"/>'
    + '</svg></div>';
};

// ── Inline JS atoms ──────────────────────────────────────────────────────────

_RENDERERS['typewriter_text'] = function(b) {
  var text  = b.text || b.content || b.label || '';
  var speed = parseInt(b.speed || 38, 10);
  var uid = Math.random().toString(36).substr(2, 6);
  return '<div style="border:1px solid #374151;border-radius:10px;padding:16px;margin:1rem 0;background:#1e1e2e;">'
    + '<style>@keyframes blink-' + uid + '{0%,100%{opacity:1;}50%{opacity:0;}}</style>'
    + '<pre id="tw-' + uid + '" data-text="' + _esc(text) + '" style="margin:0;font-family:\'Courier New\',monospace;font-size:0.875rem;color:#cdd6f4;white-space:pre-wrap;line-height:1.6;min-height:1.4em;"></pre>'
    + '<span id="twc-' + uid + '" style="display:inline-block;width:2px;height:1em;background:#a855f7;vertical-align:text-bottom;animation:blink-' + uid + ' 1s step-end infinite;margin-left:2px;"></span>'
    + '<script>(function(){'
    + 'var el=document.getElementById("tw-' + uid + '");'
    + 'var t=el.getAttribute("data-text");var i=0;'
    + 'function next(){if(i<t.length){el.textContent+=t[i++];setTimeout(next,' + speed + ');}else{var c=document.getElementById("twc-' + uid + '");if(c)c.style.display="none";}}'
    + 'next();'
    + '})();<\/script>'
    + '</div>';
};
_RENDERERS['typewriter'] = _RENDERERS['typewriter_text'];

_RENDERERS['animated_counter'] = function(b) {
  var end   = parseFloat(b.value !== undefined ? b.value : (b.end !== undefined ? b.end : 0));
  var start = parseFloat(b.start !== undefined ? b.start : 0);
  var dur   = parseInt(b.duration || 1600, 10);
  var pre   = b.prefix || '';
  var suf   = b.suffix || '';
  var label = b.label || b.title || '';
  var dec   = b.decimals !== undefined ? parseInt(b.decimals, 10) : (String(end).indexOf('.') > -1 ? String(end).split('.')[1].length : 0);
  var uid = Math.random().toString(36).substr(2, 6);
  return '<div id="ac-wrap-' + uid + '" style="border:1px solid #e5e7eb;border-radius:12px;padding:28px;margin:1rem 0;text-align:center;background:#fff;">'
    + '<div id="ac-' + uid + '" style="font-size:2.6rem;font-weight:800;color:#1f2937;">' + _esc(pre) + start.toFixed(dec) + _esc(suf) + '</div>'
    + (label ? '<div style="font-size:0.85rem;color:#6b7280;margin-top:6px;font-weight:500;">' + _esc(label) + '</div>' : '')
    + '<script>(function(){'
    + 'var el=document.getElementById("ac-' + uid + '");'
    + 'var wrap=document.getElementById("ac-wrap-' + uid + '");'
    + 'var s=' + start + ',e=' + end + ',d=' + dur + ',dec=' + dec + ';'
    + 'var pre="' + _esc(pre).replace(/\\/g,'\\\\').replace(/"/g,'\\"') + '",suf="' + _esc(suf).replace(/\\/g,'\\\\').replace(/"/g,'\\"') + '";'
    + 'var done=false;'
    + 'function run(){if(done)return;done=true;var t0=null;'
    + 'function step(ts){if(!t0)t0=ts;var p=Math.min((ts-t0)/d,1);var ease=p<0.5?2*p*p:1-Math.pow(-2*p+2,2)/2;'
    + 'el.textContent=pre+(s+(e-s)*ease).toFixed(dec)+suf;if(p<1)requestAnimationFrame(step);}'
    + 'requestAnimationFrame(step);}'
    + 'if("IntersectionObserver" in window){new IntersectionObserver(function(es,ob){if(es[0].isIntersecting){run();ob.disconnect();}},{threshold:0.3}).observe(wrap);}else{run();}'
    + '})();<\/script>'
    + '</div>';
};
_RENDERERS['live_metric'] = _RENDERERS['animated_counter'];
_RENDERERS['number_odometer'] = _RENDERERS['animated_counter'];

_RENDERERS['countdown_timer'] = function(b) {
  var target = b.target_date || b.target || '';
  var label  = b.label || b.title || '';
  var uid = Math.random().toString(36).substr(2, 6);
  if (!target) {
    return '<div style="border:1px solid #e5e7eb;border-radius:12px;padding:20px;margin:1rem 0;text-align:center;background:#fff;">'
      + (label ? '<div style="font-size:0.78rem;font-weight:600;color:#9ca3af;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">⏱ ' + _esc(label) + '</div>' : '')
      + '<div id="cd-' + uid + '" style="font-size:2.2rem;font-weight:800;color:#1f2937;font-family:monospace;">00:00:00</div>'
      + '<script>(function(){var s=0,el=document.getElementById("cd-' + uid + '");setInterval(function(){s++;var h=Math.floor(s/3600),m=Math.floor((s%3600)/60),sec=s%60;el.textContent=[h,m,sec].map(function(n){return n<10?"0"+n:n}).join(":");},1000);})();<\/script>'
      + '</div>';
  }
  return '<div style="border:1px solid #e5e7eb;border-radius:12px;padding:22px;margin:1rem 0;background:#fff;">'
    + (label ? '<div style="font-size:0.78rem;font-weight:600;color:#9ca3af;text-transform:uppercase;letter-spacing:0.08em;text-align:center;margin-bottom:16px;">' + _esc(label) + '</div>' : '')
    + '<div style="display:flex;justify-content:center;gap:12px;">'
    + ['days','hrs','min','sec'].map(function(u) {
        return '<div style="text-align:center;min-width:60px;background:#f9fafb;border-radius:10px;padding:12px 8px;">'
          + '<div id="cd-' + uid + '-' + u + '" style="font-size:1.9rem;font-weight:800;color:#1f2937;font-family:monospace;line-height:1;">--</div>'
          + '<div style="font-size:0.68rem;color:#9ca3af;font-weight:700;margin-top:4px;text-transform:uppercase;letter-spacing:0.06em;">' + u + '</div>'
          + '</div>';
      }).join('')
    + '</div>'
    + '<script>(function(){'
    + 'var end=new Date("' + _esc(target) + '").getTime();'
    + 'function set(id,v){var el=document.getElementById(id);if(el)el.textContent=v<10?"0"+v:v;}'
    + 'function tick(){var diff=Math.max(end-Date.now(),0);'
    + 'set("cd-' + uid + '-days",Math.floor(diff/86400000));'
    + 'set("cd-' + uid + '-hrs",Math.floor((diff%86400000)/3600000));'
    + 'set("cd-' + uid + '-min",Math.floor((diff%3600000)/60000));'
    + 'set("cd-' + uid + '-sec",Math.floor((diff%60000)/1000));'
    + 'if(diff>0)setTimeout(tick,1000);}'
    + 'tick();'
    + '})();<\/script>'
    + '</div>';
};
_RENDERERS['deadline_ticker'] = _RENDERERS['countdown_timer'];

_RENDERERS['encrypted_reveal'] = function(b) {
  var text  = b.text || b.content || b.label || '';
  var title = b.title || '';
  var uid = Math.random().toString(36).substr(2, 6);
  return '<div style="border:1px solid #1f2937;border-radius:12px;padding:20px;margin:1rem 0;background:#0f172a;">'
    + (title ? '<div style="font-size:0.75rem;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:10px;">' + _esc(title) + '</div>' : '')
    + '<div id="er-' + uid + '" data-text="' + _esc(text) + '" style="font-family:\'Courier New\',monospace;font-size:1.05rem;font-weight:600;color:#22d3ee;line-height:1.6;min-height:1.5em;cursor:pointer;" title="click to reveal"></div>'
    + '<div style="font-size:0.7rem;color:#475569;margin-top:8px;">↑ click to reveal</div>'
    + '<script>(function(){'
    + 'var el=document.getElementById("er-' + uid + '");'
    + 'var target=el.getAttribute("data-text");'
    + 'var chars="!<>-_\\/[]{}=+*^?#@";var itr=0,iv,done=false;'
    + 'function scramble(){el.textContent=target.split("").map(function(c,i){return c===" "?" ":(i<Math.floor(itr)?target[i]:chars[Math.floor(Math.random()*chars.length)]);}).join("");'
    + 'if(itr>=target.length){clearInterval(iv);el.textContent=target;done=true;}itr+=0.5;}'
    + 'function start(){if(done)return;if(iv)clearInterval(iv);itr=0;iv=setInterval(scramble,30);}'
    + 'el.addEventListener("click",start);'
    + 'setTimeout(start,600);'
    + '})();<\/script>'
    + '</div>';
};
_RENDERERS['scramble_reveal'] = _RENDERERS['encrypted_reveal'];

_RENDERERS['word_flip'] = function(b) {
  var words    = b.words || b.items || ['One','Two','Three'];
  var prefix   = b.prefix || b.text || '';
  var suffix   = b.suffix || '';
  var interval = parseInt(b.interval || 2200, 10);
  var color    = b.color || '#6366f1';
  var uid = Math.random().toString(36).substr(2, 6);
  var wordsJson = JSON.stringify(words.map(function(w) { return String(w); }));
  return '<div style="margin:1rem 0;font-size:1.3rem;font-weight:700;color:#1f2937;line-height:1.5;">'
    + (prefix ? '<span>' + _esc(prefix) + ' </span>' : '')
    + '<span id="wf-' + uid + '" style="color:' + _esc(color) + ';transition:opacity 0.28s ease;">' + _esc(String(words[0] || '')) + '</span>'
    + (suffix ? '<span> ' + _esc(suffix) + '</span>' : '')
    + '<script>(function(){'
    + 'var el=document.getElementById("wf-' + uid + '");'
    + 'var words=' + wordsJson + ';var i=0;'
    + 'setInterval(function(){el.style.opacity="0";setTimeout(function(){i=(i+1)%words.length;el.textContent=words[i];el.style.opacity="1";},280);},' + interval + ');'
    + '})();<\/script>'
    + '</div>';
};

_RENDERERS['word_scramble'] = function(b) {
  var words = b.words || b.items || ['HELLO','WORLD'];
  var uid = Math.random().toString(36).substr(2, 6);
  var wordsJson = JSON.stringify(words.map(function(w) { return String(w).toUpperCase(); }));
  return '<div style="border:1px solid #1e293b;border-radius:12px;padding:28px;margin:1rem 0;background:#0f172a;text-align:center;">'
    + '<div id="ws-' + uid + '" style="font-family:\'Courier New\',monospace;font-size:1.6rem;font-weight:800;color:#22d3ee;letter-spacing:0.12em;min-height:2rem;"></div>'
    + '<script>(function(){'
    + 'var el=document.getElementById("ws-' + uid + '");'
    + 'var words=' + wordsJson + ';var chars="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";var wi=0,itr=0,iv;'
    + 'function tick(){var t=words[wi];el.textContent=t.split("").map(function(c,i){return i<Math.floor(itr)?c:chars[Math.floor(Math.random()*chars.length)];}).join("");'
    + 'itr+=0.4;if(itr>=t.length+4){clearInterval(iv);setTimeout(function(){wi=(wi+1)%words.length;itr=0;iv=setInterval(tick,40);},1400);}}'
    + 'iv=setInterval(tick,40);'
    + '})();<\/script>'
    + '</div>';
};

_RENDERERS['reveal_on_scroll'] = function(b) {
  var text  = b.text || b.content || '';
  var title = b.title || '';
  var delay = parseFloat(b.delay || 0);
  var dir   = b.direction || 'up';
  var uid = Math.random().toString(36).substr(2, 6);
  var startT = dir==='left'?'translateX(-28px)':dir==='right'?'translateX(28px)':dir==='down'?'translateY(-18px)':'translateY(20px)';
  return '<div id="ros-' + uid + '" style="margin:1rem 0;opacity:0;transform:' + startT + ';transition:opacity 0.65s ease ' + delay + 's,transform 0.65s ease ' + delay + 's;">'
    + (title ? '<div style="font-size:1.1rem;font-weight:700;color:#111827;margin-bottom:8px;">' + _esc(title) + '</div>' : '')
    + (text  ? '<div style="color:#374151;line-height:1.7;">' + _markdownToHtml(text) + '</div>' : '')
    + '<script>(function(){'
    + 'var el=document.getElementById("ros-' + uid + '");'
    + 'function show(){el.style.opacity="1";el.style.transform="none";}'
    + 'if("IntersectionObserver" in window){new IntersectionObserver(function(es,ob){if(es[0].isIntersecting){show();ob.disconnect();}},{threshold:0.12}).observe(el);}else{show();}'
    + '})();<\/script>'
    + '</div>';
};
_RENDERERS['scroll_trigger'] = _RENDERERS['reveal_on_scroll'];

_RENDERERS['tilt_card'] = function(b) {
  var title = b.title || '';
  var text  = b.text || b.content || '';
  var uid = Math.random().toString(36).substr(2, 6);
  return '<div id="tilt-' + uid + '" style="border:1px solid #e5e7eb;border-radius:16px;padding:24px;margin:1rem 0;background:#fff;transition:transform 0.12s ease,box-shadow 0.12s ease;cursor:default;">'
    + (title ? '<div style="font-size:1rem;font-weight:700;color:#111827;margin-bottom:8px;">' + _esc(title) + '</div>' : '')
    + (text  ? '<div style="font-size:0.875rem;color:#6b7280;line-height:1.6;">' + _markdownToHtml(text) + '</div>' : '')
    + '<script>(function(){'
    + 'var el=document.getElementById("tilt-' + uid + '");'
    + 'el.addEventListener("mousemove",function(e){var r=el.getBoundingClientRect();var x=(e.clientX-r.left)/r.width-0.5;var y=(e.clientY-r.top)/r.height-0.5;el.style.transform="perspective(600px) rotateY("+(x*14)+"deg) rotateX("+(-y*14)+"deg) scale(1.025)";el.style.boxShadow=(x*10)+"px "+(y*10)+"px 32px rgba(0,0,0,0.13)";});'
    + 'el.addEventListener("mouseleave",function(){el.style.transform="";el.style.boxShadow="";});'
    + '})();<\/script>'
    + '</div>';
};

_RENDERERS['magnetic_button'] = function(b) {
  var label = b.text || b.label || b.title || 'Click me';
  var color = b.color || '#6366f1';
  var uid = Math.random().toString(36).substr(2, 6);
  return '<div style="margin:1rem 0;text-align:center;">'
    + '<button id="mag-' + uid + '" style="background:' + _esc(color) + ';color:#fff;font-weight:700;font-size:1rem;padding:14px 36px;border:none;border-radius:50px;cursor:pointer;transition:transform 0.12s ease,box-shadow 0.12s ease;box-shadow:0 4px 24px rgba(0,0,0,0.14);">' + _esc(label) + '</button>'
    + '<script>(function(){'
    + 'var el=document.getElementById("mag-' + uid + '");'
    + 'el.addEventListener("mousemove",function(e){var r=el.getBoundingClientRect();var x=(e.clientX-r.left-r.width/2)*0.28;var y=(e.clientY-r.top-r.height/2)*0.28;el.style.transform="translate("+x+"px,"+y+"px)";});'
    + 'el.addEventListener("mouseleave",function(){el.style.transform="";});'
    + '})();<\/script>'
    + '</div>';
};

_RENDERERS['animated_beam'] = function(b) {
  var from  = b.from  || 'Source';
  var to    = b.to    || 'Target';
  var label = b.label || b.text || '';
  var color = b.color || '#6366f1';
  var uid = Math.random().toString(36).substr(2, 6);
  return '<style>@keyframes beam-' + uid + '{to{stroke-dashoffset:-20;}}</style>'
    + '<div style="margin:1rem 0;display:flex;align-items:center;gap:0;">'
    + '<div style="flex-shrink:0;background:#fff;border:2px solid ' + _esc(color) + ';border-radius:8px;padding:8px 14px;font-size:0.85rem;font-weight:600;color:#1f2937;">' + _esc(from) + '</div>'
    + '<div style="flex:1;position:relative;height:32px;">'
    + '<svg width="100%" height="32" xmlns="http://www.w3.org/2000/svg" style="position:absolute;top:0;left:0;overflow:visible;">'
    + '<line x1="0" y1="16" x2="100%" y2="16" stroke="' + _esc(color) + '" stroke-width="2.5" stroke-dasharray="7 5" style="animation:beam-' + uid + ' 0.7s linear infinite;"/>'
    + '<polygon points="-6,-5 4,0 -6,5" fill="' + _esc(color) + '" transform="translate(100%,16)"/>'
    + '</svg>'
    + (label ? '<div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);background:#fff;border:1px solid #e5e7eb;border-radius:20px;padding:2px 10px;font-size:0.72rem;color:#6b7280;white-space:nowrap;">' + _esc(label) + '</div>' : '')
    + '</div>'
    + '<div style="flex-shrink:0;background:#fff;border:2px solid ' + _esc(color) + ';border-radius:8px;padding:8px 14px;font-size:0.85rem;font-weight:600;color:#1f2937;">' + _esc(to) + '</div>'
    + '</div>';
};
_RENDERERS['flow_connector'] = _RENDERERS['animated_beam'];

_RENDERERS['confetti_burst'] = function(b) {
  var label  = b.label || b.text || b.title || '🎉 Achievement Unlocked!';
  var uid = Math.random().toString(36).substr(2, 6);
  return '<style>@keyframes cf-' + uid + '{0%{opacity:1;transform:translate(var(--tx),0) rotate(0deg);}100%{opacity:0;transform:translate(var(--tx),var(--ty)) rotate(720deg);}}</style>'
    + '<div id="cfb-' + uid + '" style="position:relative;overflow:hidden;border-radius:16px;padding:36px;margin:1rem 0;background:linear-gradient(135deg,#1e1b4b,#312e81);text-align:center;">'
    + '<div style="position:relative;z-index:1;font-size:1.2rem;font-weight:700;color:#fff;">' + _esc(label) + '</div>'
    + '</div>'
    + '<script>(function(){'
    + 'var wrap=document.getElementById("cfb-' + uid + '");'
    + 'var colors=["#f43f5e","#f59e0b","#10b981","#3b82f6","#a855f7","#ec4899"];'
    + 'for(var i=0;i<40;i++){var p=document.createElement("span");var c=colors[i%colors.length];var sz=6+Math.random()*9;var tx=(Math.random()*200-100);var ty=120+Math.random()*80;var del=Math.random()*0.5;var dur=0.85+Math.random()*0.65;'
    + 'p.style.cssText="position:absolute;left:"+Math.random()*100+"%;top:20%;width:"+sz+"px;height:"+sz+"px;background:"+c+";border-radius:"+(Math.random()>0.5?"50%":"2px")+";pointer-events:none;animation:cf-' + uid + ' "+dur+"s ease-in "+del+"s both;--tx:"+tx+"px;--ty:"+ty+"px;";'
    + 'wrap.appendChild(p);}'
    + '})();<\/script>';
};

_RENDERERS['confetti_trigger'] = function(b) {
  var label   = b.label  || b.text  || '🎉 Congratulations!';
  var trigger = b.trigger || b.button || 'Celebrate';
  var uid = Math.random().toString(36).substr(2, 6);
  return '<style>@keyframes cft-' + uid + '{0%{opacity:1;transform:translate(var(--tx),0) rotate(0deg);}100%{opacity:0;transform:translate(var(--tx),var(--ty)) rotate(720deg);}}</style>'
    + '<div id="cft-wrap-' + uid + '" style="position:relative;overflow:hidden;border-radius:16px;padding:32px;margin:1rem 0;background:#f9fafb;border:1px solid #e5e7eb;text-align:center;transition:background 0.5s;">'
    + '<button id="cft-btn-' + uid + '" style="background:#6366f1;color:#fff;font-weight:700;padding:12px 28px;border:none;border-radius:10px;font-size:0.95rem;cursor:pointer;">' + _esc(trigger) + '</button>'
    + '<div id="cft-msg-' + uid + '" style="display:none;font-size:1.2rem;font-weight:700;color:#fff;">' + _esc(label) + '</div>'
    + '</div>'
    + '<script>(function(){'
    + 'var wrap=document.getElementById("cft-wrap-' + uid + '");'
    + 'document.getElementById("cft-btn-' + uid + '").addEventListener("click",function(){'
    + 'this.style.display="none";'
    + 'document.getElementById("cft-msg-' + uid + '").style.display="block";'
    + 'wrap.style.background="linear-gradient(135deg,#1e1b4b,#312e81)";'
    + 'var colors=["#f43f5e","#f59e0b","#10b981","#3b82f6","#a855f7","#ec4899"];'
    + 'for(var i=0;i<44;i++){var p=document.createElement("span");var c=colors[i%colors.length];var sz=6+Math.random()*9;var tx=(Math.random()*200-100);var ty=100+Math.random()*90;var del=Math.random()*0.55;var dur=0.9+Math.random()*0.65;'
    + 'p.style.cssText="position:absolute;left:"+Math.random()*100+"%;top:20%;width:"+sz+"px;height:"+sz+"px;background:"+c+";border-radius:"+(Math.random()>0.5?"50%":"2px")+";pointer-events:none;animation:cft-' + uid + ' "+dur+"s ease-in "+del+"s both;--tx:"+tx+"px;--ty:"+ty+"px;";'
    + 'wrap.appendChild(p);}});'
    + '})();<\/script>';
};

// Atoms that genuinely require canvas or physics — kept as informational placeholders
_RENDERERS['meteor_shower'] = function(b) {
  return _animFallback('meteor shower', b.title || b.label || b.text || '');
};
_RENDERERS['floating_particles'] = function(b) {
  return _animFallback('floating particles', b.title || b.label || b.text || '');
};
_RENDERERS['parallax_section'] = function(b) {
  return _animFallback('parallax section', b.title || b.label || b.text || '');
};
_RENDERERS['effect_overlay'] = function(b) {
  return _animFallback('effect overlay', b.title || b.label || b.text || '');
};

// ── New GAS-native atoms ─────────────────────────────────────────────────────

_RENDERERS['scroll_progress'] = function(b) {
  var color  = b.color  || '#6366f1';
  var height = parseInt(b.height || 3, 10);
  return '<style>#a2ui-sp-bar{position:fixed;top:0;left:0;width:0%;height:' + height + 'px;background:' + _esc(color) + ';z-index:9999;transition:width 0.08s linear;pointer-events:none;}</style>'
    + '<div id="a2ui-sp-bar"></div>'
    + '<script>(function(){if(document.getElementById("a2ui-sp-bar-init"))return;var m=document.createElement("meta");m.id="a2ui-sp-bar-init";document.head.appendChild(m);var bar=document.getElementById("a2ui-sp-bar");window.addEventListener("scroll",function(){var s=document.documentElement.scrollTop||document.body.scrollTop;var h=document.documentElement.scrollHeight-document.documentElement.clientHeight;bar.style.width=(h>0?Math.min(s/h*100,100):0)+"%";},{passive:true});})();<\/script>';
};

_RENDERERS['live_clock'] = function(b) {
  var label  = b.label || b.title || '';
  var format = b.format || '24h';
  var tz     = b.timezone || '';
  var uid = Math.random().toString(36).substr(2, 6);
  return '<div style="display:inline-flex;flex-direction:column;align-items:center;background:#0f172a;border-radius:16px;padding:24px 36px;margin:1rem 0;">'
    + (label ? '<div style="font-size:0.72rem;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:10px;">' + _esc(label) + '</div>' : '')
    + '<div id="lc-' + uid + '" style="font-size:2.6rem;font-weight:800;font-family:monospace;color:#22d3ee;letter-spacing:0.07em;">--:--:--</div>'
    + (tz ? '<div style="font-size:0.7rem;color:#475569;margin-top:6px;">' + _esc(tz) + '</div>' : '')
    + '<script>(function(){'
    + 'var el=document.getElementById("lc-' + uid + '");var f="' + format + '";'
    + 'function tick(){var now=new Date();var h=now.getHours(),m=now.getMinutes(),s=now.getSeconds(),suf="";'
    + 'if(f==="12h"){suf=h>=12?" PM":" AM";h=h%12||12;}'
    + 'el.textContent=[h,m,s].map(function(n){return n<10?"0"+n:n}).join(":")+suf;}'
    + 'tick();setInterval(tick,1000);'
    + '})();<\/script>'
    + '</div>';
};

_RENDERERS['decision_tree'] = function(b) {
  var nodes = b.nodes || b.tree || [];
  var title = b.title || '';

  function renderNode(node, depth) {
    depth = depth || 0;
    var children = node.children || node.branches || [];
    if (!children.length) {
      return '<div style="padding:10px 14px;margin:4px 0;background:#f0fdf4;border:1px solid #86efac;border-radius:8px;font-size:0.875rem;color:#166534;font-weight:500;">✓ ' + _esc(node.text || node.label || '') + '</div>';
    }
    return '<details style="margin:4px 0;"' + (depth === 0 ? ' open' : '') + '>'
      + '<summary style="cursor:pointer;list-style:none;padding:10px 14px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;font-size:0.875rem;font-weight:600;color:#0f172a;user-select:none;">'
      + '▸ ' + _esc(node.text || node.label || node.question || '')
      + '</summary>'
      + '<div style="padding-left:20px;border-left:2px solid #e2e8f0;margin-left:14px;margin-top:4px;">'
      + children.map(function(c) { return renderNode(c, depth + 1); }).join('')
      + '</div></details>';
  }

  return '<div style="border:1px solid #e5e7eb;border-radius:12px;padding:20px;margin:1rem 0;">'
    + (title ? '<div style="font-size:1rem;font-weight:700;color:#111827;margin-bottom:14px;">' + _esc(title) + '</div>' : '')
    + nodes.map(function(n) { return renderNode(n, 0); }).join('')
    + '</div>';
};

_RENDERERS['step_reveal_sequence'] = function(b) {
  var steps = b.steps || [];
  if (!steps.length) return '';
  var uid = Math.random().toString(36).substr(2, 6);
  var css = '<style>';
  steps.forEach(function(_, i) {
    css += '#srs-' + uid + '-' + i + ':checked ~ .srs-nav-' + uid + ' .srs-lbl-' + uid + ':nth-child(' + (i+1) + '){background:#6366f1;color:#fff;border-color:#6366f1;}';
    css += '#srs-' + uid + '-' + i + ':checked ~ .srs-body-' + uid + ' .srs-panel-' + uid + ':nth-child(' + (i+1) + '){display:block;}';
  });
  css += '.srs-panel-' + uid + '{display:none;padding:20px;animation:srs-in-' + uid + ' 0.3s ease;}';
  css += '@keyframes srs-in-' + uid + '{from{opacity:0;transform:translateY(8px);}to{opacity:1;transform:none;}}';
  css += '</style>';
  var inputs = steps.map(function(_, i) {
    return '<input type="radio" id="srs-' + uid + '-' + i + '" name="srs-' + uid + '"' + (i===0?' checked':'') + ' style="display:none;">';
  }).join('');
  var nav = '<div class="srs-nav-' + uid + '" style="display:flex;gap:6px;flex-wrap:wrap;padding:12px 16px;border-bottom:1px solid #e5e7eb;">'
    + steps.map(function(s, i) {
        return '<label for="srs-' + uid + '-' + i + '" class="srs-lbl-' + uid + '" style="cursor:pointer;padding:6px 14px;border-radius:20px;border:1px solid #e5e7eb;font-size:0.8rem;font-weight:600;color:#6b7280;transition:all 0.15s;">' + (i+1) + (s.title ? '. ' + _esc(s.title) : '') + '</label>';
      }).join('')
    + '</div>';
  var body = '<div class="srs-body-' + uid + '">'
    + steps.map(function(s) {
        return '<div class="srs-panel-' + uid + '">'
          + (s.title ? '<div style="font-size:1rem;font-weight:700;color:#111827;margin-bottom:10px;">' + _esc(s.title) + '</div>' : '')
          + (s.text || s.content ? '<div style="color:#374151;line-height:1.7;">' + _markdownToHtml(s.text || s.content || '') + '</div>' : '')
          + '</div>';
      }).join('')
    + '</div>';
  return css + '<div style="border:1px solid #e5e7eb;border-radius:12px;overflow:hidden;margin:1rem 0;">'
    + inputs + nav + body + '</div>';
};

_RENDERERS['chat_sequence'] = function(b) {
  var messages = b.messages || [];
  if (!messages.length) return '';
  var html = '<style>@keyframes chat-in{from{opacity:0;transform:translateY(10px);}to{opacity:1;transform:none;}}</style>'
    + '<div style="border:1px solid #e5e7eb;border-radius:16px;padding:16px;margin:1rem 0;background:#f9fafb;display:flex;flex-direction:column;gap:12px;">';
  messages.forEach(function(msg, i) {
    var isUser = msg.role === 'user' || msg.align === 'right';
    var delay  = (i * 0.28) + 's';
    html += '<div style="display:flex;flex-direction:column;align-items:' + (isUser?'flex-end':'flex-start') + ';animation:chat-in 0.4s ease ' + delay + ' both;">'
      + '<div style="font-size:0.7rem;color:#9ca3af;margin-bottom:4px;">' + _esc(msg.name || (isUser ? 'You' : 'Assistant')) + '</div>'
      + '<div style="max-width:82%;background:' + (isUser?'#6366f1':'#fff') + ';color:' + (isUser?'#fff':'#1f2937') + ';border-radius:' + (isUser?'16px 4px 16px 16px':'4px 16px 16px 16px') + ';padding:10px 14px;font-size:0.875rem;line-height:1.55;' + (isUser?'':'box-shadow:0 1px 4px rgba(0,0,0,0.07);') + '">' + _markdownToHtml(msg.text || msg.content || '') + '</div>'
      + '</div>';
  });
  return html + '</div>';
};

_RENDERERS['tooltip_glossary'] = function(b) {
  var terms = b.terms || b.items || [];
  var intro = b.text || b.intro || '';
  return '<style>.tg-term{position:relative;cursor:help;color:#6366f1;font-weight:600;border-bottom:1px dashed #6366f1;}'
    + '.tg-tip{display:none;position:absolute;bottom:120%;left:50%;transform:translateX(-50%);background:#1f2937;color:#fff;font-size:0.78rem;padding:6px 12px;border-radius:8px;white-space:nowrap;z-index:20;box-shadow:0 4px 14px rgba(0,0,0,0.22);}'
    + '.tg-tip::after{content:"";position:absolute;top:100%;left:50%;transform:translateX(-50%);border:5px solid transparent;border-top-color:#1f2937;}'
    + '.tg-term:hover .tg-tip{display:block;}</style>'
    + '<div style="border:1px solid #e5e7eb;border-radius:12px;padding:20px;margin:1rem 0;">'
    + (intro ? '<div style="color:#374151;line-height:1.7;margin-bottom:14px;">' + _markdownToHtml(intro) + '</div>' : '')
    + terms.map(function(t) {
        return '<div style="display:flex;gap:14px;align-items:baseline;padding:10px 0;border-bottom:1px solid #f3f4f6;">'
          + '<span class="tg-term" style="flex-shrink:0;min-width:100px;">' + _esc(t.term || t.word || '') + '<span class="tg-tip">' + _esc(t.definition || t.def || '') + '</span></span>'
          + '<span style="color:#6b7280;font-size:0.875rem;">' + _markdownToHtml(t.definition || t.def || '') + '</span>'
          + '</div>';
      }).join('')
    + '</div>';
};

_RENDERERS['focus_lens'] = function(b) {
  var title = b.title || '';
  var text  = b.text || b.content || '';
  var uid = Math.random().toString(36).substr(2, 6);
  return '<style>'
    + '.fl-wrap-' + uid + '{position:relative;border-radius:16px;overflow:hidden;margin:1rem 0;min-height:140px;}'
    + '.fl-bg-' + uid + '{filter:blur(4px);padding:30px;background:#f3f4f6;opacity:0.7;user-select:none;font-size:0.82rem;color:#9ca3af;line-height:1.8;}'
    + '.fl-lens-' + uid + '{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);background:rgba(255,255,255,0.96);border-radius:14px;padding:22px 30px;box-shadow:0 6px 40px rgba(0,0,0,0.16);max-width:80%;text-align:center;z-index:2;}'
    + '</style>'
    + '<div class="fl-wrap-' + uid + '">'
    + '<div class="fl-bg-' + uid + '">Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore et dolore magna aliqua ut enim ad minim veniam quis nostrud exercitation ullamco laboris.</div>'
    + '<div class="fl-lens-' + uid + '">'
    + (title ? '<div style="font-size:1rem;font-weight:700;color:#111827;margin-bottom:8px;">' + _esc(title) + '</div>' : '')
    + (text  ? '<div style="font-size:0.875rem;color:#374151;line-height:1.6;">' + _markdownToHtml(text) + '</div>' : '')
    + '</div></div>';
};

// ── Gap atoms ────────────────────────────────────────────────────────────────

_RENDERERS['terminal_boot'] = function(b) {
  var lines = b.lines || [];
  var title = b.title || '';
  var speed = parseInt(b.speed || 380, 10);
  var uid = Math.random().toString(36).substr(2, 6);
  var linesHtml = lines.map(function(line, i) {
    var l = String(line);
    var isOk  = l.indexOf('✓') > -1 || l.indexOf('OK') > -1 || l.indexOf('ok') > -1;
    var isErr = l.indexOf('✗') > -1 || l.indexOf('ERR') > -1 || l.indexOf('FAIL') > -1;
    var col   = isOk ? '#22c55e' : isErr ? '#f87171' : '#94a3b8';
    return '<div id="tb-' + uid + '-' + i + '" style="opacity:0;line-height:1.9;color:' + col + ';">'
      + '<span style="color:#475569;margin-right:10px;user-select:none;">$</span>' + _esc(l) + '</div>';
  }).join('');
  return '<div style="background:#0a0f1e;border:1px solid #1e293b;border-radius:12px;padding:20px 24px;margin:1rem 0;font-family:\'Courier New\',monospace;font-size:0.84rem;">'
    + (title ? '<div style="font-size:0.7rem;font-weight:700;color:#334155;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:14px;">' + _esc(title) + '</div>' : '')
    + '<div>' + linesHtml + '</div>'
    + '<span id="tb-cur-' + uid + '" style="display:inline-block;width:8px;height:14px;background:#22c55e;vertical-align:middle;margin-left:2px;animation:tb-bl-' + uid + ' 1s step-end infinite;"></span>'
    + '<style>@keyframes tb-bl-' + uid + '{0%,100%{opacity:1;}50%{opacity:0;}}</style>'
    + '<script>(function(){'
    + 'var els=[];for(var i=0;i<' + lines.length + ';i++){var el=document.getElementById("tb-' + uid + '-"+i);if(el)els.push(el);}'
    + 'var cur=document.getElementById("tb-cur-' + uid + '");var i=0;'
    + 'function next(){if(i<els.length){els[i].style.opacity="1";i++;setTimeout(next,' + speed + ');}else if(cur){cur.style.display="none";}}'
    + 'setTimeout(next,400);'
    + '})();<\/script>'
    + '</div>';
};

_RENDERERS['stagger_list'] = function(b) {
  var items = b.items || [];
  var dir   = b.direction || 'up';
  var gap   = parseFloat(b.stagger !== undefined ? b.stagger : 0.1);
  var uid = Math.random().toString(36).substr(2, 6);
  var startT = dir==='left'?'translateX(-22px)':dir==='right'?'translateX(22px)':dir==='down'?'translateY(-14px)':'translateY(16px)';
  return '<style>@keyframes sl-' + uid + '{from{opacity:0;transform:' + startT + ';}to{opacity:1;transform:none;}}</style>'
    + '<div style="margin:1rem 0;display:flex;flex-direction:column;gap:8px;">'
    + items.map(function(item, i) {
        var delay = (i * gap) + 's';
        var base  = 'opacity:0;animation:sl-' + uid + ' 0.45s ease ' + delay + ' both;';
        if (typeof item === 'string') {
          return '<div style="' + base + 'padding:10px 14px;background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;font-size:0.9rem;color:#374151;">' + _markdownToHtml(item) + '</div>';
        }
        var icon = item.icon || '•';
        var text = item.text || item.label || '';
        var sub  = item.sub  || item.description || '';
        return '<div style="' + base + 'padding:12px 16px;background:#f9fafb;border:1px solid #e5e7eb;border-radius:10px;display:flex;gap:12px;align-items:flex-start;">'
          + '<span style="font-size:1.2rem;flex-shrink:0;line-height:1.4;">' + _esc(icon) + '</span>'
          + '<div><div style="font-size:0.9rem;font-weight:600;color:#111827;">' + _esc(text) + '</div>'
          + (sub ? '<div style="font-size:0.8rem;color:#6b7280;margin-top:2px;">' + _esc(sub) + '</div>' : '')
          + '</div></div>';
      }).join('')
    + '</div>';
};

_RENDERERS['liquid_button'] = function(b) {
  var label = b.text || b.label || b.title || 'Action';
  var color = b.color || '#6366f1';
  var uid = Math.random().toString(36).substr(2, 6);
  return '<style>'
    + '.lq-' + uid + '{background:' + _esc(color) + ';color:#fff;font-weight:700;font-size:0.95rem;padding:14px 36px;border:none;border-radius:50%;cursor:pointer;transition:border-radius 0.45s cubic-bezier(0.34,1.56,0.64,1),transform 0.2s ease,box-shadow 0.2s ease;box-shadow:0 4px 22px ' + _esc(color) + '55;}'
    + '.lq-' + uid + ':hover{border-radius:14px;transform:scale(1.05);box-shadow:0 6px 30px ' + _esc(color) + '77;}'
    + '.lq-' + uid + ':active{transform:scale(0.96);border-radius:50%;}'
    + '</style>'
    + '<div style="margin:1rem 0;text-align:center;"><button class="lq-' + uid + '">' + _esc(label) + '</button></div>';
};

_RENDERERS['highlight_sweep'] = function(b) {
  var text  = b.text  || b.content || '';
  var color = b.color || '#fef08a';
  var delay = parseFloat(b.delay !== undefined ? b.delay : 0.4);
  var size  = b.size  || '1.05rem';
  var uid = Math.random().toString(36).substr(2, 6);
  return '<style>'
    + '.hs-' + uid + '{background:linear-gradient(90deg,' + _esc(color) + ' 50%,transparent 50%);background-size:201% 100%;background-position:100% 0;animation:hs-' + uid + ' 0.75s ease ' + delay + 's forwards;padding:1px 3px;border-radius:3px;}'
    + '@keyframes hs-' + uid + '{to{background-position:0% 0;}}'
    + '</style>'
    + '<div style="margin:1rem 0;font-size:' + _esc(size) + ';line-height:1.75;color:#1f2937;">'
    + '<span class="hs-' + uid + '">' + _esc(text) + '</span>'
    + '</div>';
};

_RENDERERS['progress_reveal'] = function(b) {
  var value  = parseFloat(b.value !== undefined ? b.value : (b.percent !== undefined ? b.percent : 0));
  var label  = b.label || b.title || '';
  var color  = b.color || '#6366f1';
  var suffix = b.suffix !== undefined ? b.suffix : '%';
  var height = parseInt(b.height || 10, 10);
  var uid = Math.random().toString(36).substr(2, 6);
  return '<div id="pr-wrap-' + uid + '" style="margin:1rem 0;">'
    + '<div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:8px;">'
    + (label ? '<span style="font-size:0.875rem;font-weight:600;color:#374151;">' + _esc(label) + '</span>' : '<span></span>')
    + '<span id="pr-val-' + uid + '" style="font-size:0.875rem;font-weight:700;color:' + _esc(color) + ';">0' + _esc(String(suffix)) + '</span>'
    + '</div>'
    + '<div style="height:' + height + 'px;background:#f3f4f6;border-radius:999px;overflow:hidden;">'
    + '<div id="pr-bar-' + uid + '" style="height:100%;width:0%;background:' + _esc(color) + ';border-radius:999px;transition:width 1.3s cubic-bezier(0.34,1.1,0.64,1);"></div>'
    + '</div>'
    + '<script>(function(){'
    + 'var wrap=document.getElementById("pr-wrap-' + uid + '");'
    + 'var bar=document.getElementById("pr-bar-' + uid + '");'
    + 'var val=document.getElementById("pr-val-' + uid + '");'
    + 'var target=' + value + ';var suf="' + _esc(String(suffix)).replace(/"/g,'\\"') + '";var done=false;'
    + 'function run(){if(done)return;done=true;'
    + 'bar.style.width=Math.min(target,100)+"%";'
    + 'var t0=null,dur=1300;'
    + 'function step(ts){if(!t0)t0=ts;var p=Math.min((ts-t0)/dur,1);val.textContent=Math.round(target*p)+suf;if(p<1)requestAnimationFrame(step);}'
    + 'requestAnimationFrame(step);}'
    + 'if("IntersectionObserver" in window){new IntersectionObserver(function(es,ob){if(es[0].isIntersecting){run();ob.disconnect();}},{threshold:0.3}).observe(wrap);}else{run();}'
    + '})();<\/script>'
    + '</div>';
};

// ── High-impact visual atoms ─────────────────────────────────────────────────

_RENDERERS['big_reveal'] = function(b) {
  var text  = b.text  || b.value || b.label || '';
  var sub   = b.sub   || b.subtitle || '';
  var color = b.color || '#1f2937';
  var size  = b.size  || '5rem';
  var delay = parseFloat(b.delay !== undefined ? b.delay : 0.1);
  var uid = Math.random().toString(36).substr(2, 6);
  return '<style>@keyframes br-' + uid + '{from{opacity:0;transform:scale(0.35);}to{opacity:1;transform:scale(1);}}</style>'
    + '<div style="text-align:center;padding:44px 24px;margin:1rem 0;">'
    + '<div style="font-size:' + _esc(size) + ';font-weight:900;color:' + _esc(color) + ';line-height:1.05;animation:br-' + uid + ' 0.75s cubic-bezier(0.34,1.56,0.64,1) ' + delay + 's both;">' + _esc(text) + '</div>'
    + (sub ? '<div style="font-size:1.05rem;color:#6b7280;margin-top:14px;font-weight:500;animation:br-' + uid + ' 0.75s cubic-bezier(0.34,1.56,0.64,1) ' + (delay+0.18) + 's both;">' + _esc(sub) + '</div>' : '')
    + '</div>';
};

_RENDERERS['kinetic_headline'] = function(b) {
  var text  = b.text || b.title || '';
  var size  = b.size  || '2.6rem';
  var color = b.color || '#111827';
  var gap   = parseFloat(b.stagger !== undefined ? b.stagger : 0.08);
  var style = b.style || 'up';
  var uid = Math.random().toString(36).substr(2, 6);
  var fromT = style==='down'?'translateY(-22px)':style==='scale'?'scale(0.5)':style==='fade'?'none':'translateY(26px)';
  var words = text.split(' ');
  return '<style>@keyframes kh-' + uid + '{from{opacity:0;transform:' + fromT + ';}to{opacity:1;transform:none;}}</style>'
    + '<div style="margin:1rem 0;font-size:' + _esc(size) + ';font-weight:800;color:' + _esc(color) + ';line-height:1.2;">'
    + words.map(function(w, i) {
        return '<span style="display:inline-block;opacity:0;animation:kh-' + uid + ' 0.55s ease ' + (i*gap) + 's both;margin-right:0.22em;">' + _esc(w) + '</span>';
      }).join('')
    + '</div>';
};

_RENDERERS['text_reveal_mask'] = function(b) {
  var text  = b.text  || b.title || '';
  var size  = b.size  || '2rem';
  var color = b.color || '#111827';
  var delay = parseFloat(b.delay !== undefined ? b.delay : 0.2);
  var uid = Math.random().toString(36).substr(2, 6);
  return '<style>@keyframes trm-' + uid + '{from{clip-path:inset(0 100% 0 0);}to{clip-path:inset(0 0% 0 0);}}</style>'
    + '<div style="margin:1rem 0;overflow:hidden;">'
    + '<div style="font-size:' + _esc(size) + ';font-weight:800;color:' + _esc(color) + ';line-height:1.3;animation:trm-' + uid + ' 1s cubic-bezier(0.77,0,0.175,1) ' + delay + 's both;">' + _esc(text) + '</div>'
    + '</div>';
};

_RENDERERS['split_reveal'] = function(b) {
  var title = b.title || '';
  var text  = b.text  || b.content || '';
  var color = b.color || '#6366f1';
  var delay = parseFloat(b.delay !== undefined ? b.delay : 0.2);
  var uid = Math.random().toString(36).substr(2, 6);
  return '<style>'
    + '.sr-t-' + uid + '{position:absolute;top:0;left:0;right:0;height:51%;background:' + _esc(color) + ';z-index:2;animation:sr-top-' + uid + ' 0.75s cubic-bezier(0.77,0,0.175,1) ' + delay + 's both;}'
    + '.sr-b-' + uid + '{position:absolute;bottom:0;left:0;right:0;height:51%;background:' + _esc(color) + ';z-index:2;animation:sr-bot-' + uid + ' 0.75s cubic-bezier(0.77,0,0.175,1) ' + delay + 's both;}'
    + '@keyframes sr-top-' + uid + '{from{transform:translateY(0);}to{transform:translateY(-100%);}}'
    + '@keyframes sr-bot-' + uid + '{from{transform:translateY(0);}to{transform:translateY(100%);}}'
    + '</style>'
    + '<div style="position:relative;border-radius:16px;overflow:hidden;margin:1rem 0;">'
    + '<div style="padding:32px;background:#fff;border:1px solid #e5e7eb;border-radius:16px;">'
    + (title ? '<div style="font-size:1.2rem;font-weight:700;color:#111827;margin-bottom:10px;">' + _esc(title) + '</div>' : '')
    + (text  ? '<div style="color:#374151;line-height:1.7;">' + _markdownToHtml(text) + '</div>' : '')
    + '</div>'
    + '<div class="sr-t-' + uid + '"></div>'
    + '<div class="sr-b-' + uid + '"></div>'
    + '</div>';
};

_RENDERERS['glass_card'] = function(b) {
  var title = b.title || '';
  var text  = b.text  || b.content || '';
  var bg    = b.bg    || 'linear-gradient(135deg,#4f46e5,#7c3aed,#a21caf)';
  var uid = Math.random().toString(36).substr(2, 6);
  return '<div style="background:' + _esc(bg) + ';border-radius:20px;padding:32px;margin:1rem 0;position:relative;overflow:hidden;">'
    + '<div style="position:absolute;width:220px;height:220px;border-radius:50%;background:rgba(255,255,255,0.1);top:-60px;right:-60px;pointer-events:none;"></div>'
    + '<div style="position:absolute;width:160px;height:160px;border-radius:50%;background:rgba(255,255,255,0.07);bottom:-40px;left:-40px;pointer-events:none;"></div>'
    + '<div style="position:relative;z-index:1;background:rgba(255,255,255,0.1);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);border:1px solid rgba(255,255,255,0.22);border-radius:16px;padding:24px;">'
    + (title ? '<div style="font-size:1.1rem;font-weight:700;color:#fff;margin-bottom:10px;">' + _esc(title) + '</div>' : '')
    + (text  ? '<div style="color:rgba(255,255,255,0.88);line-height:1.7;font-size:0.9rem;">' + _markdownToHtml(text) + '</div>' : '')
    + '</div>'
    + '</div>';
};

_RENDERERS['mesh_gradient'] = function(b) {
  var title  = b.title  || '';
  var text   = b.text   || b.content || '';
  var bg     = b.bg     || '#0f0a1e';
  var colors = b.colors || ['#f43f5e','#6366f1','#22d3ee','#f59e0b'];
  var positions = ['12% 18%','82% 8%','18% 82%','78% 78%','50% 45%'];
  var gradients = colors.map(function(c, i) {
    return 'radial-gradient(ellipse 55% 45% at ' + positions[i % positions.length] + ',' + _esc(c) + '44,transparent)';
  }).join(',');
  return '<div style="border-radius:20px;overflow:hidden;padding:44px 36px;margin:1rem 0;background:' + _esc(bg) + ';background-image:' + gradients + ';">'
    + (title ? '<div style="font-size:1.3rem;font-weight:800;color:#fff;margin-bottom:12px;">' + _esc(title) + '</div>' : '')
    + (text  ? '<div style="color:rgba(255,255,255,0.82);line-height:1.75;">' + _markdownToHtml(text) + '</div>' : '')
    + '</div>';
};

_RENDERERS['marquee_strip'] = function(b) {
  var items = b.items || b.tags || b.words || [];
  var speed = parseInt(b.speed || 28, 10);
  var bg    = b.bg    || '#0f172a';
  var color = b.color || '#94a3b8';
  var sep   = b.separator || '·';
  var uid = Math.random().toString(36).substr(2, 6);
  var itemHtml = items.map(function(item) {
    var label = typeof item === 'string' ? item : (item.text || item.label || '');
    var icon  = typeof item === 'object' ? (item.icon || '') : '';
    return '<span style="padding:0 24px;white-space:nowrap;">' + (icon ? _esc(icon) + ' ' : '') + _esc(label) + ' <span style="opacity:0.3;margin-left:24px;">' + _esc(sep) + '</span></span>';
  }).join('');
  return '<style>'
    + '.mq-' + uid + '{display:flex;width:max-content;animation:mq-' + uid + ' ' + speed + 's linear infinite;}'
    + '.mq-' + uid + ':hover{animation-play-state:paused;}'
    + '@keyframes mq-' + uid + '{from{transform:translateX(0);}to{transform:translateX(-50%);}}'
    + '</style>'
    + '<div style="background:' + _esc(bg) + ';border-radius:12px;padding:14px 0;margin:1rem 0;overflow:hidden;color:' + _esc(color) + ';font-size:0.9rem;font-weight:500;">'
    + '<div class="mq-' + uid + '">' + itemHtml + itemHtml + '</div>'
    + '</div>';
};

_RENDERERS['stripe_background'] = function(b) {
  var title  = b.title  || '';
  var text   = b.text   || b.content || '';
  var color1 = b.color1 || '#6366f1';
  var color2 = b.color2 || '#4f46e5';
  var speed  = parseInt(b.speed || 5, 10);
  var uid = Math.random().toString(36).substr(2, 6);
  return '<style>'
    + '.strp-' + uid + '{background:repeating-linear-gradient(45deg,' + _esc(color1) + ',' + _esc(color1) + ' 10px,' + _esc(color2) + ' 10px,' + _esc(color2) + ' 20px);background-size:28px 28px;animation:strp-' + uid + ' ' + speed + 's linear infinite;}'
    + '@keyframes strp-' + uid + '{from{background-position:0 0;}to{background-position:56px 56px;}}'
    + '</style>'
    + '<div class="strp-' + uid + '" style="border-radius:16px;overflow:hidden;padding:40px 32px;margin:1rem 0;">'
    + '<div style="background:rgba(0,0,0,0.38);backdrop-filter:blur(2px);border-radius:12px;padding:24px;">'
    + (title ? '<div style="font-size:1.3rem;font-weight:700;color:#fff;margin-bottom:10px;">' + _esc(title) + '</div>' : '')
    + (text  ? '<div style="color:rgba(255,255,255,0.92);line-height:1.7;">' + _markdownToHtml(text) + '</div>' : '')
    + '</div>'
    + '</div>';
};

_RENDERERS['status_timeline'] = function(b) {
  var events = b.events || b.items || [];
  var title  = b.title || '';
  var uid = Math.random().toString(36).substr(2, 6);
  var dotColors = { done:'#22c55e', active:'#3b82f6', pending:'#d1d5db', error:'#ef4444', warning:'#f59e0b' };
  var bgColors  = { done:'#f0fdf4', active:'#eff6ff', pending:'#f9fafb', error:'#fef2f2', warning:'#fffbeb' };
  var bdColors  = { done:'#86efac', active:'#93c5fd', pending:'#e5e7eb', error:'#fecaca', warning:'#fde68a' };
  var evHtml = events.map(function(ev, i) {
    var status = ev.status || 'pending';
    var dot = dotColors[status] || dotColors.pending;
    var bg  = bgColors[status]  || bgColors.pending;
    var bd  = bdColors[status]  || bdColors.pending;
    var isLast = i === events.length - 1;
    var delay  = (i * 0.14) + 's';
    return '<div style="display:flex;gap:16px;opacity:0;animation:st-' + uid + ' 0.4s ease ' + delay + ' both;">'
      + '<div style="display:flex;flex-direction:column;align-items:center;flex-shrink:0;width:16px;">'
      + '<div style="width:14px;height:14px;border-radius:50%;background:' + dot + ';flex-shrink:0;margin-top:5px;' + (status==='active'?'box-shadow:0 0 0 4px '+dot+'33;':'') + '"></div>'
      + (!isLast ? '<div style="width:2px;flex:1;background:#e5e7eb;margin:4px 0;min-height:16px;"></div>' : '')
      + '</div>'
      + '<div style="background:' + bg + ';border:1px solid ' + bd + ';border-radius:10px;padding:12px 16px;flex:1;margin-bottom:' + (isLast?'0':'10px') + ';">'
      + (ev.title ? '<div style="font-size:0.9rem;font-weight:600;color:#111827;">' + _esc(ev.title) + '</div>' : '')
      + (ev.date  ? '<div style="font-size:0.72rem;color:' + dot + ';font-weight:600;text-transform:uppercase;letter-spacing:0.06em;margin-top:2px;">' + _esc(ev.date) + '</div>' : '')
      + (ev.text  ? '<div style="font-size:0.82rem;color:#6b7280;line-height:1.5;margin-top:5px;">' + _esc(ev.text) + '</div>' : '')
      + '</div>'
      + '</div>';
  }).join('');
  return '<style>@keyframes st-' + uid + '{from{opacity:0;transform:translateX(-14px);}to{opacity:1;transform:none;}}</style>'
    + '<div style="border:1px solid #e5e7eb;border-radius:12px;padding:20px;margin:1rem 0;">'
    + (title ? '<div style="font-size:1rem;font-weight:700;color:#111827;margin-bottom:16px;">' + _esc(title) + '</div>' : '')
    + evHtml + '</div>';
};

_RENDERERS['counter_group'] = function(b) {
  var stats = b.stats || b.items || [];
  var uid = Math.random().toString(36).substr(2, 6);
  var cellsHtml = stats.map(function(stat, i) {
    var val   = parseFloat(stat.value || stat.end || 0);
    var dec   = stat.decimals !== undefined ? parseInt(stat.decimals, 10) : (String(val).indexOf('.')>-1?String(val).split('.')[1].length:0);
    var pre   = stat.prefix  || '';
    var suf   = stat.suffix  || '';
    var label = stat.label   || stat.title || '';
    var color = stat.color   || '#6366f1';
    var notLast = i < stats.length - 1;
    return '<div style="flex:1;min-width:90px;text-align:center;padding:0 16px;' + (notLast?'border-right:1px solid #e5e7eb;':'') + '">'
      + '<div id="cg-' + uid + '-' + i + '" data-e="' + val + '" data-d="' + dec + '" data-p="' + _esc(pre) + '" data-s="' + _esc(suf) + '" style="font-size:2.4rem;font-weight:800;color:' + _esc(color) + ';line-height:1;">' + _esc(pre) + '0' + _esc(suf) + '</div>'
      + (label ? '<div style="font-size:0.78rem;color:#6b7280;font-weight:500;margin-top:6px;">' + _esc(label) + '</div>' : '')
      + '</div>';
  }).join('');
  return '<div id="cg-wrap-' + uid + '" style="border:1px solid #e5e7eb;border-radius:16px;padding:28px 8px;margin:1rem 0;display:flex;flex-wrap:wrap;gap:0;background:#fff;align-items:center;">'
    + cellsHtml
    + '</div>'
    + '<script>(function(){'
    + 'var wrap=document.getElementById("cg-wrap-' + uid + '");'
    + 'var n=' + stats.length + ';var els=[];for(var i=0;i<n;i++){var el=document.getElementById("cg-' + uid + '-"+i);if(el)els.push(el);}'
    + 'var done=false,dur=1600;'
    + 'function run(){if(done)return;done=true;var t0=null;'
    + 'function step(ts){if(!t0)t0=ts;var p=Math.min((ts-t0)/dur,1);var ease=p<0.5?2*p*p:1-Math.pow(-2*p+2,2)/2;'
    + 'els.forEach(function(el){var e=parseFloat(el.dataset.e||0),d=parseInt(el.dataset.d||0),p2=el.dataset.p||"",s=el.dataset.s||"";el.textContent=p2+(e*ease).toFixed(d)+s;});'
    + 'if(p<1)requestAnimationFrame(step);}'
    + 'requestAnimationFrame(step);}'
    + 'if("IntersectionObserver" in window){new IntersectionObserver(function(es,ob){if(es[0].isIntersecting){run();ob.disconnect();}},{threshold:0.3}).observe(wrap);}else{run();}'
    + '})();<\/script>';
};

_RENDERERS['orbit_diagram'] = function(b) {
  var center = b.center || 'Core';
  var nodes  = b.nodes  || b.items || [];
  var color  = b.color  || '#6366f1';
  var speed  = parseInt(b.speed || 10, 10);
  var uid = Math.random().toString(36).substr(2, 6);
  var n = Math.max(nodes.length, 1);
  var radius = 95;
  var size = 280;
  var cx = size / 2, cy = size / 2;
  var nodeElems = nodes.map(function(node, i) {
    var angle = (i / n) * 2 * Math.PI - Math.PI / 2;
    var x = Math.round(cx + Math.cos(angle) * radius);
    var y = Math.round(cy + Math.sin(angle) * radius);
    var label  = typeof node === 'string' ? node : (node.label || node.text || '');
    var nc     = typeof node === 'object' && node.color ? node.color : color;
    return '<div style="position:absolute;left:' + x + 'px;top:' + y + 'px;transform:translate(-50%,-50%);background:' + _esc(nc) + ';color:#fff;font-size:0.7rem;font-weight:700;padding:5px 11px;border-radius:20px;white-space:nowrap;box-shadow:0 2px 10px rgba(0,0,0,0.15);z-index:3;">' + _esc(label) + '</div>';
  }).join('');
  var svgLines = nodes.map(function(_, i) {
    var angle = (i / n) * 2 * Math.PI - Math.PI / 2;
    return '<line x1="' + cx + '" y1="' + cy + '" x2="' + Math.round(cx+Math.cos(angle)*radius) + '" y2="' + Math.round(cy+Math.sin(angle)*radius) + '" stroke="' + _esc(color) + '" stroke-width="1" opacity="0.18"/>';
  }).join('');
  return '<style>@keyframes orb-dash-' + uid + '{to{stroke-dashoffset:-24;}}</style>'
    + '<div style="display:flex;justify-content:center;margin:1rem 0;">'
    + '<div style="position:relative;width:' + size + 'px;height:' + size + 'px;">'
    + '<svg style="position:absolute;inset:0;width:100%;height:100%;" viewBox="0 0 ' + size + ' ' + size + '" xmlns="http://www.w3.org/2000/svg">'
    + svgLines
    + '<circle cx="' + cx + '" cy="' + cy + '" r="' + radius + '" fill="none" stroke="' + _esc(color) + '" stroke-width="1.5" stroke-dasharray="5 7" opacity="0.4" style="animation:orb-dash-' + uid + ' ' + (speed/4) + 's linear infinite;"/>'
    + '</svg>'
    + nodeElems
    + '<div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);background:' + _esc(color) + ';color:#fff;font-weight:700;font-size:0.85rem;width:68px;height:68px;border-radius:50%;display:flex;align-items:center;justify-content:center;text-align:center;box-shadow:0 4px 22px ' + _esc(color) + '55;z-index:5;">' + _esc(center) + '</div>'
    + '</div></div>';
};

_RENDERERS['noise_card'] = function(b) {
  var title = b.title || '';
  var text  = b.text  || b.content || '';
  var bg    = b.bg    || '#1e1b4b';
  var color = b.color || '#fff';
  var uid = Math.random().toString(36).substr(2, 6);
  return '<div style="position:relative;border-radius:16px;overflow:hidden;padding:28px;margin:1rem 0;background:' + _esc(bg) + ';">'
    + '<svg width="0" height="0" style="position:absolute;pointer-events:none;">'
    + '<defs><filter id="nf-' + uid + '" x="0%" y="0%" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency="0.7" numOctaves="4" stitchTiles="stitch" result="noise"/><feColorMatrix in="noise" type="saturate" values="0" result="grey"/><feBlend in="SourceGraphic" in2="grey" mode="overlay" result="blend"/><feComposite in="blend" in2="SourceGraphic" operator="in"/></filter></defs>'
    + '</svg>'
    + '<div style="position:absolute;inset:0;opacity:0.055;background:#aaa;filter:url(#nf-' + uid + ');pointer-events:none;"></div>'
    + '<div style="position:relative;z-index:1;">'
    + (title ? '<div style="font-size:1.1rem;font-weight:700;color:' + _esc(color) + ';margin-bottom:10px;">' + _esc(title) + '</div>' : '')
    + (text  ? '<div style="color:' + _esc(color) + 'cc;line-height:1.7;font-size:0.9rem;">' + _markdownToHtml(text) + '</div>' : '')
    + '</div>'
    + '</div>';
};

_RENDERERS['cursor_glow'] = function(b) {
  var color  = b.color  || '#6366f1';
  var size   = parseInt(b.size || 280, 10);
  var blur   = parseInt(b.blur || 80, 10);
  var opacity = parseFloat(b.opacity !== undefined ? b.opacity : 0.18);
  return '<style>'
    + '#a2ui-cg{position:fixed;pointer-events:none;border-radius:50%;background:radial-gradient(circle,' + _esc(color) + ',' + _esc(color) + '00 70%);width:' + size + 'px;height:' + size + 'px;transform:translate(-50%,-50%);filter:blur(' + blur + 'px);opacity:' + opacity + ';z-index:9998;transition:opacity 0.3s;}'
    + '</style>'
    + '<div id="a2ui-cg"></div>'
    + '<script>(function(){if(document.getElementById("a2ui-cg-init"))return;var m=document.createElement("meta");m.id="a2ui-cg-init";document.head.appendChild(m);'
    + 'var el=document.getElementById("a2ui-cg"),cx=0,cy=0,tx=0,ty=0,raf;'
    + 'document.addEventListener("mousemove",function(e){tx=e.clientX;ty=e.clientY;if(!raf)raf=requestAnimationFrame(loop);});'
    + 'document.addEventListener("mouseleave",function(){el.style.opacity="0";});'
    + 'document.addEventListener("mouseenter",function(){el.style.opacity="' + opacity + '";});'
    + 'function loop(){cx+=(tx-cx)*0.12;cy+=(ty-cy)*0.12;el.style.left=Math.round(cx)+"px";el.style.top=Math.round(cy)+"px";raf=null;if(Math.abs(tx-cx)>0.5||Math.abs(ty-cy)>0.5)raf=requestAnimationFrame(loop);}'
    + '})();<\/script>';
};

// ── comparison_morph ─────────────────────────────────────────────────────────

_RENDERERS['comparison_morph'] = function(b) {
  var before = b.before || {};
  var after  = b.after  || {};
  var title  = b.title  || '';
  var uid = Math.random().toString(36).substr(2, 6);
  return '<div style="margin:1rem 0;">'
    + (title ? '<div style="font-size:1rem;font-weight:700;color:#111827;margin-bottom:12px;">' + _esc(title) + '</div>' : '')
    + '<style>'
    + '.cm-after-' + uid + '{position:absolute;top:0;left:0;width:100%;height:100%;padding:22px;background:#f0fdf4;border:2px solid #86efac;border-radius:12px;clip-path:inset(0 50% 0 0);box-sizing:border-box;overflow:hidden;}'
    + '.cm-hdl-' + uid + '{position:absolute;top:0;left:50%;transform:translateX(-50%);height:100%;width:2px;background:#6366f1;pointer-events:none;}'
    + '.cm-hdl-' + uid + '::after{content:"\\u29FA";position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);background:#6366f1;color:#fff;font-size:0.75rem;padding:4px 8px;border-radius:20px;white-space:nowrap;}'
    + '</style>'
    + '<div style="position:relative;border-radius:12px;overflow:hidden;">'
    + '<div style="padding:22px;background:#fef2f2;border:2px solid #fecaca;border-radius:12px;">'
    + '<div style="font-size:0.72rem;font-weight:700;color:#dc2626;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">' + _esc(before.label || 'Before') + '</div>'
    + '<div style="font-size:0.9rem;color:#374151;line-height:1.65;">' + _markdownToHtml(before.text || '') + '</div>'
    + '</div>'
    + '<div class="cm-after-' + uid + '" id="cm-after-' + uid + '">'
    + '<div style="font-size:0.72rem;font-weight:700;color:#16a34a;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">' + _esc(after.label || 'After') + '</div>'
    + '<div style="font-size:0.9rem;color:#374151;line-height:1.65;">' + _markdownToHtml(after.text || '') + '</div>'
    + '</div>'
    + '<div class="cm-hdl-' + uid + '" id="cm-hdl-' + uid + '"></div>'
    + '</div>'
    + '<input type="range" min="0" max="100" value="50" style="width:100%;margin-top:10px;accent-color:#6366f1;cursor:pointer;"'
    + ' oninput="(function(v){document.getElementById(\'cm-after-' + uid + '\').style.clipPath=\'inset(0 \'+(100-v)+\'% 0 0)\';document.getElementById(\'cm-hdl-' + uid + '\').style.left=v+\'%\';})(this.value)">'
    + '</div>';
};

// word_cloud — static, local-input, or live Google Sheets backed
// Schema: { type:"word_cloud", words:[{text,weight}], sheet_url:"...", write_url:"...", poll:5, palette:["#..."], placeholder:"..." }
_RENDERERS['word_cloud'] = function(b) {
  var uid         = Math.random().toString(36).substr(2, 6);
  var palette     = b.palette || ['#6366f1','#8b5cf6','#ec4899','#f59e0b','#10b981','#3b82f6','#ef4444','#14b8a6'];
  var poll        = parseInt(b.poll || 5, 10) * 1000;
  var sheetUrl    = b.sheet_url || '';
  var writeUrl    = b.write_url || '';
  var ph          = b.placeholder || 'Type a word…';
  var accent      = b.accent || '#6366f1';
  var staticWords = b.words || [];
  var paletteJson = JSON.stringify(palette);
  var staticJson  = JSON.stringify(staticWords.map(function(w) {
    return { text: String(w.text || w.word || w.label || ''), weight: Number(w.weight || w.count || w.size || 1) };
  }));

  return '<style>'
    // cloud canvas: relative container, words absolutely placed
    + '#wc-' + uid + '{position:relative;width:100%;min-height:calc(100vh - 80px);overflow:hidden;}'
    + '#wc-' + uid + ' span{position:absolute;display:inline-block;border-radius:6px;padding:3px 10px;cursor:default;transition:transform 0.25s,opacity 0.25s;white-space:nowrap;}'
    + '#wc-' + uid + ' span:hover{transform:scale(1.22) rotate(0deg)!important;opacity:0.85;z-index:10;}'
    + '@keyframes wc-in-' + uid + '{from{opacity:0;transform:scale(0.3) rotate(var(--r));}to{opacity:1;transform:scale(1) rotate(var(--r));}}'
    // fixed bottom input bar — same purple as accent
    + '#wc-bar-' + uid + '{position:fixed;bottom:0;left:0;right:0;display:flex;gap:10px;padding:14px 20px;'
    + 'background:' + accent + ';z-index:9999;box-shadow:0 -4px 24px rgba(0,0,0,0.18);}'
    + '#wc-inp-' + uid + '{flex:1;padding:11px 16px;border:none;border-radius:10px;font-size:1rem;outline:none;'
    + 'background:rgba(255,255,255,0.18);color:#fff;caret-color:#fff;}'
    + '#wc-inp-' + uid + '::placeholder{color:rgba(255,255,255,0.6);}'
    + '#wc-inp-' + uid + ':focus{background:rgba(255,255,255,0.28);}'
    + '#wc-btn-' + uid + '{padding:11px 22px;background:#fff;color:' + accent + ';border:none;border-radius:10px;'
    + 'font-size:1rem;font-weight:700;cursor:pointer;transition:opacity 0.2s;white-space:nowrap;}'
    + '#wc-btn-' + uid + ':hover{opacity:0.88;}'
    + (sheetUrl ? '#wc-badge-' + uid + '{position:fixed;top:10px;right:14px;font-size:0.68rem;color:#9ca3af;z-index:9999;}' : '')
    + '</style>'
    + '<div id="wc-' + uid + '" data-static=\'' + staticJson.replace(/'/g, '&#39;') + '\' data-palette=\'' + paletteJson.replace(/'/g, '&#39;') + '\'></div>'
    + (sheetUrl ? '<div id="wc-badge-' + uid + '">● live</div>' : '')
    + '<div id="wc-bar-' + uid + '">'
    + '<input id="wc-inp-' + uid + '" type="text" placeholder="' + _esc(ph) + '" maxlength="40" autocomplete="off">'
    + '<button id="wc-btn-' + uid + '">Add ↵</button>'
    + '</div>'
    + '<script>(function(){'
    + 'var el=document.getElementById("wc-' + uid + '");'
    + 'var inp=document.getElementById("wc-inp-' + uid + '");'
    + 'var btn=document.getElementById("wc-btn-' + uid + '");'
    + 'var palette=JSON.parse(el.getAttribute("data-palette"));'
    + 'var staticWords=JSON.parse(el.getAttribute("data-static"));'
    + 'var sheetUrl=' + JSON.stringify(sheetUrl) + ';'
    + 'var writeUrl=' + JSON.stringify(writeUrl) + ';'
    + 'var poll=' + poll + ';'
    + 'var localWords=[];'

    + 'function rnd(min,max){return min+Math.random()*(max-min);}'

    + 'function render(words){'
    + '  if(!words||!words.length)return;'
    + '  var max=words.reduce(function(m,w){return Math.max(m,w.weight);},1);'
    + '  el.innerHTML="";'
    + '  var W=el.offsetWidth||window.innerWidth;'
    + '  var H=el.offsetHeight||Math.max(400,window.innerHeight-100);'
    + '  words.forEach(function(w,i){'
    + '    var norm=w.weight/max;'
    + '    var size=(0.8+norm*2.8).toFixed(2);'         // wider range: 0.8–3.6rem
    + '    var rot=rnd(-42,42).toFixed(1);'              // ±42° rotation
    + '    var col=palette[Math.floor(Math.random()*palette.length)];' // fully random color
    + '    var opacity=(0.55+Math.random()*0.45).toFixed(2);'          // random opacity 0.55–1
    + '    var left=rnd(3,88).toFixed(1);'
    + '    var top=rnd(2,88).toFixed(1);'
    + '    var sp=document.createElement("span");'
    + '    sp.textContent=w.text;'
    + '    sp.style.cssText="font-size:"+size+"rem;font-weight:"+(norm>0.5?"700":"400")+";color:"+col'
    + '      +";--r:"+rot+"deg;background:"+col+"22;opacity:"+opacity'
    + '      +";left:"+left+"%;top:"+top+"%;transform:rotate("+rot+"deg)"'
    + '      +";animation:wc-in-' + uid + ' 0.55s cubic-bezier(0.34,1.56,0.64,1) "+(i*0.035).toFixed(2)+"s both;";'
    + '    el.appendChild(sp);'
    + '  });'
    + '}'

    + 'function mergeLocal(remote){'
    + '  var map={};'
    + '  remote.forEach(function(w){map[w.text.toLowerCase()]=w;});'
    + '  localWords.forEach(function(w){'
    + '    var k=w.text.toLowerCase();'
    + '    if(!map[k])map[k]={text:w.text,weight:1};'
    + '  });'
    + '  return Object.values(map).sort(function(a,b){return b.weight-a.weight;});'
    + '}'

    + 'function parseCSV(csv){'
    + '  var lines=csv.trim().split("\\n").slice(1);'
    + '  var map={};'
    + '  lines.forEach(function(l){'
    + '    var cols=l.split(",");'
    + '    var word=(cols[0]||"").trim().replace(/^"|"$/g,"");'
    + '    var cnt=cols[1]?parseInt(cols[1].trim(),10):1;'
    + '    if(word)map[word]=(map[word]||0)+cnt;'
    + '  });'
    + '  return Object.keys(map).map(function(k){return{text:k,weight:map[k]};}).sort(function(a,b){return b.weight-a.weight;});'
    + '}'

    + 'function parseJSON(data){'
    + '  var arr=Array.isArray(data)?data:(data.words||[]);'
    + '  return arr.map(function(w){return{text:String(w.text||w.word||""),weight:Number(w.weight||w.count||1)};});'
    + '}'

    + 'function fetchAndRender(){'
    + '  fetch(sheetUrl)'
    + '  .then(function(r){var ct=r.headers.get("content-type")||"";return ct.indexOf("json")>-1?r.json().then(parseJSON):r.text().then(parseCSV);})'
    + '  .then(function(words){render(mergeLocal(words));})'
    + '  .catch(function(){});'
    + '}'

    + 'function submit(){'
    + '  var word=inp.value.trim();'
    + '  if(!word)return;'
    + '  inp.value="";inp.focus();'
    + '  localWords.push({text:word,weight:1});'
    + '  var cur=[];'
    + '  el.querySelectorAll("span").forEach(function(s){cur.push({text:s.textContent,weight:1});});'
    + '  render(mergeLocal(cur));'
    + '  if(writeUrl){'
    + '    fetch(writeUrl+"?word="+encodeURIComponent(word),{method:"GET",mode:"no-cors"}).catch(function(){});'
    + '  }'
    + '}'

    + 'btn.addEventListener("click",submit);'
    + 'inp.addEventListener("keydown",function(e){if(e.key==="Enter")submit();});'
    + 'if(staticWords.length){render(staticWords);}'
    + 'if(sheetUrl){fetchAndRender();setInterval(fetchAndRender,poll);}'
    + '})();<\/script>';
};

// quiz_set — multi-question MCQ with score, pass/fail result, badge, and URL branching
// Schema: { type:"quiz_set", title:"...", pass_score:70, accent:"#6366f1",
//   questions:[{question,options:[],correct(0-idx),explanation}],
//   on_pass:{title,message,badge,icon,url}, on_fail:{title,message,url} }
// on_pass.url / on_fail.url: navigate to a different encoded schema URL on result — enables static branching
_RENDERERS['quiz_set'] = function(b) {
  var uid       = Math.random().toString(36).substr(2, 6);
  var title     = b.title || 'Knowledge Check';
  var questions = b.questions || [];
  var passScore = parseInt(b.pass_score || 70, 10);
  var accent    = b.accent || '#6366f1';
  var onPass    = b.on_pass || {};
  var onFail    = b.on_fail || {};
  var qJson     = JSON.stringify(questions);
  var onPassJ   = JSON.stringify(onPass);
  var onFailJ   = JSON.stringify(onFail);

  return '<style>'
    + '#qs-wrap-' + uid + '{max-width:680px;margin:1.5rem auto;padding:28px;background:#fff;border-radius:14px;box-shadow:0 2px 24px rgba(0,0,0,0.07);}'
    + '#qs-title-' + uid + '{font-size:0.7rem;font-weight:700;color:#9ca3af;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:14px;}'
    + '#qs-prog-' + uid + '{height:5px;background:#e5e7eb;border-radius:3px;margin-bottom:22px;}'
    + '#qs-bar-' + uid + '{height:100%;background:' + accent + ';border-radius:3px;width:0%;transition:width 0.45s cubic-bezier(0.4,0,0.2,1);}'
    + '#qs-num-' + uid + '{font-size:0.72rem;font-weight:700;color:#9ca3af;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:10px;}'
    + '#qs-q-' + uid + '{font-size:1.08rem;font-weight:700;color:#111827;line-height:1.55;margin-bottom:18px;}'
    + '.qs-o-' + uid + '{display:block;width:100%;text-align:left;padding:12px 16px;margin-bottom:8px;background:#f9fafb;border:2px solid #e5e7eb;border-radius:10px;font-size:0.95rem;cursor:pointer;transition:all 0.15s;font-family:inherit;color:#374151;}'
    + '.qs-o-' + uid + ':hover:not([disabled]){border-color:' + accent + ';background:' + accent + '0d;}'
    + '.qs-ok-' + uid + '{border-color:#10b981!important;background:#ecfdf5!important;color:#065f46!important;font-weight:600;}'
    + '.qs-no-' + uid + '{border-color:#ef4444!important;background:#fef2f2!important;color:#991b1b!important;}'
    + '#qs-exp-' + uid + '{display:none;padding:12px 16px;background:#f0f9ff;border-left:3px solid ' + accent + ';font-size:0.875rem;color:#374151;line-height:1.65;margin:10px 0 14px;border-radius:0 8px 8px 0;}'
    + '#qs-next-' + uid + '{display:none;padding:10px 28px;background:' + accent + ';color:#fff;border:none;border-radius:8px;font-size:0.95rem;font-weight:600;cursor:pointer;font-family:inherit;transition:opacity 0.2s;}'
    + '#qs-next-' + uid + ':hover{opacity:0.87;}'
    + '#qs-result-' + uid + '{display:none;text-align:center;padding:8px 0;}'
    + '.qs-ring-' + uid + '{width:112px;height:112px;border-radius:50%;margin:0 auto 18px;display:flex;align-items:center;justify-content:center;font-size:1.9rem;font-weight:800;}'
    + '#qs-retry-' + uid + '{padding:9px 22px;background:transparent;color:#9ca3af;border:2px solid #e5e7eb;border-radius:8px;font-size:0.88rem;font-weight:600;cursor:pointer;font-family:inherit;margin-top:8px;transition:all 0.2s;}'
    + '#qs-retry-' + uid + ':hover{border-color:#9ca3af;color:#374151;}'
    + '</style>'
    + '<div id="qs-wrap-' + uid + '">'
    + '<div id="qs-title-' + uid + '">' + _esc(title) + '</div>'
    + '<div id="qs-prog-' + uid + '"><div id="qs-bar-' + uid + '"></div></div>'
    + '<div id="qs-num-' + uid + '"></div>'
    + '<div id="qs-q-' + uid + '"></div>'
    + '<div id="qs-opts-' + uid + '"></div>'
    + '<div id="qs-exp-' + uid + '"></div>'
    + '<button id="qs-next-' + uid + '">Next →</button>'
    + '<div id="qs-result-' + uid + '"></div>'
    + '</div>'
    + '<script>(function(){'
    + 'var questions=' + qJson + ';'
    + 'var passScore=' + passScore + ';'
    + 'var accent=' + JSON.stringify(accent) + ';'
    + 'var onPass=' + onPassJ + ';'
    + 'var onFail=' + onFailJ + ';'
    + 'var idx=0,score=0,answered=false;'
    + 'var bar=document.getElementById("qs-bar-' + uid + '");'
    + 'var numEl=document.getElementById("qs-num-' + uid + '");'
    + 'var qEl=document.getElementById("qs-q-' + uid + '");'
    + 'var optsEl=document.getElementById("qs-opts-' + uid + '");'
    + 'var expEl=document.getElementById("qs-exp-' + uid + '");'
    + 'var nextBtn=document.getElementById("qs-next-' + uid + '");'
    + 'var resultEl=document.getElementById("qs-result-' + uid + '");'

    + 'function reset(){'
    + '  idx=0;score=0;answered=false;'
    + '  [numEl,qEl,optsEl].forEach(function(e){e.style.display="";});'
    + '  nextBtn.style.display="none";expEl.style.display="none";'
    + '  resultEl.style.display="none";resultEl.innerHTML="";'
    + '  showQ(0);'
    + '}'

    + 'function showQ(i){'
    + '  answered=false;'
    + '  var q=questions[i];'
    + '  bar.style.width=Math.round((i/questions.length)*100)+"%";'
    + '  numEl.textContent="Question "+(i+1)+" of "+questions.length;'
    + '  qEl.textContent=q.question;'
    + '  expEl.style.display="none";nextBtn.style.display="none";optsEl.innerHTML="";'
    + '  q.options.forEach(function(opt,oi){'
    + '    var btn=document.createElement("button");'
    + '    btn.className="qs-o-' + uid + '";'
    + '    btn.textContent=opt;'
    + '    btn.addEventListener("click",function(){'
    + '      if(answered)return;answered=true;'
    + '      var ok=oi===q.correct;if(ok)score++;'
    + '      btn.classList.add(ok?"qs-ok-' + uid + '":"qs-no-' + uid + '");'
    + '      optsEl.querySelectorAll("button").forEach(function(b,bi){b.disabled=true;if(bi===q.correct)b.classList.add("qs-ok-' + uid + '");});'
    + '      if(q.explanation){expEl.textContent=q.explanation;expEl.style.display="block";}'
    + '      nextBtn.style.display="inline-block";'
    + '      nextBtn.textContent=i===questions.length-1?"See Results →":"Next →";'
    + '    });'
    + '    optsEl.appendChild(btn);'
    + '  });'
    + '}'

    + 'function showResult(){'
    + '  var pct=Math.round((score/questions.length)*100);'
    + '  var pass=pct>=passScore;'
    + '  var col=pass?"#10b981":"#ef4444";'
    + '  var cfg=pass?onPass:onFail;'
    + '  bar.style.width="100%";'
    + '  [numEl,qEl,optsEl,expEl,nextBtn].forEach(function(e){e.style.display="none";});'
    + '  resultEl.style.display="block";'
    + '  resultEl.innerHTML='
    + '    "<div class=\'qs-ring-' + uid + '\' style=\'background:"+col+"1a;color:"+col+";border:3px solid "+col+";\'>"+pct+"%</div>"'
    + '    +"<div style=\'font-size:1.22rem;font-weight:800;color:#111827;margin-bottom:6px;\'>"+(cfg.title||(pass?"Well done!":"Keep going!"))+"</div>"'
    + '    +"<div style=\'font-size:0.88rem;color:#6b7280;margin-bottom:18px;\'>"+score+" of "+questions.length+" correct"+(pass?" · Pass ✓":" · "+passScore+"% needed")+"</div>"'
    + '    +(cfg.message?"<div style=\'font-size:0.88rem;color:#374151;padding:12px 16px;background:#f9fafb;border-radius:8px;margin-bottom:16px;\'>"+cfg.message+"</div>":"")'
    + '    +(pass&&cfg.badge?"<div style=\'display:inline-flex;align-items:center;gap:8px;padding:10px 20px;background:"+col+"1a;border:2px solid "+col+";border-radius:10px;font-weight:700;color:"+col+";font-size:0.95rem;margin-bottom:18px;\'>"+(cfg.icon||"🏆")+" "+cfg.badge+"</div><br>":"")'
    // branch URL button (pass or fail) — if set, show a "Continue →" button that navigates to the next schema URL
    + '    +(cfg.url?"<a href=\'"+cfg.url+"\' style=\'display:inline-block;padding:10px 28px;background:"+col+";color:#fff;border-radius:8px;font-weight:700;font-size:0.95rem;text-decoration:none;margin-bottom:10px;\'>Continue →</a><br>":"")'
    + '    +"<button id=\'qs-retry-' + uid + '\' style=\'margin-top:8px;\'>Try again</button>";'
    + '  var rb=document.getElementById("qs-retry-' + uid + '");'
    + '  if(rb)rb.addEventListener("click",reset);'
    // also save pass/fail to localStorage keyed by title for lightweight progress
    + '  try{var k="qs-"+btoa(unescape(encodeURIComponent(' + JSON.stringify(title) + ')));localStorage.setItem(k,JSON.stringify({pct:pct,pass:pass,ts:Date.now()}));}catch(e){}'
    + '}'

    + 'nextBtn.addEventListener("click",function(){'
    + '  idx++;'
    + '  if(idx<questions.length){showQ(idx);}else{showResult();}'
    + '});'
    + 'showQ(0);'
    + '})();<\/script>';
};
```

---

## atoms_demo.gs — demo/meta atoms

```javascript
// === Meta Demo Kit — atoms for demoing the renderer itself ===
// All cross-surface compatible: GAS, Meet Stage, Web
// Depends on _RENDERERS and _esc() defined in atom.gs

// surface_unlocked — game-style "NEW SURFACE UNLOCKED" achievement notification
_RENDERERS['surface_unlocked'] = function(b) {
  var uid     = Math.random().toString(36).substr(2, 6);
  var icon    = b.icon    || '⚡';
  var surface = b.surface || 'New Surface';
  var sub     = b.sub     || 'NEW SURFACE UNLOCKED';
  var accent  = b.accent  || '#6366f1';
  return '<style>'
    + '@keyframes su-in-' + uid + '{0%{opacity:0;transform:translateY(-18px) scale(0.96);}100%{opacity:1;transform:none;}}'
    + '@keyframes su-glow-' + uid + '{0%,100%{box-shadow:0 0 0 0 ' + accent + '55;}60%{box-shadow:0 0 0 10px ' + accent + '00;}}'
    + '#su-' + uid + '{animation:su-in-' + uid + ' 0.5s cubic-bezier(0.34,1.56,0.64,1) both,su-glow-' + uid + ' 1.8s 0.5s ease-out 3;}'
    + '</style>'
    + '<div id="su-' + uid + '" style="margin:1.5rem 0;padding:22px 26px;background:' + accent + '12;border:2px solid ' + accent + ';border-radius:14px;display:flex;align-items:center;gap:22px;">'
    + '<div style="font-size:3rem;line-height:1;flex-shrink:0">' + icon + '</div>'
    + '<div>'
    + '<div style="font-size:0.6rem;font-weight:900;letter-spacing:0.22em;text-transform:uppercase;color:' + accent + ';margin-bottom:5px">' + _esc(sub) + '</div>'
    + '<div style="font-size:1.4rem;font-weight:800;color:var(--text);line-height:1.25">' + _esc(surface) + '</div>'
    + '</div>'
    + '</div>';
};

// schema_reveal — decodes the current page's ?p= URL parameter and displays the schema that built this page
_RENDERERS['schema_reveal'] = function(b) {
  var uid    = Math.random().toString(36).substr(2, 6);
  var title  = b.title || 'This page was built from this schema';
  var accent = b.accent || '#6366f1';
  return '<style>'
    + '#srev-' + uid + '{background:#0f172a;border-radius:12px;overflow:hidden;margin:1rem 0;}'
    + '#srev-hd-' + uid + '{display:flex;align-items:center;justify-content:space-between;padding:12px 16px;background:#1e293b;}'
    + '#srev-hd-' + uid + ' span{font-size:0.75rem;font-weight:600;color:#94a3b8;font-family:monospace;}'
    + '#srev-copy-' + uid + '{padding:4px 12px;background:' + accent + ';color:#fff;border:none;border-radius:5px;font-size:0.75rem;font-weight:600;cursor:pointer;font-family:inherit;}'
    + '#srev-body-' + uid + '{padding:16px;overflow-x:auto;max-height:420px;overflow-y:auto;}'
    + '#srev-pre-' + uid + '{margin:0;font-family:monospace;font-size:0.78rem;line-height:1.65;color:#e2e8f0;white-space:pre;}'
    + '#srev-none-' + uid + '{padding:16px;font-size:0.85rem;color:#64748b;font-family:monospace;}'
    + '</style>'
    + '<div style="font-size:0.72rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px;">' + _esc(title) + '</div>'
    + '<div id="srev-' + uid + '">'
    + '<div id="srev-hd-' + uid + '"><span>schema.json</span><button id="srev-copy-' + uid + '">Copy</button></div>'
    + '<div id="srev-body-' + uid + '"><pre id="srev-pre-' + uid + '"></pre><div id="srev-none-' + uid + '" style="display:none;">Schema not available.</div></div>'
    + '</div>'
    + '<script>(function(){'
    + 'var pre=document.getElementById("srev-pre-' + uid + '");'
    + 'var none=document.getElementById("srev-none-' + uid + '");'
    + 'var copyBtn=document.getElementById("srev-copy-' + uid + '");'
    + 'try{'
    + '  var schema=null;'
    + '  if(window.__A2UI_SCHEMA__){schema=window.__A2UI_SCHEMA__;}'
    + '  else{'
    + '    var m=window.location.search.match(/[?&]p=([^&]*)/);'
    + '    if(m){var b64=decodeURIComponent(m[1]);var bin=atob(b64);var bytes=new Uint8Array(bin.length);for(var i=0;i<bin.length;i++)bytes[i]=bin.charCodeAt(i);schema=JSON.parse(new TextDecoder().decode(bytes));}'
    + '  }'
    + '  if(!schema){none.style.display="block";pre.style.display="none";return;}'
    + '  pre.textContent=JSON.stringify(schema,null,2);'
    + '  copyBtn.onclick=function(){navigator.clipboard.writeText(pre.textContent).then(function(){copyBtn.textContent="Copied!";setTimeout(function(){copyBtn.textContent="Copy";},1500);});};'
    + '}catch(e){none.textContent="Could not decode schema: "+e.message;none.style.display="block";pre.style.display="none";}'
    + '})();<\/script>';
};

// url_anatomy — visually dissects the shareable URL into its parts
_RENDERERS['url_anatomy'] = function(b) {
  var uid    = Math.random().toString(36).substr(2, 6);
  var accent = b.accent || '#6366f1';
  return '<style>'
    + '#ua-' + uid + '{background:var(--surface);border:2px solid var(--border);border-radius:12px;padding:20px;margin:1rem 0;overflow:hidden;}'
    + '#ua-url-' + uid + '{font-family:monospace;font-size:0.78rem;word-break:break-all;color:var(--text);line-height:1.8;margin-bottom:16px;}'
    + '.ua-part-' + uid + '{display:inline;padding:2px 5px;border-radius:3px;}'
    + '.ua-label-row-' + uid + '{display:flex;gap:16px;flex-wrap:wrap;margin-top:4px;}'
    + '.ua-legend-' + uid + '{display:flex;align-items:center;gap:6px;font-size:0.72rem;color:var(--muted);}'
    + '.ua-dot-' + uid + '{width:10px;height:10px;border-radius:2px;flex-shrink:0;}'
    + '</style>'
    + '<div id="ua-' + uid + '">'
    + '<div style="font-size:0.7rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:0.1em;margin-bottom:10px;">How the URL works</div>'
    + '<div id="ua-url-' + uid + '">Loading current URL…</div>'
    + '<div class="ua-label-row-' + uid + '">'
    + '<div class="ua-legend-' + uid + '"><div class="ua-dot-' + uid + '" style="background:#bfdbfe;"></div>GAS endpoint (always running)</div>'
    + '<div class="ua-legend-' + uid + '"><div class="ua-dot-' + uid + '" style="background:#bbf7d0;"></div>?p= parameter</div>'
    + '<div class="ua-legend-' + uid + '"><div class="ua-dot-' + uid + '" style="background:' + accent + '44;"></div>base64 schema (the content)</div>'
    + '</div>'
    + '</div>'
    + '<script>(function(){'
    + 'var el=document.getElementById("ua-url-' + uid + '");'
    + 'var url=window.location.href;'
    + 'var pi=url.indexOf("?p=");'
    + 'if(pi>-1){'
    + '  var base=url.substring(0,pi);'
    + '  var payload=url.substring(pi+3);'
    + '  el.innerHTML="<span class=\'ua-part-' + uid + '\' style=\'background:#bfdbfe;color:#1e3a5f;\'>"+base+"</span>"'
    + '    +"<span class=\'ua-part-' + uid + '\' style=\'background:#bbf7d0;color:#14532d;\'>?p=</span>"'
    + '    +"<span class=\'ua-part-' + uid + '\' style=\'background:' + accent + '22;color:' + accent + ';\'>"+payload.substring(0,60)+(payload.length>60?"…":"")+"</span>";'
    + '}else{el.textContent=url;}'
    + '})();<\/script>';
};

// schema_qr — generates a QR code for the current page URL via Google Charts API
_RENDERERS['schema_qr'] = function(b) {
  var uid   = Math.random().toString(36).substr(2, 6);
  var size  = parseInt(b.size || 220, 10);
  var label = b.label || 'Scan to open this page on any device';
  var url   = b.url || '';
  var sub   = b.sub || '';
  if (url) {
    var src = 'https://chart.googleapis.com/chart?chs=' + size + 'x' + size + '&cht=qr&chl=' + encodeURIComponent(url) + '&choe=UTF-8&chld=M|2';
    return '<div style="text-align:center;padding:24px 16px;">'
      + '<img src="' + src + '" width="' + size + '" height="' + size + '" style="border-radius:10px;box-shadow:0 4px 20px rgba(0,0,0,0.1);">'
      + '<div style="font-size:0.88rem;font-weight:600;color:var(--text);margin-top:12px;">' + _esc(label) + '</div>'
      + (sub ? '<div style="font-size:0.78rem;color:var(--muted);margin-top:4px;">' + _esc(sub) + '</div>' : '')
      + '</div>';
  }
  return '<div id="sqr-' + uid + '" style="text-align:center;padding:24px 16px;">'
    + '<img id="sqr-img-' + uid + '" width="' + size + '" height="' + size + '" style="border-radius:10px;box-shadow:0 4px 20px rgba(0,0,0,0.1);">'
    + '<div style="font-size:0.88rem;font-weight:600;color:var(--text);margin-top:12px;">' + _esc(label) + '</div>'
    + (sub ? '<div style="font-size:0.78rem;color:var(--muted);margin-top:4px;">' + _esc(sub) + '</div>' : '')
    + '</div>'
    + '<script>(function(){'
    + 'var u=encodeURIComponent(window.location.href);'
    + 'document.getElementById("sqr-img-' + uid + '").src="https://chart.googleapis.com/chart?chs=' + size + 'x' + size + '&cht=qr&chl="+u+"&choe=UTF-8&chld=M|2";'
    + '})();<\/script>';
};

// take_away_card — bold single-insight card, designed to be screenshot-able
_RENDERERS['take_away_card'] = function(b) {
  var headline   = b.headline || b.text || b.quote || b.insight || '';
  var sub        = b.sub || b.author || b.source || '';
  var accent     = b.accent || '#6366f1';
  var size       = b.size || '1.9rem';
  var gradient   = b.gradient ? b.gradient : null;
  var textColor  = b.text_color || (gradient ? '#fff' : 'var(--text)');
  var bg         = gradient
    ? 'linear-gradient(135deg,' + gradient[0] + ',' + gradient[1] + ')'
    : 'linear-gradient(135deg,' + accent + '0f,' + accent + '1a)';
  var border     = gradient ? 'none' : '2px solid ' + accent + '33';
  return '<div style="background:' + bg + ';border:' + border + ';border-radius:16px;padding:36px 32px;margin:1.5rem 0;text-align:center;">'
    + '<div style="font-size:2rem;margin-bottom:16px;opacity:0.5;color:' + (gradient ? 'rgba(255,255,255,0.7)' : accent) + ';">❝</div>'
    + '<div style="font-size:' + _esc(size) + ';font-weight:800;color:' + textColor + ';line-height:1.25;letter-spacing:-0.02em;">' + _esc(headline) + '</div>'
    + (sub ? '<div style="font-size:0.82rem;font-weight:600;color:' + (gradient ? 'rgba(255,255,255,0.7)' : accent) + ';margin-top:16px;text-transform:uppercase;letter-spacing:0.1em;">' + _esc(sub) + '</div>' : '')
    + '</div>';
};

// next_step_strip — horizontal step guide with optional links
_RENDERERS['next_step_strip'] = function(b) {
  var steps  = b.steps || [];
  var accent = b.accent || '#6366f1';
  var html = '<div style="display:flex;gap:0;margin:1.5rem 0;border-radius:12px;overflow:hidden;border:1px solid var(--border);">';
  steps.forEach(function(s, i) {
    var isLast = i === steps.length - 1;
    html += '<div style="flex:1;padding:20px 18px;background:var(--surface);' + (!isLast ? 'border-right:1px solid var(--border);' : '') + '">'
      + '<div style="font-size:1.4rem;font-weight:900;color:' + accent + ';margin-bottom:6px;">' + _esc(String(s.number || (i + 1))) + '</div>'
      + '<div style="font-size:0.9rem;font-weight:700;color:var(--text);margin-bottom:4px;">' + _esc(s.label || '') + '</div>'
      + '<div style="font-size:0.8rem;color:var(--muted);">' + _esc(s.detail || s.action || '') + '</div>'
      + (s.url ? '<a href="' + _esc(s.url) + '" target="_top" style="display:inline-block;margin-top:10px;font-size:0.78rem;font-weight:600;color:' + accent + ';text-decoration:none;">Open →</a>' : '')
      + '</div>';
  });
  return html + '</div>';
};

// copy_prompt — displays a copyable text block (for sharing Gemini prompts)
_RENDERERS['copy_prompt'] = function(b) {
  var uid    = Math.random().toString(36).substr(2, 6);
  var label  = b.label || 'Copy this prompt';
  var prompt = b.prompt || b.text || b.content || '';
  var accent = b.accent || '#6366f1';
  return '<style>'
    + '#cp-wrap-' + uid + '{background:#0f172a;border-radius:12px;overflow:hidden;margin:1rem 0;}'
    + '#cp-hd-' + uid + '{display:flex;align-items:center;justify-content:space-between;padding:10px 16px;background:#1e293b;}'
    + '#cp-lbl-' + uid + '{font-size:0.75rem;font-weight:600;color:#94a3b8;}'
    + '#cp-btn-' + uid + '{padding:4px 12px;background:' + accent + ';color:#fff;border:none;border-radius:5px;font-size:0.75rem;font-weight:600;cursor:pointer;font-family:inherit;}'
    + '#cp-body-' + uid + '{padding:16px;font-family:monospace;font-size:0.82rem;color:#e2e8f0;line-height:1.7;white-space:pre-wrap;max-height:300px;overflow-y:auto;}'
    + '</style>'
    + '<div id="cp-wrap-' + uid + '">'
    + '<div id="cp-hd-' + uid + '"><span id="cp-lbl-' + uid + '">' + _esc(label) + '</span><button id="cp-btn-' + uid + '">Copy</button></div>'
    + '<div id="cp-body-' + uid + '" data-text="' + _esc(prompt) + '">' + _esc(prompt) + '</div>'
    + '</div>'
    + '<script>(function(){'
    + 'var btn=document.getElementById("cp-btn-' + uid + '");'
    + 'var text=document.getElementById("cp-body-' + uid + '").getAttribute("data-text");'
    + 'btn.onclick=function(){navigator.clipboard.writeText(text).then(function(){btn.textContent="Copied!";setTimeout(function(){btn.textContent="Copy";},1500);});};'
    + '})();<\/script>';
};

// atom_anatomy — shows a rendered output alongside its schema snippet
_RENDERERS['atom_anatomy'] = function(b) {
  var label  = b.label || 'atom';
  var schema = b.schema || {};
  var accent = b.accent || '#6366f1';
  var schemaStr = JSON.stringify(schema, null, 2);
  var rendered  = '';
  try { rendered = renderAtoms([schema]); } catch(e) { rendered = '<em style="color:var(--muted);">Could not render preview</em>'; }
  return '<div style="border:1px solid var(--border);border-radius:12px;overflow:hidden;margin:1rem 0;">'
    + '<div style="padding:8px 16px;background:var(--surface2);font-size:0.7rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:0.1em;border-bottom:1px solid var(--border);">' + _esc(label) + '</div>'
    + '<div style="display:flex;gap:0;">'
    + '<div style="flex:1;padding:20px;border-right:1px solid var(--border);min-width:0;">'
    + '<div style="font-size:0.68rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">Rendered</div>'
    + rendered
    + '</div>'
    + '<div style="flex:1;padding:20px;background:#0f172a;min-width:0;">'
    + '<div style="font-size:0.68rem;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">Schema</div>'
    + '<pre style="margin:0;font-family:monospace;font-size:0.72rem;color:#e2e8f0;white-space:pre-wrap;line-height:1.6;">' + _esc(schemaStr) + '</pre>'
    + '</div>'
    + '</div></div>';
};

// renderer_stats — static stats grid about the renderer/page
_RENDERERS['renderer_stats'] = function(b) {
  var stats  = b.stats || [];
  var accent = b.accent || '#6366f1';
  var sub    = b.sub || '';
  var html = '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:1px;background:var(--border);border-radius:12px;overflow:hidden;margin:1rem 0;">';
  stats.forEach(function(s) {
    html += '<div style="padding:20px 16px;background:var(--surface);text-align:center;">'
      + '<div style="font-size:1.7rem;font-weight:900;color:' + accent + ';line-height:1;">' + _esc(String(s.value || '')) + '</div>'
      + '<div style="font-size:0.75rem;color:var(--muted);margin-top:5px;font-weight:500;">' + _esc(s.label || '') + '</div>'
      + '</div>';
  });
  html += '</div>';
  if (sub) html += '<div style="font-size:0.75rem;color:var(--muted);text-align:center;margin-top:-8px;">' + _esc(sub) + '</div>';
  return html;
};

// prompt_to_schema — three panel stepped reveal: prompt → schema → output
_RENDERERS['prompt_to_schema'] = function(b) {
  var uid    = Math.random().toString(36).substr(2, 6);
  var prompt = b.prompt || 'Describe a page…';
  var schema = b.schema || '{ "blocks": [] }';
  var output = b.output || 'The rendered page';
  var accent = b.accent || '#6366f1';
  var labels = b.labels || ['Natural language', 'Generated schema', 'Rendered page'];
  var schemaStr = typeof schema === 'object' ? JSON.stringify(schema, null, 2) : String(schema);

  return '<style>'
    + '#pts-' + uid + '{display:flex;gap:0;border-radius:12px;overflow:hidden;border:1px solid var(--border);margin:1rem 0;}'
    + '.pts-panel-' + uid + '{flex:1;display:flex;flex-direction:column;}'
    + '.pts-hd-' + uid + '{padding:10px 14px;font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;border-bottom:1px solid var(--border);}'
    + '.pts-body-' + uid + '{flex:1;padding:16px;font-size:0.82rem;line-height:1.65;}'
    + '.pts-arrow-' + uid + '{display:flex;align-items:center;padding:0 8px;color:var(--muted);font-size:1.4rem;background:var(--surface2);}'
    + '</style>'
    + '<div id="pts-' + uid + '">'
    + '<div class="pts-panel-' + uid + '">'
    + '<div class="pts-hd-' + uid + '" style="background:#1e3a5f;color:#7dd3fc;">' + _esc(labels[0]) + '</div>'
    + '<div class="pts-body-' + uid + '" style="background:#0c2340;color:#bae6fd;font-style:italic;">"' + _esc(prompt) + '"</div>'
    + '</div>'
    + '<div class="pts-arrow-' + uid + '">→</div>'
    + '<div class="pts-panel-' + uid + '">'
    + '<div class="pts-hd-' + uid + '" style="background:#0f172a;color:#475569;">{ } &nbsp;' + _esc(labels[1]) + '</div>'
    + '<div class="pts-body-' + uid + '" style="background:#0f172a;"><pre style="margin:0;font-family:monospace;font-size:0.7rem;color:#94a3b8;white-space:pre-wrap;">' + _esc(schemaStr.substring(0, 320)) + (schemaStr.length > 320 ? '\n…' : '') + '</pre></div>'
    + '</div>'
    + '<div class="pts-arrow-' + uid + '">→</div>'
    + '<div class="pts-panel-' + uid + '">'
    + '<div class="pts-hd-' + uid + '" style="background:#14291e;color:#4ade80;">' + _esc(labels[2]) + '</div>'
    + '<div class="pts-body-' + uid + '" style="background:#0d1f16;color:#86efac;">' + _esc(output) + '</div>'
    + '</div>'
    + '</div>';
};

// before_after_stack — animated comparison: old stack items cross out, new way reveals
_RENDERERS['before_after_stack'] = function(b) {
  var uid          = Math.random().toString(36).substr(2, 6);
  var beforeLabel  = b.before_label || 'Traditional stack';
  var beforeItems  = b.items || b.before_items || ['Hosting','Framework','Deploy pipeline','Database','Auth','CDN','DevOps'];
  var afterLabel   = b.after_label  || 'This approach';
  var afterText    = b.result || b.after_text || 'A URL';
  var accent       = b.accent       || '#6366f1';
  var delay        = parseFloat(b.delay_ms || b.delay || 400) / (b.delay_ms ? 1 : 0.001);
  if (b.delay_ms) delay = parseInt(b.delay_ms, 10);
  else delay = parseFloat(b.delay || 0.4) * 1000;

  var leftItems = beforeItems.map(function(item, i) {
    return '<div id="bas-item-' + uid + '-' + i + '" style="display:flex;align-items:center;gap:8px;padding:7px 0;font-size:0.9rem;color:var(--text);transition:all 0.4s;">'
      + '<span style="color:var(--muted);font-size:0.75rem;">▸</span>' + _esc(item)
      + '</div>';
  }).join('');

  return '<style>'
    + '@keyframes bas-slide-' + uid + '{from{opacity:0;transform:translateX(30px);}to{opacity:1;transform:none;}}'
    + '#bas-after-' + uid + '{opacity:0;}'
    + '</style>'
    + '<div style="display:flex;gap:16px;margin:1.5rem 0;">'
    + '<div style="flex:1;padding:24px;background:#2d0f0f;border:2px solid #7f1d1d;border-radius:12px;">'
    + '<div style="font-size:0.72rem;font-weight:700;color:#f87171;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:14px;">' + _esc(beforeLabel) + '</div>'
    + '<div id="bas-before-' + uid + '">' + leftItems + '</div>'
    + '</div>'
    + '<div style="display:flex;align-items:center;font-size:1.5rem;color:var(--muted);padding:0 4px;">→</div>'
    + '<div id="bas-after-' + uid + '" style="flex:1;padding:24px;background:' + accent + '0d;border:2px solid ' + accent + '44;border-radius:12px;display:flex;align-items:center;justify-content:center;">'
    + '<div style="text-align:center;">'
    + '<div style="font-size:0.72rem;font-weight:700;color:' + accent + ';text-transform:uppercase;letter-spacing:0.1em;margin-bottom:14px;">' + _esc(afterLabel) + '</div>'
    + '<div style="font-size:2.2rem;font-weight:900;color:' + accent + ';">' + _esc(afterText) + '</div>'
    + '</div>'
    + '</div>'
    + '</div>'
    + '<script>(function(){'
    + 'var items=document.getElementById("bas-before-' + uid + '").children;'
    + 'var after=document.getElementById("bas-after-' + uid + '");'
    + 'var total=items.length;var i=0;'
    + 'function strike(){'
    + '  if(i<total){'
    + '    items[i].style.textDecoration="line-through";items[i].style.opacity="0.35";'
    + '    i++;setTimeout(strike,' + delay + ');'
    + '  } else {'
    + '    after.style.opacity="1";after.style.animation="bas-slide-' + uid + ' 0.6s ease";'
    + '  }'
    + '}'
    + 'if("IntersectionObserver" in window){'
    + '  new IntersectionObserver(function(es,ob){if(es[0].isIntersecting){setTimeout(strike,400);ob.disconnect();}},{threshold:0.3}).observe(after);'
    + '}else{setTimeout(strike,800);}'
    + '})();<\/script>';
};

// live_vote — Sheet-backed live voting with real-time results bar chart
_RENDERERS['live_vote'] = function(b) {
  var uid      = Math.random().toString(36).substr(2, 6);
  var question = b.question || 'What do you think?';
  var options  = b.options  || ['Yes', 'No'];
  var sheetUrl = b.sheet_url || '';
  var writeUrl = b.write_url || '';
  var poll     = parseInt(b.poll_interval || b.poll || 5000, 10);
  var accent   = b.accent || '#6366f1';
  var optsJson = JSON.stringify(options);

  var optBtns = options.map(function(o) {
    return '<button class="lv-opt-' + uid + '" data-opt="' + _esc(o) + '">' + _esc(o) + '</button>';
  }).join('');

  return '<style>'
    + '#lv-' + uid + '{max-width:620px;margin:1.5rem auto;padding:24px;background:var(--surface);border-radius:14px;box-shadow:0 2px 20px rgba(0,0,0,0.12);}'
    + '#lv-q-' + uid + '{font-size:1.05rem;font-weight:700;color:var(--text);margin-bottom:18px;line-height:1.5;}'
    + '#lv-btns-' + uid + '{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:20px;}'
    + '.lv-opt-' + uid + '{flex:1;padding:12px 8px;background:var(--surface2);border:2px solid var(--border);border-radius:10px;font-size:0.9rem;font-weight:600;cursor:pointer;transition:all 0.15s;font-family:inherit;color:var(--text);}'
    + '.lv-opt-' + uid + ':hover{border-color:' + accent + ';background:' + accent + '0d;}'
    + '.lv-voted-' + uid + '{border-color:' + accent + '!important;background:' + accent + '!important;color:#fff!important;}'
    + '#lv-results-' + uid + '{display:none;}'
    + '.lv-bar-row-' + uid + '{display:flex;align-items:center;gap:10px;margin-bottom:10px;}'
    + '.lv-bar-label-' + uid + '{font-size:0.82rem;font-weight:600;color:var(--text);min-width:60px;}'
    + '.lv-bar-track-' + uid + '{flex:1;height:26px;background:var(--surface2);border-radius:6px;overflow:hidden;}'
    + '.lv-bar-fill-' + uid + '{height:100%;background:' + accent + ';border-radius:6px;transition:width 0.6s cubic-bezier(0.4,0,0.2,1);display:flex;align-items:center;padding-left:8px;}'
    + '.lv-bar-pct-' + uid + '{font-size:0.72rem;font-weight:700;color:#fff;}'
    + '#lv-total-' + uid + '{font-size:0.72rem;color:var(--muted);text-align:right;margin-top:6px;}'
    + '</style>'
    + '<div id="lv-' + uid + '">'
    + '<div id="lv-q-' + uid + '">' + _esc(question) + '</div>'
    + '<div id="lv-btns-' + uid + '">' + optBtns + '</div>'
    + '<div id="lv-results-' + uid + '">'
    + options.map(function(o, i) {
        return '<div class="lv-bar-row-' + uid + '">'
          + '<div class="lv-bar-label-' + uid + '">' + _esc(o) + '</div>'
          + '<div class="lv-bar-track-' + uid + '"><div id="lv-fill-' + uid + '-' + i + '" class="lv-bar-fill-' + uid + '" style="width:0%"><span class="lv-bar-pct-' + uid + '" id="lv-pct-' + uid + '-' + i + '">0%</span></div></div>'
          + '</div>';
      }).join('')
    + '<div id="lv-total-' + uid + '">0 votes</div>'
    + '</div>'
    + '</div>'
    + '<script>(function(){'
    + 'var opts=' + optsJson + ';'
    + 'var sheetUrl=' + JSON.stringify(sheetUrl) + ';'
    + 'var writeUrl=' + JSON.stringify(writeUrl) + ';'
    + 'var poll=' + poll + ';'
    + 'var voted=false;'
    + 'var counts={};opts.forEach(function(o){counts[o]=0;});'
    + 'var btns=document.querySelectorAll(".lv-opt-' + uid + '");'
    + 'var resultsEl=document.getElementById("lv-results-' + uid + '");'

    + 'function updateBars(){'
    + '  var total=opts.reduce(function(s,o){return s+(counts[o]||0);},0);'
    + '  opts.forEach(function(o,i){'
    + '    var pct=total?Math.round((counts[o]||0)/total*100):0;'
    + '    document.getElementById("lv-fill-' + uid + '-"+i).style.width=pct+"%";'
    + '    document.getElementById("lv-pct-' + uid + '-"+i).textContent=pct+"% ("+(counts[o]||0)+")";'
    + '  });'
    + '  document.getElementById("lv-total-' + uid + '").textContent=total+" vote"+(total!==1?"s":"");'
    + '}'

    + 'function parseCSV(csv){'
    + '  var lines=csv.trim().split("\\n").slice(1);'
    + '  var map={};'
    + '  lines.forEach(function(l){var c=l.split(",");var o=(c[0]||"").trim().replace(/^"|"$/g,"");var n=parseInt(c[1]||"1",10);if(o)map[o]=(map[o]||0)+n;});'
    + '  return map;'
    + '}'

    + 'function fetchResults(){'
    + '  fetch(sheetUrl).then(function(r){return r.text();}).then(function(t){'
    + '    var m=parseCSV(t);opts.forEach(function(o){counts[o]=m[o]||0;});updateBars();'
    + '  }).catch(function(){});'
    + '}'

    + 'btns.forEach(function(btn){'
    + '  btn.addEventListener("click",function(){'
    + '    if(voted)return;voted=true;'
    + '    var opt=btn.getAttribute("data-opt");'
    + '    counts[opt]=(counts[opt]||0)+1;'
    + '    btn.classList.add("lv-voted-' + uid + '");'
    + '    btns.forEach(function(b){b.disabled=true;});'
    + '    resultsEl.style.display="block";updateBars();'
    + '    if(writeUrl)fetch(writeUrl+"?option="+encodeURIComponent(opt),{method:"GET",mode:"no-cors"}).catch(function(){});'
    + '  });'
    + '});'

    + 'if(sheetUrl){fetchResults();setInterval(fetchResults,poll);}'
    + '})();<\/script>';
};

// reaction_shower — emoji reaction buttons, reactions rain down the screen, Sheet-backed totals
_RENDERERS['reaction_shower'] = function(b) {
  var uid       = Math.random().toString(36).substr(2, 6);
  var reactions = b.reactions || ['🔥', '💡', '🤯', '👏'];
  var writeUrl  = b.write_url || '';
  var sheetUrl  = b.sheet_url || '';
  var poll      = parseInt(b.poll_interval || b.poll || 4000, 10);
  var accent    = b.accent || '#6366f1';
  var countsJson = JSON.stringify(reactions.reduce(function(m, r) { m[r] = 0; return m; }, {}));

  return '<style>'
    + '#rs-' + uid + '{position:relative;overflow:hidden;}'
    + '#rs-btns-' + uid + '{display:flex;gap:12px;justify-content:center;flex-wrap:wrap;padding:20px;}'
    + '.rs-btn-' + uid + '{font-size:2rem;padding:10px 18px;background:var(--surface);border:2px solid var(--border);border-radius:12px;cursor:pointer;transition:transform 0.15s,border-color 0.15s;line-height:1;}'
    + '.rs-btn-' + uid + ':hover{transform:scale(1.18);border-color:' + accent + ';}'
    + '.rs-btn-' + uid + ':active{transform:scale(0.95);}'
    + '#rs-counts-' + uid + '{display:flex;gap:16px;justify-content:center;padding:0 20px 16px;flex-wrap:wrap;}'
    + '.rs-count-' + uid + '{font-size:0.8rem;color:var(--muted);}'
    + '@keyframes rs-fall-' + uid + '{0%{transform:translateY(-30px) rotate(0deg);opacity:1;}100%{transform:translateY(100vh) rotate(720deg);opacity:0;}}'
    + '.rs-particle-' + uid + '{position:fixed;pointer-events:none;font-size:2rem;z-index:9999;animation:rs-fall-' + uid + ' 2.2s ease-in forwards;}'
    + '</style>'
    + '<div id="rs-' + uid + '">'
    + '<div id="rs-btns-' + uid + '">'
    + reactions.map(function(r) {
        return '<button class="rs-btn-' + uid + '" data-r="' + _esc(r) + '">' + r + '</button>';
      }).join('')
    + '</div>'
    + '<div id="rs-counts-' + uid + '">'
    + reactions.map(function(r, i) {
        return '<span class="rs-count-' + uid + '">' + r + ' <span id="rs-c-' + uid + '-' + i + '">0</span></span>';
      }).join('')
    + '</div>'
    + '</div>'
    + '<script>(function(){'
    + 'var reactions=' + JSON.stringify(reactions) + ';'
    + 'var counts=' + countsJson + ';'
    + 'var writeUrl=' + JSON.stringify(writeUrl) + ';'
    + 'var sheetUrl=' + JSON.stringify(sheetUrl) + ';'
    + 'var poll=' + poll + ';'

    + 'function shower(emoji){'
    + '  for(var i=0;i<6+Math.floor(Math.random()*6);i++)(function(){'
    + '    var el=document.createElement("div");'
    + '    el.className="rs-particle-' + uid + '";'
    + '    el.textContent=emoji;'
    + '    el.style.left=(10+Math.random()*80)+"%";'
    + '    el.style.top="-40px";'
    + '    el.style.animationDelay=(Math.random()*0.5)+"s";'
    + '    document.body.appendChild(el);'
    + '    setTimeout(function(){el.remove();},3000);'
    + '  })();'
    + '}'

    + 'function updateCounts(){'
    + '  reactions.forEach(function(r,i){'
    + '    var el=document.getElementById("rs-c-' + uid + '-"+i);'
    + '    if(el)el.textContent=counts[r]||0;'
    + '  });'
    + '}'

    + 'document.querySelectorAll(".rs-btn-' + uid + '").forEach(function(btn){'
    + '  btn.addEventListener("click",function(){'
    + '    var r=btn.getAttribute("data-r");'
    + '    counts[r]=(counts[r]||0)+1;'
    + '    shower(r);updateCounts();'
    + '    if(writeUrl)fetch(writeUrl+"?reaction="+encodeURIComponent(r),{method:"GET",mode:"no-cors"}).catch(function(){});'
    + '  });'
    + '});'

    + 'function fetchCounts(){'
    + '  fetch(sheetUrl).then(function(r){return r.text();}).then(function(t){'
    + '    var lines=t.trim().split("\\n").slice(1);'
    + '    lines.forEach(function(l){var c=l.split(",");var k=(c[0]||"").trim().replace(/^"|"$/g,"");var v=parseInt(c[1]||"0",10);if(k)counts[k]=v;});'
    + '    updateCounts();'
    + '  }).catch(function(){});'
    + '}'

    + 'if(sheetUrl){fetchCounts();setInterval(fetchCounts,poll);}'
    + 'updateCounts();'
    + '})();<\/script>';
};

// raise_hand — single button Sheet counter
_RENDERERS['raise_hand'] = function(b) {
  var uid      = Math.random().toString(36).substr(2, 6);
  var question = b.question || 'Raise your hand';
  var label    = b.label || '✋ Raise hand';
  var writeUrl = b.write_url || '';
  var sheetUrl = b.sheet_url || '';
  var poll     = parseInt(b.poll_interval || b.poll || 4000, 10);
  var accent   = b.accent || '#6366f1';

  return '<div style="text-align:center;padding:28px 20px;margin:1rem 0;">'
    + '<div style="font-size:1rem;font-weight:700;color:var(--text);margin-bottom:20px;">' + _esc(question) + '</div>'
    + '<button id="rh-btn-' + uid + '" style="font-size:1.5rem;padding:16px 32px;background:var(--surface);border:2px solid var(--border);border-radius:14px;cursor:pointer;transition:all 0.15s;font-family:inherit;color:var(--text);display:inline-block;">' + _esc(label) + '</button>'
    + '<div style="margin-top:16px;font-size:2rem;font-weight:900;color:' + accent + ';" id="rh-count-' + uid + '">0</div>'
    + '<div style="font-size:0.78rem;color:var(--muted);">hands raised</div>'
    + '</div>'
    + '<script>(function(){'
    + 'var btn=document.getElementById("rh-btn-' + uid + '");'
    + 'var countEl=document.getElementById("rh-count-' + uid + '");'
    + 'var writeUrl=' + JSON.stringify(writeUrl) + ';'
    + 'var sheetUrl=' + JSON.stringify(sheetUrl) + ';'
    + 'var poll=' + poll + ';'
    + 'var raised=false;var count=0;'
    + 'btn.addEventListener("click",function(){'
    + '  if(raised)return;raised=true;count++;'
    + '  btn.style.borderColor="' + accent + '";btn.style.background="' + accent + '0d";'
    + '  countEl.textContent=count;'
    + '  if(writeUrl)fetch(writeUrl+"?hand=1",{method:"GET",mode:"no-cors"}).catch(function(){});'
    + '});'
    + 'function fetchCount(){'
    + '  fetch(sheetUrl).then(function(r){return r.text();}).then(function(t){'
    + '    var lines=t.trim().split("\\n").slice(1);var total=0;'
    + '    lines.forEach(function(l){var c=l.split(",");total+=parseInt(c[1]||"1",10)||1;});'
    + '    count=total;countEl.textContent=total;'
    + '  }).catch(function(){});'
    + '}'
    + 'if(sheetUrl){fetchCount();setInterval(fetchCount,poll);}'
    + '})();<\/script>';
};

// surface_map — visual diagram of the A2UI surfaces
_RENDERERS['surface_map'] = function(b) {
  var accent  = b.accent  || '#6366f1';
  var title   = b.title   || 'One schema. Three surfaces.';
  var surfaces = b.surfaces || [
    { name: 'GAS Web App',       icon: '⚡', desc: 'Live web app · GAS runtime · URL = content', color: '#6366f1' },
    { name: 'Meet Stage',        icon: '📺', desc: 'Full-screen · Live demos · Audience view',   color: '#8b5cf6' },
    { name: 'Google Sites HTML', icon: '📄', desc: 'Blog / docs · SEO · Static publish',         color: '#3b82f6' },
    { name: 'Google Chat',       icon: '💬', desc: 'Cards · Bots · Workspace native',            color: '#06b6d4' }
  ];

  // Google Workspace product SVGs — colors from official gstatic icons
  // Apps Script: 4-color (blue/red/yellow/green), Meet: yellow #FBBC04,
  // Sites: purple #4758B5, Chat: green #34A853
  var _gas  = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 28 28" width="28" height="28"><mask id="mgas"><rect width="28" height="28" rx="6" fill="white"/></mask><g mask="url(#mgas)"><rect width="14" height="14" fill="#4285F4"/><rect x="14" width="14" height="14" fill="#EA4335"/><rect y="14" width="14" height="14" fill="#FBBC04"/><rect x="14" y="14" width="14" height="14" fill="#34A853"/></g><path d="M10 9L6 14l4 5M18 9l4 5-4 5" stroke="white" stroke-width="2.2" stroke-linecap="round" fill="none"/></svg>';
  var _meet = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 28 28" width="28" height="28"><rect width="28" height="28" rx="6" fill="#FBBC04"/><rect x="4" y="9" width="14" height="10" rx="2" fill="white"/><path d="M18 12.5l6-3.5v10l-6-3.5z" fill="white"/></svg>';
  var _sites= '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 28 28" width="28" height="28"><rect width="28" height="28" rx="6" fill="#4758B5"/><rect x="6" y="6" width="7" height="7" rx="1" fill="white"/><rect x="15" y="6" width="7" height="7" rx="1" fill="white"/><rect x="6" y="15" width="7" height="7" rx="1" fill="white"/><rect x="15" y="15" width="7" height="7" rx="1" fill="white"/></svg>';
  var _chat = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 28 28" width="28" height="28"><rect width="28" height="28" rx="6" fill="#34A853"/><path d="M5 9a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-8l-4 3v-3H7a2 2 0 01-2-2z" fill="white"/></svg>';
  var _SVG = {
    'GAS Web App': _gas, 'Google Apps Script': _gas,
    'Meet Stage':  _meet, 'Google Meet': _meet,
    'Google Sites HTML': _sites, 'Google Sites': _sites, 'Web Article': _sites,
    'Google Chat': _chat
  };

  var html = '<div style="margin:1.5rem 0;">'
    + '<div style="font-size:0.72rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:0.12em;text-align:center;margin-bottom:16px;">' + _esc(title) + '</div>'
    + '<div style="display:flex;align-items:center;justify-content:center;gap:0;flex-wrap:wrap;">'
    + '<div style="padding:14px 20px;background:#0f172a;border-radius:10px;text-align:center;margin-right:8px;">'
    + '<div style="font-size:0.65rem;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:4px;">Schema</div>'
    + '<div style="font-family:monospace;font-size:0.72rem;color:#94a3b8;">{ blocks: […] }</div>'
    + '</div>'
    + '<div style="font-size:1.2rem;color:var(--muted);margin-right:8px;">→</div>';

  surfaces.forEach(function(s, i) {
    var iconHtml = _SVG[s.name]
      ? '<div style="margin-bottom:6px;display:flex;justify-content:center;">' + _SVG[s.name] + '</div>'
      : '<div style="font-size:1.6rem;margin-bottom:4px;">' + s.icon + '</div>';
    html += '<div style="flex:1;min-width:120px;padding:16px 14px;background:' + s.color + '0d;border:2px solid ' + s.color + '33;border-radius:10px;text-align:center;' + (i < surfaces.length - 1 ? 'margin-right:8px;' : '') + '">'
      + iconHtml
      + '<div style="font-size:0.8rem;font-weight:700;color:' + s.color + ';margin-bottom:4px;">' + _esc(s.name) + '</div>'
      + '<div style="font-size:0.7rem;color:var(--muted);line-height:1.5;">' + _esc(s.desc) + '</div>'
      + '</div>';
  });

  return html + '</div></div>';
};

// speed_counter — stopwatch that freezes when the page finishes loading
_RENDERERS['speed_counter'] = function(b) {
  var uid    = Math.random().toString(36).substr(2, 6);
  var label  = b.label  || 'Page loaded in';
  var sub    = b.sub    || '';
  var accent = b.accent || '#6366f1';
  return '<div style="text-align:center;padding:28px 20px;margin:1rem 0;">'
    + '<div style="font-size:0.72rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:0.1em;margin-bottom:10px;">' + _esc(label) + '</div>'
    + '<div id="sc-' + uid + '" style="font-size:3.5rem;font-weight:900;color:' + accent + ';font-variant-numeric:tabular-nums;letter-spacing:-0.02em;line-height:1;">0.0s</div>'
    + (sub ? '<div style="font-size:0.82rem;color:var(--muted);margin-top:8px;">' + _esc(sub) + '</div>' : '')
    + '</div>'
    + '<script>(function(){'
    + 'var el=document.getElementById("sc-' + uid + '");'
    + 'var t0=window.performance&&performance.timing?performance.timing.navigationStart:Date.now();'
    + 'function fmt(ms){var s=ms/1000;return s<60?s.toFixed(2)+"s":Math.floor(s/60)+"m "+Math.round(s%60)+"s";}'
    + 'var iv=setInterval(function(){el.textContent=fmt(Date.now()-t0);},50);'
    + 'window.addEventListener("load",function(){'
    + '  clearInterval(iv);'
    + '  el.textContent=fmt(Date.now()-t0);'
    + '});'
    + '})();<\/script>';
};

// live_edit — embedded mini schema editor with live rendered preview
_RENDERERS['live_edit'] = function(b) {
  var uid         = Math.random().toString(36).substr(2, 6);
  var placeholder = b.placeholder || '{ "type": "heading", "level": 1, "text": "Hello" }';
  var accent      = b.accent || '#6366f1';
  var rendererUrl = b.renderer_url || '';

  return '<style>'
    + '#le-' + uid + '{border:1px solid var(--border);border-radius:12px;overflow:hidden;margin:1rem 0;}'
    + '#le-hd-' + uid + '{padding:10px 16px;background:#1e293b;display:flex;align-items:center;justify-content:space-between;}'
    + '#le-hd-' + uid + ' span{font-size:0.72rem;font-weight:700;color:#94a3b8;}'
    + '#le-ta-' + uid + '{width:100%;height:130px;background:#0f172a;border:none;padding:14px;color:#e2e8f0;font-family:monospace;font-size:0.8rem;resize:none;outline:none;border-bottom:1px solid #1e293b;}'
    + '#le-preview-' + uid + '{min-height:80px;padding:20px;background:var(--bg);}'
    + '#le-err-' + uid + '{display:none;padding:8px 16px;background:#2d0f0f;font-size:0.78rem;color:#f87171;font-family:monospace;}'
    + '#le-run-' + uid + '{padding:5px 14px;background:' + accent + ';color:#fff;border:none;border-radius:5px;font-size:0.75rem;font-weight:600;cursor:pointer;font-family:inherit;}'
    + '</style>'
    + '<div id="le-' + uid + '">'
    + '<div id="le-hd-' + uid + '"><span>live editor — type a single atom JSON block</span><button id="le-run-' + uid + '">Render ▶</button></div>'
    + '<textarea id="le-ta-' + uid + '" spellcheck="false" placeholder=\'' + _esc(placeholder) + '\'></textarea>'
    + '<div id="le-err-' + uid + '"></div>'
    + '<div id="le-preview-' + uid + '"><span style="color:var(--muted);font-size:0.82rem;">Preview will appear here…</span></div>'
    + '</div>'
    + '<script>(function(){'
    + 'var ta=document.getElementById("le-ta-' + uid + '");'
    + 'var preview=document.getElementById("le-preview-' + uid + '");'
    + 'var err=document.getElementById("le-err-' + uid + '");'
    + 'var btn=document.getElementById("le-run-' + uid + '");'
    + 'var rendererUrl=' + JSON.stringify(rendererUrl) + ';'
    + 'function run(){'
    + '  try{'
    + '    var obj=JSON.parse(ta.value.trim()||"{}");'
    + '    err.style.display="none";'
    + '    if(!rendererUrl){preview.innerHTML="<em style=\'color:#9ca3af;font-size:0.82rem;\'>Set renderer_url to enable live preview</em>";return;}'
    + '    var schema={blocks:[obj]};'
    + '    var enc=btoa(unescape(encodeURIComponent(JSON.stringify(schema))));'
    + '    preview.innerHTML="<iframe src=\'"+rendererUrl+"?p="+encodeURIComponent(enc)+"\' style=\'width:100%;min-height:120px;border:none;\' frameborder=\'0\'></iframe>";'
    + '  }catch(e){err.textContent=e.message;err.style.display="block";}'
    + '}'
    + 'btn.addEventListener("click",run);'
    + 'ta.addEventListener("keydown",function(e){if(e.key==="Enter"&&(e.ctrlKey||e.metaKey))run();});'
    + '})();<\/script>';
};
```

---

