"""Generate a beautiful pitch page for A2UI on Apps Script Web App surface.

Usage:
    python3 examples/pitch_apps_script_web.py
    # outputs: examples/pitch_apps_script_web.html
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from renderers.apps_script_web import render

BLOCKS = [
    # ── Hero ──────────────────────────────────────────────────────────────────
    {"type": "user_greeting", "prefix": "Hey"},

    {"type": "heading", "level": 1, "text": "A2UI — now on Apps Script Web App"},

    {"type": "body", "text": "**100+ composable atoms. One JSON schema. Zero HTML.** A2UI lets you build rich, interactive Workspace pages by describing what you want — not how to render it."},

    {"type": "alert_banner", "variant": "success", "icon": "🎉",
     "text": "**Apps Script Web App is now a first-class A2UI surface.** Workspace-native atoms call Google APIs at runtime — no backend, no auth tokens, no extra infra."},

    {"type": "divider"},

    # ── What is A2UI ──────────────────────────────────────────────────────────
    {"type": "heading", "level": 2, "text": "What is A2UI?"},

    {"type": "body", "text": "A2UI is an atom catalogue for AI-generated UIs. An AI agent emits a JSON block list; A2UI renders it to a beautiful, surface-aware page. You get consistent design, safe rendering, and Workspace integration — without maintaining any frontend code."},

    {"type": "table",
     "headers": ["Surface", "Renderer", "Atoms available", "Status"],
     "rows": [
         ["**Apps Script Web App**", "`apps_script_web.py`", "150+", "✅ New"],
         ["Web / Blog",             "`web_article.py`",     "150+", "✅ Live"],
         ["Google Chat",            "`googlechat.py`",      "40+",  "✅ Live"],
         ["GAS Sidebar",            "`apps_script_web.py`", "150+", "✅ Live"],
     ]},

    {"type": "divider"},

    # ── Why Apps Script Web App ───────────────────────────────────────────────
    {"type": "heading", "level": 2, "text": "Why Apps Script Web App?"},

    {"type": "bullet_list", "items": [
        {"label": "Zero infrastructure", "text": "Deploy from the Apps Script editor in 30 seconds — no Cloud Run, no Docker, no domain setup."},
        {"label": "Workspace identity", "text": "`Session.getActiveUser()` gives you the signed-in user for free. No OAuth dance."},
        {"label": "Live Google data",   "text": "DriveApp, SpreadsheetApp, GmailApp, CalendarApp — all callable server-side, results rendered as atoms."},
        {"label": "Script actions",     "text": "`script_run_button` calls your `.gs` function directly via `google.script.run`. No HTTP endpoints."},
        {"label": "iframe-safe",        "text": "All links force `target=\"_top\"` so clicks break out of the sandbox. `<base target=\"_top\">` in the document head."},
    ]},

    {"type": "divider"},

    # ── Workspace-native atoms ────────────────────────────────────────────────
    {"type": "heading", "level": 2, "text": "Live Workspace Data — Rendered as Atoms"},

    {"type": "body", "text": "These atoms call real Google APIs at runtime. In preview mode they show representative mock data so you can build without deploying."},

    {"type": "user_greeting", "prefix": "Signed in as"},

    {"type": "sheet_preview",
     "spreadsheet_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms",
     "sheet_name": "Q2 Pipeline",
     "range": "A1:E5"},

    {"type": "drive_file_list",
     "folder_id": "0B3X9GlR6EmbnWksyTEtCM0Fmc1U",
     "max_results": 5},

    {"type": "gmail_summary",
     "query": "label:a2ui OR label:apps-script is:unread",
     "max_results": 3},

    {"type": "calendar_upcoming", "max_results": 3},

    {"type": "divider"},

    # ── Script run buttons ────────────────────────────────────────────────────
    {"type": "heading", "level": 2, "text": "Server-Side Actions"},

    {"type": "body", "text": "The `script_run_button` atom calls your Apps Script function directly — wired through `google.script.run` with built-in loading state and success/error feedback."},

    {"type": "callout", "icon": "⚡",
     "text": "Add `function refreshDashboard() { ... }` to your `.gs` file and the button below calls it. No HTTP endpoint. No auth token. Just Apps Script."},

    {"type": "script_run_button", "label": "Refresh Dashboard",   "function_name": "refreshDashboard"},
    {"type": "script_run_button", "label": "Export to Sheets",    "function_name": "exportToSheets"},
    {"type": "script_run_button", "label": "Send Summary Email",  "function_name": "sendSummaryEmail"},

    {"type": "divider"},

    # ── Interactive atoms ─────────────────────────────────────────────────────
    {"type": "heading", "level": 2, "text": "Interactive & Training Atoms"},

    {"type": "body", "text": "A2UI ships with a full suite of training atoms — quizzes, fill-in-the-blank, matching exercises, and gamification. All client-side, all CSP-safe."},

    {"type": "quiz_question",
     "question": "Which Apps Script service retrieves live spreadsheet data?",
     "options": ["UrlFetchApp", "SpreadsheetApp", "GmailApp", "PropertiesService"],
     "correct": 1,
     "explanation": "SpreadsheetApp.openById(id).getSheetByName(name).getRange(range).getValues() returns a 2D array of live cell data."},

    {"type": "fill_in_blank",
     "template": "Use {blank} to serve an HTML page, and call server functions with {blank}.",
     "answers": [["HtmlService", "HtmlService.createHtmlOutput"], ["google.script.run"]],
     "hint": "Both are core Apps Script APIs, not imported libraries."},

    {"type": "match_exercise",
     "pairs": [
         {"term": "DriveApp",        "definition": "List files in a Google Drive folder"},
         {"term": "SpreadsheetApp",  "definition": "Read and write Google Sheets data"},
         {"term": "GmailApp",        "definition": "Search and read Gmail threads"},
         {"term": "CalendarApp",     "definition": "Fetch upcoming calendar events"},
         {"term": "Session",         "definition": "Get the active user's email address"},
     ],
     "shuffle": True},

    {"type": "hint_reveal",
     "label": "Struggling with the match?",
     "hint": "Each Apps Script service is named after the Google product it wraps. DriveApp → Drive, SpreadsheetApp → Sheets, and so on."},

    {"type": "divider"},

    # ── Gamification ──────────────────────────────────────────────────────────
    {"type": "heading", "level": 2, "text": "Gamification Atoms"},

    {"type": "xp_bar",
     "level_label": "Workspace Developer — Level 3",
     "xp_current": 750,
     "xp_next": 1000,
     "accent": "#1a73e8"},

    {"type": "achievement_badge",
     "title": "Apps Script Pioneer",
     "description": "First to deploy A2UI on a Web App surface",
     "icon": "🚀",
     "color": "#1a73e8",
     "unlocked_at": "Jun 16, 2026"},

    {"type": "achievement_badge",
     "title": "Data Connector",
     "description": "Rendered a live Sheet preview via SpreadsheetApp",
     "icon": "📊",
     "color": "#34a853",
     "unlocked_at": "Jun 16, 2026"},

    {"type": "achievement_badge",
     "title": "Inbox Zero",
     "description": "Cleared all unread mail via the Gmail atom",
     "icon": "✉️",
     "color": "#fbbc04",
     "locked": True},

    {"type": "score_summary",
     "correct": 4,
     "total": 5,
     "time_taken": "2m 14s",
     "pass_threshold": 70,
     "retry_label": "Try again",
     "continue_label": "Next: Deploy your Web App →",
     "continue_url": "#deploy"},

    {"type": "divider"},

    # ── Architecture callout ──────────────────────────────────────────────────
    {"type": "heading", "level": 2, "text": "How It Works"},

    {"type": "code_block", "language": "python", "content":
"""# 1. An AI agent emits atom blocks
blocks = [
    {"type": "user_greeting", "prefix": "Hello"},
    {"type": "sheet_preview", "spreadsheet_id": "...", "range": "A1:D10"},
    {"type": "quiz_question",  "question": "...", "options": [...], "correct": 0},
]

# 2. Preview locally with the Python renderer
from renderers.apps_script_web import render
html = render(blocks, title="My Dashboard")

# 3. Serve from Apps Script
# In Code.gs:
#   function doGet() {
#     return HtmlService.createHtmlOutput(renderAtoms(blocks));
#   }"""},

    {"type": "callout", "icon": "🔄",
     "text": "The Python renderer and the `atom.gs` runtime share the same CSS classes, atom field names, and rendering logic — so what you preview locally is what users see in production."},

    {"type": "divider"},

    # ── Get started ───────────────────────────────────────────────────────────
    {"type": "heading", "level": 2, "text": "Get Started in 3 Steps"},

    {"type": "bullet_list", "items": [
        {"label": "1. Copy the surface files",
         "text": "Add `atom.gs`, `AtomPage.html`, `AtomStyles.html`, and `AtomScripts.html` from `apps-script-surface/` into your Apps Script project."},
        {"label": "2. Call renderAtoms()",
         "text": "Pass your block list to `renderAtoms(blocks)` and serve the result with `HtmlService.createHtmlOutput(html)`."},
        {"label": "3. Add workspace atoms",
         "text": "Drop in `drive_file_list`, `sheet_preview`, `gmail_summary`, or `calendar_upcoming` atoms — they call the relevant Google API automatically."},
    ]},

    {"type": "cta_button",
     "label": "View the full A2UI Catalogue →",
     "url": "https://techmusings.krygier.fr"},

    {"type": "divider"},

    # ── Footer nav ────────────────────────────────────────────────────────────
    {"type": "course_progress_card",
     "course_title": "A2UI Developer Series",
     "accent": "#1a73e8",
     "modules": [
         {"title": "Core atoms & schema",           "lessons_total": 5, "lessons_done": 5},
         {"title": "Web & Chat surfaces",           "lessons_total": 4, "lessons_done": 4},
         {"title": "Apps Script Web App surface",   "lessons_total": 3, "lessons_done": 2},
         {"title": "AI agent integration",          "lessons_total": 4, "lessons_done": 0},
     ]},

    {"type": "lesson_nav",
     "module_label": "A2UI Developer Series",
     "current_title": "Apps Script Web App Surface",
     "prev_title": "Google Chat Surface",
     "prev_url": "#chat",
     "next_title": "AI Agent Integration",
     "next_url": "#agents",
     "show_completion": True},
]


if __name__ == "__main__":
    out_path = Path(__file__).with_suffix(".html")
    html = render(
        BLOCKS,
        title="A2UI — Apps Script Web App Surface",
        theme="light",
    )
    out_path.write_text(html)
    print(f"✓ Written {len(html):,} chars → {out_path}")
