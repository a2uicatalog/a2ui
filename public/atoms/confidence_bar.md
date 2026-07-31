# Confidence Bar

Horizontal confidence or probability bar — shows a percentage value with a label and colour-coded fill indicating certainty level. Used for classification confidence, sentiment strength, retrieval relevance scores, or any normalised probability output. Original a2ui-catalogue atom.

## Surfaces

web, google-meet-stage, email, pdf, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| label | string. What is being measured, e.g. Positive Sentiment or Retrieval Relevance. |
| value | number. Confidence percentage 0-100. |
| items | array (optional). List of {label, value} for multi-row display instead of single bar. |
| color | string (optional). Override bar fill colour. Auto-assigned green/amber/red by value band if omitted. |

## Example payload

```json
{
  "type": "confidence_bar",
  "label": "Confidence Bar",
  "value": 75
}
```

Live page: https://a2uicatalog.ai/atoms/confidence_bar/
Full field contract: https://a2uicatalog.ai/spec.json
