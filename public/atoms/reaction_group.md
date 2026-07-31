# Reaction Group

Displays an interactive set of emoji elements collecting emotional sentiment feedback from readers.

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| enabled_emojis | array. Tracked emojis: thumbs_up | heart | rocket | mind_blown. |

## Example payload

```json
{
  "type": "reaction_group",
  "enabled_emojis": [
    "\ud83d\udc4d",
    "\u2764\ufe0f",
    "\ud83c\udf89",
    "\ud83d\ude80"
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/reaction_group/
Full field contract: https://a2uicatalog.ai/spec.json
