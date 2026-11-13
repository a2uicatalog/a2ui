# Progress Checkpoint

Displays an indicator showing the reader's current location within a multi-step sequence.

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
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| current_step | integer. The current active step index. |
| total_steps | integer. Total steps in the sequence. |

## Example payload

```json
{
  "type": "progress_checkpoint",
  "current_step": 2,
  "total_steps": 5
}
```

Live page: https://a2uicatalog.ai/atoms/progress_checkpoint/
Full field contract: https://a2uicatalog.ai/spec.json
