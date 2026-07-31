# Gradient Text

Heading text rendered with an animated shifting gradient fill using CSS background-clip:text and a background-position keyframe. The gradient flows continuously between the from/to colours, creating a shimmer effect on titles and hero text.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| text | string. The heading text to display. |
| from | string (optional). Gradient start colour. Default "#4f46e5". |
| to | string (optional). Gradient end colour. Default "#06b6d4". |
| via | string (optional). Optional midpoint colour. |
| size | string (optional). Font size. Default "2rem". |
| weight | string (optional). Font weight. Default "800". |
| duration | number (optional). Cycle duration in seconds. Default 4. |

## Example payload

```json
{
  "type": "gradient_text",
  "text": "A concise description of the content."
}
```

Live page: https://a2uicatalog.ai/atoms/gradient_text/
Full field contract: https://a2uicatalog.ai/spec.json
