# Playbook: Another Google Workspace A2UI Use Case — Discovery Announcement

Schema-to-web-app pitch page. Dark, game-style. Opens with a "NEW SURFACE UNLOCKED" animation,
achievement badge, XP bar, then the before/after and meta reveal. Fire this into the GAS generator
live during a demo for maximum meta effect.

**Demo flow:**
1. Open the GAS generator URL
2. Paste this schema → Generate
3. Share the rendered URL — audience sees the announcement page
4. Scroll to the bottom — schema_reveal shows the JSON that built the page they're looking at

**Regenerate URL:** `python3 /tmp/gen_announcement_url.py`

```json
{
  "title": "A2UI — Another Google Workspace Use Case",
  "theme": "dark",
  "blocks": [
    {
      "type": "surface_unlocked",
      "icon": "⚡",
      "surface": "Google Apps Script Web App",
      "sub": "NEW SURFACE UNLOCKED",
      "accent": "#6366f1"
    },
    { "type": "heading", "level": 1, "text": "Another Google Workspace A2UI Use Case ⚡" },
    {
      "type": "achievement_badge",
      "icon": "🎮",
      "title": "Use Case #4 Unlocked",
      "description": "GAS Web App joins Meet Stage, Google Sites HTML and Google Chat",
      "color": "#6366f1"
    },
    { "type": "xp_bar", "level_label": "A2UI Surfaces", "xp_current": 4, "xp_next": 4, "accent": "#6366f1" },
    { "type": "body", "text": "A2UI started on a Meet stage. Then blog articles. Then Google Chat. Now a web app. One schema vocabulary. Four surfaces. No hosting. No deploys. Just JSON." },
    {
      "type": "before_after_stack",
      "before_label": "Building a web app used to mean",
      "items": [
        "Cloud hosting setup",
        "Framework & build tools",
        "Deploy pipeline",
        "Domain & SSL cert",
        "Auth layer",
        "CDN configuration",
        "DevOps overhead"
      ],
      "after_label": "Now it means",
      "result": "A schema.",
      "accent": "#6366f1",
      "delay_ms": 320
    },
    {
      "type": "renderer_stats",
      "stats": [
        { "label": "Atoms", "value": "289" },
        { "label": "Surfaces", "value": "4" },
        { "label": "Hosting cost", "value": "$0" },
        { "label": "Deploys needed", "value": "0" }
      ],
      "accent": "#6366f1"
    },
    { "type": "heading", "level": 2, "text": "Schema to web app — 60 seconds" },
    {
      "type": "next_step_strip",
      "steps": [
        { "label": "1. Describe", "detail": "Tell Gemini what page you want" },
        { "label": "2. Generate", "detail": "Get a JSON atom schema back" },
        { "label": "3. Paste", "detail": "Drop it into the A2UI generator" },
        { "label": "4. Done", "detail": "Live page — share the URL" }
      ],
      "accent": "#6366f1"
    },
    {
      "type": "prompt_to_schema",
      "prompt": "Create a discovery announcement page for A2UI's new web app surface. Dark theme. Show a before/after of how complex web apps used to be vs now. End with the meta reveal that this page is itself an A2UI schema.",
      "schema": "{\"title\":\"A2UI Use Case #4\",\"theme\":\"dark\",\"blocks\":[{\"type\":\"surface_unlocked\",\"icon\":\"⚡\",\"surface\":\"Google Apps Script Web App\",\"sub\":\"NEW SURFACE UNLOCKED\"},{\"type\":\"before_after_stack\",\"items\":[\"Hosting\",\"Framework\",\"Deploy\",\"DevOps\"],\"result\":\"A schema.\"},{\"type\":\"schema_reveal\",\"title\":\"And this page? Also an A2UI schema.\"}]}",
      "output": "This page.",
      "accent": "#6366f1",
      "labels": ["You described", "Gemini returned", "A2UI rendered"]
    },
    { "type": "url_anatomy", "accent": "#6366f1" },
    {
      "type": "surface_map",
      "title": "One schema. Four surfaces.",
      "surfaces": [
        { "name": "GAS Web App",        "icon": "⚡", "desc": "Live page · Shareable URL · Zero deploy",  "color": "#6366f1" },
        { "name": "Meet Stage",         "icon": "📺", "desc": "Full-screen · Live demos · Audience view",  "color": "#8b5cf6" },
        { "name": "Google Sites HTML",  "icon": "📄", "desc": "Blog · Docs · SEO · Static publish",        "color": "#3b82f6" },
        { "name": "Google Chat",        "icon": "💬", "desc": "Cards · Bots · Workspace native",           "color": "#06b6d4" }
      ]
    },
    {
      "type": "take_away_card",
      "headline": "If you can describe it, it ships.",
      "sub": "Describe a page to Gemini. Get a schema. The renderer turns it into a live web app. No deploy. No hosting. No code. Just a URL.",
      "gradient": ["#6366f1", "#4f46e5"],
      "text_color": "#fff"
    },
    {
      "type": "cta_button",
      "label": "Open the A2UI Generator →",
      "url": "https://script.google.com/macros/s/AKfycbxDpNWMnEKmO0M94EiUB8QU3p4gs-cAv3AXhIWO0VtMaTF3BkuOo8FbK69mknE1PAHtSg/exec"
    },
    { "type": "schema_reveal", "title": "And this page? Also an A2UI schema.", "accent": "#6366f1" }
  ]
}
```
