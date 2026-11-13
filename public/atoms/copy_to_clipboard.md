# Copy To Clipboard

Inline code or text element with a one-click copy button that provides feedback on success.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

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
| text | string. Display label. |
| value | string. Value copied to clipboard. |

## Example payload

```json
{
  "type": "copy_to_clipboard",
  "text": "A concise description of the content.",
  "value": "1,234"
}
```

Live page: https://a2uicatalog.ai/atoms/copy_to_clipboard/
Full field contract: https://a2uicatalog.ai/spec.json
