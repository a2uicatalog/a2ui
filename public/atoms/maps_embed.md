# Maps Embed

Embeds a Google Maps location search in an iframe. Suitable for event location, office address, field ops context.

## Surfaces

web, google-apps-script-web, google-apps-script-side-panel, mcp-apps

## Fields

| Field | Type |
|---|---|
| q | address or place name to search (required) |
| height | iframe height in px (default 360) |
| zoom | map zoom level 1-20 (default 14) |
| caption | optional caption below the map |

## Example payload

```json
{
  "type": "maps_embed",
  "q": "Eiffel Tower, Paris"
}
```

Live page: https://a2uicatalog.ai/atoms/maps_embed/
Full field contract: https://a2uicatalog.ai/spec.json
