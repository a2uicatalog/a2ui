# Annotation Highlight

Rich body text passage with clickable highlighted terms that reveal inline explanations in a panel below. No state required. Ideal for glossary enrichment, technical definitions, or legal clause annotation within learning content.

## Surfaces

google-apps-script-web, web, google-meet-stage, mcp-apps, android

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
| text | string (required). Body text passage. Annotated terms are replaced server-side. |
| notes | array (required). Array of {term, explanation, color?} objects. First match in text is highlighted. |

## Example payload

```json
{
  "type": "annotation_highlight",
  "text": "A concise description of the content.",
  "notes": [
    {
      "text": "Important annotation",
      "range": "line 5"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/annotation_highlight/
Full field contract: https://a2uicatalog.ai/spec.json
