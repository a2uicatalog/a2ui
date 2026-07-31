# Audio Link

Renders a clickable link to an audio file, often with an audio icon.

## Surfaces

web, google-meet-stage, google-chat, email, pdf, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| audio_url | string |
| label | string |
| icon_type | string |

## Example payload

```json
{
  "type": "audio_link",
  "audio_url": "https://example.com",
  "label": "Audio Link",
  "icon_type": "star"
}
```

Live page: https://a2uicatalog.ai/atoms/audio_link/
Full field contract: https://a2uicatalog.ai/spec.json
