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
| default_value | string (optional). Pre-selected option value. `selected_value` is accepted as a synonym — the renderer read only that spelling while this file documented only this one, so the documented prop pre-selected nothing until 2026-08-14. |
| rules | array of strings (optional). e.g. ['required']. |
| wired | Carries `onChange` in the wired dialect, emitting the CHECKED option's value, and accepts a `value` wire that checks the matching option. The binding DELEGATES over the group rather than reading the first input, so N elements behave as one control. This is the single-select alternative to combobox for the case a dropdown gets wrong: few options, on a phone, where a dropdown costs two taps and a modal to answer a three-way question. |

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
  ],
  "wired": "Wired"
}
```

Live page: https://a2uicatalog.ai/atoms/form_radio_group/
Full field contract: https://a2uicatalog.ai/spec.json
