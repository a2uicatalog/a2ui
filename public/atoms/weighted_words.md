# Weighted Words

Agentic typesetting: the agent decides how much each WORD weighs. A headline where every word carries an emphasis 1-5 that sets its size, weight and opacity, with the heaviest words in the accent colour; words land in sequence, heavier ones from higher up. The reader sees the shape of the argument before reading it. Give it "words" as [{text, weight}] to typeset deliberately, or plain "text" for an even setting. Screenshot-ready, light or dark. Capped at 40 words of 24 characters; weights clamp to 1-5.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, pdf

## Fields

| Field | Type |
|---|---|
| words | array of {text, weight} (optional). weight is an integer 1-5; 5 is set in the accent colour. Strings are accepted as weight 2. |
| text | string (optional). Fallback when words is absent; every word set at weight 2. |
| voice | "display" | "serif" | "mono"  (optional, default "display"). System font stacks. |
| theme | "dark" | "light"  (optional, default "dark") |
| accent | "#rrggbb" (optional). Default "#38bdf8". |
| align | "left" | "center"  (optional, default "left") |
| animate | bool (optional). Words land in sequence on load. Default true. |

## Example payload

```json
{
  "type": "weighted_words"
}
```

Live page: https://a2uicatalog.ai/atoms/weighted_words/
Full field contract: https://a2uicatalog.ai/spec.json
