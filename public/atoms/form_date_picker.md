# Form Date Picker

Date picker input supporting single-date selection or a date-range (start + end). Renders a calendar popover. Use inside a form or standalone.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| label | string (optional). Visible label. |
| name | string. Field identifier. |
| mode | string (optional). One of: single, range. Default: single. |
| placeholder | string (optional). e.g. 'Pick a date'. |
| rules | array of strings (optional). e.g. ['required']. |

## Example payload

```json
{
  "type": "form_date_picker",
  "name": "Form Date Picker"
}
```

Live page: https://a2uicatalog.ai/atoms/form_date_picker/
Full field contract: https://a2uicatalog.ai/spec.json
