# Api Param Table

Renders a structured documentation table outlining parameter fields, data types, requirements, and fallback options.

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
| parameters | array. Objects defining name, type, required flag, default value, and description. |

## Example payload

```json
{
  "type": "api_param_table"
}
```

Live page: https://a2uicatalog.ai/atoms/api_param_table/
Full field contract: https://a2uicatalog.ai/spec.json
