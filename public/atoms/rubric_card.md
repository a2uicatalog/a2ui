# Rubric Card

Assessment rubric table. Rows are assessment criteria, columns are performance levels (e.g. Beginning/Developing/Proficient/Exemplary). Descriptor text in each cell describes that level for that criterion. Static display — no state required.

## Surfaces

google-apps-script-web, web, google-meet-stage, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (optional). Table heading. Default "Assessment Rubric". |
| levels | array (optional). Performance level column headers. Default [Beginning, Developing, Proficient, Exemplary]. |
| accent | string (optional). Highest-level column colour. Default |
| criteria | array (required). Array of {criterion, descriptors[]} objects. descriptors[] maps to levels[] by index. |

## Example payload

```json
{
  "type": "rubric_card",
  "criteria": [
    {
      "label": "Accuracy",
      "score": 4,
      "max": 5
    },
    {
      "label": "Clarity",
      "score": 3,
      "max": 5
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/rubric_card/
Full field contract: https://a2uicatalog.ai/spec.json
