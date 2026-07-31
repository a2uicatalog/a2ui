# Word Flip

Inline overflow-hidden container that cycles through a list of words using a CSS steps() translateY animation. The agent provides the word array; the component handles all timing and looping. Useful for dynamic hero headlines such as "Grow your [Retention | Revenue | Signups]". No JavaScript required.

## Surfaces

web, google-meet-stage, google-apps-script-side-panel, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| words | array of strings. The words to cycle through. Minimum 2. |
| prefix | string (optional). Static text before the flipping section, e.g. "Grow your ". |
| suffix | string (optional). Static text after the flipping section. |
| speed | "slow" | "normal" | "fast"  (optional, default "normal"). Per-word hold duration. |
| color | string (optional). Flipping word colour. Default "#38bdf8". |
| size | string (optional). Font size, e.g. "32px". Default "inherit". |
| weight | string (optional). Font weight of flipping words. Default "700". |

## Example payload

```json
{
  "type": "word_flip",
  "words": [
    "Amazing",
    "Fast",
    "Reliable",
    "Scalable"
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/word_flip/
Full field contract: https://a2uicatalog.ai/spec.json
