# Env Var List

Renders a clear configuration list detailing system environment variable keys, descriptions, and default values.

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
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| variables | array. List of objects including key name, description, requirement status, and default. |

## Example payload

```json
{
  "type": "env_var_list"
}
```

Live page: https://a2uicatalog.ai/atoms/env_var_list/
Full field contract: https://a2uicatalog.ai/spec.json
