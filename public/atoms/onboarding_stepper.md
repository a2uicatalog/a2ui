# Onboarding Stepper

Guided step-by-step onboarding flow for first-time learners. Each step has a label, description, optional action URL (navigated to on completion), and a "Mark complete" button. Completed steps persist in progress_store and are restored on revisit. Progress count shown at top.

## Surfaces

google-apps-script-web, web, google-meet-stage, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (optional). Stepper heading. Default "Get Started". |
| accent | string (optional). Active step indicator colour. Default |
| steps | array (required). Array of {id, icon, label, description, action_label, action_url?} objects. |

## Example payload

```json
{
  "type": "onboarding_stepper",
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

Live page: https://a2uicatalog.ai/atoms/onboarding_stepper/
Full field contract: https://a2uicatalog.ai/spec.json
