# Video Pair

Two YouTube videos side by side with optional labels

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
| Flutter | Not supported | 2026-11-13 | component type unknown to the renderer |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| caption | string (optional) |
| left | {'url': 'string', 'label': 'string (optional)'} |
| right | {'url': 'string', 'label': 'string (optional)'} |

## Example payload

```json
{
  "type": "video_pair"
}
```

Live page: https://a2uicatalog.ai/atoms/video_pair/
Full field contract: https://a2uicatalog.ai/spec.json
