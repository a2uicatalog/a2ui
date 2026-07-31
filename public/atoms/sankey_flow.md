# Sankey Flow

Renders a flow diagram (Sankey flow) where left-hand source nodes connect to right-hand target nodes via beautiful, curved gradient Bezier bands.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| nodes | list of dictionaries representing columns (e.g., [{'id': 'revenue', 'label': 'Revenue', 'column': 0, 'color': '#10b981'}, ...]) |
| links | list of dictionaries representing flows (e.g., [{'source': 'revenue', 'target': 'marketing', 'value': 25000, 'color': '#38bdf8'}, ...]) |
| title | string (optional, title of the chart, e.g., 'Financial Flow Allocation') |

## Example payload

```json
{
  "type": "sankey_flow",
  "nodes": [
    {
      "id": "a",
      "label": "Source"
    },
    {
      "id": "b",
      "label": "Target"
    }
  ],
  "links": [
    {
      "label": "GitHub",
      "url": "https://github.com/a2uicatalog/a2ui"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/sankey_flow/
Full field contract: https://a2uicatalog.ai/spec.json
