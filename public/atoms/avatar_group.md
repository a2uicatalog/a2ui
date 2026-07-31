# Avatar Group

Renders a stack or row of small user avatars, often indicating a group

## Surfaces

web, google-meet-stage, pdf, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| avatars | list |
| total_count | integer |
| label | string |

## Example payload

```json
{
  "type": "avatar_group",
  "avatars": [
    {
      "src": "https://example.com/image.png",
      "name": "Alice"
    },
    {
      "src": "https://example.com/image.png",
      "name": "Bob"
    }
  ],
  "total_count": 5,
  "label": "Avatar Group"
}
```

Live page: https://a2uicatalog.ai/atoms/avatar_group/
Full field contract: https://a2uicatalog.ai/spec.json
