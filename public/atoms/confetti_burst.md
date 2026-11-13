# Confetti Burst

JS confetti celebration effect. trigger load fires immediately, trigger button shows a clickable button.

## Surfaces

web, google-meet-stage, google-apps-script-web, google-apps-script-side-panel, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn | 2026-11-13 |  |
| a2ui-vue | Drawn | 2026-11-13 |  |
| Flutter | Not supported | 2026-11-13 | component type unknown to the renderer |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

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
