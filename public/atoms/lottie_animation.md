# Lottie Animation

Renders an active vector illustration display controlled via Lottie runtime rules.

## Surfaces

web, mcp-apps

## Fields

| Field | Type |
|---|---|
| src_url | string. Direct reference path to remote asset configuration. |
| loop | boolean. Whether playback recreates endlessly. |

## Example payload

```json
{
  "type": "lottie_animation",
  "src_url": "https://example.com",
  "loop": true
}
```

Live page: https://a2uicatalog.ai/atoms/lottie_animation/
Full field contract: https://a2uicatalog.ai/spec.json
