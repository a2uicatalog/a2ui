# Notification Badge

Small badge overlaid on an icon or element to indicate unread count or alert state.

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
| text | string. Badge label or count. |
| color | string (optional). Background colour (hex). |

## Example payload

```json
{
  "type": "notification_badge",
  "text": "New"
}
```

Live page: https://a2uicatalog.ai/atoms/notification_badge/
Full field contract: https://a2uicatalog.ai/spec.json
