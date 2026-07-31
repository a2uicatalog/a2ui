# Jump Nav

Horizontal strip of pill buttons that smooth-scroll to other blocks on the page by id.

## Surfaces

google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| links | array (required) of {label, target (block id to scroll to)} |

## Example payload

```json
{
  "type": "jump_nav",
  "links": [
    {
      "label": "GitHub",
      "url": "https://github.com/a2uicatalog/a2ui"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/jump_nav/
Full field contract: https://a2uicatalog.ai/spec.json
