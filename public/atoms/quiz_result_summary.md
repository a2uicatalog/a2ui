# Quiz Result Summary

End-of-quiz result screen showing score percentage, pass/fail badge, time taken, per-question dot breakdown (green tick / red cross), and navigation buttons. Automatically writes the score to progress_store keyed by quiz_id. Pass mark is configurable.

## Surfaces

google-apps-script-web, web, google-meet-stage, mcp-apps

## Fields

| Field | Type |
|---|---|
| score | integer (required). Number of correct answers. |
| total | integer (required). Total number of questions. |
| quiz_id | string (required). ID used to write score to progress_store. |
| pass_mark | integer (optional). Percentage required to pass. Default 70. |
| time_secs | integer (optional). Time taken in seconds for display. |
| questions | array (optional). Array of {label, correct} for per-question breakdown dots. |
| next_url | string (optional). URL for Continue button (shown when passed). |
| retry_url | string (optional). URL for Retry button. |

## Example payload

```json
{
  "type": "quiz_result_summary",
  "score": 75,
  "total": 5,
  "quiz_id": "Quiz id"
}
```

Live page: https://a2uicatalog.ai/atoms/quiz_result_summary/
Full field contract: https://a2uicatalog.ai/spec.json
