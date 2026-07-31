# Custom Checkbox Group

Renders a group of custom-styled checkboxes allowing multiple selections.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| group_label | string |
| options | list of objects with label, value, is_checked |
| name | string |

## Example payload

```json
{
  "type": "custom_checkbox_group",
  "group_label": "Group label",
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
  "name": "Custom Checkbox Group"
}
```

Live page: https://a2uicatalog.ai/atoms/custom_checkbox_group/
Full field contract: https://a2uicatalog.ai/spec.json
