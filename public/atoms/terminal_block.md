# Terminal Block

Renders a static or interactive command-line interface terminal window showing input commands and output logs.

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
| command | string. The execution command displayed at the prompt. |
| output | string. The stdout or stderr text block response from the command. |
| shell | string: bash | zsh | powershell | cmd. The console design theme. |

## Example payload

```json
{
  "type": "terminal_block",
  "command": "npm install a2ui",
  "output": "\u2713 Done in 1.2s",
  "shell": "bash"
}
```

Live page: https://a2uicatalog.ai/atoms/terminal_block/
Full field contract: https://a2uicatalog.ai/spec.json
