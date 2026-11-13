# Audio Player

Renders an embedded audio player for a given URL.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn with differences | 2026-11-13 | contrast worse than React (dark 360); contrast worse than React (dark 480); overflows at 360 px; pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480); visible text differs from React |
| a2ui-vue | Drawn with differences | 2026-11-13 | pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480); visible text differs from React |
| Flutter | Degraded | 2026-11-13 | lowered to Basic components |
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| audio_url | string |
| title | string |
| autoplay | boolean |
| loop | boolean |

## Example payload

```json
{
  "type": "audio_player",
  "audio_url": "https://example.com",
  "title": "Audio Player",
  "autoplay": true,
  "loop": true
}
```

Live page: https://a2uicatalog.ai/atoms/audio_player/
Full field contract: https://a2uicatalog.ai/spec.json
