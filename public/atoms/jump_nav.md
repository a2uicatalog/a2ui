# Jump Nav

Horizontal strip of pill buttons that smooth-scroll to other blocks on the page by id.

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
| links | array (required) of {label, target (block id to scroll to)} |

## Example payload

```json
{
  "type": "jump_nav",
  "links": [
    {
      "label": "GitHub",
      "url": "https://github.com/a2uicatalog/a2ui"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/jump_nav/
Full field contract: https://a2uicatalog.ai/spec.json
