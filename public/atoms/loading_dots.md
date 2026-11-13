# Loading Dots

Three-dot pulsing loader. Use during async content load or as a status indicator.

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
| color | dot colour (default var(--a2ui-accent)) |
| size | sm, md (default), lg |
| label | optional text beside the dots |
| align | flex-start (default) or center |

## Example payload

```json
{
  "type": "loading_dots"
}
```

Live page: https://a2uicatalog.ai/atoms/loading_dots/
Full field contract: https://a2uicatalog.ai/spec.json
