# Typing Indicator

Three bouncing dots inside a chat bubble that signals an agent or user is composing a response. Each dot animates with a staggered delay using CSS @keyframes translateY, creating a continuous wave effect.

## Surfaces

web, google-meet-stage, google-apps-script-side-panel, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| name | string (optional). Agent or user name shown above the bubble. Default "Agent". |
| variant | "dark" | "light"  (optional, default "dark"). Bubble colour scheme. |

## Example payload

```json
{
  "type": "typing_indicator"
}
```

Live page: https://a2uicatalog.ai/atoms/typing_indicator/
Full field contract: https://a2uicatalog.ai/spec.json
