# Tree View

IBM Carbon Design System hierarchical tree for displaying recursive data structures — organisational charts, category hierarchies, nested permission models, BOM trees. More semantically general than file_tree which is file-system specific. Expanded/collapsed state set per node. Adapted from IBM Carbon TreeView component.

## Surfaces

web, google-meet-stage, email, pdf, google-apps-script-web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn | 2026-11-13 |  |
| a2ui-vue | Drawn | 2026-11-13 |  |
| Flutter | Native | 2026-11-13 |  |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

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
