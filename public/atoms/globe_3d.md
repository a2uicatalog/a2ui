# Globe 3D

Spinning interactive 3-D wireframe or earth globe rendered on HTML5 canvas — draggable with inertia

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| size | number (optional, diameter px, default 300) |
| color | string (optional, hex accent, default #6366f1) |
| speed | number (optional, auto-spin speed, default 0.006) |
| lines | number (optional, latitude line count, default 10) |
| theme | string (optional, wire|earth, default wire) |
| dots | array of {lat, lon, label (optional), color (optional)} (optional, pins on globe) |
| arcs | array of {from: [lat,lon], to: [lat,lon], color (optional)} (optional, great-circle arcs) |

## Example payload

```json
{
  "type": "globe_3d"
}
```

Live page: https://a2uicatalog.ai/atoms/globe_3d/
Full field contract: https://a2uicatalog.ai/spec.json
