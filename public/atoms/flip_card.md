# Flip Card

Renders a card with a front and back side that flips on interaction.

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
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| front_content | string |
| back_content | string |
| trigger_on_hover | boolean |

## Example payload

```json
{
  "type": "flip_card",
  "front_content": "Front content",
  "back_content": "Back content",
  "trigger_on_hover": true
}
```

Live page: https://a2uicatalog.ai/atoms/flip_card/
Full field contract: https://a2uicatalog.ai/spec.json
