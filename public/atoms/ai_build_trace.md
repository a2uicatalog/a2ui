# Ai Build Trace

Token usage and model trace card — shows Gemini call stats inline on a page

## Surfaces

google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| model | string (optional, e.g. gemini-2.5-flash) |
| prompt_tokens | integer (optional) |
| thinking_tokens | integer (optional) |
| output_tokens | integer (optional) |
| total_tokens | integer (optional) |

## Example payload

```json
{
  "type": "ai_build_trace"
}
```

Live page: https://a2uicatalog.ai/atoms/ai_build_trace/
Full field contract: https://a2uicatalog.ai/spec.json
