# Glitch Text

Cyan glitch-effect headline — periodic RGB-split animation

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
| text | string (alias: title, label) |
| size | string (optional, CSS font-size, default 2rem) |

## Example payload

```json
{
  "type": "glitch_text",
  "text": "A concise description of the content."
}
```

Live page: https://a2uicatalog.ai/atoms/glitch_text/
Full field contract: https://a2uicatalog.ai/spec.json
