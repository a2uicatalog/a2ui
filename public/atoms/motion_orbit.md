# Motion Orbit

Tiles that fly out from the centre onto an ellipse as p goes 0 to 1, then swing round it as step goes 0 to 1: the ring of app icons around a product shot. Tiles are text (a letter, a glyph or a short label), never brand logos, so there is nothing to license. Place it over the same box as the thing it surrounds. Uses CSS cos() and sin(), so it needs a current browser. Plain HTML and CSS, no script; standalone it renders the tiles in place.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| items | array (max 12) of string or {text}; text max 8 characters (one or two reads as a glyph, longer as a small label). |
| size | integer (optional). Tile px, 24-160. Default 64. |
| rx | integer (optional). Horizontal radius, percent of the placed box, 5-60. Default 40. |
| ry | integer (optional). Vertical radius, percent of the placed box, 5-60. Default 36. |
| start | integer (optional). Angle of the first tile in degrees, -360 to 360. Default -90 (top). |
| spin | integer (optional). Degrees the ring turns as step goes 0 to 1, -360 to 360. Default 40. |
| fill | "#rrggbb" (optional). Tile colour. Default "#ffffff". |
| ink | "#rrggbb" (optional). Tile text colour. Default "#111827". |
| ring | bool (optional). A faint dashed ellipse behind the tiles. Default true. |

## Example payload

```json
{
  "type": "motion_orbit",
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

Live page: https://a2uicatalog.ai/atoms/motion_orbit/
Full field contract: https://a2uicatalog.ai/spec.json
