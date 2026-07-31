# Confetti Burst

JS confetti celebration effect. trigger load fires immediately, trigger button shows a clickable button.

## Surfaces

web, google-meet-stage, google-apps-script-web, google-apps-script-side-panel, mcp-apps

## Fields

| Field | Type |
|---|---|
| trigger | button (default) or load |
| label | button label (default Celebrate!) |
| count | number of confetti pieces (default 80) |
| colors | array of hex colours |
| duration | total animation duration in ms (default 2000) |
| accent | button colour |

## Example payload

```json
{
  "type": "confetti_burst",
  "colors": [
    "#3b82f6",
    "#10b981",
    "#f59e0b",
    "#ef4444"
  ],
  "accent": "#6366f1"
}
```

Live page: https://a2uicatalog.ai/atoms/confetti_burst/
Full field contract: https://a2uicatalog.ai/spec.json
