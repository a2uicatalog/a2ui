# Hover Card

Renders a rich content card that appears when a user hovers over a specified trigger element.

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
| trigger_element | string The text or element that, when hovered, reveals the card. |
| card_title | string The title of the hover card. |
| card_content | string The main content of the hover card, can include rich text or simple HTML. |
| card_image_url | string, optional An optional image to display within the card. |

## Example payload

```json
{
  "type": "hover_card",
  "trigger_element": "Trigger element",
  "card_title": "Card title",
  "card_content": "Card content"
}
```

Live page: https://a2uicatalog.ai/atoms/hover_card/
Full field contract: https://a2uicatalog.ai/spec.json
