# Token Budget Meter

Visual context-window usage meter — shows tokens consumed versus the model's total context limit, with a colour-coded fill that shifts amber then red as capacity is approached. Designed for AI agent dashboards, session monitoring, and prompt-engineering tooling. Original a2ui-catalogue atom.

## Surfaces

web, google-meet-stage, pdf, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| used | integer. Tokens consumed so far. |
| total | integer. Model context window size, e.g. 200000. |
| model | string (optional). Model name shown as subtitle, e.g. "claude-sonnet-4-6". |
| label | string (optional). Override the default "Context window" heading. |
| warn_at | number (optional). Percentage threshold to shift to amber. Default 70. |
| critical_at | number (optional). Percentage threshold to shift to red. Default 90. |
| animate | boolean (optional). Count up from 0 to `used` using CSS @property animation. Bar grows in sync. Uses dark styling suited to Meet stage. Default false (static). |
| duration | number (optional). Animation duration in seconds when animate is true. Default 2.0. |

## Example payload

```json
{
  "type": "token_budget_meter",
  "used": 1,
  "total": 5
}
```

Live page: https://a2uicatalog.ai/atoms/token_budget_meter/
Full field contract: https://a2uicatalog.ai/spec.json
