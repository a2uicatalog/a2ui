# Surface Map

Visual diagram showing the A2UI surfaces — schema feeds into each render target

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (optional) |
| surfaces | array of {name, icon, desc, color} (optional, defaults to GAS/Meet/Sites/Chat) |
| accent | string (optional, hex) |

## Example payload

```json
{
  "type": "surface_map"
}
```

Live page: https://a2uicatalog.ai/atoms/surface_map/
Full field contract: https://a2uicatalog.ai/spec.json
