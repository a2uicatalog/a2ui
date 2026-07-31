# Script Run Button

Interactive button that executes a custom Google Apps Script server function when clicked, showing a loading spinner and returning/displaying the function result. Works on Google Apps Script only.

## Surfaces

google-apps-script-web, mcp-apps

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
