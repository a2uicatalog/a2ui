# Decision Tree

Interactive collapsible decision tree with nested branches

## Surfaces

web, google-apps-script-web, mcp-apps, android

## Fields

| Field | Type |
|---|---|
| nodes | array of {text, children: [{text, children}]} — nested tree nodes |
| title | string (optional) |
| layout | string (optional). Absent, 'outline' or anything else keeps the collapsible outline. 'tree' draws the nested form as a static top-down tidy tree (the same d3 tree layout and boxes as org_chart; the nested lists stay in the page for screen readers, but there is nothing to expand or collapse). It draws at most 31 nodes, 6 levels and labels of up to 32 characters; beyond that, or for the id/next graph form, the outline is shown with a note. Branch text stays inside each node's text (there is no separate edge label field). |
| version | integer (optional, default 1). The decision_tree contract the payload was written for. Only version 1 exists; a higher whole number is drawn as version 1 with a note. |

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
