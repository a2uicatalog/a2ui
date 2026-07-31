# Scenario Branch

Narrative branching learning atom. Presents a real-world situation with 2-4 labelled choices. Each choice reveals a consequence with good/neutral/bad outcome styling (green/amber/red). Includes a "try again" reset on non-linked consequences. Ideal for compliance, leadership, and soft-skills training.

## Surfaces

google-apps-script-web, web, google-meet-stage, mcp-apps

## Fields

| Field | Type |
|---|---|
| scenario | string (required). The situation or challenge presented to the learner. |
| context | string (optional). Background context shown in italics above the scenario. |
| accent | string (optional). Accent colour for choice buttons. Default |
| choices | array (required). Array of {label, consequence, outcome, next_url?} objects. outcome is "good", "neutral", or "bad". |

## Example payload

```json
{
  "type": "scenario_branch",
  "scenario": "Success path",
  "choices": [
    {
      "label": "Path A",
      "next": "node-a"
    },
    {
      "label": "Path B",
      "next": "node-b"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/scenario_branch/
Full field contract: https://a2uicatalog.ai/spec.json
