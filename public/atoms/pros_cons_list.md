# Pros Cons List

Renders a two-column list itemizing advantages and disadvantages for

## Surfaces

web, google-meet-stage, google-chat, email, pdf, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| subject | string |
| pros | array |
| cons | array |

## Example payload

```json
{
  "type": "pros_cons_list",
  "subject": "Example subject matter",
  "pros": [
    "Scalable architecture",
    "Clean API design",
    "Excellent documentation"
  ],
  "cons": [
    "Steeper learning curve",
    "Limited third-party plugins"
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/pros_cons_list/
Full field contract: https://a2uicatalog.ai/spec.json
