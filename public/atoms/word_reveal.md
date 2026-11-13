# Word Reveal

Words appear one by one with a fade-up animation that auto-plays on page load — no user interaction required. Great for Meet Stage title slides and reveal moments.

## Surfaces

google-apps-script-web, web, google-meet-stage, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn | 2026-11-13 |  |
| a2ui-vue | Drawn | 2026-11-13 |  |
| Flutter | Native | 2026-11-13 |  |
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

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
