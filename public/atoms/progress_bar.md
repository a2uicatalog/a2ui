# Progress Bar

Progress bar with an animated width transition, an optional percentage and an optional caption

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, claude-code, android

## Fields

| Field | Type |
|---|---|
| value | integer (0-100) |
| label | string |
| accent | string (optional) |
| show_percent | bool (optional) |
| caption | string (optional) |

## Example payload

```json
{
  "type": "progress_bar",
  "value": 75,
  "label": "Progress Bar"
}
```

Live page: https://a2uicatalog.ai/atoms/progress_bar/
Full field contract: https://a2uicatalog.ai/spec.json
