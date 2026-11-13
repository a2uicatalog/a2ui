# Status Timeline

Vertical timeline with status dots (done/active/pending/error/warning)

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
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| events | array of {title, date (optional), text (optional), status (done|active|pending|error|warning)} |
| title | string (optional) |

## Example payload

```json
{
  "type": "status_timeline"
}
```

Live page: https://a2uicatalog.ai/atoms/status_timeline/
Full field contract: https://a2uicatalog.ai/spec.json
