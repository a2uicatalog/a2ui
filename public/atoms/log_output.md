# Log Output

Displays a scrollable monospace block containing raw system or compilation log strings.

## Surfaces

web, google-apps-script-web, mcp-apps, android

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
| logs | string. The raw console log output text block. |

## Example payload

```json
{
  "type": "log_output",
  "logs": "2026-06-28 INFO: Process started\n2026-06-28 INFO: Completed."
}
```

Live page: https://a2uicatalog.ai/atoms/log_output/
Full field contract: https://a2uicatalog.ai/spec.json
