# Audio Player

Renders an embedded audio player for a given URL.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| audio_url | string |
| title | string |
| autoplay | boolean |
| loop | boolean |

## Example payload

```json
{
  "type": "audio_player",
  "audio_url": "https://example.com",
  "title": "Audio Player",
  "autoplay": true,
  "loop": true
}
```

Live page: https://a2uicatalog.ai/atoms/audio_player/
Full field contract: https://a2uicatalog.ai/spec.json
