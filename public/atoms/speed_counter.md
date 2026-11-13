# Speed Counter

Stopwatch that starts ticking on load and freezes when the page finishes loading — shows real page load time

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
| label | string (optional, e.g. "Page loaded in") |
| sub | string (optional, sub-label) |
| accent | string (optional, hex) |

## Example payload

```json
{
  "type": "speed_counter"
}
```

Live page: https://a2uicatalog.ai/atoms/speed_counter/
Full field contract: https://a2uicatalog.ai/spec.json
