# Form Input

Standalone labelled text input field — text, email, password, number, or url. Use inside a form atom or as a standalone search/filter control.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| label | string. Visible label above the input. |
| name | string. Field identifier. |
| type | string (optional). One of: text, email, password, number, url. Default: text. |
| placeholder | string (optional). |
| rules | array of strings (optional). e.g. ['required', 'email', 'minLength:2']. |

## Example payload

```json
{
  "type": "form_input",
  "label": "Form Input",
  "name": "Form Input"
}
```

Live page: https://a2uicatalog.ai/atoms/form_input/
Full field contract: https://a2uicatalog.ai/spec.json
