# Step Progress

Horizontal step progress indicator with numbered circles and connecting lines. Completed steps show a tick. Use at the top of wizard or onboarding flows.

## Surfaces

web, google-apps-script-web, pdf, mcp-apps

## Fields

| Field | Type |
|---|---|
| current | integer (required, 1-based index of active step) |
| accent | string (optional, hex, default "#6366f1") |
| steps | array (required). Array of {label or title} |

## Example payload

```json
{
  "type": "step_progress",
  "current": 2,
  "steps": [
    {
      "title": "Step one",
      "body": "First thing to do."
    },
    {
      "title": "Step two",
      "body": "Then this."
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/step_progress/
Full field contract: https://a2uicatalog.ai/spec.json
