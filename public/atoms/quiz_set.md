# Quiz Set

Multi-question quiz with multiple-choice options, per-question explanations, pass score, and result screen

## Surfaces

google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (optional) |
| questions | array of {question, options: [string], correct: integer (0-based index), explanation (optional)} |
| pass_score | integer (optional, % to pass, default 70) |
| accent | string (optional, hex) |
| on_pass | object (optional, atom block shown on pass) |
| on_fail | object (optional, atom block shown on fail) |

## Example payload

```json
{
  "type": "quiz_set"
}
```

Live page: https://a2uicatalog.ai/atoms/quiz_set/
Full field contract: https://a2uicatalog.ai/spec.json
