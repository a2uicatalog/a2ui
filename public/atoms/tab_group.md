# Tab Group

Pill tabs that switch which ONE of several sibling atoms is visible, e.g. "how will you give me the source — a URL, a file, or pasted text" — rather than showing every input area stacked and unlabelled at once. panels maps a tab's value to ANOTHER layout element's id and toggles that element's own wrapper directly; safe regardless of layout order, since the whole surface's markup exists before any atom's script runs. Same direct-engine pattern as lens_grid/domain_picker.

## Surfaces

google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| target | string (optional). A ValueStore primitive's id, set to the selected tab's value on click. |
| options | array of {value, label, selected?} (required). |
| panels | object mapping a tab value to another layout element's id (required) — that element's wrapper is shown when its tab is selected, hidden otherwise. |

## Example payload

```json
{
  "type": "tab_group",
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
  "panels": "Panels"
}
```

Live page: https://a2uicatalog.ai/atoms/tab_group/
Full field contract: https://a2uicatalog.ai/spec.json
