# Readability Card

Prose metrics as a typographic card: the Flesch reading-ease score set huge, its plain-language grade, and a stat row -- words, sentences, minutes to read at a declared words-per-minute, words per sentence, syllables per word, longest sentence -- all computed by the renderer from the text with identical arithmetic on every renderer (syllables by a vowel-group heuristic, sentences on . ! ? followed by space). The excerpt is shown underneath with the longest sentence highlighted, which is usually the one to cut. Built for the writing workflow; give it a draft and it tells you what a reader will feel.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, pdf

## Fields

| Field | Type |
|---|---|
| text | string (required). The prose to measure, up to 5000 characters. |
| title | string (optional). Label above the score. Default "readability". |
| wpm | integer (optional). Reading speed for the time estimate, clamped 100-500. Default 230. |
| highlight_longest | bool (optional). Mark the longest sentence in the excerpt. Default true. |
| theme | "dark" | "light"  (optional, default "light") |
| accent | "#rrggbb" (optional). Default "#0e7bb8". |

## Example payload

```json
{
  "type": "readability_card",
  "text": "A concise description of the content."
}
```

Live page: https://a2uicatalog.ai/atoms/readability_card/
Full field contract: https://a2uicatalog.ai/spec.json
