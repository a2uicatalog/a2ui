# Glossary Term

Renders a term with its definition, often with an optional link for

## Surfaces

web, google-meet-stage, google-chat, email, pdf, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| term | string (the term itself) |
| definition | string (the explanation) |
| link_text | optional string (e.g., "Learn more") |
| link_url | optional string (URL for more details) |

## Example payload

```json
{
  "type": "glossary_term",
  "term": "API",
  "definition": "Application Programming Interface"
}
```

Live page: https://a2uicatalog.ai/atoms/glossary_term/
Full field contract: https://a2uicatalog.ai/spec.json
