# Embed Codepen

Renders an embedded interactive CodePen sandbox workspace within the document.

## Surfaces

web, mcp-apps

## Fields

| Field | Type |
|---|---|
| pen_id | string. Alphanumeric identity of the target snippet. |
| user_handle | string. Profile handle owning the snippet. |

## Example payload

```json
{
  "type": "embed_codepen",
  "pen_id": "Pen id",
  "user_handle": "User handle"
}
```

Live page: https://a2uicatalog.ai/atoms/embed_codepen/
Full field contract: https://a2uicatalog.ai/spec.json
