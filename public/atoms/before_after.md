# Before After

Side-by-side code comparison — red/green panels showing old vs new

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
| language | string |
| before | string |
| after | string |
| before_label | string (optional) |
| after_label | string (optional) |
| caption | string (optional) |

## Example payload

```json
{
  "type": "before_after",
  "language": "json",
  "before": "// example code",
  "after": "// example code"
}
```

Live page: https://a2uicatalog.ai/atoms/before_after/
Full field contract: https://a2uicatalog.ai/spec.json
