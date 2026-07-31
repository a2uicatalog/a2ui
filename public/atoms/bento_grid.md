# Bento Grid

Asymmetric CSS grid of feature tiles. First tile typically spans multiple columns for visual emphasis. Supports per-tile icons, titles, descriptions, and accent colors. MagicUI/shadcn bento pattern.

## Surfaces

web, pdf, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| heading | string (optional). Section heading above the grid. |
| columns | integer (optional). Number of grid columns. Default 3. |
| tiles | array of objects with — title, subtitle, icon (emoji), span (integer, default 1; span 2 fills two columns), color (optional hex), background (optional hex). |

## Example payload

```json
{
  "type": "bento_grid"
}
```

Live page: https://a2uicatalog.ai/atoms/bento_grid/
Full field contract: https://a2uicatalog.ai/spec.json
