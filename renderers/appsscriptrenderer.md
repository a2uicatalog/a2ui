# Apps Script Web App Renderer — Spec

## What this surface is

A Google Apps Script **Web App** is not a webpage served from a CDN. It is:

- A `.gs` (V8 JavaScript) file that implements `doGet(e)` and returns an `HtmlOutput` via `HtmlService`
- HTML served from Google's own domain, sandboxed in an IFRAME
- Backed by full Workspace server APIs: `DriveApp`, `SpreadsheetApp`, `GmailApp`, `Session`, `UrlFetchApp`, `PropertiesService`
- Client ↔ server communication exclusively via `google.script.run.functionName(args)`

This makes it categorically different from `web_article.py` (a Python HTML renderer) or any static surface. The renderer here is **Google Apps Script JavaScript** — not Python wrapping HTML strings.

---

## Proposed file structure

```
apps-script-surface/
├── atom.gs            ← server-side: atom renderer + data functions
├── AtomPage.html      ← HTML template (client-side shell + CSS)
├── AtomStyles.html    ← CSS partial (<?!= include('AtomStyles') ?>)
└── AtomScripts.html   ← JS partial (client logic, google.script.run wiring)
```

`atom.gs` is the primary deliverable — the server-side renderer that:
1. Accepts a list of atom block objects (JSON)
2. Returns an HTML string per atom
3. Provides server-side data fetch functions called by the client via `google.script.run`

---

## Atom categories and required actions

### Category A — Static content (pure HTML, no server bridge needed)

These render entirely server-side into the `HtmlOutput`. No `google.script.run` required.

| Atom | Notes |
|---|---|
| `heading`, `subheading`, `text_block`, `paragraph` | Escape and wrap in `<h1-4>/<p>` |
| `callout`, `alert_banner`, `info_card` | Themed `<div>` with icon prefix |
| `divider`, `spacer` | `<hr>` / `<div style="height:Xpx">` |
| `tag_chip`, `badge`, `status_dot` | Inline chips |
| `code_block`, `inline_code` | `<pre><code>` — no syntax highlighting (no CDN libs in strict CSP) |
| `blockquote` | `<blockquote>` |
| `image` | `<img src="">` — must use public URLs or Drive sharing links |
| `highlighted_text` | `<mark>` with optional tooltip via `data-note` |
| `key_value_row`, `definition_list` | `<dl>/<dt>/<dd>` |
| `numbered_list`, `bullet_list`, `checklist` | `<ol>/<ul>/<li>` |
| `table` | `<table>` — no dynamic sort (no external JS) |

### Category B — Link / navigation atoms (need `<base target="_top">`)

In IFRAME sandbox mode, links without `target="_top"` open inside the iframe silently.  
**Required:** every `<a>` tag must have `target="_top"`, or the page must include `<base target="_top">` in `<head>`.

| Atom | Notes |
|---|---|
| `link_button`, `cta_button`, `nav_link` | All hrefs must be absolute and have `target="_top"` |
| `lesson_nav`, `breadcrumb`, `page_tabs` | Same — enforce `target="_top"` on all anchors |
| `card`, `feature_card` | If the card itself is a link, add `target="_top"` |

### Category C — Interactive atoms (require `google.script.run` bridge)

These atoms have state that must persist or be acted on server-side (quiz scoring, form submission, data save). They need:
1. A client-side event handler (JavaScript in `AtomScripts.html`)
2. A server-side handler function in `atom.gs`
3. `google.script.run.withSuccessHandler(fn).serverFn(args)` wiring

| Atom | Server function needed in atom.gs | Notes |
|---|---|---|
| `quiz_question` | `saveQuizAnswer(atomId, selectedIdx)` | Persist answer to `PropertiesService` or Sheet |
| `fill_in_blank` | `checkFillInBlank(atomId, answers[])` | Server validates; returns `{correct: bool[]}` |
| `match_exercise` | `saveMatchResult(atomId, score)` | Log result |
| `score_summary` | `getScoreData(sessionId)` | Pull aggregated quiz answers from server |
| `achievement_badge` | `unlockAchievement(badgeId)` | Write to user PropertiesService or Sheet |
| `xp_bar` | `getXP(userId)` | Read from PropertiesService or Sheet |
| `feedback_form`, `rating_widget` | `submitFeedback(data)` | Write to Sheet or send email |
| `data_table` (dynamic) | `getTableData(sheetId, range)` | `SpreadsheetApp.openById` |
| `chart` (live data) | `getChartData(sheetId, range)` | Same |

### Category D — Workspace-native atoms (unique to Apps Script surface)

These atoms have no equivalent on any other surface. They leverage Workspace APIs directly.

| Atom (proposed) | GAS API | What it does |
|---|---|---|
| `drive_file_list` | `DriveApp.getFolderById(id).getFiles()` | Renders a live list of Drive files with links |
| `sheet_preview` | `SpreadsheetApp.openById(id).getSheetByName(n)` | Renders a read-only snapshot of a sheet range |
| `gmail_summary` | `GmailApp.search(query, 0, 5)` | Shows last N emails matching a query |
| `calendar_upcoming` | `CalendarApp.getDefaultCalendar().getUpcomingEvents(n)` | Shows next N calendar events |
| `user_greeting` | `Session.getActiveUser().getEmail()` | Personalised "Hello, curtis@…" |
| `script_run_button` | Calls any named `.gs` function | Button that triggers a server function; shows spinner + result |

These are **new atom types** that only exist on `google-apps-script-web`. They should be added to `schema.yaml` with `works_on: [google-apps-script-web]` only.

### Category E — Degraded atoms (iframe / CDN restricted)

These are tagged `degraded_on: google-apps-script-web` in the schema. The renderer must output a graceful fallback instead of a broken embed.

> **Confirmed:** GAS HtmlService IFRAME sandbox blocks dynamic CDN script loading (`document.createElement('script')`) and external image sources via CSP. Do not attempt client-side CDN loading — use `UrlFetchApp` server-side or avoid the dependency entirely.

| Atom | Reason | Fallback |
|---|---|---|
| `youtube` | Nested iframe inside IFRAME sandbox may be blocked | Link button: "Watch on YouTube →" |
| `embed_codepen`, `embed_stackblitz`, `embed_gist` | Nested iframes blocked | Link card with URL |
| `embed_tweet`, `social_feed_embed` | External widgets require 3rd-party JS | Plain text quote block |
| `embed_google_slides` | Nested Google IFRAME restricted | Link to slides + thumbnail if available |
| `figma_embed` | Same | Link card |
| `lottie_animation` | Requires CDN JS bundle | Static fallback PNG or skip |
| `parallax_card` | scroll-based JS effects won't work in IFRAME | Render as plain card |

### Category F — Server-side rendered atoms (UrlFetchApp)

These atoms require external rendering services and would fetch server-side during `renderAtoms()` to embed results inline. No browser-side network calls needed.

| Atom | Service | Status |
|---|---|---|
| `mermaid_diagram` | `mermaid.ink/svg/` | ⏸ Deferred — mermaid.ink approach did not render in testing; removed from catalogue until a working solution is found |

---

## `atom.gs` — renderer function signature

```javascript
/**
 * Renders a list of atom blocks to an HTML string.
 * Called from doGet() or an HtmlTemplate.
 *
 * @param {Object[]} blocks - Array of atom block objects
 * @param {Object}   opts   - { theme: 'light'|'dark', sidebar: boolean }
 * @returns {string} HTML fragment (no <html> wrapper — injected into template)
 */
function renderAtoms(blocks, opts) { ... }
```

`doGet(e)` wires it:
```javascript
function doGet(e) {
  var template = HtmlService.createTemplateFromFile('AtomPage');
  template.content = renderAtoms(MY_BLOCKS, { theme: 'light' });
  return template.evaluate()
    .setTitle('My App')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}
```

---

## Per-atom render function pattern in atom.gs

```javascript
var _RENDERERS = {
  heading:          _renderHeading,
  text_block:       _renderTextBlock,
  quiz_question:    _renderQuizQuestion,
  // ...
};

function _renderHeading(b) {
  var level = b.level || 2;
  return '<h' + level + ' class="asw-heading">' + _esc(b.text) + '</h' + level + '>';
}

function _esc(str) {
  return String(str)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
```

---

## CSS / theming approach

- Inline `<style>` in `AtomStyles.html` (no CDN)
- Google Sans via `fonts.googleapis.com` (allowed in Apps Script HTML)
- CSS custom properties (`--bg`, `--accent`, etc.) for theming; dark overrides on `body.asw-dark-theme`
- No Tailwind, no Bootstrap — zero external CSS bundles
- Theme-sensitive state colours use `rgba()` with opacity (e.g. `rgba(52,168,83,0.1)` for correct answer bg) so they work in both light and dark without separate overrides
- `--highlight-bg` is declared in both `:root` (light) and `body.asw-dark-theme` (dark) — never use hardcoded hex for highlight backgrounds

---

## `google.script.run` pattern for interactive atoms

```javascript
// Client side (in AtomScripts.html or inline in atom HTML):
function submitQuiz(atomId, selectedIdx) {
  google.script.run
    .withSuccessHandler(function(result) {
      showFeedback(atomId, result.correct);
    })
    .withFailureHandler(function(err) {
      console.error(err);
    })
    .saveQuizAnswer(atomId, selectedIdx);
}
```

---

## Build / deploy steps

1. Copy `atom.gs`, `AtomPage.html`, `AtomStyles.html`, `AtomScripts.html` into a GAS project (via clasp or copy-paste)
2. Define your atom blocks array in a separate `data.gs` or inline in `doGet()`
3. Deploy as Web App: **Execute as: Me**, **Who has access: Anyone in [domain]** or **Anyone**
4. Test locally first: `clasp run renderAtoms` with a test payload

---

## Python side (catalogue integration)

The existing `renderers/apps_script_web.py` **is not the runtime renderer** — it is a preview/catalogue tool that simulates what `atom.gs` would output, for use in:
- The a2ui Firestore publish pipeline
- README compatibility table generation
- Design-time preview of what atoms look like in the Apps Script surface

`atom.gs` is the **production Apps Script runtime renderer** that developers copy into their GAS projects.

---

## File status

| File | Status |
|---|---|
| `renderers/apps_script_web.py` | ✅ exists — catalogue preview renderer (delegates to web_article for shared atoms, overrides for GAS-specific ones) |
| `apps-script-surface/a2ui-gem-renderer/atom.gs` | ✅ exists — primary GAS renderer (289+ atoms) |
| `apps-script-surface/a2ui-gem-renderer/atoms_demo.gs` | ✅ exists — demo/meta atoms (`mermaid_diagram`, `live_edit`, `live_vote`, etc.) |
| `apps-script-surface/a2ui-gem-renderer/atoms_charts.gs` | ✅ exists — SVG chart atoms |
| `apps-script-surface/a2ui-gem-renderer/AtomPage.html` | ✅ exists |
| `apps-script-surface/a2ui-gem-renderer/AtomStyles.html` | ✅ exists |
| `apps-script-surface/a2ui-gem-renderer/AtomScripts.html` | ✅ exists |
| `apps-script-surface/a2ui-gem-renderer/Code.js` | ✅ exists — `doGet`/`doPost`, base64 decode, `_renderFromPayload` |
| `apps-script-surface/a2ui-gem-renderer/playbooks/` | ✅ exists — test schemas for each atom category |
| `schema.yaml` — Workspace-native atoms | ⚠ implemented in renderers but not catalogued in schema.yaml |
