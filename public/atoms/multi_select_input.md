# Multi Select Input

Tag/chip style multi-value selector. Displays selected values as removable chips above a filtered option list. Shadcn multi-select pattern.

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
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| label | string (optional). Visible label above the field. |
| name | string. Field identifier. |
| placeholder | string (optional). Input placeholder when no chips are selected. |
| options | array of {value, label} pairs. |
| selected | array of value strings. Pre-selected values shown as chips. |

## Example payload

```json
{
  "type": "multi_select_input",
  "name": "Multi Select Input",
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
  "selected": [
    "Option A"
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/multi_select_input/
Full field contract: https://a2uicatalog.ai/spec.json
