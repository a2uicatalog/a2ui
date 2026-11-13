# Lottie Animation

Renders an active vector illustration display controlled via Lottie runtime rules.

## Surfaces

web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Not verified | 2026-11-13 | no visible text in the example |
| Lit | Not verified | 2026-11-13 | blank on both sides (light 360); blank on both sides (light 480); no visible text in the example |
| Angular | Not verified | 2026-11-13 | blank on both sides (light 360); blank on both sides (light 480); no visible text in the example |
| CopilotKit | Not verified | 2026-11-13 | blank on both sides (light 360); blank on both sides (light 480); no visible text in the example |
| a2ui-vue | Not verified | 2026-11-13 | blank on both sides (light 360); blank on both sides (light 480); no visible text in the example |
| Flutter | Not supported | 2026-11-13 | component type unknown to the renderer |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| src_url | string. Direct reference path to remote asset configuration. |
| loop | boolean. Whether playback recreates endlessly. |

## Example payload

```json
{
  "type": "lottie_animation",
  "src_url": "https://example.com",
  "loop": true
}
```

Live page: https://a2uicatalog.ai/atoms/lottie_animation/
Full field contract: https://a2uicatalog.ai/spec.json
