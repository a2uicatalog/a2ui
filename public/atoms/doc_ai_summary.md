# Doc Ai Summary

Opens a Google Doc by ID, sends its text to Vertex AI Gemini, and renders the response as a structured summary card with word count and a link to the original doc. Requires VERTEX_PROJECT_ID in Script Properties.

## Surfaces

google-apps-script-web

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn | 2026-11-13 |  |
| a2ui-vue | Drawn | 2026-11-13 |  |
| Flutter | Native | 2026-11-13 |  |
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

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
