# Roadmap Card

Quarter-based product roadmap showing milestones across Q1–Q4 or custom periods. Each period contains a list of items with a status indicator (done, in-progress, planned). Useful for product announcements and release planning slides.

## Surfaces

web, google-meet-stage, google-chat, email, pdf, google-apps-script-web, mcp-apps, android, slides, pptx

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn | 2026-11-13 |  |
| a2ui-vue | Drawn | 2026-11-13 |  |
| Flutter | Native | 2026-11-13 |  |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| title | string (optional). Heading above the roadmap. |
| periods | {'type': 'array', 'description': 'List of {label, items} where each item is {text, status}. status is one of done | in-progress | planned.'} |

## Example payload

```json
{
  "type": "roadmap_card",
  "periods": [
    "Week 1",
    "Week 2",
    "Week 3",
    "Week 4"
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/roadmap_card/
Full field contract: https://a2uicatalog.ai/spec.json
