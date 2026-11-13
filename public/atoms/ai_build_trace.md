# Ai Build Trace

Token usage and model trace card — shows Gemini call stats inline on a page

## Surfaces

google-apps-script-web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn with differences | 2026-11-13 | pixels differ from React (light 480) |
| a2ui-vue | Drawn with differences | 2026-11-13 | pixels differ from React (dark 480); pixels differ from React (light 480) |
| Flutter | Native | 2026-11-13 |  |
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

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
