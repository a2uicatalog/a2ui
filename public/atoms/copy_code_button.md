# Copy Code Button

Renders a discrete interactive button that copies associated text or code to the clipboard.

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| text_to_copy | string. The raw string content sent to clipboard when clicked. |

## Example payload

```json
{
  "type": "copy_code_button",
  "text_to_copy": "Text to copy"
}
```

Live page: https://a2uicatalog.ai/atoms/copy_code_button/
Full field contract: https://a2uicatalog.ai/spec.json
