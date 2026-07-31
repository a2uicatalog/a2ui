# Footnote

Renders a numbered footnote reference and its corresponding text, typically

## Surfaces

web, google-meet-stage, google-chat, email, pdf, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| number | integer (the footnote number) |
| text | string (the footnote content) |
| id | string (unique identifier for linking, e.g., "fn1") |

## Example payload

```json
{
  "type": "footnote",
  "number": 1,
  "text": "A concise description of the content.",
  "id": "example-id"
}
```

Live page: https://a2uicatalog.ai/atoms/footnote/
Full field contract: https://a2uicatalog.ai/spec.json
