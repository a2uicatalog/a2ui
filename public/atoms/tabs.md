# Tabs

CSS-only tabbed panels — ideal for multi-language code examples

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| accent | string (optional) |
| tabs | [{'label': 'string', 'language': 'string', 'content': 'string'}] |

## Example payload

```json
{
  "type": "tabs",
  "tabs": [
    {
      "label": "Tab 1",
      "content": "Content one."
    },
    {
      "label": "Tab 2",
      "content": "Content two."
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/tabs/
Full field contract: https://a2uicatalog.ai/spec.json
