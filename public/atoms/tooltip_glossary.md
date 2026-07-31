# Tooltip Glossary

Glossary list where hovering a term shows its definition as a tooltip

## Surfaces

google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| terms | array of {term, definition} |
| text | string (optional, introductory prose, alias: intro) |

## Example payload

```json
{
  "type": "tooltip_glossary",
  "terms": [
    {
      "term": "API",
      "definition": "Application Programming Interface"
    },
    {
      "term": "A2UI",
      "definition": "Adaptive Atom-based UI"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/tooltip_glossary/
Full field contract: https://a2uicatalog.ai/spec.json
