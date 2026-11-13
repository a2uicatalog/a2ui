# Form Date Picker

Date picker input supporting single-date selection or a date-range (start + end). Renders a calendar popover. Use inside a form or standalone.

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
