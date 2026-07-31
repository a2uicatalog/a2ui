# Step Reveal Sequence

Tab-style step-by-step content with radio-button navigation

## Surfaces

google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| steps | array of {title, text} — each step shown in its own tab panel |

## Example payload

```json
{
  "type": "step_reveal_sequence",
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

Live page: https://a2uicatalog.ai/atoms/step_reveal_sequence/
Full field contract: https://a2uicatalog.ai/spec.json
