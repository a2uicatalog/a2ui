# Completion Gate

Renders a locked placeholder card until the specified module id is marked complete in progress_store. Once complete, the gate disappears to reveal content below it. Use to sequence content and prevent skipping.

## Surfaces

google-apps-script-web, web, google-meet-stage, mcp-apps, android

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
| requires | string (required). Module id that must be complete in progress_store to unlock. |
| label | string (optional). Lock card heading. Default "Locked". |
| message | string (optional). Message shown on the lock card. |

## Example payload

```json
{
  "type": "completion_gate",
  "requires": "complete_intro"
}
```

Live page: https://a2uicatalog.ai/atoms/completion_gate/
Full field contract: https://a2uicatalog.ai/spec.json
