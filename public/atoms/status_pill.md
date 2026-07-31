# Status Pill

A small, colored label or "pill" used to display a concise status for

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

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
