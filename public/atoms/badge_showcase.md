# Badge Showcase

Achievement badge wall — all course badges displayed in a grid. Earned badges glow with indigo highlight and full colour emoji; locked badges are greyed and dimmed. Each badge checks its required_id against progress_store to determine earned status.

## Surfaces

google-apps-script-web, web, google-meet-stage, mcp-apps, android

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
| title | string (optional). Section heading. Default "Achievements". |
| columns | integer (optional). Grid columns, max 6. Default 4. |
| badges | array (required). Array of {id, label, icon, description, required_id} objects. required_id is the progress_store key to check for completion. |

## Example payload

```json
{
  "type": "badge_showcase",
  "badges": [
    {
      "label": "TypeScript",
      "color": "#3178c6"
    },
    {
      "label": "React",
      "color": "#61dafb"
    },
    {
      "label": "A2UI",
      "color": "#6366f1"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/badge_showcase/
Full field contract: https://a2uicatalog.ai/spec.json
