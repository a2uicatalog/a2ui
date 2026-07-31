# Isometric Mesh

Rotating 3D isometric height-field mesh. Default surface is a 16×16 Gaussian hill pre-computed server-side. Drag to rotate manually; auto-rotates until first touch. Height colour interpolates from deep indigo (low) to bright violet (high).

## Surfaces

google-apps-script-web, web, google-meet-stage, mcp-apps

## Fields

| Field | Type |
|---|---|
| grid | integer (optional). Grid dimension N (N×N). Default 16. |
| height_scale | number (optional). Vertical exaggeration multiplier. Default 1.0. |
| colour_low | string (optional). Hex colour at minimum height. Default |
| colour_high | string (optional). Hex colour at maximum height. Default |
| bg | string (optional). Background colour. Default |
| height | integer (optional). Canvas height px. Default 460. |
| auto_rotate | boolean (optional). Auto-rotate until user drags. Default true. |

## Example payload

```json
{
  "type": "isometric_mesh"
}
```

Live page: https://a2uicatalog.ai/atoms/isometric_mesh/
Full field contract: https://a2uicatalog.ai/spec.json
