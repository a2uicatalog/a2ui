# Countdown Timer

Flip-clock style countdown display showing hours, minutes, and seconds in individual digit tiles. Renders a static snapshot of the target time — pair with a dataModelUpdate SSE stream to tick the values.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| hours | integer (optional). Hours component. Default 0. |
| minutes | integer (optional). Minutes component. Default 4. |
| seconds | integer (optional). Seconds component. Default 59. |
| label | string (optional). Caption below the timer. |
| variant | "dark" | "light"  (optional, default "dark"). |
| accent | string (optional). Separator and accent colour. Default "#00f2ff". |

## Example payload

```json
{
  "type": "countdown_timer"
}
```

Live page: https://a2uicatalog.ai/atoms/countdown_timer/
Full field contract: https://a2uicatalog.ai/spec.json
