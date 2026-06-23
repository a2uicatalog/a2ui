# Gemini Prompt — A2UI Workspace Pitch (Animated)

Paste the block below into Gemini. It will return a complete JSON payload — paste it directly into the A2UI renderer.

---

```
You are generating a JSON payload for A2UI — a Google Apps Script renderer that displays animated, full-screen content as a flowing dark-theme page.

Return ONLY valid JSON. No markdown fences, no explanation, no comments.

## Brief

Pitch A2UI as a native Google Workspace Apps Script capability.
Tagline: "Useful for Humans. Declarative for Agents."
Angle: Developers and agents can describe a rich UI in plain JSON, and it renders instantly inside Meet, Chat, or any Apps Script surface. No HTML, no frameworks, no deployment pipeline — just a schema and a URL.

## Top-level structure

{
  "title": "A2UI — Built for Google Workspace",
  "theme": "dark",
  "blocks": [ ...Block ]
}

## Atom vocabulary — use these in this order

### 1. Open with shimmer headline
{
  "type": "shimmer_text",
  "text": "A2UI",
  "size": "4.5rem",
  "from": "#6366f1", "via": "#ffffff", "to": "#10b981",
  "align": "center"
}

### 2. Shimmer tagline
{
  "type": "shimmer_text",
  "text": "Useful for Humans.  Declarative for AI Agents.",
  "size": "1.35rem",
  "from": "#9ca3af", "via": "#e5e7eb", "to": "#9ca3af",
  "align": "center"
}

### 3. Workspace logo marquee — USE THESE EXACT URLs
{
  "type": "marquee",
  "title": "Native to Google Workspace",
  "speed": 20,
  "gap": 56,
  "pause_on_hover": true,
  "color_icons": true,
  "items": [
    { "image_url": "https://workspacelogos.com/logos/google-workspace-logos/Meet/logo_meet_2026q2_color_2x_web_96dp.png", "label": "Google Meet" },
    { "image_url": "https://workspacelogos.com/logos/google-workspace-logos/Chat/logo_chat_2026q2_color_2x_web_96dp.png", "label": "Google Chat" },
    { "image_url": "https://workspacelogos.com/logos/google-workspace-logos/Apps%20Script/logo_apps_script_192px.png", "label": "Apps Script" }
  ]
}

### 4. Wave divider
{ "type": "wave_divider", "color": "#6366f1", "height": 44, "opacity": "0.15" }

### 5. Staggered reveal of 3 animated-border feature cards (in a 3-col columns block)
{
  "type": "reveal",
  "animation": "stagger",
  "stagger_delay": 130,
  "blocks": [{
    "type": "columns",
    "cols": 3,
    "items": [
      { "blocks": [{ "type": "animated_border", "from": "#6366f1", "to": "#8b5cf6", "via": "#0ea5e9", "speed": "4",
          "content": "**① Prompt**\n\nDescribe the UI you need in plain language. Any LLM that reads JSON can generate a valid schema." }] },
      { "blocks": [{ "type": "animated_border", "from": "#10b981", "to": "#6366f1", "via": "#34d399", "speed": "4",
          "content": "**② Schema**\n\nTyped atoms. Validated structure. The agent proposes — the schema guarantees what can render." }] },
      { "blocks": [{ "type": "animated_border", "from": "#f59e0b", "to": "#10b981", "via": "#fbbf24", "speed": "4",
          "content": "**③ App**\n\nPaste. Click Open. Shareable URL — live inside Meet, Chat, or any Apps Script surface." }] }
    ]
  }]
}

### 6. Flipped wave divider
{ "type": "wave_divider", "color": "#10b981", "height": 44, "opacity": "0.12", "flip": true }

### 7. Staggered reveal of a metric row — write strong numbers
{
  "type": "reveal",
  "animation": "stagger",
  "stagger_delay": 90,
  "blocks": [{
    "type": "metric_row",
    "metrics": [
      { "value": "< 60s", "label": "Prompt to live URL", "trend": "up" },
      { "value": "0",     "label": "Lines of HTML",      "trend": "down" },
      { "value": "3+",    "label": "Workspace surfaces",  "trend": "up" },
      { "value": "∞",     "label": "Topics",              "trend": "up" }
    ]
  }]
}

### 8. Second wave divider
{ "type": "wave_divider", "color": "#8b5cf6", "height": 36, "opacity": "0.10" }

### 9. Staggered reveal of highlight_box — write a punchy "why now" statement
{
  "type": "reveal",
  "animation": "fade",
  "blocks": [{
    "type": "highlight_box",
    "accent": "#6366f1",
    "title": "Why now?",
    "body": "..."
  }]
}

### 10. Reverse marquee — feature strip with emoji tags
{
  "type": "marquee",
  "speed": 16,
  "direction": "right",
  "gap": 44,
  "items": [
    { "icon": "🤖", "text": "Agent-native schema" },
    { "icon": "✅", "text": "Validated before render" },
    { "icon": "🔗", "text": "Shareable URL" },
    { "icon": "🎨", "text": "Dark & light themes" },
    { "icon": "📊", "text": "Hub navigation" },
    { "icon": "⚡", "text": "Zero dependencies" },
    { "icon": "🔒", "text": "Stays in Workspace" },
    { "icon": "🌍", "text": "Any language, any topic" }
  ]
}

### 11. Close with confetti
{ "type": "confetti_burst", "trigger": "load", "count": 60, "duration": 3000 }

## Rules

- Follow the atom order above exactly — do not reorder or skip atoms
- Only write the content inside the atoms marked with "..." — do not change structure, URLs, colours, or sizes
- Write the "Why now?" highlight_box body as 1–2 punchy sentences about AI agents + Workspace + no-code UI
- Keep all other copy as specified above
- Return the complete JSON with all 11 atoms — do not abbreviate or omit any block
```
