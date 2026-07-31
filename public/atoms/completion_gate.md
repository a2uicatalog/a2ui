# Completion Gate

Renders a locked placeholder card until the specified module id is marked complete in progress_store. Once complete, the gate disappears to reveal content below it. Use to sequence content and prevent skipping.

## Surfaces

google-apps-script-web, web, google-meet-stage, mcp-apps

## Fields

| Field | Type |
|---|---|
| requires | string (required). Module id that must be complete in progress_store to unlock. |
| label | string (optional). Lock card heading. Default "Locked". |
| message | string (optional). Message shown on the lock card. |

## Example payload

```json
{
  "type": "completion_gate",
  "requires": "complete_intro"
}
```

Live page: https://a2uicatalog.ai/atoms/completion_gate/
Full field contract: https://a2uicatalog.ai/spec.json
