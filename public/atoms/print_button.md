# Print Button

A button that triggers window.print() to print or save the current page as PDF.

## Surfaces

web, google-apps-script-web, google-apps-script-side-panel, mcp-apps, android

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
