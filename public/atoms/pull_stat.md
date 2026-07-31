# Pull Stat

Renders a prominent, large statistic or number, often with a brief

## Surfaces

web, google-meet-stage, google-chat, email, pdf, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| value | string (the prominent number/statistic, e.g., "99%", "1.2M") |
| label | string (descriptive text for the stat, e.g., "customer satisfaction") |
| unit | optional string (e.g., "%", "users", "USD") |
| color | optional string (hex code or named color for the value) |

## Example payload

```json
{
  "type": "pull_stat",
  "value": 1,
  "label": "Pull Stat"
}
```

Live page: https://a2uicatalog.ai/atoms/pull_stat/
Full field contract: https://a2uicatalog.ai/spec.json
