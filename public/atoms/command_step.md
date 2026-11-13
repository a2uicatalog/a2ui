# Command Step

Terminal-styled command with copy button and a done-checkbox. Wire done/setDone to a ValueStore to track completion (used by training runbooks for progress).

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
| label | string (optional, step title above the command) |
| command | string (required, the shell command; empty for manual steps) |
| hint | string (optional, small helper line under the checkbox) |

## Example payload

```json
{
  "type": "command_step",
  "command": "npm install a2ui"
}
```

Live page: https://a2uicatalog.ai/atoms/command_step/
Full field contract: https://a2uicatalog.ai/spec.json
