# Playbook: Atom Showcase — Meta Demo Kit

Demonstrates all 16 meta demo kit atoms in a single scrollable page.
Use this as a QA / reference schema.

```json
{
  "title": "Meta Demo Kit — All Atoms",
  "theme": "dark",
  "blocks": [
    {
      "type": "heading",
      "level": 2,
      "text": "speed_counter"
    },
    {
      "type": "speed_counter",
      "label": "Time on page",
      "accent": "#6366f1"
    },
    {
      "type": "heading",
      "level": 2,
      "text": "surface_map"
    },
    {
      "type": "surface_map",
      "accent": "#6366f1"
    },
    {
      "type": "heading",
      "level": 2,
      "text": "renderer_stats"
    },
    {
      "type": "renderer_stats",
      "stats": [
        { "label": "Atoms", "value": "289" },
        { "label": "Surfaces", "value": "3" },
        { "label": "Infrastructure", "value": "0" },
        { "label": "Hosting cost", "value": "$0" }
      ],
      "accent": "#6366f1"
    },
    {
      "type": "heading",
      "level": 2,
      "text": "take_away_card"
    },
    {
      "type": "take_away_card",
      "headline": "The URL is the app.",
      "sub": "No deploy. No hosting. No framework.",
      "gradient": ["#4f46e5", "#7c3aed"],
      "text_color": "#fff"
    },
    {
      "type": "heading",
      "level": 2,
      "text": "before_after_stack"
    },
    {
      "type": "before_after_stack",
      "before_label": "Traditional stack",
      "after_label": "A2UI renderer",
      "items": ["Hosting", "CI/CD", "Build step", "Framework", "Auth"],
      "result": "Schema + URL",
      "accent": "#6366f1",
      "delay_ms": 500
    },
    {
      "type": "heading",
      "level": 2,
      "text": "next_step_strip"
    },
    {
      "type": "next_step_strip",
      "steps": [
        { "label": "Describe", "detail": "Tell Gemini what you want" },
        { "label": "Schema", "detail": "Get JSON back" },
        { "label": "Encode", "detail": "Base64 it" },
        { "label": "Share", "detail": "That's the app" }
      ],
      "accent": "#6366f1"
    },
    {
      "type": "heading",
      "level": 2,
      "text": "copy_prompt"
    },
    {
      "type": "copy_prompt",
      "label": "Sample Gemini prompt",
      "text": "Generate an A2UI schema for a team standup briefing page with a status_timeline showing 3 items and a countdown_timer to 09:00 tomorrow."
    },
    {
      "type": "heading",
      "level": 2,
      "text": "url_anatomy"
    },
    {
      "type": "url_anatomy",
      "accent": "#6366f1"
    },
    {
      "type": "heading",
      "level": 2,
      "text": "schema_reveal"
    },
    {
      "type": "schema_reveal",
      "accent": "#6366f1"
    },
    {
      "type": "heading",
      "level": 2,
      "text": "schema_qr"
    },
    {
      "type": "schema_qr",
      "label": "Scan to open this page",
      "use_current_url": true,
      "accent": "#6366f1"
    },
    {
      "type": "heading",
      "level": 2,
      "text": "prompt_to_schema"
    },
    {
      "type": "prompt_to_schema",
      "prompt": "Make a launch countdown page with a big number and a CTA button.",
      "schema": "{\"title\":\"Launch\",\"blocks\":[{\"type\":\"countdown_timer\",\"label\":\"Launching in\",\"target\":\"2026-07-01T00:00:00\"},{\"type\":\"cta_button\",\"label\":\"Join waitlist\",\"url\":\"#\"}]}",
      "accent": "#6366f1"
    },
    {
      "type": "heading",
      "level": 2,
      "text": "raise_hand"
    },
    {
      "type": "raise_hand",
      "label": "Raise your hand ✋",
      "sheet_url": "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/gviz/tq?tqx=out:csv",
      "write_url": "https://script.google.com/macros/s/YOUR_WRITE_ENDPOINT/exec",
      "accent": "#6366f1"
    },
    {
      "type": "heading",
      "level": 2,
      "text": "reaction_shower"
    },
    {
      "type": "reaction_shower",
      "reactions": ["🔥", "💡", "👏", "🤯"],
      "sheet_url": "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/gviz/tq?tqx=out:csv",
      "write_url": "https://script.google.com/macros/s/YOUR_WRITE_ENDPOINT/exec",
      "accent": "#6366f1"
    }
  ]
}
```
