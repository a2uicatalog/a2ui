# Doc Ai Summary

Opens a Google Doc by ID, sends its text to Vertex AI Gemini, and renders the response as a structured summary card with word count and a link to the original doc. Requires VERTEX_PROJECT_ID in Script Properties.

## Surfaces

google-apps-script-web

## Fields

| Field | Type |
|---|---|
| doc_id | string. Google Doc ID to summarise. |
| prompt | string (optional). Instruction sent to Gemini before the doc text. |
| title | string (optional). Override card title. Defaults to the doc name. |
| model | string (optional). Gemini model override. Defaults to VERTEX_MODEL property. |
| max_chars | integer (optional). Max doc characters sent to Gemini. Default 12000. |
| accent | string (optional). Accent colour. |
| show_meta | boolean (optional). Show word count and doc link. Default true. |

## Example payload

```json
{
  "type": "doc_ai_summary",
  "doc_id": "Doc id"
}
```

Live page: https://a2uicatalog.ai/atoms/doc_ai_summary/
Full field contract: https://a2uicatalog.ai/spec.json
