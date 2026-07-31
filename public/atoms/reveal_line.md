# Reveal Line

A single line of text that sweeps in from left using a clip-path animation — dramatic and instant. Auto-plays on load, no click required. Great for Meet Stage opening slides.

## Surfaces

google-apps-script-web, web, google-meet-stage, mcp-apps

## Fields

| Field | Type |
|---|---|
| text | string. Text content. |
| gradient | string (optional). CSS gradient applied to text. Default indigo→pink. |
| size | string (optional). Font-size. Default clamp(2.5rem,6vw,4rem). |
| weight | integer (optional). Font-weight. Default 900. |
| duration | integer (optional). Animation duration ms. Default 800. |
| delay | integer (optional). Start delay ms. Default 200. |

## Example payload

```json
{
  "type": "reveal_line",
  "text": "A concise description of the content."
}
```

Live page: https://a2uicatalog.ai/atoms/reveal_line/
Full field contract: https://a2uicatalog.ai/spec.json
