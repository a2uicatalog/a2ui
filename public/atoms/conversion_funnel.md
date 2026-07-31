# Conversion Funnel

Renders a premium pipeline conversion funnel with tapered glowing step bars, percentage conversion rates, and leakage drop-off markers.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (optional, e.g., 'Acquisition Funnel') |
| steps | list of dictionaries representing funnel stages: [{'stage': 'Visits', 'value': 10000}, {'stage': 'Signups', 'value': 4500}, ...] |

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
