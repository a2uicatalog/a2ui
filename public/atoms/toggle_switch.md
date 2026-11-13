# Toggle Switch

Renders a visual on/off switch.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

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
| label | string |
| is_checked | boolean |
| name | string |

## Example payload

```json
{
  "type": "toggle_switch",
  "label": "Toggle Switch",
  "is_checked": true,
  "name": "Toggle Switch"
}
```

Live page: https://a2uicatalog.ai/atoms/toggle_switch/
Full field contract: https://a2uicatalog.ai/spec.json
