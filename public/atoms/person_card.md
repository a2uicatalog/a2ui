# Person Card

Individual person card with name, role, optional photo, bio, tags, and contact links. Use inside a columns atom to build team rosters.

## Surfaces

web, google-apps-script-web, pdf, mcp-apps, android, slides, pptx

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
| name | string (required) |
| role | string (optional) |
| photo_url | string (optional, URL) |
| bio | string (optional, markdown) |
| email | string (optional) |
| linkedin | string (optional, URL) |
| tags | string[] (optional) |
| accent | string (optional, hex, default "#4f46e5") |

## Example payload

```json
{
  "type": "person_card",
  "name": "Person Card"
}
```

Live page: https://a2uicatalog.ai/atoms/person_card/
Full field contract: https://a2uicatalog.ai/spec.json
