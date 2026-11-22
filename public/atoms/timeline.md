# Timeline

Vertical timeline with dot connectors, date badges, tag pills

## Surfaces

web, google-meet-stage, pdf, google-apps-script-web, mcp-apps, android, slides, pptx

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn | 2026-11-13 |  |
| a2ui-vue | Drawn | 2026-11-13 |  |
| Flutter | Native | 2026-11-13 |  |
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| title | string (optional) |
| accent | string (optional) |
| events | [{'date': 'string', 'label': 'string', 'text': 'string', 'tag': 'string (optional)'}] |

## Example payload

```json
{
  "type": "timeline",
  "events": [
    {
      "date": "2024",
      "title": "A2UI v1",
      "body": "First atoms defined."
    },
    {
      "date": "2025",
      "title": "576 atoms",
      "body": "Full schema published."
    },
    {
      "date": "2026",
      "title": "ARD catalog",
      "body": "Live on a2uicatalog.ai."
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/timeline/
Full field contract: https://a2uicatalog.ai/spec.json
