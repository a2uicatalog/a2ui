# Text Reveal Mask

Headline that sweeps in from left using clip-path mask animation

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
| text | string (alias: title) |
| size | string (optional, CSS font-size) |
| color | string (optional, hex) |
| delay | number (optional, seconds) |

## Example payload

```json
{
  "type": "text_reveal_mask",
  "text": "A concise description of the content."
}
```

Live page: https://a2uicatalog.ai/atoms/text_reveal_mask/
Full field contract: https://a2uicatalog.ai/spec.json
