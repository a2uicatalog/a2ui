# Motion Shader

A WebGL shader background: a domain-warped liquid gradient (kind liquid), soft aurora bands (kind aurora) or folded satin with a moving sheen (kind silk) in three colours. Seekable: shader time follows the film, read from the second dial (--s) every frame, so a step track drives it and seeking shows exactly that frame (span = shader seconds per unit of --s); standalone it runs on its own clock, or holds still with still true or under reduced motion. The shader and its driver are fixed in the renderer and the config is numbers only, so nothing in the payload becomes code. Its own CSS gradient of the same colours is the fallback when WebGL is missing, the shader fails, the page prints or the host strips scripts. p fades it in. Preview: a spike to judge whether WebGL earns a place.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| kind | "liquid" | "aurora" | "silk" (optional, default "liquid"). silk: satin folds lit from their own surface, color1 the shadowed cloth, color2 the lit cloth, color3 the sheen. |
| color1 | "#rrggbb" (optional). Deep colour. Default #0b0712. |
| color2 | "#rrggbb" (optional). Default #ff3d81. |
| color3 | "#rrggbb" (optional). Default #ffb347. |
| scale | number (optional). Pattern scale, 0.5-12. Default 2. |
| span | number (optional). Shader seconds per unit of --s, 0-600. Default 20. |
| speed | number (optional). Standalone speed, 0-5. Default 1. |
| still | bool (optional). Standalone, hold a still frame. Default false. |
| ratio | "16:9" | "4:3" | "1:1" | "3:4" | "9:16" (optional, default "16:9") |
| fill | bool (optional). Fill the placed box height instead of using ratio. Default false. |
| radius | integer (optional). Corner px, 0-60. Default 0. |
| label | string (optional, max 60). Accessible name. |

## Example payload

```json
{
  "type": "motion_shader"
}
```

Live page: https://a2uicatalog.ai/atoms/motion_shader/
Full field contract: https://a2uicatalog.ai/spec.json
