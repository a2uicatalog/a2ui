# Sankey Flow

Renders a flow diagram (Sankey flow) where nodes sit in columns from left to right and are connected by curved gradient Bezier bands whose width is the flow value. Two or more columns; columns come from each node's optional `column` hint, or from graph distance when it is absent. Layout is d3-sankey's.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

## Fields

| Field | Type |
|---|---|
| nodes | list of dictionaries (e.g., [{'id': 'revenue', 'label': 'Revenue', 'column': 0, 'color': '#10b981'}, ...]); `column` is an optional hint, an integer 0..n for the left-to-right column (0 = leftmost, up to 15); without it the column is the node's distance from the sources (a node with no outgoing flow goes to the last column), so a source -> middle -> target chain gets three columns and the chart is wider by 220px per column beyond two. Flows that close a cycle, or would run backwards between columns, are not drawn and are listed in a note under the chart. |
| links | list of dictionaries representing flows (e.g., [{'source': 'revenue', 'target': 'marketing', 'value': 25000, 'color': '#38bdf8'}, ...]) |
| title | string (optional, title of the chart, e.g., 'Financial Flow Allocation') |
| keyed | bool (optional, default false). True adds the build contract to the drawing so motion_build and motion_transition can move its parts: each node rectangle carries data-cb "node" and each node name data-cb "label", both with data-key = the node id, and each flow carries data-cb "link" with data-key = "sourceId>targetId" (a repeated pair gets "#2", "#3"). Use ids that another atom also keys (ISO 3166-1 alpha-3 codes against choropleth_map tiles) and a motion_transition joins the two element by element. Absent or false: the markup is unchanged, byte for byte. |

## Example payload

```json
{
  "type": "sankey_flow",
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
