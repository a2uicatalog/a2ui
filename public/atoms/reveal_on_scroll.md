# Reveal On Scroll

Content block that starts invisible and fades + slides into view when scrolled into the viewport, using an IntersectionObserver with a CSS class toggle. Requires a small inline script — degrades gracefully to visible static content where JS is unavailable.

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (optional). Bold heading inside the block. |
| body | string (optional). Body text inside the block. |
| direction | "up" | "down" | "left" | "right"  (optional, default "up"). Drift direction before reveal. |
| duration | number (optional). Transition duration in seconds. Default 0.7. |
| accent | string (optional). Left border accent colour. Default "#4f46e5". |
| background | string (optional). Block background. Default "#f8fafc". |

## Example payload

```json
{
  "type": "reveal_on_scroll"
}
```

Live page: https://a2uicatalog.ai/atoms/reveal_on_scroll/
Full field contract: https://a2uicatalog.ai/spec.json
