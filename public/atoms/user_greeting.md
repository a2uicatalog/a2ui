# User Greeting

Personalised greeting showing the active user's Google account email. Works on Google Apps Script only.

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
| Flutter | Not supported | 2026-11-13 | component type unknown to the renderer |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| prefix | string (optional). The greeting prefix. Default is "Hello". |

## Example payload

```json
{
  "type": "user_greeting"
}
```

Live page: https://a2uicatalog.ai/atoms/user_greeting/
Full field contract: https://a2uicatalog.ai/spec.json
