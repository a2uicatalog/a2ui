# Prompt To Schema

Three-panel flow diagram: natural language prompt → generated JSON schema → rendered page

## Surfaces

web, google-apps-script-web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn | 2026-11-13 |  |
| a2ui-vue | Drawn | 2026-11-13 |  |
| Flutter | Native | 2026-11-13 |  |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| prompt | string (the input prompt text) |
| schema | object or string (the generated JSON schema) |
| output | string (description of the rendered output) |
| labels | array of 3 strings (optional, panel headers) |
| accent | string (optional, hex) |

## Example payload

```json
{
  "type": "prompt_to_schema",
  "prompt": "Describe what you'd like to create.",
  "schema": "{\"type\": \"example\", \"value\": \"1,234\"}",
  "output": "\u2713 Done in 1.2s"
}
```

Live page: https://a2uicatalog.ai/atoms/prompt_to_schema/
Full field contract: https://a2uicatalog.ai/spec.json
