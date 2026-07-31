# Progress Checkpoint

Displays an indicator showing the reader's current location within a multi-step sequence.

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| current_step | integer. The current active step index. |
| total_steps | integer. Total steps in the sequence. |

## Example payload

```json
{
  "type": "progress_checkpoint",
  "current_step": 2,
  "total_steps": 5
}
```

Live page: https://a2uicatalog.ai/atoms/progress_checkpoint/
Full field contract: https://a2uicatalog.ai/spec.json
