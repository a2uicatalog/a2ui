# Script Run Button

Interactive button that executes a custom Google Apps Script server function when clicked, showing a loading spinner and returning/displaying the function result. Works on Google Apps Script only.

## Surfaces

google-apps-script-web, mcp-apps, android

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
| label | string. The button text. |
| function_name | string. The name of the server-side V8 JavaScript function to call. |
| argument | string (optional). Optional string argument to pass to the function. |

## Example payload

```json
{
  "type": "script_run_button",
  "label": "Script Run Button",
  "function_name": "Function name"
}
```

Live page: https://a2uicatalog.ai/atoms/script_run_button/
Full field contract: https://a2uicatalog.ai/spec.json
