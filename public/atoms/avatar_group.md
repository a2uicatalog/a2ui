# Avatar Group

Renders a stack or row of small user avatars, often indicating a group

## Surfaces

web, google-meet-stage, pdf, google-apps-script-web, mcp-apps, android

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
| avatars | list |
| total_count | integer |
| label | string |

## Example payload

```json
{
  "type": "avatar_group",
  "avatars": [
    {
      "src": "https://example.com/image.png",
      "name": "Alice"
    },
    {
      "src": "https://example.com/image.png",
      "name": "Bob"
    }
  ],
  "total_count": 5,
  "label": "Avatar Group"
}
```

Live page: https://a2uicatalog.ai/atoms/avatar_group/
Full field contract: https://a2uicatalog.ai/spec.json
