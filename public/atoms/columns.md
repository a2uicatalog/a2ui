# Columns

Generic multi-column layout container. Each column holds an array of atom blocks rendered inline. 2–6 columns; collapses to single column on mobile.

## Surfaces

web, google-apps-script-web, pdf, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn with differences | 2026-11-13 | pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480) |
| a2ui-vue | Drawn with differences | 2026-11-13 | pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480) |
| Flutter | Degraded | 2026-11-13 | lowered to Basic components |
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| cols | integer (optional, 2–6, default 2) |
| gap | string (optional, css gap value, default "1.5rem") |
| align | string (optional, "top"|"center"|"stretch", default "top") |
| items | array (required). Each item is {blocks: [atom blocks]} — one entry per column. |

## Example payload

```json
{
  "type": "columns",
  "items": [
    {
      "label": "Item 1"
    },
    {
      "label": "Item 2"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/columns/
Full field contract: https://a2uicatalog.ai/spec.json
