# Floating Badge

An emoji or icon that bobs up and down continuously. Great for CTAs and achievement moments.

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
| icon | emoji or character to float (required) |
| label | optional caption below |
| size | sm, md (default), lg |
| speed | bob cycle in seconds (default 3) |
| shadow | drop shadow that deepens on rise (default true) |
| align | center (default), left, right |

## Example payload

```json
{
  "type": "floating_badge",
  "icon": "\u2b50"
}
```

Live page: https://a2uicatalog.ai/atoms/floating_badge/
Full field contract: https://a2uicatalog.ai/spec.json
