# Color Section

Renders child atom blocks inside a colored background container. Use to visually group content with tint, solid, or dark style.

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| accent | string (optional, hex, default "#6366f1") |
| style | string (optional, "tint"|"solid"|"dark"|"light", default "tint") |
| padding | string (optional, css, default "24px") |
| grid | boolean (optional, default false, added 2026-07-24). Layers a faint 32px graph-paper grid (tinted by accent) on top of the base colour — for technical/blueprint-style sections. |
| max_width | string (optional, css length/%, added 2026-07-24). Caps and centres the section (e.g. "90%") so a wide section doesn't run the full column width; omitted → full width. |
| blocks | array (required, atom blocks rendered inside) |

## Example payload

```json
{
  "type": "color_section",
  "blocks": [
    {
      "type": "body",
      "text": "Example content."
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/color_section/
Full field contract: https://a2uicatalog.ai/spec.json
