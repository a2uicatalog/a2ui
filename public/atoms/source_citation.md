# Source Citation

Inline-numbered RAG source reference card — shows a citation number, source title, optional excerpt, and optional URL. Designed to accompany AI-generated content that cites retrieved documents. Pairs with in-body superscript references [1], [2] etc. Original a2ui-catalogue atom.

## Surfaces

web, google-meet-stage, email, pdf, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| sources | {'type': 'array', 'description': 'List of {number, title, url?, excerpt?, author?, date?} citation objects.'} |
| heading | string (optional). Section heading above the list, e.g. "Sources". |

## Example payload

```json
{
  "type": "source_citation",
  "sources": 1
}
```

Live page: https://a2uicatalog.ai/atoms/source_citation/
Full field contract: https://a2uicatalog.ai/spec.json
