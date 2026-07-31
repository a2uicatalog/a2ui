# Tilt Card

A card that tilts in 3D perspective as the cursor moves across it, with a radial glare highlight that tracks cursor position. Uses CSS preserve-3d and dynamic box-shadow.

## Surfaces

google-apps-script-web, web, google-meet-stage, mcp-apps

## Fields

| Field | Type |
|---|---|
| content | string (optional). Inner HTML rendered inside the card. |
| title | string (optional). Card heading rendered above content. |
| max_tilt | number (optional). Maximum rotation degrees. Default 14. |
| glare | boolean (optional). Show glare highlight. Default true. |
| accent | string (optional). Glare colour. Default rgba(255,255,255,0.15). |
| padding | string (optional). Inner padding. Default 28px. |

## Example payload

```json
{
  "type": "tilt_card"
}
```

Live page: https://a2uicatalog.ai/atoms/tilt_card/
Full field contract: https://a2uicatalog.ai/spec.json
