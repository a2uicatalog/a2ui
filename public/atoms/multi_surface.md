# Multi Surface

One data pool rendered simultaneously across three surface engines: spatial map (desktop), phone frame card list (mobile), circular focus face (IoT/watch)

## Surfaces

google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (optional) |
| nodes | array of {id, type, label, temp (optional), value (optional), intensity (0–100, optional), coords: {x, y}} |

## Example payload

```json
{
  "type": "multi_surface"
}
```

Live page: https://a2uicatalog.ai/atoms/multi_surface/
Full field contract: https://a2uicatalog.ai/spec.json
