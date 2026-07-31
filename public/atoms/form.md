# Form

Form container with labelled field controls and explicit submit/cancel buttons. Fields are expressed as a list of {label, type, name, placeholder, options, rules} entries.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (optional). Form heading shown above fields. |
| submit_label | string (optional, default 'Submit'). Label for the primary submit button. |
| cancel_label | string (optional). If set, renders a secondary cancel button. |
| fields | {'type': 'array', 'items': {'label': 'string. Visible field label.', 'name': 'string. Field identifier used in form submission.', 'type': 'string. One of: text, email, password, number, url, textarea, select, radio, checkbox, switch, slider, date. Default: text.', 'placeholder': 'string (optional).', 'options': 'array of {value, label} (required for select, radio, checkbox types).', 'default_value': 'string | boolean | number (optional).', 'rules': "array of strings (optional). Validation rules e.g. ['required', 'email', 'minLength:2']."}} |

## Example payload

```json
{
  "type": "form"
}
```

Live page: https://a2uicatalog.ai/atoms/form/
Full field contract: https://a2uicatalog.ai/spec.json
