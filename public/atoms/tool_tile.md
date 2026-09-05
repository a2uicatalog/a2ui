# Tool Tile

Large icon+title tile, the WHOLE tile clickable — for a small set of primary choices (an app/tool selector), not a data-dense card. Bigger visual weight than a plain button. The wired dialect has no nested-children container atom, so lay several of these out as a grid by wrapping them in row_open/row_close with style "display:grid; grid-template-columns:repeat(N,1fr)" (row_open's own default display:flex is overridden by a later declaration in the same style string — normal CSS cascade, not a special case this atom needs to know about).

## Surfaces

google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| icon | string (optional). An ICON TOKEN (not an emoji or a font ligature), shown as an inline SVG line-icon in a small circular badge — "user", "book", "folder" today, extend the lookup table in atoms_nav.gs as more are needed. Inline, deliberately not a web font — Material Symbols (icon_feature_grid) loads from an external CDN the MCP Apps bundle's CSP-clean-by-design principle is very likely to block. A token this atom does not recognise renders as literal text instead of nothing, so passing an emoji directly still degrades visibly rather than silently. |
| label | string (required). The tile's title. |
| count | number (optional). Shown muted, in parentheses, right after label. |
| badge | string (optional). Small pill in the top-right corner, e.g. "POC". |
| variant | string (optional, default "indigo"). "indigo" (bold indigo/violet gradient) or "violet_magenta" (violet-to-magenta gradient) — two fixed color treatments, not an arbitrary color prop, so a grid of tiles reads as one deliberate palette rather than a random assortment. |

## Example payload

```json
{
  "type": "tool_tile",
  "label": "Tool Tile"
}
```

Live page: https://a2uicatalog.ai/atoms/tool_tile/
Full field contract: https://a2uicatalog.ai/spec.json
