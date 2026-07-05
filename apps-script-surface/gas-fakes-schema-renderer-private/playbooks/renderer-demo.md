# Playbook: Renderer Demo — The Meta Pitch

Use this schema to demo the renderer to someone who has never seen it.
The page explains itself using atoms that are themselves proof of concept.

```json
{
  "title": "A2UI × Apps Script — Pop-up Web App Renderer",
  "theme": "dark",
  "blocks": [
    {
      "type": "cursor_glow",
      "color": "#6366f1",
      "size": 340,
      "opacity": 0.13
    },
    {
      "type": "speed_counter",
      "label": "Page loaded in",
      "accent": "#6366f1"
    },
    {
      "type": "big_reveal",
      "equation": "JSON schema",
      "result": "Live web app",
      "color": "#a5b4fc"
    },
    {
      "type": "surface_map",
      "accent": "#6366f1"
    },
    {
      "type": "renderer_stats",
      "stats": [
        { "label": "Atoms", "value": "289" },
        { "label": "Infrastructure", "value": "0 deploys" },
        { "label": "Surfaces", "value": "3" },
        { "label": "Hosting cost", "value": "$0" }
      ],
      "accent": "#6366f1"
    },
    {
      "type": "before_after_stack",
      "before_label": "Traditional stack",
      "after_label": "A2UI renderer",
      "items": [
        "Hosting provider",
        "CI/CD pipeline",
        "Build step",
        "Framework",
        "Auth layer",
        "CDN"
      ],
      "result": "Describe → Schema → URL → Done",
      "accent": "#6366f1",
      "delay_ms": 600
    },
    {
      "type": "url_anatomy",
      "accent": "#6366f1"
    },
    {
      "type": "schema_reveal",
      "accent": "#6366f1"
    },
    {
      "type": "take_away_card",
      "headline": "The URL is the app.",
      "sub": "No deploy. No hosting. No framework. Share the link — that's it.",
      "gradient": ["#4f46e5", "#7c3aed"],
      "text_color": "#fff"
    }
  ]
}
```
