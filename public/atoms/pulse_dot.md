# Pulse Dot

Pulsing status or attention indicator dot. Inline or block display.

## Surfaces

web, google-meet-stage, google-apps-script-web, google-apps-script-side-panel, mcp-apps, android

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
| color | dot colour (default |
| size | sm, md (default), lg |
| label | optional text beside the dot |
| speed | animation cycle in seconds (default 1.8) |
| inline | render inline (default true) |

## Example payload

```json
{
  "type": "pulse_dot"
}
```

Live page: https://a2uicatalog.ai/atoms/pulse_dot/
Full field contract: https://a2uicatalog.ai/spec.json
