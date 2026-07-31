# Effect Overlay

CSS-animated celebration overlay triggered by a named effect type. confetti fires falling coloured rectangles via keyframe animation. trophy bounces a large emoji with a scale-in animation. pulse radiates a glowing circle. fireworks scatters particles radially. Designed as a schema atom wrapper around the canvas particle blast used in Cyberpunk Maverick demos.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

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
