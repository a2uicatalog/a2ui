# Caution Block

Renders a high-visibility callout box warning readers about potential pitfalls or destructive actions.

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
| message | string. The warning content. |

## Example payload

```json
{
  "type": "caution_block",
  "message": "Your action was completed successfully."
}
```

Live page: https://a2uicatalog.ai/atoms/caution_block/
Full field contract: https://a2uicatalog.ai/spec.json
