# Spotlight Card

A content card where a radial gradient spotlight follows the cursor. Child blocks or content field.

## Surfaces

web, google-meet-stage, google-apps-script-web, google-apps-script-side-panel, mcp-apps

## Fields

| Field | Type |
|---|---|
| blocks | array of child atoms inside the card |
| content | markdown string (if no blocks) |
| accent | spotlight tint colour (default var(--a2ui-accent)) |

## Example payload

```json
{
  "type": "spotlight_card",
  "blocks": [
    {
      "type": "body",
      "text": "Example content."
    }
  ],
  "content": "A concise description of the content."
}
```

Live page: https://a2uicatalog.ai/atoms/spotlight_card/
Full field contract: https://a2uicatalog.ai/spec.json
