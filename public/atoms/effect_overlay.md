# Effect Overlay

CSS-animated celebration overlay triggered by a named effect type. confetti fires falling coloured rectangles via keyframe animation. trophy bounces a large emoji with a scale-in animation. pulse radiates a glowing circle. fireworks scatters particles radially. Designed as a schema atom wrapper around the canvas particle blast used in Cyberpunk Maverick demos.

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
| Flutter | Native | 2026-11-13 |  |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| trigger | string (required). One of confetti, trophy, pulse, fireworks. |
| status | string (optional). Small label shown above the effect (e.g. resolved, done). |
| message | string (optional). Text shown below the icon. |
| color | string (optional). Primary accent color for pulse effect. Default |

## Example payload

```json
{
  "type": "effect_overlay",
  "trigger": "click"
}
```

Live page: https://a2uicatalog.ai/atoms/effect_overlay/
Full field contract: https://a2uicatalog.ai/spec.json
