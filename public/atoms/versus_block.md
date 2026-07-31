# Versus Block

Renders a block explicitly comparing two entities with a prominent

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| entity_a_name | string |
| entity_a_description | string |
| entity_a_image_url | string |
| entity_b_name | string |
| entity_b_description | string |
| entity_b_image_url | string |
| comparison_points | array |

## Example payload

```json
{
  "type": "versus_block",
  "entity_a_name": "Entity a name",
  "entity_a_description": "Entity a description",
  "entity_a_image_url": "https://example.com",
  "entity_b_name": "Entity b name",
  "entity_b_description": "Entity b description",
  "entity_b_image_url": "https://example.com",
  "comparison_points": [
    {
      "label": "Performance",
      "a": "Fast",
      "b": "Moderate"
    },
    {
      "label": "Price",
      "a": "$9",
      "b": "$19"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/versus_block/
Full field contract: https://a2uicatalog.ai/spec.json
