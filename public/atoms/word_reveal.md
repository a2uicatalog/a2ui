# Word Reveal

Words appear one by one with a fade-up animation that auto-plays on page load — no user interaction required. Great for Meet Stage title slides and reveal moments.

## Surfaces

google-apps-script-web, web, google-meet-stage, mcp-apps

## Fields

| Field | Type |
|---|---|
| text | string. Text to reveal word by word. |
| colour | string (optional). Text colour. Default rgba(255,255,255,0.92). |
| gradient | string (optional). CSS gradient applied to whole line (overrides colour). |
| size | string (optional). Font-size. Default clamp(2rem,5vw,3.5rem). |
| weight | integer (optional). Font-weight. Default 800. |
| delay | number (optional). Seconds between each word. Default 0.12. |
| align | string (optional). text-align. Default center. |

## Example payload

```json
{
  "type": "word_reveal",
  "text": "A concise description of the content."
}
```

Live page: https://a2uicatalog.ai/atoms/word_reveal/
Full field contract: https://a2uicatalog.ai/spec.json
