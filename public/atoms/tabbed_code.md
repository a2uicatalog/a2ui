# Tabbed Code

Renders multiple code snippets organized inside an interactive, multi-tab container component.

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| tabs | array. Collection of objects containing the language identifier, tab label, and code string. |

## Example payload

```json
{
  "type": "tabbed_code",
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

Live page: https://a2uicatalog.ai/atoms/tabbed_code/
Full field contract: https://a2uicatalog.ai/spec.json
