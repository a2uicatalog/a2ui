# Annotation Highlight

Rich body text passage with clickable highlighted terms that reveal inline explanations in a panel below. No state required. Ideal for glossary enrichment, technical definitions, or legal clause annotation within learning content.

## Surfaces

google-apps-script-web, web, google-meet-stage, mcp-apps

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
