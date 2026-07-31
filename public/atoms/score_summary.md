# Score Summary

End-of-exercise or end-of-module score card showing correct answers, total questions, percentage, and optional time taken. Animates the score fraction on render using a CSS counter. Includes a contextual pass/fail or grade label and an optional retry/continue CTA row.

## Surfaces

web, google-meet-stage, pdf, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| correct | integer. Number of correct answers. |
| total | integer. Total number of questions. |
| time_taken | string (optional). Human-readable time string e.g. "2m 14s". |
| pass_threshold | integer (optional). Percentage (0–100) required to pass. Drives pass/fail label colour. |
| retry_label | string (optional). Label for the retry button. Omit to hide retry CTA. |
| continue_label | string (optional). Label for the continue button. Omit to hide continue CTA. |
| continue_url | url (optional). Destination for the continue button. |

## Example payload

```json
{
  "type": "score_summary",
  "correct": 1,
  "total": 5
}
```

Live page: https://a2uicatalog.ai/atoms/score_summary/
Full field contract: https://a2uicatalog.ai/spec.json
