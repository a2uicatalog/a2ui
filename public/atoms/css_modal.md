# Css Modal

Renders a modal dialog that appears on click and can be dismissed,

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

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
