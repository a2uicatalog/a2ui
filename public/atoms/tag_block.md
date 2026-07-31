# Tag Block

Horizontal wrapping block of plain content tags — feature labels, category chips, or keyword pills. Neutral styling. Distinct from badge_group which carries semantic status colour. Adapted from the TagBlock pattern in OpenUI OUI benchmark samples.

## Surfaces

web, google-meet-stage, email, pdf, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| tags | array of strings. The tag labels. |
| color | string (optional). Override chip accent — hex or CSS colour. Default is neutral gray. |

## Example payload

```json
{
  "type": "tag_block",
  "tags": [
    "typescript",
    "react",
    "a2ui"
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/tag_block/
Full field contract: https://a2uicatalog.ai/spec.json
