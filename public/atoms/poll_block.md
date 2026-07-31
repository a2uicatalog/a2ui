# Poll Block

Interactive poll with a question and vote-count bar for each option.

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| question | string. Poll question. |
| options | array of {text, votes}. Poll choices. |

## Example payload

```json
{
  "type": "poll_block",
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
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/poll_block/
Full field contract: https://a2uicatalog.ai/spec.json
