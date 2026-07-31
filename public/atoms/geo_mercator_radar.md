# Geo Mercator Radar

Interactive Mercator projection map with draggable pan, node pins, and animated link vectors — dark radar aesthetic

## Surfaces

google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (optional) |
| color | string (optional, hex accent, default #00f2ff) |
| height | number (optional, px, default 450) |
| nodes | array of {id, name, lat, lon, value (optional)} |
| links | array of {from: id, to: id} (optional) |

## Example payload

```json
{
  "type": "geo_mercator_radar"
}
```

Live page: https://a2uicatalog.ai/atoms/geo_mercator_radar/
Full field contract: https://a2uicatalog.ai/spec.json
