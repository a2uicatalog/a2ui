# Media Stream Card

Auto-detecting media embed that accepts a raw URL and builds the correct iframe for YouTube, Loom, Google Slides, or Vimeo. Displays a labelled card shell with a skeleton shimmer while loading. Designed for stage-first delivery where the URL is the only payload.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| url | string (required). Raw URL — YouTube, Loom, Google Slides, Vimeo, or any embeddable URL. Platform is auto-detected. |
| title | string (optional). Card label shown above the iframe. Defaults to detected platform name. |
| height | string (optional). CSS height for the iframe container. Default 360px. |

## Example payload

```json
{
  "type": "media_stream_card",
  "url": "https://example.com"
}
```

Live page: https://a2uicatalog.ai/atoms/media_stream_card/
Full field contract: https://a2uicatalog.ai/spec.json
