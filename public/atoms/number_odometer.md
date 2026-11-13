# Number Odometer

Slot-machine style digit-by-digit flip animation where each digit column independently scrolls to its target value using staggered CSS translateY keyframes. Distinct from animated_counter which counts up sequentially — this flips each digit column independently.

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
| value | string. The target number to display e.g. "1337" or "42.5k". |
| label | string (optional). Caption below the number. |
| color | string (optional). Digit colour. Default "#0f172a". |
| accent | string (optional). Accent colour. Default "#4f46e5". |
| size | string (optional). Font size. Default "3rem". |
| duration | number (optional). Animation duration in seconds. Default 1.2. |

## Example payload

```json
{
  "type": "number_odometer",
  "value": 1
}
```

Live page: https://a2uicatalog.ai/atoms/number_odometer/
Full field contract: https://a2uicatalog.ai/spec.json
