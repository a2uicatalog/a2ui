# Live Vote

Live audience voting: buttons to vote, bar chart results, optional Google Sheets backend

## Surfaces

google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| question | string |
| options | array of strings (vote choices) |
| sheet_url | string (optional, Google Sheet CSV for live tallies) |
| write_url | string (optional, GAS doGet URL to record votes) |
| poll | number (optional, poll interval ms, default 5000) |
| accent | string (optional, hex) |

## Example payload

```json
{
  "type": "live_vote",
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

Live page: https://a2uicatalog.ai/atoms/live_vote/
Full field contract: https://a2uicatalog.ai/spec.json
