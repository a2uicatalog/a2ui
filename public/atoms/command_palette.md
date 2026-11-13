# Command Palette

Keyboard-driven command palette overlay for quick navigation and action execution.

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
| commands | array of {text, shortcut}. Available commands. |

## Example payload

```json
{
  "type": "command_palette",
  "commands": [
    {
      "label": "New File",
      "shortcut": "Ctrl+N"
    },
    {
      "label": "Open File",
      "shortcut": "Ctrl+O"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/command_palette/
Full field contract: https://a2uicatalog.ai/spec.json
