# Live Edit

Embedded mini schema editor with a textarea for typing a single atom JSON block and a live rendered preview below

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
| placeholder | string (optional, example atom JSON) |
| accent | string (optional, hex) |
| renderer_url | string (optional, renderer base URL for linking) |

## Example payload

```json
{
  "type": "live_edit"
}
```

Live page: https://a2uicatalog.ai/atoms/live_edit/
Full field contract: https://a2uicatalog.ai/spec.json
