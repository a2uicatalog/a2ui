# Form Radio Group

Labelled group of radio buttons for single-option selection. Each option has a value, visible label, and optional description.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| label | string (optional). Group label. |
| name | string. Field identifier. |
| options | {'type': 'array', 'description': 'List of {value, label, description?} entries.'} |
| default_value | string (optional). Pre-selected option value. |
| rules | array of strings (optional). e.g. ['required']. |

## Example payload

```json
{
  "type": "form_radio_group",
  "name": "Form Radio Group",
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
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/form_radio_group/
Full field contract: https://a2uicatalog.ai/spec.json
