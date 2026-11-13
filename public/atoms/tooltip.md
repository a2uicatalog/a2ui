# Tooltip

Renders a small, informational popup that appears when a user hovers

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
| trigger_text | string The text or element that, when hovered, reveals the tooltip. |
| tooltip_content | string The content displayed within the tooltip. |

## Example payload

```json
{
  "type": "tooltip",
  "trigger_text": "Click to trigger",
  "tooltip_content": "Tooltip content"
}
```

Live page: https://a2uicatalog.ai/atoms/tooltip/
Full field contract: https://a2uicatalog.ai/spec.json
