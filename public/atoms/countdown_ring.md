# Countdown Ring

Circular SVG countdown that depletes as seconds tick down.

## Surfaces

web, google-meet-stage, google-apps-script-web, google-apps-script-side-panel, mcp-apps

## Fields

| Field | Type |
|---|---|
| duration_sec | total countdown in seconds (required, default 60) |
| size | ring diameter in px (default 80) |
| color | ring colour (default var(--a2ui-accent)) |
| label | caption below |

## Example payload

```json
{
  "type": "countdown_ring",
  "label": "Countdown Ring"
}
```

Live page: https://a2uicatalog.ai/atoms/countdown_ring/
Full field contract: https://a2uicatalog.ai/spec.json
