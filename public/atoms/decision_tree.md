# Decision Tree

Interactive collapsible decision tree with nested branches

## Surfaces

google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| nodes | array of {text, children: [{text, children}]} — nested tree nodes |
| title | string (optional) |

## Example payload

```json
{
  "type": "decision_tree",
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

Live page: https://a2uicatalog.ai/atoms/decision_tree/
Full field contract: https://a2uicatalog.ai/spec.json
