# Cursor Trail

A chain of fading dots that follow the cursor using worm-chain physics — each dot lerps toward the one ahead of it, creating a fluid trailing effect.

## Surfaces

google-apps-script-web, web, google-meet-stage, mcp-apps, android

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
| colour | string (optional). Dot colour. Default |
| length | integer (optional). Number of chain dots. Default 16. |
| size | integer (optional). Lead dot diameter px. Default 10. |
| speed | number (optional). Lerp factor per dot. Default 0.35. |

## Example payload

```json
{
  "type": "cursor_trail"
}
```

Live page: https://a2uicatalog.ai/atoms/cursor_trail/
Full field contract: https://a2uicatalog.ai/spec.json
