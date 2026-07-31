# Command Step

Terminal-styled command with copy button and a done-checkbox. Wire done/setDone to a ValueStore to track completion (used by training runbooks for progress).

## Surfaces

google-apps-script-web, mcp-apps

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
