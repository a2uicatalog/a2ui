# Case Study Card

Structured enterprise case study card. Sections for situation narrative, key data points (label/value/note), numbered analysis questions, and an optional model answer reveal. No state required. The model answer is hidden behind a toggle button.

## Surfaces

google-apps-script-web, web, google-meet-stage, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (required). Case study title. |
| situation | string (required). The scenario narrative. |
| data_points | array (optional). Array of {label, value, note?} metric blocks. |
| questions | array (optional). Array of question strings for analysis. |
| model_answer | string (optional). Model answer text shown on toggle. Hidden by default. |
| accent | string (optional). Accent colour for data point values. Default |

## Example payload

```json
{
  "type": "case_study_card",
  "title": "Case Study Card",
  "situation": "A startup facing rapid growth challenges."
}
```

Live page: https://a2uicatalog.ai/atoms/case_study_card/
Full field contract: https://a2uicatalog.ai/spec.json
