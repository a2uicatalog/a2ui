# Keyboard Shortcut

Renders inline text visual tags mimicking keyboard keys to highlight shortcuts or hotkey combinations.

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
| keys | array. Individual key characters like Ctrl, Shift, or C to join. |
| action | string. The function or command triggered by the keystroke combination. |

## Example payload

```json
{
  "type": "keyboard_shortcut",
  "keys": [
    "Ctrl",
    "Shift",
    "K"
  ],
  "action": "submit"
}
```

Live page: https://a2uicatalog.ai/atoms/keyboard_shortcut/
Full field contract: https://a2uicatalog.ai/spec.json
