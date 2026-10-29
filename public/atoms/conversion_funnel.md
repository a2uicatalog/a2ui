# Conversion Funnel

Renders a premium pipeline conversion funnel with tapered glowing step bars, percentage conversion rates, and leakage drop-off markers.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

## Fields

| Field | Type |
|---|---|
| title | string (optional, e.g., 'Acquisition Funnel') |
| steps | list of dictionaries representing funnel stages: [{'stage': 'Visits', 'value': 10000}, {'stage': 'Signups', 'value': 4500}, ...] |
| shape | string (optional, "area"): draws centred stacked bands whose area is proportional to each stage value (Plotly funnelarea) with a numbered legend and a hidden table; anything else keeps the tapered bars. Up to 12 stages. |
| version | integer (optional, default 1). A whole number above 1 draws as version 1 with a muted note (area shape only). |

## Example payload

```json
{
  "type": "conversion_funnel",
  "steps": [
    {
      "title": "Step one",
      "body": "First thing to do."
    },
    {
      "title": "Step two",
      "body": "Then this."
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/conversion_funnel/
Full field contract: https://a2uicatalog.ai/spec.json
