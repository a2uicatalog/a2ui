# Tree View

IBM Carbon Design System hierarchical tree for displaying recursive data structures — organisational charts, category hierarchies, nested permission models, BOM trees. More semantically general than file_tree which is file-system specific. Expanded/collapsed state set per node. Adapted from IBM Carbon TreeView component.

## Surfaces

web, google-meet-stage, email, pdf, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (optional). Label above the tree panel. |
| nodes | array. Recursive list of {label, icon?, expanded?, meta?, children?[]} node objects. |

## Example payload

```json
{
  "type": "tree_view",
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

Live page: https://a2uicatalog.ai/atoms/tree_view/
Full field contract: https://a2uicatalog.ai/spec.json
