# Chartjs Pie

Multi-slice pie or donut chart rendered as inline SVG — category proportions with a colour-coded legend. Distinct from donut_stat which shows a single metric as a CSS ring. Adapted from the PieChart/Slice pattern in OpenUI OUI benchmark samples.

## Surfaces

web, google-meet-stage, pdf, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (optional). Chart heading. |
| variant | string (optional). "pie" or "donut". Default "donut". |
| data | {'type': 'array', 'description': 'List of {label, value} slice objects.'} |
| colors | array of strings (optional). Hex colours per slice; auto-assigned if omitted. |
| show_legend | boolean (optional). Show colour-keyed legend below chart. Default true. |
| show_labels | boolean (optional). Show percentage labels on slices. Default true. |

## Example payload

```json
{
  "type": "chartjs_pie",
  "data": [
    {
      "label": "Category A",
      "value": 40
    },
    {
      "label": "Category B",
      "value": 35
    },
    {
      "label": "Category C",
      "value": 25
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/chartjs_pie/
Full field contract: https://a2uicatalog.ai/spec.json
