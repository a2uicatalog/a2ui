# Highlighted Text

Inline passage of text with a coloured highlight background and an optional margin annotation note. The annotation appears as a side-note pill on hover (CSS :hover) or as a visible aside on smaller viewports. Useful for reading comprehension exercises, exam technique callouts, and annotated source analysis.

## Surfaces

web, google-meet-stage, pdf, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| text | string. The passage to highlight. |
| annotation | string (optional). Margin note revealed on hover. |
| color | string (optional). Highlight background colour. Default "#fef08a" (yellow). |
| annotation_color | string (optional). Annotation pill background. Default "#fbbf24". |

## Example payload

```json
{
  "type": "highlighted_text",
  "text": "A concise description of the content."
}
```

Live page: https://a2uicatalog.ai/atoms/highlighted_text/
Full field contract: https://a2uicatalog.ai/spec.json
