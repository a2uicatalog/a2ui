# Animated Border

Card or section with a rotating conic gradient border. Child blocks or content inside.

## Surfaces

web, google-meet-stage, google-apps-script-web, google-apps-script-side-panel, mcp-apps

## Fields

| Field | Type |
|---|---|
| blocks | array of child atoms inside |
| content | markdown string (if no blocks) |
| from | gradient start colour (default |
| to | gradient end colour (default |
| via | gradient mid colour (default |
| speed | rotation speed in seconds (default 3) |
| padding | inner padding (default 20px) |
| radius | border radius (default 12px) |

## Example payload

```json
{
  "type": "animated_border",
  "blocks": [
    {
      "type": "body",
      "text": "Example content."
    }
  ],
  "content": "A concise description of the content."
}
```

Live page: https://a2uicatalog.ai/atoms/animated_border/
Full field contract: https://a2uicatalog.ai/spec.json
