# Split Stat

Two-column layout — a large glowing stat number on the left (with neon text-shadow) and heading + body text on the right. Classic keynote layout, great for Meet Stage.

## Surfaces

google-apps-script-web, web, google-meet-stage, mcp-apps

## Fields

| Field | Type |
|---|---|
| value | string. The stat number or short value. |
| prefix | string (optional). Text before value (e.g. "$", "~"). |
| suffix | string (optional). Text after value (e.g. "%", "k", "+"). |
| heading | string (optional). Right-side heading. |
| body | string (optional). Right-side paragraph text. |
| colour | string (optional). Stat glow colour. Default |
| flip | boolean (optional). Put stat on right side. Default false. |

## Example payload

```json
{
  "type": "split_stat",
  "value": 1
}
```

Live page: https://a2uicatalog.ai/atoms/split_stat/
Full field contract: https://a2uicatalog.ai/spec.json
