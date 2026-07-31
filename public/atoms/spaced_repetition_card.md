# Spaced Repetition Card

Single flashcard with front/back flip animation and a post-flip confidence rating (1-5 with emoji). Writes {rating, next_days, rated_at} to progress_store under "srs:<card_id>". Next-review hint computed via simplified SM-2 (1→1d, 2→2d, 3→4d, 4→7d, 5→14d).

## Surfaces

google-apps-script-web, web, google-meet-stage, mcp-apps

## Fields

| Field | Type |
|---|---|
| front | string (required). Front face — term or question. |
| back | string (required). Back face — answer or definition. |
| card_id | string (optional). Key for progress_store SRS data. Auto-generated if omitted. |
| accent | string (optional). Front card highlight colour. Default |

## Example payload

```json
{
  "type": "spaced_repetition_card",
  "front": "What is an atom?",
  "back": "A self-contained UI block with a type and fields."
}
```

Live page: https://a2uicatalog.ai/atoms/spaced_repetition_card/
Full field contract: https://a2uicatalog.ai/spec.json
