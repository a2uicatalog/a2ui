# Print Button

A button that triggers window.print() to print or save the current page as PDF.

## Surfaces

web, google-apps-script-web, google-apps-script-side-panel, mcp-apps

## Fields

| Field | Type |
|---|---|
| label | string (default "Print this page") |
| align | left, center, or right |
| size | sm, md, or lg |
| accent | hex colour for button background |
| icon | boolean (default true) — show printer emoji prefix |

## Example payload

```json
{
  "type": "print_button",
  "align": "center",
  "size": "md",
  "accent": "#6366f1"
}
```

Live page: https://a2uicatalog.ai/atoms/print_button/
Full field contract: https://a2uicatalog.ai/spec.json
