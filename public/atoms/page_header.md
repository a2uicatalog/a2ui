# Page Header

Full-width app-style page header with title, subtitle, icon, accent color, and optional tag badge. Sets the visual tone of a pop-up app or brief. Use as the first block of any page.

## Surfaces

web, google-apps-script-web, pdf, mcp-apps, android, slides, pptx

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn with differences | 2026-11-13 | pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480); content sits 1 px lower than in React (and than 1.85.0), stable between passes; cause not isolated. A real difference, not hidden |
| a2ui-vue | Drawn | 2026-11-13 |  |
| Flutter | Native | 2026-11-13 |  |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| title | string (required, markdown) |
| subtitle | string (optional, markdown) |
| icon | string (optional, emoji or short text) |
| tag | string (optional, badge label shown in accent pill) |
| accent | string (optional, hex, default "#4f46e5") |
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
