# Shortcut Legend

Keyboard shortcut cheat-sheet grid. Multiple shortcuts displayed in a compact two-column layout, each showing the key combination and its action label. Distinct from keyboard_shortcut which shows a single combination inline.

## Surfaces

web, google-meet-stage, google-chat, email, pdf, google-apps-script-web, mcp-apps, android, slides, pptx

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Not verified | 2026-11-13 | no visible text in the example |
| Lit | Not verified | 2026-11-13 | no visible text in the example |
| Angular | Not verified | 2026-11-13 | no visible text in the example |
| CopilotKit | Not verified | 2026-11-13 | no visible text in the example |
| a2ui-vue | Not verified | 2026-11-13 | no visible text in the example |
| Flutter | Native | 2026-11-13 |  |
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| title | string (optional). Heading above the grid. |
| items | {'type': 'array', 'description': 'List of {keys, action} entries. keys is an array of key strings e.g. ["⌘", "K"]. action is the human-readable description.'} |

## Example payload

```json
{
  "type": "shortcut_legend",
  "items": [
    {
      "label": "Item 1"
    },
    {
      "label": "Item 2"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/shortcut_legend/
Full field contract: https://a2uicatalog.ai/spec.json
