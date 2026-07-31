# Risk Flag

Structured risk callout list with severity levels, description, and mitigation. For meeting prep, project status, incident reports.

## Surfaces

web, google-apps-script-web, pdf, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (optional) |
| risks | array (required). Array of {level ("critical"|"high"|"medium"|"low"), title, description?, mitigation?} |

## Example payload

```json
{
  "type": "risk_flag",
  "risks": [
    {
      "label": "Scope creep",
      "severity": "high"
    },
    {
      "label": "Timeline slip",
      "severity": "medium"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/risk_flag/
Full field contract: https://a2uicatalog.ai/spec.json
