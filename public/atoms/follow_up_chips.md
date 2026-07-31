# Follow Up Chips

A row of tappable suggestion chips placed at the end of a response or slide, prompting the user with pre-written follow-up questions or actions. Each chip fires its text as a new user message when clicked.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| items | {'type': 'array', 'description': "List of suggestion strings. e.g. ['What's the ROI?', 'Show me by region', 'Compare to last year']."} |
| label | string (optional). Small heading above the chips. e.g. 'You might also ask:' |

## Example payload

```json
{
  "type": "follow_up_chips",
  "items": [
    {
      "label": "Item 1"
    },
    {
      "label": "Item 2"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/follow_up_chips/
Full field contract: https://a2uicatalog.ai/spec.json
