# Confetti Trigger

Button that triggers confetti explosion when clicked

## Surfaces

google-apps-script-web, mcp-apps, android

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
| label | string (message shown after click, alias: text) |
| trigger | string (button label, alias: button) |

## Example payload

```json
{
  "type": "confetti_trigger",
  "label": "Confetti Trigger",
  "trigger": "click"
}
```

Live page: https://a2uicatalog.ai/atoms/confetti_trigger/
Full field contract: https://a2uicatalog.ai/spec.json
