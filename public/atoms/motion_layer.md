# Motion Layer

A scene. Children are any atoms, placed in percent of THIS layer (place {x, y, w, h, z, origin}, id, exactly as inside a motion_timeline), and the whole layer moves as one: give the layer an id and fade, slide, scale or blur it with opacity, x, y, scale and blur tracks to cut between scenes. Use it inside a motion_timeline; a layer with no place fills the stage. Layers are what make a piece with several scenes cheap to author: one id per scene instead of one track per element.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

## Fields

| Field | Type |
|---|---|
| blocks | array (max 24) of any atom blocks. Each may carry id (^[a-z][a-z0-9_-]{0,31}$), place {x, y, w, h, z, origin}. Ids must be unique across the whole timeline. |

## Example payload

```json
{
  "type": "motion_layer",
  "blocks": [
    {
      "type": "body",
      "text": "Example content."
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/motion_layer/
Full field contract: https://a2uicatalog.ai/spec.json
