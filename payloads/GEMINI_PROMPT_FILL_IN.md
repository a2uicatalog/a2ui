# Gemini Fill-In Prompt — Animated Pitch (any topic)

The structure is locked. Gemini only writes the content inside the marked slots.
Paste this entire block into Gemini — it will return the completed JSON.

---

```
Complete the JSON below by filling in every value marked <<FILL: instruction>>.
Return ONLY the completed JSON. No markdown fences, no explanation, no extra keys.
Do not change any keys, structure, URLs, colours, sizes, or atom types.
Only replace the <<FILL: ...>> placeholders with your text.

{
  "title": "<<FILL: short punchy title for the pitch, max 8 words>>",
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
      "blocks": [
        {
          "type": "columns",
          "cols": 3,
          "items": [
            { "blocks": [{ "type": "animated_border", "from": "#6366f1", "to": "#8b5cf6", "via": "#0ea5e9", "speed": "4",
                "content": "**① <<FILL: step 1 label, 1-3 words>>**\n\n<<FILL: step 1 description, 1-2 sentences, what the human or agent does first>>" }] },
            { "blocks": [{ "type": "animated_border", "from": "#10b981", "to": "#6366f1", "via": "#34d399", "speed": "4",
                "content": "**② <<FILL: step 2 label, 1-3 words>>**\n\n<<FILL: step 2 description, 1-2 sentences, what happens in the middle>>" }] },
            { "blocks": [{ "type": "animated_border", "from": "#f59e0b", "to": "#10b981", "via": "#fbbf24", "speed": "4",
                "content": "**③ <<FILL: step 3 label, 1-3 words>>**\n\n<<FILL: step 3 description, 1-2 sentences, the result or output>>" }] }
          ]
        }
      ]
    },
    { "type": "wave_divider", "color": "#10b981", "height": 44, "opacity": "0.12", "flip": true },
    {
      "type": "reveal",
      "animation": "stagger",
      "stagger_delay": 90,
      "blocks": [{
        "type": "metric_row",
        "metrics": [
          { "value": "<<FILL: short metric value e.g. <60s>>", "label": "<<FILL: metric label>>", "trend": "up" },
          { "value": "<<FILL: short metric value>>",           "label": "<<FILL: metric label>>", "trend": "down" },
          { "value": "<<FILL: short metric value>>",           "label": "<<FILL: metric label>>", "trend": "up" },
          { "value": "<<FILL: short metric value>>",           "label": "<<FILL: metric label>>", "trend": "up" }
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
        "title": "<<FILL: punchy section title e.g. 'Why now?' or 'The insight'>>",
        "body": "<<FILL: 2-3 sentences. The core 'why this matters' argument. Be sharp, not corporate.>>"
      }]
    },
    {
      "type": "marquee",
      "speed": 16,
      "direction": "right",
      "gap": 44,
      "items": [
        { "icon": "🤖", "text": "<<FILL: feature tag 1, 3-5 words>>" },
        { "icon": "✅", "text": "<<FILL: feature tag 2, 3-5 words>>" },
        { "icon": "🔗", "text": "<<FILL: feature tag 3, 3-5 words>>" },
        { "icon": "🎨", "text": "<<FILL: feature tag 4, 3-5 words>>" },
        { "icon": "📊", "text": "<<FILL: feature tag 5, 3-5 words>>" },
        { "icon": "⚡", "text": "<<FILL: feature tag 6, 3-5 words>>" },
        { "icon": "🔒", "text": "<<FILL: feature tag 7, 3-5 words>>" },
        { "icon": "🌍", "text": "<<FILL: feature tag 8, 3-5 words>>" }
      ]
    },
    { "type": "confetti_burst", "trigger": "load", "count": 60, "duration": 3000 }
  ]
}

Topic for this pitch: <<FILL: describe your topic here before sending>>
```
