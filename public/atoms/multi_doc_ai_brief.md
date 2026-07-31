# Multi Doc Ai Brief

Takes an array of Google Doc IDs and renders one Vertex AI Gemini summary card per doc — a compact briefing pack for meetings. Each doc can have its own prompt override.

## Surfaces

google-apps-script-web

## Fields

| Field | Type |
|---|---|
| docs | array. Array of {doc_id, title?, prompt?} objects. |
| default_prompt | string (optional). Fallback prompt for docs without their own. |
| accent | string (optional). Accent colour for doc links. |
| model | string (optional). Gemini model override. |

## Example payload

```json
{
  "type": "multi_doc_ai_brief",
  "docs": [
    {
      "title": "Doc 1",
      "url": "https://example.com"
    },
    {
      "title": "Doc 2",
      "url": "https://example.com"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/multi_doc_ai_brief/
Full field contract: https://a2uicatalog.ai/spec.json
