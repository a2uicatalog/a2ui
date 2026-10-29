# Motion Mask

Reveals its child blocks through a shape that grows as p goes 0 to 1: a wobbly blob, a circle, a diagonal wipe, a rounded rectangle that opens, venetian bars, a diamond, a halftone dot grid, a conic sweep, or horizontal slats. The scene that opens out of a cloud-shaped hole, or the screenshot that wipes in. The blob and circle are 20-vertex polygons whose coordinates use CSS cos() and sin(), so they need no script and a current browser. At p = 1 the child is fully visible; standalone it renders fully revealed.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

## Fields

| Field | Type |
|---|---|
| shape | "blob" | "circle" | "diagonal" | "rounded" | "bars" | "diamond" | "halftone" | "conic" | "slats" | "path" (optional, default "blob") |
| d | string (optional, max 4000 characters; used only when shape is "path"). An SVG path of straight and curve commands (M L H V C S Q T Z, absolute or relative; no arcs A, no exponent numbers, numbers up to 1000000). Only the first subpath is used. It is flattened, resampled to 48 points and stretched to fill the box, then scales in from the centre as p goes 0 to 1 (a 48-vertex clip polygon, pure CSS); at p = 1 the child shows through the whole shape. A missing or invalid d, or one that covers less than 1% of the box (a straight line), is ignored with an HTML comment and the blob is used. Absent: unchanged. |
| blocks | array (max 6) of any atom blocks, revealed together. Each may carry an id a timeline track can address. |

## Example payload

```json
{
  "type": "motion_mask",
  "blocks": [
    {
      "type": "body",
      "text": "Example content."
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/motion_mask/
Full field contract: https://a2uicatalog.ai/spec.json
