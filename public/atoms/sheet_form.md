# Sheet Form

A form that submits data to a named Google Sheet tab via google.script.run. Requires the GAS project to be bound to a Spreadsheet.

## Surfaces

web, google-apps-script-web, google-apps-script-side-panel, mcp-apps, android

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
| title | optional form heading |
| sheet | sheet tab name to write to (required). Created automatically if it doesn't exist. |
| submit_label | button label (default "Submit") |
| accent | hex colour for submit button |
| fields | array (required). Each item has label, name (optional), type (text/email/textarea/select), placeholder, required, hint, options (for select), rows (for textarea) |

## Example payload

```json
{
  "type": "sheet_form",
  "sheet": "Sheet1",
  "accent": "#6366f1"
}
```

Live page: https://a2uicatalog.ai/atoms/sheet_form/
Full field contract: https://a2uicatalog.ai/spec.json
