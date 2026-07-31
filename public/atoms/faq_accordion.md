# Faq Accordion

Renders a list of questions and answers, where answers are hidden until

## Surfaces

web, google-meet-stage, pdf, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| items | list of objects, each with 'question' (string) and 'answer' (string) |

## Example payload

```json
{
  "type": "faq_accordion",
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

Live page: https://a2uicatalog.ai/atoms/faq_accordion/
Full field contract: https://a2uicatalog.ai/spec.json
