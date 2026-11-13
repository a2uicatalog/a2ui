# Image Pair

Two images side by side with individual captions

## Surfaces

web, google-meet-stage, pdf, google-apps-script-web, mcp-apps, android

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
| left | {'url': 'string', 'alt': 'string', 'caption': 'string (optional)'} |
| right | {'url': 'string', 'alt': 'string', 'caption': 'string (optional)'} |

## Example payload

```json
{
  "type": "image_pair"
}
```

Live page: https://a2uicatalog.ai/atoms/image_pair/
Full field contract: https://a2uicatalog.ai/spec.json
