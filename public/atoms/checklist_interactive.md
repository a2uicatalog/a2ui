# Checklist Interactive

Renders a list of items with actionable checkboxes for readers to track task progress.

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
| items | array. Individual checkpoint task strings. |

## Example payload

```json
{
  "type": "checklist_interactive",
  "items": 1
}
```

Live page: https://a2uicatalog.ai/atoms/checklist_interactive/
Full field contract: https://a2uicatalog.ai/spec.json
