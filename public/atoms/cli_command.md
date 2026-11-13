# Cli Command

Displays a copyable single-line command-line prompt for terminal execution.

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
| command | string. The exact shell command to be copied and executed. |

## Example payload

```json
{
  "type": "cli_command",
  "command": "npm install a2ui"
}
```

Live page: https://a2uicatalog.ai/atoms/cli_command/
Full field contract: https://a2uicatalog.ai/spec.json
