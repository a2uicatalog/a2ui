# Split Reveal

Content hidden behind two coloured panels that slide apart to reveal it

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
| title | string (optional) |
| text | string (optional, alias: content) |
| color | string (optional, panel colour hex) |
| delay | number (optional, seconds) |

## Example payload

```json
{
  "type": "split_reveal"
}
```

Live page: https://a2uicatalog.ai/atoms/split_reveal/
Full field contract: https://a2uicatalog.ai/spec.json
