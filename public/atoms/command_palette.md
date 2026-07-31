# Command Palette

Keyboard-driven command palette overlay for quick navigation and action execution.

## Surfaces

web, google-apps-script-web, mcp-apps

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
