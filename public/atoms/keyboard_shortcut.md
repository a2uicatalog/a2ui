# Keyboard Shortcut

Renders inline text visual tags mimicking keyboard keys to highlight shortcuts or hotkey combinations.

## Surfaces

web, google-apps-script-web, mcp-apps

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
