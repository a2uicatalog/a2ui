# Copy Code Button

Renders a discrete interactive button that copies associated text or code to the clipboard.

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
| text_to_copy | string. The raw string content sent to clipboard when clicked. |

## Example payload

```json
{
  "type": "copy_code_button",
  "text_to_copy": "Text to copy"
}
```

Live page: https://a2uicatalog.ai/atoms/copy_code_button/
Full field contract: https://a2uicatalog.ai/spec.json
