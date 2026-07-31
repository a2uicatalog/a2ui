# Segmented Control

Renders a group of mutually exclusive buttons for selection, styled

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| options | list of objects with label, value |
| selected_value | string |
| name | string |

## Example payload

```json
{
  "type": "segmented_control",
  "options": [
    {
      "label": "Option A",
      "value": "a"
    },
    {
      "label": "Option B",
      "value": "b"
    },
    {
      "label": "Option C",
      "value": "c"
    }
  ],
  "selected_value": "Selected value",
  "name": "Segmented Control"
}
```

Live page: https://a2uicatalog.ai/atoms/segmented_control/
Full field contract: https://a2uicatalog.ai/spec.json
