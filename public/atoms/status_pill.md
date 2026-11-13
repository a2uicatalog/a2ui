# Status Pill

A small, colored label or "pill" used to display a concise status for an item.

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
| label | string The text label for the status. |
| color | string The semantic color of the pill (e.g., "success", "warning", "error", "info", "neutral"). |
| icon | string Optional icon to display within the pill. |

## Example payload

```json
{
  "type": "status_pill",
  "label": "Status Pill",
  "color": "#6366f1"
}
```

Live page: https://a2uicatalog.ai/atoms/status_pill/
Full field contract: https://a2uicatalog.ai/spec.json
