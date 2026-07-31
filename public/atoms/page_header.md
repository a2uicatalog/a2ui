# Page Header

Full-width app-style page header with title, subtitle, icon, accent color, and optional tag badge. Sets the visual tone of a pop-up app or brief. Use as the first block of any page.

## Surfaces

web, google-apps-script-web, pdf, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (required, markdown) |
| subtitle | string (optional, markdown) |
| icon | string (optional, emoji or short text) |
| tag | string (optional, badge label shown in accent pill) |
| accent | string (optional, hex, default "#6366f1") |
| theme | string (optional, "light"|"dark", default "light") |
| background | string (optional, css background override — now honoured in dark theme too, added 2026-07-24; previously silently discarded in favour of the dark default) |
| meta | array (optional, added 2026-07-24). Array of {label, value} shown as a small monospace stat row under the header — e.g. a title-block summary line for a reference/spec page. |

## Example payload

```json
{
  "type": "page_header",
  "title": "Page Header"
}
```

Live page: https://a2uicatalog.ai/atoms/page_header/
Full field contract: https://a2uicatalog.ai/spec.json
