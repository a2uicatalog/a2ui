# Combobox

Searchable filterable dropdown that narrows its option list as the user types. Renders with a search icon, chevron, and an open option list for article preview. Native <datalist> enables browser-level autocomplete.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| label | string (optional). Visible label above the field. |
| name | string. Field identifier. |
| placeholder | string (optional). Input placeholder text. |
| options | array of {value, label} pairs. |
| selected | string (optional). Pre-selected option value. |
| rules | array of strings (optional). e.g. ['required']. |

## Example payload

```json
{
  "type": "combobox",
  "name": "Combobox",
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

Live page: https://a2uicatalog.ai/atoms/combobox/
Full field contract: https://a2uicatalog.ai/spec.json
