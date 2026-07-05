# Gemini Prompt — A2UI Workspace Pitch

Paste the block below into Gemini. Replace every `<<FILL: ...>>` with your content.
Return ONLY completed JSON. No markdown fences, no explanation, no extra keys.
Do not change any structure, URLs, colours, sizes, or atom types.

---

```
Complete the JSON below by replacing every <<FILL: instruction>> with your text.
Return ONLY valid JSON. No markdown fences. No explanation. No added or removed keys.
Do not change structure, atom types, logo URLs, colours, or sizes.

{
  "title": "A2UI — Useful for Humans. Declarative for AI Agents.",
  "theme": "dark",
  "blocks": [
    {
      "type": "shimmer_text",
      "text": "A2UI",
      "size": "4.5rem",
      "from": "#6366f1",
      "via": "#ffffff",
      "to": "#10b981",
      "align": "center"
    },
    {
      "type": "shimmer_text",
      "text": "Useful for Humans.  Declarative for AI Agents.",
      "size": "1.35rem",
      "from": "#9ca3af",
      "via": "#e5e7eb",
      "to": "#9ca3af",
      "align": "center"
    },
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
    },
    { "type": "wave_divider", "color": "#6366f1", "height": 44, "opacity": "0.15" },
    {
      "type": "reveal",
      "animation": "stagger",
      "stagger_delay": 130,
      "blocks": [{
        "type": "columns",
        "cols": 3,
        "items": [
          { "blocks": [{ "type": "animated_border", "from": "#6366f1", "to": "#8b5cf6", "via": "#0ea5e9", "speed": "4",
              "content": "**① Prompt**\n\n<<FILL: 1-2 sentences. What the human or agent does. Starts with describing what they want in plain language.>>" }] },
          { "blocks": [{ "type": "animated_border", "from": "#10b981", "to": "#6366f1", "via": "#34d399", "speed": "4",
              "content": "**② Schema**\n\n<<FILL: 1-2 sentences. What the AI returns. Typed atoms, valid JSON, verifiable before render.>>" }] },
          { "blocks": [{ "type": "animated_border", "from": "#f59e0b", "to": "#10b981", "via": "#fbbf24", "speed": "4",
              "content": "**③ App**\n\n<<FILL: 1-2 sentences. The result. Shareable URL, live in Meet/Chat/Apps Script, no pipeline.>>" }] }
        ]
      }]
    },
    { "type": "wave_divider", "color": "#10b981", "height": 44, "opacity": "0.12", "flip": true },
    {
      "type": "reveal",
      "animation": "stagger",
      "stagger_delay": 90,
      "blocks": [{
        "type": "metric_row",
        "metrics": [
          { "value": "<<FILL: e.g. <60s>>",  "label": "<<FILL: prompt to live URL or similar>>", "trend": "up" },
          { "value": "<<FILL: e.g. 0>>",      "label": "<<FILL: lines of HTML or similar>>",      "trend": "down" },
          { "value": "<<FILL: e.g. 85%>>",    "label": "<<FILL: token efficiency vs raw HTML>>",  "trend": "up" },
          { "value": "<<FILL: e.g. ∞>>",      "label": "<<FILL: topics or surfaces>>",            "trend": "up" }
        ]
      }]
    },
    { "type": "wave_divider", "color": "#8b5cf6", "height": 36, "opacity": "0.10" },
    {
      "type": "reveal",
      "animation": "fade",
      "blocks": [{
        "type": "highlight_box",
        "accent": "#6366f1",
        "title": "Why now?",
        "body": "<<FILL: 2-3 sharp sentences. Why declarative UI matters for AI agents right now. Mention: HTML is noisy/unsafe for agents, typed schemas are verifiable, this works inside tools people already use. No corporate language.>>"
      }]
    },
    {
      "type": "marquee",
      "speed": 16,
      "direction": "right",
      "gap": 44,
      "items": [
        { "icon": "🤖", "text": "<<FILL: feature tag, 3-5 words>>" },
        { "icon": "✅", "text": "<<FILL: feature tag, 3-5 words>>" },
        { "icon": "🔗", "text": "<<FILL: feature tag, 3-5 words>>" },
        { "icon": "🎨", "text": "<<FILL: feature tag, 3-5 words>>" },
        { "icon": "📊", "text": "<<FILL: feature tag, 3-5 words>>" },
        { "icon": "⚡", "text": "<<FILL: feature tag, 3-5 words>>" },
        { "icon": "🔒", "text": "<<FILL: feature tag, 3-5 words>>" },
        { "icon": "🌍", "text": "<<FILL: feature tag, 3-5 words>>" }
      ]
    },
    { "type": "confetti_burst", "trigger": "load", "count": 60, "duration": 3000 }
  ]
}
```
