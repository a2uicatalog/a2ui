# Motion Checklist

A card of items that tick off one after another as p goes 0 to 1: each row brightens and slides in while its check pops, with optional empty placeholder rows under the real ones (the "recipe" card: your knowledge, your process, your automations). Plain HTML and CSS, no script: it moves with the --p custom property a motion_timeline p track sets, and standalone it renders every item ticked.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

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
| title | string (optional, max 40). |
| items | array (max 6) of string or {text, icon?} (text max 40, icon max 2 characters). Default one item "Item". |
| skeleton | integer (optional). Empty placeholder rows under the items, 0-4. Default 0. |
| size | integer (optional). Font size px, 10-80. Default 26. |
| accent | "#rrggbb" (optional). Colour of the ticks. Default the stage accent. |

## Example payload

```json
{
  "type": "motion_checklist"
}
```

Live page: https://a2uicatalog.ai/atoms/motion_checklist/
Full field contract: https://a2uicatalog.ai/spec.json
