# Table Of Contents

Renders an active list directory of navigation links targeting main content sections.

## Surfaces

web, google-apps-script-web, mcp-apps, android

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
| headings | array. Structured items detailing section names and anchor tags. |

## Example payload

```json
{
  "type": "table_of_contents",
  "headings": [
    {
      "level": 2,
      "text": "Introduction"
    },
    {
      "level": 2,
      "text": "Methods"
    },
    {
      "level": 2,
      "text": "Results"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/table_of_contents/
Full field contract: https://a2uicatalog.ai/spec.json
