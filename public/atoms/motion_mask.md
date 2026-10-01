# Motion Mask

Reveals its child blocks through a shape that grows as p goes 0 to 1: a wobbly blob, a circle, a diagonal wipe, a rounded rectangle that opens, or venetian bars. The scene that opens out of a cloud-shaped hole, or the screenshot that wipes in. The blob and circle are 20-vertex polygons whose coordinates use CSS cos() and sin(), so they need no script and a current browser. At p = 1 the child is fully visible; standalone it renders fully revealed.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| shape | "blob" | "circle" | "diagonal" | "rounded" | "bars" (optional, default "blob") |
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
