# Table

HTML table with styled headers, alternating rows, horizontal scroll

## Surfaces

web, google-meet-stage, email, pdf, google-apps-script-web, mcp-apps, claude-code, android, slides, pptx

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
| caption | string (optional) |
| headers | list[string] |
| rows | list[list[string]] |
| col_widths | list[string] (optional, added 2026-07-24). One CSS width per column (e.g. ["46%","18%","18%","18%"]), switches to table-layout:fixed. Without it, a long label in one column can pull free space away from short single-glyph cells in the others. |

## Example payload

```json
{
  "type": "table",
  "headers": [
    "Name",
    "Value",
    "Status"
  ],
  "rows": [
    [
      "Example",
      "42",
      "Active"
    ],
    [
      "Another",
      "17",
      "Pending"
    ]
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/table/
Full field contract: https://a2uicatalog.ai/spec.json
