# Count Up Stat

A stat number that counts up from zero to the target value using a cubic ease function on page load. Auto-plays — no user interaction required.

## Surfaces

google-apps-script-web, web, google-meet-stage, mcp-apps

## Fields

| Field | Type |
|---|---|
| value | integer. Target number to count to. |
| label | string (optional). Descriptor shown below the number. |
| prefix | string (optional). Text before the number (e.g. "$"). |
| suffix | string (optional). Text after the number (e.g. "%", "k"). |
| colour | string (optional). Glow colour. Default |
| duration | integer (optional). Count-up duration ms. Default 1800. |
| size | string (optional). Font-size. Default 4rem. |

## Example payload

```json
{
  "type": "count_up_stat",
  "value": 1
}
```

Live page: https://a2uicatalog.ai/atoms/count_up_stat/
Full field contract: https://a2uicatalog.ai/spec.json
