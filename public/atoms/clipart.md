# Clipart

One piece of verified vector clipart from the scene kit, by id, drawn at its own size with an optional variant (for example a person in a hard hat), scale and flip. Themeable colours, original MIT artwork, no external references. Use it as an illustration inside an article, card or slide; use scene_stage when several props should be composed into a moving picture.

## Surfaces

mcp-apps

## Fields

| Field | Type |
|---|---|
| asset | string. A prop id from the asset index (https://a2uicatalog.ai/catalogue/assets-index-v1.json); only stable props are listed and preview props are refused. |
| variant | string (optional). A variant of that prop, for example scrubs, hard-hat or doctor on person-standing. |
| scale | number (optional, 0.2..5). Default 1. |
| flip | boolean (optional). Mirror horizontally. |
| time | "dawn"|"day"|"dusk"|"night" (optional). Palette the artwork is drawn in. Default day. |
| label | string (optional). Caption under the image. |
| alt | string (optional). Accessible name. Default is the prop name. |

## Example payload

```json
{
  "type": "clipart",
  "asset": []
}
```

Live page: https://a2uicatalog.ai/atoms/clipart/
Full field contract: https://a2uicatalog.ai/spec.json
