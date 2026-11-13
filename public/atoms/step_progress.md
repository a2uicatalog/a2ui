# Step Progress

Horizontal step progress indicator with numbered circles and connecting lines. Completed steps show a tick. Use at the top of wizard or onboarding flows.

## Surfaces

web, google-apps-script-web, pdf, mcp-apps, android, slides, pptx

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
| current | integer (required, 1-based index of active step) |
| accent | string (optional, hex, default "#4f46e5") |
| steps | array (required). Array of {label or title} |

## Example payload

```json
{
  "type": "step_progress",
  "current": 2,
  "steps": [
    {
      "title": "Step one",
      "body": "First thing to do."
    },
    {
      "title": "Step two",
      "body": "Then this."
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/step_progress/
Full field contract: https://a2uicatalog.ai/spec.json
