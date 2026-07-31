# Resources List

Renders a clean inventory list of downloadable assets or reference files with metadata.

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| items | array. Download assets containing title, size, type, and url. |

## Example payload

```json
{
  "type": "resources_list",
  "items": [
    {
      "label": "Item 1"
    },
    {
      "label": "Item 2"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/resources_list/
Full field contract: https://a2uicatalog.ai/spec.json
