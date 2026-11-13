# Css Slide Panel

Renders a panel that slides into view from the side of the screen on activation.

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
| trigger_text | string |
| panel_content | string |
| slide_from_side | string |

## Example payload

```json
{
  "type": "css_slide_panel",
  "trigger_text": "Click to trigger",
  "panel_content": "Panel content",
  "slide_from_side": "Slide from side"
}
```

Live page: https://a2uicatalog.ai/atoms/css_slide_panel/
Full field contract: https://a2uicatalog.ai/spec.json
