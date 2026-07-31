# Roadmap Card

Quarter-based product roadmap showing milestones across Q1–Q4 or custom periods. Each period contains a list of items with a status indicator (done, in-progress, planned). Useful for product announcements and release planning slides.

## Surfaces

web, google-meet-stage, google-chat, email, pdf, google-apps-script-web, mcp-apps

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
