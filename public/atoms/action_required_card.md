# Action Required Card

A card highlighting an important status or issue that requires immediate

## Surfaces

web, google-meet-stage, google-chat, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string The main title of the card, indicating the required action. |
| description | string A detailed explanation of the action needed. |
| action_label | string The text for the primary action button. |
| action_url | string The URL for the primary action button. |
| icon | string Optional icon to display on the card. |

## Example payload

```json
{
  "type": "action_required_card",
  "title": "Action Required Card",
  "description": "A concise description of the content.",
  "action_label": "Action label",
  "action_url": "https://example.com"
}
```

Live page: https://a2uicatalog.ai/atoms/action_required_card/
Full field contract: https://a2uicatalog.ai/spec.json
