# Expandable Text

Renders a block of text that can be expanded or collapsed to reveal

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| summary | string |
| details | string |
| initial_state_expanded | boolean |

## Example payload

```json
{
  "type": "expandable_text",
  "summary": "A concise description of the content.",
  "details": "Click to expand and read the full details.",
  "initial_state_expanded": true
}
```

Live page: https://a2uicatalog.ai/atoms/expandable_text/
Full field contract: https://a2uicatalog.ai/spec.json
