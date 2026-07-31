# File Tree

Renders a hierarchical layout displaying directory structures, folders, and individual files for software projects.

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| nodes | array. Highly structured list of folder and file objects with nesting indicators. |

## Example payload

```json
{
  "type": "file_tree",
  "nodes": [
    {
      "label": "src/",
      "children": [
        {
          "label": "index.ts"
        }
      ]
    },
    {
      "label": "package.json"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/file_tree/
Full field contract: https://a2uicatalog.ai/spec.json
