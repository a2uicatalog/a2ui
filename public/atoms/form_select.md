# Form Select

Labelled dropdown select with a list of value/label options. Supports required validation and an optional placeholder prompt.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn | 2026-11-13 |  |
| a2ui-vue | Drawn | 2026-11-13 |  |
| Flutter | Native | 2026-11-13 |  |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| label | string. Visible label. |
| name | string. Field identifier. |
| placeholder | string (optional). e.g. 'Select an option…' |
| options | {'type': 'array', 'description': 'List of {value, label} pairs.'} |
| rules | array of strings (optional). e.g. ['required']. |

## Example payload

```json
{
  "type": "form_select",
  "label": "Form Select",
  "name": "Form Select",
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

Live page: https://a2uicatalog.ai/atoms/form_select/
Full field contract: https://a2uicatalog.ai/spec.json
