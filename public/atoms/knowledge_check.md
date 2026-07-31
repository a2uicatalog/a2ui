# Knowledge Check

Lightweight inline comprehension pulse — a single multiple-choice question with instant feedback and no score impact. Correct answer turns green with explanation; wrong answer turns red with explanation. All options lock after selection. No retry gate — learner simply continues reading.

## Surfaces

google-apps-script-web, web, google-meet-stage, mcp-apps

## Fields

| Field | Type |
|---|---|
| question | string (required). The comprehension question. |
| options | array (required). Array of answer strings. |
| correct | integer (required). Zero-based index of the correct answer. |
| explanation | string (optional). Explanation shown after any selection. |

## Example payload

```json
{
  "type": "knowledge_check",
  "question": "Which option do you prefer?",
  "options": [
    {
      "label": "Option A",
      "value": "a"
    },
    {
      "label": "Option B",
      "value": "b"
    },
    {
      "label": "Option C",
      "value": "c"
    }
  ],
  "correct": 1
}
```

Live page: https://a2uicatalog.ai/atoms/knowledge_check/
Full field contract: https://a2uicatalog.ai/spec.json
