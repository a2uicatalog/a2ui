# Tool Call Card

A structured card displaying an AI agent tool invocation — in-flight, completed, or failed. Shows the tool name, execution status badge (running, success, error, pending), elapsed latency, formatted input arguments, and returned result or error message. Essential for agentic run narration, live tool traces, and human inspection of autonomous actions.

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| tool_name | string (required). The name of the invoked tool, e.g. "search_database" or "execute_code". |
| status | string (optional, default "running"). Status of the tool execution ("running", "success", "error", or "pending"). |
| args | string (optional). The input arguments passed to the tool, formatted as JSON string or key-value summary. |
| result | string (optional). The output data or response returned by the tool. |
| latency_ms | number (optional). Execution duration in milliseconds. |
| error | string (optional). Error details or exception message if status is "error". |

## Example payload

```json
{
  "type": "tool_call_card",
  "tool_name": "Tool name"
}
```

Live page: https://a2uicatalog.ai/atoms/tool_call_card/
Full field contract: https://a2uicatalog.ai/spec.json
