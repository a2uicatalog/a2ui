# Cursor Trail

A chain of fading dots that follow the cursor using worm-chain physics — each dot lerps toward the one ahead of it, creating a fluid trailing effect.

## Surfaces

google-apps-script-web, web, google-meet-stage, mcp-apps

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
