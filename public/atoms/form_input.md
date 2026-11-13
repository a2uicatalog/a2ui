# Form Input

Standalone labelled text input field — text, email, password, number, or url. Use inside a form atom or as a standalone search/filter control.

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
