# Log Output

Displays a scrollable monospace block containing raw system or compilation log strings.

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| logs | string. The raw console log output text block. |

## Example payload

```json
{
  "type": "log_output",
  "logs": "2026-06-28 INFO: Process started\n2026-06-28 INFO: Completed."
}
```

Live page: https://a2uicatalog.ai/atoms/log_output/
Full field contract: https://a2uicatalog.ai/spec.json
