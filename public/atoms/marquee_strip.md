# Marquee Strip

Infinite horizontally-scrolling strip of text labels or logo+text items, driven by a CSS @keyframes animation with no JavaScript. Ideal for customer logo rows, tech-stack badges, testimonial tickers, and social proof strips. Pause-on-hover is CSS-only.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| items | array. Each item is a string or {text, image_url} object. |
| speed | "slow" | "normal" | "fast"  (optional, default "normal") |
| direction | "left" | "right"  (optional, default "left") |
| pause_on_hover | bool (optional, default true). Pause scroll on hover. |
| label | string (optional). Small header label above the strip. |
| gap | string (optional). CSS gap between items. Default "40px". |

## Example payload

```json
{
  "type": "marquee_strip",
  "items": [
    {
      "label": "Item 1"
    },
    {
      "label": "Item 2"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/marquee_strip/
Full field contract: https://a2uicatalog.ai/spec.json
