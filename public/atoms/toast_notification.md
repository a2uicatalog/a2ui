# Toast Notification

A fixed-position slide-in notification toast that appears from a corner of the viewport, holds for 3.5 seconds, then slides back out — all via CSS keyframes. Renders a viewport placeholder in the article flow with the toast positioned fixed above it.

## Surfaces

web, google-apps-script-side-panel, google-apps-script-web, mcp-apps, android

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
| title | string (optional). Bold notification title. Default "Changes saved". |
| message | string (optional). Body text. Default "Your updates have been applied successfully." |
| variant | "success" | "error" | "info" | "warning"  (optional, default "success") |
| position | "bottom-right" | "bottom-left" | "top-right" | "top-left"  (optional, default "bottom-right") |

## Example payload

```json
{
  "type": "toast_notification"
}
```

Live page: https://a2uicatalog.ai/atoms/toast_notification/
Full field contract: https://a2uicatalog.ai/spec.json
