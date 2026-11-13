# Abbr Tooltip

Inline abbreviation with a tooltip revealing the full expanded form on hover.

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
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| text | string. The abbreviation to display. |
| title | string. The expanded full form. |

## Example payload

```json
{
  "type": "abbr_tooltip",
  "text": "A concise description of the content.",
  "title": "Abbr Tooltip"
}
```

Live page: https://a2uicatalog.ai/atoms/abbr_tooltip/
Full field contract: https://a2uicatalog.ai/spec.json
