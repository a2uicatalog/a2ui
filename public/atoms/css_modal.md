# Css Modal

Renders a modal dialog that appears on click and can be dismissed, controlled purely by CSS without JavaScript.

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
| trigger_text | string The text or element that, when clicked, opens the modal. |
| modal_title | string The title displayed at the top of the modal. |
| modal_body | string The main content of the modal dialog. |
| close_button_label | string, default "Close" The label for the button to close the modal. |

## Example payload

```json
{
  "type": "css_modal",
  "trigger_text": "Click to trigger",
  "modal_title": "Modal title",
  "modal_body": "Modal body"
}
```

Live page: https://a2uicatalog.ai/atoms/css_modal/
Full field contract: https://a2uicatalog.ai/spec.json
