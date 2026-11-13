# Reaction Group

Displays an interactive set of emoji elements collecting emotional sentiment feedback from readers.

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
| enabled_emojis | array. Tracked emojis: thumbs_up | heart | rocket | mind_blown. |

## Example payload

```json
{
  "type": "reaction_group",
  "enabled_emojis": [
    "\ud83d\udc4d",
    "\u2764\ufe0f",
    "\ud83c\udf89",
    "\ud83d\ude80"
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/reaction_group/
Full field contract: https://a2uicatalog.ai/spec.json
