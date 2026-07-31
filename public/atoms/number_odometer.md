# Number Odometer

Slot-machine style digit-by-digit flip animation where each digit column independently scrolls to its target value using staggered CSS translateY keyframes. Distinct from animated_counter which counts up sequentially — this flips each digit column independently.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

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
