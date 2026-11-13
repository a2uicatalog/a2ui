# Before After Stack

Animated comparison: old approach items cross out one by one, then new approach slides in

## Surfaces

google-apps-script-web, mcp-apps, android

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
| items | array of strings (old approach items to cross out, alias: before_items) |
| before_label | string (optional) |
| after_label | string (optional) |
| result | string (the new approach shown after animation, alias: after_text) |
| delay | number (optional, seconds between strikes) |
| accent | string (optional, hex) |

## Example payload

```json
{
  "type": "before_after_stack",
  "items": [
    {
      "label": "Item 1"
    },
    {
      "label": "Item 2"
    }
  ],
  "result": "Improved"
}
```

Live page: https://a2uicatalog.ai/atoms/before_after_stack/
Full field contract: https://a2uicatalog.ai/spec.json
